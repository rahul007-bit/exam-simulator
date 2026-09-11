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

const username = ref('')
const password = ref('')
const formError = ref<string | null>(null)

/** Only allow same-origin paths (never protocol-relative URLs) as the destination. */
const redirectTarget = computed(() => {
  const value = route.query.redirect
  if (typeof value === 'string' && value.startsWith('/') && !value.startsWith('//')) {
    return value
  }
  return auth.isAdmin ? '/admin' : '/assignments'
})

async function onSubmit(): Promise<void> {
  formError.value = null
  if (username.value.trim().length === 0) {
    formError.value = 'Enter your username.'
    return
  }
  if (password.value.length === 0) {
    formError.value = 'Enter your password.'
    return
  }

  const ok = await auth.login(username.value.trim(), password.value)
  if (!ok) {
    const detail = auth.error ?? 'Invalid username or password'
    formError.value = detail
    push({ variant: 'error', title: 'Sign-in failed', message: detail })
    return
  }

  password.value = ''
  push({ variant: 'success', message: 'Signed in' })
  await router.replace(redirectTarget.value)
}
</script>

<template>
  <main class="flex min-h-[calc(100vh_-_var(--header-height))] items-center justify-center p-4">
    <Card
      title="Sign in"
      subtitle="Enter your username and password to continue."
      class="w-full max-w-sm"
      padding="lg"
    >
      <form class="flex flex-col gap-4" novalidate @submit.prevent="onSubmit">
        <Input
          v-model="username"
          label="Username"
          type="text"
          name="username"
          autocomplete="username"
          required
          :disabled="auth.loading"
        />
        <Input
          v-model="password"
          label="Password"
          type="password"
          name="password"
          autocomplete="current-password"
          required
          :disabled="auth.loading"
        />
        <p v-if="formError" role="alert" class="text-xs text-danger-text">{{ formError }}</p>
        <Button type="submit" variant="primary" block :loading="auth.loading">Sign in</Button>
      </form>
    </Card>
  </main>
</template>
