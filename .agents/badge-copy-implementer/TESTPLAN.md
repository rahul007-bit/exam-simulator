# TESTPLAN — badge-copy

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test -- badge-copy` | copyable Badge renders a button, copies text, emits, stops propagation | PASS | pending |
| T2 | unit | `bun run test -- badge-copy` | copied `check` state toggles and reverts after 1.2s | PASS | pending |
| T3 | unit | `bun run test -- badge-copy` | neutral copyable badge uses accent; semantics preserved; aria-label | PASS | pending |
| T4 | unit | `bun run test -- question-nav` | drawer cards remain queryable/clickable with role=button + tabindex | PASS | pending |
| T5 | audit | `bun run test -- hex-audit decor-audit` | no raw hex/glow/emoji introduced | PASS | pending |
| T6 | static | `bun run lint && bunx vue-tsc --noEmit` | clean | PASS | pending |
| T7 | suite | `bun run test` | 202 passed (baseline 194 + 8) | PASS | pending |

## Edge cases / additions
- `copyText` omitted → slot text extracted (string/number vnodes).
- `copyLabel` omitted → `Copy "<text>"`.
- Nested badge inside a clickable card does not activate the card.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration`
- Host: Windows / pwsh, bun 1.4.2
- Browser(s): n/a (jsdom unit tests)

## Verdict
- Implementer: PASS, 2026-09-10
- Verifier: pending
