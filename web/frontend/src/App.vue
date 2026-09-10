<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import Toaster from '@/components/Toaster.vue'

const route = useRoute()
// The candidate route renders its own slim header (AppShell), so suppress the
// global topbar there to avoid a stacked double bar (FE-020 integration).
// `route` is undefined when the app is mounted without a router (unit smoke
// tests), in which case the topbar is shown.
const showTopbar = computed(() => route?.name !== 'candidate')
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--fixed': !showTopbar }">
    <header v-if="showTopbar" class="app-topbar">
      <span class="app-topbar__brand">Kubernetes Exam Simulator</span>
      <ThemeToggle />
    </header>
    <RouterView />
    <Toaster />
    <ConfirmDialog />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/*
 * The candidate route (which renders its own AppShell) owns the viewport: it
 * locks to 100vh and hides page overflow so its internal panes scroll instead.
 * Every other route (admin/login) is a normal document that scrolls, so its
 * content must not be clipped to the viewport.
 */
.app-shell--fixed {
  height: 100vh;
  overflow: hidden;
}

.app-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  min-height: var(--header-height);
  padding: 0 var(--space-4);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.app-topbar__brand {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
}
</style>
