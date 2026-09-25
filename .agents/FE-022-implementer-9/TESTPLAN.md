# TESTPLAN — FE-022

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-022` → `tests`).
Mirrored below, plus the added edge/audit cases.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bunx vitest run tests/unit/markdown.test.ts` — `renderMarkdown('<img src=x onerror=alert(1)>')` | DOMPurify strips `onerror`; no executable attribute/tag survives | PASS (`onerror` + `alert(1)` absent; also `<script>`, `javascript:`, `onmouseover`, `<iframe>`, `style=` cases) | |
| T2 | manual / unit | click inline code + block copy button (`tests/unit/markdown.test.ts` code-copy suite) | clipboard receives the code text; visible feedback (`Copied` label / `is-copied` class) | PASS (inline + block copy, keyboard activation, `copy` event emitted) | |
| A1 | audit | scan FE-022 files for raw hex / glow / emoji | none | PASS | |
| A2 | unit | `taskBadges()` variants | neutral for metadata, danger only for flagged | PASS | |
| A3 | integration | `bun run test` (full unit suite) | all pass, no regressions | PASS (130 tests, 11 files) | |
| A4 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS | |
| A5 | audit | `bun run lint` | exit 0 | PASS | |

## Edge cases / additions
- Unknown fenced language falls back to plaintext without throwing.
- Keyboard activation (Enter/Space) copies inline code.
- `copy` event emitted with the exact copied text.
- `<iframe>`, `<style>`, and inline `style=` attributes are removed.
- Empty source renders the configurable empty text and no `.markdown-body`.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (not committed)
- Host: local workstation (win32) — Bun runtime; browser leg DEFERRED per PROTOCOL §6
- Browser(s): n/a (unit/jsdom)

## Verdict
- Implementer: PASS, 2026-09-10T09:35:00Z
- Verifier: pending
