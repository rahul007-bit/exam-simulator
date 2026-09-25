from typing import List, Optional

from core.models import Difficulty, Domain, Question

DIFFICULTY_VALUES = {d.value: d for d in Difficulty}
DOMAIN_VALUES = {d.value: d for d in Domain}


def generate_questions(
    count: int,
    difficulty: Optional[str] = None,
    domains: Optional[List[str]] = None,
    selector=None,
) -> List[Question]:
    """Selects questions by difficulty/domain for an ephemeral generated preset.

    Pure logic: validates inputs, maps strings to the core.enums and delegates
    to QuestionSelector.select_custom. Raises ValueError so the route can
    return a 400.
    """
    if not isinstance(count, int) or isinstance(count, bool) or not (1 <= count <= 50):
        raise ValueError("count must be an integer between 1 and 50")

    difficulties: Optional[List[Difficulty]] = None
    if difficulty is not None:
        d_key = str(difficulty).strip().lower()
        if d_key not in DIFFICULTY_VALUES:
            raise ValueError(f"Unknown difficulty '{difficulty}' (expected one of: {', '.join(DIFFICULTY_VALUES)})")
        difficulties = [DIFFICULTY_VALUES[d_key]]

    domain_enums: Optional[List[Domain]] = None
    if domains is not None:
        if not isinstance(domains, list):
            raise ValueError("domains must be a list of domain values")
        domain_enums = []
        for d in domains:
            d_key = str(d).strip().lower()
            if d_key not in DOMAIN_VALUES:
                raise ValueError(f"Unknown domain '{d}' (expected one of: {', '.join(DOMAIN_VALUES)})")
            domain_enums.append(DOMAIN_VALUES[d_key])

    if selector is None:
        from web.api.state import selector as default_selector

        selector = default_selector

    questions = selector.select_custom(
        difficulties=difficulties,
        domains=domain_enums,
        count=count,
    )
    if not questions:
        raise ValueError("no questions match the requested criteria")
    return list(questions)[:count]
