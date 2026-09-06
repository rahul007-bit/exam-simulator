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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain.value if hasattr(self.domain, "value") else str(self.domain),
            "difficulty": self.difficulty.value if hasattr(self.difficulty, "value") else str(self.difficulty),
            "points": self.points,
            "target_context": self.target_context,
            "description": self.description,
            "namespace": self.namespace,
            "cluster_scoped": self.cluster_scoped,
            "breaking": self.breaking,
            "chain_id": self.chain_id,
            "chain_step": self.chain_step,
            "depends_on": self.depends_on,
            "preserve_state": self.preserve_state,
            "tags": self.tags,
            "grader_hint": self.grader_hint,
            "path": str(self.path) if self.path else None,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Question":
        return cls(
            id=d["id"],
            title=d.get("title", ""),
            domain=Domain(d.get("domain", "troubleshooting")),
            difficulty=Difficulty(d.get("difficulty", "medium")),
            points=int(d.get("points", 3)),
            target_context=d.get("target_context", "k3d-cka"),
            description=d.get("description", ""),
            namespace=d.get("namespace"),
            cluster_scoped=bool(d.get("cluster_scoped", False)),
            breaking=bool(d.get("breaking", False)),
            chain_id=d.get("chain_id"),
            chain_step=d.get("chain_step"),
            depends_on=d.get("depends_on"),
            preserve_state=bool(d.get("preserve_state", False)),
            tags=d.get("tags", []),
            grader_hint=d.get("grader_hint"),
            path=Path(d["path"]) if d.get("path") else None,
        )



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
    status: str = "active"          # "active" | "completed" | "expired" | "idle_timeout"
    last_active_at: Optional[str] = None  # ISO8601 UTC of last candidate activity
    candidate_token: Optional[str] = None  # Unique per-candidate URL token

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
            "status": self.status,
            "last_active_at": self.last_active_at,
            "candidate_token": self.candidate_token,
        }

