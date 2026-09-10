# TESTPLAN — FE-032

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-032` → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | set default preset, reload | value persists from `/api/admin/config` | DEFERRED (host-only, testing paused) — code path: `saveDefaultPreset()` POSTs then updates local `defaultPreset`; `loadAll()` GETs on mount | |
| T2 | e2e | submit invalid max sessions | inline/toast error, no save | DEFERRED (host-only, testing paused) — `validateMaxSessions()` rejects `< 1` / non-integers; form emits `invalid` (toast) and never calls `/api/admin/resources` | |
| T3 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS (2026-09-10T11:19:53Z) | |

## Edge cases / additions
- Non-numeric / empty max-sessions input -> `Number('') === 0` -> rejected.
- Non-integer (`2.5`) -> rejected by `validateMaxSessions`.
- Server-side validation parity: backend also rejects `< 1` with HTTP 400; the
  client validates first and the toast surfaces any 400 detail if it slips
  through.
- `default_preset = "all"` round-trips because the synthetic Full Curriculum
  option is appended to the catalogue.
- Resource draft resync only when there is no unsaved edit (no clobbering while
  the admin is typing).
- No raw hex / glow / emoji introduced; `Select` is used via `@/components/ui`.

## Environment
- Commit / build: working tree (branch `feature/frontend-vue-migration`)
- Host: authoring (Windows) — browser/e2e deferred to platform host
- Browser(s): n/a (deferred)

## Verdict
- Implementer: PASS (typecheck), e2e DEFERRED, 2026-09-10T11:19:53Z
- Verifier: <pending>
