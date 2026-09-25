# TESTPLAN — FE-002

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-002` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | audit | `rg '#[0-9a-fA-F]{3,6}' src/components src/views` (no `rg` here → equivalent PowerShell scan + `tests/unit/hex-audit.test.ts`) | no matches (tokens only) | **PASS** — 0 matches in 2 dirs; hex-audit suite 2/2 green | **PASS (verifier-1)** — independent Select-String scan: 0 matches under `src/components`+`src/views`; hex literals occur only in `src/assets/styles/tokens.css`; hex-audit suite 2/2 green |
| T2 | e2e | toggle theme + reload → `data-theme` flips and persists; both themes AA | flip + persist + AA in both themes | **PASS (equivalent)** — `tests/unit/theme.test.ts` (7) + `tests/unit/theme-toggle.test.ts` (1) + `tests/unit/tokens.test.ts` contrast (22 pairs) all green. Browser Playwright spec committed (`tests/e2e/theme.spec.ts`) but **DEFERRED**: chromium binary absent and cannot be downloaded offline | **PASS (verifier-1, literal browser)** — `bunx playwright test` passes `theme.spec.ts` (toggle flips, survives `page.reload()`, computed body contrast >= 4.5 in both states) plus `smoke.spec.ts`; browsers present (chromium-1243). Implementer's DEFERRAL does not reproduce; no deferral needed |

## Edge cases / additions
- `prefers-color-scheme: light` with no stored choice → light; with `dark` stored → dark
  wins (reload persistence). Covered in `theme.test.ts`.
- OS theme change followed while no manual override exists; ignored after an override.
  Covered in `theme.test.ts`.
- `clearTheme()` returns to OS preference. Covered.
- No-JS `@media (prefers-color-scheme: light)` fallback block equals the explicit light
  theme. Covered in `tokens.test.ts`.
- All 11 text/background token pairs per theme asserted ≥ 4.5:1 (WCAG AA).
- `--color-text-dim` intentionally excluded from body text (see token comments): it is
  3.3:1 (dark) / 3.1:1 (light) on the app background and is only for disabled/decorative
  affordances.

## Environment
- Commit / build: branch `feature/frontend-vue-migration`, working tree; `bun run build`
  emits `web/dist/` (`index-*.css` 6.38 kB).
- Runtime: Bun 1.4.2 (Windows). Node/npm/`rg` not on PATH. Python 3.12.4.
- Browser(s): none available locally (Playwright downloads blocked offline).

## Verdict
- Implementer: PASS for T1 and the equivalent of T2 (2026-09-10T06:02:32Z); browser e2e
  leg deferred to a networked/platform host.
- Verifier (**verifier-1**, 2026-09-10T06:09:10Z): T1 PASS and T2 PASS with the **literal
  browser e2e**; independent WCAG math -> 22/22 pairs >= 4.5:1, 0 failures; media fallback
  identical to light theme; dark/light palettes match PLAN.md §2. No regressions.
  **Verdict: verified** (verifier-1 is not the implementer).
