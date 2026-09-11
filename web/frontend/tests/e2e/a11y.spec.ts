import { createRequire } from 'node:module'

import { expect, test, type Page } from '@playwright/test'

import { mockAdminBackend, mockCandidateBackend } from './helpers'

const require = createRequire(import.meta.url)
const axePath = require.resolve('axe-core/axe.min.js')

const AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']

interface AxeNode {
  target: string[]
  html: string
  failureSummary?: string
}

interface AxeViolation {
  id: string
  impact: string | null
  help: string
  nodes: AxeNode[]
}

async function injectAxe(page: Page): Promise<void> {
  const present = await page.evaluate(() => Boolean((window as unknown as { axe?: unknown }).axe))
  if (!present) await page.addScriptTag({ path: axePath })
}

/** Run axe (WCAG 2 A/AA) and return only the critical-impact violations. */
async function criticalViolations(page: Page): Promise<AxeViolation[]> {
  await injectAxe(page)
  const violations = await page.evaluate(async (tags) => {
    const axe = (
      window as unknown as {
        axe: {
          run: (context: Document, options: unknown) => Promise<{ violations: AxeViolation[] }>
        }
      }
    ).axe
    const result = await axe.run(document, { runOnly: { type: 'tag', values: tags } })
    return result.violations.map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      help: violation.help,
      nodes: violation.nodes.map((node) => ({
        target: node.target,
        html: node.html,
        failureSummary: node.failureSummary,
      })),
    }))
  }, AXE_TAGS)
  return violations.filter((violation) => violation.impact === 'critical')
}

function expectNoCritical(violations: AxeViolation[]): void {
  const detail = violations
    .map(
      (violation) =>
        `[${violation.impact}] ${violation.id} — ${violation.help}\n` +
        violation.nodes
          .map((node) => `  ${node.target.join(' ')}\n    ${node.failureSummary ?? node.html}`)
          .join('\n'),
    )
    .join('\n')
  if (detail) console.error(`axe critical violations:\n${detail}`)
  expect(violations, detail).toEqual([])
}

/**
 * FE-042 T2 — axe accessibility scan.
 *
 * Injects the installed `axe-core` bundle and asserts **zero critical**
 * violations on the candidate start screen, an open modal/dialog state and the
 * admin surface. All network is mocked (see `helpers.ts`). T2 is host-only per
 * PROTOCOL §6; run it with `npx playwright test tests/e2e/a11y.spec.ts`.
 */
test.describe('FE-042 axe accessibility', () => {
  test('T2: candidate route has no critical violations', async ({ page }) => {
    await mockCandidateBackend(page)
    await page.goto('/')
    await expect(page.getByTestId('start-exam')).toBeVisible()
    expectNoCritical(await criticalViolations(page))
  })

  test('T2: admin route + session action dialog have no critical violations', async ({ page }) => {
    await mockAdminBackend(page)
    await page.goto('/admin')
    await expect(page.getByTestId('sessions-refresh')).toBeVisible()
    expectNoCritical(await criticalViolations(page))

    await page.getByTestId('datatable-row').first().click()
    await expect(page.getByTestId('session-action-terminate')).toBeVisible()
    expectNoCritical(await criticalViolations(page))
  })
})
