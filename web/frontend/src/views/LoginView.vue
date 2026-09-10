<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { Button, Card, Input } from '@/components/ui'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { push } = useToast()

const password = ref('')
const formError = ref<string | null>(null)

/** Only allow same-origin paths (never protocol-relative URLs) as the destination. */
const redirectTarget = computed(() => {
  const value = route.query.redirect
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')
    ? value
    : '/admin'
})

async function onSubmit(): Promise<void> {
  formError.value = null
  if (password.value.length === 0) {
    formError.value = 'Enter the admin password.'
    return
  }

  const ok = await auth.login(password.value)
  if (!ok) {
    const detail = auth.error ?? 'Invalid admin password'
    formError.value = detail
    push({ variant: 'error', title: 'Sign-in failed', message: detail })
    return
  }

  password.value = ''
  push({ variant: 'success', message: 'Signed in as administrator' })
  await router.replace(redirectTarget.value)
}
</script>

<template>
  <main class="flex min-h-[calc(100vh_-_var(--header-height))] items-center justify-center p-4">
    <Card
      title="Admin sign-in"
      subtitle="Enter the administrator password to manage exam sessions."
      class="w-full max-w-sm"
      padding="lg"
    >
      <form class="flex flex-col gap-4" novalidate @submit.prevent="onSubmit">
        <Input
          v-model="password"
          label="Admin password"
          type="password"
          name="password"
          autocomplete="current-password"
          required
          :error="formError ?? undefined"
          :disabled="auth.loading"
        />
        <Button type="submit" variant="primary" block :loading="auth.loading">Sign in</Button>
      </form>
    </Card>
  </main>
</template>
