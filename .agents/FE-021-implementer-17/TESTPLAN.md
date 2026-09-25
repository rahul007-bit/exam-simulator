# TESTPLAN — FE-021

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-021` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | manual | load workspace | right pane >=76% width | DEFERRED (testing paused); impl: left `24%`, right `flex-1` | |
| T2 | manual | drag gutter then reload | ratio persisted in `localStorage` | DEFERRED (testing paused); impl: read/write `cka:workspace:split` | |
| T3 | manual | toggle collapse-left | left hidden, workspace full width | DEFERRED (testing paused); impl: `v-show` + `aria-pressed` handle | |
| T4 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS (`EXIT=0`) | |

## Edge cases / additions
- Min-size clamp at small viewports: `bounds()` caps the ratio so left >=300px
  and right >=520px while dragging; CSS `min-width` backstops the initial ratio.
- Keyboard: ArrowLeft/ArrowRight nudge by 2%, `Home` resets, `Enter`/`Space`
  toggles collapse on the `role="separator"` gutter.
- Double-click gutter resets to 24% (and persists).
- SSR/jsdom: `localStorage` and `setPointerCapture` guarded; no runtime throw.
- Raw hex / emoji audit: none introduced (Tailwind utilities + tokens only).
- FE-026 boundary: no `NoVncFrame.vue` import; tab bar left as
  `TODO(workspace-tabs)` slot in `CandidateView.vue`.

## Environment
- Commit / build: working tree, branch `feature/frontend-vue-migration`
- Host: Windows authoring env (win32)
- Browser(s): deferred (testing paused per batch rules)

## Verdict
- Implementer: PASS on implementation + `vue-tsc`; manual/browser legs DEFERRED.
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
