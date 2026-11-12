import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { checkInputs, getResult, getRun, products, submitRun } from './backtesting'
const id = 'a'.repeat(32)
const request = { product_code: 'IM' as const, start_date: '2024-10-18', end_date: '2024-10-21', strategy_profile: 'expiry_to_M1_v1' as const }
const immutable = { ...request, case: 'futures_roll_long_v1' }
const accepted = { run_id: id, request: immutable, status: 'PENDING', created_at: '2026-11-09T00:00:00Z' }
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
let release: () => void
const unauthorized = vi.fn()
beforeEach(() => { unauthorized.mockClear(); release = installRequestBoundary(createRequestBoundary(unauthorized)) })
afterEach(() => { release(); vi.unstubAllGlobals() })
const signal = () => new AbortController().signal

describe('Backtesting HTTP adapter', () => {
  it('uses generated products and protected same-origin JSON POST', async () => {
    expect(products).toEqual(['IM', 'IC', 'IF', 'IH'])
    const fetch = vi.fn().mockResolvedValue(response(accepted, 202)); vi.stubGlobal('fetch', fetch)
    expect(await submitRun(request, signal())).toEqual(accepted)
    expect(fetch.mock.calls[0][0]).toBe('/api/backtesting/futures-roll/runs')
    expect(fetch.mock.calls[0][1]).toMatchObject({ method: 'POST', credentials: 'same-origin', body: JSON.stringify(request) })
  })
  it.each([[409, 'run_busy'], [400, 'invalid_request'], [503, 'unavailable'], [403, 'origin_forbidden']])('classifies POST %s %s', async (status, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind, detail: 'safe', param: null } }, status as number)))
    await expect(submitRun(request, signal())).rejects.toMatchObject({ kind })
  })
  it('rejects error classification at the wrong status and invalid envelopes', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response({ error: { kind: 'run_busy', detail: 'safe', param: null } }, 503)).mockResolvedValueOnce(response({ ...accepted, request: { ...immutable, product_code: 'IC' } }, 202)).mockResolvedValueOnce(response({ run_id: id }))
    vi.stubGlobal('fetch', fetch)
    await expect(submitRun(request, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(submitRun(request, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(getRun(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
  })
  it('validates run identity, state coherence and report profile', async () => {
    const run = { ...accepted, started_at: null, finished_at: null, result_available: false, failure: null }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(run)).mockResolvedValueOnce(response({ ...run, run_id: 'b'.repeat(32) })).mockResolvedValueOnce(response({ ...run, result_available: true })).mockResolvedValueOnce(response({ run_id: id, request: immutable, result_status: 'complete', data: { profile: 'wrong' } })))
    expect(await getRun(id, signal())).toEqual(run)
    await expect(getRun(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(getRun(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(getResult(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
  })
  it('closes the application gate on 401 and never retries a lost POST', async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new TypeError('lost')).mockResolvedValueOnce(response({ error: { kind: 'authentication_required', detail: 'safe' } }, 401)); vi.stubGlobal('fetch', fetch)
    await expect(submitRun(request, signal())).rejects.toMatchObject({ kind: 'network' })
    expect(fetch).toHaveBeenCalledTimes(1)
    await expect(getRun(id, signal())).rejects.toMatchObject({ name: 'AbortError' })
    expect(unauthorized).toHaveBeenCalledOnce()
  })
})

it('validates full producer Result and rejects association, profile and invalid V2', async () => {
  const { default: data } = await import('./result.fixture.json')
  const envelope = { run_id: id, request: { ...data.request }, data }
  const mutations = [
    (v: any) => { v.data.request.strategy_profile = 'expiry_to_Q1_v1' },
    (v: any) => { v.data.profile = 'wrong' },
    (v: any) => { v.data.definition_version = 'wrong' },
    (v: any) => { v.data.views.returns.layers[0].x_axis = 'missing' },
    (v: any) => { v.data.views.drawdown.layers[0].layer.data.reverse() },
    (v: any) => { v.data.summary.extra = 1 },
  ]
  const fetch = vi.fn().mockResolvedValueOnce(response(envelope))
  for (const mutate of mutations) { const v = structuredClone(envelope); mutate(v); fetch.mockResolvedValueOnce(response(v)) }
  vi.stubGlobal('fetch', fetch)
  expect((await getResult(id, signal())).data).toEqual(data)
  for (const _ of mutations) await expect(getResult(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
})

it('keeps advisory preflight independent and validates its request association', async () => {
  const dependency = { dependency: 'futures', state: 'incomplete', reason: 'cache_incomplete', coverage: null }
  const value = { request: immutable, ready: false, calendar_cffex: { ...dependency, dependency: 'calendar_cffex' }, futures: dependency, index: { ...dependency, dependency: 'index' } }
  // Safe reason vocabulary comes from the published schema, not free text.
  const { default: schema } = await import('./backtesting.openapi.json')
  const reason = schema.components.schemas.FuturesRollReadinessDependency.properties.reason.enum[0]
  for (const k of ['calendar_cffex', 'futures', 'index'] as const) value[k].reason = reason
  const fetch = vi.fn().mockResolvedValueOnce(response(value)).mockResolvedValueOnce(response({ ...value, request: { ...immutable, strategy_profile: 'expiry_to_Q1_v1' } }))
  vi.stubGlobal('fetch', fetch)
  expect(await checkInputs(request, signal())).toEqual(value)
  await expect(checkInputs(request, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
  expect(fetch.mock.calls[0][0]).toBe('/api/backtesting/futures-roll/preflight')
})

it.each([[409, 'corrupt'], [409, 'result_not_ready'], [413, 'result_too_large'], [413, 'response_too_large'], [503, 'read_busy'], [503, 'unavailable'], [404, 'run_not_found'], [500, 'internal_error']])('maps Result %s %s', async (status, kind) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind, detail: 'safe', param: null } }, status as number)))
  await expect(getResult(id, signal())).rejects.toMatchObject({ kind })
})
it('preserves supplied numeric facts without recomputing summary or curves', async () => {
  const { default: original } = await import('./result.fixture.json')
  const data = structuredClone(original)
  data.summary.gross_return = 0.123456
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ run_id: id, request: data.request, data })))
  const result = await getResult(id, signal())
  expect(result.data.summary.gross_return).toBe(0.123456)
  expect(result.data.views).toEqual(original.views)
})
it('lets an obsolete 401 close this authentication lifetime', async () => {
  let resolve!: (r: Response) => void
  vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(done => { resolve = done })))
  const controller = new AbortController()
  const pending = getRun(id, controller.signal)
  controller.abort()
  resolve(response({}, 401))
  await expect(pending).rejects.toMatchObject({ name: 'AbortError' })
  expect(unauthorized).toHaveBeenCalledOnce()
})
