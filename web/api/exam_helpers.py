from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.models import ExamSession, Question


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
