# TESTPLAN - FE-004

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-004` -> `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run gen:api && bun run typecheck` | types generate; exit 0 | PASS (GEN_API_EXIT=0, TYPECHECK_EXIT=0) | **PASS** (verifier-3) — `bun run gen:api` exit 0, `bun run typecheck` exit 0; `bunx tsc --noEmit` (TS 5.7.3) exit 0. |
| T2 | integration | `session store fetchSession()` | typed /api/session data populated | PASS (`tests/unit/stores.test.ts`, 10/10) | **PASS** (verifier-3) — 48/48 suite, 10/10 store tests; live-backend leg **DEFERRED** (D-006). |

## Edge cases / additions
- E1 (schema fidelity): generated `AdminSessionItem` must contain
  `container_running: boolean`, `current_index?: number \| null`,
  `type: "active" \| "invite" \| "archived"`, `url: string \| null`, and
  `total_tasks: number \| null`; and must NOT contain `time_limit_minutes`.
  Result: PASS (asserted from generated `src/api/schema.d.ts`).
  Verifier-3: PASS (machine-checked against the three handler row shapes).
- E2 (nullable-only-where-null): `session_id`/`candidate_token`/`url` nullable;
  `name`/`status`/`created_at`/`container_running`/`type` non-null;
  `archived_at`/`current_index`/`scorecard_summary` optional.
  Result: PASS.
  Verifier-3: PASS (property set == union of row keys; required == intersection;
  nullability exact; enum correct; `time_limit_minutes` absent).

## Environment
- Commit / build: working tree (no commits), branch `feature/frontend-vue-migration`
- Host: Windows, Bun 1.4.2, Node v26.8.2
- Browser(s): n/a (browser leg host-only, DEFERRED)

## Verdict
- Implementer: PASS, 2026-09-10T07:36:53Z
- Verifier: **VERIFIED** (verifier-3, 2026-09-10T07:19:00Z) — rejection blocker
  (`AdminSessionItem`) resolved; all covered endpoints match `web/server.py`; 48/48
  tests, lint/typecheck/build green; FE-002 theme tests unaffected.
  Host-only: live `/openapi.json` diff + live `/api/session` — DEFERRED (not blocking).
