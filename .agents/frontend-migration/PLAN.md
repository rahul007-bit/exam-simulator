# PLAN — Frontend Migration (Vue 3 + TS + Vite)

Single source of truth for *what* we are building and *why*. Task tracking lives in
`BOARD.md` / `tasks.json`; agent rules live in `PROTOCOL.md`.

## 1. Goal

Replace the vanilla-JS candidate + admin frontends with one maintainable,
professional SPA:

- **Stack:** Vue 3 + TypeScript + Vite, Pinia, vue-router.
- **UI:** Tailwind CSS + Headless UI (Vue) + TanStack Table (admin tables only).
- **Theme:** slate neutrals + single indigo accent, dark + light toggle.
- **UX:** candidate workspace prioritizes the desktop (right pane); native dialogs
  replaced by toasts/confirm/prompt; no neon glow or emoji.
- **Deploy:** build to `web/dist/` on the platform host, served by FastAPI.

## 2. Design system

Token layer: `src/assets/styles/tokens.css`, theme via `data-theme` on `<html>`
(default from `prefers-color-scheme`, persisted).

```
Accent (single):   indigo       #4f46e5 (light) / #6366f1 (dark)
Semantic only:     success #22c55e  warning #f59e0b  danger #ef4444  info #60a5fa

Dark:   bg-app #0b0f16  surface #121826  elevated #1a2233  hover #222c40
        border #263042  border-strong #33405a
        text #e6e9ef   muted #9aa4b2   dim #5b6675
Light:  bg-app #f6f7f9  surface #ffffff  elevated #ffffff  hover #eef1f5
        border #e2e6ec  border-strong #cbd2db
        text #0f172a   muted #5b6675   dim #8a94a3

Radii: 6 / 8 / 12px
Spacing: 4px grid (Tailwind default scale)
Shadows: one subtle elevation scale (no glows)
Type: Inter (UI) + JetBrains Mono (code), self-hosted

**Accessibility / derived tokens** (see `tokens.css`; verified at token level by FE-002):

- `--color-text-dim` is for decorative/non-essential text only. It does **not** meet AA
  for body text (`#5b6675` on `#0b0f16` ≈ 3.2:1; `#8a94a3` on `#f6f7f9` ≈ 2.8:1). Use
  `--color-text-muted` for readable secondary text.
- The raw accent `#6366f1` on white is ≈ 4.47:1 (just under AA). For accent **text** use
  `--color-accent-text`; for accent **fills carrying white text** use `--color-accent-solid`
  (`#4f46e5`). `--color-accent` is retained for decorative/ring use.
- Semantic states expose AA-safe text variants: `--color-{success,warning,danger,info}-text`.
- All body/UI text pairs are asserted at ≥ 4.5:1 for both themes in `tokens.test.ts`.
```

**Removals:** cyan/purple/pink accents; `code-copied` glow (`style.css:598,605`);
`pulse` (`:152`); `badgePop` (`:628`); rainbow badges; emoji in UI (⏱📋🎯).
Icons become a small inline-SVG set.

## 3. Architecture

```
web/frontend/
  index.html  vite.config.ts  tsconfig.json  package.json
  src/
    main.ts  App.vue
    router/            # "/" candidate, "/admin" admin (+ /login,/dashboard,/exam/:id placeholders)
    api/               # typed client generated from /openapi.json
    stores/            # Pinia: session, timer, presets, admin, auth
    composables/       # useSessionWs, useTimer, useClipboard, useFullscreen, useToast, useConfirm
    islands/           # XTerm.vue, NoVncFrame.vue, ReplayPlayer.vue (imperative, ref-driven)
    components/        # common/ candidate/ admin/
    assets/styles/     # tokens.css + base.css
```

Principles:

- Framework owns shell/state/forms; **xterm, noVNC, replay are imperative islands**
  wrapped in components with `ref` + `onMounted`/`onBeforeUnmount`.
- **Preserve WS contracts:** `clipboard_update`, `timer_tick`, `transition_progress`,
  `session_expired`, `session_terminated` (`app.js:43-66`).
- **Preserve URL contracts:** `?token=`, `?admin=1`, `?candidate=1`, `?preset=` via
  router query params.
- Add `DOMPurify` around `marked` output.
- No CDN for runtime libs; vendor/bundle everything.

## 4. Backend glue (small, deliberate)

- Serve `web/dist/` from FastAPI with an SPA fallback → `index.html`.
- Keep every REST + WebSocket route unchanged; keep `/novnc` mount.
- Expose `/openapi.json` for client type generation.
- Remove wildcard CORS (same-origin after cutover).
- Build step wired into `tools/start-web.sh` and the systemd unit.

## 5. Candidate UX changes

- Split default `[24, 76]`, min `[300, 520]`, persisted to `localStorage`;
  double-click gutter resets; **collapse-left toggle** for near-full-width desktop.
- Workspace tab bar 40 → 36px; Desktop/Terminal become a segmented control.
- Slim 52px header: exam name (truncated) · progress · timer · Flag · Submit ·
  `⋯` overflow (session-id copy, Fullscreen/Reload/New tab/Copy from Desktop/
  Recordings, admin-only End/Reset).
- Toast service, promise-based confirm dialog, prompt modal replace all native dialogs.
- TanStack Table **only** in admin; candidate uses cards/lists.

## 6. Milestones & acceptance

| Milestone | Tasks | Acceptance |
|---|---|---|
| M1 Foundation | FE-000..004 | build + dev proxy green; SPA served by FastAPI; typed API smoke test |
| M2 UI system | FE-010..014 | tokens audited (no raw hex outside tokens); toasts/dialogs/table working; zero glow/emoji |
| M3 Candidate | FE-020..029 | full exam journey at 1366×768 and 1920×1080; desktop prioritized; no native dialogs |
| M4 Admin | FE-030..035 | all admin actions via new dialogs/tables |
| M5 Cutover | FE-040..044 | legacy deleted; no external network calls; E2E + a11y pass; docs updated |

Strict parity: anti-cheat fullscreen/keyboard-lock, clipboard sync, replay, token
routing, timer server-sync must all behave as they do today.

## 7. Risks

| Risk | Mitigation |
|---|---|
| noVNC iframe URL/port + token propagation | explicit island contract + E2E check |
| Clipboard requires user gesture | port existing `pendingHostClipboardText` flush logic verbatim |
| Fullscreen/keyboard-lock browser fragility | isolate in `useFullscreen`; test Chrome + Firefox |
| xterm version/addon drift | pin xterm + addon-fit; replay uses asciinema cast |
| Router query/token changes breaking links | preserve `?token`/`?admin`/`?candidate`/`?preset` semantics |
| Cache busting change | hashed assets replace `?v=37/38` |

## 8. Future scope (not gating M1–M5)

Tracked as `FS-*` in `tasks.json`. Architecture must not preclude:

- **Auth & roles** (admin/user): `/login`, user store, password hashing, role guards.
- **Owned sessions & assignment:** admin assigns an exam to a user; user dashboard
  shows only their exams; sessions gain ownership fields (`user_id`, `assigned_by`)
  instead of one global `var/session.json`.
- **Hidden catalog:** users never see the full preset list, only their assignments.
- **Dynamic preset generator:** `POST /api/presets/generate {count, difficulty, domains?}`
  builds an ephemeral preset + session without listing individual questions.

Forward-compat constraints for the current build: include `/login`, `/dashboard`,
`/exam/:sessionId` routes and an `auth` store from day one; design the API client to
send credentials; model the session store around `sessionId` + optional ownership.
