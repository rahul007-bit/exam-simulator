# BRIEFING — FE-011

## Mission
Replace native `window.confirm()` / `window.prompt()` with promise-based,
accessible dialog primitives: `useConfirm()` (module-singleton queue) plus a
single Headless UI `Dialog` host mounted once in `App.vue`.

## 🔒 Identity
- Task: FE-011
- Role: implementer
- Agent: implementer-6
- Working directory: .agents/FE-011-implementer-6
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-010 (useToast/Toaster), FE-005 (Tailwind + Headless UI refactor)
- **Acceptance criteria:**
  1. `useConfirm` resolves `true`/`false`.
  2. Prompt modal returns value or `null`.
  3. Focus trap + `Escape` + `aria-modal`.
- **Test cases:**
  1. T1 (unit) — `useConfirm()`/`prompt()` resolve/cancel: confirm→true,
     cancel→false, prompt→value, prompt cancel→null.
  2. T2 (Playwright, real browser) — keyboard-only: `Escape` cancels;
     `Tab`/`Shift+Tab` stay trapped; `aria-modal="true"` present; confirm button
     focused initially.
- **Verifier:** independent agent (not the implementer)

## Key constraints
- Follow `decisions.md` (D-002 Tailwind + Headless UI, D-003 palette).
- No raw hex, no glow/emoji; `hex-audit` covers `src/components` + `src/views`.
- Accessible: labelled title/description, initial focus, `Escape` cancels,
  focus returns to the invoker.
- Clean, testable API; no coupling to any specific page.
- Do not self-certify; independent verifier signs off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/composables/useConfirm.ts` (new)
  - `web/frontend/src/components/ConfirmDialog.vue` (new)
  - `web/frontend/src/App.vue` (mount host)
  - `web/frontend/tests/unit/confirm.test.ts` (new)
  - `web/frontend/tests/e2e/confirm.spec.ts` (new)

## Artifact index
- `.agents/FE-011-implementer-6/DISPATCH.md`
- `.agents/FE-011-implementer-6/progress.md`
- `.agents/FE-011-implementer-6/EVIDENCE.md`
- `.agents/FE-011-implementer-6/TESTPLAN.md`
