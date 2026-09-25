# TESTPLAN — FE-035

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-035` → `tests`).
Mirror them here, then add any edge cases discovered during work.
Testing is paused for this batch: only `bunx vue-tsc --noEmit` is run; browser
legs are DEFERRED (host-only, per PROTOCOL §6).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | observe active session; switch Desktop/Terminal; Reset/End | terminal (`/ws/terminal/<sid>`) + view-only desktop attach; reset/end hit the admin endpoints | DEFERRED (browser host-only) — static wiring verified | |
| T2 | integration | attempt cross-session attach | server rejects (WS close 1008) | DEFERRED (browser host-only) — client never emits a fuzzy target | |
| T3 | unit/typecheck | `bunx vue-tsc --noEmit` | exit 0 | PASS | |
| T4 | audit | grep observe sources for `active`/`default` fallback targets | none | PASS | |
| T5 | audit | no raw hex / glow / emoji in the two new files | none | PASS | |

## Edge cases / additions
- Empty/blank `sessionId` → islands are **not** mounted (`observe-empty` state),
  so `/ws/terminal` (admin, no sid → 1008) and the noVNC `active` sentinel can
  never be reached.
- Session id changes while open → detail is cleared, the in-flight request token
  is invalidated, and the islands reconnect to the new explicit id.
- 404 (archived/terminated) during poll → soft; last known detail retained.
- Escape closes the overlay; confirmation is handled by the teleported
  `ConfirmDialog` (no native `confirm()`).

## Environment
- Commit / build: branch `feature/frontend-vue-migration` (uncommitted working tree)
- Host: win32 authoring host (D-006 platform host is canonical)
- Browser(s): n/a (deferred)

## Verdict
- Implementer: PASS (typecheck + audits), browser legs DEFERRED, 2026-09-10T11:28:58Z
- Verifier:
