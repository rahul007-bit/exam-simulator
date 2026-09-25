# DISPATCH — FE-029

## 2026-09-10
You are assigned task **FE-029** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-029-implementer-23`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`ReplayPlayer.vue` + `useReplay` parsing an asciinema v2 `.cast` (header +
`[time, "o", data]`) and playing it into xterm, with scrubber, play/pause, speed
(0.5–10x), restart and an event timeline synced to the replay position. Plus
`RecordingsModal.vue` listing `/api/recordings` and reviewing a session via
`/api/recordings/{id}` + `/cast`, and a typed API module `src/api/recordings.ts`.

### Acceptance criteria
1. cast parses and plays in xterm
2. scrubber + play/pause + speed work
3. event timeline synced to replay position

### Verification method
- `bunx vue-tsc --noEmit` (must pass).
- Manual/e2e: open a real recording, confirm the terminal replays; scrub, speed
  and pause; confirm the timeline highlight tracks the playhead.
- Independent verifier re-runs T1/T2 on a clean checkout (browser leg on host).

### Constraints
- One focused change; only the five assigned files.
- Preserve parity behavior (routes, review→replay flow, only `"o"` frames).
- Update `EVIDENCE.md` with proof.
