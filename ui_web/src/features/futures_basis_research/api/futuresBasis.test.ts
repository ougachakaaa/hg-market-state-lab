import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { getReport, getRun, products, submitRun } from './futuresBasis'
const id = 'a'.repeat(32)
const request = { product_code: 'IM' as const, start_date: '2024-10-18', end_date: '2024-10-21' }
const immutable = { ...request, case: 'futures_basis_v1', analysis_profile: 'r01a_standard_v1' }
const accepted = { run_id: id, request: immutable, status: 'PENDING', created_at: '2026-11-09T00:00:00Z' }
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
let release: () => void
const unauthorized = vi.fn()
beforeEach(() => { unauthorized.mockClear(); release = installRequestBoundary(createRequestBoundary(unauthorized)) })
afterEach(() => { release(); vi.unstubAllGlobals() })
const signal = () => new AbortController().signal

describe('Futures Basis HTTP adapter', () => {
  it('uses generated products and protected same-origin JSON POST', async () => {
    expect(products).toEqual(['IM', 'IC', 'IF', 'IH'])
    const fetch = vi.fn().mockResolvedValue(response(accepted, 202)); vi.stubGlobal('fetch', fetch)
    expect(await submitRun(request, signal())).toEqual(accepted)
    expect(fetch.mock.calls[0][0]).toBe('/api/research/futures-basis/runs')
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
    const run = { ...accepted, started_at: null, finished_at: null, result_available: false, result_status: null, failure: null }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(run)).mockResolvedValueOnce(response({ ...run, run_id: 'b'.repeat(32) })).mockResolvedValueOnce(response({ ...run, result_available: true })).mockResolvedValueOnce(response({ run_id: id, request: immutable, result_status: 'complete', data: { profile: 'wrong' } })))
    expect(await getRun(id, signal())).toEqual(run)
    await expect(getRun(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(getRun(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(getReport(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
  })
  it('closes the application gate on 401 and never retries a lost POST', async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new TypeError('lost')).mockResolvedValueOnce(response({ error: { kind: 'authentication_required', detail: 'safe' } }, 401)); vi.stubGlobal('fetch', fetch)
    await expect(submitRun(request, signal())).rejects.toMatchObject({ kind: 'network' })
    expect(fetch).toHaveBeenCalledTimes(1)
    await expect(getRun(id, signal())).rejects.toMatchObject({ name: 'AbortError' })
    expect(unauthorized).toHaveBeenCalledOnce()
  })
})

it('validates complete producer payload association and every View', async () => {
  const { readerFixture } = await import('../report/reader.fixture')
  const data = readerFixture()
  const envelope = { run_id: id, request: immutable, result_status: 'complete', data }
  const mismatch = structuredClone(envelope); mismatch.data.request.observation.product_code = 'IC'
  const badView = structuredClone(envelope); (badView.data.views.history.basis_value as any).version = 77
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(envelope)).mockResolvedValueOnce(response(mismatch)).mockResolvedValueOnce(response(badView)))
  expect((await getReport(id, signal())).data.fingerprint).toBe(data.fingerprint)
  await expect(getReport(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
  await expect(getReport(id, signal())).rejects.toMatchObject({ kind: 'invalid_response' })
})
