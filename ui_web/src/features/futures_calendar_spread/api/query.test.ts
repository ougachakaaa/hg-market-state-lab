import { afterEach, expect, it, vi } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { loadQuery } from './query'
import { errorMessage } from '../model/format'
import type { Query } from './validateResult'
import legacy from '../testing/daily.json'
import { referenceStates, withReference } from '../testing/reference'
const fixture = withReference(legacy)
const query: Query = { product_code: 'IM', trade_date: '2024-10-18' }
const unauthorized = vi.fn()
let dispose: (() => void) | undefined
function boundary() { const b = createRequestBoundary(unauthorized); dispose = installRequestBoundary(b); return b }
afterEach(() => { dispose?.(); vi.unstubAllGlobals(); vi.clearAllMocks() })
it('uses the correct gateway, same-origin credentials and a validated response', async () => {
  boundary(); const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(fixture)))
  vi.stubGlobal('fetch', fetch)
  expect(await loadQuery(query, new AbortController().signal)).toEqual(fixture)
  expect(fetch.mock.calls[0][0]).toBe('/api/data/futures-calendar-spread/query')
  expect(fetch.mock.calls[0][1].credentials).toBe('same-origin')
  expect(fetch.mock.calls[0][1].method).toBe('POST')
  expect(fetch.mock.calls[0][1].headers['Content-Type']).toBe('application/json')
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual(query)
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

it.each([
  [409, 'incomplete_inputs', 'cache_incomplete', '所需数据仍不完整'],
  [409, 'incomplete_inputs', 'final_export_incomplete', '已尝试自动准备'],
  [503, 'upstream_unavailable', 'credential_missing', '配置数据源凭据'],
  [503, 'upstream_unavailable', 'cache_incompatible', '维护人员处理缓存'],
  [503, 'upstream_unavailable', 'operation_unavailable', '稍后重试或联系维护人员'],
  [502, 'input_contract_error', 'malformed_export', '契约问题'],
  [502, 'input_contract_error', 'malformed_ensure_result', '契约问题'],
  [502, 'input_contract_error', 'upstream_request_rejected', '契约问题'],
] as const)('projects safe reason-specific feedback: %s %s %s', async (status, kind, reason_code, message) => {
  boundary()
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { kind, reason_code, detail: '/private secret', param: null } }), { status }))
  vi.stubGlobal('fetch', fetch)
  const error = await loadQuery(query, new AbortController().signal).catch(e => e)
  expect(error).toMatchObject({ kind, reason_code })
  expect(errorMessage(error)).toContain(message)
  expect(errorMessage(error)).not.toContain('secret')
  expect(fetch).toHaveBeenCalledOnce()
})
it.each([
  ['upstream_unavailable', 'malformed_export'],
  ['input_contract_error', 'unknown'],
  ['invalid_request', 'credential_missing'],
])('rejects an invalid reason contract %s %s', async (kind, reason_code) => {
  boundary()
  const status = kind === 'upstream_unavailable' ? 503 : kind === 'input_contract_error' ? 502 : 400
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { kind, reason_code, detail: 'safe', param: null } }), { status })))
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ kind: 'invalid_response' })
})
it('retains safe legacy feedback without requiring manual data preparation', () => {
  expect(errorMessage({ kind: 'incomplete_inputs' })).toContain('所需数据仍不完整')
  expect(errorMessage({ kind: 'incomplete_inputs' })).not.toContain('请先')
  expect(errorMessage({ kind: 'transport_busy' })).toContain('手动重试')
})

it('rejects a legacy omission specifically at the Online boundary', async () => {
  boundary(); const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(legacy))); vi.stubGlobal('fetch', fetch)
  await expect(loadQuery(query, new AbortController().signal)).rejects.toMatchObject({ kind: 'invalid_response' })
  expect(fetch).toHaveBeenCalledOnce()
})
it.each(referenceStates)('consumes the complete Online reference %s/%s/%s with unchanged pairs', async (...state) => {
  boundary()
  const payload = withReference(legacy, state)
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload)))
  vi.stubGlobal('fetch', fetch)
  const result = await loadQuery(query, new AbortController().signal)
  expect(result).toEqual(payload)
  expect(result.day).toEqual(legacy.day)
  expect(result.accounting).toEqual(legacy.accounting)
  expect(fetch).toHaveBeenCalledOnce()
})
