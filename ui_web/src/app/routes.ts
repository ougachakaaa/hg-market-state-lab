import { useCallback, useEffect, useState } from 'react'

import { isWorkspacePath, type WorkspacePath } from './routeInventory'

export function currentWorkspacePath(): WorkspacePath {
  const url = new URL(window.location.href)
  if (url.pathname === '/backtesting' && url.searchParams.has('run_id')) {
    url.pathname = '/backtesting/futures-roll-long'
    window.history.replaceState(null, '', url.pathname + url.search + url.hash)
  }
  return isWorkspacePath(window.location.pathname)
    ? window.location.pathname : '/research'
}

export function useWorkspaceRoute() {
  const [path, setPath] = useState(currentWorkspacePath)
  useEffect(() => {
    const sync = () => {
      if (!isWorkspacePath(window.location.pathname)) window.history.replaceState(null, '', '/research')
      setPath(currentWorkspacePath())
    }
    window.addEventListener('popstate', sync)
    return () => window.removeEventListener('popstate', sync)
  }, [])
  // Optional identity is supplied only by authenticated menu navigation. History
  // synchronization and direct URL restoration never consult navigation memory.
  const navigate = useCallback((next: WorkspacePath, replace = false, runId?: string) => {
    if (window.location.pathname !== next) {
      const query = runId ? `?${new URLSearchParams({ run_id: runId })}` : ''
      window.history[replace ? 'replaceState' : 'pushState'](null, '', next + query)
    }
    setPath(next)
  }, [])
  return { path, navigate }
}
