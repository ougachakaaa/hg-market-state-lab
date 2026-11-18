import DailyCalendarSpreadPage from '../features/futures_calendar_spread/page/DailyPage'
import RelativeValuePage from '../features/calendar_spread_relative_value/page/RelativeValuePage'
import { LogoutOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Spin, Typography, theme } from 'antd'
import { Activity, useEffect, useState } from 'react'
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
import type { CurrentUser, LoginRequest } from './auth/api/auth'
import { useWorkspaceRoute } from './routes'
import { useRunNavigation } from './useRunNavigation'
import { defaultWorkspacePath, isWorkspacePath, type WorkspacePath } from './routeInventory'

function ProductionWorkspace({ user, signOut, path, navigate: navigateRoute }: {
  user: CurrentUser; signOut: () => Promise<void>; path: WorkspacePath;
  navigate: (path: WorkspacePath, replace?: boolean, runId?: string) => void;
}) {
  const navigate = useRunNavigation(navigateRoute)
  const active = path === '/backtesting/futures-roll-long'
  const [visited, setVisited] = useState(active)
  if (active && !visited) setVisited(true)
  return <ApplicationShell path={path} navigate={navigate} href={path => path} header={
    <Flex align="center" gap="middle" wrap>
      <Typography.Text type="secondary" style={{ overflowWrap: 'anywhere' }}>{user.username}</Typography.Text>
      <Button icon={<LogoutOutlined aria-hidden="true" />} onClick={() => void signOut()}>退出登录</Button>
    </Flex>
  }>
    {path === defaultWorkspacePath ? <StrategyResearchMap navigate={navigate} href={path => path} />
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
  const { path, navigate } = useWorkspaceRoute()
  useEffect(() => {
    if (state.status === 'authenticated' && !isWorkspacePath(window.location.pathname)) {
      navigate(defaultWorkspacePath, true)
    }
  }, [state.status, navigate])
  const login = async (credentials: LoginRequest) => {
    await signIn(credentials)
    if (!isWorkspacePath(window.location.pathname)) navigate(defaultWorkspacePath, true)
  }
  if (state.status === 'authenticated') return <ProductionWorkspace user={state.user} signOut={signOut} path={path} navigate={navigate} />
  if (state.status === 'anonymous') return <AuthForm signIn={login} />
  return <Flex vertical align="center" justify="center" gap="middle" style={{ minHeight: '100vh', padding: 24,
    boxSizing: 'border-box', background: token.colorBgLayout }}>
    {state.status === 'checking' && <><Spin /><Typography.Text>正在检查登录状态…</Typography.Text></>}
    {state.status === 'error' && <><Alert type="error" title={state.message} /><Button icon={<ReloadOutlined aria-hidden="true" />} onClick={() => void check()}>重试登录状态检查</Button></>}
    {state.status === 'logging_out' && (state.pending ? <><Spin /><Typography.Text>正在退出…</Typography.Text></>
      : <><Alert type="error" title={state.message} /><Button icon={<ReloadOutlined aria-hidden="true" />} onClick={() => void signOut()}>重试退出</Button></>)}
  </Flex>
}

function App() {
  return <AppUiProvider><AuthenticationGate /></AppUiProvider>
}

export default App
