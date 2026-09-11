import { ref } from 'vue'

import { createSessionInvite } from '@/api/admin'
import type { CreateSessionInviteResponse } from '@/api/admin'
import { fallbackCopyText } from '@/composables/useClipboard'

/**
 * useAdminInvites (FE-033) — data + mutation layer for the admin
 * "create candidate invite" card.
 *
 * Endpoint (already typed in `@/api/admin`):
 *   POST /api/admin/sessions/create -> { token, preset, url }
 *
 * The backend returns a root-relative `url` (`/?token=<token>`). The legacy
 * admin surface composed the absolute link from `window.location.origin`;
 * `buildInviteUrl` preserves that behavior and passes an already-absolute URL
 * through untouched.
 *
 * Mutations rethrow so the view can toast the server `detail` (e.g. the HTTP
 * 429 "Server resource limit reached…") while the composable also records it in
 * `error`. A failed create clears `latestInvite` so no stale link is shown.
 */

/** Turn a possibly root-relative invite URL into an absolute one. */
export function absoluteInviteUrl(url: string, origin?: string): string {
  if (/^https?:\/\//i.test(url)) return url
  const base = origin ?? (typeof window !== 'undefined' ? window.location.origin : '')
  if (!base) return url
  return url.startsWith('/') ? `${base}${url}` : `${base}/${url}`
}

/** Absolute invite URL using the current origin (SSR/jsdom-safe). */
export function buildInviteUrl(url: string): string {
  return absoluteInviteUrl(url, typeof window !== 'undefined' ? window.location.origin : undefined)
}

/**
 * Copy text to the clipboard, falling back to the legacy `execCommand('copy')`
 * shim when the async Clipboard API is unavailable or blocked.
 */
export async function copyTextToClipboard(text: string, doc?: Document): Promise<boolean> {
  if (!text) return false

  const clipboard = typeof navigator !== 'undefined' ? navigator.clipboard : undefined
  if (clipboard?.writeText) {
    try {
      await clipboard.writeText(text)
      return true
    } catch {
      /* permission denied / insecure context — fall through to the fallback */
    }
  }

  fallbackCopyText(text, doc ?? (typeof document !== 'undefined' ? document : undefined))
  return true
}

export function useAdminInvites() {
  const creating = ref(false)
  const error = ref<string | null>(null)
  const latestInvite = ref<CreateSessionInviteResponse | null>(null)

  /** Create a candidate invite (optionally pre-assigned to a preset). */
  async function createInvite(preset?: string): Promise<CreateSessionInviteResponse> {
    creating.value = true
    error.value = null
    try {
      const invite = await createSessionInvite(preset)
      latestInvite.value = invite
      return invite
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      latestInvite.value = null
      throw cause
    } finally {
      creating.value = false
    }
  }

  return { creating, error, latestInvite, createInvite }
}

export type UseAdminInvites = ReturnType<typeof useAdminInvites>
