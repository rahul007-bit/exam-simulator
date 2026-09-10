<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

import Icon from '@/components/Icon.vue'
import { Button } from '@/components/ui'
import { useFullscreen } from '@/composables/useFullscreen'

/**
 * FullscreenGuard (FE-028) — the "EXAM LOCKED: FULLSCREEN REQUIRED" overlay.
 *
 * Ported from the legacy `showFullscreenWarning` (`web/static/js/app.js:1797`),
 * redesigned to the slate/indigo system (D-003): severity conveyed by colour
 * only, with no animated keyframes, shadow effects or emoji. It reads the shared
 * `useFullscreen` singleton so the candidate view can call `enter()` on Start
 * while this component reacts to the resulting state.
 *
 * Accessibility: `role="alertdialog"` with `aria-modal`, a labelled/described
 * body and an element with `role="alert"` for the assertive announcement. Focus
 * is moved to the return action while shown and Tab is trapped on that control.
 */

const { warningVisible, reenter } = useFullscreen()

const returnButton = ref<InstanceType<typeof Button> | null>(null)

async function focusReturn(): Promise<void> {
  await nextTick()
  returnButton.value?.$el?.focus?.()
}

watch(warningVisible, (visible) => {
  if (visible) void focusReturn()
})

onMounted(() => {
  if (warningVisible.value) void focusReturn()
})

function onReturn(): void {
  void reenter()
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out motion-reduce:transition-none"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
    >
      <div
        v-if="warningVisible"
        class="fixed inset-0 z-[2147483000] flex flex-col items-center justify-center gap-4 bg-app/95 p-6 text-center backdrop-blur-sm"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="fullscreen-warning-title"
        aria-describedby="fullscreen-warning-desc"
        @keydown.tab.prevent="focusReturn"
      >
        <span class="text-danger-text" aria-hidden="true">
          <Icon name="warning" :size="40" />
        </span>

        <h2
          id="fullscreen-warning-title"
          role="alert"
          class="m-0 text-2xl font-bold tracking-tight text-danger-text"
        >
          EXAM LOCKED: FULLSCREEN REQUIRED
        </h2>

        <p id="fullscreen-warning-desc" class="m-0 max-w-md text-sm leading-relaxed text-text-muted">
          Exam policy requires fullscreen mode. Your workspace is locked. Return to fullscreen to
          resume.
        </p>

        <Button ref="returnButton" variant="primary" size="lg" class="mt-2" @click="onReturn">
          Return to fullscreen and resume
        </Button>
      </div>
    </Transition>
  </Teleport>
</template>
