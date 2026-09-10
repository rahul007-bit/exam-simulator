# TESTPLAN — FE-026

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results.

Test cases are defined canonically in `tasks.json` (task FE-026 → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | manual | load desktop tab | noVNC connects; iframe src/params match legacy | BLOCKED (no host/browser; URL contract asserted statically) | |
| T2 | manual | switch tabs and back | desktop session preserved | BLOCKED (no host/browser; state-preservation reasoned from `v-show` + one-shot `src`) | |
| T3 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS | |
| T4 | audit | compare `buildNoVncUrl()` to `app.js:1655` / `admin.js:778` | exact string match | PASS (see EVIDENCE.md) | |

## Edge cases / additions
- `sessionId` empty/null → falls back to `active` (legacy `|| 'active'`).
- `viewOnly` → inserts `view_only=true` before `path` (legacy `admin.js:778`).
- Session id with URL-special characters → `encodeURIComponent(sid)` for the path
  value only; slashes in `ws/desktop/` stay literal.
- Tab switch to terminal refits xterm after layout.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit).
- Host: Windows workstation (`bunx vue-tsc`); noVNC runtime requires the platform
  host + desktop fleet.
- Browser(s): deferred (testing paused this batch).

## Verdict
- Implementer: PASS for static checks; T1/T2 DEFERRED to platform host, 2026-09-10.
- Verifier: <pending>
