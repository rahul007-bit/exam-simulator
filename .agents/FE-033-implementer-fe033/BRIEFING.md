# BRIEFING — FE-033

## Mission
Deliver the admin "Create candidate invite" surface for the Vue 3 frontend: create
a session invite (optional preset) via `POST /api/admin/sessions/create`, copy the
generated absolute invite URL to the clipboard with toast feedback, and surface
capacity-limit / API errors non-blockingly.

## 🔒 Identity
- Task: FE-033
- Role: implementer
- Working directory: .agents/FE-033-implementer-fe033
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-031
- **Acceptance criteria:** (mirror the task entry)
  1. A candidate session invite can be created from the admin UI via `POST /api/admin/sessions/create` (optional preset selection).
  2. The generated invite URL is copied to the clipboard and confirmed with a toast.
  3. Capacity-limit / API errors (e.g. HTTP 429 "Server resource limit reached…") are surfaced to the admin (toast, non-blocking).
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 (type `e2e`) — "create invite and open URL" → expected "invited start screen for its preset". Browser/Playwright is host-only (PROTOCOL §6): satisfied by-equivalent with Vitest + jsdom locally; browser leg DEFERRED to the FE-V4 milestone gate.
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/composables/useAdminInvites.ts`
  - `web/frontend/src/components/admin/AdminInviteForm.vue`
  - `web/frontend/src/views/AdminView.vue`
  - `web/frontend/tests/unit/admin-invites.test.ts`
  - `.agents/FE-033-implementer-fe033/`

## Artifact index
- `.agents/FE-033-implementer-fe033/DISPATCH.md`
- `.agents/FE-033-implementer-fe033/progress.md`
- `.agents/FE-033-implementer-fe033/EVIDENCE.md`
- `.agents/FE-033-implementer-fe033/TESTPLAN.md`
