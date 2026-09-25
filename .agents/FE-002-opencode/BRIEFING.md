# BRIEFING — FE-002

## Mission
Establish the single source of truth for colour, radius, spacing, type and elevation in
the new Vue SPA, with a working dark/light theme switch, so that later UI tasks never
hand-code colours.

## 🔒 Identity
- Task: FE-002
- Role: implementer
- Agent: opencode
- Working directory: `.agents/FE-002-opencode/`
- Branch: `feature/frontend-vue-migration`

## Task contract
- **Depends on:** FE-001 (scaffold). ⚠️ FE-001 was `in-review`, not `verified`, when this
  task started; PROTOCOL §3 says dependencies should be `verified`. The assignment to
  execute FE-002 now was explicit, so work proceeded. See EVIDENCE "Protocol notes".
- **Acceptance criteria:**
  1. all palette values exposed as CSS variables; no raw hex in components
  2. dark and light themes both render with AA-contrast text
  3. `prefers-color-scheme` default + persisted manual toggle
- **Test cases:** (canonical: `tasks.json` → FE-002 → `tests`)
  1. T1 (audit) `rg '#[0-9a-fA-F]{3,6}' src/components src/views` → no matches
  2. T2 (e2e) toggle theme and reload → `data-theme` flips and persists; both themes AA
- **Verifier:** independent agent (not opencode)

## Key constraints
- Follow `decisions.md` D-001..D-009 (D-003 pins the slate+indigo palette).
- Strict behavioural parity (D-007) — unaffected by this task (no WS/URL changes).
- Do not self-certify; an independent verifier must sign off.
- No CDN/runtime network deps; no raw hex outside the token layer.

## Deliverable
- `web/frontend/src/assets/styles/tokens.css`
- `web/frontend/src/assets/styles/base.css`
- Supporting wiring: `src/composables/useTheme.ts`, `src/components/ThemeToggle.vue`,
  `src/main.ts`, `src/App.vue`, `index.html`.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md` (§2 design system)
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/assets/styles/`, `web/frontend/src/components/`,
  `web/frontend/src/composables/useTheme.ts`, `web/frontend/tests/`

## Artifact index
- `.agents/FE-002-opencode/DISPATCH.md`
- `.agents/FE-002-opencode/progress.md`
- `.agents/FE-002-opencode/EVIDENCE.md`
- `.agents/FE-002-opencode/TESTPLAN.md`
