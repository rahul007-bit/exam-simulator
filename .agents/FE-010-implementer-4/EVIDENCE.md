# EVIDENCE — FE-010

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-4 (2026-09-10T07:56:42Z)

### Deliverable
`useToast()` toast service + `<Toaster/>` host component, mounted exactly once in
the app shell. Public API: `const { toasts, push, dismiss, clear, pause, resume } =
useToast()`.

### Files touched
| File | Change |
| :--- | :--- |
| `web/frontend/src/composables/useToast.ts` | **new** — module-singleton toast store + composable |
| `web/frontend/src/components/Toaster.vue` | **new** — fixed, nonintrusive toast host with inline SVG glyphs |
| `web/frontend/src/App.vue` | mount `<Toaster/>` once after `<RouterView/>` |
| `web/frontend/tests/unit/toast.test.ts` | **new** — T1 (11 tests) + T2 axe-equivalent audit (3 tests) |
| `web/frontend/eslint.config.js` | allow the documented single-word `Toaster` component name |

### Public API (from `src/composables/useToast.ts`)
```ts
export type ToastVariant = 'info' | 'success' | 'warning' | 'error'
export interface ToastOptions { message: string; variant?: ToastVariant; title?: string; duration?: number }
export interface Toast { id: string; variant: ToastVariant; title?: string; message: string; duration: number }
export const DEFAULT_TOAST_DURATION = 5000

// push accepts push('msg', 'success') or push({ message, variant, title, duration })
// duration 0 => persistent until dismissed; default 5000ms
export function push(input: ToastOptions | string, variant?: ToastVariant): string
export function dismiss(id: string): void
export function clear(): void
export function pause(id: string): void   // suspend auto-dismiss (hover/focus)
export function resume(id: string): void  // resume with remaining time
export function useToast(): {
  toasts: Readonly<Ref<Toast[]>>
  push; dismiss; clear; pause; resume
}
```

### Behaviour
- **Four variants** (`info`/`success`/`warning`/`error`) each map to a semantic token;
  `error` uses the `danger` token family (`--color-danger-text`).
- **Stacking**: toasts render in a `v-for` column in insertion order; the host is
  `position: fixed`, top-right, `pointer-events: none` on the container and
  `pointer-events: auto` on each toast (nonintrusive).
- **Auto-dismiss**: per-toast `setTimeout` (default 5000ms); `duration: 0` opts out.
- **Manual dismiss**: per-toast close button (`aria-label="Dismiss <variant> notification"`,
  keyboard operable) plus programmatic `dismiss(id)` and `clear()`.
- **aria-live**: a persistent `.toaster__list[aria-live="polite"]` exists even when
  empty; each toast is `role="status"` (or `role="alert"` for `error`); decorative
  SVG glyphs are `aria-hidden`.
- **Timing (WCAG 2.2.1)**: auto-dismiss pauses on hover/focus and resumes on leave.
- **Tokens only**: component CSS consumes `tokens.css` variables; no raw hex, no
  glow/`text-shadow`/`blur()`, no emoji.

### Commands run + observed output (cwd `web/frontend/`)
```
python scripts/agents_board.py --check
  -> [tasks] validation OK (44 tasks)

python scripts/agents_board.py --claim FE-010 implementer-4
  -> [tasks] FE-010 claimed by implementer-4
  -> [tasks] BOARD.md written (44 tasks: claimed=1, in-review=1, todo=38, verified=4)

bun install
  -> Checked 314 installs across 355 packages (no changes) [665.00ms]

bun run test
  -> ✓ tests/unit/toast.test.ts (14 tests)
  -> Test Files  7 passed (7)
  -> Tests  62 passed (62)                                   TEST_EXIT=0

bun run lint
  -> $ eslint .                                              LINT_EXIT=0

bunx tsc --noEmit
  -> (no errors)                                             TSC_EXIT=0

bun run build
  -> $ node scripts/gen-api.mjs && vue-tsc --noEmit && vite build
  -> ✓ 54 modules transformed.
  -> ../dist/index.html 1.24 kB · assets/index-CUZNzyi1.css 8.50 kB · assets/index-DpVX7e3I.js 109.78 kB
  -> ✓ built in 1.03s                                        BUILD_EXIT=0
```

### Test cases executed (see TESTPLAN.md)
**T1 PASS** (`tests/unit/toast.test.ts`, 11 tests: four variants, stacking,
auto-dismiss configured/default, `duration:0`, manual dismiss, clear, dismiss-by-id,
pause/resume).
**T2 PASS (equivalent)** (3 tests: persistent `aria-live`; status/alert roles +
labelled controls + `aria-hidden` glyphs; no raw hex/glow + AA token contrast for all
variants on `--color-elevated` in both themes). Literal browser axe leg **DEFERRED**.

### Screenshots
n/a (headless; browser leg host-only, DEFERRED per PROTOCOL §6).

### Self-check against acceptance criteria
1. **four variants with semantic colors — PASS.** `push` normalises four variants;
   `.toast--{info,success,warning,error}` set `--toast-accent` to
   `--color-{info,success,warning,danger}-text`; tokens audit + contrast assertions pass.
2. **stacking + auto-dismiss + manual dismiss — PASS.** Insertion-order stack; timer
   auto-dismiss (configurable, `0` = persistent); close-button/programmatic dismiss and
   `clear()`.
3. **aria-live announced; keyboard dismissible — PASS.** Persistent
   `[aria-live="polite"]` region + per-toast `role`; close buttons are focusable,
   Enter/Space activatable, and labelled.

### Safety / scope
- No destructive git commands; nothing committed/amended/pushed/PR'd.
- FE-010-scoped files only (see table). `web/frontend/` is an untracked tree on this
  branch; `git status --porcelain -- web/frontend/src web/frontend/tests
  web/frontend/eslint.config.js` reports `??` for those paths (no unrelated tracked
  file edited/deleted).
- `tasks.json` / `BOARD.md` updated only through `scripts/agents_board.py`.
- Status set to `in-review` only; **not** marked `verified` (independent verifier required).

### Deferrals (host-only / tooling)
- **Browser axe on the Toaster:** DEFERRED — no `axe-core` dependency and Playwright is
  host-only (PROTOCOL §6). Intent satisfied via jsdom structural audit + token-level
  contrast assertions.
- **Manual "trigger each variant" in a real browser:** DEFERRED — Bun-only host cannot
  start the Playwright `webServer` (`npm run dev`); covered by the jsdom render tests.
- **Backend/FastAPI:** not required for this UI-only task (Linux-only, D-006).

## Verifier — verifier-4 (2026-09-10T08:01:06Z)

Independent verification. I did **not** implement FE-010. Re-derived all results from
the working tree; no source was modified, nothing committed/pushed.

### Environment
- Branch `feature/frontend-vue-migration` (unchanged), Windows 11, Bun 1.4.2, Node v26.8.2,
  Python 3.12.4. cwd `web/frontend/`. `web/frontend/` is an **untracked tree**
  (`git ls-files web/frontend/` → 0 files), so no tracked file was edited by FE-010.
- No destructive git commands used. The one probe file created for independent
  behavioural testing was written outside the source and then deleted (see below).

### Re-ran acceptance commands (my own output)
```
bun install
  -> Checked 314 installs across 355 packages (no changes) [74.00ms]   INSTALL_EXIT=0
bun run test
  -> tests/unit/toast.test.ts (14 tests)
  -> Test Files 7 passed (7) | Tests 62 passed (62)                    TEST_EXIT=0
bun run lint
  -> $ eslint .                                                        LINT_EXIT=0
bunx tsc --noEmit
  -> (no errors)                                                       TSC_EXIT=0
bun run build
  -> ../dist/index.html 1.24 kB · assets/index-CUZNzyi1.css 8.50 kB
     assets/index-DpVX7e3I.js 109.78 kB · built in 1.09s               BUILD_EXIT=0
python scripts/agents_board.py --check
  -> [tasks] validation OK (44 tasks)                                  EXIT=0
```

### Independent behavioural probe (my own assertions, not the implementer's test)
Wrote a throwaway Bun script exercising `useToast()` directly (real timers); deleted
it afterwards (`Test-Path` → False). Result `PROBE_RESULT=ALL_PASS`:
```
PASS :: four variants pushed :: ["info","success","warning","error"]
PASS :: variant order preserved
PASS :: default duration applied :: 5000
PASS :: shorthand push(message, variant)
PASS :: manual dismiss by id
PASS :: clear empties
PASS :: duration:0 not auto-dismissed after 120ms
PASS :: present before duration
PASS :: auto-dismissed after duration
PASS :: paused toast survives past duration
PASS :: resumed toast dismisses with remaining time
```

### Independent static audits
- Raw hex in `useToast.ts` / `Toaster.vue`: **none** (`Select-String '#[0-9a-fA-F]{3,6}\b'`).
- `text-shadow` / `drop-shadow` / `blur(` / `gradient` / `glow`: **none**. The only
  shadow is `box-shadow: var(--shadow-md)` (token elevation, allowed by PLAN §2).
- Emoji / non-ASCII above U+2000 in both files: **0** (node scan).
- Every `var(--token)` in `Toaster.vue` resolves to a declaration in `tokens.css`.
- Template confirms: persistent `.toaster__list[aria-live="polite"]` (no `v-if`),
  `role="status"` (non-error) / `role="alert"` (error), labelled close buttons,
  `aria-hidden` decorative SVG, insertion-order `v-for` stack, hover/focus pause+resume.

### Criterion-by-criterion
1. **Four variants with semantic colors — PASS.** Probe pushed info/success/warning/error
   in order; template maps `.toast--{variant}` to `--color-{info,success,warning,danger}-text`.
   Contrast of each accent token and `--color-text` on `--color-elevated` ≥ 4.5:1 in both
   themes (asserted; I re-derived the token values from `tokens.css`).
2. **Stacking + auto-dismiss + manual dismiss — PASS.** Independent probe: insertion-order
   stack, per-toast auto-dismiss, default 5000ms, `duration:0` persistent, `dismiss(id)`,
   `clear()`, and pause/resume remaining-time.
3. **aria-live announced; keyboard dismissible — PASS.** Persistent polite region +
   per-toast roles; close button is a native `<button>` with a variant-specific
   `aria-label`, so Enter/Space activate it. (No explicit keydown test exists, but native
   button semantics make it keyboard-operable.)

### Regression checks
- `bun run test` runs the full suite (7 files / 62 tests) — no regression.
- No WS/clipboard/timer/anti-cheat behavior is touched by FE-010 (composable + host only;
  `App.vue` gains a single `<Toaster/>`).
- Scope: FE-010 write-times limited to `useToast.ts`, `Toaster.vue`, `App.vue`,
  `toast.test.ts`, `eslint.config.js`. `schema.d.ts` was regenerated only by my own build.
  No unrelated tracked file edited/deleted. `tasks.json`/`BOARD.md` only via the board CLI.

### eslint.config.js assessment
The edit adds `'vue/multi-word-component-names': ['error', { ignores: ['Toaster'] }]`
for `**/*.vue` (line 37), with an inline rationale comment. It is a **rule-option
exemption for one name**, not a file-level `ignores` and not a rule disable. Because the
whole `web/frontend/` tree is new/untracked, it weakens nothing for pre-existing files;
within the frontend, only a component literally named `Toaster` is exempt — other
single-word component names still error. It matches the canonical `<Toaster/>` name in
`tasks.json`/PLAN. **Acceptable / low-risk.** A rename to e.g. `ToastHost` would remove
the need for the exemption entirely; note as an optional cleanup, not a blocker.

### Deferrals (host-only, PROTOCOL §6)
- Literal browser **axe** run on the Toaster: **DEFERRED** (no `axe-core` dep; Playwright
  host-only). Intent satisfied by jsdom structural tests + token-level contrast.
- Manual "trigger each variant" in a real browser: **DEFERRED** (Bun-only host cannot
  start the Playwright `webServer`); covered by the jsdom mount tests + my probe.
- Backend/FastAPI, WS, clipboard: not applicable to this UI-only task.

### Verdict: `verified`
All acceptance criteria and tests T1/T2 (equivalent) pass on my independent re-run; the
shared-config edit is narrow and justified; no regressions. Literal browser axe and
manual browser legs remain host-only DEFERRED items.
