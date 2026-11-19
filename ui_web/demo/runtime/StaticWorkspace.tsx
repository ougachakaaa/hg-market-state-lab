import { useMemo, type ComponentType, type ReactNode } from 'react'
import { Flex, Typography } from 'antd'
import { StrategyResearchMap } from '../../src/features/strategy_research_map/presentation'
import map from 'virtual:strategy-research-map'
import { isFixedWorkspacePath, type WorkspacePath, type FixedWorkspacePath } from '../../src/app/routeInventory'
import { createStrategyRoutes } from '../../src/app/strategyRoutes'
import ApplicationShell from '../../src/app/ApplicationShell'
import AppUiProvider from '../../src/app/AppUiProvider'
import BacktestingOverview from '../../src/app/BacktestingOverview'
import DailyDataLanding from '../../src/app/DailyDataLanding'
import { staticHref, useHashRoute } from './hashRoutes'
import { bundleStore, resource, type Resource } from './resources'
import { AsyncContent } from './AsyncContent'
import type { BundleLoaders } from './results'
import type { StaticPageProps } from './pages/types'

const strategies = createStrategyRoutes(map.nodes)

// Explicit consumer mapping, exhaustively checked against the formal route inventory.
// These imports load code only; Bundle data remains in the selected consumer's store.
const pages = {
  '/data/futures-calendar-spread': resource(() => import('./pages/DailySpread')),
  '/research/calendar-spread-relative-value': resource(() => import('./pages/CalendarSpread')),
  '/research': resource(() => import('./pages/Catalog')),
  '/research/futures-basis': resource(() => import('./pages/Basis')),
  '/research/publications': resource(() => import('./pages/Explorer')),
  '/data/mo-option-chain': resource(() => import('./pages/Chain')),
  '/data/mo-premium-plane': resource(() => import('./pages/Premium')),
  '/backtesting/futures-roll-long': resource(() => import('./pages/Backtesting')),
} satisfies Record<Exclude<FixedWorkspacePath, '/data' | '/backtesting'>, Resource<{ default: ComponentType<StaticPageProps> }>>

function StaticPage({ path, ...props }: StaticPageProps & { path: WorkspacePath }) {
  if (!isFixedWorkspacePath(path)) {
    const strategy = strategies.match(path)!
    return <StrategyResearchMap map={map} strategyId={strategy.id} navigate={props.navigate} href={staticHref} />
  }
  if (path === '/data') return <DailyDataLanding mode="static" navigate={props.navigate} />
  if (path === '/backtesting') return <BacktestingOverview navigate={props.navigate} />
  return <AsyncContent resource={pages[path]}>{({ default: Page }) => <Page {...props} />}</AsyncContent>
}
export function StaticWorkspace({ loaders, header, notice }: { loaders: BundleLoaders; header: string; notice: ReactNode }) {
  const { path, navigate } = useHashRoute(strategies)
  const store = useMemo(() => bundleStore(loaders), [loaders])
  return <AppUiProvider><ApplicationShell strategies={strategies} mode="static" path={path} navigate={navigate} href={staticHref} header={<Typography.Text type="secondary">{header}</Typography.Text>}>
    <Flex vertical gap="large" style={{ minWidth: 0, maxWidth: '100%', overflowX: 'auto' }}>
      {notice}
      <StaticPage key={path} path={path} store={store} navigate={navigate} />
    </Flex>
  </ApplicationShell></AppUiProvider>
}
