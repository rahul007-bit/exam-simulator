import type { BadgeVariant } from '@/components/ui'

/**
 * Candidate task model + badge derivation for `TaskPane` (FE-022).
 *
 * Kept in a plain `.ts` module (like the FE-012 UI prop types) because the
 * ambient `*.vue` declaration types SFCs as opaque components that cannot carry
 * named type exports.
 */

export interface TaskPaneTask {
  task_num: number
  title: string
  description: string
  points: number
  namespace?: string | null
  target_context?: string | null
  is_flagged?: boolean
}

export interface TaskBadge {
  key: string
  label: string
  variant: BadgeVariant
  /**
   * Overrides the clipboard text when set. Metadata chips show a descriptive
   * label (`context: k3d-cka`) but should copy only the raw value
   * (`k3d-cka`); badges without `copy` fall back to the label.
   */
  copy?: string
}

const DEFAULT_CONTEXT = 'k3d-cka'
const DEFAULT_NAMESPACE = 'default'

/**
 * Header badges. Metadata uses neutral chips; the only semantic state is the
 * danger flag for a flagged task (FE-022 acceptance: neutral + semantic status
 * colours only; difficulty stays intentionally hidden to match legacy).
 */
export function taskBadges(task: TaskPaneTask): TaskBadge[] {
  const badges: TaskBadge[] = [
    { key: 'number', label: `Task ${task.task_num}`, variant: 'neutral' },
    { key: 'points', label: `${task.points} pts`, variant: 'neutral' },
    {
      key: 'context',
      label: `context: ${task.target_context || DEFAULT_CONTEXT}`,
      variant: 'neutral',
      copy: task.target_context || DEFAULT_CONTEXT,
    },
    {
      key: 'namespace',
      label: `ns: ${task.namespace || DEFAULT_NAMESPACE}`,
      variant: 'neutral',
      copy: task.namespace || DEFAULT_NAMESPACE,
    },
  ]

  if (task.is_flagged) {
    badges.push({ key: 'flagged', label: 'FLAGGED', variant: 'danger' })
  }

  return badges
}
