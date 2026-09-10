import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import Icon from '@/components/Icon.vue'
import { ICONS, ICON_NAMES } from '@/components/ui/icons'

/**
 * FE-014 — de-glow / de-emoji audit and icon-set coverage.
 *
 * Permanent regression guard for the M2 design language (D-003):
 *  - no glow (`text-shadow`, `drop-shadow`, `blur(`, raw `box-shadow`/`filter`);
 *  - no gradients;
 *  - no decorative keyframes / custom `animation:` declarations;
 *  - no emoji in UI copy;
 *  - the `Icon` component renders and covers every glyph the UI uses.
 *
 * Scope is deliberately limited to the files FE-014 owns plus `components/ui/**`
 * so parallel agents' brand-new files do not race this audit.
 */

const SRC = join(process.cwd(), 'src')

const EXPLICIT_FILES = [
  'components/Icon.vue',
  'components/Toaster.vue',
  'components/ConfirmDialog.vue',
  'views/DevUiView.vue',
  'assets/styles/base.css',
]

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry)
    return statSync(full).isDirectory() ? walk(full) : [full]
  })
}

const FILES = [
  ...EXPLICIT_FILES.map((relative) => join(SRC, relative)),
  ...walk(join(SRC, 'components/ui')),
].filter((file) => /\.(vue|ts|css)$/.test(file))

/** Remove comments so prose that *mentions* "glow"/"gradient" cannot match. */
function stripComments(text: string): string {
  return text
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/(^|[^:])\/\/.*$/gm, '$1')
}

function codeOf(file: string): string {
  return stripComments(readFileSync(file, 'utf8'))
}

describe('FE-014 de-glow audit (scoped sources)', () => {
  it('audits a stable, non-empty set of owned files', () => {
    expect(FILES.length).toBeGreaterThan(0)
    for (const relative of EXPLICIT_FILES) {
      expect(FILES).toContain(join(SRC, relative))
    }
  })

  it('contains no glow primitives (text-shadow / drop-shadow / blur / box-shadow / filter)', () => {
    const offenders: string[] = []
    for (const file of FILES) {
      codeOf(file)
        .split('\n')
        .forEach((line, index) => {
          if (/text-shadow|drop-shadow|\bblur\s*\(|box-shadow\s*:|\bfilter\s*:/i.test(line)) {
            offenders.push(`${file}:${index + 1}: ${line.trim()}`)
          }
        })
    }
    expect(offenders).toEqual([])
  })

  it('only uses the elevation-token shadows for arbitrary shadow utilities', () => {
    const offenders: string[] = []
    for (const file of FILES) {
      const text = codeOf(file)
      const re = /shadow-\[([^\]]*)\]/g
      let match: RegExpExecArray | null
      while ((match = re.exec(text))) {
        const value = match[1].replace(/\s+/g, '')
        if (!/^var\(--shadow-(xs|sm|md|lg)\)$/.test(value)) {
          offenders.push(`${file}: ${match[0]}`)
        }
      }
    }
    expect(offenders).toEqual([])
  })

  it('contains no gradients', () => {
    const offenders: string[] = []
    for (const file of FILES) {
      codeOf(file)
        .split('\n')
        .forEach((line, index) => {
          if (/gradient/i.test(line)) offenders.push(`${file}:${index + 1}: ${line.trim()}`)
        })
    }
    expect(offenders).toEqual([])
  })

  it('contains no decorative keyframes or custom animation declarations', () => {
    const offenders: string[] = []
    for (const file of FILES) {
      codeOf(file)
        .split('\n')
        .forEach((line, index) => {
          if (/@keyframes|animation\s*:/i.test(line)) {
            offenders.push(`${file}:${index + 1}: ${line.trim()}`)
          }
        })
    }
    expect(offenders).toEqual([])
  })

  it('contains no emoji in UI copy', () => {
    const offenders: string[] = []
    for (const file of FILES) {
      codeOf(file)
        .split('\n')
        .forEach((line, index) => {
          if (/\p{Extended_Pictographic}/u.test(line)) {
            offenders.push(`${file}:${index + 1}: ${line.trim()}`)
          }
        })
    }
    expect(offenders).toEqual([])
  })
})

describe('FE-014 Icon component', () => {
  it('exposes a non-empty catalogue with shapes for every name', () => {
    expect(ICON_NAMES.length).toBeGreaterThan(0)
    for (const name of ICON_NAMES) {
      expect(ICONS[name].length, name).toBeGreaterThan(0)
    }
  })

  it('covers every glyph the UI currently uses', () => {
    const currentlyUsed = [
      // toast variants + dismiss
      'info',
      'success',
      'warning',
      'error',
      'close',
      // select / chip / table affordances
      'check',
      'chevron-up',
      'chevron-down',
      'chevrons-up-down',
      // spinner + theme toggle
      'spinner',
      'sun',
      'moon',
    ] as const
    for (const name of currentlyUsed) {
      expect(ICON_NAMES, name).toContain(name)
    }
  })

  it('renders a stroke-based, decorative SVG by default', () => {
    const wrapper = mount(Icon, { props: { name: 'close' } })
    const svg = wrapper.get('svg')
    expect(svg.attributes('aria-hidden')).toBe('true')
    expect(svg.attributes('viewBox')).toBe('0 0 24 24')
    expect(svg.attributes('fill')).toBe('none')
    expect(svg.attributes('stroke')).toBe('currentColor')
    expect(svg.attributes('width')).toBe('16px')
    expect(svg.find('path').exists()).toBe(true)
  })

  it('becomes a labelled image when an accessible name is supplied', () => {
    const wrapper = mount(Icon, { props: { name: 'success', label: 'Saved', size: 20 } })
    const svg = wrapper.get('svg')
    expect(svg.attributes('role')).toBe('img')
    expect(svg.attributes('aria-label')).toBe('Saved')
    expect(svg.attributes('aria-hidden')).toBeUndefined()
    expect(svg.attributes('width')).toBe('20px')
  })

  it('renders every catalogue name without error', () => {
    for (const name of ICON_NAMES) {
      const wrapper = mount(Icon, { props: { name } })
      expect(wrapper.find('svg').exists(), name).toBe(true)
    }
  })
})
