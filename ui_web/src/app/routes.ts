import { useCallback, useEffect, useState } from 'react'

export type WorkspacePath = '/research' | '/research/publications' | '/data' | '/data/mo-option-chain' | '/data/mo-premium-plane' | '/backtesting'

const known = new Set<WorkspacePath>([
  '/research', '/research/publications', '/data', '/data/mo-option-chain',
  '/data/mo-premium-plane', '/backtesting',
])

export function currentWorkspacePath(): WorkspacePath {
  return known.has(window.location.pathname as WorkspacePath)
    ? window.location.pathname as WorkspacePath : '/research'
}

export function useWorkspaceRoute() {
  const [path, setPath] = useState(currentWorkspacePath)
  useEffect(() => {
    const sync = () => {
      if (!known.has(window.location.pathname as WorkspacePath)) window.history.replaceState(null, '', '/research')
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
