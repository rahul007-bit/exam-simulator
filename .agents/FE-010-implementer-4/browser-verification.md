# FE-010 — Browser axe + manual trigger verification

Date: 2026-09-10
Capability: host item "browser axe / manual variant trigger" (previously DEFERRED by
the implementer/verifier because the Bun-only host cannot start Playwright's
`npm run dev` webServer).

## Method

- Added `axe-core` (devDependency) and `tests/e2e/toast.spec.ts`.
- Ran Playwright locally (chromium, installed). Playwright's `webServer.command` is
  `npm run dev`; since npm is absent, a temporary `npm`→`bun` shim was placed on PATH
  for the run (no repo/config change).
- The spec loads `/`, dynamically imports `useToast()` in the page, pushes all four
  variants, asserts semantics, dismisses one, then injects axe and runs WCAG 2 A/AA.

## Result — PASS

```
Running 1 test using 1 worker
[1/1] [chromium] › tests/e2e/toast.spec.ts › FE-010 toasts render, are announced,
      dismiss, and pass axe
  1 passed (4.3s)
```

Asserted:
- exactly one `[aria-live="polite"]` region in the Toaster;
- 4 toasts render, one per variant (`toast--info/success/warning/error`);
- error → `role="alert"` (1), others → `role="status"` (3);
- close button removes exactly one toast;
- **axe (wcag2a, wcag2aa, wcag21a, wcag21aa): 0 violations.**

The `[WebServer] http proxy error: /api/... ECONNREFUSED` lines are expected — no
backend is running locally; the app shell and toaster still render.

## Supporting checks (same session)
- `bun run lint` → exit 0
- `bunx tsc --noEmit` → exit 0
- `bun run test` → 7 files, 62 tests passed

## Note
This adds a devDependency (`axe-core`) and one e2e spec to the FE-010 artifact after
its initial verification; it strengthens the deferred T2 browser leg rather than
changing `useToast.ts`/`Toaster.vue`. Re-confirm at the M2 gate (FE-V2).
