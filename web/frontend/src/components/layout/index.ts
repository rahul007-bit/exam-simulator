/**
 * Layout components barrel (FE-020).
 *
 * The candidate shell public surface: `AppShell` (52px header + workspace slot),
 * `AppHeader` (primary controls), `WorkspaceSplit` (FE-021 split panes) and
 * `OverflowMenu` (secondary actions).
 */
export { default as AppShell } from './AppShell.vue'
export { default as AppHeader } from './AppHeader.vue'
export { default as WorkspaceSplit } from './WorkspaceSplit.vue'
export { default as OverflowMenu } from './OverflowMenu.vue'

export { buildOverflowMenu, progressLabel } from './menu'
export type { HeaderMenuItem, HeaderProgress, OverflowAction, OverflowMenuOptions } from './types'
