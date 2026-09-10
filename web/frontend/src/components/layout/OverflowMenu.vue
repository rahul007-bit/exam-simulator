<script setup lang="ts">
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { computed } from 'vue'

import Icon from '@/components/Icon.vue'
import { FOCUS_RING } from '@/components/ui'

import type { HeaderMenuItem } from './types'

/**
 * OverflowMenu (FE-020) — the single `⋯` menu that keeps secondary header
 * actions out of the primary 52px bar.
 *
 * Built on Headless UI `Menu` so it gets the accessible `menu`/`menuitem`
 * roles, roving arrow-key focus, `Escape` to close and click-outside handling
 * for free. Colours come from FE-012 tokens only; the only semantic state is
 * the danger treatment used by the admin-only rows (no raw hex/glow/emoji).
 */

const props = withDefaults(
  defineProps<{
    items: HeaderMenuItem[]
    /** Accessible name for the trigger (icon-only). */
    label?: string
    /** Which edge the panel aligns to. */
    align?: 'left' | 'right'
    disabled?: boolean
  }>(),
  { label: 'More actions', align: 'right', disabled: false },
)

const emit = defineEmits<{ select: [id: string] }>()

const panelPosition = computed(() => (props.align === 'right' ? 'right-0' : 'left-0'))

function choose(item: HeaderMenuItem): void {
  if (item.disabled) return
  emit('select', item.id)
}
</script>

<template>
  <Menu as="div" class="relative">
    <MenuButton
      type="button"
      :disabled="disabled"
      :aria-label="label"
      :title="label"
      class="inline-flex h-8 w-8 flex-none items-center justify-center rounded-[var(--radius-sm)] border border-border bg-surface text-text-muted transition-colors hover:bg-hover hover:text-text disabled:cursor-not-allowed disabled:opacity-60"
      :class="FOCUS_RING"
      data-testid="header-overflow"
    >
      <Icon name="ellipsis" :size="18" />
    </MenuButton>

    <Transition
      enter-active-class="transition duration-100 ease-out motion-reduce:transition-none"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-75 ease-in motion-reduce:transition-none"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <MenuItems
        :class="[
          'absolute z-50 mt-1 w-56 origin-top rounded-[var(--radius-md)] border border-border bg-elevated p-1 shadow-[var(--shadow-md)] focus:outline-none',
          panelPosition,
        ]"
        data-testid="header-overflow-menu"
      >
        <MenuItem
          v-for="item in items"
          :key="item.id"
          v-slot="{ active }"
          :disabled="item.disabled"
        >
          <button
            type="button"
            :disabled="item.disabled"
            :data-action="item.id"
            :class="[
              'flex w-full items-center gap-2 rounded-[var(--radius-sm)] px-2.5 py-2 text-left text-sm transition-colors',
              active && !item.disabled ? 'bg-hover' : '',
              item.danger ? 'text-danger-text' : 'text-text',
              item.disabled ? 'cursor-not-allowed opacity-60' : '',
            ]"
            @click="choose(item)"
          >
            <Icon :name="item.icon" :size="16" class="shrink-0" />
            <span class="truncate">{{ item.label }}</span>
          </button>
        </MenuItem>
      </MenuItems>
    </Transition>
  </Menu>
</template>
