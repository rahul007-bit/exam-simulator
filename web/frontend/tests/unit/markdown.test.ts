import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { taskBadges } from '@/components/candidate/task'
import { renderMarkdown, sanitizeHtml } from '@/composables/useMarkdown'

async function settle(): Promise<void> {
  await flushPromises()
  await Promise.resolve()
  await flushPromises()
}

async function mountMarkdown(source: string) {
  const wrapper = mount(MarkdownRenderer, { attachTo: document.body, props: { source } })
  await settle()
  return wrapper
}

describe('useMarkdown — sanitisation (FE-022 T1)', () => {
  it('removes the onerror handler from an <img> payload', () => {
    const html = renderMarkdown('<img src=x onerror=alert(1)>')
    expect(html).not.toMatch(/onerror/i)
    expect(html).not.toMatch(/alert\(1\)/)
  })

  it('strips <script> tags and their contents', () => {
    const html = renderMarkdown('<script>window.__pwned = true</script>')
    expect(html).not.toMatch(/<script/i)
    expect(html).not.toMatch(/__pwned/)
  })

  it('strips inline event-handler attributes generally', () => {
    const html = renderMarkdown('<a href="#" onmouseover="alert(1)">x</a>')
    expect(html).not.toMatch(/onmouseover/i)
  })

  it('blocks javascript: URLs in markdown links', () => {
    const html = renderMarkdown('[click](javascript:alert(1))')
    expect(html).not.toMatch(/javascript:/i)
  })

  it('strips <iframe>/<style> and inline style attributes', () => {
    const html = renderMarkdown('<iframe src="https://evil.test"></iframe><b style="color:red">x</b>')
    expect(html).not.toMatch(/<iframe/i)
    expect(html).not.toMatch(/style=/i)
  })

  it('exposes sanitizeHtml as the single sanitisation entry point', () => {
    expect(sanitizeHtml('<img src=x onerror=alert(1)>')).not.toMatch(/onerror/i)
  })

  it('still renders benign markdown', () => {
    const html = renderMarkdown('**bold** text\n\n- one\n- two')
    expect(html).toContain('<strong>bold</strong>')
    expect(html).toMatch(/<ul>/)
    expect(html.match(/<li>/g)).toHaveLength(2)
  })
})

describe('useMarkdown — highlighting (FE-022)', () => {
  it('highlights fenced code with the requested language', () => {
    const html = renderMarkdown('```js\nconst total = 41 + 1\n```')
    expect(html).toMatch(/class="hljs language-js"/)
    // highlight.js wrapped at least one token in a span.
    expect(html).toMatch(/class="hljs-[a-z]+"/)
    expect(html).toContain('total')
  })

  it('falls back to plaintext for an unknown language', () => {
    const html = renderMarkdown('```notalanguage\nhello\n```')
    expect(html).toMatch(/class="hljs language-notalanguage"/)
    expect(html).toContain('hello')
  })

  it('renders inline code as a <code> element', () => {
    expect(renderMarkdown('run `kubectl get nodes`')).toContain('<code>kubectl get nodes</code>')
  })
})

describe('MarkdownRenderer — sanitized DOM (FE-022 T1)', () => {
  it('never injects event handlers into the live DOM', async () => {
    const wrapper = await mountMarkdown('<img src=x onerror=alert(1)><script>alert(2)</script>')
    expect(wrapper.html()).not.toMatch(/onerror/i)
    expect(wrapper.html()).not.toMatch(/<script/i)
    wrapper.unmount()
  })

  it('shows the empty text when there is no source', () => {
    const wrapper = mount(MarkdownRenderer, { props: { source: '', emptyText: 'Nothing here' } })
    expect(wrapper.text()).toContain('Nothing here')
    expect(wrapper.find('.markdown-body').exists()).toBe(false)
  })
})

describe('MarkdownRenderer — code copy (FE-022 T2)', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    writeText.mockClear()
    Object.defineProperty(window.navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
      writable: true,
    })
  })

  it('adds a copy button to each fenced block and copies its text', async () => {
    const wrapper = await mountMarkdown('```bash\nkubectl get pods -A\n```')

    const button = wrapper.get('[data-code-copy]')
    expect(button.text()).toBe('Copy')

    await button.trigger('click')

    expect(writeText).toHaveBeenCalledTimes(1)
    expect(writeText.mock.calls[0][0]).toContain('kubectl get pods -A')
    expect(button.text()).toBe('Copied')
    expect(button.classes()).toContain('is-copied')

    wrapper.unmount()
  })

  it('copies inline code on click and shows success feedback', async () => {
    const wrapper = await mountMarkdown('Run `kubectl get pods` now.')

    const code = wrapper.get('code.inline-code-copy')
    expect(code.attributes('role')).toBe('button')
    expect(code.attributes('tabindex')).toBe('0')

    await code.trigger('click')

    expect(writeText).toHaveBeenCalledWith('kubectl get pods')
    expect(code.classes()).toContain('is-copied')

    wrapper.unmount()
  })

  it('supports keyboard activation of inline code', async () => {
    const wrapper = await mountMarkdown('Use `kubectl apply -f x.yaml`.')

    const code = wrapper.get('code.inline-code-copy')
    await code.trigger('keydown', { key: 'Enter' })

    expect(writeText).toHaveBeenCalledWith('kubectl apply -f x.yaml')

    wrapper.unmount()
  })

  it('emits a copy event with the copied text', async () => {
    const wrapper = await mountMarkdown('`only-code`')
    await wrapper.get('code').trigger('click')
    expect(wrapper.emitted('copy')?.[0]).toEqual(['only-code'])
    wrapper.unmount()
  })
})

describe('taskBadges — neutral chips + semantic status (FE-022)', () => {
  const task = {
    task_num: 3,
    title: 'Scale a deployment',
    description: 'body',
    points: 5,
    namespace: 'default',
    target_context: 'k3d-cka',
  }

  it('returns only neutral badges for an unflagged task', () => {
    const badges = taskBadges(task)
    expect(badges.map((badge) => badge.key)).toEqual(['number', 'points', 'context', 'namespace'])
    expect(badges.every((badge) => badge.variant === 'neutral')).toBe(true)
    expect(badges[0].label).toBe('Task 3')
    expect(badges[1].label).toBe('5 pts')
  })

  it('adds a danger FLAGGED badge only when flagged', () => {
    const badges = taskBadges({ ...task, is_flagged: true })
    const flagged = badges.find((badge) => badge.key === 'flagged')
    expect(flagged?.variant).toBe('danger')
    expect(flagged?.label).toBe('FLAGGED')
  })

  it('falls back to the legacy context/namespace defaults', () => {
    const badges = taskBadges({ ...task, target_context: null, namespace: null })
    expect(badges.find((badge) => badge.key === 'context')?.label).toBe('context: k3d-cka')
    expect(badges.find((badge) => badge.key === 'namespace')?.label).toBe('ns: default')
  })
})

describe('FE-022 constraints audit (hex / glow / emoji)', () => {
  const HEX = /#[0-9a-fA-F]{3,6}\b/
  const GLOW = /text-shadow|drop-shadow|blur\(/
  const EMOJI = /\p{Extended_Pictographic}/u

  const files = [
    join(process.cwd(), 'src/components/MarkdownRenderer.vue'),
    join(process.cwd(), 'src/components/candidate/TaskPane.vue'),
    join(process.cwd(), 'src/components/candidate/task.ts'),
    join(process.cwd(), 'src/composables/useMarkdown.ts'),
  ]

  it('uses tokens only (no raw hex) and no glow/blur', () => {
    for (const file of files) {
      const text = readFileSync(file, 'utf8')
      expect(text, file).not.toMatch(HEX)
      expect(text, file).not.toMatch(GLOW)
    }
  })

  it('contains no emoji in UI copy or code', () => {
    for (const file of files) {
      expect(readFileSync(file, 'utf8'), file).not.toMatch(EMOJI)
    }
  })
})
