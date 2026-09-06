import os
import json
import time
import secrets
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

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
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
from core.redis_bus import bus as redis_bus, get_system_resource_info
from core.desktop_manager import desktop_mgr

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
    preset: Optional[str] = None
    all_questions: Optional[bool] = False
    question_ids: Optional[List[str]] = None
    candidate_token: Optional[str] = None


class PresetSelectRequest(BaseModel):
    preset: str


class ClipboardRequest(BaseModel):
    text: str


class AdminLoginRequest(BaseModel):
    password: str


class AdminConfigRequest(BaseModel):
    default_preset: str


class CreateSessionInviteRequest(BaseModel):
    preset: Optional[str] = None


ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
_admin_tokens: set = set()


def is_admin_authenticated(req_or_ws) -> bool:
    """Checks if request or websocket carries valid admin credentials."""
    # 1. Cookie check
    cookie_token = None
    if hasattr(req_or_ws, "cookies") and req_or_ws.cookies:
        cookie_token = req_or_ws.cookies.get("admin_token")
    if cookie_token:
        if cookie_token in _admin_tokens or redis_bus.verify_admin_token(cookie_token):
            return True

    # 2. Authorization Bearer header
    headers = getattr(req_or_ws, "headers", {}) or {}
    auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token in _admin_tokens or redis_bus.verify_admin_token(token):
            return True

    # 3. Query param check (e.g. for WebSockets or iframes)
    params = getattr(req_or_ws, "query_params", {}) or {}
    q_token = params.get("admin_token")
    if q_token:
        if q_token in _admin_tokens or redis_bus.verify_admin_token(q_token):
            return True

    # 4. Fallback to EXAM_ADMIN env
    if os.getenv("EXAM_ADMIN", "0").lower() in ("1", "true"):
        return True

    return False


_running_containers_cache: set = set()
_last_container_cache_time: float = 0.0


def get_running_desktop_containers() -> set:
    """Returns a cached set of running desktop container names with a 2-second TTL to avoid CLI subprocess storms."""
    global _running_containers_cache, _last_container_cache_time
    now = time.time()
    if now - _last_container_cache_time < 2.0 and _running_containers_cache is not None:
        return _running_containers_cache
    try:
        r = subprocess.run(
            ["docker", "ps", "--filter", "name=cka-desktop-", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0:
            _running_containers_cache = set(r.stdout.strip().split())
            _last_container_cache_time = now
            return _running_containers_cache
    except Exception:
        pass
    return _running_containers_cache


def is_container_running(sid: Optional[str]) -> bool:
    """Checks whether the docker desktop container for the session is actively running (O(1) cached lookup)."""
    if not sid or sid == "None":
        return False
    container_name = f"cka-desktop-{sid}"
    running_set = get_running_desktop_containers()
    return container_name in running_set



# Idle timeout: auto-kill container + session after this many minutes of inactivity
IDLE_TIMEOUT_MINUTES: int = int(os.getenv("EXAM_IDLE_TIMEOUT_MINUTES", "30"))

# In-memory candidate token -> session_id mapping (supplements Redis for fast lookup)
# token -> session_id
_candidate_token_map: Dict[str, str] = {}


class ClientEventRequest(BaseModel):
    event_type: str
    data: Optional[Dict[str, Any]] = None


_selected_preset_override: Optional[str] = None


def _get_locked_preset_info(override_preset: Optional[str] = None) -> Dict[str, Any]:
    global _selected_preset_override
    default_cfg = redis_bus.get_default_preset() if redis_bus.is_available() else "mock-01-acme"
    preset_key = override_preset or _selected_preset_override or os.getenv("EXAM_PRESET") or default_cfg
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
    # Check query params for admin/candidate mode + candidate token routing
    url_admin = request.query_params.get("admin")
    url_candidate = request.query_params.get("candidate")
    url_preset = request.query_params.get("preset")
    url_token = request.query_params.get("token")  # Per-candidate session token

    admin_auth = is_admin_authenticated(request)
    if url_admin in ("1", "true", "yes") and admin_auth:
        is_admin = True
    else:
        is_admin = False

    # Candidate token routing: resolve session_id from token
    session = None
    if url_token:
        sid_for_token = _candidate_token_map.get(url_token)
        if not sid_for_token and redis_bus.is_available():
            try:
                sid_val = redis_bus.get_sync_client().get(f"token:{url_token}")
                if sid_val:
                    sid_for_token = sid_val if isinstance(sid_val, str) else sid_val.decode()
            except Exception:
                pass
        if sid_for_token:
            state = redis_bus.get_session_state(sid_for_token)
            if state and state.get("status") == "active":
                q_ids = state.get("question_ids", [])
                questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
                from core.models import ExamSession
                session = ExamSession(
                    session_id=state.get("session_id", "default"),
                    created_at=state.get("created_at", ""),
                    name=state.get("name", "Active Practice Session"),
                    questions=questions,
                    target_contexts=state.get("target_contexts", []),
                    time_limit_minutes=state.get("time_limit_minutes"),
                    mode=state.get("mode", "batch"),
                    current_index=state.get("current_index", 0),
                    scores=state.get("scores", {}),
                    flagged=state.get("flagged", []),
                    scorecard=state.get("scorecard"),
                    status=state.get("status", "active"),
                    last_active_at=state.get("last_active_at"),
                    candidate_token=state.get("candidate_token"),
                )

    if session is None and not url_token:
        session = deployer.load_active_session(loader)
    elif session is None and url_token:
        active_s = deployer.load_active_session(loader)
        if active_s and getattr(active_s, "candidate_token", None) == url_token and active_s.status == "active":
            session = active_s

    # If no active session found but candidate token has an invitation
    if session is None and url_token:
        invitation = redis_bus.get_invitation(url_token)
        if invitation:
            assigned_preset = invitation.get("preset") or redis_bus.get_default_preset()
            preset_info = _get_locked_preset_info(assigned_preset)
            return {
                "active": False,
                "invited": True,
                "preset": assigned_preset,
                "token": url_token,
                "locked_preset": preset_info,
                "is_admin": is_admin,
            }

    preset_info = _get_locked_preset_info(url_preset)

    if not session:
        return {
            "active": False,
            "session": None,
            "locked_preset": preset_info,
            "is_admin": is_admin,
        }

    # Auto-Restore Container for Active Sessions
    if session and session.session_id and session.status == "active":
        if not is_container_running(session.session_id):
            res_info = get_system_resource_info()
            if res_info.get("available_mem_mb", 0) >= 350:
                print(f"[AutoRestore] Container for active session {session.session_id} was not running. Automatically restored.", flush=True)
                desktop_mgr.start_desktop(session.session_id)

    # Touch activity timestamp for idle timeout tracking
    now_utc = datetime.now(timezone.utc)
    try:
        session.last_active_at = now_utc.isoformat()
        deployer.save_session(session)
        redis_bus.touch_session_activity(session.session_id)
    except Exception:
        pass

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
        "candidate_token": session.candidate_token,
        "name": session.name,
        "mode": session.mode,
        "status": session.status,
        "current_index": cur_idx,
        "total_tasks": len(session.questions),
        "time_limit_minutes": session.time_limit_minutes,
        "time_remaining_seconds": time_remaining,
        "created_at": session.created_at,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "server_timestamp": now_utc.timestamp(),
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
    default_cfg = redis_bus.get_default_preset() if redis_bus.is_available() else "mock-01-acme"
    selected = _selected_preset_override or os.getenv("EXAM_PRESET") or default_cfg
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

    actor = "admin" if is_admin_authenticated(request) else "candidate"
    try:
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_JUMP", {"task_num": req.task_num, "actor": actor}, actor=actor)
    except Exception:
        pass

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
def action_retry(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.current_question:
        raise HTTPException(status_code=400, detail="No active question to retry")

    cur_idx = session.current_index
    actor = "admin" if is_admin_authenticated(request) else "candidate"
    try:
        cur_q = session.current_question
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_RETRY", {
            "task_num": cur_idx + 1,
            "question_id": cur_q.id if cur_q else None,
            "title": cur_q.title if cur_q else None,
            "actor": actor,
        }, actor=actor)
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

    try:
        if session and session.session_id:
            desktop_mgr.stop_desktop(session.session_id)
            redis_bus.archive_session(
                session.session_id,
                status="completed",
                scorecard={
                    "total_earned": total_earned,
                    "total_possible": total_possible,
                    "percentage": round(pct, 1),
                    "passed": passed,
                },
            )
    except Exception:
        pass

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
    cand_tok = req.candidate_token
    # If candidate token is provided, check if session already active for it
    if cand_tok:
        existing_sid = _candidate_token_map.get(cand_tok)
        if not existing_sid and redis_bus.is_available():
            try:
                sid_val = redis_bus.get_sync_client().get(f"token:{cand_tok}")
                if sid_val:
                    existing_sid = sid_val if isinstance(sid_val, str) else sid_val.decode()
            except Exception:
                pass
        if existing_sid:
            existing_session = deployer.load_active_session(loader)
            if existing_session and existing_session.session_id == existing_sid and existing_session.status == "active":
                return get_session(request)

    # Resource check before starting a new session / container
    old_session = deployer.load_active_session(loader)
    res_info = get_system_resource_info()
    running = res_info["running_containers"]
    max_sessions = res_info["max_concurrent_sessions"]
    avail_mem = res_info["available_mem_mb"]

    # Check if this start request is replacing an existing running desktop container
    is_replacing_running = False
    if old_session and old_session.session_id and is_container_running(old_session.session_id):
        is_replacing_running = True

    effective_running = (running - 1) if is_replacing_running else running

    if effective_running >= max_sessions or avail_mem < 350:
        raise HTTPException(
            status_code=429,
            detail=f"Server resource limit reached: Maximum concurrent sessions ({max_sessions}) currently active ({running} running). Please wait for an active session to finish or contact the administrator."
        )

    # Archive any currently active session before starting a new one
    if old_session and old_session.session_id:
        try:
            desktop_mgr.stop_desktop(old_session.session_id)
            redis_bus.archive_session(old_session.session_id, status="replaced")
        except Exception:
            pass

    # Preset selection: request preset > candidate invitation preset > global default
    preset_name = req.preset
    if cand_tok and not preset_name:
        inv = redis_bus.get_invitation(cand_tok)
        if inv and inv.get("preset"):
            preset_name = inv.get("preset")

    if not preset_name:
        preset_name = redis_bus.get_default_preset()

    if req.all_questions or preset_name == "all":
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

    if session and session.session_id:
        token = cand_tok or secrets.token_urlsafe(16)
        session.candidate_token = token
        session.status = "active"
        session.last_active_at = datetime.now(timezone.utc).isoformat()
        deployer.save_session(session)

        # Register token -> session_id mapping in memory and Redis
        _candidate_token_map[token] = session.session_id
        if redis_bus.is_available():
            try:
                redis_bus.get_sync_client().set(
                    f"token:{token}", session.session_id, ex=86400
                )
                if cand_tok:
                    redis_bus.update_invitation(cand_tok, {
                        "status": "started",
                        "session_id": session.session_id,
                        "started_at": time.time(),
                    })
            except Exception:
                pass

        redis_bus.touch_session_activity(session.session_id)
        desktop_mgr.start_desktop(session.session_id)

    return get_session(request)


class RestoreSessionRequest(BaseModel):
    session_id: str


@app.post("/api/session/restore")
def restore_session(req: RestoreSessionRequest, request: Request):
    session_id = req.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    # Check resource limit before restoring
    res_info = get_system_resource_info()
    running = res_info["running_containers"]
    max_sessions = res_info["max_concurrent_sessions"]
    avail_mem = res_info["available_mem_mb"]

    is_already_running = is_container_running(session_id)
    effective_running = (running - 1) if is_already_running else running

    if effective_running >= max_sessions or avail_mem < 350:
        raise HTTPException(
            status_code=429,
            detail=f"Server resource limit reached: Maximum concurrent sessions ({max_sessions}) currently active ({running} running). Please wait for an active session to finish or contact the administrator."
        )

    # Retrieve archived session from Redis history:{session_id} or file archive
    data = None
    if redis_bus.is_available():
        data = redis_bus.get_archived_session(session_id)
        if not data:
            try:
                raw = redis_bus.get_sync_client().get(f"session:{session_id}")
                if raw:
                    data = json.loads(raw)
            except Exception:
                pass

    if not data:
        archive_p = BASE_DIR / "var" / "archive" / f"{session_id}.json"
        if archive_p.exists():
            try:
                data = json.loads(archive_p.read_text(encoding="utf-8"))
            except Exception:
                pass
        elif deployer.session_file.exists():
            try:
                s_data = json.loads(deployer.session_file.read_text(encoding="utf-8"))
                if s_data.get("session_id") == session_id:
                    data = s_data
            except Exception:
                pass

    if not data:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found in history or archive")

    q_ids = data.get("question_ids", [])
    questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]

    session = ExamSession(
        session_id=session_id,
        created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        name=data.get("name", "Restored Exam Session"),
        questions=questions,
        target_contexts=data.get("target_contexts", []),
        time_limit_minutes=data.get("time_limit_minutes"),
        mode=data.get("mode", "sequential"),
        current_index=data.get("current_index", 0),
        scores=data.get("scores", {}),
        flagged=data.get("flagged", []),
        scorecard=data.get("scorecard"),
        status="active",
        last_active_at=datetime.now(timezone.utc).isoformat(),
        candidate_token=data.get("candidate_token"),
    )

    # Revive session as active session in Redis & deployer.save_session
    deployer.save_session(session)
    if redis_bus.is_available():
        redis_bus.set_session_state(session_id, session.to_dict())
        redis_bus.register_active_session(session_id, session.to_dict())
        if session.candidate_token:
            _candidate_token_map[session.candidate_token] = session_id
            try:
                redis_bus.get_sync_client().set(f"token:{session.candidate_token}", session_id, ex=86400)
            except Exception:
                pass
        redis_bus.touch_session_activity(session_id)

    # Start desktop container
    desktop_mgr.start_desktop(session_id)

    actor = "admin" if is_admin_authenticated(request) else "candidate"
    try:
        recorder.attach_or_resume(session_id, session.name)
        recorder.log_event("SESSION_RESTORED", {"session_id": session_id, "actor": actor}, actor=actor)
    except Exception:
        pass

    print(f"[SessionRestore] Restored and revived session {session_id}", flush=True)
    return get_session(request)


@app.post("/api/reset")
def reset_exam(request: Request):
    actor = "admin" if is_admin_authenticated(request) else "candidate"
    active_session = deployer.load_active_session(loader)
    if active_session and active_session.session_id:
        try:
            recorder.attach_or_resume(active_session.session_id, active_session.name)
            recorder.log_event("EXAM_RESET", {"actor": actor}, actor=actor)
        except Exception:
            pass
        desktop_mgr.stop_desktop(active_session.session_id)
        try:
            redis_bus.archive_session(active_session.session_id, status="reset")
        except Exception:
            pass
    deployer.clear_session(cleanup_cluster=True)
    return {"status": "ok", "message": "Exam session cleared and cluster cleaned"}


@app.get("/api/sessions")
def list_sessions():
    """Returns session history (all past + current sessions) from Redis archive."""
    history = redis_bus.list_session_history(limit=50)
    # Also include any currently active session
    current = deployer.load_active_session(loader)
    if current:
        history.insert(0, {
            "session_id": current.session_id,
            "name": current.name,
            "status": current.status or "active",
            "created_at": current.created_at,
            "archived_at": None,
            "total_tasks": len(current.questions),
            "time_limit_minutes": current.time_limit_minutes,
            "time_remaining_seconds": _calculate_time_remaining(current),
            "scorecard_summary": None,
            "candidate_token": current.candidate_token,
        })
    return {"sessions": history, "total": len(history)}


# --- Admin Plane Endpoints ---

@app.post("/api/admin/login")
def admin_login(req: AdminLoginRequest, response: Response):
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    token = secrets.token_urlsafe(32)
    _admin_tokens.add(token)
    redis_bus.store_admin_token(token, expires_in=86400 * 7)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        path="/",
        samesite="lax",
    )
    return {"status": "ok", "token": token, "authenticated": True}


@app.get("/api/admin/check")
def admin_check(request: Request):
    return {"authenticated": is_admin_authenticated(request)}


@app.post("/api/admin/logout")
def admin_logout(request: Request, response: Response):
    cookie_token = request.cookies.get("admin_token")
    if cookie_token:
        _admin_tokens.discard(cookie_token)
        redis_bus.revoke_admin_token(cookie_token)
    auth_header = request.headers.get("authorization", "") or request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        t = auth_header[7:].strip()
        _admin_tokens.discard(t)
        redis_bus.revoke_admin_token(t)
    response.delete_cookie(key="admin_token", path="/")
    return {"status": "ok", "authenticated": False}


@app.get("/api/admin/config")
def admin_get_config(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    preset = redis_bus.get_default_preset()
    return {"default_preset": preset}


@app.post("/api/admin/config")
def admin_set_config(req: AdminConfigRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    redis_bus.set_default_preset(req.default_preset)
    return {"status": "ok", "default_preset": req.default_preset}


class SetResourceLimitRequest(BaseModel):
    max_concurrent_sessions: int


@app.get("/api/admin/resources")
def admin_get_resources(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_system_resource_info()


@app.post("/api/admin/resources")
def admin_set_resources(req: SetResourceLimitRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if req.max_concurrent_sessions < 1:
        raise HTTPException(status_code=400, detail="max_concurrent_sessions must be at least 1")
    redis_bus.set_max_concurrent_sessions(req.max_concurrent_sessions)
    return get_system_resource_info()


@app.post("/api/admin/sessions/create")
def admin_create_session_invite(req: CreateSessionInviteRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    res_info = get_system_resource_info()
    if res_info["running_containers"] >= res_info["max_concurrent_sessions"] or res_info["available_mem_mb"] < 350:
        raise HTTPException(
            status_code=429,
            detail=f"Server resource limit reached: Maximum concurrent sessions ({res_info['max_concurrent_sessions']}) currently active ({res_info['running_containers']} running). Please wait for an active session to finish or contact the administrator."
        )

    preset = req.preset or redis_bus.get_default_preset()
    token = secrets.token_urlsafe(16)
    redis_bus.create_invitation(token, preset)
    return {
        "token": token,
        "preset": preset,
        "url": f"/?token={token}",
    }


@app.get("/api/admin/sessions")
def admin_list_sessions(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    items = []
    seen_tokens = set()
    seen_sids = set()

    # 1. Active session
    active_s = deployer.load_active_session(loader)
    if active_s and active_s.status == "active":
        sid = active_s.session_id
        seen_sids.add(sid)
        if active_s.candidate_token:
            seen_tokens.add(active_s.candidate_token)
        rem = _calculate_time_remaining(active_s)
        items.append({
            "session_id": sid,
            "candidate_token": active_s.candidate_token,
            "name": active_s.name,
            "status": "active",
            "created_at": active_s.created_at,
            "time_remaining_seconds": rem,
            "container_running": is_container_running(sid),
            "total_tasks": len(active_s.questions),
            "current_index": active_s.current_index,
            "type": "active",
            "url": f"/?token={active_s.candidate_token}" if active_s.candidate_token else "/",
        })

    # 2. Invitations
    invitations = redis_bus.list_invitations()
    now_ts = time.time()
    for inv in invitations:
        token = inv.get("token")
        status = inv.get("status", "pending")
        created_ts = inv.get("created_at") or now_ts

        # Automatically expire pending invites older than 24 hours (86400s)
        if status == "pending" and (now_ts - created_ts > 86400):
            status = "expired"
            try:
                redis_bus.update_invitation(token, {"status": "expired"})
            except Exception:
                pass

        if status in ("pending", "expired") or (token not in seen_tokens and status != "started"):
            seen_tokens.add(token)
            created_str = datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat() if created_ts else ""
            items.append({
                "session_id": None,
                "candidate_token": token,
                "name": inv.get("preset", "Default Preset"),
                "status": status,
                "created_at": created_str,
                "time_remaining_seconds": None,
                "container_running": False,
                "total_tasks": None,
                "current_index": None,
                "type": "invite",
                "url": f"/?token={token}",
            })

    # 3. History
    history = redis_bus.list_session_history(limit=50)
    for h in history:
        sid = h.get("session_id")
        if sid and sid not in seen_sids:
            seen_sids.add(sid)
            tok = h.get("candidate_token")
            if tok:
                seen_tokens.add(tok)
            items.append({
                "session_id": sid,
                "candidate_token": tok,
                "name": h.get("name", "Exam Session"),
                "status": h.get("status", "completed"),
                "created_at": h.get("created_at", ""),
                "archived_at": h.get("archived_at"),
                "time_remaining_seconds": 0,
                "container_running": is_container_running(sid),
                "total_tasks": h.get("total_tasks", 0),
                "scorecard_summary": h.get("scorecard_summary"),
                "type": "archived",
                "url": f"/?token={tok}" if tok else None,
            })

    return {"sessions": items, "total": len(items)}


@app.get("/api/admin/session/{session_id}")
def admin_get_session_detail(session_id: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    state = redis_bus.get_session_state(session_id)
    if not state:
        current = deployer.load_active_session(loader)
        if current and current.session_id == session_id:
            state = current.to_dict()
    if not state and redis_bus.is_available():
        client = redis_bus.get_sync_client()
        raw = client.get(f"history:{session_id}")
        if raw:
            try:
                state = json.loads(raw)
            except Exception:
                pass

    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    q_ids = state.get("question_ids", [])
    questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
    cur_idx = state.get("current_index", 0)
    current_q = questions[cur_idx] if 0 <= cur_idx < len(questions) else None

    task_data = None
    if current_q:
        task_data = {
            "task_num": cur_idx + 1,
            "id": current_q.id,
            "title": current_q.title,
            "domain": current_q.domain.value if hasattr(current_q.domain, "value") else str(current_q.domain),
            "difficulty": current_q.difficulty.value if hasattr(current_q.difficulty, "value") else str(current_q.difficulty),
            "points": current_q.points,
            "target_context": current_q.target_context,
            "namespace": current_q.namespace or "default",
            "description": current_q.description,
            "is_flagged": current_q.id in state.get("flagged", []),
            "score_data": state.get("scores", {}).get(current_q.id),
        }

    return {
        "session_id": session_id,
        "candidate_token": state.get("candidate_token"),
        "name": state.get("name"),
        "status": state.get("status", "active"),
        "current_index": cur_idx,
        "total_tasks": len(questions),
        "time_limit_minutes": state.get("time_limit_minutes"),
        "created_at": state.get("created_at"),
        "current_task": task_data,
        "container_running": is_container_running(session_id),
        "questions": [
            {
                "task_num": i + 1,
                "id": q.id,
                "title": q.title,
                "points": q.points,
                "is_current": i == cur_idx,
                "is_flagged": q.id in state.get("flagged", []),
                "score_data": state.get("scores", {}).get(q.id),
            }
            for i, q in enumerate(questions)
        ]
    }


@app.post("/api/admin/sessions/{identifier}/terminate")
def admin_terminate_session(identifier: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        recorder.attach_or_resume(identifier)
        recorder.log_event("ADMIN_SESSION_TERMINATE", {"session_id": identifier, "actor": "admin"}, actor="admin")
    except Exception:
        pass

    desktop_mgr.stop_desktop(identifier)
    redis_bus.archive_session(identifier, status="terminated")

    active_s = deployer.load_active_session(loader)
    if active_s and active_s.session_id == identifier:
        deployer.clear_session(cleanup_cluster=False)

    redis_bus.delete_invitation(identifier)
    if redis_bus.is_available():
        try:
            client = redis_bus.get_sync_client()
            client.delete(f"history:{identifier}")
            client.delete(f"token:{identifier}")
            client.delete(f"session:{identifier}")
            client.delete(f"session:{identifier}:state")
        except Exception:
            pass
    return {"status": "ok", "message": f"Session or invite {identifier} deleted/terminated"}


@app.post("/api/admin/sessions/{identifier}/reset")
def admin_reset_session(identifier: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        recorder.attach_or_resume(identifier)
        recorder.log_event("ADMIN_EXAM_RESET", {"session_id": identifier, "actor": "admin"}, actor="admin")
    except Exception:
        pass

    desktop_mgr.stop_desktop(identifier)
    redis_bus.archive_session(identifier, status="reset")

    active_s = deployer.load_active_session(loader)
    if active_s and active_s.session_id == identifier:
        deployer.clear_session(cleanup_cluster=True)

    return {"status": "ok", "message": f"Session {identifier} reset and cluster cleaned"}


@app.post("/api/admin/sessions/{identifier}/end")
def admin_end_session(identifier: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        recorder.attach_or_resume(identifier)
        recorder.log_event("ADMIN_EXAM_END", {"session_id": identifier, "actor": "admin"}, actor="admin")
    except Exception:
        pass

    active_s = deployer.load_active_session(loader)
    scorecard = None
    if active_s and active_s.session_id == identifier:
        scorecard = action_submit()
    else:
        desktop_mgr.stop_desktop(identifier)
        redis_bus.archive_session(identifier, status="submitted")

    return {"status": "ok", "message": f"Session {identifier} ended and evaluated", "scorecard": scorecard}


# --- Built-in WebSocket PTY Terminal ---

@app.websocket("/ws/terminal")
@app.websocket("/ws/terminal/{session_id}")
async def terminal_websocket(websocket: WebSocket, session_id: Optional[str] = None):
    await websocket.accept()

    is_admin = is_admin_authenticated(websocket)
    actor = "admin" if is_admin else "candidate"
    param_sid = session_id or websocket.query_params.get("session_id")
    if is_admin and param_sid:
        sid = param_sid
        session = None
    else:
        session = deployer.load_active_session(loader)
        sid = session.session_id if session else "default"

    if session:
        try:
            recorder.attach_or_resume(session.session_id, session.name)
            recorder.log_event("ADMIN_TERMINAL_ATTACH" if is_admin else "TERMINAL_ATTACH", {"session_id": session.session_id, "actor": actor}, actor=actor)
        except Exception:
            pass
    elif is_admin and sid:
        try:
            recorder.attach_or_resume(sid)
            recorder.log_event("ADMIN_TERMINAL_ATTACH", {"session_id": sid, "actor": "admin"}, actor="admin")
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
        container_name = f"cka-desktop-{sid}"
        use_container = False
        if desktop_mgr.is_docker_available():
            try:
                r = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                if r.returncode == 0 and "true" in r.stdout.lower():
                    use_container = True
            except Exception:
                pass

        if use_container:
            try:
                os.setpgid(0, 0)
                termios.tcsetpgrp(0, os.getpgrp())
            except Exception:
                pass
            docker_cmd = [
                "docker", "exec", "-it",
                "-u", "exam",
                "-e", "TERM=xterm-256color",
                "-e", "COLORTERM=truecolor",
                "-e", "EXAM_RECORDED=1",
                "-e", "WEB_TERMINAL=1",
                container_name,
                "bash", "-l",
            ]
            os.execvp("docker", docker_cmd)

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
                            recorder.record_input(msg["bytes"], actor=actor)
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
                                recorder.record_input(raw_b, actor=actor)
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
            recorder.log_event("ADMIN_TERMINAL_DETACH" if is_admin else "TERMINAL_DETACH", {"session_id": sid, "actor": actor}, actor=actor)
        except Exception:
            pass

        try:
            os.close(master_fd)
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        except Exception:
            pass


# --- Integrated noVNC WebSocket Proxy ---

async def _proxy_vnc(websocket: WebSocket, session_id: Optional[str] = None):
    requested_proto = websocket.headers.get("sec-websocket-protocol", "")
    subprotocol = "binary" if "binary" in requested_proto else None
    await websocket.accept(subprotocol=subprotocol)

    is_admin_mode = is_admin_authenticated(websocket)

    # Resolve active session
    active_sid = None
    try:
        client = redis_bus.get_sync_client()
        if client:
            real_sid = client.get("session:active:id")
            if real_sid:
                active_sid = real_sid.decode() if isinstance(real_sid, bytes) else real_sid
    except Exception:
        pass

    sid = session_id
    if not sid or sid == "active":
        sid = active_sid

    # Security check: candidates can ONLY access their own active session
    if not is_admin_mode:
        if not sid or (active_sid and sid != active_sid):
            print(f"[VNC Proxy] Forbidden: Candidate attempted to access unauthorized session {session_id} (active: {active_sid})", flush=True)
            await websocket.close(code=1008)
            return

    target_host = None
    target_port = 5901

    if sid:
        # Auto-Restore Container for Active Sessions:
        if not is_container_running(sid):
            res_info = get_system_resource_info()
            if res_info.get("available_mem_mb", 0) >= 350:
                print(f"[AutoRestore] Container for active session {sid} was not running. Automatically restored.", flush=True)
                desktop_mgr.start_desktop(sid)

        # Check Redis registration, wait up to 8s if container is currently registering
        for _ in range(16):
            desktop_info = redis_bus.get_desktop_info(sid)
            if desktop_info and "host" in desktop_info:
                h = desktop_info["host"]
                # Candidates must never connect to host loopback
                if not is_admin_mode and (h == "127.0.0.1" or h == "localhost"):
                    pass
                else:
                    target_host = h
                    target_port = int(desktop_info.get("vnc_port", 5901))
                    break
            await asyncio.sleep(0.5)

    if not target_host:
        if is_admin_mode:
            target_host = "127.0.0.1"
            target_port = 5901
        else:
            print(f"[VNC Proxy] Connection rejected: Container desktop for session {sid} is unavailable (host fallback is disabled for candidates)", flush=True)
            await websocket.close(code=1008)
            return

    try:
        reader, writer = await asyncio.open_connection(target_host, target_port)
        print(f"[VNC Proxy] Connected to VNC at {target_host}:{target_port} (session: {session_id or 'default'}, resolved_sid: {sid})", flush=True)
    except Exception as e:
        print(f"[VNC Proxy] Failed to connect to VNC target {target_host}:{target_port}: {e}", flush=True)
        await websocket.close()
        return

    async def client_to_vnc():
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if "bytes" in msg and msg["bytes"]:
                    writer.write(msg["bytes"])
                    await writer.drain()
                elif "text" in msg and msg["text"]:
                    writer.write(msg["text"].encode("latin1"))
                    await writer.drain()
        except Exception:
            pass
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
                    break
                await websocket.send_bytes(data)
        except Exception:
            pass
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


@app.websocket("/ws/desktop/{session_id}")
@app.websocket("/novnc/ws/desktop/{session_id}")
async def vnc_ws_dynamic_desktop(websocket: WebSocket, session_id: str):
    await _proxy_vnc(websocket, session_id=session_id)


@app.websocket("/ws/desktop")
@app.websocket("/novnc/ws/desktop")
async def vnc_ws_dynamic_desktop_default(websocket: WebSocket):
    await _proxy_vnc(websocket, session_id=None)


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

                    # Touch activity for any message to reset idle timeout
                    try:
                        target = session_id
                        if target == "active":
                            s = deployer.load_active_session(loader)
                            target = s.session_id if s else "default"
                        redis_bus.touch_session_activity(target)
                    except Exception:
                        pass
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


# --- Background Workers: Host Clipboard, Timer Broadcast, Idle Reaper, Timer Expiry ---

_last_x11_clipboard = ""

@app.on_event("startup")
async def start_background_workers():
    # 1. Initial scan: warm up question catalog and kubectl completion in Redis
    loop = asyncio.get_running_loop()
    def warm_up_cache():
        try:
            print("[Startup] Scanning question catalog into Redis...", flush=True)
            loader.reload(use_cache=False)
            count = len(loader.all())
            print(f"[Startup] Question catalog pre-warmed: {count} questions cached in Redis.", flush=True)
        except Exception as ex:
            print(f"[Startup] Catalog cache warm-up error: {ex}", flush=True)

        # Pre-cache kubectl completion in Redis and write to /etc/bash_completion.d/kubectl
        try:
            comp = redis_bus.get_kubectl_completion()
            if not comp:
                r = subprocess.run(["kubectl", "completion", "bash"], capture_output=True, text=True, timeout=10)
                if r.returncode == 0 and r.stdout:
                    comp = r.stdout
                    redis_bus.cache_kubectl_completion(comp)
            if comp:
                p = Path("/etc/bash_completion.d/kubectl")
                if not p.exists() or p.stat().st_size == 0:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(comp, encoding="utf-8")
        except Exception:
            pass

    async def _run_warmup():
        await loop.run_in_executor(None, warm_up_cache)

    asyncio.create_task(_run_warmup())

    asyncio.create_task(_clipboard_x11_monitor())
    asyncio.create_task(_session_timer_broadcaster())
    asyncio.create_task(_idle_session_reaper())
    asyncio.create_task(_session_expiry_enforcer())


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
async def _idle_session_reaper():
    """Auto-terminates a candidate session if idle for IDLE_TIMEOUT_MINUTES with no activity."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        try:
            session = deployer.load_active_session(loader)
            if not session or not session.session_id:
                continue

            last_active = redis_bus.get_session_last_active(session.session_id)
            if last_active is None:
                # No activity record yet; seed it now
                redis_bus.touch_session_activity(session.session_id)
                continue

            idle_seconds = time.time() - last_active
            idle_limit_seconds = IDLE_TIMEOUT_MINUTES * 60
            if idle_seconds >= idle_limit_seconds:
                print(
                    f"[SessionReaper] Session {session.session_id} idle for "
                    f"{int(idle_seconds)}s (limit {idle_limit_seconds}s). Terminating."
                )
                try:
                    await redis_bus.async_publish_session_event(session.session_id, {
                        "type": "session_expired",
                        "reason": "idle_timeout",
                        "idle_seconds": int(idle_seconds),
                        "message": f"Session expired due to {IDLE_TIMEOUT_MINUTES} minutes of inactivity.",
                    })
                except Exception:
                    pass
                await asyncio.sleep(2)  # Give WS clients time to receive the event
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: (
                    desktop_mgr.stop_desktop(session.session_id),
                    redis_bus.archive_session(session.session_id, status="idle_timeout"),
                    deployer.clear_session(cleanup_cluster=False),
                ))
        except Exception as e:
            print(f"[SessionReaper] Error: {e}")


async def _session_expiry_enforcer():
    """Server-side enforcement: terminates session when time_remaining hits zero."""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        try:
            session = deployer.load_active_session(loader)
            if not session or not session.session_id:
                continue
            if not session.time_limit_minutes:
                continue  # Untimed session

            rem = _calculate_time_remaining(session)
            if rem is not None and rem <= 0:
                print(
                    f"[ExpiryEnforcer] Session {session.session_id} time limit reached. Auto-submitting."
                )
                try:
                    await redis_bus.async_publish_session_event(session.session_id, {
                        "type": "session_expired",
                        "reason": "time_limit",
                        "message": "Exam time limit reached. Session auto-submitted.",
                    })
                except Exception:
                    pass
                await asyncio.sleep(2)
                # Archive as expired (not graded since we don't have full grading context async)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: (
                    desktop_mgr.stop_desktop(session.session_id),
                    redis_bus.archive_session(session.session_id, status="expired"),
                    deployer.clear_session(cleanup_cluster=False),
                ))
        except Exception as e:
            print(f"[ExpiryEnforcer] Error: {e}")


# Admin dashboard route
@app.get("/admin", response_class=HTMLResponse)
def get_admin_page(request: Request):
    admin_html = STATIC_DIR / "admin.html"
    if admin_html.exists():
        return HTMLResponse(content=admin_html.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Admin page not found")


# Mount noVNC static files if present
NOVNC_DIR = Path("/usr/share/novnc")
if NOVNC_DIR.exists():
    app.mount("/novnc", StaticFiles(directory=str(NOVNC_DIR), html=True), name="novnc")

# Mount static directory for frontend web UI
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
