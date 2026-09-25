# BRIEFING — FE-043

## Mission
Align the user-facing docs with the completed FE-040 cutover: document the Vue 3 +
Vite SPA build-on-deploy flow, the Node.js requirement, and the current frontend
architecture, and remove dead documentation links.

## 🔒 Identity
- Task: FE-043
- Role: implementer
- Working directory: .agents/fe043-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-040 (verified)
- **Acceptance criteria:** (mirror the task entry)
  1. README reflects the Vite build step
  2. HANDOVER documents frontend architecture
  3. PLATFORM_SETUP lists the Node requirement
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 (manual) — follow docs on a clean host → build + run succeeds
  2. T2 (audit) — check docs → Node requirement + build-on-deploy documented
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.
- Two other agents are editing `web/frontend/**` concurrently — stay strictly within
  the doc file list. Do not touch `web/frontend/src`, `web/frontend/tests`,
  `web/server.py`, `tools/**`, the board files, or other docs.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `README.md`, `PLATFORM_SETUP.md`,
  `.agents/frontend-migration/HANDOVER.md`, `web/frontend/README.md`

## Artifact index
- `.agents/fe043-implementer/DISPATCH.md`
- `.agents/fe043-implementer/progress.md`
- `.agents/fe043-implementer/EVIDENCE.md`
