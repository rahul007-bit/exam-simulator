"""Unit tests for the dynamic preset generator (web/api/services/preset_generator.py).

Runs on a plain Windows dev box: no FastAPI, no Redis, no questions/ catalog.
The module is loaded directly from its file path so the fastapi-importing
web.api package __init__ is never executed. The real selector (web.api.state)
is never touched — a stub selector is injected into generate_questions.
Tests are skipped cleanly when the core package tree cannot be imported.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MODULE_PATH = REPO_ROOT / "web" / "api" / "services" / "preset_generator.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("preset_generator_under_test", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    from core.models import Difficulty, Domain, Question
    _pg = _load_module()
    generate_questions = _pg.generate_questions
    _CORE_OK = True
except Exception:
    _CORE_OK = False


def _make_question(qid: str, difficulty: str = "medium", domain: str = "troubleshooting"):
    return Question(
        id=qid,
        title=f"Task {qid}",
        domain=Domain(domain),
        difficulty=Difficulty(difficulty),
        points=3,
        target_context="k3d-cka",
        description="stub",
    )


class _StubSelector:
    def __init__(self, pool):
        self.pool = pool
        self.calls = []

    def select_custom(self, difficulties=None, domains=None, count=5, **kwargs):
        self.calls.append({"difficulties": difficulties, "domains": domains, "count": count})
        return list(self.pool)


@unittest.skipUnless(_CORE_OK, "core.models / web.api tree not importable on this box")
class GenerateQuestionsTests(unittest.TestCase):
    def test_count_zero_rejected(self):
        with self.assertRaises(ValueError):
            generate_questions(0, selector=_StubSelector([_make_question("q1")]))

    def test_count_over_50_rejected(self):
        with self.assertRaises(ValueError):
            generate_questions(51, selector=_StubSelector([_make_question("q1")]))

    def test_count_non_int_rejected(self):
        for bad in ("5", None, 2.5, True):
            with self.assertRaises(ValueError):
                generate_questions(bad, selector=_StubSelector([_make_question("q1")]))

    def test_count_boundaries_accepted(self):
        pool = [_make_question(f"q{i}") for i in range(5)]
        stub = _StubSelector(pool)
        self.assertEqual(len(generate_questions(1, selector=stub)), 1)
        self.assertEqual(len(generate_questions(50, selector=stub)), 5)

    def test_difficulty_case_insensitive(self):
        stub = _StubSelector([_make_question("q1", difficulty="easy")])
        result = generate_questions(2, difficulty="EaSy", selector=stub)
        self.assertEqual(len(result), 1)
        self.assertEqual(stub.calls[0]["difficulties"], [Difficulty.EASY])

    def test_difficulty_unknown_rejected(self):
        stub = _StubSelector([_make_question("q1")])
        with self.assertRaises(ValueError):
            generate_questions(3, difficulty="impossible", selector=stub)

    def test_domain_unknown_rejected(self):
        stub = _StubSelector([_make_question("q1")])
        with self.assertRaises(ValueError):
            generate_questions(3, domains=["storage", "bogus"], selector=stub)

    def test_domains_list_required(self):
        stub = _StubSelector([_make_question("q1")])
        with self.assertRaises(ValueError):
            generate_questions(3, domains="storage", selector=stub)

    def test_respects_count_truncation(self):
        pool = [_make_question(f"q{i}") for i in range(5)]
        stub = _StubSelector(pool)
        result = generate_questions(3, selector=stub)
        self.assertEqual(len(result), 3)
        result = generate_questions(7, selector=stub)
        self.assertEqual(len(result), 5)

    def test_empty_pool_rejected(self):
        stub = _StubSelector([])
        with self.assertRaises(ValueError) as ctx:
            generate_questions(3, selector=stub)
        self.assertIn("no questions match the requested criteria", str(ctx.exception))

    def test_enum_mapping_passed_to_selector(self):
        pool = [_make_question("q1", difficulty="hard", domain="security")]
        stub = _StubSelector(pool)
        generate_questions(4, difficulty="hard", domains=["security"], selector=stub)
        self.assertEqual(stub.calls[0]["difficulties"], [Difficulty.HARD])
        self.assertEqual(stub.calls[0]["domains"], [Domain.SECURITY])
        self.assertEqual(stub.calls[0]["count"], 4)

    def test_none_inputs_passed_as_none(self):
        stub = _StubSelector([_make_question("q1")])
        generate_questions(2, selector=stub)
        self.assertIsNone(stub.calls[0]["difficulties"])
        self.assertIsNone(stub.calls[0]["domains"])
        self.assertEqual(stub.calls[0]["count"], 2)


if __name__ == "__main__":
    unittest.main()
