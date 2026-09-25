# DISPATCH — FE-026

## 2026-09-10 11:12 UTC
You are assigned task **FE-026** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-026-implementer-18`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`NoVncFrame.vue` (iframe island) + `WorkspaceTabs.vue` (36px segmented
Desktop/Terminal control, terminal renders the read-only `XTerm.vue` island) +
`useVnc.ts` (noVNC URL and `postMessage` helpers), preserving the legacy iframe
URL/params and allow attrs.

### Acceptance criteria
1. desktop iframe URL/params match current behavior
2. tab switch preserves iframe state
3. clipboard/allowed attrs preserved

### Verification method
- `bunx vue-tsc --noEmit` (must pass).
- Compare `buildNoVncUrl()` output to `app.js:1655` / `admin.js:778` and the
  `allow` string to `index.html:142`.
- Manual: load desktop tab (T1); switch tabs and back (T2).

### Constraints
- One focused change; strict file ownership.
- Testing paused: only `bunx vue-tsc --noEmit`.
- Preserve parity behaviour (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; orchestrator owns `tasks.json`.
