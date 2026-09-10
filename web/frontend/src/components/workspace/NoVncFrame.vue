<script setup lang="ts">
import { nextTick, ref, useTemplateRef, watch } from 'vue'

import { VNC_ALLOW, buildNoVncUrl, postClipboardToFrame } from '@/composables/useVnc'

/**
 * NoVncFrame (FE-026) — the imperative noVNC desktop island.
 *
 * An `<iframe>` pointed at the server's compiled `/novnc/vnc.html` bundle. The
 * URL/params and `allow` contract are preserved byte-for-byte from the legacy
 * client (D-007): see `web/static/index.html:142` and `web/static/js/app.js:1655`.
 *
 * State preservation: `src` is set once when the island first becomes active and
 * is intentionally never cleared while it stays mounted, so switching to the
 * Terminal tab and back does not tear down the VNC session. `active` only gates
 * the *first* load; visibility is controlled by the parent via `v-show`.
 */

const props = withDefaults(
  defineProps<{
    sessionId?: string
    /** Whether this frame is the visible workspace tab. */
    active?: boolean
    /** Observe mode: appends `view_only=true` (admin, legacy `admin.js:778`). */
    viewOnly?: boolean
    title?: string
    ariaLabel?: string
  }>(),
  {
    sessionId: '',
    active: true,
    viewOnly: false,
    title: 'Remote desktop',
    ariaLabel: 'Remote desktop',
  },
)

const frameRef = useTemplateRef<HTMLIFrameElement>('frame')
const src = ref('')

function currentUrl(): string {
  return buildNoVncUrl(props.sessionId, { viewOnly: props.viewOnly })
}

function ensureLoaded(): void {
  const next = currentUrl()
  if (src.value !== next) src.value = next
}

watch(
  () => props.active,
  (active) => {
    if (active) ensureLoaded()
  },
  { immediate: true },
)

watch(
  () => [props.sessionId, props.viewOnly],
  () => {
    if (props.active) ensureLoaded()
  },
)

/** Force a fresh noVNC connection (legacy `frame.src = frame.src`, `app.js:1737`). */
function reload(): void {
  const next = currentUrl()
  src.value = 'about:blank'
  void nextTick(() => {
    src.value = next
  })
}

/** Push host clipboard text into the island (`syncTextToVnc`, `app.js:256`). */
function sendClipboard(text: string): boolean {
  return postClipboardToFrame(frameRef.value, text)
}

defineExpose({
  frame: frameRef,
  src,
  reload,
  sendClipboard,
})
</script>

<template>
  <iframe
    ref="frame"
    :src="src"
    :title="title"
    :aria-label="ariaLabel"
    :allow="VNC_ALLOW"
    allowfullscreen
    class="h-full w-full border-0 bg-app"
    data-testid="novnc-frame"
  ></iframe>
</template>
