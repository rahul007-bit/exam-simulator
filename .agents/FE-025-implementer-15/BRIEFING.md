# BRIEFING — FE-025

## Mission
Wrap `@xterm/xterm` + `@xterm/addon-fit` in a ref-driven imperative island
(`XTerm.vue`) backed by a transport composable (`useTerminal.ts`) that speaks the
existing `/ws/terminal/<sessionId>` binary/JSON contract.

## 🔒 Identity
- Task: FE-025
- Role: implementer
- Agent: implementer-15
- Working directory: .agents/FE-025-implementer-15
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-003 (verified)
- **Deliverable:** XTerm.vue wrapping xterm + addon-fit with `/ws/terminal`,
  resize, buffered replay.
- **Acceptance criteria:**
  1. connects to `/ws/terminal/<sid>`
  2. resize messages sent on container resize
  3. scrollback buffer replayed on reconnect
- **Test cases:** (see TESTPLAN.md; canonical in `tasks.json`)
  1. T1 integration — run `echo hi`; output returned over `/ws/terminal/<sid>`
  2. T2 manual — resize then reconnect; fits container, buffer replayed
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md`. No contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): binary frames for PTY I/O, JSON text
  `{"resize":{"rows":R,"cols":C}}` for resize; server-side Redis scrollback
  replay must not regress.
- No reactivity over terminal internals; refs only.
- Tailwind + tokens for the container; no raw hex/glow/emoji.
- Do not self-certify; an independent verifier must sign off.

## Blocker
`@xterm/xterm` and `@xterm/addon-fit` are **NOT installed** (absent from
`package.json` and `node_modules`). Per batch instructions the agent must not
install deps or edit `package.json`; the orchestrator must add both packages
(pinned xterm 5.5.0 + addon-fit 0.10.0) and re-run integration.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/workspace/XTerm.vue`,
  `web/frontend/src/composables/useTerminal.ts`

## Artifact index
- `.agents/FE-025-implementer-15/DISPATCH.md`
- `.agents/FE-025-implementer-15/progress.md`
- `.agents/FE-025-implementer-15/EVIDENCE.md`
- `.agents/FE-025-implementer-15/TESTPLAN.md`
