import { afterEach, expect, it, vi } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { loadQuery } from './query'
import type { Query } from './validateResult'
import fixture from '../testing/daily.json'
const query: Query = { product_code: 'IM', trade_date: '2024-10-18' }
const unauthorized = vi.fn()
let dispose: (() => void) | undefined
function boundary() { const b = createRequestBoundary(unauthorized); dispose = installRequestBoundary(b); return b }
afterEach(() => { dispose?.(); vi.unstubAllGlobals(); vi.clearAllMocks() })
it('uses the correct gateway, same-origin credentials and a validated response', async () => {
  boundary(); const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(fixture)))
  vi.stubGlobal('fetch', fetch)
  expect(await loadQuery(query, new AbortController().signal)).toEqual(fixture)
  expect(fetch.mock.calls[0][0]).toBe('/api/data/futures-calendar-spread?product_code=IM&trade_date=2024-10-18')
  expect(fetch.mock.calls[0][1].credentials).toBe('same-origin')
  expect(fetch.mock.calls[0][1].method).toBeUndefined()
})
it.each([[400,'invalid_request'], [403,'origin_forbidden'], [409,'incomplete_inputs'], [413,'request_too_large'], [413,'response_too_large'], [422,'calculation_failure'], [422,'slot_resolution_error'], [502,'input_contract_error'], [503,'upstream_unavailable'], [503,'transport_busy'], [500,'internal_error']])('preserves HTTP %s / %s', async (status, kind) => {
  boundary(); vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { kind, detail: 'safe', param: null } }), { status: status as number })))
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ kind })
  expect(unauthorized).not.toHaveBeenCalled()
})
it('delegates 401 to authentication and isolates a closed lifecycle success', async () => {
  boundary(); vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 401 })))
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ name: 'AbortError' })
  expect(unauthorized).toHaveBeenCalledOnce()
  const b = boundary()
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async () => { b.close(); return new Response(JSON.stringify(fixture)) }))
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ name: 'AbortError' })
})
it('distinguishes network failure, malformed data and abort without retry', async () => {
  boundary(); const fetch = vi.fn().mockRejectedValue(new TypeError('offline')); vi.stubGlobal('fetch', fetch)
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ kind: 'network' })
  fetch.mockResolvedValue(new Response('{}'))
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ kind: 'invalid_response' })
  const controller = new AbortController(); controller.abort()
  await expect(loadQuery(query, controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
  expect(fetch).toHaveBeenCalledTimes(2)
})
