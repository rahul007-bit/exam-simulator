import random
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.models import Question, Difficulty, Domain
from core.loader import QuestionLoader


class QuestionSelector:
    def __init__(self, loader: QuestionLoader, presets_dir: Optional[Path] = None):
        self.loader = loader
        self.presets_dir = presets_dir or (Path(__file__).parent.parent / "presets")

    def load_preset(self, preset_name: str) -> Optional[Dict[str, Any]]:
        preset_clean = preset_name.replace(".yaml", "").replace(".yml", "")
        # Exact file match
        direct = self.presets_dir / f"{preset_clean}.yaml"
        if direct.exists():
            with open(direct, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

        # Dynamic search in presets_dir
        if self.presets_dir.exists():
            for p in sorted(self.presets_dir.glob("*.yaml")):
                if preset_clean in p.stem or p.stem in preset_clean:
                    with open(p, "r", encoding="utf-8") as f:
                        return yaml.safe_load(f)
        return None

    def list_presets(self) -> List[Dict[str, Any]]:
        presets = []
        if self.presets_dir.exists():
            for p_file in sorted(self.presets_dir.glob("*.yaml")):
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data and isinstance(data, dict):
                            data["filename"] = p_file.stem
                            presets.append(data)
                except Exception:
                    pass
        return presets

    def select_preset(self, question_ids: List[str]) -> List[Question]:
        questions = []
        for q_id in question_ids:
            q = self.loader.get(q_id)
            if q:
                questions.append(q)
            else:
                print(f"[Warning] Question ID '{q_id}' not found in catalog.")
        return questions

    def select_custom(
        self,
        difficulties: Optional[List[Difficulty]] = None,
        domains: Optional[List[Domain]] = None,
        target_contexts: Optional[List[str]] = None,
        count: int = 5,
        avoid_cluster_conflict: bool = True,
    ) -> List[Question]:
        pool = self.loader.filter(
            difficulties=difficulties,
            domains=domains,
            target_contexts=target_contexts,
        )
        if not pool:
            return []

        random.shuffle(pool)
        selected: List[Question] = []
        used_cluster_scoped = False

        for q in pool:
            if avoid_cluster_conflict and q.cluster_scoped:
                if used_cluster_scoped:
                    continue
                used_cluster_scoped = True
            selected.append(q)
            if len(selected) >= count:
                break

        return selected

    def select_mock_exam(self, target_count: int = 17) -> List[Question]:
        all_q = self.loader.all()
        if len(all_q) < target_count:
            return all_q[:target_count]

        em = [q for q in all_q if q.difficulty in (Difficulty.EASY, Difficulty.MEDIUM)]
        tr_pool = [q for q in em if q.domain == Domain.TROUBLESHOOTING]
        other_pool = [q for q in em if q.domain != Domain.TROUBLESHOOTING]
        random.shuffle(tr_pool)
        random.shuffle(other_pool)

        def by_diff(pool: List[Question], d: Difficulty) -> List[Question]:
            return [q for q in pool if q.difficulty == d]

        # Target mix: 7 easy / 10 medium with troubleshooting at ~60%.
        quotas = [
            (by_diff(tr_pool, Difficulty.EASY), 4),
            (by_diff(tr_pool, Difficulty.MEDIUM), 6),
            (by_diff(other_pool, Difficulty.EASY), 3),
            (by_diff(other_pool, Difficulty.MEDIUM), 4),
        ]

        selected: List[Question] = []
        used = set()
        leftovers: List[Question] = []
        for pool, want in quotas:
            take = pool[:want]
            selected.extend(take)
            used.update(id(q) for q in take)
            leftovers.extend(pool[want:])

        # Top up toward the 10-medium / 7-easy target when buckets ran dry.
        if len(selected) < target_count:
            spares = [q for q in leftovers + em if id(q) not in used]
            dedup: List[Question] = []
            seen = set()
            for q in spares:
                if id(q) not in seen:
                    seen.add(id(q))
                    dedup.append(q)
            for d in (Difficulty.MEDIUM, Difficulty.EASY):
                if len(selected) >= target_count:
                    break
                bucket = [q for q in dedup if q.difficulty == d and id(q) not in used]
                selected.extend(bucket[: target_count - len(selected)])
                used.update(id(q) for q in bucket)

        return selected[:target_count]

    def select_crazy_gauntlet(self, count: int = 5) -> List[Question]:
        pool = self.loader.filter(difficulties=[Difficulty.CRAZY, Difficulty.HARD])
        random.shuffle(pool)
        return pool[:count]
