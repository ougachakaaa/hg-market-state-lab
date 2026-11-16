import { useCallback, useRef } from 'react'
import type { WorkspacePath } from './routeInventory'

type RunPath = '/backtesting/futures-roll-long' | '/research/futures-basis'
function isRunPath(path: string): path is RunPath {
  return path === '/backtesting/futures-roll-long' || path === '/research/futures-basis'
}

type Navigate = (path: WorkspacePath, replace?: boolean, runId?: string) => void

// Mount only within ProductionWorkspace: its authentication lifetime owns memory.
export function useRunNavigation(navigate: Navigate) {
  const identities = useRef<Partial<Record<RunPath, string>>>({})
  return useCallback((next: WorkspacePath, replace = false) => {
    const current = new URL(window.location.href)
    // Features write accepted identities through History API without rerendering
    // Application. Sample the URL at the navigation boundary, never a render snapshot.
    if (isRunPath(current.pathname)) {
      const id = current.searchParams.get('run_id')
      if (id) identities.current[current.pathname] = id
      else delete identities.current[current.pathname]
    }
    navigate(next, replace, isRunPath(next) ? identities.current[next] : undefined)
  }, [navigate])
}
