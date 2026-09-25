import { expect, test } from '@playwright/test'

interface ConfirmModule {
  confirm: (options?: Record<string, unknown>) => Promise<boolean>
  prompt: (options?: Record<string, unknown>) => Promise<string | null>
}

declare global {
  interface Window {
    __useConfirm: ConfirmModule
  }
}

// FE-011 browser verification (T2): the dialog must be fully keyboard-operable —
// Escape cancels, Tab/Shift+Tab stay trapped, `aria-modal="true"` is present,
// the confirm button receives initial focus, and focus returns to the invoker.
test.describe('FE-011 confirm/prompt dialog (keyboard only)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate(async () => {
      const modulePath = '/src/composables/useConfirm.ts'
      window.__useConfirm = (await import(/* @vite-ignore */ modulePath)) as unknown as Window['__useConfirm']
    })
  })

  test('Escape cancels, focus is trapped, aria-modal is set, confirm is initially focused', async ({
    page,
  }) => {
    await page.evaluate(() => {
      const invoker = document.createElement('button')
      invoker.id = 'invoker'
      invoker.textContent = 'open dialog'
      document.body.appendChild(invoker)
      invoker.focus()
      void window.__useConfirm.confirm({ title: 'Confirm action', message: 'Proceed?' })
    })

    const dialog = page.getByTestId('dialog-root')
    const panel = page.getByTestId('dialog-panel')
    await expect(panel).toBeVisible()
    await expect(dialog).toHaveAttribute('role', 'dialog')
    await expect(dialog).toHaveAttribute('aria-modal', 'true')

    const confirmButton = page.getByTestId('confirm')
    const cancelButton = page.getByTestId('cancel')
    await expect(confirmButton).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(cancelButton).toBeFocused()
    await page.keyboard.press('Tab')
    await expect(confirmButton).toBeFocused()
    await page.keyboard.press('Shift+Tab')
    await expect(cancelButton).toBeFocused()

    await page.keyboard.press('Escape')
    await expect(panel).toBeHidden()
    await expect(page.locator('#invoker')).toBeFocused()
  })

  test('prompt focusses the input and Enter resolves the value', async ({ page }) => {
    const pending = page.evaluate(() =>
      window.__useConfirm.prompt({ title: 'Session name', placeholder: 'name' }),
    )

    const input = page.getByTestId('prompt-input')
    await expect(input).toBeFocused()

    await input.fill('lab-7')
    await page.keyboard.press('Enter')
    await expect(page.getByTestId('dialog-panel')).toBeHidden()

    expect(await pending).toBe('lab-7')
  })
})
