# DISPATCH — FE-032

## 2026-09-10T11:19:53Z
You are assigned task **FE-032** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-032-implementer-22`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Admin config and resource forms: a default-preset selector backed by
`/api/admin/config` (GET current, POST to set) with the preset catalogue loaded
from `/api/presets`, and a max-concurrent-sessions form backed by
`/api/admin/resources` (GET/POST) with client-side validation (`>= 1`) plus the
current resource snapshot. Inline/toast error feedback and toast success.

### Acceptance criteria
1. Forms reflect `/api/admin/config` and `/api/admin/resources`.
2. Validation errors shown via toast/inline.
3. Success feedback via toast.

### Verification method
- `bunx vue-tsc --noEmit` (must pass; batch testing paused).
- Host-only e2e (deferred locally per PROTOCOL §6):
  - set default preset then reload -> value persists from `/api/admin/config`.
  - submit invalid max sessions -> inline/toast error, no save.
- Manual save/load against a running backend; invalid input path.

### Constraints
- One focused change.
- File ownership: `views/AdminView.vue`, `components/admin/**`,
  `composables/useAdminConfig.ts` only.
- Tailwind + tokens only; no raw hex/glow/emoji.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; leave status handling to the orchestrator
  (batch pre-claims; agents do not run the board CLI).
