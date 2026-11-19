import DailyCalendarSpreadPage from '../features/futures_calendar_spread/page/DailyPage'
import RelativeValuePage from '../features/calendar_spread_relative_value/page/RelativeValuePage'
import { LogoutOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Spin, Typography, theme } from 'antd'
import { Activity, useState, type ReactNode } from 'react'
import FuturesBasisPage from '../features/futures_basis_research/page/FuturesBasisPage'
import OptionChainPage from '../features/mo_option_chain'
import PremiumPlanePage from '../features/mo_option_premium'
import ResearchExplorerPage from '../features/research_explorer/page/ResearchExplorerPage'
import ResearchWorkspacePage from '../features/research_catalog/page/ResearchWorkspacePage'
import { StrategyResearchMap } from '../features/strategy_research_map/presentation'
import BacktestingPage from '../features/backtesting/page/BacktestingPage'
import AppUiProvider from './AppUiProvider'
import ApplicationShell from './ApplicationShell'
import BacktestingOverview from './BacktestingOverview'
import DailyDataLanding from './DailyDataLanding'
import AuthForm from './auth/AuthForm'
import { useAuthentication } from './auth/useAuthentication'
import { useWorkspaceRoute } from './routes'
import { useRunNavigation } from './useRunNavigation'
import map from 'virtual:strategy-research-map'
import type { WorkspaceDestination, WorkspacePath } from './routeInventory'
import { createStrategyRoutes } from './strategyRoutes'

const strategies = createStrategyRoutes(map.nodes)

function OnlineWorkspace({ header, path, navigate: navigateRoute }: {
  header: ReactNode; path: WorkspacePath;
  navigate: (path: WorkspaceDestination, replace?: boolean, runId?: string) => void;
}) {
  const navigate = useRunNavigation(navigateRoute)
  const strategy = strategies.match(path)
  const active = path === '/backtesting/futures-roll-long'
  const [visited, setVisited] = useState(active)
  if (active && !visited) setVisited(true)
  return <ApplicationShell strategies={strategies} path={path} navigate={navigate} href={path => path} header={header}>
    {strategy ? <StrategyResearchMap key={strategy.id} map={map} strategyId={strategy.id} navigate={navigate} href={path => path} />
      : path === '/research' ? <ResearchWorkspacePage openExplorer={() => navigate('/research/publications')} openFuturesBasis={() => navigate('/research/futures-basis')} openCalendarSpread={() => navigate('/research/calendar-spread-relative-value')} />
      : path === '/research/calendar-spread-relative-value' ? <RelativeValuePage />
      : path === '/data/futures-calendar-spread' ? <DailyCalendarSpreadPage />
      : path === '/research/futures-basis' ? <FuturesBasisPage />
        : path === '/research/publications' ? <ResearchExplorerPage />
          : path === '/data' ? <DailyDataLanding navigate={navigate} />
            : path === '/data/mo-option-chain' ? <OptionChainPage />
              : path === '/data/mo-premium-plane' ? <PremiumPlanePage />
                : path === '/backtesting' ? <BacktestingOverview navigate={navigate} />
                  : null}
    {(visited || active) && <Activity mode={active ? 'visible' : 'hidden'}>
      <BacktestingPage active={active} />
    </Activity>}
  </ApplicationShell>
}

function AuthenticationGate() {
  const { token } = theme.useToken()
  const { state, check, signIn, signOut } = useAuthentication()
  const ready = state.status === 'local' || state.status === 'authenticated'
  const { path, navigate } = useWorkspaceRoute(strategies, ready)
  if (state.status === 'local' || state.status === 'authenticated') {
    const header = state.status === 'local' ? <Typography.Text type="secondary">本地模式</Typography.Text> :
      <Flex align="center" gap="middle" wrap>
        <Typography.Text type="secondary" style={{ overflowWrap: 'anywhere' }}>{state.user.username}</Typography.Text>
        <Button icon={<LogoutOutlined aria-hidden="true" />} onClick={() => void signOut()}>退出登录</Button>
      </Flex>
    return <OnlineWorkspace header={header} path={path} navigate={navigate} />
  }
  if (state.status === 'anonymous') return <AuthForm signIn={signIn} />
  return <Flex vertical align="center" justify="center" gap="middle" style={{ minHeight: '100vh', padding: 24,
    boxSizing: 'border-box', background: token.colorBgLayout }}>
    {state.status === 'checking' && <><Spin /><Typography.Text>正在检查工作区访问状态…</Typography.Text></>}
    {state.status === 'error' && <><Alert type="error" title={state.message} /><Button icon={<ReloadOutlined aria-hidden="true" />} onClick={() => void check()}>重试访问检查</Button></>}
    {state.status === 'logging_out' && (state.pending ? <><Spin /><Typography.Text>正在退出…</Typography.Text></>
      : <><Alert type="error" title={state.message} /><Button icon={<ReloadOutlined aria-hidden="true" />} onClick={() => void signOut()}>重试退出</Button></>)}
  </Flex>
}

function App() {
  return <AppUiProvider><AuthenticationGate /></AppUiProvider>
}

export default App
