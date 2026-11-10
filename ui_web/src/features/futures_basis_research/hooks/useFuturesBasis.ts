import { useCallback, useEffect, useRef, useState } from 'react'
import { getReport, getRun, ResearchError, submitRun } from '../api/futuresBasis'
import type { Accepted, ReportResponse, Run, RunRequest } from '../api/futuresBasis'

type Phase = 'IDLE' | 'PENDING' | 'RUNNING' | 'REPORT_LOADING' | 'COMPLETED' | 'FAILED' | 'INTERRUPTED' | 'STATUS_ERROR' | 'REPORT_ERROR' | 'UNKNOWN_RUN' | 'UNAVAILABLE'
type State = { phase: Phase; run?: Run | Accepted; report?: ReportResponse; error?: ResearchError; errorRead?: 'status' | 'report' }
function identity() { return new URLSearchParams(window.location.search).get('run_id') ?? '' }
function asError(error: unknown) { return error instanceof ResearchError ? error : new ResearchError('invalid_response') }
function cancelled(error: unknown) { return error instanceof DOMException && error.name === 'AbortError' }
export function useFuturesBasis() {
  const [id, setId] = useState(identity)
  const [state, setState] = useState<State>({ phase: 'IDLE' })
  const [feedback, setFeedback] = useState<ResearchError>()
  const [submitting, setSubmitting] = useState(false)
  const [attempt, setAttempt] = useState({ sequence: 0, report: false })
  const post = useRef<AbortController | null>(null)
  const epoch = useRef(0)
  const lastRun = useRef<Run | Accepted | undefined>(undefined)
  const writeId = useCallback((next: string, replace = false) => {
    const url = new URL(window.location.href)
    if (next) url.searchParams.set('run_id', next); else url.searchParams.delete('run_id')
    window.history[replace ? 'replaceState' : 'pushState'](null, '', url.pathname + url.search)
    setId(next)
  }, [])
  useEffect(() => {
    const sync = () => { epoch.current++; post.current?.abort(); setSubmitting(false); setFeedback(undefined); setId(identity()); setAttempt(a => ({ sequence: a.sequence + 1, report: false })) }
    window.addEventListener('popstate', sync)
    // Cleanup intentionally aborts the latest POST in this mounted lifecycle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => { window.removeEventListener('popstate', sync); epoch.current++; post.current?.abort() }
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
    if (!id) { setState(s => s.phase === 'UNKNOWN_RUN' ? s : { phase: 'IDLE' }); return () => { live = false; controller.abort() } }
    setState({ phase: attempt.report ? 'REPORT_LOADING' : 'PENDING', run: restored })
    async function loadReport(run: Run | Accepted) {
      if (!current()) return
      setState({ phase: 'REPORT_LOADING', run })
      try {
        const report = await getReport(id, controller.signal)
        if (!current()) return
        if (['product_code', 'start_date', 'end_date'].some(k => report.request[k as keyof RunRequest] !== run.request[k as keyof RunRequest])) throw new ResearchError('invalid_response')
        if ('result_status' in run && report.result_status !== run.result_status) throw new ResearchError('invalid_response')
        setState({ phase: 'COMPLETED', run, report })
      } catch (error) { failure(error, true, run) }
    }
    function failure(error: unknown, report: boolean, run?: Run | Accepted) {
      if (!current() || cancelled(error)) return
      const e = asError(error)
      if (e.kind === 'run_not_found') {
        lastRun.current = undefined
        setState({ phase: 'UNKNOWN_RUN', error: e }); writeId('', true)
      } else setState({ phase: e.kind === 'unavailable' ? 'UNAVAILABLE' : report ? 'REPORT_ERROR' : 'STATUS_ERROR', run, error: e, errorRead: report ? 'report' : 'status' })
    }
    async function poll() {
      try {
        const run = await getRun(id, controller.signal)
        if (!current()) return
        const previous = lastRun.current
        if (previous?.run_id === id && (['product_code', 'start_date', 'end_date'] as const).some(k => previous.request[k] !== run.request[k])) throw new ResearchError('invalid_response')
        lastRun.current = run
        if (run.status === 'COMPLETED') { await loadReport(run); return }
        setState({ phase: run.status, run })
        if (run.status === 'PENDING' || run.status === 'RUNNING') timer = setTimeout(() => void poll(), 1500)
      } catch (error) { failure(error, false, lastRun.current?.run_id === id ? lastRun.current : undefined) }
    }
    if (attempt.report && restored) void loadReport(restored); else void poll()
    return () => { live = false; controller.abort(); clearTimeout(timer) }
  }, [id, attempt, writeId])
  const submit = useCallback(async (request: RunRequest) => {
    if (post.current && !post.current.signal.aborted) return
    const controller = new AbortController(); post.current = controller
    const generation = epoch.current
    setSubmitting(true); setFeedback(undefined)
    try {
      const accepted = await submitRun(request, controller.signal)
      if (controller.signal.aborted || generation !== epoch.current) return
      // Invalidate the previous Run before React commits the new URL lifecycle.
      epoch.current++
      lastRun.current = accepted
      setState({ phase: 'PENDING', run: accepted })
      setAttempt(a => ({ sequence: a.sequence + 1, report: false }))
      writeId(accepted.run_id)
    } catch (error) {
      if (!controller.signal.aborted && generation === epoch.current && !cancelled(error)) setFeedback(asError(error))
    } finally { if (post.current === controller) { post.current = null; setSubmitting(false) } }
  }, [writeId])
  const retry = useCallback((report: boolean) => setAttempt(a => ({ sequence: a.sequence + 1, report })), [])
  const visible: State = state.run && state.run.run_id !== id ? { phase: 'PENDING' } : state
  return { ...visible, id, feedback, submitting, submit, retry }
}
