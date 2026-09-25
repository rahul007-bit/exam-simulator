import type { components } from './schema'
import { apiRequest } from './client'
import type { SessionResponse } from './session'

export type Preset = components['schemas']['Preset']
export type PresetsResponse = components['schemas']['PresetsResponse']
export type PresetSelectRequest = components['schemas']['PresetSelectRequest']
export type PresetSelectResponse = components['schemas']['PresetSelectResponse']

/** Difficulty tiers accepted by `POST /api/presets/generate` (FS-006). */
export type GenerateDifficulty = 'easy' | 'medium' | 'hard' | 'crazy'

/** Knowledge domains accepted by `POST /api/presets/generate` (FS-006). */
export type GenerateDomain =
  | 'troubleshooting'
  | 'storage'
  | 'workloads'
  | 'cluster-arch'
  | 'security'

/**
 * Body for `POST /api/presets/generate` (FS-006).
 *
 * Hand-written rather than derived from `schema.d.ts` because the OpenAPI
 * snapshot is refreshed for this endpoint by a separate owner; the request shape
 * is authoritative in `web/api/schemas.py::GeneratePresetRequest`.
 */
export interface GeneratePresetRequest {
  count: number
  difficulty?: GenerateDifficulty
  domains?: GenerateDomain[]
}

/**
 * `POST /api/presets/generate` starts an ephemeral exam and responds with the
 * same active-session payload as `POST /api/start`.
 */
export type GeneratePresetResponse = SessionResponse

export function generatePreset(body: GeneratePresetRequest): Promise<GeneratePresetResponse> {
  return apiRequest<GeneratePresetResponse>('/api/presets/generate', { method: 'POST', body })
}

export function getPresets(): Promise<PresetsResponse> {
  return apiRequest<PresetsResponse>('/api/presets')
}

export function selectPreset(preset: string): Promise<PresetSelectResponse> {
  const body: PresetSelectRequest = { preset }
  return apiRequest<PresetSelectResponse>('/api/presets/select', { method: 'POST', body })
}
