/**
 * Public prop types for the UI primitives (FE-012).
 *
 * Kept in a plain `.ts` module because the ambient `*.vue` declaration in
 * `env.d.ts` types SFCs as opaque components and cannot carry named type exports.
 */

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'warning' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

export type BadgeVariant = 'neutral' | 'accent' | 'success' | 'warning' | 'danger' | 'info'
export type BadgeSize = 'sm' | 'md'

export type ChipVariant = 'neutral' | 'accent' | 'success' | 'warning' | 'danger' | 'info'

export type CardVariant = 'default' | 'outlined' | 'elevated'
export type CardPadding = 'none' | 'sm' | 'md' | 'lg'

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SegmentOption {
  value: string
  label: string
  disabled?: boolean
}
