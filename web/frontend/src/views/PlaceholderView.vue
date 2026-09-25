<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <main>
    <h1>Reserved Route</h1>
    <p>
      <code>{{ route.path }}</code> is reserved for future scope (auth, per-user exam assignment,
      dynamic preset generator).
    </p>
  </main>
</template>
