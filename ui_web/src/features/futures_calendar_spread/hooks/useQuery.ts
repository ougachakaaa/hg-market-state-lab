import { useEffect, useRef, useState } from 'react'
import { loadQuery, QueryError } from '../api/query'
import type { Query, Result } from '../api/validateResult'
export type QueryState = { status: 'idle' } | { status: 'loading'; query: Query } | { status: 'success'; query: Query; result: Result; revision: number } | { status: 'error'; query: Query; error: QueryError }
export function useQuery() {
  const [state, setState] = useState<QueryState>({ status: 'idle' })
  const active = useRef<AbortController | null>(null)
  const sequence = useRef(0)
  useEffect(() => () => { ++sequence.current; active.current?.abort() }, [])
  function submit(input: Query) {
    active.current?.abort()
    const query = structuredClone(input)
    const id = ++sequence.current
    const controller = new AbortController(); active.current = controller
    setState({ status: 'loading', query })
    void loadQuery(query, controller.signal).then(result => {
      if (!controller.signal.aborted && id === sequence.current) setState({ status: 'success', query, result, revision: id })
    }).catch(error => {
      if (!controller.signal.aborted && id === sequence.current && error?.name !== 'AbortError') setState({ status: 'error', query, error: error instanceof QueryError ? error : new QueryError('network') })
    })
  }
  return { state, submit, retry: () => { if (state.status === 'error') submit(state.query) } }
}
