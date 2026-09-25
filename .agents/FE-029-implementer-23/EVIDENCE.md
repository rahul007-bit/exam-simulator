# EVIDENCE — FE-029

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-23 (2026-09-10)
- Deliverable: typed recordings API + asciinema `.cast` replay island + recordings
  review modal (list → replay with synced event/task timeline).
- Files touched:
  - `web/frontend/src/api/recordings.ts` (new)
  - `web/frontend/src/api/index.ts` (added `recordingsApi` export only)
  - `web/frontend/src/composables/useReplay.ts` (new)
  - `web/frontend/src/components/workspace/ReplayPlayer.vue` (new)
  - `web/frontend/src/components/candidate/RecordingsModal.vue` (new)
  - `.agents/FE-029-implementer-23/*` (workspace metadata)
- Note: `tasks.json` is owned by the orchestrator during this batch; no board
  CLI was run (PROTOCOL §9). All other tracked modifications in `git status`
  pre-existed this task.

- Commands run + output:
  ```
  $ bunx vue-tsc --noEmit        # in web/frontend
  (no diagnostics)
  EXIT=0
  ```
  Raw-hex scan of the new surfaces (FE-002):
  ```
  grep '#[0-9a-fA-F]{3,6}' ReplayPlayer.vue useReplay.ts RecordingsModal.vue
  -> no matches
  ```

- Screenshots: n/a (testing paused for this batch; browser leg host-only)

- Test cases executed (see TESTPLAN.md): T1/T2 DEFERRED (browser), T3 PASS, T4 PASS

- Self-check against acceptance criteria:
  1. cast parses and plays in xterm — IMPLEMENTED; `parseCastRecording` handles
     the v2 header + `[time,type,data]` frames, `ReplayPlayer` opens an xterm
     (`@xterm/xterm` + `@xterm/addon-fit`) and writes `"o"` frames via `useReplay`.
     Live browser replay DEFERRED to the host verifier.
  2. scrubber + play/pause + speed work — IMPLEMENTED; range scrubber calls
     `seek`, transport toggles `play/pause/restart`, speed select 0.5–10x via
     `setSpeed`. Manual browser pass DEFERRED.
  3. event timeline synced to replay position — IMPLEMENTED; `activeEventIndex`
     tracks the playhead and the sidebar highlights/scrolls the active event;
     clicking an entry seeks. Event/task tabs via `SegmentedControl`.

## Component / composable API
- `useReplay({ terminal, durationFallback })` → `frames`, `header`, `events`,
  `duration`, `currentTime`, `isPlaying`, `speed`, `progress`, `activeEventIndex`,
  `loadCast`, `setEvents`, `play`, `pause`, `toggle`, `restart`, `seek`,
  `seekRelative`, `setSpeed`, `reset`, `dispose`.
- `parseCastRecording(text)` → `{ header, frames, duration }` (asciinema v2).
- `ReplayPlayer.vue` props: `castText`, `events`, `tasks`, `durationFallback`,
  `ariaLabel`; exposes `play/pause/toggle/seek/restart/setSpeed`.
- `RecordingsModal.vue` props: `modelValue` (v-model), `title`, `description`.
- `recordings.ts`: `listRecordings`, `getRecording`, `getRecordingCast`,
  `getRecordingEvents`, `recordingCastUrl`, `recordingEventsUrl` + types.

## Integration notes (overflow `recordings` action)
The orchestrator wires `CandidateView.onAction('recordings')` (currently a no-op,
`CandidateView.vue:185`) by adding a boolean ref and the modal:

```vue
<RecordingsModal v-model="recordingsOpen" />

case 'recordings':
  recordingsOpen.value = true
  return
```

The modal is fully controlled (`v-model:modelValue`) and self-contained; it lists
`/api/recordings`, and Review loads `/api/recordings/{id}` + `/cast` and renders
`ReplayPlayer`. It is already gated by `can-view-recordings` (admin) in the
header. No shared file was modified by this task.

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1, T2, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
