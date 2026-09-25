import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

import { describe, expect, it } from 'vitest'

const SRC = join(process.cwd(), 'src')
const AUDITED_DIRS = ['components', 'views']
const HEX = /#[0-9a-fA-F]{3,6}\b/

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry)
    return statSync(full).isDirectory() ? walk(full) : [full]
  })
}

describe('raw-hex audit (FE-002 test T1)', () => {
  it.each(AUDITED_DIRS)('src/%s contains no raw hex colours', (dir) => {
    const files = walk(join(SRC, dir))
    expect(files.length).toBeGreaterThan(0)

    const offenders: string[] = []
    for (const file of files) {
      if (!/\.(vue|ts|css)$/.test(file)) continue
      const text = readFileSync(file, 'utf8')
      text.split('\n').forEach((line, index) => {
        if (HEX.test(line)) offenders.push(`${file}:${index + 1}: ${line.trim()}`)
      })
    }

    expect(offenders).toEqual([])
  })
})
