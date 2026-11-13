import { useCallback, useEffect, useState } from 'react'

import { isWorkspacePath, type WorkspacePath } from './routeInventory'

export function currentWorkspacePath(): WorkspacePath {
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
  const navigate = useCallback((next: WorkspacePath, replace = false) => {
    if (window.location.pathname !== next) window.history[replace ? 'replaceState' : 'pushState'](null, '', next)
    setPath(next)
  }, [])
  return { path, navigate }
}
