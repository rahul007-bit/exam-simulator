import os
from pathlib import Path

from core.loader import QuestionLoader
from core.selector import QuestionSelector
from core.deployer import LabDeployer
from core.grader import LabGrader

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Built Vue SPA (FE-003). Produced by the frontend build on deploy; the output is
# not committed (D-005). Since the FE-040 cutover it is the ONLY UI served: when
# the build is absent the server returns 503 until web/dist exists.
DIST_DIR = BASE_DIR / "web" / "dist"
SPA_INDEX = DIST_DIR / "index.html"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RECORDINGS_DIR = BASE_DIR / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

loader = QuestionLoader(BASE_DIR / "questions")
selector = QuestionSelector(loader, BASE_DIR / "presets")
deployer = LabDeployer(BASE_DIR / "var" / "session.json", BASE_DIR / "sets")
grader = LabGrader()

# Idle timeout: auto-kill container + session after this many minutes of inactivity
IDLE_TIMEOUT_MINUTES: int = int(os.getenv("EXAM_IDLE_TIMEOUT_MINUTES", "30"))
