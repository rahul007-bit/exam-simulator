import type { HeaderMenuItem, HeaderProgress, OverflowMenuOptions } from './types'

/**
 * Pure header helpers (FE-020).
 *
 * Ordering and admin gating mirror the legacy workspace dropdown: Fullscreen,
 * Reload, New tab, Copy from Desktop, Recordings & Review, then admin-only
 * End/Reset. Copy session ID is prepended because the session-id badge moved
 * into the menu.
 */

const PRIMARY_ITEMS: readonly HeaderMenuItem[] = [
  { id: 'fullscreen', label: 'Fullscreen', icon: 'maximize' },
  { id: 'reload', label: 'Reload', icon: 'refresh' },
  { id: 'new-tab', label: 'New tab', icon: 'external-link' },
  { id: 'copy-from-desktop', label: 'Copy from Desktop', icon: 'desktop' },
]

/** Build the overflow menu rows for the current shell state. */
export function buildOverflowMenu(options: OverflowMenuOptions = {}): HeaderMenuItem[] {
  const items: HeaderMenuItem[] = [
    {
      id: 'copy-session-id',
      label: 'Copy session ID',
      icon: 'copy',
      disabled: !options.hasSessionId,
    },
    ...PRIMARY_ITEMS,
  ]

  if (options.canViewRecordings) {
    items.push({ id: 'recordings', label: 'Recordings & review', icon: 'play' })
  }

  if (options.isAdmin) {
    items.push({ id: 'admin-end', label: 'End exam', icon: 'success', danger: true })
    items.push({ id: 'admin-reset', label: 'Reset exam', icon: 'refresh', danger: true })
  }

  return items
}

/** `Task 3 of 17`; a neutral placeholder until a session is active. */
export function progressLabel(progress: HeaderProgress): string {
  if (progress.total <= 0) return 'No tasks'
  return `Task ${progress.current} of ${progress.total}`
}
