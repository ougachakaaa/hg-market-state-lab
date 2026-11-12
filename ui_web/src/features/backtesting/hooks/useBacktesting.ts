import { useCallback, useEffect, useRef, useState } from 'react'
import { getResult, getRun, BacktestingError, sameRequest, submitRun } from '../api/backtesting'
import type { Accepted, ResultResponse, Run, RunRequest } from '../api/backtesting'

type Phase = 'IDLE' | 'STATUS_LOADING' | 'PENDING' | 'RUNNING' | 'RESULT_LOADING' | 'COMPLETED' | 'RESULT_READY' | 'FAILED' | 'INTERRUPTED' | 'STATUS_ERROR' | 'RESULT_ERROR' | 'UNKNOWN_RUN' | 'UNAVAILABLE'
type State = { phase: Phase; run?: Run | Accepted; result?: ResultResponse; error?: BacktestingError; errorRead?: 'status' | 'result' }
function identity() { return new URLSearchParams(window.location.search).get('run_id') ?? '' }
function asError(error: unknown) { return error instanceof BacktestingError ? error : new BacktestingError('invalid_response') }
function cancelled(error: unknown) { return error instanceof DOMException && error.name === 'AbortError' }
export function useBacktesting() {
  const [id, setId] = useState(identity)
  const [state, setState] = useState<State>({ phase: 'IDLE' })
  const [feedback, setFeedback] = useState<BacktestingError>()
  const [submitting, setSubmitting] = useState(false)
  const [attempt, setAttempt] = useState({ sequence: 0, result: false })
  const post = useRef<AbortController | null>(null)
  const epoch = useRef(0)
  const submissionEpoch = useRef(0)
  const lastRun = useRef<Run | Accepted | undefined>(undefined)
  const writeId = useCallback((next: string, replace = false) => {
    const url = new URL(window.location.href)
    if (next) url.searchParams.set('run_id', next); else url.searchParams.delete('run_id')
    window.history[replace ? 'replaceState' : 'pushState'](null, '', url.pathname + url.search)
    setId(next)
  }, [])
  useEffect(() => {
    const sync = () => { epoch.current++; submissionEpoch.current++; post.current?.abort(); setSubmitting(false); setFeedback(undefined); setId(identity()); setAttempt(a => ({ sequence: a.sequence + 1, result: false })) }
    window.addEventListener('popstate', sync)
    // Cleanup intentionally aborts the latest POST in this mounted lifecycle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => { window.removeEventListener('popstate', sync); epoch.current++; submissionEpoch.current++; post.current?.abort() }
  }, [])
  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    let live = true
    const generation = ++epoch.current
    const current = () => live && generation === epoch.current && !controller.signal.aborted
    const restored = lastRun.current?.run_id === id ? lastRun.current : undefined
    // Synchronize presentation with the external URL/request lifecycle.
    // eslint-disable-next-line react/set-state-in-effect
    if (!id) { setState({ phase: 'IDLE' }); return () => { live = false; controller.abort() } }
    setState({ phase: attempt.result ? 'RESULT_LOADING' : restored?.status ?? 'STATUS_LOADING', run: restored })
    async function loadResult(run: Run | Accepted) {
      if (!current()) return
      setState({ phase: 'RESULT_LOADING', run })
      try {
        const result = await getResult(id, controller.signal)
        if (!current()) return
        if (!sameRequest(result.request, run.request)) throw new BacktestingError('invalid_response')
        setState({ phase: 'RESULT_READY', run, result })
      } catch (error) { failure(error, true, run) }
    }
    function failure(error: unknown, result: boolean, run?: Run | Accepted) {
      if (!current() || cancelled(error)) return
      const e = asError(error)
      if (e.kind === 'run_not_found') {
        lastRun.current = undefined
        setState({ phase: 'UNKNOWN_RUN', error: e, errorRead: result ? 'result' : 'status' })
      } else setState({ phase: e.kind === 'unavailable' ? 'UNAVAILABLE' : result ? 'RESULT_ERROR' : 'STATUS_ERROR', run, error: e, errorRead: result ? 'result' : 'status' })
    }
    async function poll() {
      try {
        const run = await getRun(id, controller.signal)
        if (!current()) return
        const previous = lastRun.current
        if (previous?.run_id === id && !sameRequest(previous.request, run.request)) throw new BacktestingError('invalid_response')
        lastRun.current = run
        if (run.status === 'COMPLETED') { await loadResult(run); return }
        setState({ phase: run.status, run })
        if (run.status === 'PENDING' || run.status === 'RUNNING') timer = setTimeout(() => void poll(), 1500)
      } catch (error) { failure(error, false, lastRun.current?.run_id === id ? lastRun.current : undefined) }
    }
    if (attempt.result && restored?.status === 'COMPLETED') void loadResult(restored); else void poll()
    return () => { live = false; controller.abort(); clearTimeout(timer) }
  }, [id, attempt, writeId])
  const submit = useCallback(async (request: RunRequest) => {
    if (post.current && !post.current.signal.aborted) return
    const controller = new AbortController(); post.current = controller
    const generation = submissionEpoch.current
    setSubmitting(true); setFeedback(undefined)
    try {
      const accepted = await submitRun(request, controller.signal)
      if (controller.signal.aborted || generation !== submissionEpoch.current) return
      // Invalidate the previous Run before React commits the new URL lifecycle.
      epoch.current++
      lastRun.current = accepted
      setState({ phase: 'PENDING', run: accepted })
      setAttempt(a => ({ sequence: a.sequence + 1, result: false }))
      writeId(accepted.run_id)
    } catch (error) {
      if (!controller.signal.aborted && generation === submissionEpoch.current && !cancelled(error)) setFeedback(asError(error))
    } finally { if (post.current === controller) { post.current = null; setSubmitting(false) } }
  }, [writeId])
  const retry = useCallback((result: boolean) => setAttempt(a => ({ sequence: a.sequence + 1, result })), [])
  const visible: State = state.run && state.run.run_id !== id ? { phase: id ? 'STATUS_LOADING' : 'IDLE' } : state
  return { ...visible, id, feedback, submitting, submit, retry }
}
