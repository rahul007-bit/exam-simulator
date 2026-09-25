<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { startSession } from '@/api/session'
import AdminAssignmentPanel from '@/components/admin/AdminAssignmentPanel.vue'
import AdminConfigForm from '@/components/admin/AdminConfigForm.vue'
import AdminInviteForm from '@/components/admin/AdminInviteForm.vue'
import AdminResourceForm from '@/components/admin/AdminResourceForm.vue'
import AdminUsersPanel from '@/components/admin/AdminUsersPanel.vue'
import PresetBuilder from '@/components/admin/PresetBuilder.vue'
import { Button, Card } from '@/components/ui'
import { useAdminConfig } from '@/composables/useAdminConfig'
import { buildInviteUrl, copyTextToClipboard, useAdminInvites } from '@/composables/useAdminInvites'
import { useToast } from '@/composables/useToast'

/**
 * Admin settings (split out of AdminView).
 *
 * Hosts the configuration surface — default preset, server resource limits,
 * candidate invites, per-user assignments and the custom exam builder — so the
 * sessions page stays focused on live sessions, invitations and history.
 */

const router = useRouter()
const { push } = useToast()
const {
  presetOptions,
  defaultPreset,
  resources,
  loading: configLoading,
  savingPreset,
  savingResources,
  presetName,
  loadAll: loadAdminConfig,
  saveDefaultPreset,
  saveMaxSessions,
} = useAdminConfig()
const { creating: inviteCreating, latestInvite, createInvite } = useAdminInvites()
const inviteStarting = ref(false)

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

async function refreshAdminConfig(): Promise<void> {
  try {
    await loadAdminConfig()
  } catch (cause) {
    push({ variant: 'error', message: describeError(cause) })
  }
}

async function onSavePreset(preset: string): Promise<void> {
  try {
    await saveDefaultPreset(preset)
    push({ variant: 'success', message: `Default preset set to ${presetName(preset) ?? preset}` })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not save default preset',
      message: describeError(cause),
    })
  }
}

async function onSaveMaxSessions(limit: number): Promise<void> {
  try {
    await saveMaxSessions(limit)
    push({ variant: 'success', message: `Concurrency limit updated to ${limit}` })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not update resource limit',
      message: describeError(cause),
    })
  }
}

function onInvalidMaxSessions(message: string): void {
  push({ variant: 'warning', message })
}

async function onCreateInvite(preset: string): Promise<void> {
  try {
    const invite = await createInvite(preset || undefined)
    await copyTextToClipboard(buildInviteUrl(invite.url))
    push({ variant: 'success', message: 'Candidate link generated & copied!' })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not create invite',
      message: describeError(cause),
    })
  }
}

async function onCopyInvite(url: string): Promise<void> {
  try {
    await copyTextToClipboard(url)
    push({ variant: 'success', message: 'Invite link copied to clipboard!' })
  } catch (cause) {
    push({ variant: 'error', message: describeError(cause) })
  }
}

async function onStartInvite(token: string): Promise<void> {
  if (inviteStarting.value) return
  inviteStarting.value = true
  try {
    await startSession({ candidate_token: token })
    push({ variant: 'success', message: 'Starting exam…' })
    await router.push({ path: '/', query: { token } })
  } catch (cause) {
    push({ variant: 'error', title: 'Could not start exam', message: describeError(cause) })
  } finally {
    inviteStarting.value = false
  }
}

onMounted(() => {
  void refreshAdminConfig()
})
</script>

<template>
  <main class="mx-auto w-full max-w-6xl p-4">
    <div class="flex flex-col gap-4">
      <Card
        title="Admin settings"
        subtitle="Configure the default preset, capacity, invites, assignments and custom exams."
      >
        <template #actions>
          <Button variant="secondary" data-testid="settings-back" @click="router.push('/admin')">
            Back to sessions
          </Button>
        </template>
      </Card>

      <div class="grid gap-4 lg:grid-cols-2">
        <AdminConfigForm
          :saved="defaultPreset"
          :options="presetOptions"
          :loading="configLoading"
          :saving="savingPreset"
          @save="onSavePreset"
          @reload="refreshAdminConfig"
        />

        <AdminInviteForm
          :options="presetOptions"
          :invite="latestInvite"
          :creating="inviteCreating"
          :starting="inviteStarting"
          @create="onCreateInvite"
          @copy="onCopyInvite"
          @start="onStartInvite"
        />
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <AdminResourceForm
          :resources="resources"
          :loading="configLoading"
          :saving="savingResources"
          @save="onSaveMaxSessions"
          @invalid="onInvalidMaxSessions"
          @reload="refreshAdminConfig"
        />

        <PresetBuilder />
      </div>

      <AdminAssignmentPanel />

      <AdminUsersPanel />
    </div>
  </main>
</template>
