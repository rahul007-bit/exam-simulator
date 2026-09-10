/**
 * UI primitives barrel (FE-012).
 *
 * Import components from here to keep the public surface in one place:
 *   import { Button, Modal, SegmentedControl } from '@/components/ui'
 */
export { default as Button } from './Button.vue'
export { default as Input } from './Input.vue'
export { default as Select } from './Select.vue'
export { default as Badge } from './Badge.vue'
export { default as Chip } from './Chip.vue'
export { default as Card } from './Card.vue'
export { default as Modal } from './Modal.vue'
export { default as Spinner } from './Spinner.vue'
export { default as SegmentedControl } from './SegmentedControl.vue'
export { default as DataTable } from './DataTable.vue'
export { default as Icon } from '../Icon.vue'

/**
 * Public column configuration for `DataTable` (FE-013).
 *
 * Defined here (rather than in the SFC) so the plain `tsc` ambient `*.vue`
 * declaration can still resolve the named type export. `DataTable.vue` imports
 * this type back with `import type`, which is erased at build time.
 */
export interface DataTableColumn<T = Record<string, unknown>> {
  /** Accessor key on the row object. */
  key: Extract<keyof T, string>
  /** Visible column header text. */
  header: string
  /**
   * Optional custom value accessor. Overrides the default `row[key]` value used
   * for sorting and global filtering; `cell` still controls the displayed text.
   */
  accessor?: (row: T) => unknown
  /** Optional custom cell renderer; defaults to the raw accessor value. */
  cell?: (row: T) => string | number
  /** Enables click/keyboard sort on this column (default true). */
  sortable?: boolean
  /** Includes this column in the global search filter (default true). */
  filterable?: boolean
  /** Text alignment for the cell contents. */
  align?: 'left' | 'center' | 'right'
}

export type {
  ButtonVariant,
  ButtonSize,
  BadgeVariant,
  BadgeSize,
  ChipVariant,
  CardVariant,
  CardPadding,
  ModalSize,
  SelectOption,
  SegmentOption,
} from './types'

export { ICONS, ICON_NAMES } from './icons'
export type { IconName, IconShape, IconPath, IconCircle } from './icons'

export { FOCUS_RING, DISABLED } from './shared'
