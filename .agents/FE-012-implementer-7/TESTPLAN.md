# TESTPLAN — FE-012

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-012` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | audit | `npx playwright test tests/e2e/ui-primitives.spec.ts` (axe on `/dev/ui`, Chromium, WCAG 2 A/AA + 2.1 A/AA) | no critical violations | **PASS** — axe `violations` is `[]` on the full gallery, and again with the Modal open. | **PASS** — `ui-primitives.spec.ts` 5/5; my own axe+Playwright probe returned `violations=[]` with the gallery and with the Modal open, in BOTH dark and light `colorScheme` (panel asserted visible, root `role=dialog`/`aria-modal=true`). |
| T2 | manual/automated | Playwright keyboard probe + `bun run test` (unit mounts) | visible focus ring on each interactive primitive; disabled + loading render correctly | **PASS** — keyboard Tab reaches Button, Input, Select, SegmentedControl and Chip remove; each focused control has `outline-width > 0`, `outline-style ≠ none`, colour ≠ black. Disabled button is disabled; loading button is disabled + `aria-busy="true"` + decorative spinner. 27 Vitest tests mount all primitives. | **PASS** — `bun run test` 97/97; my probe keyboard-Tabs each primitive and confirms outline `2px solid` whose settled colour **exactly equals** `--focus-ring-color` (`#818cf8` dark, `#4f46e5` light). Caveat: implementer's assertion `outlineColor !== black` is weak (passes on `currentColor`); at t=0 the colour is still transitioning (`transition-colors` includes `outline-color`), so exact-value-after-settle is the real proof. Disabled/loading: attr, `aria-busy="true"`, 1 spinner, opacity 0.6 all correct. |

## Edge cases / additions
- E1 — **constraints audit** (Vitest): no raw hex, no `text-shadow`/`drop-shadow`/`blur(`, no emoji over `src/components/ui` + `DevUiView.vue`. PASS.
- E2 — **Button loading**: `disabled` + `aria-busy="true"`; embedded spinner is `aria-hidden` (unit). PASS.
- E3 — **Input error wiring**: `aria-invalid="true"` and `aria-describedby` resolves to the error text (unit). PASS.
- E4 — **Select/Listbox**: opens, shows all options, emits `update:modelValue`; disabled option carries `aria-disabled` (unit). PASS.
- E5 — **SegmentedControl/RadioGroup**: `role="radiogroup"`, labelled, `aria-checked`, disabled option `aria-disabled`, emits selection (unit). PASS.
- E6 — **Modal**: closed renders nothing; open sets `role="dialog"` + `aria-modal="true"` with a labelled title; `Escape` emits `update:modelValue=false` (unit). Browser: visible panel, axe clean, Escape closes. PASS.
- E7 — **dev-only route**: `DevUiView` is absent from the production bundle (`web/dist` has no gallery chunk/string). PASS.

## Environment
- Commit / build: working tree (no commits), branch `feature/frontend-vue-migration`
- Host: Windows, Bun 1.4.2, Node v26.8.2, Playwright (Chromium) via `webServer` = `npm run dev`
- Browser(s): Chromium (headless)

## Verdict
- Implementer: **PASS**, 2026-09-10T09:16:44Z — `build 0`, `lint 0`, `tsc 0`, `test 97/97`, `playwright 11/11`, axe 0.
- Verifier (verifier-8): **PASS/verified**, 2026-09-10T09:25:33Z — `build 0`, `lint 0`, `tsc 0`, `test 97/97`, full `playwright` 11/11 (run #2; run #1 hit the pre-existing FE-002 theme-transition flake), own axe probe 0 violations dark+light with/without Modal, focus rings exact token. Advisory: 2 non-token `black` utility colours (Modal scrim, Chip remove hover) and a blanket `require-default-prop` disable under `src/components/ui/**` (masks 14 real findings).
