# EVIDENCE — FE-000

Independent verification evidence for **FE-000 — Program workspace, board, protocol
and validator** (deliverable: `.agents/frontend-migration/` + `scripts/agents_board.py`).

## Verifier — verifier-6 (2026-09-10T08:48:51Z)

- Role: independent verifier (did not author FE-000; owner in `tasks.json` is `orchestrator`).
- Environment: branch `feature/frontend-vue-migration`, win32, Python 3.12.4
  (`C:\Users\HP\.pyenv\pyenv-win\versions\3.12.4\python.exe`).
- Working tree: did not commit/push; ran no destructive git commands (PROTOCOL §4.1).

### T1 — `python scripts/agents_board.py --check`
```
$ python scripts/agents_board.py --check
[tasks] validation OK (45 tasks)
EXIT=0
```
PASS — exit 0, prints `validation OK`.

### T2 — workspace contents
```
.agents/frontend-migration/
  PLAN.md  decisions.md  PROTOCOL.md  ORIGINAL_REQUEST.md
  tasks.json  BOARD.md
  templates/{BRIEFING,DISPATCH,progress,EVIDENCE,TESTPLAN}.md
scripts/agents_board.py
```
PASS — all program artifacts present: `PLAN.md`, `decisions.md` (D-001..D-009),
`PROTOCOL.md`, `ORIGINAL_REQUEST.md`, `tasks.json` (M1–M5 + `FS-001..008` backlog),
`templates/` (all five), plus `scripts/agents_board.py`.

### BOARD regeneration + consistency
```
$ python scripts/agents_board.py
[tasks] BOARD.md written (45 tasks: in-review=1, todo=38, verified=6)
EXIT=0
```
Re-rendered `BOARD.md` in memory with `render_board(tasks.json)` and compared against
the file after normalizing only the `Last generated:` timestamp line:
```
line counts: 742 742
equal after timestamp normalization: True
computed counts: {'in-review': 1, 'verified': 6, 'todo': 38} total 45
BOARD has '| todo | 38 |' True
BOARD has '| claimed | 0 |' True
BOARD has '| in-review | 1 |' True
BOARD has '| verified | 6 |' True
BOARD has '| blocked | 0 |' True
BOARD has '| rejected | 0 |' True
total row present: True
generated header present: True
missing task ids in BOARD: []
```
PASS — BOARD.md status counts, per-task rows and generated header are exactly
consistent with `tasks.json`.

### CLI guardrails (safe, reversible; `tasks.json` backed up first)
Backup hash: `0F6A24D6C2B0662A7BDA79D22B0A6895ABEC6F770406DAE2822F15AC09B54C9F`.

Dependency gate — FE-020 depends on `FE-012` + `FE-014` (both `todo`); the task
brief's hint about FE-003 was stale because FE-003 only depends on FE-001 (verified).
```
$ python scripts/agents_board.py --claim FE-020 verifier-6
[tasks] ERROR: FE-020: dependencies not verified: FE-012, FE-014. Complete/verify them first, or pass --force "<reason>" to override.
EXIT=1
```
`--force` records the override:
```
$ python scripts/agents_board.py --claim FE-020 verifier-6 --force "verifier-6 dependency-gate test"
[tasks] FE-020 dependency override: verifier-6 dependency-gate test
[tasks] FE-020 claimed by verifier-6
[tasks] BOARD.md written (45 tasks: claimed=1, in-review=1, todo=37, verified=6)
EXIT=0
FE-020 state: owner='verifier-6' status='claimed:verifier-6' dep_override='verifier-6 dependency-gate test'
```
Evidence gate:
```
$ python scripts/agents_board.py --status FE-012 in-review
[tasks] ERROR: FE-012: cannot move to in-review without evidence (use --set-evidence)
EXIT=1
```
Reject → unclaim round-trip:
```
$ python scripts/agents_board.py --reject FE-020 "round-trip test rejection"
[tasks] FE-020 rejected: round-trip test rejection   (EXIT=0)
  after reject:  status='rejected', rejection='round-trip test rejection'
$ python scripts/agents_board.py --unclaim FE-020
[tasks] FE-020 unclaimed -> todo                     (EXIT=0)
  after unclaim: owner=None status='todo' rejection=None dep_override=None
```
PASS — dep gate refuses and `--force` logs `dep_override`; `in-review` requires
evidence; reject/unclaim round-trips cleanly.

### Validator fault-injection (in-memory copies — real file untouched)
```
[CAUGHT] duplicate IDs                 duplicate id: FE-000
[CAUGHT] unknown dependency            FE-020: unknown dependency 'FE-NOPE'
[CAUGHT] dependency cycle              dependency cycle: FE-020 -> FE-021 -> FE-020
[CAUGHT] impl task missing verifier    FE-012: impl task missing independent verifier
[CAUGHT] verified without evidence     FE-020: verified without evidence
[CAUGHT] rejected without reason       FE-020: rejected without a reason
[CAUGHT] missing test cases            FE-012: missing test cases
[CAUGHT] missing acceptance criteria   FE-012: missing acceptance criteria
[CAUGHT] milestone unknown task        milestone M1: unknown task 'FE-NOPE'
[CAUGHT] invalid status                FE-012: invalid status 'banana'
Baseline (unmodified) errors: []
```
PASS — all required violation classes are detected; the unmodified board is clean.

### Restoration
`tasks.json` restored from backup; SHA-256
`0F6A24D6C2B0662A7BDA79D22B0A6895ABEC6F770406DAE2822F15AC09B54C9F` — byte-for-byte
identical to the pre-test file. `--check` re-run: `validation OK (45 tasks)`, EXIT=0.
`git status` unchanged (no unrelated files deleted or modified).

### Criterion-by-criterion result
1. Program workspace with PLAN/decisions/PROTOCOL/ORIGINAL_REQUEST — **PASS**.
2. `tasks.json` seeded with M1–M5 tasks and FS backlog — **PASS** (45 tasks; FS-001..008).
3. `scripts/agents_board.py` generates BOARD.md and validates — **PASS**.
4. `python scripts/agents_board.py --check` exits 0 — **PASS**.

### Regression checks
Not applicable to this process/tooling task (no WS/clipboard/timer/a11y surface).

### Verdict
`verified` — all FE-000 acceptance criteria and test cases pass on independent
re-execution; validator and CLI guardrails behave as documented.
