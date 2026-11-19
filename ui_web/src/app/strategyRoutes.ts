import type { ResearchNode } from '../../research-map/definition'
import {
  isFixedWorkspacePath, isStaticWorkspacePath, roadmapAlias, strategyIdFromPath,
  type StrategyPath, type WorkspacePath,
} from './routeInventory'

export function createStrategyRoutes(nodes: readonly Pick<ResearchNode, 'kind' | 'id' | 'title'>[]) {
  const entries = nodes.filter(node => node.kind === 'strategy').map(({ id, title }) => ({
    id, title, path: `${roadmapAlias}/${id}` as StrategyPath,
  }))
  if (!entries.length) throw new Error('Strategy routes require at least one Strategy')
  const byId = new Map(entries.map(entry => [entry.id, entry]))
  const defaultPath = entries[0].path

  function match(path: string) {
    const id = strategyIdFromPath(path)
    return id === undefined ? undefined : byId.get(id)
  }

  function resolve(path: string, mode: 'production' | 'static'): WorkspacePath {
    const isFixedPath = mode === 'production' ? isFixedWorkspacePath : isStaticWorkspacePath
    return isFixedPath(path) ? path : match(path)?.path ?? defaultPath
  }

  return { entries, defaultPath, match, resolve }
}

export type StrategyRoutes = ReturnType<typeof createStrategyRoutes>
