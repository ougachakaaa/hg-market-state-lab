import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { checkInputs, submitRun, type RunRequest, type Preflight } from '../api/backtesting'
import { usePreflight } from './usePreflight'
vi.mock('../api/backtesting', async original => ({ ...await original<typeof import('../api/backtesting')>(), checkInputs: vi.fn(), submitRun: vi.fn() }))
const query: RunRequest = { product_code: 'IM' as const, start_date: '2025-02-17', end_date: '2025-03-25', strategy_profile: 'expiry_to_M1_v1' as const }
const assessment = { ready: false } as Preflight
beforeEach(() => { vi.useFakeTimers(); vi.clearAllMocks() })
afterEach(() => { cleanup(); vi.useRealTimers() })
it('invalidates immediately on edits, ignores stale response and never submits', async () => {
  let resolve!: (v: Preflight) => void
  vi.mocked(checkInputs).mockReturnValueOnce(new Promise(done => { resolve = done })).mockResolvedValue(assessment)
  const { result, rerender } = renderHook(({ q }) => usePreflight(q), { initialProps: { q: query } })
  await act(async () => { await vi.advanceTimersByTimeAsync(350) })
  const signal = vi.mocked(checkInputs).mock.calls[0][1]
  rerender({ q: { ...query, end_date: '2025-03-26' } })
  expect(signal.aborted).toBe(true); expect(result.current.result).toBeUndefined()
  await act(async () => { resolve({ ready: true } as Preflight); await Promise.resolve() })
  expect(result.current.result).toBeUndefined()
  await act(async () => { await vi.advanceTimersByTimeAsync(350) })
  expect(result.current.result?.ready).toBe(false)
  act(() => result.current.refresh()); expect(result.current.result).toBeUndefined()
  expect(submitRun).not.toHaveBeenCalled()
})
it('does nothing without a complete query', async () => {
  renderHook(() => usePreflight(undefined))
  await act(async () => { await vi.advanceTimersByTimeAsync(1000) })
  expect(checkInputs).not.toHaveBeenCalled()
})
it('does not resurrect old readiness when returning to a previous form identity', async () => {
  vi.mocked(checkInputs).mockResolvedValue(assessment)
  const { result, rerender } = renderHook(({ q }) => usePreflight(q), { initialProps: { q: query } })
  await act(async () => { await vi.advanceTimersByTimeAsync(350) })
  expect(result.current.result).toBe(assessment)
  rerender({ q: { ...query, strategy_profile: 'expiry_to_Q1_v1' } })
  rerender({ q: query })
  expect(result.current.result).toBeUndefined(); expect(result.current.checking).toBe(true)
})
