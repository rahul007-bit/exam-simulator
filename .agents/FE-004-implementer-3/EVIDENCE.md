# EVIDENCE — FE-004

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-3 (2026-09-10T07:36:53Z)

Re-claim after verifier rejection of implementer-2. This iteration is a **schema-only
fidelity fix** plus regenerated types; no application code changed.

### Root cause (from `.agents/FE-004-implementer-2/EVIDENCE.md`, Verifier section)
`AdminSessionItem` in `web/frontend/openapi.json` (the sole API type source) did not
match `web/server.py::admin_list_sessions` (lines 1353-1436):
omitted `container_running`/`current_index`/`type`/`url`, added a never-returned
`time_limit_minutes`, and typed `total_tasks` as non-null though invite rows return `None`.

### Handler facts re-derived (not guessed)
- `admin_list_sessions` (server.py:1353-1436) builds rows in 3 branches — active
  (1365-1377), invite (1398-1410), history/archived (1421-1434).
- `ExamSession` (`core/models.py:130-169`): `session_id: str`, `created_at: str`,
  `name: str`, `current_index: int = 0`, `candidate_token: Optional[str]`.
- `redis_bus.list_session_history` (`core/redis_bus.py:432-441`) returns `total_tasks`
  as an int and `scorecard_summary`/`archived_at` as optional.
- Fields present in **every** row: `session_id`, `candidate_token`, `name`, `status`,
  `created_at`, `time_remaining_seconds`, `container_running`, `total_tasks`, `type`, `url`.
- `current_index` is **absent** from archived rows; `archived_at` and
  `scorecard_summary` are **absent** from active/invite rows -> optional.
- `created_at` is always a `str`; `name`/`status`/`type`/`container_running` are never null.
- Nullable only where emitted: `session_id` (invite `None`), `candidate_token`
  (`Optional`), `time_remaining_seconds` (invite `None`), `total_tasks` (invite `None`),
  `current_index` (invite `None`), `url` (history row `None`), `archived_at`,
  `scorecard_summary`.

### Schema change — `openapi.json` `AdminSessionItem`

BEFORE (lines 890-904):
```json
"AdminSessionItem": {
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "name": { "type": "string" },
    "status": { "type": "string" },
    "created_at": { "type": ["string", "null"] },
    "archived_at": { "type": ["string", "null"] },
    "total_tasks": { "type": "integer" },
    "time_limit_minutes": { "type": ["integer", "null"] },
    "time_remaining_seconds": { "type": ["number", "null"] },
    "scorecard_summary": { "type": ["object", "null"], "additionalProperties": true },
    "candidate_token": { "type": ["string", "null"] }
  }
}
```

AFTER:
```json
"AdminSessionItem": {
  "type": "object",
  "required": [
    "session_id", "candidate_token", "name", "status", "created_at",
    "time_remaining_seconds", "container_running", "total_tasks", "type", "url"
  ],
  "properties": {
    "session_id": { "type": ["string", "null"] },
    "candidate_token": { "type": ["string", "null"] },
    "name": { "type": "string" },
    "status": { "type": "string" },
    "created_at": { "type": "string" },
    "archived_at": { "type": ["string", "null"] },
    "time_remaining_seconds": { "type": ["number", "null"] },
    "container_running": { "type": "boolean" },
    "total_tasks": { "type": ["integer", "null"] },
    "current_index": { "type": ["integer", "null"] },
    "type": { "type": "string", "enum": ["active", "invite", "archived"] },
    "url": { "type": ["string", "null"] },
    "scorecard_summary": { "type": ["object", "null"], "additionalProperties": true }
  }
}
```

Diff summary: **+`container_running`(bool)**, **+`current_index`(int|null)**,
**+`type`(enum)**, **+`url`(string|null)**, **−`time_limit_minutes`**,
**`total_tasks` -> integer|null**; `created_at` string|null -> string (handler never
emits null); `required` added for always-present fields.

### Optional doc fix — `/api/session/restore` (server.py:1108-1109)
Added `"400": { "$ref": "#/components/responses/Error" }` alongside 404/429
(handler raises 400 when `session_id` is falsy).

### Generated type (after `bun run gen:api`) — `src/api/schema.d.ts`
```ts
AdminSessionItem: {
    session_id: string | null;
    candidate_token: string | null;
    name: string;
    status: string;
    created_at: string;
    archived_at?: string | null;
    time_remaining_seconds: number | null;
    container_running: boolean;
    total_tasks: number | null;
    current_index?: number | null;
    /** @enum {string} */
    type: "active" | "invite" | "archived";
    url: string | null;
    scorecard_summary?: { [key: string]: unknown; } | null;
};
```
No `time_limit_minutes`. Matches the handler union.

### Commands run + observed output (cwd `web/frontend/`)
```
python scripts/agents_board.py --check        -> [tasks] validation OK (44 tasks)
python scripts/agents_board.py --claim FE-004 implementer-3
  -> [tasks] FE-004 claimed by implementer-3

bun run gen:api
  $ node scripts/gen-api.mjs
  [gen:api] snapshot: C:\...\web\frontend\openapi.json
  [gen:api] wrote C:\...\web\frontend\src\api\schema.d.ts      GEN_API_EXIT=0

bun run typecheck
  $ node scripts/gen-api.mjs && vue-tsc --noEmit              TYPECHECK_EXIT=0

bun run test
  ✓ tests/unit/hex-audit.test.ts    (2 tests)
  ✓ tests/unit/tokens.test.ts       (27 tests)
  ✓ tests/unit/theme.test.ts        (7 tests)
  ✓ tests/unit/smoke.test.ts        (1 test)
  ✓ tests/unit/theme-toggle.test.ts (1 test)
  ✓ tests/unit/stores.test.ts       (10 tests)
  Test Files  6 passed (6) · Tests  48 passed (48)            TEST_EXIT=0

bun run lint
  $ eslint .                                                 LINT_EXIT=0

bun run build
  $ node scripts/gen-api.mjs && vue-tsc --noEmit && vite build
  ✓ 50 modules transformed.
  ../dist/index.html 1.24 kB · assets/index-*.css 6.38 kB · assets/index-*.js 105.56 kB
  ✓ built in 983ms                                           BUILD_EXIT=0
```

### Screenshots
n/a (headless, no backend; browser leg host-only, DEFERRED per PROTOCOL §6).

### Test cases executed (see TESTPLAN.md)
**T1 PASS** (gen:api + typecheck exit 0), **T2 PASS** (48/48, incl. 10 store tests).
Edge cases E1/E2 (nullability + presence/absence audit) PASS.

### Self-check against acceptance criteria
1. **types generated from /openapi.json — PASS.** `bun run gen:api` rewrites
   `src/api/schema.d.ts`; the corrected `AdminSessionItem` is consumed via
   `components['schemas']` (`src/api/admin.ts:16`).
2. **client covers session, timer, presets, actions endpoints — PASS** (unchanged;
   full suite green).
3. **stores expose typed state and actions; smoke test hits /api/session — PASS**
   (48/48 tests incl. `stores.test.ts`).
4. **Verifier blocker resolved — PASS.** `AdminSessionItem` now matches
   `admin_list_sessions` exactly.

### Safety / scope
- No destructive git commands; nothing committed/amended/pushed/PR'd.
- Only FE-004-scoped files changed: `web/frontend/openapi.json` (tracked-untracked
  snapshot) and the generated/ignored `web/frontend/src/api/schema.d.ts`; plus
  `.agents/FE-004-implementer-3/**` and `tasks.json`/`BOARD.md` via the CLI.
- `git status --porcelain -- web/frontend/openapi.json`: `?? web/frontend/openapi.json`
  (untracked pre-existing tree; no unrelated file touched).

### Deferrals (host-only / tooling)
- **Live `/openapi.json` fetch:** DEFERRED — platform host stalls before sending the
  body (documented by implementer-2/verifier-3); committed snapshot remains the source.
- **Live `/api/session` against FastAPI:** DEFERRED — backend Linux-only (D-006).
- Browser/Playwright leg: host-only (PROTOCOL §6).

## Verifier — verifier-3 (2026-09-10T07:19:00Z)

Independent re-verification of the rework. I re-derived the handler shape from
`web/server.py::admin_list_sessions` (L1353-1436) and `core/models.py`; I did not rely
on implementer-3's quoted "AFTER" JSON. Working dir `web/frontend/`.

### openapi.json fidelity — AdminSessionItem (blocker from my prior rejection)

I encoded the three emitted row shapes and machine-checked the schema against them
(`fe004_adminitem_check.py`). Result: **ALL CHECKS PASSED**.
- **active** (L1365-1377): session_id str, candidate_token str|null, name str, status
  str, created_at str, time_remaining_seconds int|null, container_running bool,
  total_tasks int, current_index int, type "active", url str — no archived_at/scorecard_summary.
- **invite** (L1398-1410): session_id **null**, total_tasks **null**, current_index
  **null**, time_remaining_seconds null, container_running false, type "invite", url str.
- **archived** (L1421-1434): session_id str, archived_at str|null, scorecard_summary
  obj|null, **no current_index**, total_tasks int, type "archived", url str|null.

Assertions verified:
- `properties` set == union of all row keys (13 fields); no `time_limit_minutes`.
- `required` == intersection of always-present keys: session_id, candidate_token, name,
  status, created_at, time_remaining_seconds, container_running, total_tasks, type, url.
- `current_index`, `archived_at`, `scorecard_summary` correctly optional.
- Nullability matches exactly where the handler emits null; `type` enum ==
  {active, invite, archived}; `total_tasks` = integer|null.
- Generated `schema.d.ts:545-562` reflects the above (`current_index?: number | null`,
  `type: "active" | "invite" | "archived"`, no `time_limit_minutes`).

### No-regression check on the rest of the contract
Full schema inventory re-extracted and compared to my pre-rework baseline: **identical
for every schema except `AdminSessionItem`**. Endpoint set unchanged; the only other
delta is the intended `400` response added to `POST /api/session/restore`
(`server.py:1108-1109`, legitimate). All other covered endpoints still match source
(session/timer/presets/actions/admin auth+config+resources/invite).

### Commands re-run (my output, cwd `web/frontend/`)
```
python scripts/agents_board.py --check  -> validation OK (44 tasks)        EXIT 0
bun run gen:api                         -> wrote src/api/schema.d.ts       EXIT 0
bun run typecheck (gen:api && vue-tsc)  -> (no errors)                     EXIT 0
bunx tsc --noEmit (local TS 5.7.3)      -> (no errors)                     EXIT 0
bun run lint (eslint .)                 -> (no errors)                     EXIT 0
bun run test                            -> 6 files / 48 tests passed       EXIT 0
bun run build                           -> 50 modules, built in 1.03s      EXIT 0
```
`bun run test`: hex-audit 2, tokens 27, **theme 7**, smoke 1, **theme-toggle 1**,
stores 10. FE-002 theme suites unaffected (only the Node 26 `localStorage is not
available` warning remains, absorbed by the unchanged `tests/setup.ts` shim).

### Previously-failing / new checks
- E1 (schema fidelity) — **PASS** (asserted from generated `schema.d.ts`).
- E2 (nullable-only-where-null) — **PASS** (machine-checked).
- T1 — **PASS**; T2 — **PASS** (10/10 store tests). Live-backend leg DEFERRED.
- FE-002 theme tests — **PASS**, no masking.

### Scope note (not a FE-004 defect)
`git status` shows an untracked root file `no` (244 B) containing VPN "DF" MTU ping
output, created 2026-09-10T13:09 — unrelated to FE-004 and consistent with the reported
client VPN-MTU diagnosis. Left untouched. All FE-004 changes remain schema-only
(`openapi.json` + regenerated ignored `schema.d.ts`).

### Verdict: `verified`
The rejection blocker is resolved: `AdminSessionItem` now faithfully represents the
active/invite/archived row union with correct required/optional/nullability. All
acceptance criteria, T1/T2, lint/typecheck/build/test pass with no regression.

Host-only items remain: live `/openapi.json` diff and live `/api/session` (D-006);
not blocking (VPN MTU reachability issue on the client).
