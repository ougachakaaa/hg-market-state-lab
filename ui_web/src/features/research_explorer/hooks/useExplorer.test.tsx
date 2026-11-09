import { vi } from 'vitest'
vi.mock('react-plotly.js', () => ({ default: () => null }))
import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { useExplorer } from './useExplorer'
let release: (() => void) | undefined
afterEach(() => { release?.(); vi.unstubAllGlobals() })
const response = (body: unknown) => ({ status: 200, ok: true, json: async () => body }) as Response
it('loads only list initially and aborts obsolete publication on selection changes', async () => {
  release = installRequestBoundary(createRequestBoundary(() => {}))
  const pending: { signal: AbortSignal; finish: (r: Response) => void }[] = []
  const fetch = vi.fn().mockImplementation((url: string, options: RequestInit) => url === '/api/research/publications' ? Promise.resolve(response({ data: [], next_cursor: null })) : new Promise<Response>(finish => pending.push({ signal: options.signal!, finish })))
  vi.stubGlobal('fetch', fetch)
  const { result, unmount } = renderHook(() => useExplorer())
  await waitFor(() => expect(result.current.list.status).toBe('success'))
  expect(fetch).toHaveBeenCalledTimes(1)
  act(() => result.current.selectPublication('first'))
  act(() => result.current.selectPublication('second'))
  expect(pending[0].signal.aborted).toBe(true)
  expect(result.current.manifest.status).toBe('loading')
  await act(async () => pending[0].finish(response({ data: {} })))
  expect(result.current.manifest.status).toBe('loading')
  unmount()
  expect(pending[1].signal.aborted).toBe(true)
})
