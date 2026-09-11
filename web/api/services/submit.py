import json
from datetime import datetime, timezone

from fastapi import HTTPException

from core.recorder import recorder
from core.redis_bus import bus as redis_bus
from core.sandbox_orchestrator import orchestrator

from web.api.state import REPORTS_DIR, deployer, grader, loader
from web.api.owner_lock import _clear_owner, _enforce_owner


def perform_submit(request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")
    _enforce_owner(request, session.session_id)

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
            # Archive FIRST: it snapshots the session state blob (name,
            # created_at, candidate_token, total_tasks) for the admin history
            # list — teardown deletes that blob, so archiving after teardown
            # produced "Unknown" rows with no creation date.
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
            orchestrator.teardown_session(session.session_id)
            deployer.clear_active_session()
            _clear_owner(session.session_id)
    except Exception:
        pass



    return report_data
