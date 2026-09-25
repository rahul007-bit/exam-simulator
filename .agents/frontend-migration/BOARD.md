# BOARD - Frontend Migration

> GENERATED FILE - do not edit by hand.
> Canonical data: `.agents/frontend-migration/tasks.json`.
> Regenerate with `python scripts/agents_board.py`. Last generated: 2026-09-25T04:26:56Z.

**Program:** `frontend-migration`  
**Branch:** `feature/frontend-vue-migration`  

## Status summary

| Status | Count |
| :--- | ---: |
| todo | 0 |
| claimed | 0 |
| in-review | 0 |
| verified | 48 |
| blocked | 0 |
| rejected | 0 |
| **total** | **48** |

## Milestones

| Milestone | Name | Tasks | Gate |
| :--- | :--- | :--- | :--- |
| M1 | Foundation | FE-000, FE-001, FE-002, FE-003, FE-004, FE-005 | FE-V1 |
| M2 | UI system | FE-010, FE-011, FE-012, FE-013, FE-014 | FE-V2 |
| M3 | Candidate | FE-020, FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029 | FE-V3 |
| M4 | Admin | FE-030, FE-031, FE-032, FE-033, FE-034, FE-035, FE-036 | FE-V4 |
| M5 | Cutover | FE-040, FE-041, FE-042, FE-043, FE-044 | FE-V5 |

## Tasks

### 0 - Foundation

| ID | Title | Depends | Owner | Status | Verifier | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FE-000` | Program workspace, board, protocol and validator | - | orchestrator | verified | independent-agent | .agents/frontend-migration/ |
| `FE-001` | Vite + Vue 3 + TS scaffold and tooling | FE-000 | opencode | verified | independent-agent | .agents/FE-001-opencode/EVIDENCE.md |
| `FE-002` | Design tokens and base styles (dark + light) | FE-001 | opencode | verified | independent-agent | .agents/FE-002-opencode/EVIDENCE.md |
| `FE-003` | FastAPI SPA fallback and build integration | FE-001 | implementer-1 | verified | independent-agent | .agents/FE-003-implementer-1/EVIDENCE.md |
| `FE-004` | Typed API client and Pinia base stores | FE-003 | implementer-3 | verified | independent-agent | .agents/FE-004-implementer-3/EVIDENCE.md |
| `FE-005` | Adopt Tailwind CSS + Headless UI and refactor foundation + Toaster | FE-002, FE-010 | implementer-5 | verified | independent-agent | .agents/FE-005-implementer-5/EVIDENCE.md |
| `FE-V1` | M1 gate - independent verification | FE-000, FE-001, FE-002, FE-003, FE-004, FE-005 | - | verified | - | .agents/FE-V1-gate/EVIDENCE.md |

### 1 - UI system

| ID | Title | Depends | Owner | Status | Verifier | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FE-010` | Toast service and Toaster component | FE-002 | implementer-4 | verified | independent-agent | .agents/FE-010-implementer-4/EVIDENCE.md |
| `FE-011` | Confirm dialog and PromptModal | FE-010, FE-005 | implementer-6 | verified | independent-agent | .agents/FE-011-implementer-6/EVIDENCE.md |
| `FE-012` | UI primitives | FE-002, FE-005 | implementer-7 | verified | independent-agent | .agents/FE-012-implementer-7/EVIDENCE.md |
| `FE-013` | TanStack Table wrapper (admin use) | FE-012 | implementer-8 | verified | independent-agent | .agents/FE-013-implementer-8/EVIDENCE.md |
| `FE-014` | De-glow/de-emoji audit and icon set | FE-002, FE-005 | implementer-11 | verified | independent-agent | .agents/FE-014-implementer-11/EVIDENCE.md |
| `FE-V2` | M2 gate - independent verification | FE-010, FE-011, FE-012, FE-013, FE-014 | fe-v2-audit | verified | - | .agents/FE-V2-gate/EVIDENCE.md |

### 2 - Candidate

| ID | Title | Depends | Owner | Status | Verifier | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FE-020` | Slim app shell and candidate header | FE-012, FE-014 | implementer-14 | verified | independent-agent | .agents/FE-020-implementer-14/EVIDENCE.md |
| `FE-021` | Split-pane workspace prioritization | FE-020 | implementer-17 | verified | independent-agent | .agents/FE-021-implementer-17/EVIDENCE.md |
| `FE-022` | Task pane, markdown, DOMPurify, code copy | FE-012 | implementer-9 | verified | independent-agent | .agents/FE-022-implementer-9/EVIDENCE.md |
| `FE-023` | Timer via session WS with poll fallback | FE-004 | implementer-10 | verified | independent-agent | .agents/FE-023-implementer-10/EVIDENCE.md |
| `FE-024` | Question drawer, presets modal, scorecard | FE-013 | implementer-12 | verified | independent-agent | .agents/FE-024-implementer-12/EVIDENCE.md |
| `FE-025` | XTerm island | FE-003 | implementer-15 | verified | independent-agent | .agents/FE-025-implementer-15/orchestrator-resolution.md |
| `FE-026` | noVNC island and workspace tabs | FE-003 | implementer-18 | verified | independent-agent | .agents/FE-026-implementer-18/EVIDENCE.md |
| `FE-027` | Clipboard sync composable | FE-026 | implementer-20 | verified | independent-agent | .agents/FE-027-implementer-20/EVIDENCE.md |
| `FE-028` | Fullscreen anti-cheat composable | FE-020 | implementer-21 | verified | independent-agent | .agents/FE-028-implementer-21/EVIDENCE.md |
| `FE-029` | Recordings list and replay island | FE-025 | implementer-23 | verified | independent-agent | .agents/FE-029-implementer-23/EVIDENCE.md |
| `FE-V3` | M3 gate - candidate parity verification | FE-020, FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029 | - | verified | - | .agents/FE-V3-gate/EVIDENCE.md |

### 3 - Admin

| ID | Title | Depends | Owner | Status | Verifier | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FE-030` | Admin auth guard and login | FE-012 | implementer-13 | verified | independent-agent | .agents/FE-030-implementer-13/EVIDENCE.md |
| `FE-031` | Admin sessions table and actions | FE-013, FE-011 | implementer-16 | verified | independent-agent | .agents/FE-031-implementer-16/EVIDENCE.md |
| `FE-032` | Admin config and resource forms | FE-012 | implementer-22 | verified | independent-agent | .agents/FE-032-implementer-22/EVIDENCE.md |
| `FE-033` | Admin create invite | FE-031 | implementer-fe033 | verified | independent-agent | .agents/FE-033-verifier-fe033/EVIDENCE.md |
| `FE-034` | Admin infrastructure table | FE-013 | implementer-24 | verified | independent-agent | .agents/FE-034-implementer-24/EVIDENCE.md |
| `FE-035` | Admin live observe view | FE-025, FE-026 | implementer-25 | verified | independent-agent | .agents/FE-035-implementer-25/EVIDENCE.md |
| `FE-036` | Admin session actions: tighter dialog spacing + non-blocking per-row loading | FE-031 | implementer-19 | verified | independent-agent | .agents/FE-036-implementer-19/EVIDENCE.md |
| `FE-V4` | M4 gate - admin verification | FE-030, FE-031, FE-032, FE-033, FE-034, FE-035, FE-036 | - | verified | - | .agents/FE-V4-gate/EVIDENCE.md |

### 4 - Cutover

| ID | Title | Depends | Owner | Status | Verifier | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FE-040` | Legacy removal and static cutover | FE-020, FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029, FE-030, FE-031, FE-032, FE-033, FE-034, FE-035 | implementer-fe040 | verified | independent-agent | .agents/fe040-verifier/EVIDENCE.md |
| `FE-041` | Self-host fonts and dependencies (offline) | FE-040 | implementer-fe041 | verified | independent-agent | .agents/fe041-043-verifier/EVIDENCE.md |
| `FE-042` | Playwright E2E and axe accessibility | FE-040 | implementer-fe042 | verified | independent-agent | .agents/fe041-043-verifier/EVIDENCE.md |
| `FE-043` | Update docs (README, HANDOVER, PLATFORM_SETUP) | FE-040 | implementer-fe043 | verified | independent-agent | .agents/fe041-043-verifier/EVIDENCE.md |
| `FE-044` | Full regression against real backend | FE-042 | - | verified | independent-agent | .agents/FE-044-regression/EVIDENCE.md |
| `FE-V5` | M5 gate - victory audit | FE-040, FE-041, FE-042, FE-043, FE-044 | - | verified | - | .agents/FE-V5-gate/EVIDENCE.md |

### Future (FS)

| ID | Title | Depends | Owner | Status | Verifier | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FS-001` | Auth backend (users, roles, hashing, login/logout) | FE-004 | opencode | verified | - | .agents/FS-001-opencode/EVIDENCE.md |
| `FS-002` | Auth frontend (/login, auth store, guards) | FS-001 | opencode | verified | - | .agents/FS-002-opencode/EVIDENCE.md |
| `FS-003` | Session ownership model | FS-001 | opencode | verified | - | .agents/FS-003-opencode/EVIDENCE.md |
| `FS-004` | Admin assigns exam to user | FS-003 | opencode | verified | - | .agents/FS-004-opencode/EVIDENCE.md |
| `FS-005` | User dashboard (own exams only) | FS-002, FS-004 | opencode | verified | - | .agents/FS-005-opencode/EVIDENCE.md |
| `FS-006` | Dynamic preset generator API | FE-004 | opencode | verified | - | .agents/FS-006-opencode/EVIDENCE.md |
| `FS-007` | Custom exam builder UI | FS-006 | opencode | verified | - | .agents/FS-007-opencode/EVIDENCE.md |
| `FS-008` | Hide preset catalog from non-admin users | FS-002 | opencode | verified | - | .agents/FS-008-opencode/EVIDENCE.md |
| `FS-003b` | Concurrent per-user sessions (multi-session) | FS-003, FS-004 | - | verified | - | .agents/FS-003b-opencode/EVIDENCE.md |
| `FS-009` | Per-terminal channel recording, conditional provisioning and admin notifications | FS-003b | opencode | verified | - | .agents/FS-009-opencode/EVIDENCE.md |

## Acceptance criteria

### FE-000 - Program workspace, board, protocol and validator

- **Deliverable:** .agents/frontend-migration/ workspace (PLAN, decisions, PROTOCOL, tasks.json, templates) + scripts/agents_board.py
- **Depends on:** -
- **Acceptance:**
  - program workspace exists with PLAN.md, decisions.md, PROTOCOL.md, ORIGINAL_REQUEST.md
  - tasks.json seeded with M1-M5 tasks and FS backlog
  - scripts/agents_board.py generates BOARD.md and validates the board
  - python scripts/agents_board.py --check exits 0
- **Test cases:**
  - `T1` (audit) run: python scripts/agents_board.py --check -> expect: exit 0, 'validation OK'
  - `T2` (audit) run: list .agents/frontend-migration/ -> expect: PLAN.md, decisions.md, PROTOCOL.md, tasks.json, BOARD.md, templates/ present
- **Verification:**
  - `python scripts/agents_board.py --check`
  - `confirm BOARD.md matches tasks.json and statuses`

### FE-001 - Vite + Vue 3 + TS scaffold and tooling

- **Deliverable:** web/frontend/ scaffold: Vite, Vue 3, TS, ESLint, Prettier, Vitest, Playwright, dev proxy for /api,/ws,/novnc
- **Depends on:** FE-000
- **Acceptance:**
  - npm run build succeeds and emits web/dist/
  - npm run dev starts and /api proxy reaches FastAPI on :3000
  - ESLint + Prettier + tsc --noEmit pass
  - Vitest smoke test passes
- **Test cases:**
  - `T1` (integration) run: npm ci && npm run build  (or: bun install && bun run build) -> expect: exit 0 and web/dist/index.html exists
  - `T2` (audit) run: npm run lint && npx tsc --noEmit  (or: bun run lint && bunx tsc --noEmit) -> expect: exit 0
  - `T3` (unit) run: npm run test  (or: bun run test) -> expect: smoke test passes
- **Verification:**
  - `npm ci && npm run build  (or bun install && bun run build)`
  - `npm run lint && npx tsc --noEmit  (or bun run lint && bunx tsc --noEmit)`
  - `npm run test  (or bun run test)`

### FE-002 - Design tokens and base styles (dark + light)

- **Deliverable:** src/assets/styles/tokens.css + base.css (slate+indigo palette, radii, spacing, type, elevation, data-theme), plus the useTheme composable + ThemeToggle component and theme tests
- **Depends on:** FE-001
- **Acceptance:**
  - all palette values exposed as CSS variables in tokens.css; no raw hex in components/views
  - dark and light themes both render with AA-contrast text (>= 4.5:1 for body/UI text)
  - prefers-color-scheme default, plus a persisted manual toggle via useTheme + ThemeToggle
- **Test cases:**
  - `T1` (audit) run: scan src/components and src/views for /#[0-9a-fA-F]{3,6}/ (grep -R / Select-String; rg optional) -> expect: no matches (tokens only)
  - `T2` (e2e) run: toggle theme and reload -> expect: data-theme flips and persists; both themes AA contrast
- **Verification:**
  - `grep raw hex outside tokens (should be none)`
  - `contrast check via axe on a token sample page`

### FE-003 - FastAPI SPA fallback and build integration

- **Deliverable:** server.py serves web/dist with SPA fallback; /admin routed to SPA; build wired into tools/start-web.sh + systemd unit
- **Depends on:** FE-001
- **Acceptance:**
  - GET / and GET /admin return SPA index
  - all existing /api and /ws routes unchanged
  - /novnc mount preserved
  - build on deploy produces web/dist without committing it
- **Test cases:**
  - `T1` (integration) run: curl -s localhost:3000/ -> expect: SPA index returned
  - `T2` (integration) run: curl -s -o NUL -w '%{http_code}' localhost:3000/api/session -> expect: 200
  - `T3` (integration) run: python scripts/verify_platform_api.py -> expect: pass
- **Verification:**
  - `curl -s localhost:3000/ \| head`
  - `python scripts/verify_platform_api.py`

### FE-004 - Typed API client and Pinia base stores

- **Deliverable:** src/api client generated from /openapi.json + stores/session,timer,presets with typed responses
- **Depends on:** FE-003
- **Acceptance:**
  - types generated from /openapi.json
  - client covers session, timer, presets, actions endpoints
  - stores expose typed state and actions; smoke test hits /api/session
- **Test cases:**
  - `T1` (unit) run: npm run gen:api && npx tsc --noEmit -> expect: types generate; exit 0
  - `T2` (integration) run: session store fetchSession() -> expect: typed /api/session data populated
- **Verification:**
  - `npm run gen:api && npx tsc --noEmit`
  - `npm run test`

### FE-005 - Adopt Tailwind CSS + Headless UI and refactor foundation + Toaster

- **Deliverable:** Adopt Tailwind CSS (v4 via @tailwindcss/vite) and @headlessui/vue; expose the existing design tokens to Tailwind via @theme; refactor base styles and the Toaster to the new stack while preserving FE-002 and FE-010 acceptance.
- **Depends on:** FE-002, FE-010
- **Acceptance:**
  - tailwindcss + @tailwindcss/vite + @headlessui/vue installed and wired into the Vite build
  - design tokens exposed to Tailwind (@theme) so utilities resolve to the token palette; no raw hex in components/views
  - @headlessui/vue used for at least one accessible primitive (e.g. Toast transitions and/or a Dialog)
  - FE-002 acceptance (dark/light AA, no raw hex) and FE-010 acceptance (4 variants, aria-live, axe 0) still pass
- **Test cases:**
  - `T1` (unit) run: bun run build && bun run lint && bunx tsc --noEmit && bun run test -> expect: all pass; Tailwind plugin active in the build
  - `T2` (audit) run: confirm tailwindcss + @tailwindcss/vite + @headlessui/vue installed; no CDN/external URLs in src or index.html -> expect: deps present; no external asset URLs
  - `T3` (integration) run: Playwright toast spec + hex audit over src/components and src/views -> expect: axe 0 violations; 0 raw hex; both themes AA
- **Verification:**
  - `bun run build && bun run lint && bunx tsc --noEmit && bun run test`
  - `bunx playwright test tests/e2e/toast.spec.ts`
  - `re-run FE-002 token/hex/theme tests and FE-010 toast tests`

### FE-010 - Toast service and Toaster component

- **Deliverable:** useToast() + <Toaster/> (info/success/warning/error, stacking, auto-dismiss, aria-live)
- **Depends on:** FE-002
- **Acceptance:**
  - four variants with semantic colors
  - stacking + auto-dismiss + manual dismiss
  - aria-live announced; keyboard dismissible
- **Test cases:**
  - `T1` (unit) run: toast.push each variant -> expect: 4 variants render, stack, auto-dismiss
  - `T2` (audit) run: axe on toaster -> expect: aria-live present, no critical
- **Verification:**
  - `npm run test (unit)`
  - `manual: trigger each variant`

### FE-011 - Confirm dialog and PromptModal

- **Deliverable:** promise-based useConfirm() and prompt modal replacing confirm()/prompt()
- **Depends on:** FE-010, FE-005
- **Acceptance:**
  - useConfirm resolves true/false
  - prompt modal returns value or null
  - focus trap + Escape + aria-modal
- **Test cases:**
  - `T1` (unit) run: useConfirm() resolve/cancel -> expect: true on confirm, false on cancel
  - `T2` (manual) run: keyboard only: Escape / Tab -> expect: focus trapped, Escape cancels
- **Verification:**
  - `npm run test`
  - `manual keyboard-only flow`

### FE-012 - UI primitives

- **Deliverable:** Button, Input, Select, Badge/Chip, Card, Modal, Spinner, Segmented control
- **Depends on:** FE-002, FE-005
- **Acceptance:**
  - all variants styled from tokens only
  - focus-visible rings; disabled/loading states
  - no glow/gradient; no emoji
- **Test cases:**
  - `T1` (audit) run: axe on primitives demo -> expect: no critical violations
  - `T2` (manual) run: tab through every primitive -> expect: visible focus ring; disabled/loading correct
- **Verification:**
  - `storybook-or-demo page review`
  - `axe pass`

### FE-013 - TanStack Table wrapper (admin use)

- **Deliverable:** reusable DataTable component (sorting, filtering, pagination) built on TanStack Table
- **Depends on:** FE-012
- **Acceptance:**
  - sort/filter/paginate working
  - keyboard-accessible headers and rows
  - empty/loading states
- **Test cases:**
  - `T1` (unit) run: sort/filter/paginate helpers -> expect: correct ordering, filtering, page slicing
  - `T2` (e2e) run: click header sort; filter to empty -> expect: rows reorder; empty state shown
- **Verification:**
  - `npm run test`
  - `manual on sample data`

### FE-014 - De-glow/de-emoji audit and icon set

- **Deliverable:** remove glows/pulse/badgePop/emoji; add inline-SVG Icon component
- **Depends on:** FE-002, FE-005
- **Acceptance:**
  - no box-shadow glow, no text-shadow, no decorative keyframes
  - no emoji in UI copy
  - icon set covers all current glyph needs
- **Test cases:**
  - `T1` (audit) run: rg 'box-shadow\|text-shadow\|blur\(' src/assets/styles -> expect: no glow/shadow applied to UI chrome
  - `T2` (audit) run: grep emoji ranges in src -> expect: no emoji in UI copy
- **Verification:**
  - `grep audit for glow/gradient/emoji`
  - `visual review`

### FE-020 - Slim app shell and candidate header

- **Deliverable:** AppShell + 52px candidate header (name, progress, timer, Flag, Submit, overflow)
- **Depends on:** FE-012, FE-014
- **Acceptance:**
  - header shows only primary controls; secondary in overflow menu
  - session-id copy and admin End/Reset moved to overflow
  - responsive at 1366x768 and 1920x1080
- **Test cases:**
  - `T1` (e2e) run: load candidate view -> expect: header shows name/progress/timer/Flag/Submit; secondary in overflow
  - `T2` (audit) run: screenshot at 1366x768 and 1920x1080 -> expect: no overflow/clipping
- **Verification:**
  - `visual review at both resolutions`
  - `axe pass`

### FE-021 - Split-pane workspace prioritization

- **Deliverable:** default split [24,76] min [300,520], persistence, double-click reset, collapse-left toggle, 36px tab bar
- **Depends on:** FE-020
- **Acceptance:**
  - right pane gets >=76% by default
  - split ratio persists across reloads
  - collapse toggle maximizes workspace
- **Test cases:**
  - `T1` (manual) run: load workspace -> expect: right pane >=76% width
  - `T2` (manual) run: drag gutter then reload -> expect: ratio persisted in localStorage
  - `T3` (manual) run: toggle collapse-left -> expect: left hidden, workspace full width
- **Verification:**
  - `manual drag + reload`
  - `localStorage inspect`

### FE-022 - Task pane, markdown, DOMPurify, code copy

- **Deliverable:** task header badges, markdown body (marked + DOMPurify + highlight), inline/block code copy
- **Depends on:** FE-012
- **Acceptance:**
  - markdown sanitized via DOMPurify
  - code copy works for inline and blocks with feedback
  - badges use neutral chips + semantic status only
- **Test cases:**
  - `T1` (unit) run: render '<img src=x onerror=alert(1)>' -> expect: sanitized by DOMPurify
  - `T2` (manual) run: click inline code and block copy -> expect: copied with visible feedback
- **Verification:**
  - `npm run test`
  - `XSS payload render is sanitized`

### FE-023 - Timer via session WS with poll fallback

- **Deliverable:** useTimer consuming timer_tick + /api/timer fallback; warning/critical states without pulse glow
- **Depends on:** FE-004
- **Acceptance:**
  - timer stays in sync with server_timestamp
  - reconnects and continues correctly
  - warning/critical styles use color only
- **Test cases:**
  - `T1` (integration) run: start exam, watch timer -> expect: updates on timer_tick
  - `T2` (manual) run: drop WS then reconnect -> expect: poll fallback within 5s; resyncs
- **Verification:**
  - `manual: start exam, observe ticks`
  - `simulate WS drop`

### FE-024 - Question drawer, presets modal, scorecard

- **Deliverable:** question navigator, preset selector (admin), full curriculum card, final scorecard
- **Depends on:** FE-013
- **Acceptance:**
  - navigator reflects flagged/current/score states
  - scorecard matches /api/action/submit payload
  - no emoji in preset cards
- **Test cases:**
  - `T1` (e2e) run: open question drawer -> expect: current/flagged/score states correct
  - `T2` (e2e) run: submit exam -> expect: scorecard totals equal /api/action/submit payload
- **Verification:**
  - `manual end-to-end`
  - `compare scorecard numbers`

### FE-025 - XTerm island

- **Deliverable:** XTerm.vue wrapping xterm + addon-fit with /ws/terminal, resize, buffered replay
- **Depends on:** FE-003
- **Acceptance:**
  - connects to /ws/terminal/<sid>
  - resize messages sent on container resize
  - scrollback buffer replayed on reconnect
- **Test cases:**
  - `T1` (integration) run: run `echo hi` in terminal -> expect: output returned over /ws/terminal/<sid>
  - `T2` (manual) run: resize then reconnect -> expect: fits container; buffer replayed
- **Verification:**
  - `manual terminal interaction`
  - `inspect WS frames`

### FE-026 - noVNC island and workspace tabs

- **Deliverable:** NoVncFrame.vue + segmented Desktop/Terminal switch preserving iframe URL/params
- **Depends on:** FE-003
- **Acceptance:**
  - desktop iframe URL/params match current behavior
  - tab switch preserves iframe state
  - clipboard/allowed attrs preserved
- **Test cases:**
  - `T1` (manual) run: load desktop tab -> expect: noVNC connects; iframe src/params match legacy
  - `T2` (manual) run: switch tabs and back -> expect: desktop session preserved
- **Verification:**
  - `manual desktop connect`
  - `compare iframe src to legacy`

### FE-027 - Clipboard sync composable

- **Deliverable:** useClipboard: host<->VNC sync via WS + /api/clipboard, user-gesture flush
- **Depends on:** FE-026
- **Acceptance:**
  - copy in host reaches desktop and vice-versa
  - pending-flush logic preserved verbatim for permission
  - no busy polling when WS connected
- **Test cases:**
  - `T1` (manual) run: copy host -> desktop -> expect: text pastes in desktop
  - `T2` (manual) run: copy desktop -> host -> expect: text pastes in browser
  - `T3` (integration) run: watch network while WS connected -> expect: no /api/clipboard polling
- **Verification:**
  - `manual bidirectional copy`
  - `inspect network/WS`

### FE-028 - Fullscreen anti-cheat composable

- **Deliverable:** useFullscreen: auto-fullscreen on start, warning overlay on exit, keyboard lock where supported
- **Depends on:** FE-020
- **Acceptance:**
  - warning overlay shows on fullscreen exit
  - candidate mode enforces lock; admin bypass
  - graceful on unsupported browsers
- **Test cases:**
  - `T1` (manual) run: start exam then exit fullscreen -> expect: warning overlay shown
  - `T2` (manual) run: admin mode fullscreen -> expect: no lock enforced
  - `T3` (manual) run: Firefox unsupported lock -> expect: degrades without breaking exam
- **Verification:**
  - `manual Chrome + Firefox`
  - `toggle fullscreen`

### FE-029 - Recordings list and replay island

- **Deliverable:** ReplayPlayer.vue parsing asciinema cast + event timeline, scrubber, speed
- **Depends on:** FE-025
- **Acceptance:**
  - cast parses and plays in xterm
  - scrubber + play/pause + speed work
  - event timeline synced to replay position
- **Test cases:**
  - `T1` (integration) run: open a cast recording -> expect: terminal plays the session
  - `T2` (manual) run: scrub / speed / pause -> expect: controls work; timeline highlight syncs
- **Verification:**
  - `manual replay of a real recording`
  - `compare timeline events`

### FE-030 - Admin auth guard and login

- **Deliverable:** vue-router guard + /admin login flow using /api/admin/login, logout, check
- **Depends on:** FE-012
- **Acceptance:**
  - unauthenticated /admin redirects to login
  - cookie/bearer handled by client
  - role guard generalized for future FS-002
- **Test cases:**
  - `T1` (e2e) run: visit /admin unauthenticated -> expect: redirect to login
  - `T2` (e2e) run: bad creds then good creds -> expect: error toast then dashboard
  - `T3` (integration) run: logout then /api/admin/check -> expect: authenticated=false
- **Verification:**
  - `manual login/logout`
  - `curl /api/admin/check`

### FE-031 - Admin sessions table and actions

- **Deliverable:** DataTable of sessions/invites/history + terminate/reset/end via confirm dialog
- **Depends on:** FE-013, FE-011
- **Acceptance:**
  - table sorting/filtering/pagination
  - actions call correct admin endpoints
  - no native confirm/alert
- **Test cases:**
  - `T1` (e2e) run: terminate/reset/end from table -> expect: confirm dialog then correct endpoint hit
  - `T2` (audit) run: grep built bundle for alert(/confirm( -> expect: none
- **Verification:**
  - `manual full admin flow`
  - `verify endpoint calls`

### FE-032 - Admin config and resource forms

- **Deliverable:** default preset selector + max concurrent sessions form with validation + toasts
- **Depends on:** FE-012
- **Acceptance:**
  - forms reflect /api/admin/config and /api/admin/resources
  - validation errors shown via toast/inline
  - success feedback via toast
- **Test cases:**
  - `T1` (e2e) run: set default preset, reload -> expect: value persists from /api/admin/config
  - `T2` (e2e) run: submit invalid max sessions -> expect: inline/toast error, no save
- **Verification:**
  - `manual save/load`
  - `invalid input path`

### FE-033 - Admin create invite

- **Deliverable:** create session invite (optional preset) with copyable URL
- **Depends on:** FE-031
- **Acceptance:**
  - invite created via /api/admin/sessions/create
  - URL copied with toast feedback
  - capacity-limit errors surfaced
- **Test cases:**
  - `T1` (e2e) run: create invite and open URL -> expect: invited start screen for its preset
- **Verification:**
  - `manual create invite`
  - `open generated URL`

### FE-034 - Admin infrastructure table

- **Deliverable:** infrastructure/resources DataTable + terminate resource action
- **Depends on:** FE-013
- **Acceptance:**
  - nodes + docker + incus resources listed
  - terminate calls /api/admin/infrastructure/terminate
  - confirmation via dialog
- **Test cases:**
  - `T1` (e2e) run: list then terminate a test resource -> expect: row removed, endpoint hit, confirm dialog
- **Verification:**
  - `manual list + terminate a test resource`

### FE-035 - Admin live observe view

- **Deliverable:** observe overlay reusing XTerm + NoVNC islands per session
- **Depends on:** FE-025, FE-026
- **Acceptance:**
  - observe connects to the selected session only
  - admin reset/end available in observe
  - no cross-session leakage
- **Test cases:**
  - `T1` (e2e) run: observe active session -> expect: terminal/desktop attach; reset/end work
  - `T2` (integration) run: attempt cross-session attach -> expect: rejected (server close 1008)
- **Verification:**
  - `manual observe active session`
  - `verify admin WS attach rules`

### FE-036 - Admin session actions: tighter dialog spacing + non-blocking per-row loading

- **Deliverable:** Admin reset/terminate/end UX: reduce excessive dialog margin and make long-running actions non-blocking (GCP-style) so one in-flight action never locks the rest of the admin sessions page.
- **Depends on:** FE-031
- **Acceptance:**
  - admin action/confirm dialogs use tighter, consistent spacing (no excessive margin/padding)
  - starting an action shows a per-row/inline busy state but does NOT block opening or acting on other sessions
  - the sessions table stays populated during a mutation (no full-table loading blank); only the affected row's actions are disabled
  - results are still reported via toast and actions still go through the promise confirm dialog (no native dialogs)
- **Test cases:**
  - `T1` (unit) run: useAdminSessions per-row pending: isRowPending(id) true only for the acting row -> expect: other identifiers report not pending
  - `T2` (e2e) run: trigger a slow action on row A; confirm row B is still clickable and the table stays populated -> expect: no global block; inline busy on row A
- **Verification:**
  - `bunx vue-tsc --noEmit`
  - `unit: useAdminSessions exposes per-row pending state`
  - `manual/e2e: while one row is resetting, another row can be opened and actioned`

### FE-040 - Legacy removal and static cutover

- **Deliverable:** remove web/static app.js/admin.js/old HTML; serve only built SPA; update server mounts
- **Depends on:** FE-020, FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029, FE-030, FE-031, FE-032, FE-033, FE-034, FE-035
- **Acceptance:**
  - legacy files deleted
  - all routes serve from web/dist
  - no 404s or dead references
- **Test cases:**
  - `T1` (audit) run: grep for app.js/admin.js/legacy refs -> expect: no references remain
  - `T2` (integration) run: navigate / and /admin -> expect: served from web/dist, no 404/dead refs
- **Verification:**
  - `grep for legacy references`
  - `navigate all routes`

### FE-041 - Self-host fonts and dependencies (offline)

- **Deliverable:** no runtime CDN calls; Inter + JetBrains Mono + all libs bundled
- **Depends on:** FE-040
- **Acceptance:**
  - network tab shows no external requests
  - assets served from same origin
  - offline load renders correctly
- **Test cases:**
  - `T1` (audit) run: devtools network audit -> expect: no external domains
  - `T2` (manual) run: load with network disabled -> expect: fully styled, functions
- **Verification:**
  - `devtools network audit`
  - `load with network disabled`

### FE-042 - Playwright E2E and axe accessibility

- **Deliverable:** E2E journeys (start -> navigate -> submit; admin) + axe checks
- **Depends on:** FE-040
- **Acceptance:**
  - E2E covers candidate + admin critical paths
  - axe reports no critical violations
  - runs headless in CI/local
- **Test cases:**
  - `T1` (e2e) run: npx playwright test  (host-only; requires npx playwright install) -> expect: all journeys pass
  - `T2` (audit) run: axe scan  (browser, host-only) -> expect: no critical violations
- **Verification:**
  - `npx playwright test`
  - `axe report`

### FE-043 - Update docs (README, HANDOVER, PLATFORM_SETUP)

- **Deliverable:** document build-on-deploy, dev workflow, new frontend structure
- **Depends on:** FE-040
- **Acceptance:**
  - README reflects Vite build step
  - HANDOVER documents frontend architecture
  - PLATFORM_SETUP lists Node requirement
- **Test cases:**
  - `T1` (manual) run: follow docs on clean host -> expect: build + run succeeds
  - `T2` (audit) run: check docs -> expect: Node requirement + build-on-deploy documented
- **Verification:**
  - `follow docs from clean state`

### FE-044 - Full regression against real backend

- **Deliverable:** end-to-end regression vs platform host: candidate full exam + admin lifecycle
- **Depends on:** FE-042
- **Acceptance:**
  - full exam completes with correct scorecard
  - admin terminate/reset/end verified
  - no console errors or regressions
- **Test cases:**
  - `T1` (e2e) run: full exam vs platform host -> expect: completes with correct scorecard
  - `T2` (e2e) run: admin terminate/reset/end -> expect: all succeed
  - `T3` (audit) run: browser console -> expect: no errors/warnings
- **Verification:**
  - `run against platform host`
  - `capture scorecard + logs`

### FE-V1 - M1 gate - independent verification

- **Deliverable:** independent gate verification of all M1 tasks
- **Depends on:** FE-000, FE-001, FE-002, FE-003, FE-004, FE-005
- **Acceptance:**
  - each M1 task independently verified with evidence
  - build + serve + typed API smoke verified on platform host
- **Test cases:**
  - `T1` (audit) run: re-run all M1 acceptance + tests on clean checkout -> expect: all pass; each M1 task verified with evidence
- **Verification:**
  - `re-run all M1 acceptance on clean checkout`

### FE-V2 - M2 gate - independent verification

- **Deliverable:** independent gate verification of all M2 tasks
- **Depends on:** FE-010, FE-011, FE-012, FE-013, FE-014
- **Acceptance:**
  - tokens audited, no raw hex/glow/emoji
  - toasts/dialogs/table/a11y verified
- **Test cases:**
  - `T1` (audit) run: re-run all M2 acceptance + tests -> expect: tokens audit clean; dialogs/table/a11y pass
- **Verification:**
  - `re-run all M2 acceptance on clean checkout`

### FE-V3 - M3 gate - candidate parity verification

- **Deliverable:** independent candidate parity verification
- **Depends on:** FE-020, FE-021, FE-022, FE-023, FE-024, FE-025, FE-026, FE-027, FE-028, FE-029
- **Acceptance:**
  - full exam journey at 1366x768 and 1920x1080
  - WS/clipboard/timer/anti-cheat/replay parity confirmed
- **Test cases:**
  - `T1` (audit) run: candidate journey at 1366x768 + 1920x1080 -> expect: parity: WS, clipboard, timer, anti-cheat, replay
- **Verification:**
  - `manual + automated candidate journey`

### FE-V4 - M4 gate - admin verification

- **Deliverable:** independent admin verification
- **Depends on:** FE-030, FE-031, FE-032, FE-033, FE-034, FE-035, FE-036
- **Acceptance:**
  - all admin actions work via new dialogs/tables
  - no native dialogs remain
- **Test cases:**
  - `T1` (audit) run: admin lifecycle -> expect: all actions via dialogs/tables; no native dialogs
- **Verification:**
  - `manual admin lifecycle`

### FE-V5 - M5 gate - victory audit

- **Deliverable:** independent victory audit of the migration
- **Depends on:** FE-040, FE-041, FE-042, FE-043, FE-044
- **Acceptance:**
  - all M1-M5 gates verified
  - legacy removed, offline verified, docs updated
  - no open critical issues
- **Test cases:**
  - `T1` (audit) run: end-to-end victory audit on clean checkout -> expect: all gates verified; legacy gone; offline verified; docs updated
- **Verification:**
  - `end-to-end audit on clean checkout`

### FS-001 - Auth backend (users, roles, hashing, login/logout)

- **Deliverable:** user store + role claims + password hashing + login/logout/session endpoints
- **Depends on:** FE-004
- **Acceptance:**
  - roles admin/user
  - secure hashing
  - session cookie/JWT
- **Verification:**
  - `security review + endpoint tests`

### FS-002 - Auth frontend (/login, auth store, guards)

- **Deliverable:** /login route, auth Pinia store, role guards
- **Depends on:** FS-001
- **Acceptance:**
  - login persists session
  - guards by role
  - logout clears state
- **Verification:**
  - `manual role flows`

### FS-003 - Session ownership model

- **Deliverable:** ExamSession ownership fields + per-user session storage
- **Depends on:** FS-001
- **Acceptance:**
  - sessions owned by user
  - assigned_by recorded
- **Verification:**
  - `migration test of session data`

### FS-004 - Admin assigns exam to user

- **Deliverable:** assignment UI + API
- **Depends on:** FS-003
- **Acceptance:**
  - admin assigns preset to user
  - assignment visible to user
- **Verification:**
  - `end-to-end assign/start`

### FS-005 - User dashboard (own exams only)

- **Deliverable:** /dashboard listing only the user's exams
- **Depends on:** FS-002, FS-004
- **Acceptance:**
  - no full catalog exposed
  - start assigned exam from dashboard
- **Verification:**
  - `manual user flow`

### FS-006 - Dynamic preset generator API

- **Deliverable:** POST /api/presets/generate {count, difficulty, domains?} -> ephemeral preset + session
- **Depends on:** FE-004
- **Acceptance:**
  - selects N questions by difficulty
  - creates session without listing questions
- **Verification:**
  - `API tests for counts/difficulties`

### FS-007 - Custom exam builder UI

- **Deliverable:** count + difficulty (+ domains) builder, no question listing
- **Depends on:** FS-006
- **Acceptance:**
  - generates and starts exam
  - no individual questions shown
- **Verification:**
  - `manual builder flow`

### FS-008 - Hide preset catalog from non-admin users

- **Deliverable:** catalog visible only to admins; users see assignments only
- **Depends on:** FS-002
- **Acceptance:**
  - non-admin cannot enumerate presets
  - API authorization enforced
- **Verification:**
  - `authorization tests`

### FS-003b - Concurrent per-user sessions (multi-session)

- **Deliverable:** true per-user concurrent active sessions (each user owns an independent session); remove the single-active-session assumption from terminal/VNC/reaper resolution
- **Depends on:** FS-003, FS-004
- **Acceptance:**
  - two users run exams concurrently
  - terminal/VNC resolve per session, not session:active:id
- **Verification:**
  - `concurrency integration test`

### FS-009 - Per-terminal channel recording, conditional provisioning and admin notifications

- **Deliverable:** per-channel terminal recording (user-web/admin-web/user-desktop) with channel-filtered replay, context-conditional sandbox provisioning, and admin -> candidate desktop notifications
- **Depends on:** FS-003b
- **Acceptance:**
  - desktop terminal input+output recorded and replayable
  - replay filters events per channel (User Web/Desktop, Admin)
  - admin notification appears as a native desktop popup
  - only the sandboxes a session needs are provisioned
- **Verification:**
  - `unit tests + host smoke`
