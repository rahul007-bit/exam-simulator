# TESTPLAN — FE-010

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-010` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test` → `toast.push` each variant (`tests/unit/toast.test.ts`, 11 tests) | 4 variants render, stack, auto-dismiss | **PASS** — 4 variants render + class-per-variant; insertion-order stacking; auto-dismiss at the configured and default durations; `duration:0` persists; manual dismiss via close button; `clear()`; programmatic `dismiss(id)`; pause/resume on hover. | **PASS (verifier-4)** — `bun run test` → toast.test.ts 14/14, full suite 62/62, exit 0. Independent Bun probe of `useToast()` (11 own assertions incl. variant order, default duration 5000, `duration:0`, auto-dismiss, dismiss-by-id, clear, pause/resume) → `PROBE_RESULT=ALL_PASS`. |
| T2 | audit | `bun run test` → `tests/unit/toast.test.ts` T2 block (3 tests); literal axe DEFERRED | aria-live present, no critical | **PASS (equivalent)** — persistent `[aria-live="polite"]` region; `role="status"`/`role="alert"` per toast; labelled close buttons; decorative glyphs `aria-hidden`; no raw hex/glow in the component; semantic `--color-*-text` on `--color-elevated` ≥ 4.5:1 in both themes. Browser axe leg **DEFERRED** (PROTOCOL §6). | **PASS (equivalent, verifier-4)** — re-ran T2 block 3/3. Independent static audit: no raw hex; no text-shadow/drop-shadow/blur/gradient/glow; 0 emoji/non-ASCII; every `var()` token resolves in `tokens.css`; template has persistent polite region + status/alert roles + labelled native `<button>` close. **Browser axe DEFERRED** (host-only, PROTOCOL §6). |

## Edge cases / additions
- E1 — `push(message, variant)` shorthand and `push(options)` both supported; default
  variant is `info`; default duration `DEFAULT_TOAST_DURATION = 5000ms`. PASS.
- E2 — `duration: 0` never auto-dismisses. PASS.
- E3 — `pause()`/`resume()` preserve remaining time while hovered/focused (WCAG 2.2.1
  friendly). PASS.
- E4 — Semantic token coverage: `error` uses the `danger` token family; all four
  `--color-{info,success,warning,danger}-text` and `--color-text` are AA (≥ 4.5:1) on
  `--color-elevated` in dark and light. PASS.
- E5 — Exactly one `<Toaster/>` mounted in `App.vue`; component is `position: fixed`
  and `pointer-events: none` on the container (nonintrusive). PASS.

## Environment
- Commit / build: working tree (no commits), branch `feature/frontend-vue-migration`
- Host: Windows, Bun 1.4.2, Node v26.8.2
- Browser(s): n/a (Bun-only host; browser/axe leg host-only, DEFERRED)

## Verdict
- Implementer: PASS, 2026-09-10T07:56:42Z
- Verifier: **PASS / verified**, verifier-4, 2026-09-10T08:01:06Z — all acceptance
  criteria + T1/T2 re-run independently; literal browser axe and manual browser legs
  remain host-only DEFERRED (PROTOCOL §6).
