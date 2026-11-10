import { Alert, Breadcrumb, Button, Card, Flex, Layout, Menu, Spin, Typography, theme } from 'antd'
import { useEffect, useState } from 'react'
import FuturesBasisPage from '../features/futures_basis_research/page/FuturesBasisPage'
import OptionChainPage from '../features/mo_option_chain'
import PremiumPlanePage from '../features/mo_option_premium'
import ResearchExplorerPage from '../features/research_explorer/page/ResearchExplorerPage'
import ResearchWorkspacePage from '../features/research_catalog/page/ResearchWorkspacePage'
import AppUiProvider from './AppUiProvider'
import AuthForm from './auth/AuthForm'
import { useAuthentication } from './auth/useAuthentication'
import type { CurrentUser, LoginRequest } from './auth/api/auth'
import { isWorkspacePath, useWorkspaceRoute, type WorkspacePath } from './routes'

const titles: Record<WorkspacePath, string> = {
  '/research': '研究工作台',
  '/research/futures-basis': 'Futures Basis Research',
  '/research/publications': 'Research Explorer',
  '/data': '数据总览',
  '/data/mo-option-chain': 'MO Option Chain',
  '/data/mo-premium-plane': 'MO Premium Plane',
  '/backtesting': '回测',
}

function Landing({ area, navigate }: { area: 'data' | 'backtesting'; navigate: (path: WorkspacePath) => void }) {
  return <Flex vertical gap="large">
    <header>
      <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>{area === 'data' ? '数据总览' : '回测'}</Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
        {area === 'data' ? '查看 MO 数据产品，读取结果后可复制 JSON 或导出数据。'
          : '规划中：策略模拟与历史验证尚未实现，目前没有回测结果。'}
      </Typography.Paragraph>
    </header>
    {area === 'data' && <Flex gap="middle" wrap>
      <Card title="MO Option Chain" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Paragraph type="secondary">查看期权链价格分布与同到期 Futures 参考。</Typography.Paragraph>
        <Button onClick={() => navigate('/data/mo-option-chain')}>打开 MO Option Chain</Button>
      </Card>
      <Card title="MO Premium Plane" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Paragraph type="secondary">查看多维权利金稀疏数值平面。</Typography.Paragraph>
        <Button onClick={() => navigate('/data/mo-premium-plane')}>打开 MO Premium Plane</Button>
      </Card>
    </Flex>}
  </Flex>
}

function ApplicationShell({ user, signOut, path, navigate }: {
  user: CurrentUser; signOut: () => Promise<void>; path: WorkspacePath;
  navigate: (path: WorkspacePath, replace?: boolean) => void
}) {
  const [collapsed, setCollapsed] = useState(() => window.matchMedia('(max-width: 1199.98px)').matches)
  const { token } = theme.useToken()
  const area = path.startsWith('/data') ? '/data' : path.startsWith('/research') ? '/research' : '/backtesting'
  const group = area === '/backtesting' ? null : `area:${area}`
  const [openKeys, setOpenKeys] = useState<string[]>(group ? [group] : [])
  const [popupKeys, setPopupKeys] = useState<string[]>([])
  const [menuPath, setMenuPath] = useState(path)
  // Reconcile navigation before rendering children, including browser history changes.
  if (menuPath !== path) {
    setMenuPath(path)
    if (group) setOpenKeys(keys => keys.includes(group) ? keys : [...keys, group])
    setPopupKeys([])
  }
  const toggleSidebar = () => {
    setCollapsed(value => !value)
    setPopupKeys([])
    if (group) setOpenKeys(keys => keys.includes(group) ? keys : [...keys, group])
  }
  const areaTitle = area === '/research' ? '研究' : area === '/data' ? '日常数据' : '回测'
  return <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
    <Layout.Sider collapsed={collapsed} collapsedWidth={64} width={232} breakpoint="xl"
      onBreakpoint={broken => { setCollapsed(broken); setPopupKeys([]) }} trigger={null}
      theme="dark" style={{ background: token.colorBgContainer, borderRight: `1px solid ${token.colorBorderSecondary}` }}>
      <Flex align="center" justify="center" style={{ minHeight: 64, paddingInline: token.paddingSM }}>
        <Typography.Text strong aria-label="Market State Lab">{collapsed ? 'MSL' : 'Market State Lab'}</Typography.Text>
      </Flex>
      <Menu aria-label="业务导航" mode="inline" theme="dark" triggerSubMenuAction="click" selectedKeys={[path]}
        openKeys={collapsed ? popupKeys : openKeys}
        onOpenChange={collapsed ? setPopupKeys : setOpenKeys} inlineCollapsed={collapsed}
        style={{ background: 'transparent', borderInlineEnd: 0 }}
        onClick={({ key }) => { if (isWorkspacePath(key)) navigate(key) }}
        items={[
          { key: 'area:/research', label: '研究', icon: <span aria-hidden="true">研</span>, children: [
            { key: '/research', label: '研究工作台' },
            { key: '/research/publications', label: 'Research Explorer' },
            { key: '/research/futures-basis', label: 'Futures Basis Research' },
          ] },
          { key: 'area:/data', label: '日常数据', icon: <span aria-hidden="true">数</span>, children: [
            { key: '/data', label: '数据总览' },
            { key: '/data/mo-option-chain', label: 'MO Option Chain' },
            { key: '/data/mo-premium-plane', label: 'MO Premium Plane' },
          ] },
          { key: '/backtesting', label: '回测 · 规划中', icon: <span aria-hidden="true">测</span> },
        ]} />
    </Layout.Sider>
    <Layout style={{ minWidth: 0 }}>
      <Layout.Header style={{ paddingInline: token.paddingLG, paddingBlock: token.paddingSM,
        background: token.colorBgContainer, lineHeight: 'normal',
        borderBottom: `1px solid ${token.colorBorderSecondary}`, height: 'auto', minHeight: 64 }}>
        <Flex justify="space-between" align="center" wrap gap="small">
          <Flex align="center" gap="middle" style={{ minWidth: 0 }}>
            <Button aria-label={collapsed ? '展开导航' : '折叠导航'} aria-expanded={!collapsed}
              onClick={toggleSidebar}>{collapsed ? '展开' : '折叠'}</Button>
            <Breadcrumb items={path === '/backtesting' ? [{ title: '回测' }] : [
              { title: path === area ? areaTitle : <a href={area} onClick={(event) => { event.preventDefault(); navigate(area) }}>{areaTitle}</a> },
              { title: titles[path] },
            ]} />
          </Flex>
          <Flex align="center" gap="middle" wrap>
            <Typography.Text type="secondary" style={{ overflowWrap: 'anywhere' }}>{user.username}</Typography.Text>
            <Button onClick={() => void signOut()}>退出登录</Button>
          </Flex>
        </Flex>
      </Layout.Header>
      <Layout.Content style={{ minWidth: 0, width: '100%', maxWidth: 1500, margin: '0 auto',
        padding: token.paddingLG, boxSizing: 'border-box' }}>
        {path === '/research' ? <ResearchWorkspacePage openExplorer={() => navigate('/research/publications')} openFuturesBasis={() => navigate('/research/futures-basis')} />
          : path === '/research/futures-basis' ? <FuturesBasisPage />
          : path === '/research/publications' ? <ResearchExplorerPage />
            : path === '/data' ? <Landing area="data" navigate={navigate} />
              : path === '/data/mo-option-chain' ? <OptionChainPage />
                : path === '/data/mo-premium-plane' ? <PremiumPlanePage />
                  : <Landing area="backtesting" navigate={navigate} />}
      </Layout.Content>
    </Layout>
  </Layout>
}

function AuthenticationGate() {
  const { token } = theme.useToken()
  const { state, check, signIn, signOut } = useAuthentication()
  const { path, navigate } = useWorkspaceRoute()
  useEffect(() => {
    if (state.status === 'authenticated' && !isWorkspacePath(window.location.pathname)) {
      navigate('/research', true)
    }
  }, [state.status, navigate])
  const login = async (credentials: LoginRequest) => {
    await signIn(credentials)
    if (!isWorkspacePath(window.location.pathname)) navigate('/research', true)
  }
  if (state.status === 'authenticated') return <ApplicationShell user={state.user} signOut={signOut} path={path} navigate={navigate} />
  if (state.status === 'anonymous') return <AuthForm signIn={login} />
  return <Flex vertical align="center" justify="center" gap="middle" style={{ minHeight: '100vh', padding: 24,
    boxSizing: 'border-box', background: token.colorBgLayout }}>
    {state.status === 'checking' && <><Spin /><Typography.Text>正在检查登录状态…</Typography.Text></>}
    {state.status === 'error' && <><Alert type="error" title={state.message} /><Button onClick={() => void check()}>重试登录状态检查</Button></>}
    {state.status === 'logging_out' && (state.pending ? <><Spin /><Typography.Text>正在退出…</Typography.Text></>
      : <><Alert type="error" title={state.message} /><Button onClick={() => void signOut()}>重试退出</Button></>)}
  </Flex>
}

function App() {
  return <AppUiProvider><AuthenticationGate /></AppUiProvider>
}

export default App
