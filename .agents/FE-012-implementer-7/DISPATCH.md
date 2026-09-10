# DISPATCH — FE-012

## 2026-09-10T09:09:37Z
You are assigned task **FE-012** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-012-implementer-7`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Reusable primitives under `web/frontend/src/components/ui/`:
`Button`, `Input`, `Select`, `Badge`/`Chip`, `Card`, `Modal`, `Spinner`, `SegmentedControl`,
plus a barrel export and a dev-only primitives gallery route `/dev/ui`.

### Acceptance criteria
1. All variants styled from tokens only (no raw hex, no glow/gradient, no emoji).
2. Accessible: `focus-visible` rings from the focus-ring tokens; disabled + loading
   states; proper labels/roles (Headless UI `Dialog` / `Listbox` / `RadioGroup`).
3. Gallery route renders every primitive in its variants/states, out of candidate/admin flows.

### Verification method
- `bun run build`, `bun run lint`, `bunx tsc --noEmit`, `bun run test`
- `npx playwright test` (full suite; Chromium) including the new gallery axe + keyboard tests
- manual keyboard tab-through of `/dev/ui`

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing) — no candidate/admin edits.
- Update `EVIDENCE.md` with proof; set status in `tasks.json` via the board CLI.
- Do not self-verify.
