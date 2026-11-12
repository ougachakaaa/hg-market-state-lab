import { useEffect, useRef, useState } from 'react'
import type { ChartView as ChartViewContract } from '../../../shared/visualization/contract'
import { getAnalysis, getChartView, getPublication, listPublications } from '../api/research'
import type { Analysis, Manifest, PublicationList } from '../api/validateResearch'
import type { ExplorerLoad, ResearchExplorerController } from '../model/explorerPresentation'

type Load<T> =
  | { status: 'idle' | 'loading'; key: string }
  | { status: 'success'; key: string; data: T }
  | { status: 'error'; key: string; error: unknown }

function useRequest<T>(key: string | null, load: (signal: AbortSignal) => Promise<T>, deps: unknown[]) {
  const [state, setState] = useState<Load<T>>({ status: 'idle', key: '' })
  const [revision, setRevision] = useState(0)
  const request = useRef(0)
  useEffect(() => {
    if (key === null) return
    const current = ++request.current
    const controller = new AbortController()
    setState({ status: 'loading', key })
    load(controller.signal).then(data => {
      if (!controller.signal.aborted && current === request.current) setState({ status: 'success', key, data })
    }, error => {
      if (!controller.signal.aborted && current === request.current) setState({ status: 'error', key, error })
    })
    return () => controller.abort()
    // Load is defined from the explicit identity dependencies.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, revision, ...deps])
  const visible: ExplorerLoad<T> = key === null ? { status: 'idle' } : state.key === key ? state : { status: 'loading' }
  return [visible, () => setRevision(value => value + 1)] as const
}

// Production controller. The four reads remain independent and lazy; the selected
// publication/analysis/view identities drive their request keys, and selection changes
// cancel or invalidate obsolete responses.
export function useExplorer(): ResearchExplorerController {
  const [cursors, setCursors] = useState<(string | null)[]>([null])
  const [page, setPage] = useState(0)
  const [publication, setPublication] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [view, setView] = useState<string | null>(null)
  const cursor = cursors[page]
  const [list, retryList] = useRequest<PublicationList>(JSON.stringify(cursor), signal => listPublications(cursor, signal), [])
  const [manifest, retryManifest] = useRequest<Manifest>(publication, signal => getPublication(publication!, signal), [])
  const [result, retryResult] = useRequest<Analysis>(publication && analysis ? JSON.stringify([publication, analysis]) : null,
    signal => getAnalysis(publication!, analysis!, signal), [])
  const [chart, retryChart] = useRequest<ChartViewContract>(publication && analysis && view ? JSON.stringify([publication, analysis, view]) : null,
    signal => getChartView(publication!, view!, signal), [])

  const canNext = list.status === 'success' && list.data.next_cursor !== null
  const canPrevious = page > 0
  function selectPublication(id: string | null) {
    setPublication(id)
    setAnalysis(null)
    setView(null)
  }
  function selectAnalysis(id: string | null) {
    setAnalysis(id)
    setView(null)
  }
  function next() {
    if (list.status !== 'success' || list.data.next_cursor === null) return
    const nextCursor = list.data.next_cursor
    setCursors([...cursors.slice(0, page + 1), nextCursor])
    setPage(page + 1)
  }
  function previous() {
    setPage(value => Math.max(0, value - 1))
  }

  return {
    list, manifest, result, chart, retryList, retryManifest, retryResult, retryChart,
    publication, analysis, view, selectPublication, selectAnalysis, setView,
    page, canPrevious, canNext, previous, next,
  }
}
