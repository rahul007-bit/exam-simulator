import { createRequire } from 'node:module'

import { expect, test } from '@playwright/test'

const require = createRequire(import.meta.url)
const axePath = require.resolve('axe-core/axe.min.js')

// FE-010 browser verification: trigger all four toast variants in a real browser,
// assert announcement semantics + manual dismiss, then run axe (WCAG 2 A/AA).
test('FE-010 toasts render, are announced, dismiss, and pass axe', async ({ page }) => {
  await page.goto('/')

  // The single live region is present even with no toasts.
  await expect(page.locator('.toaster [aria-live="polite"]')).toHaveCount(1)

  await page.evaluate(async () => {
    // Resolved by the Vite dev server at runtime; not a TS module specifier.
    const modulePath = '/src/composables/useToast.ts'
    const mod = (await import(/* @vite-ignore */ modulePath)) as {
      push: (message: string, variant: string) => void
    }
    mod.push('info sample', 'info')
    mod.push('success sample', 'success')
    mod.push('warning sample', 'warning')
    mod.push('error sample', 'error')
  })

  const toasts = page.locator('.toast')
  await expect(toasts).toHaveCount(4)
  await expect(page.locator('.toast--info')).toHaveCount(1)
  await expect(page.locator('.toast--success')).toHaveCount(1)
  await expect(page.locator('.toast--warning')).toHaveCount(1)
  await expect(page.locator('.toast--error')).toHaveCount(1)

  // Error variant is assertive; the rest are polite status.
  await expect(page.locator('.toast[role="alert"]')).toHaveCount(1)
  await expect(page.locator('.toast[role="status"]')).toHaveCount(3)

  // Manual dismiss removes exactly one toast.
  await page.locator('.toast--info .toast__close').click()
  await expect(page.locator('.toast')).toHaveCount(3)

  await page.addScriptTag({ path: axePath })
  const violations = await page.evaluate(async () => {
    const axe = (window as unknown as { axe: { run: (ctx: unknown, opts: unknown) => Promise<{ violations: { id: string }[] }> } }).axe
    const res = await axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
    })
    return res.violations.map((v) => v.id)
  })
  expect(violations).toEqual([])
})
