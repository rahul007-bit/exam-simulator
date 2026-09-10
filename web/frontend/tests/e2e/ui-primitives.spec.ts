import { createRequire } from 'node:module'

import { expect, test, type Page } from '@playwright/test'

const require = createRequire(import.meta.url)
const axePath = require.resolve('axe-core/axe.min.js')

const AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']

async function axeViolations(page: Page): Promise<string[]> {
  await page.addScriptTag({ path: axePath })
  return page.evaluate(async (tags) => {
    const axe = (
      window as unknown as {
        axe: { run: (ctx: unknown, opts: unknown) => Promise<{ violations: { id: string }[] }> }
      }
    ).axe
    const result = await axe.run(document, { runOnly: { type: 'tag', values: tags } })
    return result.violations.map((violation) => violation.id)
  }, AXE_TAGS)
}

/**
 * Move focus with the keyboard until `testid` (or a descendant of it) owns it.
 * Returns the focused element's computed outline so `:focus-visible` styling can
 * be asserted without relying on programmatic focus heuristics.
 */
async function keyboardFocus(page: Page, testid: string, maxTabs = 80) {
  await page.evaluate(() => (document.activeElement as HTMLElement | null)?.blur())
  for (let i = 0; i < maxTabs; i += 1) {
    await page.keyboard.press('Tab')
    const current = await page.evaluate(() => {
      const element = document.activeElement as HTMLElement | null
      if (!element) return null
      const owner = element.closest('[data-testid]') as HTMLElement | null
      return {
        id: element.getAttribute('data-testid') ?? owner?.getAttribute('data-testid') ?? null,
        outlineStyle: getComputedStyle(element).outlineStyle,
        outlineWidth: getComputedStyle(element).outlineWidth,
        outlineColor: getComputedStyle(element).outlineColor,
      }
    })
    if (current?.id === testid) return current
  }
  throw new Error(`could not keyboard-focus [data-testid="${testid}"]`)
}

test.describe('FE-012 primitives gallery', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dev/ui')
  })

  test('renders every primitive', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /ui primitives gallery/i })).toBeVisible()
    for (const id of [
      'btn-primary',
      'btn-disabled',
      'btn-loading',
      'input-name',
      'select-basic',
      'badge-success',
      'card-variant-elevated',
      'spinner-md',
      'segmented',
    ]) {
      await expect(page.getByTestId(id).first()).toBeVisible()
    }
  })

  test('T1: axe reports no violations on the gallery', async ({ page }) => {
    expect(await axeViolations(page)).toEqual([])
  })

  test('T2: every interactive primitive shows a token focus ring when keyboard focused', async ({
    page,
  }) => {
    for (const id of ['btn-primary', 'input-name', 'select-basic', 'segmented', 'chip-1']) {
      const focus = await keyboardFocus(page, id)
      expect(focus, id).not.toBeNull()
      expect(parseFloat(focus!.outlineWidth), id).toBeGreaterThan(0)
      expect(focus!.outlineStyle, id).not.toBe('none')
      // The ring colour resolves from the focus-ring token (indigo family).
      expect(focus!.outlineColor, id).not.toBe('rgb(0, 0, 0)')
    }
  })

  test('T2: disabled and loading states render and are non-interactive', async ({ page }) => {
    await expect(page.getByTestId('btn-disabled')).toBeDisabled()
    await expect(page.getByTestId('btn-loading')).toBeDisabled()
    await expect(page.getByTestId('btn-loading')).toHaveAttribute('aria-busy', 'true')
    await expect(page.getByTestId('btn-loading').locator('svg.animate-spin')).toHaveCount(1)
  })

  test('modal opens with dialog semantics, passes axe, closes on Escape', async ({ page }) => {
    await page.getByTestId('modal-open').click()
    // The Headless UI Dialog root is a layout-less wrapper; assert visibility on
    // the panel and roles on the root.
    const panel = page.getByTestId('modal-panel')
    const dialog = page.getByTestId('modal')
    await expect(panel).toBeVisible()
    await expect(dialog).toHaveAttribute('role', 'dialog')
    await expect(dialog).toHaveAttribute('aria-modal', 'true')

    expect(await axeViolations(page)).toEqual([])

    await page.keyboard.press('Escape')
    await expect(panel).toBeHidden()
  })
})
