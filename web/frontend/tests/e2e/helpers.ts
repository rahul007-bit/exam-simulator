import type { Page } from '@playwright/test'

/**
 * FE-042 — shared, dependency-free backend mocking for the E2E journey specs.
 *
 * The CI/host browser leg runs without a FastAPI backend, so every journey must
 * be deterministic and offline. `mockCandidateBackend` / `mockAdminBackend`
 * install an API route that serves fixed JSON fixtures, plus stubs for the
 * browser surfaces the app assumes exist (WebSocket, fullscreen, noVNC).
 */

/** Minimal request shape exposed to dynamic fixture factories. */
export interface ApiRequestInfo {
  /** Parsed JSON request body (Playwright `Request.postDataJSON`). */
  postDataJSON: () => unknown
}

export interface ApiStub {
  /** Exact pathname (e.g. `/api/presets`) or a RegExp for dynamic paths. */
  path: string | RegExp
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  /** Static body, or a factory (sync/async) evaluated per request. */
  body: unknown | ((request: ApiRequestInfo) => unknown)
  status?: number
}

export const PRESET = {
  filename: 'mock-01',
  name: 'Mock Preset',
  description: 'Deterministic fixture preset.',
  time_limit_minutes: 60,
  pass_threshold_percent: 66,
  task_count: 2,
}

export const INACTIVE_SESSION = {
  active: false,
  session: null,
  locked_preset: {
    filename: PRESET.filename,
    name: PRESET.name,
    description: PRESET.description,
    task_count: PRESET.task_count,
    time_limit_minutes: PRESET.time_limit_minutes,
    pass_threshold_percent: PRESET.pass_threshold_percent,
  },
  is_admin: false,
}

const TASK_ONE = {
  task_num: 1,
  id: 'q1',
  title: 'Task One',
  domain: 'Core',
  difficulty: 'easy',
  points: 1,
  target_context: 'kind-cluster',
  namespace: 'default',
  description: 'Create the first resource.',
  cluster_scoped: false,
  tags: ['mock'],
  is_flagged: false,
}

const TASK_TWO = {
  task_num: 2,
  id: 'q2',
  title: 'Task Two',
  domain: 'Workloads',
  difficulty: 'medium',
  points: 1,
  target_context: 'kind-cluster',
  namespace: 'workloads',
  description: 'Create the second resource.',
  cluster_scoped: false,
  tags: ['mock'],
  is_flagged: false,
}

/** Build an active `SessionActive` payload centred on the given task index. */
export function activeSession(index: number) {
  return {
    active: true,
    session_id: 'sess-mock-1',
    candidate_token: null,
    name: PRESET.name,
    mode: 'practice',
    status: 'active',
    current_index: index,
    total_tasks: 2,
    time_limit_minutes: 60,
    time_remaining_seconds: 3600,
    created_at: '2026-01-01T00:00:00.000Z',
    start_timestamp: null,
    end_timestamp: null,
    server_timestamp: Date.now(),
    flagged_ids: [],
    current_task: index === 0 ? TASK_ONE : TASK_TWO,
    terminal_port: '7681',
    novnc_port: '6080',
    is_admin: false,
  }
}

/** Navigator rows reflecting whichever task is currently open. */
function questionsFor(index: number) {
  return {
    questions: [
      {
        task_num: 1,
        id: 'q1',
        title: 'Task One',
        points: 1,
        is_current: index === 0,
        is_flagged: false,
      },
      {
        task_num: 2,
        id: 'q2',
        title: 'Task Two',
        points: 1,
        is_current: index === 1,
        is_flagged: false,
      },
    ],
    total: 2,
  }
}

const SUBMIT_REPORT = {
  scorecard: [
    {
      task_num: 1,
      id: 'q1',
      title: 'Task One',
      domain: 'Core',
      difficulty: 'easy',
      context: 'kind-cluster',
      score: 1,
      max_score: 1,
      passed: true,
      message: 'Passed',
    },
  ],
  total_earned: 1,
  total_possible: 2,
  percentage: 50,
  passed: false,
  threshold: 66,
  session_id: 'sess-mock-1',
  exam_name: PRESET.name,
  submitted_at: '2026-01-01T01:00:00.000Z',
  report_file: null,
}

export const ADMIN_SESSION = {
  session_id: 'sess-admin-1',
  candidate_token: null,
  name: 'Mock Exam',
  status: 'active',
  created_at: '2026-01-01T00:00:00.000Z',
  archived_at: null,
  time_remaining_seconds: 1800,
  container_running: true,
  total_tasks: 2,
  current_index: 0,
  type: 'active',
  url: null,
  scorecard_summary: null,
}

export const RESOURCES = {
  total_mem_mb: 16384,
  available_mem_mb: 8192,
  used_mem_mb: 8192,
  free_mem_mb: 8192,
  running_containers: 1,
  max_concurrent_sessions: 4,
  recommended_max: 8,
  can_start: true,
  reason: '',
}

const INFRASTRUCTURE = {
  nodes: [],
  resources: [],
  summary: {
    total_nodes: 0,
    total_docker_containers: 0,
    total_incus_instances: 0,
    total_resources: 0,
  },
}

/**
 * Matches real backend calls only. A bare `**\/api/**` glob would also match
 * Vite's own dev modules under `/src/api/*.ts`, serving them 404 JSON and
 * preventing the app from ever mounting.
 */
export const BACKEND_API_PATTERN = /^https?:\/\/[^/]+\/api\//

export async function mockApi(
  page: Page,
  stubs: ApiStub[],
  fallback: unknown = { detail: 'Not mocked in the FE-042 E2E suite' },
): Promise<void> {
  await page.route(BACKEND_API_PATTERN, async (route) => {
    const request = route.request()
    const { pathname } = new URL(request.url())
    const method = request.method()
    const stub = stubs.find((candidate) => {
      if (candidate.method && candidate.method !== method) return false
      return typeof candidate.path === 'string'
        ? candidate.path === pathname
        : candidate.path.test(pathname)
    })

    if (!stub) {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify(fallback),
      })
      return
    }

    const resolved =
      typeof stub.body === 'function'
        ? await (stub.body as (request: ApiRequestInfo) => unknown)(
            request as unknown as ApiRequestInfo,
          )
        : stub.body
    await route.fulfill({
      status: stub.status ?? 200,
      contentType: 'application/json',
      body: JSON.stringify(resolved),
    })
  })
}

/**
 * Replace the browser surfaces the app opens at runtime but cannot reach
 * offline: the session/terminal WebSockets, fullscreen entry and the noVNC
 * iframe bundle.
 */
export async function stubBrowserApis(page: Page): Promise<void> {
  await page.addInitScript(() => {
    class MockWebSocket {
      static readonly CONNECTING = 0
      static readonly OPEN = 1
      static readonly CLOSING = 2
      static readonly CLOSED = 3

      binaryType = 'blob'
      readyState = MockWebSocket.CONNECTING
      readonly url: string
      onopen: ((event: unknown) => void) | null = null
      onmessage: ((event: { data: unknown }) => void) | null = null
      onclose: ((event: unknown) => void) | null = null
      onerror: ((event: unknown) => void) | null = null

      constructor(url: string) {
        this.url = String(url)
        setTimeout(() => {
          this.readyState = MockWebSocket.OPEN
          this.onopen?.({ type: 'open' })
        }, 0)
      }

      send(): void {
        /* outbound frames are intentionally dropped offline */
      }

      close(): void {
        this.readyState = MockWebSocket.CLOSED
        this.onclose?.({ type: 'close', code: 1000, reason: '' })
      }

      addEventListener(): void {
        /* the app only uses the on* property handlers */
      }

      removeEventListener(): void {
        /* the app only uses the on* property handlers */
      }
    }

    ;(window as unknown as { WebSocket: unknown }).WebSocket = MockWebSocket

    /*
     * Simulate a *successful* fullscreen round-trip. The real FullscreenGuard
     * locks the candidate UI whenever the exam is active and the document is
     * not fullscreen; rejecting the request (as a headless browser does) would
     * raise the "EXAM LOCKED" overlay and intercept every subsequent click.
     */
    let fullscreenElement: Element | null = null
    Object.defineProperty(document, 'fullscreenElement', {
      configurable: true,
      get: () => fullscreenElement,
    })
    Element.prototype.requestFullscreen = function requestFullscreen() {
      fullscreenElement = document.documentElement
      document.dispatchEvent(new Event('fullscreenchange'))
      return Promise.resolve()
    }
    Document.prototype.exitFullscreen = function exitFullscreen() {
      fullscreenElement = null
      document.dispatchEvent(new Event('fullscreenchange'))
      return Promise.resolve()
    }
  })

  await page.route('**/novnc/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: '<!doctype html><html><head><title>noVNC (stubbed)</title></head><body></body></html>',
    }),
  )
}

/** Candidate critical-path fixtures: inactive session -> start -> navigate -> submit. */
export async function mockCandidateBackend(page: Page): Promise<void> {
  await stubBrowserApis(page)
  // Tracks the open task so next/prev/jump fixtures advance deterministically,
  // and so the navigator rows always mark the current task (mirrors the backend).
  let currentIndex = 0
  const clamp = (value: number): number => Math.max(0, Math.min(1, value))

  await mockApi(page, [
    { path: '/api/session', body: INACTIVE_SESSION },
    { path: '/api/timer', body: { active: false } },
    { path: '/api/presets', body: { presets: [PRESET], selected: PRESET.filename } },
    {
      path: '/api/start',
      method: 'POST',
      body: () => {
        currentIndex = 0
        return activeSession(currentIndex)
      },
    },
    { path: '/api/questions', body: () => questionsFor(currentIndex) },
    {
      path: '/api/action/jump',
      method: 'POST',
      body: (request: ApiRequestInfo) => {
        const parsed = request.postDataJSON() as { task_num?: number } | null
        if (typeof parsed?.task_num === 'number') currentIndex = clamp(parsed.task_num - 1)
        return activeSession(currentIndex)
      },
    },
    {
      path: '/api/action/next',
      method: 'POST',
      body: () => {
        currentIndex = clamp(currentIndex + 1)
        return activeSession(currentIndex)
      },
    },
    {
      path: '/api/action/prev',
      method: 'POST',
      body: () => {
        currentIndex = clamp(currentIndex - 1)
        return activeSession(currentIndex)
      },
    },
    {
      path: '/api/action/retry',
      method: 'POST',
      body: { status: 'ok', message: 'Task reset' },
    },
    { path: '/api/action/submit', method: 'POST', body: SUBMIT_REPORT },
  ])
}

/** Admin critical-path fixtures: authenticated admin with one live session. */
export async function mockAdminBackend(page: Page): Promise<void> {
  await stubBrowserApis(page)
  await mockApi(page, [
    { path: '/api/session', body: INACTIVE_SESSION },
    { path: '/api/timer', body: { active: false } },
    { path: '/api/presets', body: { presets: [PRESET], selected: PRESET.filename } },
    { path: '/api/admin/check', body: { authenticated: true } },
    { path: '/api/admin/sessions', body: { sessions: [ADMIN_SESSION], total: 1 } },
    { path: '/api/admin/config', body: { default_preset: PRESET.filename } },
    { path: '/api/admin/resources', body: RESOURCES },
    { path: '/api/admin/infrastructure', body: INFRASTRUCTURE },
    {
      path: /^\/api\/admin\/sessions\/[^/]+\/(terminate|reset|end)$/,
      method: 'POST',
      body: { status: 'ok', message: `Terminated ${ADMIN_SESSION.session_id}` },
    },
    {
      path: '/api/admin/sessions/create',
      method: 'POST',
      body: { token: 'invite-token-1', preset: PRESET.filename, url: '/?token=invite-token-1' },
    },
    {
      path: '/api/admin/config',
      method: 'POST',
      body: { status: 'ok', default_preset: PRESET.filename },
    },
    { path: '/api/admin/resources', method: 'POST', body: RESOURCES },
  ])
}
