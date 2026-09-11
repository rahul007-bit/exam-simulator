import { afterEach, describe, expect, it, vi } from 'vitest'

import { getRecordingCast, recordingCastUrl } from '@/api/recordings'

/**
 * FE-029 channel plumbing: the cast route is channelled with `?channel=`, with
 * `user-web` remaining the backend default when no channel is supplied.
 */

const fetchMock = vi.fn(() => Promise.resolve(new Response('[0, "o", "boot"]', { status: 200 })))

afterEach(() => {
  vi.unstubAllGlobals()
  fetchMock.mockClear()
})

describe('recordings API — channel parameter', () => {
  it('builds a plain cast URL without a channel', () => {
    expect(recordingCastUrl('sess-1')).toBe('/api/recordings/sess-1/cast')
  })

  it('appends the encoded channel to the cast URL', () => {
    expect(recordingCastUrl('sess-1', 'user-desktop')).toBe(
      '/api/recordings/sess-1/cast?channel=user-desktop',
    )
  })

  it('passes the channel through to the cast request', async () => {
    vi.stubGlobal('fetch', fetchMock)
    await getRecordingCast('sess-1', 'admin-web')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/recordings/sess-1/cast?channel=admin-web',
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('omits the query string when no channel is given', async () => {
    vi.stubGlobal('fetch', fetchMock)
    await getRecordingCast('sess-1')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/recordings/sess-1/cast',
      expect.objectContaining({ method: 'GET' }),
    )
  })
})
