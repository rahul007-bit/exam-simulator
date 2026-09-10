<script setup lang="ts">
import { computed } from 'vue'

import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()

const nextLabel = computed(() => (theme.value === 'dark' ? 'light' : 'dark'))
const label = computed(() => `Switch to ${nextLabel.value} theme`)
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="label"
    :title="label"
    :data-theme-state="theme"
    @click="toggleTheme"
  >
    <span class="theme-toggle__icon" aria-hidden="true">
      <svg
        v-if="theme === 'dark'"
        viewBox="0 0 24 24"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="4" />
        <path
          d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
        />
      </svg>
      <svg
        v-else
        viewBox="0 0 24 24"
        width="16"
        height="16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
      </svg>
    </span>
    <span class="theme-toggle__text">{{ nextLabel }}</span>
  </button>
</template>

<style scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    background-color var(--transition-fast),
    border-color var(--transition-fast);
}

.theme-toggle:hover {
  background-color: var(--color-hover);
  border-color: var(--color-border-strong);
}

.theme-toggle:active {
  background-color: var(--color-elevated);
}

.theme-toggle__icon {
  display: inline-flex;
  color: var(--color-accent-text);
}

.theme-toggle__text {
  text-transform: capitalize;
}
</style>
