# cka-labs frontend

Vue 3 + TypeScript + Vite SPA that replaces the legacy vanilla-JS candidate and
admin frontends. Built from `web/frontend/` into `web/dist/`, which is served
directly by FastAPI.

## Requirements

- Node.js >= 20.19.0 (LTS 22 recommended)
- npm

## Development

On the platform host (full stack available):

```bash
cd web/frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies to the FastAPI backend
on `http://localhost:3000` for `/api`, `/ws` and `/novnc`.

To point at a different backend (e.g. from a workstation):

```bash
VITE_BACKEND=http://192.168.1.249:3000 npm run dev
```

## Build

```bash
npm run build   # type-check (vue-tsc) + Vite build -> web/dist/
```

`web/dist/` is **not** committed; it is produced on deploy (decision D-005).

## Scripts

| Script              | Purpose                                                 |
| :------------------ | :------------------------------------------------------ |
| `npm run dev`       | Vite dev server + backend proxy                         |
| `npm run build`     | Type-check and build to `web/dist/`                     |
| `npm run typecheck` | `vue-tsc --noEmit`                                      |
| `npm run lint`      | ESLint (flat config)                                    |
| `npm run format`    | Prettier write                                          |
| `npm run test`      | Vitest unit tests                                       |
| `npm run test:e2e`  | Playwright E2E (starts the dev server)                  |
| `npm run gen:api`   | Generate typed API client from `/openapi.json` (FE-004) |

## Structure

```
src/
  main.ts  App.vue
  router/            # "/" candidate, "/admin" admin, future-scope placeholders
  views/             # route views (CandidateView, AdminView, LoginView, ...)
  components/
    layout/          # AppShell, AppHeader, OverflowMenu, WorkspaceSplit
    ui/              # design-system primitives (Button, Modal, DataTable, ...)
    candidate/       # TaskPane, QuestionDrawer, ExamScorecard, RecordingsModal, ...
    admin/           # config/resource/invite forms, infrastructure table, ObserveOverlay, ...
    workspace/       # workspace "islands": XTerm, NoVncFrame, WorkspaceTabs,
                     #   ClipboardBridge, ReplayPlayer
  composables/       # useVnc, useTerminal, useTimer, useClipboard, useSplitPane, ...
  stores/            # Pinia stores (session, presets, timer, auth)
  api/               # typed API clients (+ generated schema.d.ts)
  assets/styles/     # design tokens + base styles (FE-002)
tests/
  unit/              # Vitest unit tests
  e2e/               # Playwright E2E specs
```

See `.agents/frontend-migration/PLAN.md` for the full design and task board.
