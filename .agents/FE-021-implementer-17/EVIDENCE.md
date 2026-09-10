# EVIDENCE — FE-021

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-17 (2026-09-10T11:12Z)
- Deliverable: dependency-free persisted split-pane workspace prioritization.
  - `useSplitPane.ts` — ref/computed model: per-load ratio, pointer-drag,
    keyboard nudge, min-size clamping, persistence, collapse, reset.
  - `WorkspaceSplit.vue` — flex layout: left slot, `role="separator"` gutter
    (draggable + keyboard), collapse handle button, right slot.
  - `CandidateView.vue` — active workspace now renders `WorkspaceSplit`; left =
    FE-022 `TaskPane`; right = 36px `TODO(workspace-tabs)` slot + island mount
    point. No `NoVncFrame.vue` import.
  - `layout/index.ts` — exports `WorkspaceSplit`.
- Files touched:
  - `web/frontend/src/composables/useSplitPane.ts` (new)
  - `web/frontend/src/components/layout/WorkspaceSplit.vue` (new)
  - `web/frontend/src/components/layout/index.ts`
  - `web/frontend/src/views/CandidateView.vue`
  - `.agents/FE-021-implementer-17/**` (workspace metadata)
- Splitter API / persistence key:
  - `useSplitPane({ container, defaultRatio?, minLeft?, minRight?, storageKey?, keyboardStep? })`
    → `{ ratio, dragging, collapsed, leftStyle, rightStyle, onPointerDown, onKeydown, nudge, reset, toggleCollapse, collapse, expand, dispose }`.
  - Constants: `DEFAULT_SPLIT_RATIO = 24`, `DEFAULT_MIN_LEFT = 300`,
    `DEFAULT_MIN_RIGHT = 520`, `SPLIT_STORAGE_KEY = 'cka:workspace:split'`.
  - `localStorage` key: **`cka:workspace:split`** (stores the left-pane ratio as a
    percentage string, e.g. `"24"`).
- Commands run + output:
  ```
  $ bunx vue-tsc --noEmit
  EXIT=0
  ```
  (Batch rule: testing paused — only `bunx vue-tsc --noEmit` is run. `bun run test`,
  Playwright and the board CLI were intentionally NOT run.)
- Screenshots: n/a (browser/manual legs deferred under the paused-testing batch).
- Test cases executed (see TESTPLAN.md): T1/T2/T3 implementation present;
  browser/manual execution DEFERRED (testing paused).
- Self-check against acceptance criteria:
  1. Right pane >=76% default — PASS (impl): left `width: 24%`, right `flex-1`
     fills the remainder; both have `min-width` guardrails (300/520).
  2. Ratio persists across reloads — PASS (impl): read on init from
     `cka:workspace:split`, written on drag/reset/keyboard.
  3. Collapse toggle maximizes workspace — PASS (impl): `v-show="!collapsed"` on
     the left pane + `aria-pressed` handle button.

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
