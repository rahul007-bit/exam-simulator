# DISPATCH — FE-022

## 2026-09-10T09:30:10Z
You are assigned task **FE-022** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-022-implementer-9`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Candidate `TaskPane` component (task header with badges + markdown body) and a
markdown renderer: `marked` + `marked-highlight`/`highlight.js`, sanitized with
`DOMPurify`; inline and fenced code click-to-copy with visible feedback.

### Acceptance criteria
1. Markdown sanitized via DOMPurify.
2. Code copy works for inline and blocks with visible feedback.
3. Badges use neutral chips + semantic status colours only.

### Verification method
- `bun run test` (unit; includes XSS sanitisation + code-copy cases)
- `bunx vue-tsc --noEmit`
- `bun run lint`
- Manual: click inline code and a block copy button; observe feedback.

### Constraints
- One focused change; stay inside the FE-022 file ownership scope.
- Preserve parity behavior (legacy renderMarkdown / copyCode semantics).
- Update `EVIDENCE.md` with proof; do not edit `tasks.json` (orchestrator-owned).
