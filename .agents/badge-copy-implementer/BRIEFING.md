# BRIEFING — badge-copy

## Mission
Make the candidate exam-page chips clickable-to-copy and coloured, via an
opt-in extension to the shared `Badge` component that leaves admin badges and
non-copyable badges unchanged.

## 🔒 Identity
- Task: badge-copy
- Role: implementer
- Working directory: .agents/badge-copy-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** none
- **Acceptance criteria:**
  1. `Badge` gains opt-in `copyable`/`copyText`/`copyLabel` + `copy` emit with no
     behaviour change when disabled.
  2. Copy uses `navigator.clipboard.writeText` with `fallbackCopyText` fallback,
     stops propagation, shows a transient check state, cleans up on unmount.
  3. Neutral copyable badges render accent; semantic variants preserved.
  4. Every candidate badge under `components/candidate/` is copyable except
     `PresetModal.vue` "Selected" badges.
  5. Tokens only (hex/decor audits), no raw hex/emoji/glow.
- **Verifier:** independent agent

## Key constraints
- Strict behavioral parity (D-007); tokens only (D-003).
- No `bun run build`, no Playwright, no commit/push.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Files in scope: `src/components/ui/Badge.vue`, `src/components/candidate/*`,
  `tests/unit/badge-copy.test.ts`, `tests/unit/question-nav.test.ts`

## Artifact index
- `.agents/badge-copy-implementer/DISPATCH.md`
- `.agents/badge-copy-implementer/progress.md`
- `.agents/badge-copy-implementer/EVIDENCE.md`
