import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useBacktesting } from './useBacktesting'
import fixture from '../api/result.fixture.json'
import type { Run } from '../api/backtesting'
import { getResult, getRun, BacktestingError, submitRun } from '../api/backtesting'
vi.mock('../api/backtesting', async importOriginal => {
  const actual = await importOriginal<typeof import('../api/backtesting')>()
  return { ...actual, getResult: vi.fn(), getRun: vi.fn(), submitRun: vi.fn() }
})
const id = 'a'.repeat(32); const other = 'b'.repeat(32)
const request = { product_code: 'IM' as const, start_date: '2024-10-18', end_date: '2024-10-21', strategy_profile: 'expiry_to_M1_v1' as const }
const accepted = { run_id: id, request: { ...request, case: 'futures_roll_long_v1' as const }, status: 'PENDING' as const, created_at: '2026-11-09T00:00:00Z' }
const pending: Run = { ...accepted, started_at: null, finished_at: null, result_available: false, failure: null }
const completed = { ...pending, status: 'COMPLETED' as const, result_available: true }
const envelope = { run_id: id, request: accepted.request, data: fixture } as Awaited<ReturnType<typeof getResult>>
function deferred<T>() { let resolve!: (v: T) => void; const promise = new Promise<T>(done => { resolve = done }); return { promise, resolve } }
async function flush() { await act(async () => { await Promise.resolve() }) }
beforeEach(() => { vi.useFakeTimers(); vi.clearAllMocks(); window.history.replaceState(null, '', '/backtesting') })
afterEach(() => { cleanup(); vi.useRealTimers() })

describe('Backtesting run lifecycle', () => {
  it('polls at 1.5 seconds without overlap and loads completed Result once', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    const delayed = deferred<typeof pending>()
    vi.mocked(getRun).mockReturnValueOnce(delayed.promise).mockResolvedValueOnce(completed)
    vi.mocked(getResult).mockResolvedValue(envelope)
    const { result } = renderHook(useBacktesting)
    await act(async () => { await vi.advanceTimersByTimeAsync(5000) })
    expect(getRun).toHaveBeenCalledTimes(1)
    delayed.resolve(pending); await flush()
    await act(async () => { await vi.advanceTimersByTimeAsync(1499) }); expect(getRun).toHaveBeenCalledTimes(1)
    await act(async () => { await vi.advanceTimersByTimeAsync(1) })
    expect(result.current.phase).toBe('RESULT_READY'); expect(result.current.result?.data.status).toBe('complete')
    await act(async () => { await vi.advanceTimersByTimeAsync(10000) })
    expect(getRun).toHaveBeenCalledTimes(2); expect(getResult).toHaveBeenCalledTimes(1)
  })
  it('preserves terminal result on busy and unknown submission outcome without retry', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getResult).mockResolvedValue(envelope)
    vi.mocked(submitRun).mockRejectedValueOnce(new BacktestingError('run_busy')).mockRejectedValueOnce(new BacktestingError('network'))
    const { result } = renderHook(useBacktesting); await flush()
    await act(async () => { await result.current.submit(request) })
    expect(result.current.result).toBe(envelope); expect(result.current.feedback?.kind).toBe('run_busy')
    await act(async () => { await result.current.submit(request) })
    expect(result.current.result).toBe(envelope); expect(result.current.feedback?.kind).toBe('network'); expect(submitRun).toHaveBeenCalledTimes(2)
  })
  it('retries status and result independently', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    vi.mocked(getRun).mockRejectedValueOnce(new BacktestingError('network')).mockResolvedValueOnce(completed)
    vi.mocked(getResult).mockRejectedValueOnce(new BacktestingError('read_busy')).mockResolvedValueOnce(envelope)
    const { result } = renderHook(useBacktesting); await flush(); expect(result.current.phase).toBe('STATUS_ERROR')
    act(() => result.current.retry(false)); await flush(); expect(result.current.phase).toBe('RESULT_ERROR')
    act(() => result.current.retry(true)); await flush(); expect(result.current.phase).toBe('RESULT_READY')
    expect(getRun).toHaveBeenCalledTimes(2); expect(getResult).toHaveBeenCalledTimes(2); expect(submitRun).not.toHaveBeenCalled()
  })
  it('aborts and rejects late responses after same-path popstate and unmount', async () => {
    window.history.replaceState(null, '', `?run_id=${id}`)
    const old = deferred<typeof pending>(); const next = deferred<typeof pending>()
    vi.mocked(getRun).mockReturnValueOnce(old.promise).mockReturnValueOnce(next.promise)
    const { result, unmount } = renderHook(useBacktesting)
    const firstSignal = vi.mocked(getRun).mock.calls[0][1]
    act(() => { window.history.pushState(null, '', `?run_id=${other}`); window.dispatchEvent(new PopStateEvent('popstate')) })
    expect(firstSignal.aborted).toBe(true)
    old.resolve(completed); await flush(); expect(result.current.result).toBeUndefined(); expect(result.current.id).toBe(other)
    expect(getResult).not.toHaveBeenCalled()
    unmount(); expect(vi.mocked(getRun).mock.calls[1][1].aborted).toBe(true)
  })
  it('writes accepted identity to URL and clears indistinguishable not-found identity', async () => {
    vi.mocked(submitRun).mockResolvedValue(accepted); vi.mocked(getRun).mockRejectedValue(new BacktestingError('run_not_found'))
    const { result } = renderHook(useBacktesting)
    await act(async () => { await result.current.submit(request) }); await flush()
    expect(result.current.phase).toBe('UNKNOWN_RUN'); expect(window.location.search).toBe(`?run_id=${id}`)
  })
})

it('keeps failed immutable request for an explicit new Run and aborts submission on unmount', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValue({ ...pending, status: 'FAILED', failure: { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'Safe failure' } })
  const post = deferred<typeof accepted>()
  vi.mocked(submitRun).mockReturnValue(post.promise)
  const { result, unmount } = renderHook(useBacktesting); await flush()
  expect(result.current.phase).toBe('FAILED')
  const original = result.current.run!.request
  act(() => { void result.current.submit({ product_code: original.product_code, start_date: original.start_date, end_date: original.end_date, strategy_profile: original.strategy_profile }) })
  expect(submitRun).toHaveBeenCalledWith(request, expect.any(AbortSignal))
  unmount(); expect(vi.mocked(submitRun).mock.calls[0][1].aborted).toBe(true)
  post.resolve({ ...accepted, run_id: other }); await flush()
  expect(window.location.search).toBe(`?run_id=${id}`)
})

it('retains the failed read context independently of a previously completed Run', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValueOnce(completed).mockRejectedValueOnce(new BacktestingError('unavailable'))
  vi.mocked(getResult).mockResolvedValueOnce(envelope)
  const { result } = renderHook(useBacktesting); await flush()
  expect(result.current.phase).toBe('RESULT_READY')
  act(() => window.dispatchEvent(new PopStateEvent('popstate'))); await flush()
  expect(result.current.phase).toBe('UNAVAILABLE')
  expect(result.current.run?.status).toBe('COMPLETED')
  expect(result.current.errorRead).toBe('status')
  expect(submitRun).not.toHaveBeenCalled()
})

it('admits only one pending Submit and never replays it', async () => {
  const post = deferred<typeof accepted>(); vi.mocked(submitRun).mockReturnValue(post.promise)
  vi.mocked(getRun).mockResolvedValue(pending)
  const { result } = renderHook(useBacktesting)
  act(() => { void result.current.submit(request); void result.current.submit(request) })
  expect(submitRun).toHaveBeenCalledTimes(1)
  expect(result.current.submitting).toBe(true)
  post.resolve(accepted); await flush()
  expect(window.location.search).toContain(id)
  await act(async () => { await vi.advanceTimersByTimeAsync(10000) })
  expect(submitRun).toHaveBeenCalledTimes(1)
})
it.each(['FAILED', 'INTERRUPTED'] as const)('never reads Result for %s', async status => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValue({ ...pending, status, failure: { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'internal_failure' } })
  const { result } = renderHook(useBacktesting); await flush()
  expect(result.current.phase).toBe(status); expect(result.current.result).toBeUndefined()
  expect(getResult).not.toHaveBeenCalled()
})
it('rejects a Result from another strategy even for the same Run ID', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValue(completed)
  vi.mocked(getResult).mockResolvedValue({ ...envelope, request: { ...envelope.request, strategy_profile: 'expiry_to_Q1_v1' } })
  const { result } = renderHook(useBacktesting); await flush()
  expect(result.current.phase).toBe('RESULT_ERROR'); expect(result.current.result).toBeUndefined()
})
it('rejects a changed immutable request in a later Status read', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValueOnce(pending).mockResolvedValueOnce({ ...completed, request: { ...completed.request, strategy_profile: 'expiry_to_Q1_v1' } })
  const { result } = renderHook(useBacktesting); await flush()
  await act(async () => { await vi.advanceTimersByTimeAsync(1500) })
  expect(result.current.phase).toBe('STATUS_ERROR'); expect(getResult).not.toHaveBeenCalled()
})
it('keeps an in-flight Submit independent of a manual status reread', async () => {
  window.history.replaceState(null, '', `?run_id=${id}`)
  vi.mocked(getRun).mockResolvedValue(completed)
  vi.mocked(getResult).mockResolvedValue(envelope)
  const post = deferred<typeof accepted>(); vi.mocked(submitRun).mockReturnValue(post.promise)
  const { result } = renderHook(useBacktesting); await flush()
  act(() => { void result.current.submit(request) })
  act(() => result.current.retry(false)); await flush()
  post.resolve({ ...accepted, run_id: other }); await flush()
  expect(window.location.search).toBe(`?run_id=${other}`)
  expect(submitRun).toHaveBeenCalledTimes(1)
})
