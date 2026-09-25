import os
from typing import Any, Dict, Optional

from core.loader import QuestionLoader  # noqa: F401  (typing only)
from core.redis_bus import bus as redis_bus
from core.selector import QuestionSelector  # noqa: F401  (typing only)

from web.api.state import loader, selector

# Admin-selectable preset override. Redis (preset:override) is the source of
# truth so all replicas agree; the in-memory copy is only a fallback for when
# Redis is unavailable. Cleared by /api/admin/config.
_selected_preset_override: Optional[str] = None

_OVERRIDE_KEY = "preset:override"


def _redis_get_override() -> Optional[str]:
    if not redis_bus.is_available():
        return None
    try:
        val = redis_bus.get_sync_client().get(_OVERRIDE_KEY)
        if isinstance(val, bytes):
            val = val.decode()
        return val or None
    except Exception:
        return None


def _redis_set_override(preset: Optional[str]) -> None:
    if not redis_bus.is_available():
        return
    try:
        client = redis_bus.get_sync_client()
        if preset:
            client.set(_OVERRIDE_KEY, preset)
        else:
            client.delete(_OVERRIDE_KEY)
    except Exception:
        pass


def get_selected_preset_override() -> Optional[str]:
    global _selected_preset_override
    redis_val = _redis_get_override()
    if redis_val is not None:
        _selected_preset_override = redis_val
        return redis_val
    return _selected_preset_override


def set_selected_preset_override(preset: str) -> None:
    global _selected_preset_override
    _selected_preset_override = preset
    _redis_set_override(preset)


def clear_selected_preset_override() -> None:
    global _selected_preset_override
    _selected_preset_override = None
    _redis_set_override(None)


def _get_locked_preset_info(override_preset: Optional[str] = None) -> Dict[str, Any]:
    default_cfg = redis_bus.get_default_preset() if redis_bus.is_available() else "mock-01-acme"
    preset_key = override_preset or get_selected_preset_override() or default_cfg or os.getenv("EXAM_PRESET") or "mock-01-acme"
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
