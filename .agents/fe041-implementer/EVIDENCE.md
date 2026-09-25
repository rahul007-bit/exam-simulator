# EVIDENCE - FE-041

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer - implementer-fe041 (2026-09-11 07:13 UTC)
- Deliverable: Self-hosted variable fonts (latin subset) for Inter + JetBrains
  Mono, `@font-face` rules imported into the global stylesheet, and a permanent
  offline-audit Vitest guard. No runtime CDN references remain.
- Files touched:
  - CREATE `web/frontend/public/fonts/inter-latin-wght-normal.woff2` (48256 bytes, sha256 3100E775E8616CD2611BEECFA23A4263D7037586789B43F035236A2E6FBD4C62)
  - CREATE `web/frontend/public/fonts/jetbrains-mono-latin-wght-normal.woff2` (40404 bytes, sha256 18BE452724BFDC236C074CA94A249A7F41A86752C7D04AB258CE9ED5651F6A7E)
  - CREATE `web/frontend/src/assets/styles/fonts.css`
  - EDIT `web/frontend/src/assets/styles/base.css` (added `@import './fonts.css';` directly after `@import 'tailwindcss';`)
  - CREATE `web/frontend/tests/unit/offline-audit.test.ts`
  - `web/frontend/package.json` UNCHANGED (no new deps).
- Commands run + output:
  ```
  > Invoke-WebRequest https://cdn.jsdelivr.net/npm/@fontsource-variable/inter/index.css
  > Invoke-WebRequest https://cdn.jsdelivr.net/npm/@fontsource-variable/jetbrains-mono/index.css
    -> discovered latin filenames

  > Invoke-WebRequest -Uri ".../@fontsource-variable/inter/files/inter-latin-wght-normal.woff2" -OutFile "web/frontend/public/fonts/inter-latin-wght-normal.woff2"
  > Invoke-WebRequest -Uri ".../@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2" -OutFile "web/frontend/public/fonts/jetbrains-mono-latin-wght-normal.woff2"
    -> 48256 + 40404 bytes

  magic-byte check: inter magic: wOF2, jetbrains magic: wOF2

  > bun run lint
  $ eslint .
  (no errors)

  > bunx vue-tsc --noEmit
  EXIT=0

  > bunx vitest run tests/unit/offline-audit.test.ts
   ✓ tests/unit/offline-audit.test.ts (9 tests) 14ms
   Test Files  1 passed (1)
        Tests  9 passed (9)

  > bun run test
   Test Files  20 passed (20)
        Tests  218 passed (218)
  ```
- Screenshots: n/a (T2 manual leg DEFERRED — see TESTPLAN.md; no browser/build run here).
- Test cases executed (see TESTPLAN.md): T1 PASS (9 tests); T2 DEFERRED.
- Self-check against acceptance criteria:
  1. No runtime CDN calls; Inter + JetBrains Mono + all libs bundled - PASS:
     fonts vendored under `public/fonts/`, `@font-face` src are same-origin
     `/fonts/*.woff2`; audit finds no `fonts.googleapis`/`fonts.gstatic`/
     `cdn.jsdelivr`/`unpkg`/`cdnjs` in `src/**` or `index.html`; `package.json`
     untouched.
  2. Network tab shows no external requests; same-origin assets; offline render
     correct - PARTIAL: same-origin + bundle proven by T1 audit; the browser
     offline render leg (T2) is DEFERRED (not runnable in this environment).

## Verifier - <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> - PASS/FAIL - <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` - <reasons if rejected>
