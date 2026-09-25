# BRIEFING — FE-029

## Mission
Deliver the candidate "Recordings & review" surface: a typed recordings API, a
reusable asciinema replay engine/island (`useReplay` + `ReplayPlayer.vue`), and a
list/detail modal that plays `.cast` recordings into xterm.js with a synced event
timeline, scrubber, play/pause, speed and downloads.

## 🔒 Identity
- Task: FE-029
- Role: implementer
- Agent: implementer-23
- Working directory: .agents/FE-029-implementer-23
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-025 (verified)
- **Acceptance criteria:**
  1. cast parses and plays in xterm
  2. scrubber + play/pause + speed work
  3. event timeline synced to replay position
- **Test cases:**
  1. T1 (integration) — open a cast recording → terminal plays the session
  2. T2 (manual) — scrub / speed / pause → controls work; timeline highlight syncs
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md` (D-002 Tailwind, D-003 tokens, D-007 strict parity).
- Reuse `apiRequest`; only the assigned files are edited.
- No raw hex, glow, gradient, keyframes or emoji (FE-002 / FE-014).
- Testing paused for this batch: run only `bunx vue-tsc --noEmit`.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md` (§3 islands, §5 candidate UX)
- Protocol: `.agents/frontend-migration/PROTOCOL.md` (§9 batch rules)
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/api/recordings.ts` (new)
  - `web/frontend/src/api/index.ts` (add exports only)
  - `web/frontend/src/composables/useReplay.ts` (new)
  - `web/frontend/src/components/workspace/ReplayPlayer.vue` (new)
  - `web/frontend/src/components/candidate/RecordingsModal.vue` (new)

## Artifact index
- `.agents/FE-029-implementer-23/DISPATCH.md`
- `.agents/FE-029-implementer-23/progress.md`
- `.agents/FE-029-implementer-23/EVIDENCE.md`
- `.agents/FE-029-implementer-23/TESTPLAN.md`
