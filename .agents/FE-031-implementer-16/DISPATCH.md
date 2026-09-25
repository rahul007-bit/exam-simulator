# DISPATCH — FE-031

## 2026-09-10T10:57:09Z
You are assigned task **FE-031** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-031-implementer-16`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Admin sessions/invites/history `DataTable` in `AdminView.vue` with terminate,
reset and end row actions driven by `useConfirm` + surfaced via `useToast`, plus a
`useAdminSessions` fetch/mutate composable and an actions dialog component.

### Acceptance criteria
1. Table sorting/filtering/pagination via the shared `DataTable` primitive.
2. Row actions call `/api/admin/sessions/{identifier}/{terminate|reset|end}`.
3. No native `confirm()`/`alert()` — all gated by `useConfirm`.

### Verification method
- `bunx tsc --noEmit` (batch profile).
- Manual: sign in at `/admin`, sort/filter/paginate, select a row, run each action
  and confirm the endpoint request in devtools.
- Audit: no `window.confirm`/`window.alert` in the shipped source.

### Constraints
- One focused change; strict file ownership (see BRIEFING).
- Preserve parity: invites only allow terminate; archived only terminate; active
  allows terminate/reset/end.
- Update `EVIDENCE.md`; do not commit.
