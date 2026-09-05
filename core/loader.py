import yaml
from pathlib import Path
from typing import List, Dict, Optional
from core.models import Question, Difficulty, Domain


class QuestionLoader:
    def __init__(self, questions_dir: Optional[Path] = None):
        self.questions_dir = questions_dir or (Path(__file__).parent.parent / "questions")
        self._registry: Dict[str, Question] = {}
        self.reload()

    def reload(self) -> None:
        self._registry.clear()
        if not self.questions_dir.exists():
            return

        for q_yaml in self.questions_dir.glob("**/question.yaml"):
            try:
                with open(q_yaml, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data or not isinstance(data, dict):
                    continue

                q_id = str(data.get("id")).strip()
                title = str(data.get("title", "")).strip()
                domain_val = Domain(str(data.get("domain", "troubleshooting")).strip())
                diff_val = Difficulty(str(data.get("difficulty", "medium")).strip())
                points = int(data.get("points", 3))
                target_context = str(data.get("target_context", "k3d-cka")).strip()
                description = str(data.get("description", "")).strip()
                namespace = data.get("namespace")
                cluster_scoped = bool(data.get("cluster_scoped", False))
                breaking = bool(data.get("breaking", False))
                chain_id = data.get("chain_id")
                chain_step = int(data.get("chain_step")) if data.get("chain_step") is not None else None
                depends_on = data.get("depends_on")
                preserve_state = bool(data.get("preserve_state", False))
                tags = data.get("tags", [])
                grader_hint = data.get("grader_hint")

                q = Question(
                    id=q_id,
                    title=title,
                    domain=domain_val,
                    difficulty=diff_val,
                    points=points,
                    target_context=target_context,
                    description=description,
                    namespace=namespace,
                    cluster_scoped=cluster_scoped,
                    breaking=breaking,
                    chain_id=chain_id,
                    chain_step=chain_step,
                    depends_on=depends_on,
                    preserve_state=preserve_state,
                    tags=tags,
                    grader_hint=grader_hint,
                    path=q_yaml.parent,
                )
                self._registry[q_id] = q
            except Exception as e:
                print(f"[Warning] Failed to load {q_yaml}: {e}")

    def get(self, question_id: str) -> Optional[Question]:
        return self._registry.get(question_id)

    def all(self) -> List[Question]:
        return list(self._registry.values())

    def get_all(self) -> List[Question]:
        return self.all()

    def get_chain(self, chain_id: str) -> List[Question]:
        questions = [q for q in self._registry.values() if q.chain_id == chain_id]
        return sorted(questions, key=lambda q: q.chain_step or 0)

    def filter(
        self,
        difficulties: Optional[List[Difficulty]] = None,
        domains: Optional[List[Domain]] = None,
        target_contexts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Question]:
        results = []
        for q in self._registry.values():
            if difficulties and q.difficulty not in difficulties:
                continue
            if domains and q.domain not in domains:
                continue
            if target_contexts and q.target_context not in target_contexts:
                continue
            if tags and not any(tag in q.tags for tag in tags):
                continue
            results.append(q)
        return results
