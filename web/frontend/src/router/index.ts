import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized, RouteRecordRaw } from 'vue-router'

import CandidateView from '@/views/CandidateView.vue'
import AdminView from '@/views/AdminView.vue'
import { useAuthStore } from '@/stores/auth'

/**
 * Route meta contract for auth + roles (FE-030).
 *
 * `requiresAuth` gates a route behind a valid admin session; `roles` further
 * restricts it to one of the listed roles. Roles are unused beyond `admin`
 * today but the guard is generalised so the FS-002 user/admin scope only has to
 * populate `meta.roles` on new routes.
 */
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
  }
}

// NOTE: /dashboard and /exam/:sessionId are placeholders reserved for the
// future auth + per-user assignment scope (see decisions.md D-009 / FS-* tasks).
const routes: RouteRecordRaw[] = [
  { path: '/', name: 'candidate', component: CandidateView },
  {
    path: '/admin',
    name: 'admin',
    component: AdminView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/PlaceholderView.vue'),
  },
  {
    path: '/exam/:sessionId',
    name: 'exam',
    component: () => import('@/views/PlaceholderView.vue'),
  },
]

// FE-012: dev-only primitives gallery. Excluded from production builds and from
// the candidate/admin flows.
if (import.meta.env.DEV) {
  routes.push({
    path: '/dev/ui',
    name: 'dev-ui',
    component: () => import('@/views/DevUiView.vue'),
  })
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * Auth guard. Unauthenticated access to `requiresAuth` routes resolves the
 * session once via `/api/admin/check`, then redirects to `/login` (preserving
 * the attempted path in `?redirect=`) so the user returns after signing in.
 */
export async function authGuard(
  to: RouteLocationNormalized,
): Promise<true | { name: string; query?: Record<string, string> }> {
  if (!to.meta.requiresAuth) return true

  const auth = useAuthStore()
  if (!auth.initialized) await auth.check()

  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const required = to.meta.roles
  if (required && required.length > 0 && !auth.hasAnyRole(required)) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  return true
}

router.beforeEach(authGuard)

export default router
