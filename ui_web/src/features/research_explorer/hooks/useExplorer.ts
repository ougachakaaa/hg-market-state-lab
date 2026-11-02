import { useEffect, useState } from 'react'
import { getAnalysis, getChartView, getPublication, listPublications } from '../api/research'

type Load<T> = { status: 'idle' | 'loading'; key: string } | { status: 'success'; key: string; data: T } | { status: 'error'; key: string; error: unknown }
function useRequest<T>(key: string | null, load: (signal: AbortSignal) => Promise<T>, deps: unknown[]) {
  const [state, setState] = useState<Load<T>>({ status: 'idle', key: '' })
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    if (key === null) return
    const controller = new AbortController()
    setState({ status: 'loading', key })
    load(controller.signal).then(data => { if (!controller.signal.aborted) setState({ status: 'success', key, data }) }, error => {
      if (!controller.signal.aborted) setState({ status: 'error', key, error })
    })
    return () => controller.abort()
    // Load is defined from the explicit identity dependencies.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, revision, ...deps])
  const visible: Load<T> = key === null ? { status: 'idle', key: '' } : state.key === key ? state : { status: 'loading', key }
  return [visible, () => setRevision(n => n + 1)] as const
}
export function useExplorer() {
  const [cursors, setCursors] = useState<(string | null)[]>([null])
  const [page, setPage] = useState(0)
  const [publication, setPublication] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [view, setView] = useState<string | null>(null)
  const cursor = cursors[page]
  const [list, retryList] = useRequest(JSON.stringify(cursor), s => listPublications(cursor, s), [])
  const [manifest, retryManifest] = useRequest(publication, s => getPublication(publication!, s), [])
  const [result, retryResult] = useRequest(publication && analysis ? JSON.stringify([publication, analysis]) : null, s => getAnalysis(publication!, analysis!, s), [])
  const [chart, retryChart] = useRequest(publication && analysis && view ? JSON.stringify([publication, analysis, view]) : null, s => getChartView(publication!, view!, s), [])
  function selectPublication(id: string | null) { setPublication(id); setAnalysis(null); setView(null) }
  function selectAnalysis(id: string | null) { setAnalysis(id); setView(null) }
  function next(cursorValue: string) { setCursors([...cursors.slice(0, page + 1), cursorValue]); setPage(page + 1) }
  return { list, manifest, result, chart, retryList, retryManifest, retryResult, retryChart, publication, analysis, view, selectPublication, selectAnalysis, setView, page, previous: () => setPage(n => Math.max(0, n - 1)), next }
}
