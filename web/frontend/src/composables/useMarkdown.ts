import DOMPurify from 'dompurify'
import type { Config as PurifyConfig } from 'dompurify'
import hljs from 'highlight.js/lib/common'
import { Marked } from 'marked'
import { markedHighlight } from 'marked-highlight'

/**
 * Markdown pipeline (FE-022) — `marked` + `marked-highlight`/`highlight.js` for
 * rendering, then `DOMPurify` for sanitisation.
 *
 * Security contract: `renderMarkdown()` is the ONLY supported way to turn task
 * markdown into HTML. The returned string is always run through DOMPurify, so
 * event-handler attributes (`onerror`), `<script>`/`<iframe>` tags and
 * `javascript:` URLs are removed before the HTML reaches `v-html`.
 *
 * The renderer is token-styled by `MarkdownRenderer.vue`; nothing here emits
 * colours (no raw hex) and no code block is injected with executable markup.
 */

const PURIFY_CONFIG: PurifyConfig = {
  // Strip tags that can execute or restyle arbitrary content. `script`/`style`
  // are also removed by DOMPurify defaults; listing them documents intent.
  FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form'],
  // Inline styles are never needed for task instructions and are a common XSS
  // / layout-abuse vector.
  FORBID_ATTR: ['style'],
}

const HIGHLIGHT_LANG_PREFIX = 'hljs language-'
const EMPTY_LANG_CLASS = 'hljs'

let renderer: Marked | null = null

function getRenderer(): Marked {
  if (renderer) return renderer

  renderer = new Marked(
    markedHighlight({
      langPrefix: HIGHLIGHT_LANG_PREFIX,
      emptyLangClass: EMPTY_LANG_CLASS,
      highlight(code: string, language: string): string {
        const lang = language && hljs.getLanguage(language) ? language : 'plaintext'
        try {
          return hljs.highlight(code, { language: lang }).value
        } catch {
          return hljs.highlight(code, { language: 'plaintext' }).value
        }
      },
    }),
  ).setOptions({ gfm: true, breaks: true })

  return renderer
}

/** Sanitize an HTML string with DOMPurify (no markdown parsing). */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, PURIFY_CONFIG)
}

/** Render markdown to sanitized HTML. Safe to bind with `v-html`. */
export function renderMarkdown(source?: string | null): string {
  const html = getRenderer().parse(source ?? '')
  return sanitizeHtml(typeof html === 'string' ? html : '')
}

export interface MarkdownApi {
  renderMarkdown: typeof renderMarkdown
  sanitizeHtml: typeof sanitizeHtml
}

/** Composable wrapper so components depend on a stable object API. */
export function useMarkdown(): MarkdownApi {
  return { renderMarkdown, sanitizeHtml }
}
