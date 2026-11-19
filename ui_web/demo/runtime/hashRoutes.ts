import { useCallback, useEffect, useState } from 'react'
import type { StrategyRoutes } from '../../src/app/strategyRoutes'
import type { WorkspaceDestination } from '../../src/app/routeInventory'

export const staticHref = (path: WorkspaceDestination) => `#${path}`
export function hashWorkspacePath(hash: string, strategies: StrategyRoutes) {
  // Server query identity is never part of the static runtime.
  return strategies.resolve(hash.slice(1).split('?')[0], 'static')
}

export function useHashRoute(strategies: StrategyRoutes) {
  const [path, setPath] = useState(() => hashWorkspacePath(window.location.hash, strategies))
  useEffect(() => {
    const sync = () => {
      const next = hashWorkspacePath(window.location.hash, strategies)
      if (window.location.hash !== staticHref(next)) {
        window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${staticHref(next)}`)
      }
      setPath(next)
    }
    sync()
    window.addEventListener('hashchange', sync)
    window.addEventListener('popstate', sync)
    return () => {
      window.removeEventListener('hashchange', sync)
      window.removeEventListener('popstate', sync)
    }
  }, [strategies])
  const navigate = useCallback((destination: WorkspaceDestination) => {
    const next = strategies.resolve(destination, 'static')
    if (window.location.hash !== staticHref(next)) window.location.hash = staticHref(next)
    setPath(next)
  }, [strategies])
  return { path, navigate }
}
