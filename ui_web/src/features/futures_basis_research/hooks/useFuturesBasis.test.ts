import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useFuturesBasis } from './useFuturesBasis'
import type { Run } from '../api/futuresBasis'
import { getReport, getRun, ResearchError, submitRun } from '../api/futuresBasis'
vi.mock('../api/futuresBasis', async importOriginal => {
  const actual = await importOriginal<typeof import('../api/futuresBasis')>()
  return { ...actual, getReport: vi.fn(), getRun: vi.fn(), submitRun: vi.fn() }
})
const id = 'a'.repeat(32); const other = 'b'.repeat(32)
const request = { product_code: 'IM' as const, start_date: '2024-10-18', end_date: '2024-10-21' }
const accepted = { run_id: id, request: { ...request, case: 'futures_basis_v1' as const, analysis_profile: 'r01a_standard_v1' as const }, status: 'PENDING' as const, created_at: '2026-11-09T00:00:00Z' }
const pending: Run = { ...accepted, started_at: null, finished_at: null, result_available: false, result_status: null, failure: null }
const completed = { ...pending, status: 'COMPLETED' as const, result_available: true, result_status: 'partial' as const }
const report = { run_id: id, request: accepted.request, result_status: 'partial', data: { status: 'partial' } } as Awaited<ReturnType<typeof getReport>>
function deferred<T>() { let resolve!: (v: T) => void; const promise = new Promise<T>(done => { resolve = done }); return { promise, resolve } }
async function flush() { await act(async () => { await Promise.resolve() }) }
beforeEach(() => { vi.useFakeTimers(); vi.clearAllMocks(); window.history.replaceState(null, '', '/research/futures-basis') })
afterEach(() => { cleanup(); vi.useRealTimers() })

describe('Futures Basis run lifecycle', () => {
  it('polls at 1.5 seconds without overlap and loads partial report once', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    const delayed = deferred<typeof pending>()
    vi.mocked(getRun).mockReturnValueOnce(delayed.promise).mockResolvedValueOnce(completed)
    vi.mocked(getReport).mockResolvedValue(report)
    const { result } = renderHook(useFuturesBasis)
    await act(async () => { await vi.advanceTimersByTimeAsync(5000) })
    expect(getRun).toHaveBeenCalledTimes(1)
    delayed.resolve(pending); await flush()
    await act(async () => { await vi.advanceTimersByTimeAsync(1499) }); expect(getRun).toHaveBeenCalledTimes(1)
    await act(async () => { await vi.advanceTimersByTimeAsync(1) })
    expect(result.current.phase).toBe('COMPLETED'); expect(result.current.report?.data.status).toBe('partial')
    await act(async () => { await vi.advanceTimersByTimeAsync(10000) })
    expect(getRun).toHaveBeenCalledTimes(2); expect(getReport).toHaveBeenCalledTimes(1)
  })
  it('preserves terminal report on busy and unknown submission outcome without retry', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getReport).mockResolvedValue(report)
    vi.mocked(submitRun).mockRejectedValueOnce(new ResearchError('run_busy')).mockRejectedValueOnce(new ResearchError('network'))
    const { result } = renderHook(useFuturesBasis); await flush()
    await act(async () => { await result.current.submit(request) })
    expect(result.current.report).toBe(report); expect(result.current.feedback?.kind).toBe('run_busy')
    await act(async () => { await result.current.submit(request) })
    expect(result.current.report).toBe(report); expect(result.current.feedback?.kind).toBe('network'); expect(submitRun).toHaveBeenCalledTimes(2)
  })
  it('retries status and report independently', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    vi.mocked(getRun).mockRejectedValueOnce(new ResearchError('network')).mockResolvedValueOnce(completed)
    vi.mocked(getReport).mockRejectedValueOnce(new ResearchError('read_busy')).mockResolvedValueOnce(report)
    const { result } = renderHook(useFuturesBasis); await flush(); expect(result.current.phase).toBe('STATUS_ERROR')
    act(() => result.current.retry(false)); await flush(); expect(result.current.phase).toBe('REPORT_ERROR')
    act(() => result.current.retry(true)); await flush(); expect(result.current.phase).toBe('COMPLETED')
    expect(getRun).toHaveBeenCalledTimes(2); expect(getReport).toHaveBeenCalledTimes(2); expect(submitRun).not.toHaveBeenCalled()
  })
  it('aborts and rejects late responses after same-path popstate and unmount', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    const old = deferred<typeof pending>(); const next = deferred<typeof pending>()
    vi.mocked(getRun).mockReturnValueOnce(old.promise).mockReturnValueOnce(next.promise)
    const { result, unmount } = renderHook(useFuturesBasis)
    const firstSignal = vi.mocked(getRun).mock.calls[0][1]
    act(() => { window.history.pushState(null, '', `?run_id=${other}`); window.dispatchEvent(new PopStateEvent('popstate')) })
    expect(firstSignal.aborted).toBe(true)
    old.resolve(completed); await flush(); expect(result.current.report).toBeUndefined(); expect(result.current.id).toBe(other)
    expect(getReport).not.toHaveBeenCalled()
    unmount(); expect(vi.mocked(getRun).mock.calls[1][1].aborted).toBe(true)
  })
  it('writes accepted identity to URL and clears indistinguishable not-found identity', async () => {
    vi.mocked(submitRun).mockResolvedValue(accepted); vi.mocked(getRun).mockRejectedValue(new ResearchError('run_not_found'))
    const { result } = renderHook(useFuturesBasis)
    await act(async () => { await result.current.submit(request) }); await flush()
    expect(result.current.phase).toBe('UNKNOWN_RUN'); expect(window.location.search).toBe('')
  })
})

it('keeps failed immutable request for an explicit new Run and aborts submission on unmount', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValue({ ...pending, status: 'FAILED', failure: { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'Safe failure' } })
  const post = deferred<typeof accepted>()
  vi.mocked(submitRun).mockReturnValue(post.promise)
  const { result, unmount } = renderHook(useFuturesBasis); await flush()
  expect(result.current.phase).toBe('FAILED')
  const original = result.current.run!.request
  act(() => { void result.current.submit({ product_code: original.product_code, start_date: original.start_date, end_date: original.end_date }) })
  expect(submitRun).toHaveBeenCalledWith(request, expect.any(AbortSignal))
  unmount(); expect(vi.mocked(submitRun).mock.calls[0][1].aborted).toBe(true)
  post.resolve({ ...accepted, run_id: other }); await flush()
  expect(window.location.search).toBe(`?run_id=${id}`)
})

it('retains the failed read context independently of a previously completed Run', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValueOnce(completed).mockRejectedValueOnce(new ResearchError('unavailable'))
  vi.mocked(getReport).mockResolvedValueOnce(report)
  const { result } = renderHook(useFuturesBasis); await flush()
  expect(result.current.phase).toBe('COMPLETED')
  act(() => window.dispatchEvent(new PopStateEvent('popstate'))); await flush()
  expect(result.current.phase).toBe('UNAVAILABLE')
  expect(result.current.run?.status).toBe('COMPLETED')
  expect(result.current.errorRead).toBe('status')
  expect(submitRun).not.toHaveBeenCalled()
})
