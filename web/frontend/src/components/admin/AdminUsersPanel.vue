<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { createUser, deleteUser, listUsers } from '@/api/users'
import type { User } from '@/api/users'
import { Badge, Button, Card, Input, Select } from '@/components/ui'
import type { SelectOption } from '@/components/ui'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

/**
 * AdminUsersPanel — user management (FS-001 UI).
 *
 * Lists users and creates new ones (role `user` or `admin`); deletion is
 * confirmed and blocked for the current account and for the last admin.
 */

const auth = useAuthStore()
const { confirm } = useConfirm()
const { push } = useToast()

const users = ref<User[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const creating = ref(false)
const deleting = ref<string | null>(null)

const username = ref('')
const password = ref('')
const role = ref('user')

const roleOptions: SelectOption[] = [
  { value: 'user', label: 'User' },
  { value: 'admin', label: 'Admin' },
]

const adminCount = computed(() => users.value.filter((u) => u.role === 'admin').length)

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

function deleteBlockedReason(user: User): string | null {
  if (user.username === auth.username) return 'This is your own account.'
  if (user.role === 'admin' && adminCount.value <= 1) return 'The last admin cannot be deleted.'
  return null
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const response = await listUsers()
    users.value = response.users
  } catch (cause) {
    error.value = describeError(cause)
  } finally {
    loading.value = false
  }
}

async function onCreate(): Promise<void> {
  const name = username.value.trim()
  if (!name) {
    push({ variant: 'warning', message: 'Enter a username.' })
    return
  }
  if (!password.value) {
    push({ variant: 'warning', message: 'Enter a password.' })
    return
  }
  creating.value = true
  try {
    const response = await createUser(name, password.value, role.value)
    users.value = [...users.value, response.user].sort((a, b) =>
      a.username.localeCompare(b.username),
    )
    username.value = ''
    password.value = ''
    role.value = 'user'
    push({ variant: 'success', message: `User "${response.user.username}" created` })
  } catch (cause) {
    push({ variant: 'error', title: 'Could not create user', message: describeError(cause) })
  } finally {
    creating.value = false
  }
}

async function onDelete(user: User): Promise<void> {
  const reason = deleteBlockedReason(user)
  if (reason) {
    push({ variant: 'warning', message: reason })
    return
  }
  const approved = await confirm({
    title: 'Delete user?',
    message: `Permanently remove "${user.username}"? Their assignments and sessions are unaffected.`,
    confirmLabel: 'Delete user',
    danger: true,
  })
  if (!approved) return

  deleting.value = user.username
  try {
    await deleteUser(user.username)
    users.value = users.value.filter((u) => u.username !== user.username)
    push({ variant: 'success', message: `Deleted "${user.username}"` })
  } catch (cause) {
    push({ variant: 'error', title: 'Could not delete user', message: describeError(cause) })
  } finally {
    deleting.value = null
  }
}

function formatDate(value: string): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

onMounted(() => {
  void load()
})
</script>

<template>
  <Card
    title="Users"
    subtitle="Create accounts and manage roles. The last admin cannot be deleted."
  >
    <form class="flex flex-wrap items-end gap-3" novalidate @submit.prevent="onCreate">
      <div class="min-w-[12rem] flex-1">
        <Input
          v-model="username"
          label="Username"
          name="new-username"
          autocomplete="off"
          :disabled="creating"
          data-testid="users-username"
        />
      </div>
      <div class="min-w-[12rem] flex-1">
        <Input
          v-model="password"
          label="Password"
          type="password"
          name="new-password"
          autocomplete="new-password"
          :disabled="creating"
          data-testid="users-password"
        />
      </div>
      <div class="w-40">
        <Select
          :model-value="role"
          :options="roleOptions"
          label="Role"
          :disabled="creating"
          data-testid="users-role"
          @update:model-value="role = $event"
        />
      </div>
      <Button
        type="submit"
        variant="primary"
        :loading="creating"
        :disabled="creating"
        data-testid="users-add"
      >
        Add user
      </Button>
    </form>

    <div v-if="loading" class="py-8 text-center text-sm text-text-muted" data-testid="users-loading">
      Loading users…
    </div>

    <p v-else-if="error" role="alert" class="mt-4 text-sm text-danger-text" data-testid="users-error">
      {{ error }}
    </p>

    <p v-else-if="users.length === 0" class="mt-6 text-sm text-text-muted" data-testid="users-empty">
      No users yet.
    </p>

    <table v-else class="mt-4 w-full border-collapse text-sm text-text">
      <caption class="sr-only">
        Users
      </caption>
      <thead class="bg-elevated">
        <tr>
          <th scope="col" class="border-b border-border px-4 py-2 text-left font-semibold text-text-muted">
            Username
          </th>
          <th scope="col" class="border-b border-border px-4 py-2 text-left font-semibold text-text-muted">
            Role
          </th>
          <th scope="col" class="border-b border-border px-4 py-2 text-left font-semibold text-text-muted">
            Created
          </th>
          <th scope="col" class="border-b border-border px-4 py-2 text-right font-semibold text-text-muted">
            Action
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="user in users"
          :key="user.username"
          class="border-b border-border last:border-b-0"
          data-testid="users-row"
        >
          <td class="px-4 py-3 font-medium text-text">{{ user.username }}</td>
          <td class="px-4 py-3">
            <Badge :variant="user.role === 'admin' ? 'accent' : 'neutral'">{{ user.role }}</Badge>
          </td>
          <td class="px-4 py-3 text-text-muted">{{ formatDate(user.created_at) }}</td>
          <td class="px-4 py-3 text-right">
            <Button
              variant="danger"
              size="sm"
              :loading="deleting === user.username"
              :disabled="deleting !== null || deleteBlockedReason(user) !== null"
              :title="deleteBlockedReason(user) ?? undefined"
              :data-testid="`users-delete-${user.username}`"
              @click="onDelete(user)"
            >
              Delete
            </Button>
          </td>
        </tr>
      </tbody>
    </table>
  </Card>
</template>
