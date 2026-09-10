# TESTPLAN — FE-027

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-027` → `tests`).
Mirror them here, then add any edge cases discovered during work.

> Batch rule: testing is PAUSED — only `bunx vue-tsc --noEmit` may run. The
> browser-dependent legs below are DEFERRED to the platform-host verifier.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | manual | copy host → desktop | text pastes in desktop | DEFERRED (browser) | |
| T2 | manual | copy desktop → host | text pastes in browser | DEFERRED (browser) | |
| T3 | integration | watch network while WS connected | no `/api/clipboard` polling | DEFERRED (browser) | |

## Edge cases / additions
- `tsc` — `bunx vue-tsc --noEmit`: PASS (exit 0, no output) on the final run.
- Blocked background write (no user gesture) → `pendingHostClipboardText` set, then
  flushed on the next `click`/`pointerdown`/`keydown`.
- WS closed → 5s fallback `GET /api/clipboard` only while `active` and document
  visible; `POST /api/clipboard` used for outbound instead of `clipboard_copy`.
- Identical text echoed back is ignored unless it is an explicit user action
  (`lastKnownHostClipboard` / `lastKnownVncClipboard` guards).
- Empty explicit pull → `onEmpty` → info toast, no write.

## Environment
- Commit / build: working tree (no commit; branch `feature/frontend-vue-migration`)
- Host: local Windows (bun); browser legs host-only (D-006)
- Browser(s): n/a locally

## Verdict
- Implementer: PASS (tsc), browser legs DEFERRED, 2026-09-10 11:17 UTC
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
