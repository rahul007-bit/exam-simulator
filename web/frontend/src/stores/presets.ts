import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as presetsApi from '@/api/presets'
import type { Preset, PresetSelectResponse } from '@/api/presets'

export const usePresetsStore = defineStore('presets', () => {
  const presets = ref<Preset[]>([])
  const selected = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const selectedPreset = computed<Preset | null>(
    () => presets.value.find((preset) => preset.filename === selected.value) ?? null,
  )

  async function fetchPresets(): Promise<Preset[]> {
    loading.value = true
    error.value = null
    try {
      const response = await presetsApi.getPresets()
      presets.value = response.presets
      selected.value = response.selected
      return response.presets
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return []
    } finally {
      loading.value = false
    }
  }

  async function selectPreset(preset: string): Promise<PresetSelectResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await presetsApi.selectPreset(preset)
      selected.value = response.preset
      return response
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  return { presets, selected, loading, error, selectedPreset, fetchPresets, selectPreset }
})
