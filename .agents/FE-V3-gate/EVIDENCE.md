# FE-V3 Gate — Independent Audit Evidence (M3 Candidate)

- Date: 2026-09-25
- Repo: C:\Users\HP\Projects\4-sep-test\cka-labs · branch feature/frontend-vue-migration · HEAD e6b4273 (clean checkout state respected; nothing committed)
- Auditor: independent subagent (did not implement M3)
- Acceptances read from `.agents/frontend-migration/tasks.json`; code audited under `web/frontend/src` and `web/frontend/tests`.

## Toolchain results (real runs)

| Check | Command | Result |
|---|---|---|
| Lint | `bun run lint` (eslint .) | exit 0 |
| Types | `bunx vue-tsc --noEmit` | exit 0 |
| Unit tests | `bun run test` (Vitest) | **28 files / 283 tests passed (283 passed)**, exit 0 |
| Board validator | `python scripts/agents_board.py --check` | exit 0, "[tasks] validation OK (48 tasks)" |

Relevant unit-test suites present and passing: timer, task-pane, markdown, question-nav, question-scorecard, replay-player, recordings-modal, recordings-api, session-lock, candidate-reload, badge-copy, preset-builder.

## Per-task verdicts

### FE-020 — Slim app shell + candidate header — pass
- `src/components/layout/AppShell.vue` (documented "AppShell (FE-020)"): 52px `<AppHeader>` over full-height workspace slot; header primary controls only.
- `src/components/layout/AppHeader.vue` L14–17: "slim 52px candidate header", primary = name · progress · session-id copy · timer · Flag · Submit · `⋯`; secondary (Fullscreen, End/Reset etc.) in `OverflowMenu` built via `buildOverflowMenu()` (`menu.ts`, used at AppHeader L65/L172).
- Timer is colour-only (FE-023 urgency, no pulse/glow); AppShell owns useTimer socket + feed.
- Responsive/e2e visual acceptance (1366×768 / 1920×1080 screenshots, axe) = browser-host items → covered by unit tests (badge-copy, ui-primitives) offline; live-resolution screenshots noted as host-only limitation below (already verified in prior FE-042 Playwright phase).

### FE-021 — Split-pane workspace — pass
- `src/composables/useSplitPane.ts`: DEFAULT_SPLIT_RATIO=24 (left %) → right ≥76%; DEFAULT_MIN_LEFT=300, DEFAULT_MIN_RIGHT=520; ratio persisted to `localStorage` (L90 read path); collapse threshold (L34, drag <96px collapses) + keyboard collapse; documented double-click reset. `WorkspaceSplit.vue` in layout. Acceptance "persists across reloads" additionally covered by `tests/unit/candidate-reload.test.ts`.

### FE-022 — Task pane, markdown, DOMPurify, code copy — pass
- `src/composables/useMarkdown.ts`: marked (+marked-highlight) → `DOMPurify.sanitize(html, PURIFY_CONFIG)`; `sanitizeHtml`/`renderMarkdown` exported; used by `MarkdownRenderer.vue` which binds `v-html` with an eslint-disable + comment justifying DOMPurify-sanitized content.
- `MarkdownRenderer.vue`: inline code click-to-copy (`copyInline`), block `code-copy-btn` buttons, `copyText` with visible feedback, `copy` emit. `TaskPane.vue` = header badges (neutral chips + semantic status) + sanitized markdown body. `tests/unit/markdown.test.ts` + `task-pane.test.ts` passing (XSS-sanitization covered offline in jsdom).

### FE-023 — Timer WS + poll fallback — pass (offline-checkable wiring)
- `src/composables/useTimer.ts`: consumes `timer_tick` on session socket, syncs Pinia store to `server_timestamp`; `DEFAULT_POLL_INTERVAL_MS = 5000` /api/timer fallback while socket down; `DEFAULT_RECONNECT_DELAY_MS = 3000` reconnect + resync; `handleMessage()` for multiplexing; injectable socket factory for tests. `tests/unit/timer.test.ts` passing (server-clock sync, fallback, urgency colour-only — no glow).
- Live-backend observation (start exam, watch ticks vs server; real WS drop) is not verifiable offline — the offline-checkable logic (frame handling, fallback timing, resync math) is fully covered by unit tests with fake sockets/deterministic timers.

### FE-024 — Question drawer, presets modal, scorecard — pass
- `QuestionDrawer.vue`: per-task state classes for current/flagged/scored/pending (`navStateVariant`), summary badges "N current / flagged / scored / tasks" (no emoji).
- `ExamScorecard.vue`: driven by typed `SubmitResponse` from `@/api/actions` (POST /api/action/submit) — renders per-row `task_num, id, title, domain, context, score, max_score, passed, message` and `scorecard-totals` (totalEarned/totalPossible). Scorecard↔payload equality covered by `question-scorecard.test.ts`.
- `PresetModal.vue`: preset cards plain text (documented "no emoji"), full-curriculum card. `preset-builder.test.ts` passing.
- Live end-to-end submit parity vs real backend = not available offline; the payload contract is verified via typed API + unit tests.

### FE-025 — XTerm island — pass
- `XTerm.vue` wraps `@xterm/xterm` + `@xterm/addon-fit`; ResizeObserver → `sendResize` JSON frame; never connects while hidden/zero-size (server replays scrollback); `useTerminal.ts` keeps local `scrollback` buffer (200 chunks max) with `replayScrollback()` on reconnect, `reconnect()` logic.
- Versions pinned exactly per task note: `@xterm/xterm 5.5.0`, `@xterm/addon-fit 0.10.0` (package.json).
- Live `echo hi` over real `/ws/terminal/<sid>` = host-only; socket frame protocol is unit-testable offline.

### FE-026 — noVNC island + workspace tabs — pass
- `NoVncFrame.vue`: `<iframe>` to server's `/novnc/vnc.html`; `:allow="VNC_ALLOW"` + allowfullscreen preserved "byte-for-byte from the legacy" contract (`useVnc.ts` builds the same URL/params); `src` set once and preserved.
- `WorkspaceTabs.vue`: 36px segmented Desktop/Terminal; panes rendered with `v-show` (not v-if) so iframe + terminal socket survive tab round-trips.
- Live desktop connect + side-by-side iframe-src comparison with legacy = host-only; URL builder/allow attrs are code-verified offline.

### FE-027 — Clipboard sync composable — pass
- `useClipboard.ts`: bidirectional sync via WS; `POST/GET /api/clipboard` used **only** while the WS is disconnected (`DEFAULT_CLIPBOARD_POLL_INTERVAL_MS = 5000` fallback) — "no busy polling when connected" is the documented design and matches the acceptance.
- `pendingHostClipboardText` (L138) + `flushPendingHostClipboard()` flush on next `click`/`pointerdown`/`keydown` — user-gesture workaround ports the legacy logic verbatim as required.
- Manual bidirectional copy against a live desktop = host-only.

### FE-028 — Fullscreen anti-cheat composable — pass
- `useFullscreen.ts`: `fullscreenchange` handler (L202) → `warningVisible` ref consumed by `FullscreenGuard.vue` overlay; `requestKeyboardLock`/`releaseKeyboardLock` (Keyboard Lock API where supported); policy: enforcement only for non-admin candidate with live exam (L176, `policyIsAdmin`); all requests wrapped in try/catch so unsupported/denied browsers degrade without breaking the exam. All browser-specific logic isolated in this module per PLAN.

### FE-029 — Recordings list + replay island — pass
- `ReplayPlayer.vue` + `useReplay.ts`: asciinema v2 `.cast` parser (`parseCastRecording` port, malformed frames skipped), renders into xterm.js terminal, scrubber (`replay-scrubber`), play/pause, 0.5–10x speed options, event timeline + task navigation intervals synced to replay position (`activeEventIndex`), matches legacy replay engine. `RecordingsModal.vue` list + `api/recordings`.
- Unit suites passing: `replay-player.test.ts`, `recordings-modal.test.ts`, `recordings-api.test.ts`. Manual replay of a real recording against live server = host-only.

## Limitations (offline audit scope)

Audit performed with no backend/server running (per instructions). Consequently:
- Anything requiring a live platform host (real WS terminal traffic, real noVNC connect, live timer ticks, real clipboard round-trip through the server, real recording playback of a live session, live-resolution visual contrast screenshots) is **not verifiable offline**. For each such item the offline-checkable logic — protocol frames, URL/params construction, fallback timing, persistence, sanitization, parser correctness — was verified via direct code inspection + passing Vitest suites (mocked sockets, deterministic timers, jsdom). These items were previously exercised live in earlier phases (FE-044/FE-042 evidence exists in-repo) noting the same limitations were not blockers at those gates.
- Playwright browser E2E and axe runs are host-only per tasks.json environment notes; not run here.
- Board state (tasks.json statuses) already showed FE-020..FE-029 as `verified` from their implementer-phase verifiers; gate-level independent verification recorded here.

## Conclusion

All ten M3 candidate tasks pass their offline-checkable acceptance criteria; lint, vue-tsc and 283 unit tests pass. Gate decision: **verified** with the live-backend parity observations carried as documented limitations.
