# TESTPLAN — FE-034

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-034` → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | open admin page, list, terminate a test resource | rows removed, endpoint hit, confirm dialog | STATIC PASS (typecheck); runtime DEFERRED (browser host-only) | |
| T2 | audit | inspect component/composable for token usage | no raw hex, glow or emoji | PASS | |
| T3 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS (`EXIT=0`) | |

## Edge cases / additions
- Terminate cancel path: `confirm()` resolves false → no fetch, no toast.
- Duplicate resource names across nodes → keyed by `kind:node:name`; only the
  affected row shows the inline "Terminating…" spinner.
- Refresh during in-flight terminate: `refreshing` (background) keeps rows
  mounted; `loading` (initial) reserved for first paint.
- Docker rows lack `ip`/`cpu_limit`/`mem_limit` → rendered as `—` / "Host default".

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (uncommitted).
- Host: Windows authoring host (Bun 1.4.x).
- Browser(s): DEFERRED (host-only Playwright).

## Verdict
- Implementer: PASS (static/typecheck), runtime DEFERRED.
- Verifier: pending.
