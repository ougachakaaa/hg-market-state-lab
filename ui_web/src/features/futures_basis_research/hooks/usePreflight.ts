import { useCallback, useEffect, useRef, useState } from 'react'
import { checkInputs, ResearchError } from '../api/futuresBasis'
import type { Preflight, RunRequest } from '../api/futuresBasis'

export function shanghaiDate(value = new Date()) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(value)
}
export function usePreflight(query: RunRequest | undefined) {
  const key = query ? JSON.stringify(query) : ''
  const [revision, setRevision] = useState(0)
  const [state, setState] = useState<{ key: string; revision: number; result?: Preflight; error?: ResearchError; signal?: AbortSignal }>({ key: '', revision: -1 })
  const [confirmation, setConfirmation] = useState<Preflight>()
  const controller = useRef<AbortController | null>(null)
  const refresh = useCallback(() => { controller.current?.abort(); setRevision(v => v + 1); setConfirmation(undefined) }, [])
  useEffect(() => {
    window.addEventListener('focus', refresh)
    return () => window.removeEventListener('focus', refresh)
  }, [refresh])
  useEffect(() => {
    if (!key) return
    const current = new AbortController()
    controller.current = current
    const timer = setTimeout(async () => {
      try {
        const result = await checkInputs(JSON.parse(key) as RunRequest, current.signal)
        if (!current.signal.aborted) setState({ key, revision, result, signal: current.signal })
      } catch (error) {
        if (!current.signal.aborted && !(error instanceof DOMException && error.name === 'AbortError')) {
          setState({ key, revision, signal: current.signal, error: error instanceof ResearchError ? error : new ResearchError('invalid_response') })
        }
      }
    }, 400)
    return () => { current.abort(); clearTimeout(timer) }
  }, [key, revision])
  const matching = state.key === key && state.revision === revision && !!state.signal && !state.signal.aborted
  const result = matching ? state.result : undefined
  useEffect(() => {
    // Schedule using the server's observed Shanghai day/time when available.
    // This is only invalidation, never an assertion that data remains unchanged.
    const observed = result ? Date.parse(result.checked_at) : Date.now()
    const day = result?.market_date ?? shanghaiDate()
    const next = Date.parse(`${day}T00:00:00+08:00`) + 86400000
    const timer = setTimeout(refresh, Math.max(1, next - observed))
    return () => clearTimeout(timer)
  }, [result, refresh])
  const confirmed = !!result && confirmation === result
  const canSubmit = !!result && result.submission !== 'blocked' && (result.submission !== 'confirm_required' || confirmed)
  return {
    result, error: matching ? state.error : undefined,
    checking: !!key && !result && !(matching && state.error),
    confirmed, confirm: (value: boolean) => setConfirmation(value ? result : undefined),
    canSubmit, refresh,
  }
}
