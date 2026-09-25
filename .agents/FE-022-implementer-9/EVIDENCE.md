# EVIDENCE — FE-022

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-9 (2026-09-10T09:35:00Z)

### Deliverable
A sanitized markdown pipeline and candidate task pane:
- `useMarkdown` renders markdown with `marked` + `marked-highlight`/`highlight.js`
  and sanitizes the result with `DOMPurify` (single entry point `renderMarkdown`).
- `MarkdownRenderer.vue` binds the sanitized HTML and decorates code for
  click-to-copy (inline + fenced), with token-coloured visible feedback and
  keyboard activation.
- `TaskPane.vue` shows the task header (FE-012 `Badge` chips: neutral metadata +
  danger `FLAGGED`) over the markdown body.
- `taskBadges()` derives the neutral/semantic badge list (difficulty stays hidden
  to match legacy).

### Files touched (all inside the FE-022 scope; untracked `web/frontend/` tree)
| File | Change |
| :--- | :--- |
| `src/composables/useMarkdown.ts` | **new** — marked + marked-highlight + highlight.js + DOMPurify pipeline (`renderMarkdown`, `sanitizeHtml`, `useMarkdown`) |
| `src/composables/highlight-lib-common.d.ts` | **new** — ambient types for the `highlight.js/lib/common` subpath (package ships root types only) |
| `src/components/MarkdownRenderer.vue` | **new** — sanitized body + code decoration/copy + token-only highlight palette |
| `src/components/candidate/TaskPane.vue` | **new** — task header badges + markdown body |
| `src/components/candidate/task.ts` | **new** — `TaskPaneTask`, `TaskBadge`, `taskBadges()` |
| `tests/unit/markdown.test.ts` | **new** — 21 tests (sanitisation, highlighting, copy, badges, constraints audit) |

No shared/forbidden file was modified: `package.json`, `bun.lock`, `App.vue`,
`src/main.ts`, `src/router/index.ts`, `eslint.config.js`, `vite.config.ts`,
`playwright.config.ts`, `tests/setup.ts`, `src/assets/styles/**`,
`src/components/ui/**`, `src/stores/**` are all untouched.

### Public API
```ts
// src/composables/useMarkdown.ts
function renderMarkdown(source?: string | null): string     // sanitized HTML
function sanitizeHtml(html: string): string                 // DOMPurify only
function useMarkdown(): { renderMarkdown; sanitizeHtml }

// src/components/MarkdownRenderer.vue
props:  { source?: string; emptyText?: string }
emits:  { copy: [text: string] }

// src/components/candidate/TaskPane.vue
props:  { task?: TaskPaneTask | null; emptyText?: string }

// src/components/candidate/task.ts
interface TaskPaneTask { task_num; title; description; points; namespace?; target_context?; is_flagged? }
function taskBadges(task: TaskPaneTask): Array<{ key; label; variant }>
```

### Commands run + output
```
$ bunx vitest run tests/unit/markdown.test.ts
 ✓ tests/unit/markdown.test.ts (21 tests) 217ms
 Test Files  1 passed (1)
      Tests  21 passed (21)

$ bun run test
 ✓ tests/unit/tokens.test.ts (27)
 ✓ tests/unit/hex-audit.test.ts (2)
 ✓ tests/unit/theme.test.ts (7)
 ✓ tests/unit/smoke.test.ts (1)
 ✓ tests/unit/theme-toggle.test.ts (1)
 ✓ tests/unit/stores.test.ts (10)
 ✓ tests/unit/timer.test.ts (12)
 ✓ tests/unit/markdown.test.ts (21)
 ✓ tests/unit/confirm.test.ts (8)
 ✓ tests/unit/toast.test.ts (14)
 ✓ tests/unit/ui-primitives.test.ts (27)
 Test Files  11 passed (11)
      Tests  130 passed (130)

$ bunx vue-tsc --noEmit
(no output; exit 0)

$ bun run lint
$ eslint .
(no output; exit 0)
```

### Test cases executed (see TESTPLAN.md): T1 PASS, T2 PASS, A1–A5 PASS

### Self-check against acceptance criteria
1. **Markdown sanitized via DOMPurify** — PASS. `renderMarkdown('<img src=x onerror=alert(1)>')`
   contains neither `onerror` nor `alert(1)`; `<script>`, `javascript:` URLs,
   `onmouseover`, `<iframe>`, `<style>` and inline `style=` are all removed.
   `MarkdownRenderer` never injects the handler into the live DOM.
2. **Code copy works for inline and blocks with feedback** — PASS. Fenced blocks
   get a `[data-code-copy]` button (label `Copy` → `Copied`, `is-copied` class);
   inline `<code>` gets `role=button`/`tabindex=0`, click and Enter/Space copy,
   add `is-copied`, and emit `copy` with the exact text. Clipboard writes go
   through `navigator.clipboard.writeText` with the legacy `execCommand`
   fallback.
3. **Badges use neutral chips + semantic status only** — PASS. `taskBadges()`
   returns neutral for task/points/context/namespace and `danger` only for
   `FLAGGED`; rendered with the FE-012 `Badge` (imported read-only).

### Constraints audit
- No raw hex / `text-shadow` / `drop-shadow` / `blur(` / emoji in any FE-022 file
  (unit audit test). Highlight palette maps only to `--color-*` tokens.
- Browser/Playwright leg: **DEFERRED** per PROTOCOL §6 (host-only).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
