# Progress — FE-026

## Current status
Last visited: 2026-09-10 11:12 UTC
Status: in-review
Owner: implementer-18
Verifier: independent-agent

## Checklist
- [x] Read PLAN.md + decisions.md
- [x] Implement deliverable (NoVncFrame.vue + WorkspaceTabs.vue + useVnc.ts)
- [x] Meet all acceptance criteria (code complete; runtime connect is manual/host)
- [x] Capture evidence (commands/output) in EVIDENCE.md
- [ ] Independent verification
- [ ] Update tasks.json status (orchestrator owns tasks.json during the batch)

## Iteration status
Current iteration: 1 / 32

## Retrospective notes
- URL query string is assembled manually (not `URLSearchParams`) so the `/` in
  `path=ws/desktop/<sid>` is not percent-encoded — `URLSearchParams` would emit
  `%2F` and break the contract.
- `NoVncFrame` sets `src` once on first activation and never clears it, so the
  VNC session survives a Terminal↔Desktop switch (`v-show`, both islands stay
  mounted) — matches legacy `switchWorkspaceTab`.
- `WorkspaceTabs` refits the xterm island after switching to Terminal because it
  was hidden with `display:none` (legacy used `setTimeout(fitAddon.fit, 50)`).
- Shared/integration needs (orchestrator): keyboard-lock/fullscreen-on-desktop
  (`requestKeyboardLock`, `app.js:1652`) and wiring `WorkspaceTabs` into the
  candidate page + session `sessionId`; `useVnc` postMessage bridge has no
  consumer yet.
- Transient `vue-tsc` error observed once in
  `src/components/admin/SessionActionsDialog.vue:134` (`Property 'busy' does not
  exist`) — a concurrent agent's file, out of scope for FE-026; it cleared on
  re-run. Not caused by this task.
