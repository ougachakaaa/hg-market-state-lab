import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { checkInputs, ResearchError, submitRun } from '../api/futuresBasis'
import type { Preflight } from '../api/futuresBasis'
import { shanghaiDate, usePreflight } from './usePreflight'
vi.mock('../api/futuresBasis', async importOriginal => ({
  ...await importOriginal<typeof import('../api/futuresBasis')>(), checkInputs: vi.fn(), submitRun: vi.fn(),
}))
const query = { product_code: 'IM' as const, start_date: '2026-11-01', end_date: '2026-11-10' }
function assessment(submission: Preflight['submission'] = 'allowed'): Preflight {
  return { request: { ...query, case: 'futures_basis_v1', analysis_profile: 'r01a_standard_v1' },
    checked_at: '2026-11-10T15:59:59Z', market_date: '2026-11-10', today_gate: 'ready', submission, dependencies: [] }
}
function deferred<T>() { let resolve!: (v: T) => void; const promise = new Promise<T>(done => { resolve = done }); return { promise, resolve } }
async function tick(ms = 400) { await act(async () => { await vi.advanceTimersByTimeAsync(ms) }) }
beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date('2026-11-10T15:59:50Z')); vi.clearAllMocks() })
afterEach(() => { cleanup(); vi.useRealTimers() })
it('debounces, requires explicit risk confirmation and never submits a Run', async () => {
  vi.mocked(checkInputs).mockResolvedValue(assessment('confirm_required'))
  const { result } = renderHook(() => usePreflight(query))
  await tick(399); expect(checkInputs).not.toHaveBeenCalled(); expect(result.current.canSubmit).toBe(false)
  await tick(1); expect(result.current.result?.submission).toBe('confirm_required'); expect(result.current.canSubmit).toBe(false)
  act(() => result.current.confirm(true)); expect(result.current.canSubmit).toBe(true)
  act(() => result.current.refresh()); expect(result.current.canSubmit).toBe(false)
  await tick(); expect(result.current.confirmed).toBe(false)
  expect(submitRun).not.toHaveBeenCalled()
})
it('aborts edits and ignores late results, including when the query changes back', async () => {
  const first = deferred<Preflight>()
  vi.mocked(checkInputs).mockReturnValueOnce(first.promise).mockResolvedValueOnce(assessment())
  const { result, rerender, unmount } = renderHook(({ q }) => usePreflight(q), { initialProps: { q: query } })
  await tick(); const signal = vi.mocked(checkInputs).mock.calls[0][1]
  rerender({ q: { ...query, product_code: 'IC' as 'IM' } }); expect(signal.aborted).toBe(true)
  await act(async () => first.resolve(assessment())); expect(result.current.canSubmit).toBe(false)
  rerender({ q: query }); await tick(); expect(result.current.canSubmit).toBe(true)
  rerender({ q: { ...query, product_code: 'IC' as 'IM' } }); expect(result.current.canSubmit).toBe(false)
  rerender({ q: query }); expect(result.current.canSubmit).toBe(false)
  unmount(); expect(vi.mocked(checkInputs).mock.calls[1][1].aborted).toBe(true)
})
it('blocks failures and blocked assessments; rechecks on focus and server Shanghai midnight', async () => {
  vi.mocked(checkInputs).mockRejectedValueOnce(new ResearchError('network')).mockResolvedValueOnce(assessment('blocked')).mockResolvedValue(assessment())
  const { result } = renderHook(() => usePreflight(query))
  await tick(); expect(result.current.error?.kind).toBe('network'); expect(result.current.canSubmit).toBe(false)
  act(() => window.dispatchEvent(new Event('focus'))); await tick(); expect(result.current.result?.submission).toBe('blocked'); expect(result.current.canSubmit).toBe(false)
  await tick(1000); expect(result.current.canSubmit).toBe(false)
  await tick(); expect(checkInputs).toHaveBeenCalledTimes(3)
  expect(submitRun).not.toHaveBeenCalled()
})
it('uses Shanghai rather than browser-local date and does not check incomplete inputs', async () => {
  expect(shanghaiDate(new Date('2026-11-09T16:00:00Z'))).toBe('2026-11-10')
  renderHook(() => usePreflight(undefined)); await tick(); expect(checkInputs).not.toHaveBeenCalled()
})
