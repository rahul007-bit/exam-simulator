# ORIGINAL REQUEST — Frontend Migration Program

Recorded: 2026-09-10
Branch: `feature/frontend-vue-migration`
Status: active

## Verbatim user intent

> if we had to migrate current frontend to something better for this project what
> should we pick do some brainstorming on this

> real data table is good have but not everywhere also i want to improve the ui
> it's too ai sloop not professional and also alway see that we best UI and UX
> user experince
>
> and condidate page alway prioties more userspace to interaccting with desktop
> the right side since right we have soo much noice here and where, give more
> space right side panel
>
> use a better color scheme noo too much glowing effects use better pop alerts
> not alert() function
>
> create a manitainable task list so that later agents and work also try to
> distrubute the task and validate the task done by other agents

> also keep in mind in future we may need to add auth and improve session
> management so that admin can assign exams to user and user login to account and
> see there exam and start any random exam preset without shwoing all presets
> also create a preset with select number of question without listing questions
> like there select 5 question with deficulty of medium then system generate
> preset for them and create session for that
>
> just add this as future scope

## Locked decisions (from planning Q&A)

| Topic | Decision |
|---|---|
| Framework | Vue 3 + TypeScript + Vite |
| Component layer | Tailwind CSS + Headless UI (Vue) + TanStack Table (admin only) |
| Color scheme | Slate neutrals + single indigo accent; semantic status colors only |
| Themes | Dark + light toggle |
| Offline assets | Preferred, not strictly required (self-host where practical) |
| Scope | Migrate both candidate + admin, unified single SPA |
| Build pipeline | Build on deploy (platform host); `web/dist` not committed |
| Dev environment | Platform host (full stack: FastAPI + Redis + pty) |
| Branch | `feature/frontend-vue-migration` off `feature/phase-3-arch` |
| Parity | Strict behavioral parity + redesign |
| Task tracking | Integrated with `.agents/` flow; independent verifier per task |

## Current frontend baseline (pre-migration)

- Vanilla JS SPA, no build step, no `package.json`.
- Candidate: `web/static/index.html` (408 lines) + `web/static/js/app.js` (2,413 lines, 56 global functions).
- Admin: `web/static/admin.html` (1,028 lines) + `web/static/js/admin.js` (1,543 lines).
- Shared: `web/static/css/style.css` (1,592 lines).
- Backend: FastAPI (`web/server.py`, 2,347 lines) serves static files and owns all
  WebSockets: PTY terminal (`server.py:1672`), noVNC proxy (`server.py:1878`),
  session pub/sub (`server.py:2056`), plus ~35 REST endpoints.
- CDN dependencies despite an "offline" product: Google Fonts, split.js, marked,
  highlight.js, xterm + addon-fit (`index.html:7-11,401-405`, `admin.html:1022-1025`).
- Native dialogs: 30+ `alert()` / `confirm()` / `prompt()` across `app.js` / `admin.js`.

## Non-goals for this program

- Changing the Python/FastAPI backend architecture beyond static-serving glue.
- Auth, per-user assignment, dashboard, dynamic preset generator (future scope — `FS-*`).
