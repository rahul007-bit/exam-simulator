import type { IconName } from '@/components/ui'

/**
 * Candidate shell public types (FE-020).
 *
 * Kept in a plain `.ts` module (like the FE-012 UI prop types and FE-022
 * `task.ts`) because the ambient `*.vue` declaration types SFCs as opaque
 * components that cannot carry named type exports. The pure helpers in
 * `menu.ts` are unit-testable without mounting any component.
 */

/** A single actionable row inside the header `⋯` overflow menu. */
export interface HeaderMenuItem {
  /** Stable action id emitted on selection. */
  id: OverflowAction
  /** Visible label. */
  label: string
  /** Inline-SVG glyph from the FE-014 catalogue. */
  icon: IconName
  /** Renders with the semantic danger treatment (admin End/Reset). */
  danger?: boolean
  /** Renders disabled (e.g. "Copy session ID" before a session exists). */
  disabled?: boolean
}

/**
 * Every action the overflow menu can raise. The candidate shell routes these to
 * the owning feature tasks (FE-026 workspace, FE-027 clipboard, FE-028
 * fullscreen, FE-029 recordings, FE-031 admin).
 */
export type OverflowAction =
  | 'copy-session-id'
  | 'fullscreen'
  | 'reload'
  | 'new-tab'
  | 'copy-from-desktop'
  | 'recordings'
  | 'admin-end'
  | 'admin-reset'

export interface OverflowMenuOptions {
  /** A session id exists, so "Copy session ID" is enabled. */
  hasSessionId?: boolean
  /** Admin-only End/Reset entries are shown. */
  isAdmin?: boolean
  /** Recordings & review entry is shown (legacy gates this to admins). */
  canViewRecordings?: boolean
}

/** One-based task progress shown in the header. */
export interface HeaderProgress {
  current: number
  total: number
}
