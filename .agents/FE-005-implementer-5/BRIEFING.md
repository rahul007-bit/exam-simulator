# BRIEFING — FE-005

## Mission
Adopt Tailwind CSS v4 (`@tailwindcss/vite`) + `@headlessui/vue` and refactor the
foundation styles and the Toaster onto them, keeping `tokens.css` as the palette
source of truth and without regressing FE-002 or FE-010 acceptance.

## 🔒 Identity
- Task: FE-005
- Role: implementer
- Working directory: .agents/FE-005-implementer-5
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-002, FE-010 (both `verified`)
- **Acceptance criteria:** (mirror the task entry)
  1. tailwindcss + @tailwindcss/vite + @headlessui/vue installed and wired into the Vite build
  2. design tokens exposed to Tailwind (@theme) so utilities resolve to the token palette; no raw hex in components/views
  3. @headlessui/vue used for at least one accessible primitive (e.g. Toast transitions and/or a Dialog)
  4. FE-002 acceptance (dark/light AA, no raw hex) and FE-010 acceptance (4 variants, aria-live, axe 0) still pass
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 — `bun run build && bun run lint && bunx tsc --noEmit && bun run test` → all pass; Tailwind plugin active
  2. T2 — confirm tailwindcss + @tailwindcss/vite + @headlessui/vue installed; no CDN/external URLs in src or index.html
  3. T3 — Playwright toast spec + hex audit over src/components and src/views → axe 0 violations; 0 raw hex; both themes AA
- **Verifier:** independent agent (never the implementer)

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- `tokens.test.ts` asserts exact token values + AA contrast — do not change token values.
- `hex-audit.test.ts` forbids raw hex in `src/components` + `src/views`.
- Preserve toast class hooks: `.toaster`, `[aria-live="polite"]`, `.toast`,
  `.toast--info|success|warning|error`, `.toast__close`, `.toast__message`, `role="alert"` for error.
- No CDN/external asset URLs. No commit/push.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/package.json`, `web/frontend/vite.config.ts`,
  `web/frontend/src/assets/styles/base.css`, `web/frontend/src/components/Toaster.vue`
  (plus workspace metadata + optional tests).

## Artifact index
- `.agents/FE-005-implementer-5/DISPATCH.md`
- `.agents/FE-005-implementer-5/progress.md`
- `.agents/FE-005-implementer-5/EVIDENCE.md`
- `.agents/FE-005-implementer-5/TESTPLAN.md`
