# DISPATCH — FE-043

## 2026-09-11
You are assigned task **FE-043** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/fe043-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Update the docs to match the post-FE-040 frontend: Vite build-on-deploy flow and
Node.js requirement, current frontend architecture, and no dead doc links.

### Acceptance criteria
1. README reflects the Vite build step.
2. HANDOVER documents frontend architecture.
3. PLATFORM_SETUP lists the Node requirement.

### Verification method
- Re-read the edited docs and spot-check against `tools/build-frontend.sh`,
  `web/server.py`, and `web/frontend/package.json`.
- `git grep -n 'STATUS.md\|HANDOVER.md' -- README.md` → no matches.
- Confirm every relative doc link resolves.

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; set status in `tasks.json` (orchestrator does the
  board CLI, not this agent).
- Do NOT touch `web/frontend/src`, `web/frontend/tests`, `web/server.py`,
  `tools/**`, other docs, or the board files. Two other agents are editing
  `web/frontend/**` concurrently.
