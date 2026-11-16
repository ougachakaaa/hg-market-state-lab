import { Activity, StrictMode } from 'react'
import { act, cleanup, render } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { useBacktesting } from './useBacktesting'
import { getRun, getResult, submitRun, BacktestingError } from '../api/backtesting'
import type { Run } from '../api/backtesting'
import fixture from '../api/result.fixture.json'
vi.mock('../api/backtesting', async original => ({ ...await original<typeof import('../api/backtesting')>(), getRun: vi.fn(), getResult: vi.fn(), submitRun: vi.fn() }))
const a = 'a'.repeat(32), b = 'b'.repeat(32)
const request = fixture.request as Run['request']
const running: Run = { run_id: a, request, status: 'RUNNING', created_at: '2026-11-09T00:00:00Z', started_at: null, finished_at: null, result_available: false, failure: null } as Run
const completed: Run = { ...running, status: 'COMPLETED', result_available: true }
const envelope = { run_id: a, request, data: fixture } as Awaited<ReturnType<typeof getResult>>
let current: ReturnType<typeof useBacktesting>
function Page({ active }: { active: boolean }) { current = useBacktesting(active); return <div>{current.result?.run_id ?? current.phase}</div> }
function tree(active: boolean) { return <StrictMode><Activity mode={active ? 'visible' : 'hidden'}><Page active={active} /></Activity></StrictMode> }
async function flush() { await act(async () => { await Promise.resolve() }) }
beforeEach(() => { vi.useFakeTimers(); vi.clearAllMocks(); window.history.replaceState(null, '', `/backtesting/futures-roll-long?run_id=${a}`) })
afterEach(() => { cleanup(); vi.useRealTimers() })
it('retains completed Result without reads when Activity reconnects', async () => {
 vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getResult).mockResolvedValue(envelope)
 const view = render(tree(true)); await flush()
 const reads = vi.mocked(getRun).mock.calls.length
 expect(current.result).toBe(envelope)
 view.rerender(tree(false)); window.history.replaceState(null, '', '/research'); await flush()
 window.history.replaceState(null, '', `/backtesting/futures-roll-long?run_id=${a}`)
 view.rerender(tree(true)); await flush()
 expect(current.result).toBe(envelope); expect(getRun).toHaveBeenCalledTimes(reads)
 expect(getResult).toHaveBeenCalledTimes(1); expect(submitRun).not.toHaveBeenCalled()
})
it('stops polling hidden and reads backend again on return', async () => {
 vi.mocked(getRun).mockResolvedValue(running); vi.mocked(getResult).mockResolvedValue(envelope)
 const view = render(tree(true)); await flush()
 const reads = vi.mocked(getRun).mock.calls.length
 view.rerender(tree(false)); await flush()
 await act(async () => { await vi.advanceTimersByTimeAsync(10000) })
 expect(getRun).toHaveBeenCalledTimes(reads)
 vi.mocked(getRun).mockResolvedValue(completed)
 view.rerender(tree(true)); await flush()
 expect(current.result).toBe(envelope); expect(vi.mocked(getRun).mock.calls.slice(reads).filter(([, signal]) => !signal.aborted)).toHaveLength(1)
})
it('reconciles a URL changed while hidden and explicit no-ID without old-result flash', async () => {
 vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getResult).mockResolvedValue(envelope)
 const view = render(tree(true)); await flush()
 view.rerender(tree(false)); await flush()
 vi.mocked(getRun).mockReturnValue(new Promise(() => {}))
 window.history.replaceState(null, '', `/backtesting/futures-roll-long?run_id=${b}`)
 view.rerender(tree(true))
 expect(current.id).toBe(b); expect(current.result).toBeUndefined(); expect(view.container.textContent).not.toContain(a)
 act(() => { window.history.pushState(null, '', '/backtesting/futures-roll-long'); window.dispatchEvent(new PopStateEvent('popstate')) })
 expect(current.id).toBe(''); expect(current.phase).toBe('IDLE'); expect(current.result).toBeUndefined()
})
it('aborts unconfirmed POST, reports uncertainty, and ignores a late accepted response', async () => {
 vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getResult).mockResolvedValue(envelope)
 let resolve!: (value: Awaited<ReturnType<typeof submitRun>>) => void
 vi.mocked(submitRun).mockReturnValue(new Promise(done => { resolve = done }))
 const view = render(tree(true)); await flush()
 act(() => { void current.submit(request) }); expect(current.submitting).toBe(true)
 view.rerender(tree(false)); await flush()
 expect(vi.mocked(submitRun).mock.calls[0][1].aborted).toBe(true)
 view.rerender(tree(true)); await flush()
 expect(current.submitting).toBe(false); expect(current.feedback?.kind).toBe('submission_unconfirmed')
 resolve({ ...running, run_id: b, status: 'PENDING' }); await flush()
 expect(current.id).toBe(a); expect(current.result).toBe(envelope); expect(submitRun).toHaveBeenCalledTimes(1)
})
it('retains read errors on reconnect until manual GET retry', async () => {
 vi.mocked(getRun).mockRejectedValue(new BacktestingError('network'))
 const view = render(tree(true)); await flush(); const reads = vi.mocked(getRun).mock.calls.length
 view.rerender(tree(false)); view.rerender(tree(true)); await flush()
 expect(getRun).toHaveBeenCalledTimes(reads); expect(current.phase).toBe('STATUS_ERROR')
 vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getResult).mockResolvedValue(envelope)
 act(() => current.retry(false)); await flush(); expect(current.result).toBe(envelope)
})

it('loads B after hidden identity replacement and rejects the delayed Result of A', async () => {
 let resolve!: (value: typeof envelope) => void
 vi.mocked(getRun).mockResolvedValue(completed)
 vi.mocked(getResult).mockReturnValueOnce(new Promise(done => { resolve = done }))
 const view = render(tree(true)); await flush()
 view.rerender(tree(false)); await flush()
 const resultB = { ...envelope, run_id: b }
 vi.mocked(getRun).mockResolvedValue({ ...completed, run_id: b })
 vi.mocked(getResult).mockResolvedValue(resultB)
 window.history.replaceState(null, '', `/backtesting/futures-roll-long?run_id=${b}`)
 view.rerender(tree(true)); await flush()
 expect(current.id).toBe(b); expect(current.result).toBe(resultB)
 resolve(envelope); await flush()
 expect(current.result).toBe(resultB)
})

it('accepts a new Run B once and retains its Result through subsequent navigation', async () => {
 vi.mocked(getRun).mockResolvedValue(completed); vi.mocked(getResult).mockResolvedValue(envelope)
 const view = render(tree(true)); await flush()
 const resultB = { ...envelope, run_id: b }
 vi.mocked(submitRun).mockResolvedValue({ ...running, run_id: b, status: 'PENDING' })
 vi.mocked(getRun).mockResolvedValue({ ...completed, run_id: b }); vi.mocked(getResult).mockResolvedValue(resultB)
 await act(async () => { await current.submit(request) }); await flush()
 expect(window.location.search).toBe(`?run_id=${b}`); expect(current.result).toBe(resultB)
 const reads = vi.mocked(getRun).mock.calls.length
 view.rerender(tree(false)); await flush(); view.rerender(tree(true)); await flush()
 expect(current.result).toBe(resultB); expect(submitRun).toHaveBeenCalledTimes(1)
 expect(getRun).toHaveBeenCalledTimes(reads)
})
