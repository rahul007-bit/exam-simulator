# Progress — FE-020

## Current status
Last visited: 2026-09-10 11:01 UTC
Status: in-review (pending orchestrator verification)
Owner: implementer-14
Verifier: independent-agent

## Checklist
- [x] Read PLAN.md + decisions.md
- [x] Implement deliverable
- [x] Meet all acceptance criteria
- [x] Capture evidence (commands/output) in EVIDENCE.md
- [ ] Independent verification
- [ ] Update tasks.json status (orchestrator owns tasks.json during the batch)

## Iteration status
Current iteration: 1 / 32

## Retrospective notes
- Header/overflow split mirrors the legacy `workspaceDropdown` ordering
  (`web/static/index.html:39-65`) to keep behavior parity (D-007).
- `useTimer` (FE-023) is owned by `AppShell`; it exposes `handleMessage()` for
  the future shared session event bus, which is left as `TODO(integration)`.
- Browser/Playwright checks are DEFERRED per PROTOCOL §6 (host-only; batch is
  typecheck-only). Only `bunx tsc --noEmit` was run.
