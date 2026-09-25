<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import Icon from '@/components/Icon.vue'
import { useSplitPane } from '@/composables/useSplitPane'

/**
 * WorkspaceSplit (FE-021) — the candidate workspace split.
 *
 * Two panes (left task / right desktop+terminal) separated by a draggable,
 * keyboard-accessible gutter. Default 24% / 76%, min `[300, 520]px`, ratio
 * persisted by `useSplitPane` under `cka:workspace:split`. Double-clicking the
 * gutter resets to the default and the handle button collapses/expands the left
 * pane to maximize the workspace.
 *
 * The desktop/terminal tab bar is owned by FE-026 and is intentionally **not**
 * built here — the right pane exposes a default slot plus a marked
 * `TODO(workspace-tabs)` placeholder.
 */

const props = withDefaults(
  defineProps<{
    /** Left-pane share (%) when no ratio is persisted / on reset. */
    defaultRatio?: number
    /** Left-pane minimum width in px. */
    minLeft?: number
    /** Right-pane minimum width in px. */
    minRight?: number
    /** `localStorage` key for the persisted ratio. */
    storageKey?: string
  }>(),
  {
    defaultRatio: 24,
    minLeft: 300,
    minRight: 520,
    storageKey: 'cka:workspace:split',
  },
)

const container = ref<HTMLElement | null>(null)

const {
  ratio,
  collapsed,
  leftStyle,
  rightStyle,
  onPointerDown,
  onKeydown,
  reset,
  toggleCollapse,
  dispose,
} = useSplitPane({
  container,
  defaultRatio: props.defaultRatio,
  minLeft: props.minLeft,
  minRight: props.minRight,
  storageKey: props.storageKey,
})

onBeforeUnmount(dispose)

defineExpose({ ratio, collapsed, reset, toggleCollapse })
</script>

<template>
  <div
    ref="container"
    class="relative flex h-full min-h-0 w-full"
    data-testid="workspace-split"
  >
    <!-- Left: task pane -->
    <section
      v-show="!collapsed"
      class="min-h-0 min-w-0 flex-none overflow-hidden border-r border-border"
      :style="leftStyle"
      data-testid="split-left"
    >
      <slot name="left" />
    </section>

    <!-- Draggable gutter (keyboard accessible separator) -->
    <div
      class="group relative z-10 flex w-1.5 flex-none touch-none cursor-col-resize items-center justify-center bg-transparent transition-colors hover:bg-hover"
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize task pane"
      :aria-valuenow="Math.round(ratio)"
      aria-valuemin="0"
      aria-valuemax="100"
      :tabindex="0"
      data-testid="split-gutter"
      @pointerdown="onPointerDown"
      @dblclick="reset"
      @keydown="onKeydown"
    >
      <button
        type="button"
        class="absolute left-1/2 top-1/2 flex h-6 w-6 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-[var(--radius-sm)] border border-border bg-surface text-text-muted shadow-[var(--shadow-sm)] transition-colors hover:bg-hover hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring-color)]"
        :aria-label="collapsed ? 'Expand task pane' : 'Collapse task pane'"
        :title="collapsed ? 'Expand task pane' : 'Collapse task pane (drag fully left)'"
        :aria-pressed="collapsed"
        data-testid="split-collapse"
        @pointerdown.stop
        @dblclick.stop
        @click.stop="toggleCollapse"
      >
        <Icon :name="collapsed ? 'chevron-right' : 'chevron-left'" :size="14" />
      </button>
    </div>

    <!-- Right: desktop / terminal workspace (majority of the width) -->
    <section
      class="min-h-0 min-w-0 flex-1 overflow-hidden bg-elevated"
      :style="rightStyle"
      data-testid="split-right"
    >
      <slot />
    </section>
  </div>
</template>
