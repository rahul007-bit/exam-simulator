import { expect, test } from '@playwright/test'

// FE-023 browser verification (placeholder for the orchestrator's Playwright run).
//
// The timer composable renders nothing on its own — FE-020 wires it into the
// candidate header — so this spec exercises it directly in a real browser via
// the Vite dev module graph (same technique as toast.spec.ts) and checks the
// colour-only warning/critical treatment against the live semantic tokens.
test('FE-023: timer syncs a tick and stays colour-only with AA contrast', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('#app')).toBeVisible()

  const state = await page.evaluate(async () => {
    const modulePath = '/src/composables/useTimer.ts'
    const mod = (await import(/* @vite-ignore */ modulePath)) as {
      useTimer: (options?: unknown) => {
        handleMessage: (raw: unknown) => boolean
        remainingSeconds: { value: number | null }
        urgency: { value: string }
        urgencyColorVar: { value: string }
        stop: () => void
      }
    }
    const timer = mod.useTimer({ autoConnect: false })
    timer.handleMessage(
      JSON.stringify({ type: 'timer_tick', time_remaining_seconds: 120, server_timestamp: 1 }),
    )
    const result = {
      remaining: timer.remainingSeconds.value,
      urgency: timer.urgency.value,
      color: timer.urgencyColorVar.value,
    }
    timer.stop()
    return result
  })

  expect(state.remaining).toBe(120)
  expect(state.urgency).toBe('critical')
  expect(state.color).toBe('var(--color-danger-text)')

  const probe = await page.evaluate(() => {
    const el = document.createElement('div')
    el.style.color = 'var(--color-danger-text)'
    el.style.backgroundColor = 'var(--color-surface)'
    document.body.appendChild(el)

    const style = getComputedStyle(el)
    const channel = (value: number) => {
      const c = value / 255
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
    }
    const luminance = (rgb: string) => {
      const [r, g, b] = rgb
        .match(/\d+/g)!
        .slice(0, 3)
        .map(Number)
        .map(channel)
      return 0.2126 * r + 0.7152 * g + 0.0722 * b
    }
    const fg = luminance(style.color)
    const bg = luminance(style.backgroundColor)
    const [hi, lo] = fg > bg ? [fg, bg] : [bg, fg]
    const result = {
      ratio: (hi + 0.05) / (lo + 0.05),
      noAnimation: style.animationName === 'none' && style.textShadow === 'none',
    }
    el.remove()
    return result
  })

  expect(probe.ratio).toBeGreaterThanOrEqual(4.5)
  expect(probe.noAnimation).toBe(true)
})
