<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listMyAssignments } from '@/api/assignments'
import type { Assignment } from '@/api/assignments'
import PresetBuilder from '@/components/admin/PresetBuilder.vue'
import { Badge, Button, Card, Icon, Spinner } from '@/components/ui'
import type { BadgeVariant } from '@/components/ui'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'

/**
 * DashboardView (FS-005) — the signed-in user's own exams.
 *
 * Lists only the current user's assignments from `GET /api/assignments` and
 * never touches the preset/question catalog (D-010 / FS-008). The route guard
 * already ensures an authenticated session, but the view re-checks defensively
 * before loading.
 *
 * Assignments reuse the invitation/token flow (D-011): each row's `url` is
 * `/?token=<token>`, so "Start" extracts the token and hands it to the
 * candidate route (`/?token=<token>`), which begins the assigned session.
 *
 * Colours resolve to design tokens only (no raw hex or emoji).
 */

const auth = useAuthStore()
const session = useSessionStore()
const router = useRouter()

const assignments = ref<Assignment[]>([])
const loading = ref(true)
const refreshing = ref(false)
const error = ref<string | null>(null)

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

/** Pull the invitation token out of an assignment's `/?token=...` URL. */
function tokenFromUrl(url: string): string {
  const queryStart = url.indexOf('?')
  if (queryStart === -1) return ''
  return new URLSearchParams(url.slice(queryStart + 1)).get('token') ?? ''
}

function normalizeStatus(status: string | undefined): string {
  return (status ?? '').toLowerCase()
}

function statusLabel(status: string | undefined): string {
  const value = normalizeStatus(status) || 'pending'
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function statusVariant(status: string | undefined): BadgeVariant {
  const value = normalizeStatus(status)
  if (value === 'pending') return 'warning'
  if (value === 'started' || value === 'active') return 'success'
  if (value === 'expired') return 'neutral'
  return 'info'
}

function isStartable(status: string | undefined): boolean {
  const value = normalizeStatus(status)
  return value !== 'expired'
}

function actionLabel(status: string | undefined): string {
  return normalizeStatus(status) === 'started' ? 'Resume' : 'Start'
}

function formatDate(value: string): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

async function loadAssignments(): Promise<void> {
  error.value = null
  try {
    const response = await listMyAssignments()
    assignments.value = response.assignments
  } catch (cause) {
    const message = describeError(cause)
    // A legacy admin cookie can satisfy the route guard without a user auth
    // session; the user-scoped API then 401s. Send them to sign in.
    if (/unauthor|401/i.test(message)) {
      void router.push({ name: 'login', query: { redirect: '/assignments' } })
      return
    }
    error.value = message
  }
}

async function bootstrap(): Promise<void> {
  if (!auth.isAuthenticated) await auth.check()
  if (!auth.isAuthenticated) {
    void router.push({ name: 'login', query: { redirect: '/assignments' } })
    return
  }
  // Best-effort: an active exam hides the custom-exam builder.
  try {
    await session.fetchSession()
  } catch {
    /* the builder simply stays hidden/visible based on the current store state */
  }
  await loadAssignments()
  loading.value = false
}

async function refresh(): Promise<void> {
  refreshing.value = true
  await loadAssignments()
  refreshing.value = false
}

function start(assignment: Assignment): void {
  const token = tokenFromUrl(assignment.url)
  if (!token) {
    error.value = 'This assignment is missing its start link.'
    return
  }
  void router.push({ path: '/', query: { token } })
}

onMounted(() => {
  void bootstrap()
})
</script>

<template>
  <main class="mx-auto flex w-full max-w-4xl flex-col gap-4 p-4">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div class="min-w-0">
        <h1 class="m-0 text-xl font-semibold text-text">My exams</h1>
        <p v-if="auth.username" class="m-0 mt-0.5 text-sm text-text-muted">
          Assigned to {{ auth.username }}
        </p>
      </div>
      <Button
        variant="secondary"
        size="sm"
        :loading="refreshing"
        :disabled="refreshing || loading"
        data-testid="dashboard-refresh"
        @click="refresh"
      >
        <Icon name="refresh" :size="16" class="flex-none" />
        Refresh
      </Button>
    </header>

    <Card padding="none">
      <div v-if="loading" class="flex justify-center p-10" data-testid="dashboard-loading">
        <Spinner size="lg" label="Loading your exams" />
      </div>

      <div v-else-if="error" class="p-10" data-testid="dashboard-error">
        <p role="alert" class="m-0 text-sm text-danger-text">{{ error }}</p>
        <div class="mt-3">
          <Button variant="secondary" size="sm" data-testid="dashboard-retry" @click="refresh">
            Try again
          </Button>
        </div>
      </div>

      <div
        v-else-if="assignments.length === 0"
        class="p-10 text-center"
        data-testid="dashboard-empty"
      >
        <p class="m-0 text-sm text-text-muted">No assigned exams yet.</p>
      </div>

      <table v-else class="w-full border-collapse text-sm text-text">
        <caption class="sr-only">
          Your assigned exams
        </caption>
        <thead class="bg-elevated">
          <tr>
            <th
              scope="col"
              class="border-b border-border px-4 py-2 text-left font-semibold text-text-muted"
            >
              Exam
            </th>
            <th
              scope="col"
              class="border-b border-border px-4 py-2 text-left font-semibold text-text-muted"
            >
              Status
            </th>
            <th
              scope="col"
              class="border-b border-border px-4 py-2 text-left font-semibold text-text-muted"
            >
              Created
            </th>
            <th
              scope="col"
              class="border-b border-border px-4 py-2 text-right font-semibold text-text-muted"
            >
              Action
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="assignment in assignments"
            :key="assignment.id"
            class="border-b border-border last:border-b-0"
            data-testid="dashboard-row"
          >
            <td class="px-4 py-3 font-medium text-text">{{ assignment.preset }}</td>
            <td class="px-4 py-3">
              <Badge :variant="statusVariant(assignment.status)">
                {{ statusLabel(assignment.status) }}
              </Badge>
            </td>
            <td class="px-4 py-3 text-text-muted">{{ formatDate(assignment.created_at) }}</td>
            <td class="px-4 py-3 text-right">
              <Button
                v-if="isStartable(assignment.status)"
                :variant="
                  normalizeStatus(assignment.status) === 'started' ? 'secondary' : 'primary'
                "
                size="sm"
                :data-testid="`dashboard-start-${assignment.id}`"
                @click="start(assignment)"
              >
                {{ actionLabel(assignment.status) }}
              </Button>
              <span v-else class="text-xs text-text-muted" data-testid="dashboard-unavailable">
                Link expired
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </Card>

    <PresetBuilder v-if="!session.isActive" />
  </main>
</template>
