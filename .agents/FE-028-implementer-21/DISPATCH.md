# DISPATCH - FE-028

## 2026-09-10 11:18 UTC
You are assigned task **FE-028** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-028-implementer-21`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`web/frontend/src/composables/useFullscreen.ts` (new) and
`web/frontend/src/components/FullscreenGuard.vue` (new): fullscreen anti-cheat
composable + "EXAM LOCKED: FULLSCREEN REQUIRED" overlay.

### Acceptance criteria
1. Warning overlay shows on fullscreen exit.
2. Candidate mode enforces lock; admin bypass.
3. Graceful on unsupported browsers (no exam breakage).

### Verification method
- `bunx vue-tsc --noEmit` (testing paused; typecheck only).
- Manual Chrome + Firefox: start exam then exit fullscreen; admin bypass.
- Diff review of the two in-scope files.

### Constraints
- One focused change; only the two in-scope files.
- Preserve parity behaviour (anti-cheat).
- Update `EVIDENCE.md`; orchestrator owns `tasks.json` during the batch.
