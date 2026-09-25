# EVIDENCE — badge-copy

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-badge-copy (2026-09-10 UTC)
- Deliverable: Opt-in click-to-copy support on the shared `Badge`, applied to every
  candidate exam-page badge. Neutral copyable badges render with the accent
  treatment so plain-text chips become coloured.
- Files touched:
  - `web/frontend/src/components/ui/Badge.vue`
  - `web/frontend/src/components/candidate/TaskPane.vue`
  - `web/frontend/src/components/candidate/QuestionDrawer.vue`
  - `web/frontend/src/components/candidate/ExamScorecard.vue`
  - `web/frontend/src/components/candidate/RecordingsModal.vue`
  - `web/frontend/tests/unit/badge-copy.test.ts` (new)
  - `web/frontend/tests/unit/question-nav.test.ts` (added role/tabindex assertions
    to reflect the card's `<button>` → `<div role="button">` change)
  - `.agents/badge-copy-implementer/**` (this metadata workspace)

### Badge API added (all opt-in; default behaviour unchanged)
- `copyable?: boolean` (default `false`) — renders a real
  `<button type="button">` with the existing badge classes plus
  `cursor-pointer transition-opacity hover:opacity-90 active:opacity-80` and the
  shared focus ring. When `false`, renders exactly the original `<span>`.
- `copyText?: string` (default `''`) — text written to the clipboard; when
  omitted falls back to the flattened slot text (string/number vnodes).
- `copyLabel?: string` (default `''`) — accessible name; when omitted defaults to
  `Copy "<text>"`.
- `copy: [text: string]` — emitted on click.
- Colour rule: copyable + neutral → accent; `success`/`warning`/`danger`/`info`
  keep their semantic styling.
- Copies via `navigator.clipboard.writeText`, falling back to the existing
  `fallbackCopyText` from `@/composables/useClipboard`. Click calls
  `event.stopPropagation()`, flips the `copy` icon to `check` for ~1.2s, and the
  timer is cleared on unmount. Tokens only — no raw hex/emoji/glow.

### Candidate badges covered
| File | Badge | copy-text |
| :--- | :--- | :--- |
| `TaskPane.vue` | all `taskBadges` (Task N, pts, context, ns, FLAGGED) | `badge.label` |
| `QuestionDrawer.vue` | summary: `N tasks`, `N current`, `N flagged`, `N scored` | same visible text |
| `QuestionDrawer.vue` | per-task state badge (Current/Flagged/Scored/Pending) | `label(item)` |
| `ExamScorecard.vue` | summary PASSED/FAILED + per-row PASS/FAIL | same visible text |
| `RecordingsModal.vue` | status badge (Passed/Failed/In Progress) | `statusLabel(recording)` |

### Excluded
- `PresetModal.vue` "Selected" badges — pure selection-state indicators (copying
  "Selected" is meaningless) and nested inside the preset card `<button>`s, so
  making them copyable would nest interactive controls.

### Commands run + output (from `web/frontend/`)
```
$ bun run lint
$ eslint .
(no findings; exit 0)

$ bunx vue-tsc --noEmit
(no output; exit 0)

$ bun run test
Test Files  18 passed (18)
     Tests  202 passed (202)
```
Baseline was 194 tests; +8 new badge-copy tests (new file `badge-copy.test.ts`),
and `question-nav.test.ts` keeps its 9 tests (assertions added, none weakened).

- Screenshots: n/a (unit coverage only; no build/Playwright per task constraints)
- Test cases executed (see TESTPLAN.md): T1 PASS, T2 PASS, T3 PASS, T4 PASS
- Self-check against acceptance criteria:
  1. `copyable` opt-in; non-copyable renders original `<span>`/classes — PASS
  2. `copyText` with slot-text fallback; `copyLabel` accessible name — PASS
  3. `copy` emit + `stopPropagation` + transient `check` state + unmount cleanup — PASS
  4. Neutral copyable uses accent; semantic variants preserved — PASS
  5. All candidate badges copyable; PresetModal excluded — PASS
  6. Design tokens only (hex/decor audits green) — PASS
  7. lint + vue-tsc + vitest green (202 tests) — PASS

## Implementer — implementer-badge-fix (2026-09-10 UTC) — defect fix
- Deliverable: two follow-up fixes reported against the badge-copy feature.
- Defect 1 (blocking) — keyboard event bubbling: the copyable `Badge` stopped
  `click` but not `keydown`, so focusing the nested copy button inside the
  `QuestionDrawer` per-task `<div role="button" tabindex="0">` card and pressing
  Enter/Space also fired the card's jump/close (`@keydown.enter` /
  `@keydown.space.prevent`). Fix: added `@keydown.stop` to the copyable
  `<button>` in `Badge.vue`. `.stop` only stops propagation — it does not
  `preventDefault`, so native button activation (and therefore copy) still works.
- Defect 2 — wrong copy text for `ns:` / `context:` chips: the TaskPane metadata
  chips copied their full label (`ns: batch-processing`, `context: k3d-cka`).
  Now the raw value is copied (`batch-processing`, `k3d-cka`). Fix:
  - `task.ts`: added optional `copy?: string` to `TaskBadge`; set it to
    `task.target_context || DEFAULT_CONTEXT` (context) and
    `task.namespace || DEFAULT_NAMESPACE` (namespace). Other badges leave it
    undefined and keep copying their label.
  - `TaskPane.vue`: `<Badge ... :copy-text="badge.copy ?? badge.label" />`.
- Files touched:
  - `web/frontend/src/components/ui/Badge.vue`
  - `web/frontend/src/components/candidate/task.ts`
  - `web/frontend/src/components/candidate/TaskPane.vue`
  - `web/frontend/tests/unit/badge-copy.test.ts`
  - `web/frontend/tests/unit/question-nav.test.ts`
  - `.agents/badge-copy-implementer/EVIDENCE.md`, `progress.md`
- Commands run + output (from `web/frontend/`, working tree on
  `feature/frontend-vue-migration`):
  ```
  $ bunx vue-tsc --noEmit
  EXIT=0 (no output)

  $ bun run lint
  $ eslint .
  EXIT=0 (no findings)

  $ bun run test -- tests/unit/badge-copy.test.ts tests/unit/question-nav.test.ts
  ✓ tests/unit/badge-copy.test.ts  (11 tests)
  ✓ tests/unit/question-nav.test.ts  (10 tests)
  Test Files  2 passed (2)
       Tests  21 passed (21)
  EXIT=0
  ```
  Full `bun run test`, `bun run build` and Playwright were intentionally NOT run
  (another agent owns the concurrent suite build). Baseline for these two files
  was 17 tests (8 + 9); now 21 (11 + 10), with no existing assertion weakened.
- Test cases executed (see TESTPLAN.md): T1 PASS, T2 PASS, T3 PASS, T4 PASS,
  T6 PASS; T5/T7 not re-run here (owned by the orchestrator's full suite).
- Self-check against the reported defects:
  1. Keydown (Enter/Space) on the nested copy button does not bubble to a parent
     `@keydown.enter` listener — PASS (new `badge-copy.test.ts` case proves the
     parent counter stays 0 and `defaultPrevented` is false; copy still fires on
     the resulting click). `question-nav.test.ts` adds a drawer-level case
     asserting the per-task copy button's keydown emits no `select`.
  2. `context:` / `ns:` chips copy only the raw value while their labels are
     unchanged — PASS (new `taskBadges copy text` assertions cover explicit
     values and the `k3d-cka` / `default` fallbacks).
  3. Scope respected — only the five owned frontend files + this workspace were
     edited; `CandidateView.vue`, admin, `DataTable.vue`, `ui/index.ts`,
     `server.py`, `static/**`, `core/**`, `docker/**`, configs untouched.
     Design tokens only (no raw hex/emoji/glow).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: pending
- Re-ran acceptance commands: pending
- Test cases re-run independently (see TESTPLAN.md): pending
- Criterion-by-criterion result: pending
- Regression checks (WS, clipboard, timer, a11y, contrast): pending
- Verdict: pending
