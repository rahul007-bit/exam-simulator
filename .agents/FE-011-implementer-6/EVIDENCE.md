# EVIDENCE — FE-011

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-6 (2026-09-10T08:58:37Z)

### Deliverable
Promise-based confirm + prompt primitives replacing native `confirm()`/`prompt()`,
built on Headless UI `Dialog`, mounted once in `App.vue`.

### Files touched
| File | Change |
| :--- | :--- |
| `web/frontend/src/composables/useConfirm.ts` | **new** — module-singleton FIFO queue + `useConfirm()` composable |
| `web/frontend/src/components/ConfirmDialog.vue` | **new** — single Headless UI `Dialog` host |
| `web/frontend/src/App.vue` | import + mount `<ConfirmDialog/>` once |
| `web/frontend/tests/unit/confirm.test.ts` | **new** — T1 (8 tests) |
| `web/frontend/tests/e2e/confirm.spec.ts` | **new** — T2 (2 Playwright tests) |

### Public API (from `src/composables/useConfirm.ts`)
```ts
export interface ConfirmOptions {
  title?: string; message?: string; confirmLabel?: string; cancelLabel?: string; danger?: boolean
}
export interface PromptOptions extends ConfirmOptions { placeholder?: string; defaultValue?: string }
export type DialogKind = 'confirm' | 'prompt'
export interface DialogRequest { id: number; kind: DialogKind; title: string; message: string;
  confirmLabel: string; cancelLabel: string; danger: boolean; placeholder: string; defaultValue: string }

export function confirm(options?: ConfirmOptions): Promise<boolean>
export function prompt(options?: PromptOptions): Promise<string | null>
export function accept(value?: string): void   // affirmative action
export function cancel(): void                 // dismissive action
export function useConfirm(): {
  active: Readonly<Ref<DialogRequest | null>>
  confirm; prompt; accept; cancel
}
```

### Behaviour
- **Concurrency: FIFO queue.** Exactly one dialog is shown; concurrent calls wait
  and appear in order. Documented in the module header. (Task explicitly allows
  "queued or rejected deterministically".)
- **Confirm** resolves `true` on confirm, `false` on cancel / `Escape` /
  backdrop click. **Prompt** resolves the submitted string (or `''`) / `null`.
- **Accessibility comes from Headless UI `Dialog`:** focus trap, `Escape`,
  `role="dialog"`, `aria-modal="true"`, `aria-labelledby` (`DialogTitle`) and
  `aria-describedby` (`DialogDescription`). Initial focus lands on the confirm
  button (or the input for prompts). Focus return to the invoker is asserted and
  also made explicit in the host to avoid an unmount race.
- **Styling:** Tailwind utilities resolving to the existing token palette
  (`bg-elevated`, `border-border`, `text-text-muted`, `bg-accent-solid`,
  `--radius-*`, `--shadow-*`); `danger` uses the AA-safe `danger-text` tonal
  treatment. The scrim uses Tailwind's `bg-black/50` keyword (no hex literal).
- **Constraints:** no raw hex, no glow/`text-shadow`/`drop-shadow`/`blur(`, no
  emoji in the new source.

### Commands run + observed output (cwd `web/frontend/`)
```
bun run build
  -> $ node scripts/gen-api.mjs && vue-tsc --noEmit && vite build
  -> ✓ 120 modules transformed.
  -> ✓ built in 1.53s                                       BUILD_EXIT=0

bun run lint
  -> $ eslint .                                             LINT_EXIT=0

bunx tsc --noEmit
  -> (no errors)                                            TSC_EXIT=0

bun run test
  -> ✓ tests/unit/confirm.test.ts (8 tests)
  -> Test Files  8 passed (8)
  -> Tests  70 passed (70)                                  TEST_EXIT=0

npx playwright test --reporter=list        (all 6 e2e specs, Chromium)
  -> ok 1 confirm.spec.ts › Escape cancels, focus is trapped, aria-modal is set, confirm is initially focused
  -> ok 2 confirm.spec.ts › prompt focusses the input and Enter resolves the value
  -> ok 3-6 smoke (x2), theme, toast
  -> 6 passed (4.4s)
```

### Test cases executed (see TESTPLAN.md)
- **T1 PASS** — `tests/unit/confirm.test.ts`, 8 tests.
- **T2 PASS** — `tests/e2e/confirm.spec.ts`, 2 real-browser keyboard tests
  (Chromium). Full e2e suite 6/6 (no regressions).

### Screenshots
n/a — headless Playwright; assertions are programmatic (focus / attributes /
promise resolution).

### Self-check against acceptance criteria
1. **`useConfirm` resolves true/false — PASS.** Unit test: confirm→`true`,
   cancel/`Escape`→`false`. e2e: `Escape` cancels.
2. **Prompt modal returns value or null — PASS.** Unit test: prompt→`'sess-42'`
   (and `''` for empty), cancel→`null`; e2e: `Enter` resolves `'lab-7'`.
3. **Focus trap + Escape + aria-modal — PASS.** e2e: `aria-modal="true"` present,
   `Tab`/`Shift+Tab` cycle confirm↔cancel with no escape, `Escape` closes and
   returns focus to the invoker. All primitives provided by Headless UI `Dialog`.

### Safety / scope
- No destructive git commands; nothing committed/amended/pushed/PR'd.
- FE-011-scoped files only (see table). `web/frontend/` is an untracked tree on
  this branch, so no unrelated tracked file was edited or deleted.
- `tasks.json` / `BOARD.md` updated only through `scripts/agents_board.py`.
- Status set to `in-review` only; **not** marked `verified` (independent verifier
  required).

### Notes for the verifier
- Headless UI teleports the dialog to `#headlessui-portal-root`; unit tests query
  `document.body` and install a local `ResizeObserver` shim (jsdom lacks it).
- Headless UI binds `Escape` on the owner `window`; the unit test dispatches the
  keydown on `window`.
- `web/frontend/tests/setup.ts` and `playwright.config.ts` were **not** modified.

## Verifier — verifier-7 (2026-09-10T09:03:13Z)

Independent re-derivation. Did **not** author FE-011; did not trust the
implementer's numbers. Working tree on `feature/frontend-vue-migration`; no
source modified; no commits/pushes; no destructive git.

### Environment
- Windows 10, Bun 1.4.2, Node v26.8.2, npm 11.19.1, Playwright 1.63.0 (Chromium).
- cwd `web/frontend/`. `web/frontend/` is an untracked tree on this branch.

### Acceptance commands re-run (my own output)
```
bun run build      -> 120 modules transformed; ✓ built in 1.66s          BUILD_EXIT=0
bun run lint       -> eslint . (no output)                              LINT_EXIT=0
bunx tsc --noEmit  -> (no output)                                        TSC_EXIT=0
bun run test       -> 8 files passed / 70 tests passed                  TEST_EXIT=0
npx playwright test-> 6 passed (2.4s)  [smoke x2, theme, toast, confirm x2]  PW_EXIT=0
```

### Independent behaviour probe (temporary Vitest, written by me, deleted afterward)
`tests/unit/zz-verifier-probe.test.ts` (8 tests) exercised the module API
**without** mounting the host — all PASS:
- `confirm()` + `accept()` -> `true`; `confirm()` + `cancel()` -> `false`.
- `prompt()` + `accept('typed-value')` -> `'typed-value'`;
  `prompt()` + `accept()` (no arg) -> `''` (not `null`); `prompt()` + `cancel()` -> `null`.
- **FIFO concurrency**: `confirm()` then `prompt()` while both pending -> only
  the confirm is `active`; after `accept()` the confirm resolves `true` and the
  prompt becomes active; after `accept('second-value')` it resolves the value.
  Settlement order asserted `['first:true','second:second-value']`.
- `accept()`/`cancel()` on an empty queue are safe no-ops.
- Defaults normalised (`'Confirm action'`/`'Enter a value'`, `OK`/`Cancel`, `danger=false`).

### Independent browser probe (temporary Playwright, written by me, deleted afterward)
`tests/e2e/zz-verifier-probe.spec.ts` (4 tests, real Chromium) — all PASS:
- `role="dialog"`, `aria-modal="true"`; `aria-labelledby`/`aria-describedby`
  resolve to elements whose text contains the title/message.
- Initial focus = confirm button (confirm) / input (prompt); `Tab` confirm->cancel,
  `Tab` cancel->confirm, `Shift+Tab` confirm->cancel; `Escape` closes.
- Focus returns to the actual invoker (`#vp-invoker`) after dismiss.
- `confirm()` click -> `true`; `Escape` -> `false`; `prompt()` Enter -> typed value;
  `prompt()` `Escape` -> `null`.
- **axe-core** scoped to the open dialog (`wcag2a/2aa/21a/21aa`): 0 violations.
- FIFO queue observed live: second dialog does not render until the first settles.

### `resize-observer` shim — not masking real behaviour
The shim exists only in the implementer's `tests/unit/confirm.test.ts` (jsdom).
My browser probe ran with Chromium's **native** `ResizeObserver`; the dialog
mounted, became visible, trapped focus and passed axe. So the shim does not hide
a real-environment defect.

### Criterion-by-criterion result
1. `useConfirm` resolves `true`/`false` — **PASS** (unit probe + browser probe).
2. Prompt returns value / `null` — **PASS** (unit probe + browser probe).
3. Focus trap + `Escape` + `aria-modal` — **PASS** (browser probe; note `dialog-root`
   itself has no layout box — Headless UI wrapper — so visibility must be asserted
   on `dialog-panel`; attributes are correctly on `dialog-root`).
4. Queue deterministic + documented — **PASS** (FIFO; module header lines 15-19).
5. Design tokens: no raw hex in `src/components` or `src/views`; scrim uses the
   permitted `bg-black/50`; utilities resolve to tokens — **PASS**.

### Regression checks
- Full unit suite 70/70 and full e2e suite 6/6 include FE-002/FE-005 tokens+theme
  (`tokens.test.ts` 27, `theme.test.ts` 7, `theme-toggle.test.ts` 1, `hex-audit.test.ts` 2)
  and FE-010 toast+axe (`toast.test.ts` 14, `toast.spec.ts` axe 0) — no regressions.
- `tasks.json`/`BOARD.md` untouched by me. Tracked modifications
  (`.gitignore`, `core/*`, `tools/*`, `web/server.py`, `web/static/*`) contain **no**
  `ConfirmDialog`/`useConfirm`/FE-011 references — they are pre-existing platform
  work, not FE-011 scope.

### Concerns / cleanup items (non-blocking)
- Stray scratch artifact `web/frontend/hex` (208-byte audit dump) is not in the
  implementer's file table and not ignored. Recommend deleting. It is **not**
  present in any build/test path and did not affect results.
- E6 claims "no emoji/non-ASCII glyphs"; two em-dashes remain in **comments** of
  `tests/unit/confirm.test.ts` and `tests/e2e/confirm.spec.ts`. No emoji in UI copy;
  cosmetic only.

### Verdict
**`verified`** — every acceptance criterion independently reproduced with my own
commands/probes; no regressions; no out-of-scope source changes. Cleanup items
above are advisory only.
