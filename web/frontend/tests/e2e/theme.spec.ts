import { expect, test } from '@playwright/test'

import { mockCandidateBackend } from './helpers'

/** WCAG relative luminance + contrast ratio of body text vs page background. */
async function bodyContrast(page: import('@playwright/test').Page): Promise<number> {
  return page.evaluate(() => {
    function lum(rgb: string): number {
      const [r, g, b] = rgb
        .match(/\d+/g)!
        .slice(0, 3)
        .map(Number)
        .map((v) => {
          const c = v / 255
          return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
        })
      return 0.2126 * r + 0.7152 * g + 0.0722 * b
    }
    const style = getComputedStyle(document.body)
    const fg = lum(style.color)
    const bg = lum(style.backgroundColor)
    const [hi, lo] = fg > bg ? [fg, bg] : [bg, fg]
    return (hi + 0.05) / (lo + 0.05)
  })
}

test('FE-002 T2: theme toggle flips, persists across reload and stays AA', async ({ page }) => {
  // `/` is auth-gated now; mock a signed-in candidate so it renders the shell.
  await mockCandidateBackend(page)
  await page.goto('/')

  const toggle = page.getByRole('button', { name: /switch to (light|dark) theme/i })
  await expect(toggle).toBeVisible()

  const initial = await page.evaluate(() => document.documentElement.dataset.theme)
  expect(['dark', 'light']).toContain(initial)

  const initialContrast = await bodyContrast(page)
  expect(initialContrast).toBeGreaterThanOrEqual(4.5)

  await toggle.click()
  const flipped = await page.evaluate(() => document.documentElement.dataset.theme)
  expect(flipped).not.toBe(initial)
  // Colour transitions may still be settling immediately after the click.
  await expect.poll(() => bodyContrast(page)).toBeGreaterThanOrEqual(4.5)

  await page.reload()
  await expect.poll(() => page.evaluate(() => document.documentElement.dataset.theme)).toBe(flipped)
  await expect.poll(() => bodyContrast(page)).toBeGreaterThanOrEqual(4.5)
})
