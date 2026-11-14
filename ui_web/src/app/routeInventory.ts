// Pure application identities and discovery metadata. No runtime/router imports.
export type NavigationIcon = 'overview' | 'data' | 'chain' | 'research' | 'backtesting' | 'basis' | 'premium' | 'explorer'
export const workspaceAreas = {
  '/research': { title: '研究', icon: 'research' },
  '/data': { title: '日常数据', icon: 'data' },
  '/backtesting': { title: '回测', icon: 'backtesting' },
} as const
type RouteMetadata = {
  path: string; title: string; area: keyof typeof workspaceAreas;
  icon: NavigationIcon; sidebarVisible: boolean;
}
export const workspaceRoutes = [
  { path: '/research', title: '研究总览', area: '/research', icon: 'overview', sidebarVisible: true },
  { path: '/research/futures-basis', title: '历史基差研究', area: '/research', icon: 'basis', sidebarVisible: true },
  { path: '/research/publications', title: 'Research Explorer', area: '/research', icon: 'explorer', sidebarVisible: false },
  { path: '/data', title: '数据总览', area: '/data', icon: 'data', sidebarVisible: true },
  { path: '/data/mo-option-chain', title: 'MO Option Chain', area: '/data', icon: 'chain', sidebarVisible: true },
  { path: '/data/mo-premium-plane', title: 'MO Premium Plane', area: '/data', icon: 'premium', sidebarVisible: true },
  { path: '/backtesting', title: '回测', area: '/backtesting', icon: 'backtesting', sidebarVisible: true },
] as const satisfies readonly RouteMetadata[]
export type WorkspacePath = typeof workspaceRoutes[number]['path']
const paths = new Set<string>(workspaceRoutes.map(route => route.path))
export function isWorkspacePath(path: string): path is WorkspacePath { return paths.has(path) }
