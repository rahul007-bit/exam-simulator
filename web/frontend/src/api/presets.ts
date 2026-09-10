import type { components } from './schema'
import { apiRequest } from './client'

export type Preset = components['schemas']['Preset']
export type PresetsResponse = components['schemas']['PresetsResponse']
export type PresetSelectRequest = components['schemas']['PresetSelectRequest']
export type PresetSelectResponse = components['schemas']['PresetSelectResponse']

export function getPresets(): Promise<PresetsResponse> {
  return apiRequest<PresetsResponse>('/api/presets')
}

export function selectPreset(preset: string): Promise<PresetSelectResponse> {
  const body: PresetSelectRequest = { preset }
  return apiRequest<PresetSelectResponse>('/api/presets/select', { method: 'POST', body })
}
