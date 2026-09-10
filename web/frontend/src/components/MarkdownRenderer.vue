<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'

import { renderMarkdown } from '@/composables/useMarkdown'

/**
 * MarkdownRenderer (FE-022) — renders sanitized task markdown and decorates
 * code for click-to-copy.
 *
 * Sanitisation happens in `useMarkdown` (DOMPurify); this component only binds
 * the already-sanitized string with `v-html`. Code decoration is added to the
 * rendered DOM *after* sanitisation, so no user-controlled markup is ever
 * injected by this component.
 *
 * Feedback is immediate and token-coloured: inline code flashes a success
 * border/colour, fenced blocks swap the button label "Copy" -> "Copied" for 2s.
 */

const props = withDefaults(
  defineProps<{
    source?: string
    emptyText?: string
  }>(),
  { source: '', emptyText: 'No task description provided.' },
)

const emit = defineEmits<{ copy: [text: string] }>()

const COPIED_CLASS = 'is-copied'
const COPY_LABEL = 'Copy'
const COPIED_LABEL = 'Copied'
const INLINE_FEEDBACK_MS = 1200
const BLOCK_FEEDBACK_MS = 2000

const root = ref<HTMLElement | null>(null)
const html = computed(() => renderMarkdown(props.source))

/** Defer decoration until after `v-html` has patched the DOM. */
function scheduleEnhance(): void {
  void nextTick(enhance)
}

function enhance(): void {
  const el = root.value
  if (!el) return

  el.querySelectorAll<HTMLPreElement>('pre').forEach((pre) => {
    if (pre.dataset.enhanced === 'true') return
    pre.dataset.enhanced = 'true'
    if (!pre.querySelector('code')) return

    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'code-copy-btn'
    button.dataset.codeCopy = ''
    button.setAttribute('aria-label', 'Copy code block')
    button.textContent = COPY_LABEL
    pre.prepend(button)
  })

  el.querySelectorAll<HTMLElement>('code').forEach((code) => {
    if (code.closest('pre') || code.dataset.enhanced === 'true') return
    code.dataset.enhanced = 'true'
    code.classList.add('inline-code-copy')
    code.setAttribute('role', 'button')
    code.setAttribute('tabindex', '0')
    code.setAttribute('title', 'Click to copy')
    code.setAttribute('aria-label', `Copy ${code.textContent?.trim() ?? ''}`)
  })
}

function fallbackCopy(text: string): void {
  try {
    const area = document.createElement('textarea')
    area.value = text
    area.setAttribute('readonly', '')
    area.style.position = 'fixed'
    area.style.opacity = '0'
    document.body.appendChild(area)
    area.select()
    document.execCommand('copy')
    document.body.removeChild(area)
  } catch {
    /* clipboard unavailable — feedback is still shown to the user */
  }
}

function copyText(text: string): void {
  if (!text) return
  const clipboard = navigator.clipboard as Clipboard | undefined
  if (clipboard?.writeText) {
    void clipboard.writeText(text).catch(() => fallbackCopy(text))
  } else {
    fallbackCopy(text)
  }
}

function copyInline(code: HTMLElement): void {
  const text = code.textContent ?? ''
  if (!text) return
  copyText(text)
  emit('copy', text)
  code.classList.add(COPIED_CLASS)
  window.setTimeout(() => code.classList.remove(COPIED_CLASS), INLINE_FEEDBACK_MS)
}

function copyBlock(button: HTMLButtonElement): void {
  const code = button.closest('pre')?.querySelector('code')
  const text = code?.textContent ?? ''
  if (!text) return
  copyText(text)
  emit('copy', text)
  button.textContent = COPIED_LABEL
  button.classList.add(COPIED_CLASS)
  window.setTimeout(() => {
    button.textContent = COPY_LABEL
    button.classList.remove(COPIED_CLASS)
  }, BLOCK_FEEDBACK_MS)
}

function onClick(event: MouseEvent): void {
  const target = event.target as HTMLElement | null
  if (!target) return

  const button = target.closest<HTMLButtonElement>('[data-code-copy]')
  if (button) {
    copyBlock(button)
    return
  }

  const inline = target.closest<HTMLElement>('code')
  if (inline && !inline.closest('pre')) copyInline(inline)
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' && event.key !== ' ') return
  const target = event.target as HTMLElement | null
  if (target?.matches('code[role="button"]')) {
    event.preventDefault()
    copyInline(target)
  }
}

onMounted(scheduleEnhance)
watch(html, scheduleEnhance)
</script>

<template>
  <div v-if="source.trim()">
    <!-- eslint-disable-next-line vue/no-v-html -- content is DOMPurify-sanitized in useMarkdown -->
    <div ref="root" class="markdown-body" @click="onClick" @keydown="onKeydown" v-html="html" />
  </div>
  <p v-else class="markdown-empty">{{ emptyText }}</p>
</template>

<style>
/* Token-only markdown presentation. Kept unscoped so it also styles the nodes
   produced by `v-html` (scoped attributes are not applied to v-html content). */
.markdown-body {
  color: var(--color-text);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  overflow-wrap: anywhere;
}

.markdown-body > :first-child {
  margin-top: 0;
}

.markdown-body > :last-child {
  margin-bottom: 0;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 0 0 var(--space-3);
  font-weight: var(--font-weight-semibold);
  line-height: var(--leading-tight);
  color: var(--color-text);
}

.markdown-body h1 {
  font-size: var(--text-xl);
}

.markdown-body h2 {
  font-size: var(--text-lg);
}

.markdown-body h3 {
  font-size: var(--text-md);
}

.markdown-body p,
.markdown-body ul,
.markdown-body ol {
  margin: 0 0 var(--space-3);
}

.markdown-body ul,
.markdown-body ol {
  padding-left: var(--space-5);
}

.markdown-body li {
  margin: 0 0 var(--space-1);
}

.markdown-body a {
  color: var(--color-accent-text);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-body blockquote {
  margin: 0 0 var(--space-3);
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  background: var(--color-surface);
  border-left: 3px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
}

.markdown-body hr {
  margin: var(--space-4) 0;
  border: 0;
  border-top: 1px solid var(--color-border);
}

.markdown-body img {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-sm);
}

.markdown-body table {
  width: 100%;
  margin: 0 0 var(--space-3);
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.markdown-body th,
.markdown-body td {
  padding: var(--space-2);
  text-align: left;
  border: 1px solid var(--color-border);
}

.markdown-body th {
  color: var(--color-text-muted);
  font-weight: var(--font-weight-semibold);
  background: var(--color-elevated);
}

.markdown-body code {
  padding: 0.1em 0.35em;
  font-family: var(--font-mono);
  font-size: 0.9em;
  color: var(--color-text);
  background: var(--color-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.markdown-body pre {
  position: relative;
  margin: 0 0 var(--space-3);
  padding: var(--space-8) var(--space-3) var(--space-3);
  overflow: auto;
  background: var(--color-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.markdown-body pre code {
  padding: 0;
  font-size: var(--text-sm);
  background: transparent;
  border: 0;
  border-radius: 0;
}

.markdown-body code.inline-code-copy {
  cursor: pointer;
}

.markdown-body code.is-copied {
  color: var(--color-success-text);
  border-color: var(--color-success-text);
}

.markdown-body .code-copy-btn {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 var(--space-2);
  font-family: var(--font-sans);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.markdown-body .code-copy-btn:hover {
  color: var(--color-text);
  background: var(--color-hover);
}

.markdown-body .code-copy-btn:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
}

.markdown-body .code-copy-btn.is-copied {
  color: var(--color-success-text);
  border-color: var(--color-success-text);
}

.markdown-body .hljs-comment,
.markdown-body .hljs-quote {
  color: var(--color-text-muted);
  font-style: italic;
}

.markdown-body .hljs-keyword,
.markdown-body .hljs-selector-tag,
.markdown-body .hljs-built_in,
.markdown-body .hljs-name,
.markdown-body .hljs-tag {
  color: var(--color-accent-text);
}

.markdown-body .hljs-string,
.markdown-body .hljs-attr,
.markdown-body .hljs-attribute,
.markdown-body .hljs-symbol,
.markdown-body .hljs-bullet,
.markdown-body .hljs-addition {
  color: var(--color-success-text);
}

.markdown-body .hljs-number,
.markdown-body .hljs-literal,
.markdown-body .hljs-meta,
.markdown-body .hljs-link {
  color: var(--color-info-text);
}

.markdown-body .hljs-title,
.markdown-body .hljs-section,
.markdown-body .hljs-function {
  color: var(--color-warning-text);
}

.markdown-body .hljs-variable,
.markdown-body .hljs-template-variable,
.markdown-body .hljs-params,
.markdown-body .hljs-property {
  color: var(--color-text);
}

.markdown-body .hljs-deletion {
  color: var(--color-danger-text);
}

.markdown-body .hljs-emphasis {
  font-style: italic;
}

.markdown-body .hljs-strong {
  font-weight: var(--font-weight-bold);
}

.markdown-empty {
  margin: 0;
  color: var(--color-text-muted);
}
</style>
