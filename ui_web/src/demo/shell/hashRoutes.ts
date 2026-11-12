import { useCallback, useEffect, useState } from 'react'
import { isWorkspacePath, type WorkspacePath } from '../../app/routeInventory'

export const staticHref = (path: WorkspacePath) => `#${path}`
export function hashWorkspacePath(hash: string): WorkspacePath {
  // Server query identity is never part of the static runtime.
  const path = hash.slice(1).split('?')[0]
  return isWorkspacePath(path) ? path : '/research'
}
function normalizeHash() {
  const path = hashWorkspacePath(window.location.hash)
  if (window.location.hash !== staticHref(path)) {
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${staticHref(path)}`)
  }
  return path
}
export function useHashRoute() {
  const [path, setPath] = useState(() => hashWorkspacePath(window.location.hash))
  useEffect(() => {
    const sync = () => setPath(normalizeHash())
    sync()
    window.addEventListener('hashchange', sync)
    window.addEventListener('popstate', sync)
    return () => {
      window.removeEventListener('hashchange', sync)
      window.removeEventListener('popstate', sync)
    }
  }, [])
  const navigate = useCallback((next: WorkspacePath) => {
    if (window.location.hash !== staticHref(next)) window.location.hash = staticHref(next)
    setPath(next)
  }, [])
  return { path, navigate }
}
