# DISPATCH — badge-copy

## 2026-09-10T00:00:00Z
You are assigned task **badge-copy** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/badge-copy-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Opt-in click-to-copy, coloured `Badge` chips on the candidate exam page. Extend
`src/components/ui/Badge.vue` with `copyable`/`copyText`/`copyLabel` + `copy`
emit, then apply to all candidate badges except `PresetModal.vue` "Selected".

### Acceptance criteria
1. Non-copyable `Badge` renders exactly as before.
2. Copyable `Badge` is a labelled `<button>` that copies its text with clipboard
   fallback, stops propagation, shows a transient copied state, cleans up.
3. Neutral copyable badges use accent styling.
4. All candidate badges copyable; PresetModal excluded.
5. Existing tests remain green; lint + vue-tsc + vitest pass.

### Verification method
- `bun run lint`
- `bunx vue-tsc --noEmit`
- `bun run test`

### Constraints
- One focused change; no commit/push.
- Preserve parity behaviour (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof.
