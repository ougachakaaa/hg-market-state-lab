// Pure application identities and discovery metadata. No runtime/router imports.
export type NavigationIcon = 'overview' | 'data' | 'research' | 'backtesting' | 'instance' | 'explorer' | 'roadmap'
export const workspaceAreas = {
  '/research': { title: '研究', icon: 'research' },
  '/data': { title: '日常数据', icon: 'data' },
  '/backtesting': { title: '回测', icon: 'backtesting' },
} as const
export type RouteMetadata = {
  path: string; title: string; area: keyof typeof workspaceAreas;
  icon: NavigationIcon; sidebarVisible: boolean; productionOnly?: boolean;
}
export const roadmapAlias = '/roadmap'
export type StrategyPath = `/roadmap/${string}`

export function strategyIdFromPath(path: string): string | undefined {
  return /^\/roadmap\/(strategy-[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$/.exec(path)?.[1]
}

export const workspaceRoutes = [
  { path: '/research', title: '研究总览', area: '/research', icon: 'overview', sidebarVisible: true },
  { path: '/research/futures-basis', title: '历史基差研究', area: '/research', icon: 'instance', sidebarVisible: true },
  { path: '/research/calendar-spread-relative-value', title: '历史跨期相对价值研究', area: '/research', icon: 'instance', sidebarVisible: true },
  { path: '/research/publications', title: 'Research Explorer', area: '/research', icon: 'explorer', sidebarVisible: false },
  { path: '/data', title: '数据总览', area: '/data', icon: 'overview', sidebarVisible: true },
  { path: '/data/mo-option-chain', title: 'MO Option Chain', area: '/data', icon: 'instance', sidebarVisible: true },
  { path: '/data/mo-premium-plane', title: 'MO Premium Plane', area: '/data', icon: 'instance', sidebarVisible: true },
  { path: '/data/futures-calendar-spread', title: 'Futures Calendar Spread', area: '/data', icon: 'instance', sidebarVisible: true },
  { path: '/backtesting', title: '回测总览', area: '/backtesting', icon: 'overview', sidebarVisible: true },
  { path: '/backtesting/futures-roll-long', title: '期货展期做多回测', area: '/backtesting', icon: 'instance', sidebarVisible: true },
] as const satisfies readonly RouteMetadata[]
export type FixedWorkspacePath = typeof workspaceRoutes[number]['path']
export type WorkspacePath = FixedWorkspacePath | StrategyPath
export type WorkspaceDestination = WorkspacePath | typeof roadmapAlias
export type WorkspaceReferencePath = FixedWorkspacePath | typeof roadmapAlias
const paths = new Set<string>(workspaceRoutes.map(route => route.path))
export function isFixedWorkspacePath(path: string): path is FixedWorkspacePath { return paths.has(path) }

export function isStaticWorkspacePath(path: string): path is FixedWorkspacePath {
  return workspaceRoutes.some(route => route.path === path && !('productionOnly' in route && route.productionOnly))
}

export function isWorkspaceReferencePath(path: string): path is WorkspaceReferencePath {
  return path === roadmapAlias || isStaticWorkspacePath(path)
}
