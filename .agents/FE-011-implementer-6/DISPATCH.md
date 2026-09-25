# DISPATCH — FE-011

## 2026-09-10T08:44:00Z
You are assigned task **FE-011** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-011-implementer-6`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Promise-based confirm + prompt primitives replacing native `confirm()`/`prompt()`:

- `src/composables/useConfirm.ts` — module-level singleton exposing
  `confirm(options): Promise<boolean>` and `prompt(options): Promise<string | null>`
  (options: `title?`, `message?`, `confirmLabel?`, `cancelLabel?`, `danger?`,
  `placeholder?`, `defaultValue?`). Concurrent calls are **queued FIFO**.
- `src/components/ConfirmDialog.vue` — single dialog host mounted once in
  `App.vue`, built on Headless UI `Dialog` (focus trap, `Escape`, `aria-modal`).

### Acceptance criteria
1. `useConfirm` resolves `true`/`false`.
2. Prompt modal returns value or `null`.
3. Focus trap + `Escape` + `aria-modal`.

### Verification method
- `bun run build`
- `bun run lint`
- `bunx tsc --noEmit`
- `bun run test` (T1: `tests/unit/confirm.test.ts`)
- `npx playwright test tests/e2e/confirm.spec.ts` (T2, host/browser)

### Constraints
- One focused change; preserve parity behavior (WS, clipboard, timer, token routing).
- No raw hex / glow / emoji (FE-002/FE-005); Tailwind utilities + existing tokens.
- Update `EVIDENCE.md` with proof; set status via `scripts/agents_board.py`.
