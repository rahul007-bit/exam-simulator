# BRIEFING — <TASK-ID>

## Mission
<one or two sentences: what this task delivers and why>

## 🔒 Identity
- Task: <TASK-ID>
- Role: implementer | verifier
- Working directory: .agents/<TASK-ID>-<agent>
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** <ids or none>
- **Acceptance criteria:** (mirror the task entry)
  1. ...
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. ...
- **Verifier:** <agent or "independent agent">

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: <paths>

## Artifact index
- `.agents/<TASK-ID>-<agent>/DISPATCH.md`
- `.agents/<TASK-ID>-<agent>/progress.md`
- `.agents/<TASK-ID>-<agent>/EVIDENCE.md`
