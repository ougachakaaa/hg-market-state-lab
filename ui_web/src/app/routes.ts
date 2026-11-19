import { useCallback, useEffect, useState } from 'react'

import type { StrategyRoutes } from './strategyRoutes'
import type { WorkspaceDestination } from './routeInventory'

function locationRoute(strategies: StrategyRoutes, normalize = false) {
  const url = new URL(window.location.href)
  if (url.pathname === '/backtesting' && url.searchParams.has('run_id')) {
    const path = '/backtesting/futures-roll-long'
    if (normalize) window.history.replaceState(null, '', path + url.search + url.hash)
    return path
  }
  const path = strategies.resolve(url.pathname, 'production')
  if (normalize && path !== url.pathname) window.history.replaceState(null, '', path)
  return path
}

export function useWorkspaceRoute(strategies: StrategyRoutes, authenticated = true) {
  const [path, setPath] = useState(() => locationRoute(strategies))
  useEffect(() => {
    const sync = () => setPath(locationRoute(strategies, authenticated))
    sync()
    window.addEventListener('popstate', sync)
    return () => window.removeEventListener('popstate', sync)
  }, [strategies, authenticated])

  // Optional Run identity is supplied only by authenticated menu navigation.
  const navigate = useCallback((destination: WorkspaceDestination, replace = false, runId?: string) => {
    const next = strategies.resolve(destination, 'production')
    if (window.location.pathname !== next) {
      const query = runId ? `?${new URLSearchParams({ run_id: runId })}` : ''
      window.history[replace ? 'replaceState' : 'pushState'](null, '', next + query)
    }
    setPath(next)
  }, [strategies])
  return { path, navigate }
}
