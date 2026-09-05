import os
import json
import time
import subprocess
import pty
import select
import struct
import fcntl
import termios
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.loader import QuestionLoader
from core.selector import QuestionSelector
from core.deployer import LabDeployer
from core.grader import LabGrader
from core.models import ExamSession, Question, GradeResult
from core.recorder import recorder
from core.redis_bus import bus as redis_bus

app = FastAPI(title="Kubernetes Exam Web Simulator", version="2.0.0")

# Enable CORS for local development and embedded contexts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR = BASE_DIR / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

loader = QuestionLoader(BASE_DIR / "questions")
selector = QuestionSelector(loader, BASE_DIR / "presets")
deployer = LabDeployer(BASE_DIR / "var" / "session.json", BASE_DIR / "sets")
grader = LabGrader()


def _calculate_time_remaining(session: ExamSession) -> Optional[int]:
    """Calculates remaining seconds based on session created_at and time_limit_minutes."""
    if not session.time_limit_minutes:
        return None
    if not session.created_at:
        return session.time_limit_minutes * 60
    try:
        created_str = session.created_at.replace("Z", "+00:00")
        created_dt = datetime.fromisoformat(created_str)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        elapsed_seconds = int((now_dt - created_dt).total_seconds())
        total_seconds = session.time_limit_minutes * 60
        remaining = max(0, total_seconds - elapsed_seconds)
        return remaining
    except Exception as ex:
        print(f"[Warning] Failed to calculate time remaining: {ex}")
        return session.time_limit_minutes * 60


def _format_task_data(q: Question, idx: int, session: ExamSession) -> Dict[str, Any]:
    return {
        "task_num": idx + 1,
        "id": q.id,
        "title": q.title,
        "domain": q.domain.value if hasattr(q.domain, "value") else str(q.domain),
        "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
        "points": q.points,
        "target_context": q.target_context,
        "namespace": q.namespace or "default",
        "description": q.description,
        "cluster_scoped": q.cluster_scoped,
        "tags": q.tags,
        "is_flagged": q.id in session.flagged,
        "score_data": session.scores.get(q.id),
    }


class JumpRequest(BaseModel):
    task_num: int


class FlagRequest(BaseModel):
    task_num: Optional[int] = None


class StartRequest(BaseModel):
    preset: Optional[str] = "mock-01-acme"
    all_questions: Optional[bool] = False
    question_ids: Optional[List[str]] = None


class PresetSelectRequest(BaseModel):
    preset: str


class ClipboardRequest(BaseModel):
    text: str


class ClientEventRequest(BaseModel):
    event_type: str
    data: Optional[Dict[str, Any]] = None


_selected_preset_override: Optional[str] = None


def _get_locked_preset_info(override_preset: Optional[str] = None) -> Dict[str, Any]:
    global _selected_preset_override
    preset_key = override_preset or _selected_preset_override or os.getenv("EXAM_PRESET", "mock-01-acme")
    if preset_key == "all":
        return {
            "filename": "all",
            "name": "Full Curriculum (All Tasks)",
            "description": "All available exam tasks in random/sequential order.",
            "task_count": len(loader.get_all_question_ids()),
            "time_limit_minutes": None,
            "pass_threshold_percent": 66,
        }

    preset_data = selector.load_preset(preset_key)
    if preset_data:
        return {
            "filename": preset_key,
            "name": preset_data.get("name", preset_key),
            "description": preset_data.get("description", "17-question timed mock exam."),
            "task_count": len(preset_data.get("questions", [])),
            "time_limit_minutes": preset_data.get("time_limit_minutes", 120),
            "pass_threshold_percent": preset_data.get("pass_threshold_percent", 66),
        }
    return {
        "filename": "mock-01-acme",
        "name": "Mock Exam 01",
        "description": "Default mock preset",
        "task_count": 17,
        "time_limit_minutes": 120,
        "pass_threshold_percent": 66,
    }


# --- API Routes ---

@app.get("/api/session")
def get_session(request: Request):
    session = deployer.load_active_session(loader)
    
    # Check query params for admin/candidate mode
    url_admin = request.query_params.get("admin")
    url_candidate = request.query_params.get("candidate")
    url_preset = request.query_params.get("preset")

    if url_admin in ("1", "true", "yes"):
        is_admin = True
    elif url_candidate in ("1", "true", "yes"):
        is_admin = False
    else:
        is_admin = os.getenv("EXAM_ADMIN", "0") == "1"

    preset_info = _get_locked_preset_info(url_preset)

    if not session:
        return {
            "active": False,
            "session": None,
            "locked_preset": preset_info,
            "is_admin": is_admin,
        }

    cur_idx = session.current_index
    current_q = session.current_question

    task_data = None
    if current_q:
        task_data = _format_task_data(current_q, cur_idx, session)

    time_remaining = _calculate_time_remaining(session)
    start_ts = None
    end_ts = None
    if session.created_at:
        try:
            c_str = session.created_at.replace("Z", "+00:00")
            c_dt = datetime.fromisoformat(c_str)
            if c_dt.tzinfo is None:
                c_dt = c_dt.replace(tzinfo=timezone.utc)
            start_ts = c_dt.timestamp()
            if session.time_limit_minutes:
                end_ts = start_ts + (session.time_limit_minutes * 60)
        except Exception:
            pass

    # Resolve terminal & noVNC URLs
    terminal_port = os.getenv("TERMINAL_PORT", "7681")
    novnc_port = os.getenv("NOVNC_PORT", "6080")

    return {
        "active": True,
        "session_id": session.session_id,
        "name": session.name,
        "mode": session.mode,
        "current_index": cur_idx,
        "total_tasks": len(session.questions),
        "time_limit_minutes": session.time_limit_minutes,
        "time_remaining_seconds": time_remaining,
        "created_at": session.created_at,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "server_timestamp": datetime.now(timezone.utc).timestamp(),
        "flagged_ids": session.flagged,
        "current_task": task_data,
        "terminal_port": terminal_port,
        "novnc_port": novnc_port,
        "is_admin": is_admin,
    }


@app.get("/api/questions")
def get_questions():
    session = deployer.load_active_session(loader)
    if not session:
        return {"questions": []}

    questions_list = []
    for idx, q in enumerate(session.questions):
        questions_list.append({
            "task_num": idx + 1,
            "id": q.id,
            "title": q.title,
            "domain": q.domain.value if hasattr(q.domain, "value") else str(q.domain),
            "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
            "points": q.points,
            "target_context": q.target_context,
            "namespace": q.namespace or "default",
            "is_current": idx == session.current_index,
            "is_flagged": q.id in session.flagged,
            "score_data": session.scores.get(q.id),
        })

    return {"questions": questions_list, "total": len(questions_list)}


@app.get("/api/timer")
def get_timer():
    session_file = deployer.session_file
    if not session_file.exists():
        return {"active": False, "time_remaining_seconds": None}
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        time_limit = data.get("time_limit_minutes")
        created_at = data.get("created_at")
        if not time_limit:
            return {"active": True, "time_remaining_seconds": None, "time_limit_minutes": None}

        created_str = (created_at or "").replace("Z", "+00:00")
        created_dt = datetime.fromisoformat(created_str)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        start_ts = created_dt.timestamp()
        total = time_limit * 60
        end_ts = start_ts + total
        remaining = max(0, int(end_ts - now_dt.timestamp()))
        elapsed = int(now_dt.timestamp() - start_ts)
        return {
            "active": True,
            "session_id": data.get("session_id"),
            "started_at": created_dt.isoformat(),
            "start_timestamp": start_ts,
            "end_timestamp": end_ts,
            "server_timestamp": now_dt.timestamp(),
            "time_limit_minutes": time_limit,
            "total_seconds": total,
            "elapsed_seconds": elapsed,
            "time_remaining_seconds": remaining,
        }
    except Exception as e:
        return {"active": False, "error": str(e)}


@app.get("/api/presets")
def get_presets():
    presets = selector.list_presets()
    for p in presets:
        if "task_count" not in p:
            p["task_count"] = len(p.get("questions", []))
    selected = _selected_preset_override or os.getenv("EXAM_PRESET", "mock-01-acme")
    return {"presets": presets, "selected": selected}


@app.post("/api/presets/select")
def select_preset(req: PresetSelectRequest):
    global _selected_preset_override
    _selected_preset_override = req.preset
    return {"status": "ok", "preset": req.preset, "info": _get_locked_preset_info(req.preset)}


@app.post("/api/clipboard")
def set_clipboard_endpoint(req: ClipboardRequest):
    global _last_x11_clipboard
    try:
        session = deployer.load_active_session(loader)
        sid = session.session_id if session else "default"
        _last_x11_clipboard = req.text
        redis_bus.set_clipboard(sid, req.text)
        if session:
            try:
                recorder.attach_or_resume(session.session_id, session.name)
                recorder.log_event("CLIPBOARD_COPY", {
                    "length": len(req.text),
                    "preview": req.text[:120],
                })
            except Exception:
                pass
        return {"status": "ok", "length": len(req.text)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/clipboard")
def get_clipboard_endpoint():
    try:
        session = deployer.load_active_session(loader)
        sid = session.session_id if session else "default"
        text = redis_bus.get_clipboard(sid)
        return {"text": text}
    except Exception as e:
        return {"text": "", "error": str(e)}


def _make_progress_cb(session_id: str):
    def cb(stage: str, title: str, step: int, total_steps: int, desc: str = ""):
        try:
            redis_bus.publish_session_event(session_id, {
                "type": "transition_progress",
                "stage": stage,
                "title": title,
                "desc": desc,
                "step": step,
                "total_steps": total_steps,
                "percent": int((step / total_steps) * 100),
            })
        except Exception:
            pass
    return cb


@app.post("/api/action/next")
def action_next(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")

    next_idx = session.current_index + 1
    if next_idx >= len(session.questions):
        raise HTTPException(status_code=400, detail="Already at the final task")

    deployer.deploy_step(session, next_idx, progress_cb=_make_progress_cb(session.session_id))
    return get_session(request)


@app.post("/api/action/prev")
def action_prev(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")

    prev_idx = session.current_index - 1
    if prev_idx < 0:
        raise HTTPException(status_code=400, detail="Already at the first task")

    deployer.deploy_step(session, prev_idx, progress_cb=_make_progress_cb(session.session_id))
    return get_session(request)


@app.post("/api/action/jump")
def action_jump(req: JumpRequest, request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")

    target_idx = req.task_num - 1
    if target_idx < 0 or target_idx >= len(session.questions):
        raise HTTPException(status_code=400, detail=f"Task number {req.task_num} out of range")

    deployer.deploy_step(session, target_idx, progress_cb=_make_progress_cb(session.session_id))
    return get_session(request)


@app.post("/api/action/flag")
def action_flag(req: FlagRequest):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")

    idx = (req.task_num - 1) if req.task_num is not None else session.current_index
    if idx < 0 or idx >= len(session.questions):
        raise HTTPException(status_code=400, detail="Invalid task index")

    target_q = session.questions[idx]
    if target_q.id in session.flagged:
        session.flagged.remove(target_q.id)
        is_flagged = False
    else:
        session.flagged.append(target_q.id)
        is_flagged = True

    deployer.save_session(session)
    try:
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_FLAGGED" if is_flagged else "TASK_UNFLAGGED", {
            "task_num": idx + 1,
            "question_id": target_q.id,
            "title": target_q.title,
            "is_flagged": is_flagged,
        })
    except Exception:
        pass
    return {"id": target_q.id, "task_num": idx + 1, "is_flagged": is_flagged, "flagged_ids": session.flagged}


@app.post("/api/action/retry")
def action_retry():
    session = deployer.load_active_session(loader)
    if not session or not session.current_question:
        raise HTTPException(status_code=400, detail="No active question to retry")

    cur_idx = session.current_index
    try:
        cur_q = session.current_question
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_RETRY", {
            "task_num": cur_idx + 1,
            "question_id": cur_q.id if cur_q else None,
            "title": cur_q.title if cur_q else None,
        })
    except Exception:
        pass
    # Re-run deploy step for current index with forced setup reset
    deployer.deploy_step(session, cur_idx, force_setup=True, progress_cb=_make_progress_cb(session.session_id))
    return {"status": "ok", "message": f"Task {cur_idx + 1} re-initialized"}


@app.post("/api/action/submit")
def action_submit():
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")

    # 1. Evaluate active question if present
    if session.mode == "sequential" and session.current_question:
        cur_q = session.current_question
        try:
            res = grader.grade_question(cur_q)
            session.scores[cur_q.id] = {
                "passed": res.passed,
                "score": res.score,
                "max_score": res.max_score,
                "message": res.message,
            }
            try:
                recorder.attach_or_resume(session.session_id, session.name)
                recorder.log_event("TASK_EVALUATION", {
                    "task_num": session.current_index + 1,
                    "question_id": cur_q.id,
                    "score": res.score,
                    "max_score": res.max_score,
                    "passed": res.passed,
                    "message": res.message,
                })
            except Exception:
                pass
        except Exception as e:
            session.scores[cur_q.id] = {
                "passed": False,
                "score": 0,
                "max_score": cur_q.points,
                "message": f"Evaluation error: {e}",
            }
        deployer.save_session(session)

    # 2. Grade all flagged tasks upon final exam submission
    flagged_ids = set(getattr(session, "flagged", []) or [])
    for idx, q in enumerate(session.questions):
        if session.current_question and q.id == session.current_question.id:
            continue
        sc = session.scores.get(q.id)
        is_flagged = q.id in flagged_ids or (sc and str(sc.get("message", "")).startswith("Flagged for review"))
        if is_flagged:
            try:
                res = grader.grade_question(q)
                session.scores[q.id] = {
                    "passed": res.passed,
                    "score": res.score,
                    "max_score": res.max_score,
                    "message": res.message,
                }
                try:
                    recorder.attach_or_resume(session.session_id, session.name)
                    recorder.log_event("TASK_EVALUATION", {
                        "task_num": idx + 1,
                        "question_id": q.id,
                        "score": res.score,
                        "max_score": res.max_score,
                        "passed": res.passed,
                        "message": res.message,
                    })
                except Exception:
                    pass
            except Exception as e:
                session.scores[q.id] = {
                    "passed": False,
                    "score": 0,
                    "max_score": q.points,
                    "message": f"Evaluation error: {e}",
                }

    deployer.save_session(session)
    summaries = grader.grade_session(session)
    deployer.save_session(session)

    total_earned = sum(s.result.score for s in summaries)
    total_possible = sum(s.result.max_score for s in summaries)
    pct = (total_earned / total_possible * 100) if total_possible > 0 else 0.0
    passed = pct >= 66.0

    scorecard_rows = []
    for s in summaries:
        scorecard_rows.append({
            "task_num": s.task_num,
            "id": s.question.id,
            "title": s.question.title,
            "domain": s.question.domain.value if hasattr(s.question.domain, "value") else str(s.question.domain),
            "difficulty": s.question.difficulty.value if hasattr(s.question.difficulty, "value") else str(s.question.difficulty),
            "context": s.question.target_context,
            "score": s.result.score,
            "max_score": s.result.max_score,
            "passed": s.result.passed,
            "message": s.result.message,
        })

    report_data = {
        "scorecard": scorecard_rows,
        "total_earned": total_earned,
        "total_possible": total_possible,
        "percentage": round(pct, 1),
        "passed": passed,
        "threshold": 66.0,
        "session_id": getattr(session, "session_id", "session-unknown"),
        "exam_name": getattr(session, "name", "CKA Exam"),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Persist report files to disk
    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        json_path = REPORTS_DIR / f"report-{report_data['session_id']}.json"
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2)

        md_path = REPORTS_DIR / f"report-{report_data['session_id']}.md"
        status_str = "PASSED" if passed else "FAILED"
        md_lines = [
            f"# CKA Exam Report — {report_data['exam_name']}",
            f"**Result**: `{status_str}` ({round(pct, 1)}% — {total_earned}/{total_possible} pts)",
            f"**Threshold**: 66.0% | **Session**: `{report_data['session_id']}`",
            f"**Submitted**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "| # | ID | Title | Domain | Context | Score | Status | Details |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in scorecard_rows:
            st = "PASS" if r["passed"] else "FAIL"
            md_lines.append(f"| {r['task_num']} | `{r['id']}` | {r['title']} | {r['domain']} | `{r['context']}` | {r['score']}/{r['max_score']} | **{st}** | {r['message']} |")
        
        with open(md_path, "w") as f:
            f.write("\n".join(md_lines) + "\n")
        report_data["report_file"] = str(md_path)
    except Exception as ex:
        print(f"[Warning] Failed to persist report file: {ex}")

    try:
        recorder.finish_session(
            session_id=report_data["session_id"],
            scorecard=scorecard_rows,
            percentage=report_data["percentage"],
            passed=report_data["passed"],
            total_earned=total_earned,
            total_possible=total_possible,
        )
    except Exception as ex:
        print(f"[Warning] Failed to finalize recording: {ex}")

    return report_data


@app.get("/api/reports")
def list_reports():
    if not REPORTS_DIR.exists():
        return {"reports": []}
    files = sorted(REPORTS_DIR.glob("report-*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    res = []
    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                res.append({
                    "filename": f.name,
                    "session_id": data.get("session_id"),
                    "exam_name": data.get("exam_name"),
                    "submitted_at": data.get("submitted_at"),
                    "percentage": data.get("percentage"),
                    "passed": data.get("passed"),
                    "score": f"{data.get('total_earned')}/{data.get('total_possible')}",
                    "md_file": f"report-{data.get('session_id')}.md",
                })
        except Exception:
            pass
    return {"reports": res}


@app.get("/api/reports/{filename}")
def get_report(filename: str):
    file_path = REPORTS_DIR / filename
    if not file_path.is_file() or not file_path.resolve().is_relative_to(REPORTS_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Report not found")
    media_type = "application/json" if filename.endswith(".json") else "text/markdown"
    return FileResponse(file_path, media_type=media_type, filename=filename)


@app.get("/api/recordings")
def list_recordings_endpoint():
    recs = recorder.list_recordings()
    return {"recordings": recs, "total": len(recs)}


@app.get("/api/recordings/{session_id}")
def get_recording_detail_endpoint(session_id: str):
    data = recorder.get_recording(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Recording not found")
    return data


@app.get("/api/recordings/{session_id}/cast")
def get_recording_cast_endpoint(session_id: str):
    cast_path = recorder.get_cast_path(session_id)
    if not cast_path or not cast_path.is_file():
        raise HTTPException(status_code=404, detail="Asciinema cast recording not found")
    return FileResponse(
        cast_path,
        media_type="application/x-asciicast",
        filename=f"{session_id}.cast",
    )


@app.get("/api/recordings/{session_id}/events")
def get_recording_events_endpoint(session_id: str):
    events = recorder.get_events(session_id)
    return {"session_id": session_id, "events": events, "total": len(events)}


@app.post("/api/recordings/{session_id}/event")
def log_client_event_endpoint(session_id: str, req: ClientEventRequest):
    try:
        recorder.attach_or_resume(session_id)
        recorder.log_event(req.event_type, req.data or {})
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/start")
def start_exam(req: StartRequest, request: Request):
    if req.all_questions:
        questions = loader.get_all()
        session = deployer.deploy_sequential(
            questions,
            session_name="Full Curriculum (111 Tasks)",
            time_limit_minutes=None,
        )
    elif req.question_ids:
        questions = [loader.get(qid) for qid in req.question_ids if loader.get(qid) is not None]
        if not questions:
            raise HTTPException(status_code=400, detail="No valid questions found for given IDs")
        session = deployer.deploy_sequential(
            questions,
            session_name=f"Selected Practice Tasks ({len(questions)} Questions)",
            time_limit_minutes=None,
        )
    else:
        preset_name = req.preset or "mock-01-acme"
        preset_data = selector.load_preset(preset_name)
        if not preset_data:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
        q_ids = preset_data.get("questions", [])
        questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
        session = deployer.deploy_sequential(
            questions,
            session_name=preset_data.get("name", preset_name),
            time_limit_minutes=preset_data.get("time_limit_minutes", 120),
        )

    return get_session(request)


@app.post("/api/reset")
def reset_exam():
    deployer.clear_session(cleanup_cluster=True)
    return {"status": "ok", "message": "Exam session cleared and cluster cleaned"}


# --- Built-in WebSocket PTY Terminal ---

@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    await websocket.accept()

    session = deployer.load_active_session(loader)
    sid = session.session_id if session else "default"
    if session:
        try:
            recorder.attach_or_resume(session.session_id, session.name)
            recorder.log_event("TERMINAL_ATTACH", {"session_id": session.session_id})
        except Exception:
            pass

    # Instant scrollback replay from Redis buffer upon connect/reconnect
    try:
        buffered_chunks = redis_bus.get_terminal_buffer(sid)
        for chunk in buffered_chunks:
            await websocket.send_bytes(chunk)
    except Exception:
        pass

    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["COLORTERM"] = "truecolor"
    env["EXAM_RECORDED"] = "1"
    env["WEB_TERMINAL"] = "1"

    pid, master_fd = pty.fork()
    if pid == 0:
        target_user = os.getenv("EXAM_USER", "exam")
        try:
            import pwd
            user_entry = pwd.getpwnam(target_user)
            uid = user_entry.pw_uid
            gid = user_entry.pw_gid
            home_dir = user_entry.pw_dir
            shell = user_entry.pw_shell or "/bin/bash"

            env["USER"] = target_user
            env["LOGNAME"] = target_user
            env["HOME"] = home_dir
            env["SHELL"] = shell

            try:
                os.fchown(0, uid, gid)
            except Exception:
                pass

            try:
                os.chdir(home_dir)
            except Exception:
                pass

            os.initgroups(target_user, gid)
            os.setgid(gid)
            os.setuid(uid)
        except KeyError:
            shell = os.environ.get("SHELL", "/bin/bash")
            try:
                os.chdir(str(Path.home()))
            except Exception:
                pass

        try:
            os.setpgid(0, 0)
            termios.tcsetpgrp(0, os.getpgrp())
        except Exception:
            pass

        os.execvpe(shell, [shell, "-i"], env)
    else:
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        async def read_from_pty():
            while True:
                try:
                    await asyncio.sleep(0.01)
                    r, _, _ = select.select([master_fd], [], [], 0)
                    if r:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                        try:
                            recorder.record_output(data)
                        except Exception:
                            pass
                        try:
                            redis_bus.append_terminal_buffer(sid, data)
                        except Exception:
                            pass
                        await websocket.send_bytes(data)
                except Exception:
                    break

        async def write_to_pty():
            while True:
                try:
                    msg = await websocket.receive()
                    if "bytes" in msg and msg["bytes"]:
                        os.write(master_fd, msg["bytes"])
                        try:
                            recorder.record_input(msg["bytes"])
                        except Exception:
                            pass
                    elif "text" in msg and msg["text"]:
                        text = msg["text"]
                        if text.startswith('{"resize":'):
                            try:
                                rdata = json.loads(text)["resize"]
                                rows = int(rdata.get("rows", 24))
                                cols = int(rdata.get("cols", 80))
                                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                                recorder.record_resize(cols, rows)
                            except Exception:
                                pass
                        else:
                            raw_b = text.encode("utf-8")
                            os.write(master_fd, raw_b)
                            try:
                                recorder.record_input(raw_b)
                            except Exception:
                                pass
                except WebSocketDisconnect:
                    break
                except Exception:
                    break

        read_task = asyncio.create_task(read_from_pty())
        write_task = asyncio.create_task(write_to_pty())

        done, pending = await asyncio.wait(
            [read_task, write_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

        try:
            recorder.log_event("TERMINAL_DETACH")
        except Exception:
            pass

        try:
            os.close(master_fd)
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        except Exception:
            pass


# --- Integrated noVNC WebSocket Proxy ---

async def _proxy_vnc(websocket: WebSocket):
    requested_proto = websocket.headers.get("sec-websocket-protocol", "")
    subprotocol = "binary" if "binary" in requested_proto else None
    await websocket.accept(subprotocol=subprotocol)
    print(f"[VNC Proxy] Client connected from {websocket.client}. Subprotocol: {subprotocol}")

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", 5901)
        print("[VNC Proxy] Connected to TigerVNC on 127.0.0.1:5901")
    except Exception as e:
        print(f"[VNC Proxy] Failed to connect to TigerVNC: {e}")
        await websocket.close()
        return

    async def client_to_vnc():
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    print("[VNC Proxy] Client sent websocket.disconnect")
                    break
                if "bytes" in msg and msg["bytes"]:
                    writer.write(msg["bytes"])
                    await writer.drain()
                elif "text" in msg and msg["text"]:
                    writer.write(msg["text"].encode("latin1"))
                    await writer.drain()
        except Exception as e:
            print(f"[VNC Proxy] client_to_vnc exception: {e}")
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def vnc_to_client():
        try:
            while True:
                data = await reader.read(16384)
                if not data:
                    print("[VNC Proxy] TigerVNC closed reader connection (EOF)")
                    break
                await websocket.send_bytes(data)
        except Exception as e:
            print(f"[VNC Proxy] vnc_to_client exception: {e}")
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    c2v = asyncio.create_task(client_to_vnc())
    v2c = asyncio.create_task(vnc_to_client())

    done, pending = await asyncio.wait(
        [c2v, v2c],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    print("[VNC Proxy] Session finished cleanly.")


@app.websocket("/ws/vnc")
async def vnc_ws_primary(websocket: WebSocket):
    await _proxy_vnc(websocket)


@app.websocket("/websockify")
async def vnc_ws_websockify(websocket: WebSocket):
    await _proxy_vnc(websocket)


@app.websocket("/novnc/websockify")
async def vnc_ws_novnc_websockify(websocket: WebSocket):
    await _proxy_vnc(websocket)


@app.websocket("/novnc/ws/vnc")
async def vnc_ws_novnc_vnc(websocket: WebSocket):
    await _proxy_vnc(websocket)


# --- Real-Time Session & Redis Pub/Sub WebSocket ---

@app.websocket("/ws/session/{session_id}")
async def session_events_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if not redis_bus.is_available():
        # Fallback loop if Redis is temporarily offline
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "clipboard_copy":
                        text = msg.get("text", "")
                        global _last_x11_clipboard
                        _last_x11_clipboard = text
                        await redis_bus.async_set_clipboard(session_id, text)
                        try:
                            recorder.attach_or_resume(session_id)
                            recorder.log_event("CLIPBOARD_COPY", {
                                "length": len(text),
                                "preview": text[:120],
                            })
                        except Exception:
                            pass
                except Exception:
                    pass
        except WebSocketDisconnect:
            pass
        return

    async_redis = redis_bus.get_async_client()
    pubsub = async_redis.pubsub()
    channel = f"session:{session_id}"
    await pubsub.subscribe(channel)

    async def pubsub_to_ws():
        try:
            async for message in pubsub.listen():
                if message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    await websocket.send_text(raw_data)
        except Exception:
            pass

    async def ws_to_redis():
        global _last_x11_clipboard
        try:
            while True:
                raw_text = await websocket.receive_text()
                try:
                    payload = json.loads(raw_text)
                    msg_type = payload.get("type")
                    if msg_type == "clipboard_copy":
                        text = payload.get("text", "")
                        _last_x11_clipboard = text
                        target_sid = session_id
                        if target_sid == "active":
                            session = deployer.load_active_session(loader)
                            target_sid = session.session_id if session else "default"
                        await redis_bus.async_set_clipboard(target_sid, text)
                        try:
                            recorder.attach_or_resume(target_sid)
                            recorder.log_event("CLIPBOARD_COPY", {
                                "length": len(text),
                                "preview": text[:120],
                            })
                        except Exception:
                            pass
                    elif msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "time": time.time()}))
                except Exception:
                    pass
        except Exception:
            pass

    t1 = asyncio.create_task(pubsub_to_ws())
    t2 = asyncio.create_task(ws_to_redis())
    try:
        done, pending = await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception:
            pass


# --- Background Workers: Host Clipboard & Timer Broadcast ---

_last_x11_clipboard = ""

@app.on_event("startup")
async def start_background_workers():
    asyncio.create_task(_clipboard_x11_monitor())
    asyncio.create_task(_session_timer_broadcaster())

async def _clipboard_x11_monitor():
    global _last_x11_clipboard
    loop = asyncio.get_running_loop()
    while True:
        try:
            session = deployer.load_active_session(loader)
            if session and session.session_id:
                sid = session.session_id
                def read_xsel():
                    env = {
                        "DISPLAY": os.getenv("VNC_DISPLAY", ":1"),
                        "XAUTHORITY": os.getenv("XAUTHORITY", "/home/exam/.Xauthority"),
                        "HOME": os.getenv("EXAM_HOME", "/home/exam"),
                    }
                    try:
                        res = subprocess.run(["xsel", "-b", "-o"], env=env, capture_output=True, text=True, timeout=1)
                        t = res.stdout
                        if not t:
                            res_p = subprocess.run(["xsel", "-p", "-o"], env=env, capture_output=True, text=True, timeout=1)
                            t = res_p.stdout
                        return t or ""
                    except Exception:
                        return ""

                current = await loop.run_in_executor(None, read_xsel)
                if current and current != _last_x11_clipboard:
                    _last_x11_clipboard = current
                    await redis_bus.async_publish_session_event(sid, {
                        "type": "clipboard_update",
                        "text": current,
                        "timestamp": time.time(),
                    })
        except Exception:
            pass
        await asyncio.sleep(1.0)

async def _session_timer_broadcaster():
    while True:
        try:
            session = deployer.load_active_session(loader)
            if session and session.session_id:
                rem = _calculate_time_remaining(session)
                if rem is not None:
                    await redis_bus.async_publish_session_event(session.session_id, {
                        "type": "timer_tick",
                        "time_remaining_seconds": rem,
                        "server_timestamp": time.time(),
                    })
        except Exception:
            pass
        await asyncio.sleep(2.0)



# Mount noVNC static files if present
NOVNC_DIR = Path("/usr/share/novnc")
if NOVNC_DIR.exists():
    app.mount("/novnc", StaticFiles(directory=str(NOVNC_DIR), html=True), name="novnc")

# Mount static directory for frontend web UI
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
