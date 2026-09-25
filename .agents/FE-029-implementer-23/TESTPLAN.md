# TESTPLAN — FE-029

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-029` → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | integration | open a cast recording (`RecordingsModal` → Review & replay) | terminal plays the session | PARTIAL (static) — parser + player wired; live browser replay DEFERRED (testing paused, host-only) | — |
| T2 | manual | scrub / speed / pause | controls work; timeline highlight syncs | PARTIAL (static) — controls implemented and wired to `useReplay`; manual browser pass DEFERRED | — |
| T3 | typecheck | `bunx vue-tsc --noEmit` | exit 0, no diagnostics | PASS (2026-09-10) | — |
| T4 | audit | raw-hex / emoji / glow scan of new files | no raw hex, emoji, glow, gradient | PASS (grep, see EVIDENCE) | — |

## Edge cases / additions
- Empty/one-line `.cast` (no header) → frames still parsed; empty cast → "No
  terminal recording" message and disabled transport.
- Malformed frame line → skipped without aborting the rest (legacy parity).
- `has_cast` false → detail view renders timeline only; `.cast` link hidden.
- Scrub/seek resets the terminal and re-feeds frames up to the target time.
- Closing the modal / unmount aborts fetches, pauses playback, cancels rAF and
  disposes the xterm instance.
- Speed clamped to 0.5–10x.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit)
- Host: local authoring host (Bun 1.4.x); browser leg host-only
- Browser(s): Chrome/Firefox — DEFERRED

## Verdict
- Implementer: PASS (typecheck) / T1–T2 DEFERRED, 2026-09-10
- Verifier: —
