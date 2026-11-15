import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { useCatalog } from '../hooks/useCatalog'
import { useStaticCatalog } from '../static/useStaticCatalog'
import descriptor from '../api/catalog.fixture.json'

const reply = (body: unknown) => new Response(JSON.stringify(body))
let release: () => void
beforeEach(() => { release = installRequestBoundary(createRequestBoundary(vi.fn())) })
afterEach(() => { cleanup(); release(); vi.unstubAllGlobals() })

it('validates list and selects matching detail only on explicit selection', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(reply([descriptor])).mockResolvedValueOnce(reply(descriptor))
  vi.stubGlobal('fetch', fetch)
  const { result } = renderHook(useCatalog)
  await waitFor(() => expect(result.current.list.status).toBe('success'))
  expect(fetch).toHaveBeenCalledTimes(1)
  act(() => result.current.selectOnline(descriptor.id))
  await waitFor(() => expect(result.current.detail.status).toBe('success'))
  expect(fetch.mock.calls[1][0]).toBe(`/api/research/capabilities/${descriptor.id}`)
  expect(result.current.detail).toEqual({ status: 'success', data: descriptor })
})

it('retains independent manual list and detail retries', async () => {
  const fetch = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(reply([descriptor]))
    .mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(reply(descriptor))
  vi.stubGlobal('fetch', fetch)
  const { result } = renderHook(useCatalog)
  await waitFor(() => expect(result.current.list.status).toBe('error'))
  act(() => result.current.retryList?.())
  await waitFor(() => expect(result.current.list.status).toBe('success'))
  act(() => result.current.selectOnline(descriptor.id))
  await waitFor(() => expect(result.current.detail.status).toBe('error'))
  act(() => result.current.retryDetail?.())
  await waitFor(() => expect(result.current.detail.status).toBe('success'))
  expect(fetch).toHaveBeenCalledTimes(4)
})

it('rejects invalid descriptors independently of presentation', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([{ id: 'fabricated' }])))
  const { result } = renderHook(useCatalog)
  await waitFor(() => expect(result.current.list.status).toBe('error'))
})

it('aborts detail and ignores late success after local selection', async () => {
  let complete!: (value: Response) => void
  let signal: AbortSignal | undefined
  const pending = new Promise<Response>(resolve => { complete = resolve })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(reply([descriptor]))
    .mockImplementationOnce((_url, init) => { signal = init.signal; return pending }))
  const { result } = renderHook(useCatalog)
  await waitFor(() => expect(result.current.list.status).toBe('success'))
  act(() => result.current.selectOnline(descriptor.id))
  await waitFor(() => expect(signal).toBeDefined())
  act(() => result.current.selectLocal('price_segmentation_v1'))
  expect(signal?.aborted).toBe(true)
  await act(async () => { complete(reply(descriptor)) })
  expect(result.current.detail.status).toBe('idle')
})

it('validates static catalog and keeps missing detail honest without HTTP', () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  const { result } = renderHook(() => useStaticCatalog({ list: [descriptor], details: [] }))
  expect(result.current.list.status).toBe('success')
  act(() => result.current.selectOnline(descriptor.id))
  expect(result.current.detail).toEqual({ status: 'missing', id: descriptor.id })
  act(() => result.current.selectLocal('price_segmentation_v1'))
  expect(result.current.detail.status).toBe('idle')
  expect(fetch).not.toHaveBeenCalled()
})

it('rejects invalid static results before presentation', () => {
  const { result } = renderHook(() => useStaticCatalog({ list: [{ id: 'fabricated' }], details: [] }))
  expect(result.current.list.status).toBe('invalid')
})
