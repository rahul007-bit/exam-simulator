import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * FE-041 — offline/self-hosted asset audit.
 *
 * Guards that the app makes no runtime calls to external font/CDN hosts and
 * that Inter + JetBrains Mono are bundled as same-origin woff2 assets under
 * `public/fonts/`. The manual offline-load leg lives in TESTPLAN.md (DEFERRED
 * in this environment — no browser build is run here).
 */

const ROOT = process.cwd()
const SRC = join(ROOT, 'src')
const INDEX_HTML = join(ROOT, 'index.html')
const FONTS_CSS = join(SRC, 'assets/styles/fonts.css')
const BASE_CSS = join(SRC, 'assets/styles/base.css')
const TOKENS_CSS = join(SRC, 'assets/styles/tokens.css')
const PUBLIC_FONTS = join(ROOT, 'public/fonts')

const EXTERNAL_HOSTS = ['fonts.googleapis', 'fonts.gstatic', 'cdn.jsdelivr', 'unpkg', 'cdnjs']
const SCAN_EXT = /\.(vue|ts|js|mjs|css|html)$/
const EXPECTED_FONT_FAMILIES = ['Inter', 'JetBrains Mono'] as const

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry)
    return statSync(full).isDirectory() ? walk(full) : [full]
  })
}

/** Strip comments so prose that *mentions* a CDN cannot be treated as a call. */
function stripComments(text: string): string {
  return text
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/(^|[^:])\/\/.*$/gm, '$1')
}

interface FontFace {
  family: string
  style: string
  display: string
  weight: string
  src: string
}

function parseFontFaces(css: string): FontFace[] {
  const faces: FontFace[] = []
  const re = /@font-face\s*\{([^}]*)\}/g
  let match: RegExpExecArray | null
  while ((match = re.exec(css))) {
    const body = match[1]
    const field = (name: string): string => {
      const m = new RegExp(`${name}\\s*:\\s*([^;]+);`).exec(body)
      return m ? m[1].trim() : ''
    }
    faces.push({
      family: field('font-family').replace(/^['"]|['"]$/g, ''),
      style: field('font-style'),
      display: field('font-display'),
      weight: field('font-weight'),
      src: field('src'),
    })
  }
  return faces
}

function urlsOf(src: string): string[] {
  return [...src.matchAll(/url\((['"]?)([^'")]+)\1\)/g)].map((m) => m[2])
}

const scannedFiles = [...walk(SRC).filter((file) => SCAN_EXT.test(file)), INDEX_HTML]

const fontsCss = readFileSync(FONTS_CSS, 'utf8')
const faces = parseFontFaces(fontsCss)

describe('FE-041 offline asset audit (T1)', () => {
  it('audits a stable, non-empty set of sources', () => {
    expect(scannedFiles.length).toBeGreaterThan(0)
    expect(scannedFiles).toContain(FONTS_CSS)
    expect(scannedFiles).toContain(INDEX_HTML)
    expect(faces.length).toBeGreaterThanOrEqual(EXPECTED_FONT_FAMILIES.length)
  })

  it('references no external font/CDN hosts in src/** or index.html', () => {
    const offenders: string[] = []
    for (const file of scannedFiles) {
      const text = stripComments(readFileSync(file, 'utf8'))
      text.split('\n').forEach((line, index) => {
        for (const host of EXTERNAL_HOSTS) {
          if (line.includes(host)) {
            offenders.push(`${relative(ROOT, file)}:${index + 1}: ${line.trim()}`)
          }
        }
      })
    }
    expect(offenders).toEqual([])
  })

  it('index.html loads no external stylesheet or font preconnect', () => {
    const html = readFileSync(INDEX_HTML, 'utf8')
    const links = [...html.matchAll(/<link\b[^>]*>/gi)].map((m) => m[0])
    expect(links.filter((link) => /rel\s*=\s*['"]?(preconnect|dns-prefetch)['"]?/i.test(link))).toEqual(
      [],
    )
    expect(links.filter((link) => /https?:\/\//i.test(link))).toEqual([])
  })
})

describe('FE-041 self-hosted @font-face setup', () => {
  it('declares a variable face for Inter and JetBrains Mono', () => {
    for (const family of EXPECTED_FONT_FAMILIES) {
      const face = faces.find((f) => f.family === family)
      expect(face, family).toBeDefined()
      expect(face?.style).toBe('normal')
      expect(face?.display).toBe('swap')
      expect(face?.weight).toBe('100 900')
    }
  })

  it('keeps tokens.css resolving to the bundled family names', () => {
    const tokens = readFileSync(TOKENS_CSS, 'utf8')
    expect(tokens).toContain("'Inter'")
    expect(tokens).toContain("'JetBrains Mono'")
  })

  it('sources every face from a same-origin /fonts/ woff2 that exists', () => {
    for (const face of faces) {
      const urls = urlsOf(face.src)
      expect(urls.length, face.family).toBeGreaterThan(0)
      expect(face.src).toContain("format('woff2')")
      for (const url of urls) {
        expect(url.startsWith('/fonts/'), `${face.family} -> ${url}`).toBe(true)
        expect(url).not.toMatch(/^https?:/i)
        const file = join(ROOT, 'public', url.replace(/^\//, ''))
        expect(existsSync(file), file).toBe(true)
      }
    }
  })

  it('imports fonts.css from base.css after the tailwind import', () => {
    const base = readFileSync(BASE_CSS, 'utf8')
    const tailwind = base.indexOf("@import 'tailwindcss'")
    const fonts = base.indexOf("@import './fonts.css'")
    expect(tailwind).toBeGreaterThanOrEqual(0)
    expect(fonts).toBeGreaterThan(tailwind)
  })
})

describe('FE-041 bundled woff2 assets', () => {
  const expected = ['inter-latin-wght-normal.woff2', 'jetbrains-mono-latin-wght-normal.woff2']

  it('ships valid woff2 latin subsets', () => {
    const files = readdirSync(PUBLIC_FONTS).filter((name) => name.endsWith('.woff2'))
    for (const name of expected) {
      expect(files, name).toContain(name)
      const buf = readFileSync(join(PUBLIC_FONTS, name))
      expect(buf.subarray(0, 4).toString('latin1')).toBe('wOF2')
      expect(buf.length).toBeGreaterThan(1024)
    }
  })

  it('references every shipped woff2 from a @font-face rule', () => {
    const files = readdirSync(PUBLIC_FONTS).filter((name) => name.endsWith('.woff2'))
    const referenced = new Set(faces.flatMap((face) => urlsOf(face.src)).map((url) => url.split('/').pop()))
    for (const name of files) {
      expect(referenced, name).toContain(name)
    }
  })
})
