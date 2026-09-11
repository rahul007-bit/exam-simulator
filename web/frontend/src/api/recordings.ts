import { apiRequest, getApiBaseUrl } from './client'

/**
 * Recordings API (FE-029).
 *
 * Typed wrappers around the candidate session-recording routes served by
 * `web/server.py` (`core/recorder.py` is the source of truth for the shapes):
 *
 *   GET /api/recordings                 -> { recordings, total }
 *   GET /api/recordings/{id}            -> metadata + events + task_timeline + channels
 *   GET /api/recordings/{id}/cast       -> asciinema v2 `.cast` (text, `?channel=`)
 *   GET /api/recordings/{id}/events     -> { session_id, events, total }
 *
 * The list/detail payloads come from `*.meta.json` files and are intentionally
 * loose (older recordings may miss fields), so every optional key is typed as
 * possibly `null`/absent and consumers default with `??`.
 */

/** One row of `GET /api/recordings` (a `*.meta.json` plus derived stats). */
export interface RecordingSummary {
  session_id: string
  name?: string | null
  preset?: string | null
  status?: string | null
  started_at?: string | null
  ended_at?: string | null
  start_timestamp?: number | null
  duration_seconds?: number | null
  duration_formatted?: string | null
  percentage?: number | null
  passed?: boolean | null
  total_earned?: number | null
  total_possible?: number | null
  has_cast?: boolean
  cast_size_bytes?: number
  cast_size_human?: string
  has_events?: boolean
  events_count?: number
}

export interface RecordingListResponse {
  recordings: RecordingSummary[]
  total: number
}

/**
 * One per-channel cast entry from `GET /api/recordings/{id}`.
 *
 * Channels are `user-web`, `admin-web` and `user-desktop`; a channel that was
 * never attached (or has no cast on disk) reports `has_cast: false`.
 */
export interface RecordingChannel {
  id: string
  has_cast: boolean
  cast_size_bytes: number
}

/** A single structured event from `*.events.jsonl` (`recorder.log_event`). */
export interface RecordingEvent {
  timestamp?: string
  rel_time?: number
  rel_time_formatted?: string
  event: string
  actor?: string
  session_id?: string
  /** Terminal channel the event originated from (older events omit it). */
  channel?: string
  data?: Record<string, unknown>
}

/** Per-task event distilled by `recorder._build_task_timeline`. */
export interface TaskTimelineEvent {
  event: string
  rel_time: number
  formatted_time?: string
  score?: number | null
  max_score?: number | null
  passed?: boolean | null
  message?: string | null
}

/** A task navigation interval from `recorder._build_task_timeline`. */
export interface TaskTimelineEntry {
  question_id: string
  task_num?: number
  title?: string
  domain?: string
  context?: string
  points?: number
  first_seen_time?: number
  last_seen_time?: number
  visits?: number
  is_flagged?: boolean
  score?: number | null
  max_score?: number | null
  passed?: boolean | null
  message?: string | null
  events?: TaskTimelineEvent[]
}

/** `GET /api/recordings/{id}` — metadata enriched with the event log. */
export interface RecordingDetail extends RecordingSummary {
  events: RecordingEvent[]
  events_count: number
  task_timeline: TaskTimelineEntry[]
  has_cast: boolean
  cast_size_bytes: number
  channels?: RecordingChannel[]
  scorecard?: unknown
}

export interface RecordingEventsResponse {
  session_id: string
  events: RecordingEvent[]
  total: number
}

/** List all recordings, newest first. */
export function listRecordings(signal?: AbortSignal): Promise<RecordingListResponse> {
  return apiRequest<RecordingListResponse>('/api/recordings', { signal })
}

/** Full metadata + event log + task timeline for one session. */
export function getRecording(sessionId: string, signal?: AbortSignal): Promise<RecordingDetail> {
  return apiRequest<RecordingDetail>(`/api/recordings/${encodeURIComponent(sessionId)}`, {
    signal,
  })
}

/** Raw asciinema v2 `.cast` text for one session/channel (default `user-web`). */
export function getRecordingCast(
  sessionId: string,
  channel?: string,
  signal?: AbortSignal,
): Promise<string> {
  return apiRequest<string>(`/api/recordings/${encodeURIComponent(sessionId)}/cast`, {
    query: channel ? { channel } : undefined,
    signal,
  })
}

/** Just the structured event log for one session. */
export function getRecordingEvents(
  sessionId: string,
  signal?: AbortSignal,
): Promise<RecordingEventsResponse> {
  return apiRequest<RecordingEventsResponse>(
    `/api/recordings/${encodeURIComponent(sessionId)}/events`,
    { signal },
  )
}

/**
 * Direct download URL for the `.cast` file (used by `<a download>` links).
 * Built from the shared client base so it honours `VITE_API_BASE`.
 */
export function recordingCastUrl(sessionId: string, channel?: string): string {
  const base = `${getApiBaseUrl()}/api/recordings/${encodeURIComponent(sessionId)}/cast`
  return channel ? `${base}?channel=${encodeURIComponent(channel)}` : base
}

/** Direct download URL for the exported events JSON. */
export function recordingEventsUrl(sessionId: string): string {
  return `${getApiBaseUrl()}/api/recordings/${encodeURIComponent(sessionId)}/events`
}
