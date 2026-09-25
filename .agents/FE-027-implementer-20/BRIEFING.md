# BRIEFING — FE-027

## Mission
Deliver bidirectional host↔VNC clipboard sync as a Vue composable (`useClipboard`)
plus a headless `ClipboardBridge` component, faithfully porting the legacy
`app.js` clipboard logic (WS + `/api/clipboard` + user-gesture flush).

## 🔒 Identity
- Task: FE-027
- Role: implementer
- Working directory: .agents/FE-027-implementer-20
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-026 (verified)
- **Acceptance criteria:**
  1. Copy in host reaches desktop and vice-versa.
  2. Pending-flush logic preserved verbatim for browser permission.
  3. No busy `/api/clipboard` polling while the WS is connected.
- **Test cases:** T1 manual host→desktop; T2 manual desktop→host; T3 integration
  watch network while WS connected (see TESTPLAN.md).
- **Verifier:** independent agent.

## Key constraints
- Follow `decisions.md`; D-007 strict parity.
- No raw hex / glow / emoji; tokens/Tailwind only.
- Only touched the two owned files (testing paused → `bunx vue-tsc --noEmit` only).

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Files in scope: `web/frontend/src/composables/useClipboard.ts` (new),
  `web/frontend/src/components/workspace/ClipboardBridge.vue` (new)

## Artifact index
- `.agents/FE-027-implementer-20/DISPATCH.md`
- `.agents/FE-027-implementer-20/progress.md`
- `.agents/FE-027-implementer-20/EVIDENCE.md`
- `.agents/FE-027-implementer-20/TESTPLAN.md`
