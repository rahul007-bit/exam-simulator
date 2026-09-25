# DISPATCH — FE-005

## 2026-09-10T08:23:43Z
You are assigned task **FE-005** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-005-implementer-5`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Adopt Tailwind CSS (v4 via `@tailwindcss/vite`) and `@headlessui/vue`; expose the
existing design tokens to Tailwind via `@theme`; refactor base styles and the Toaster
to the new stack while preserving FE-002 and FE-010 acceptance.

### Acceptance criteria
1. `tailwindcss` + `@tailwindcss/vite` + `@headlessui/vue` installed and wired into the Vite build.
2. Design tokens exposed to Tailwind (`@theme`) so utilities resolve to the token
   palette; no raw hex in components/views.
3. `@headlessui/vue` used for at least one accessible primitive (toast enter/leave).
4. FE-002 acceptance (dark/light AA, no raw hex) and FE-010 acceptance
   (4 variants, aria-live, axe 0) still pass.

### Verification method
Independent verifier re-runs on the working tree:
```
cd web/frontend
bun run build && bun run lint && bunx tsc --noEmit && bun run test
bunx playwright test tests/e2e/toast.spec.ts
```
plus the FE-002 token/hex/theme tests and FE-010 toast tests, and confirms the
Tailwind plugin is active + no CDN/external URLs.

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Keep `tokens.css` values unchanged; preserve toast class hooks.
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
