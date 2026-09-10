# TESTPLAN — FE-014

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-014` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | audit | `Select-String -Path 'src/assets/styles/*.css' -Pattern 'box-shadow\|text-shadow\|blur\('` + `bun run test tests/unit/decor-audit.test.ts` | no glow/shadow on UI chrome | PASS — `NO_GLOW_SHADOW_MATCHES`; decor-audit glow cases green | PENDING |
| T2 | audit | emoji-range scan over `src/**/*.{vue,ts,css}` + `decor-audit.test.ts` emoji check | no emoji in UI copy | PASS — `NO_EMOJI_FOUND across 55 src files` | PENDING |
| T3 | unit | `bun run test` (full Vitest suite) | all existing + new tests pass | PASS — 16 files / 176 tests passed | PENDING |
| T4 | audit | `bunx tsc --noEmit` | exit 0 | PASS — exit 0 | PENDING |
| T5 | audit | `bun run lint` | exit 0 | PASS — exit 0, 0 errors 0 warnings | PENDING |
| T6 | unit | `decor-audit.test.ts` → `Icon` component behavior | renders svg; aria-hidden by default; role=img + label when labelled; required name set present | PASS — 11/11 decor-audit tests green | PENDING |
| T7 | audit | `bunx vue-tsc --noEmit` (read-only template check) | exit 0 | PASS — exit 0 | PENDING |

## Edge cases / additions
- The audit strips comments before matching so the documentation comments that
  literally mention "glow/gradient/emoji" do not produce false positives.
- Elevation shadows are allowed only through `shadow-[var(--shadow-*)]`; any other
  arbitrary shadow value (a colored glow) fails the audit.
- `\bfilter\s*:` (word boundary) avoids matching `enableGlobalFilter:` in
  DataTable — a false positive caught and fixed during implementation.
- Emoji detection uses `\p{Extended_Pictographic}` (Unicode property escape) in
  the Vitest audit; the shell scan uses the surrogate + symbol ranges as an
  independent cross-check.
- Audit scope is intentionally limited to the FE-014 owned files + `components/ui/**`
  so concurrent agents' new files do not race the test.

## Environment
- Commit / build: uncommitted working tree on `feature/frontend-vue-migration`
- Host: Windows dev host, Bun 1.4.x, jsdom (Vitest)
- Browser(s): Playwright DEFERRED (host-only per PROTOCOL §6)

## Verdict
- Implementer: PASS, 2026-09-10
- Verifier: PENDING
