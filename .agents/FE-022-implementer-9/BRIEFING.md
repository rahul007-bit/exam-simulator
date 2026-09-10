# BRIEFING — FE-022

## Mission
Deliver the candidate task pane and a hardened markdown renderer: sanitized
(marked + DOMPurify) task instructions with highlight.js code, click-to-copy for
inline and block code with visible feedback, and neutral/semantic header badges.

## 🔒 Identity
- Task: FE-022
- Role: implementer
- Working directory: .agents/FE-022-implementer-9
- Branch: feature/frontend-vue-migration
- Agent: implementer-9

## Task contract
- **Depends on:** FE-012 (UI primitives — verified)
- **Acceptance criteria:**
  1. markdown sanitized via DOMPurify
  2. code copy works for inline and blocks with feedback
  3. badges use neutral chips + semantic status only
- **Test cases (tasks.json):**
  1. T1 (unit): render `<img src=x onerror=alert(1)>` → sanitized by DOMPurify
  2. T2 (manual): click inline code and block copy → copied with visible feedback
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve legacy clipboard/copy behaviour.
- Tokens/Tailwind only: no raw hex, no glow/gradient, no emoji.
- Only create/modify files in the FE-022 ownership scope.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Legacy behaviour: `web/static/js/app.js:205-343` (`renderMarkdown`, `copyCode`,
  `copyInlineCode`), `web/static/index.html:90-105`
- Files in scope:
  - `web/frontend/src/composables/useMarkdown.ts` (+ `highlight-lib-common.d.ts`)
  - `web/frontend/src/components/MarkdownRenderer.vue`
  - `web/frontend/src/components/candidate/TaskPane.vue`
  - `web/frontend/src/components/candidate/task.ts`
  - `web/frontend/tests/unit/markdown.test.ts`

## Artifact index
- `.agents/FE-022-implementer-9/DISPATCH.md`
- `.agents/FE-022-implementer-9/progress.md`
- `.agents/FE-022-implementer-9/EVIDENCE.md`
- `.agents/FE-022-implementer-9/TESTPLAN.md`
