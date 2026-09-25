// Shared typed fetch wrapper for the FastAPI backend.
//
// The client is designed for the future auth scope (PLAN.md §8 / FS-002):
// every request is sent with `credentials: 'include'` so the admin cookie (and
// any future session cookie) travels with the request, and an optional bearer
// token can be attached when the backend issues one.

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export type QueryValue = string | number | boolean | null | undefined

export interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  query?: Record<string, QueryValue>
  signal?: AbortSignal
}

/**
 * Per-browser client id used by the backend session owner lock.
 *
 * A non-HttpOnly, path-scoped, 1-year `SameSite=Lax` cookie identifies this
 * browser across refreshes. It is ensured once on module load so every request
 * can advertise `X-Client-Id`; the backend 409s when a different client owns the
 * active session (see the session-lock contract).
 */
const CLIENT_ID_COOKIE = 'cka_client_id'
const CLIENT_ID_MAX_AGE = 31_536_000

function generateClientId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `cka-${Math.random().toString(16).slice(2)}${Date.now().toString(16)}`
}

function readClientIdCookie(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)cka_client_id=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

function ensureClientId(): string {
  const existing = readClientIdCookie()
  if (existing) return existing
  const generated = generateClientId()
  document.cookie = `${CLIENT_ID_COOKIE}=${encodeURIComponent(generated)}; path=/; max-age=${CLIENT_ID_MAX_AGE}; SameSite=Lax`
  return generated
}

const clientId = typeof document !== 'undefined' ? ensureClientId() : generateClientId()

export function getClientId(): string {
  return clientId
}

function initialBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE as string | undefined
  return configured ?? ''
}

let baseUrl = initialBaseUrl()
let adminToken: string | null = null

export function getApiBaseUrl(): string {
  return baseUrl
}

export function setApiBaseUrl(url: string): void {
  baseUrl = url
}

export function getAdminToken(): string | null {
  return adminToken
}

export function setAdminToken(token: string | null): void {
  adminToken = token
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = `${baseUrl}${path}`
  if (!query) return url

  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue
    params.set(key, String(value))
  }
  const qs = params.toString()
  return qs ? `${url}?${qs}` : url
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function errorMessage(payload: unknown, response: Response): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail: unknown }).detail
    if (typeof detail === 'string' && detail.length > 0) return detail
  }
  return response.statusText || `Request failed with status ${response.status}`
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (adminToken) headers.Authorization = `Bearer ${adminToken}`
  headers['X-Client-Id'] = getClientId()

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? 'GET',
    headers,
    credentials: 'include',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  })

  const payload = await parseBody(response)
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(payload, response))
  }
  return payload as T
}
