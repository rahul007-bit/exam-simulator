from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    CRAZY = "crazy"


class Domain(str, Enum):
    TROUBLESHOOTING = "troubleshooting"
    STORAGE = "storage"
    WORKLOADS = "workloads"
    CLUSTER_ARCH = "cluster-arch"
    SECURITY = "security"


@dataclass
class Question:
    id: str
    title: str
    domain: Domain
    difficulty: Difficulty
    points: int
    target_context: str
    description: str
    namespace: Optional[str] = None
    cluster_scoped: bool = False
    breaking: bool = False
    chain_id: Optional[str] = None
    chain_step: Optional[int] = None
    depends_on: Optional[str] = None
    preserve_state: bool = False
    tags: List[str] = field(default_factory=list)
    grader_hint: Optional[str] = None
    path: Optional[Path] = None

    @property
    def setup_script(self) -> Optional[Path]:
        if self.path and (self.path / "setup.sh").exists():
            return self.path / "setup.sh"
        return None

    @property
    def grader_script(self) -> Optional[Path]:
        if self.path and (self.path / "grader.py").exists():
            return self.path / "grader.py"
        return None

    @property
    def cleanup_script(self) -> Optional[Path]:
        if self.path and (self.path / "cleanup.sh").exists():
            return self.path / "cleanup.sh"
        if self.path and (self.path / "teardown.sh").exists():
            return self.path / "teardown.sh"
        return None

    @property
    def solution_file(self) -> Optional[Path]:
        if self.path and (self.path / "solution.md").exists():
            return self.path / "solution.md"
        return None


@dataclass
class GradeResult:
    passed: bool
    score: int
    max_score: int
    message: str
    details: Optional[Dict[str, Any]] = None
    skipped: bool = False


@dataclass
class TaskGradeSummary:
    task_num: int
    question: Question
    result: GradeResult


@dataclass
class ExamSession:
    session_id: str
    created_at: str
    name: str
    questions: List[Question]
    target_contexts: List[str]
    time_limit_minutes: Optional[int] = None
    mode: str = "batch"  # "batch" or "sequential"
    current_index: int = 0
    scores: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    flagged: List[str] = field(default_factory=list)
    scorecard: Optional[List[Dict[str, Any]]] = None

    @property
    def current_question(self) -> Optional[Question]:
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "name": self.name,
            "question_ids": [q.id for q in self.questions],
            "target_contexts": self.target_contexts,
            "time_limit_minutes": self.time_limit_minutes,
            "mode": self.mode,
            "current_index": self.current_index,
            "scores": self.scores,
            "flagged": self.flagged,
            "scorecard": self.scorecard,
        }
