# DISPATCH — FE-010

## 2026-09-10T07:51:24Z
You are assigned task **FE-010** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-010-implementer-4`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`useToast()` composable + `<Toaster/>` component supporting four variants
(info/success/warning/error), stacking, auto-dismiss, manual dismiss and an
`aria-live` region; mounted exactly once in `App.vue`.

### Acceptance criteria
1. four variants with semantic colors
2. stacking + auto-dismiss + manual dismiss
3. aria-live announced; keyboard dismissible

### Verification method
- `bun install` (web/frontend)
- `bun run test` — includes `tests/unit/toast.test.ts` (T1) and the accessibility
  audit (T2 substitute; literal axe is host-only)
- `bun run lint`, `bunx tsc --noEmit`, `bun run build`
- Manual: trigger each variant (browser; DEFERRED per PROTOCOL §6 on Bun-only host)

### Constraints
- One focused change, FE-010 scope only.
- Tokens only (no raw hex / glow / emoji); prefer `--color-*-text` variants.
- Update `EVIDENCE.md` with proof; set status in `tasks.json` (NOT `verified`).
