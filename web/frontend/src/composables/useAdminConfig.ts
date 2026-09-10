import { computed, ref } from 'vue'

import {
  getAdminConfig,
  getAdminResources,
  setAdminConfig,
  setAdminResources,
} from '@/api/admin'
import type { AdminSetConfigResponse, ResourceInfo } from '@/api/admin'
import { getPresets } from '@/api/presets'
import type { Preset } from '@/api/presets'
import type { SelectOption } from '@/components/ui'

/**
 * useAdminConfig (FE-032) — data + mutation layer for the admin configuration
 * and resource forms.
 *
 * Endpoints (already typed in `@/api/admin`):
 *   GET  /api/admin/config     -> { default_preset }
 *   POST /api/admin/config     -> { status, default_preset }
 *   GET  /api/admin/resources  -> ResourceInfo
 *   POST /api/admin/resources  -> ResourceInfo (validates >= 1 server-side)
 *
 * The preset catalogue comes from `/api/presets`. Following the legacy admin
 * surface, a synthetic "Full Curriculum" option (`all`) is appended so a
 * persisted default of `all` round-trips through the selector.
 *
 * Reads never throw to the caller when used via `loadAll` (the view catches and
 * toasts); mutations rethrow so the caller can surface the message while the
 * composable also records it in `error`.
 */

/** Synthetic option value that launches the full, untimed curriculum. */
export const FULL_CURRICULUM = 'all'

/** Human label for a preset option, mirroring the legacy admin select. */
export function presetLabel(preset: Preset): string {
  const tasks = preset.task_count ?? 0
  const minutes = preset.time_limit_minutes
  const suffix = minutes ? `, ${minutes}m` : ''
  return `${preset.name} (${tasks} tasks${suffix})`
}

/** Client-side validation for the max concurrent sessions field. */
export function validateMaxSessions(value: number): string | null {
  if (!Number.isFinite(value) || !Number.isInteger(value)) {
    return 'Enter a whole number of sessions (1 or more).'
  }
  if (value < 1) return 'Max concurrent sessions must be at least 1.'
  return null
}

/** 512 -> "512 MB", 2048 -> "2.0 GB". */
export function formatMemMb(mb: number): string {
  if (!Number.isFinite(mb) || mb <= 0) return '0 MB'
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${Math.round(mb)} MB`
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

export function useAdminConfig() {
  const presets = ref<Preset[]>([])
  const defaultPreset = ref('')
  const resources = ref<ResourceInfo | null>(null)

  const loading = ref(false)
  const savingPreset = ref(false)
  const savingResources = ref(false)
  const error = ref<string | null>(null)

  /** Preset options for the `Select`, plus the synthetic full-curriculum entry. */
  const presetOptions = computed<SelectOption[]>(() => {
    const options: SelectOption[] = presets.value.map((preset) => ({
      value: preset.filename,
      label: presetLabel(preset),
    }))
    options.push({
      value: FULL_CURRICULUM,
      label: 'Full Curriculum (All 111 Tasks, Untimed)',
    })
    return options
  })

  /** Friendly name for a preset filename, or `null` when it is the `all` entry. */
  function presetName(filename: string): string | null {
    return presets.value.find((preset) => preset.filename === filename)?.name ?? null
  }

  async function fetchPresets(): Promise<void> {
    const response = await getPresets()
    presets.value = response.presets
  }

  async function fetchConfig(): Promise<void> {
    const response = await getAdminConfig()
    defaultPreset.value = response.default_preset
  }

  async function fetchResources(): Promise<void> {
    resources.value = await getAdminResources()
  }

  /** Load the preset catalogue, the persisted default and the resource snapshot. */
  async function loadAll(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const [presetsResponse, config, resourceInfo] = await Promise.all([
        getPresets(),
        getAdminConfig(),
        getAdminResources(),
      ])
      presets.value = presetsResponse.presets
      defaultPreset.value = config.default_preset
      resources.value = resourceInfo
    } catch (cause) {
      error.value = errorMessage(cause)
      throw cause
    } finally {
      loading.value = false
    }
  }

  /** Persist the default preset and update local state on success. */
  async function saveDefaultPreset(preset: string): Promise<AdminSetConfigResponse> {
    savingPreset.value = true
    error.value = null
    try {
      const response = await setAdminConfig(preset)
      defaultPreset.value = response.default_preset
      return response
    } catch (cause) {
      error.value = errorMessage(cause)
      throw cause
    } finally {
      savingPreset.value = false
    }
  }

  /** Persist the max concurrent sessions limit after client-side validation. */
  async function saveMaxSessions(limit: number): Promise<ResourceInfo> {
    const invalid = validateMaxSessions(limit)
    if (invalid) throw new Error(invalid)

    savingResources.value = true
    error.value = null
    try {
      const info = await setAdminResources(limit)
      resources.value = info
      return info
    } catch (cause) {
      error.value = errorMessage(cause)
      throw cause
    } finally {
      savingResources.value = false
    }
  }

  return {
    presets,
    presetOptions,
    defaultPreset,
    resources,
    loading,
    savingPreset,
    savingResources,
    error,
    presetName,
    fetchPresets,
    fetchConfig,
    fetchResources,
    loadAll,
    saveDefaultPreset,
    saveMaxSessions,
  }
}
