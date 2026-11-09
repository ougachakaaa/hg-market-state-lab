import { useCallback, useEffect, useState } from 'react'

const knownPaths = [
  '/research', '/research/futures-basis', '/research/publications', '/data', '/data/mo-option-chain',
  '/data/mo-premium-plane', '/backtesting',
] as const
export type WorkspacePath = typeof knownPaths[number]
const known = new Set<string>(knownPaths)

export function isWorkspacePath(path: string): path is WorkspacePath {
  return known.has(path)
}

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
