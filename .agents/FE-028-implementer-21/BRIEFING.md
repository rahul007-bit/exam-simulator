# BRIEFING - FE-028

## Mission
Deliver the fullscreen anti-cheat primitives for the candidate exam: a
`useFullscreen` composable (auto-entry on Start, exit detection, Keyboard Lock
where supported, admin bypass, graceful degradation) and the
`FullscreenGuard.vue` "EXAM LOCKED: FULLSCREEN REQUIRED" overlay.

## Identity
- Task: FE-028
- Role: implementer
- Agent: implementer-21
- Working directory: .agents/FE-028-implementer-21
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-020
- **Acceptance criteria:**
  1. warning overlay shows on fullscreen exit
  2. candidate mode enforces lock; admin bypass
  3. graceful on unsupported browsers
- **Test cases:** (record results in TESTPLAN.md)
  1. T1 start exam then exit fullscreen -> warning overlay shown
  2. T2 admin mode fullscreen -> no lock enforced
  3. T3 Firefox unsupported lock -> degrades without breaking exam
- **Verifier:** independent agent (must differ from implementer-21)

## Key constraints
- Follow `decisions.md` - no contradicting accepted decisions.
- Strict behavioral parity (D-007): preserve anti-cheat behaviour from
  `web/static/js/app.js` (`enterCandidateFullscreen`, `requestKeyboardLock`,
  `releaseKeyboardLock`, `showFullscreenWarning`, `initFullscreenGuard`).
- Colour-only styling, tokens only, no raw hex/emoji (D-003).
- File scope: `src/composables/useFullscreen.ts`, `src/components/FullscreenGuard.vue`.
- Do not self-certify.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Legacy: `web/static/js/app.js:1765-1878`, `app.js:563-566`, `app.js:672`

## Artifact index
- `.agents/FE-028-implementer-21/DISPATCH.md`
- `.agents/FE-028-implementer-21/progress.md`
- `.agents/FE-028-implementer-21/EVIDENCE.md`
- `.agents/FE-028-implementer-21/TESTPLAN.md`
