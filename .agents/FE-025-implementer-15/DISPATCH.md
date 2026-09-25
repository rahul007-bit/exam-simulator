# DISPATCH — FE-025

## 2026-09-10 (UTC)
You are assigned task **FE-025** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-025-implementer-15`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`XTerm.vue` wrapping xterm + addon-fit with `/ws/terminal/<sid>` transport,
resize frames and buffered scrollback replay; `useTerminal.ts` transport helper.

### Acceptance criteria
1. connects to `/ws/terminal/<sid>`
2. resize messages sent on container resize
3. scrollback buffer replayed on reconnect

### Verification method
- `bunx tsc --noEmit` (must pass).
- Independent verifier (after the dependency blocker is cleared): start an exam,
  run `echo hi`, inspect WS frames, resize the pane, drop and reconnect the WS.

### Constraints
- One focused change; only create/modify the two scoped files.
- Preserve parity behavior (WS contracts, binary I/O + JSON resize).
- Do not install `@xterm/*` or edit `package.json`; report the blocker instead.
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.

### Blocker
`@xterm/xterm` + `@xterm/addon-fit` are not installed.
