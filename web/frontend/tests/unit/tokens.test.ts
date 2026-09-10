import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { describe, expect, it } from 'vitest'

const tokensCss = readFileSync(join(process.cwd(), 'src/assets/styles/tokens.css'), 'utf8')

/** Extract `--custom: value;` declarations from the block starting at `selector`. */
function block(css: string, selector: string): Record<string, string> {
  const start = css.indexOf(selector)
  if (start < 0) throw new Error(`selector not found: ${selector}`)
  const open = css.indexOf('{', start)
  let depth = 0
  let end = open
  for (let i = open; i < css.length; i += 1) {
    if (css[i] === '{') depth += 1
    else if (css[i] === '}') {
      depth -= 1
      if (depth === 0) {
        end = i
        break
      }
    }
  }
  const body = css.slice(open + 1, end)
  const out: Record<string, string> = {}
  const re = /(--[a-z0-9-]+)\s*:\s*([^;]+);/gi
  let match: RegExpExecArray | null
  while ((match = re.exec(body))) out[match[1]] = match[2].trim()
  return out
}

const dark = block(tokensCss, ':root {')
const light = block(tokensCss, ":root[data-theme='light']")
const mediaFallback = block(tokensCss, ':root:not([data-theme])')

function channel(value: number): number {
  const c = value / 255
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
}

function luminance(hex: string): number {
  const clean = hex.replace('#', '')
  const full =
    clean.length === 3
      ? clean
          .split('')
          .map((c) => c + c)
          .join('')
      : clean
  const r = parseInt(full.slice(0, 2), 16)
  const g = parseInt(full.slice(2, 4), 16)
  const b = parseInt(full.slice(4, 6), 16)
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
}

function contrast(foreground: string, background: string): number {
  const a = luminance(foreground)
  const b = luminance(background)
  const [hi, lo] = a > b ? [a, b] : [b, a]
  return (hi + 0.05) / (lo + 0.05)
}

describe('design tokens — palette is fully variable-ised (FE-002 acceptance #1)', () => {
  it('exposes every dark palette value from PLAN.md §2', () => {
    expect(dark['--color-bg-app']).toBe('#0b0f16')
    expect(dark['--color-surface']).toBe('#121826')
    expect(dark['--color-elevated']).toBe('#1a2233')
    expect(dark['--color-hover']).toBe('#222c40')
    expect(dark['--color-border']).toBe('#263042')
    expect(dark['--color-border-strong']).toBe('#33405a')
    expect(dark['--color-text']).toBe('#e6e9ef')
    expect(dark['--color-text-muted']).toBe('#9aa4b2')
    expect(dark['--color-text-dim']).toBe('#5b6675')
    expect(dark['--color-accent']).toBe('#6366f1')
  })

  it('exposes every light palette value from PLAN.md §2', () => {
    expect(light['--color-bg-app']).toBe('#f6f7f9')
    expect(light['--color-surface']).toBe('#ffffff')
    expect(light['--color-elevated']).toBe('#ffffff')
    expect(light['--color-hover']).toBe('#eef1f5')
    expect(light['--color-border']).toBe('#e2e6ec')
    expect(light['--color-border-strong']).toBe('#cbd2db')
    expect(light['--color-text']).toBe('#0f172a')
    expect(light['--color-text-muted']).toBe('#5b6675')
    expect(light['--color-text-dim']).toBe('#8a94a3')
    expect(light['--color-accent']).toBe('#4f46e5')
  })

  it('exposes the four semantic colours in both themes', () => {
    for (const theme of [dark, light]) {
      expect(theme['--color-success']).toBe('#22c55e')
      expect(theme['--color-warning']).toBe('#f59e0b')
      expect(theme['--color-danger']).toBe('#ef4444')
      expect(theme['--color-info']).toBe('#60a5fa')
    }
  })

  it('exposes radii, spacing, type and elevation tokens', () => {
    expect(dark['--radius-sm']).toBe('6px')
    expect(dark['--radius-md']).toBe('8px')
    expect(dark['--radius-lg']).toBe('12px')
    expect(dark['--space-1']).toBe('4px')
    expect(dark['--space-4']).toBe('16px')
    expect(dark['--font-sans']).toContain('Inter')
    expect(dark['--font-mono']).toContain('JetBrains Mono')
    expect(dark['--shadow-md']).toBeTruthy()
  })

  it('provides a no-JS prefers-color-scheme fallback identical to the light theme', () => {
    expect(mediaFallback['--color-bg-app']).toBe(light['--color-bg-app'])
    expect(mediaFallback['--color-text']).toBe(light['--color-text'])
    expect(mediaFallback['--color-accent']).toBe(light['--color-accent'])
  })
})

describe('design tokens — AA contrast (FE-002 acceptance #2)', () => {
  const pairs: Array<[string, string, string]> = [
    ['dark text on bg-app', '--color-text', '--color-bg-app'],
    ['dark text on surface', '--color-text', '--color-surface'],
    ['dark muted on bg-app', '--color-text-muted', '--color-bg-app'],
    ['dark muted on surface', '--color-text-muted', '--color-surface'],
    ['dark accent-text on surface', '--color-accent-text', '--color-surface'],
    ['dark accent-text on bg-app', '--color-accent-text', '--color-bg-app'],
    ['dark accent-contrast on accent-solid', '--color-accent-contrast', '--color-accent-solid'],
    ['dark success-text on surface', '--color-success-text', '--color-surface'],
    ['dark warning-text on surface', '--color-warning-text', '--color-surface'],
    ['dark danger-text on surface', '--color-danger-text', '--color-surface'],
    ['dark info-text on surface', '--color-info-text', '--color-surface'],
  ]

  const lightPairs: Array<[string, string, string]> = [
    ['light text on bg-app', '--color-text', '--color-bg-app'],
    ['light text on surface', '--color-text', '--color-surface'],
    ['light muted on bg-app', '--color-text-muted', '--color-bg-app'],
    ['light muted on surface', '--color-text-muted', '--color-surface'],
    ['light accent-text on surface', '--color-accent-text', '--color-surface'],
    ['light accent-text on bg-app', '--color-accent-text', '--color-bg-app'],
    ['light accent-contrast on accent-solid', '--color-accent-contrast', '--color-accent-solid'],
    ['light success-text on surface', '--color-success-text', '--color-surface'],
    ['light warning-text on surface', '--color-warning-text', '--color-surface'],
    ['light danger-text on surface', '--color-danger-text', '--color-surface'],
    ['light info-text on surface', '--color-info-text', '--color-surface'],
  ]

  it.each(pairs)('%s meets WCAG AA (>= 4.5)', (_name, fg, bg) => {
    expect(contrast(dark[fg], dark[bg])).toBeGreaterThanOrEqual(4.5)
  })

  it.each(lightPairs)('%s meets WCAG AA (>= 4.5)', (_name, fg, bg) => {
    expect(contrast(light[fg], light[bg])).toBeGreaterThanOrEqual(4.5)
  })
})
