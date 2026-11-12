import { useEffect, useState } from 'react'
import { BacktestingError, checkInputs, type Preflight, type RunRequest } from '../api/backtesting'

export function usePreflight(query: RunRequest | undefined) {
  const key = query ? JSON.stringify(query) : ''
  const [revision, setRevision] = useState(0)
  const [state, setState] = useState<{ key: string; revision: number; result?: Preflight; error?: BacktestingError; signal?: AbortSignal }>({ key: '', revision: -1 })
  useEffect(() => {
    if (!key) return
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      try {
        const result = await checkInputs(JSON.parse(key), controller.signal)
        if (!controller.signal.aborted) setState({ key, revision, result, signal: controller.signal })
      } catch (error) {
        if (!controller.signal.aborted && !(error instanceof DOMException && error.name === 'AbortError')) setState({ key, revision, signal: controller.signal, error: error instanceof BacktestingError ? error : new BacktestingError('invalid_response') })
      }
    }, 350)
    return () => { controller.abort(); clearTimeout(timer) }
  }, [key, revision])
  const matching = state.key === key && state.revision === revision && !!state.signal && !state.signal.aborted
  const result = matching ? state.result : undefined
  const error = matching ? state.error : undefined
  return { result, error, checking: !!key && !result && !error, refresh: () => setRevision(v => v + 1) }
}
