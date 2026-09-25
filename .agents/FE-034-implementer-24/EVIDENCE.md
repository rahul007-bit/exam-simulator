# EVIDENCE — FE-034

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-24 (2026-09-10 11:27 UTC)
- Deliverable: admin fleet infrastructure table + composable.
- Files touched (created):
  - `web/frontend/src/composables/useAdminInfrastructure.ts`
  - `web/frontend/src/components/admin/AdminInfrastructureTable.vue`
- Commands run + output:
  ```
  PS> bunx vue-tsc --noEmit
  EXIT=0
  ```
  (TESTING PAUSED: no test/build/Playwright/board CLI run.)
- Screenshots: n/a (browser host-only; deferred).
- Test cases executed (see TESTPLAN.md): T1 static-only PASS (type-level); runtime leg DEFERRED.
- Self-check against acceptance criteria:
  1. nodes + docker + incus resources listed — PASS — nodes grid + merged
     `resources` DataTable; Docker rows render `—` for IP and "Host default"
     limits, Incus rows render `ip`/`cpu_limit`/`mem_limit`.
  2. terminate calls `/api/admin/infrastructure/terminate` — PASS —
     `terminateResource()` POSTs `{ kind, node, name }` via `apiRequest`.
  3. confirmation via dialog — PASS — `onTerminate()` awaits `useConfirm()`'s
     promise; cancel returns before the API call; success/error reported via
     `useToast`.

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks: <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
