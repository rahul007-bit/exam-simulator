# TESTPLAN — FE-001

Canonical cases: `tasks.json` → FE-001 → `tests`.

Runtime note: Node/npm were not available in the authoring environment (Windows);
verification was executed with **Bun 1.4.2** (same Vite/Vitest toolchain). The
platform host must re-run with `npm` per acceptance (D-006).

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | integration | `bun install && bun run build` | exit 0 and `web/dist/index.html` exists | PASS — built 33 modules in 646ms; `web/dist/{index.html,assets/*}` emitted | **PASS (verifier-1)** — `web/dist` removed first; `bun install` exit 0; `bun run build` exit 0 in 413ms; `web/dist/index.html` emitted + `assets/` |
| T2 | audit | `bun run lint` + `bunx tsc --noEmit` | exit 0 | PASS — eslint clean; tsc exit 0; `format:check` clean | **PASS (verifier-1)** — `bun run lint` exit 0; `bunx tsc --noEmit` exit 0; `bun run format:check` clean |
| T3 | unit | `bun run test` | smoke test passes | PASS — 1 test passed (tests/unit/smoke.test.ts) | **PASS (verifier-1)** — `bun run test` exit 0; 5 files / 38 tests passed (smoke suite included) |

## Edge cases / additions
- T1 also confirmed `emptyOutDir` re-emitted a clean `web/dist` (old assets replaced).
- Dev proxy (`acceptance #2`) could not be fully exercised here because the FastAPI
  backend only runs on the platform host. Config verified: `/api`, `/ws`, `/novnc`
  -> `VITE_BACKEND` (default `http://localhost:3000`). Deferred to host verifier.
- A Vitest 2.x → Vite 6 nested-copy type conflict was fixed by upgrading to Vitest 3.

## Environment
- Commit / build: `web/dist` produced from `feature/frontend-vue-migration` (uncommitted)
- Host: Windows workstation, Bun 1.4.2 (no Node/npm on PATH)
- Verification target: platform host (D-006) with Node >= 20.19

## Verdict
- Implementer: T1/T2/T3 PASS (Bun); dev-proxy integration deferred to host.
- Verifier (**verifier-1**, 2026-09-10T06:09:10Z): T1/T2/T3 PASS (independently reproduced
  with Bun 1.4.2). Dev server boots and `/api` proxy is wired (ECONNREFUSED only because no
  FastAPI here) — live FastAPI reachability is **host-only**. Literal Playwright suite also
  passes locally (3/3), so the browser leg is not a deferral. **Verdict: verified.**
