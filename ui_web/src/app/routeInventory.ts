// Pure application identities and discovery metadata. No runtime/router imports.
export type NavigationIcon = 'overview' | 'data' | 'chain' | 'research' | 'backtesting' | 'basis' | 'premium' | 'explorer'
export const workspaceAreas = {
  '/research': { title: '研究', icon: 'research' },
  '/data': { title: '日常数据', icon: 'data' },
  '/backtesting': { title: '回测', icon: 'backtesting' },
} as const
export const workspaceCategories = {
  'descriptive-research': { area: '/research', title: 'DESCRIPTIVE RESEARCH' },
} as const

type RouteMetadata = {
  path: string; title: string; area: keyof typeof workspaceAreas;
  icon: NavigationIcon; category?: keyof typeof workspaceCategories;
}
export const workspaceRoutes = [
  { path: '/research', title: '研究总览', area: '/research', icon: 'overview', category: undefined },
  { path: '/research/futures-basis', title: '历史基差研究', area: '/research', icon: 'basis', category: 'descriptive-research' },
  { path: '/research/publications', title: 'Research Explorer', area: '/research', icon: 'explorer', category: undefined },
  { path: '/data', title: '数据总览', area: '/data', icon: 'data', category: undefined },
  { path: '/data/mo-option-chain', title: 'MO Option Chain', area: '/data', icon: 'chain', category: undefined },
  { path: '/data/mo-premium-plane', title: 'MO Premium Plane', area: '/data', icon: 'premium', category: undefined },
  { path: '/backtesting', title: '回测', area: '/backtesting', icon: 'backtesting', category: undefined },
] as const satisfies readonly RouteMetadata[]
export type WorkspacePath = typeof workspaceRoutes[number]['path']
const paths = new Set<string>(workspaceRoutes.map(route => route.path))
export function isWorkspacePath(path: string): path is WorkspacePath { return paths.has(path) }
