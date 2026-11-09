import { Alert, Breadcrumb, Button, Card, Flex, Layout, Menu, Spin, Typography, theme } from 'antd'
import { useEffect, useState } from 'react'
import OptionChainPage from '../features/mo_option_chain'
import PremiumPlanePage from '../features/mo_option_premium'
import ResearchExplorerPage from '../features/research_explorer/page/ResearchExplorerPage'
import AppUiProvider from './AppUiProvider'
import AuthForm from './auth/AuthForm'
import { useAuthentication } from './auth/useAuthentication'
import type { CurrentUser, LoginRequest } from './auth/api/auth'
import { useWorkspaceRoute, type WorkspacePath } from './routes'

const titles: Record<WorkspacePath, string> = {
  '/research': 'Research Workspace',
  '/research/publications': 'Research Explorer',
  '/data': 'Daily Data',
  '/data/mo-option-chain': 'MO Option Chain',
  '/data/mo-premium-plane': 'MO Premium Plane',
  '/backtesting': 'Backtesting',
}

function Landing({ area, navigate }: { area: 'research' | 'data' | 'backtesting'; navigate: (path: WorkspacePath) => void }) {
  const content = {
    research: { title: 'Research Workspace', description: '浏览已发布的研究结果与可复现证据。在线研究目录和执行能力将在后续阶段接入。', next: 'Research Explorer', path: '/research/publications' as WorkspacePath },
    data: { title: 'Daily Data', description: '查看现有的 MO 数据产品。查询与导出体验将在后续阶段完善。', next: 'MO Option Chain', path: '/data/mo-option-chain' as WorkspacePath },
    backtesting: { title: 'Backtesting', description: 'Planned：策略模拟与历史验证尚未实现，目前没有回测结果。', next: '', path: '/backtesting' as WorkspacePath },
  }[area]
  return <Card><Flex vertical gap="middle">
    <Typography.Title level={2} style={{ margin: 0 }}>{content.title}</Typography.Title>
    <Typography.Paragraph type="secondary" style={{ margin: 0 }}>{content.description}</Typography.Paragraph>
    {area !== 'backtesting' && <Button type="link" style={{ alignSelf: 'flex-start', paddingInline: 0 }} onClick={() => navigate(content.path)}>{content.next} →</Button>}
  </Flex></Card>
}

function ApplicationShell({ user, signOut, path, navigate }: {
  user: CurrentUser; signOut: () => Promise<void>; path: WorkspacePath;
  navigate: (path: WorkspacePath, replace?: boolean) => void
}) {
  const [collapsed, setCollapsed] = useState(false)
  const { token } = theme.useToken()
  const area = path.startsWith('/data') ? '/data' : path.startsWith('/research') ? '/research' : '/backtesting'
  const title = titles[path]
  return <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
    <Layout.Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} width={232}
      theme="dark" style={{ background: token.colorBgContainer, borderRight: `1px solid ${token.colorBorderSecondary}` }}>
      <div style={{ padding: token.paddingLG, minHeight: 64, whiteSpace: 'nowrap', overflow: 'hidden' }}>
        <Typography.Text strong>{collapsed ? 'MSL' : 'Market State Lab'}</Typography.Text>
      </div>
      <Menu mode="inline" theme="dark" selectedKeys={[path]} defaultOpenKeys={['/data', '/research']}
        style={{ background: 'transparent', borderInlineEnd: 0 }} onClick={({ key }) => navigate(key as WorkspacePath)}
        items={[
          { key: '/data', label: 'Daily Data', children: [
            { key: '/data/mo-option-chain', label: 'MO Option Chain' },
            { key: '/data/mo-premium-plane', label: 'MO Premium Plane' },
          ] },
          { key: '/research', label: 'Research', children: [
            { key: '/research/publications', label: 'Research Explorer' },
          ] },
          { key: '/backtesting', label: 'Backtesting' },
        ]} />
      {!collapsed && <Flex vertical gap="small" style={{ padding: token.paddingLG }}>
        <Button type={area === '/data' ? 'primary' : 'text'} onClick={() => navigate('/data')}>Daily Data overview</Button>
        <Button type={area === '/research' ? 'primary' : 'text'} onClick={() => navigate('/research')}>Research Workspace</Button>
      </Flex>}
    </Layout.Sider>
    <Layout>
      <Layout.Header style={{ paddingInline: token.paddingLG, background: token.colorBgContainer,
        borderBottom: `1px solid ${token.colorBorderSecondary}`, height: 'auto', minHeight: 64 }}>
        <Flex justify="space-between" align="center" wrap gap="small">
          <Flex vertical gap={0}>
            <Breadcrumb items={path === area ? [{ title }] : [
              { title: <a href={area} onClick={(event) => { event.preventDefault(); navigate(area) }}>{titles[area]}</a> }, { title },
            ]} />
            <Typography.Text strong>{title}</Typography.Text>
          </Flex>
          <Flex align="center" gap="middle"><Typography.Text type="secondary">{user.username}</Typography.Text>
            <Button onClick={() => void signOut()}>Logout</Button></Flex>
        </Flex>
      </Layout.Header>
      <Layout.Content style={{ minWidth: 0, width: '100%', maxWidth: 1500, margin: '0 auto',
        padding: token.paddingLG, boxSizing: 'border-box' }}>
        {path === '/research' ? <Landing area="research" navigate={navigate} />
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
  const { state, check, signIn, signOut } = useAuthentication()
  const { path, navigate } = useWorkspaceRoute()
  useEffect(() => {
    if (state.status === 'authenticated' && !['/research', '/research/publications', '/data', '/data/mo-option-chain', '/data/mo-premium-plane', '/backtesting'].includes(window.location.pathname)) {
      navigate('/research', true)
    }
  }, [state.status, navigate])
  const login = async (credentials: LoginRequest) => {
    await signIn(credentials)
    if (window.location.pathname === '/' || currentPathIsUnknown()) navigate('/research', true)
  }
  if (state.status === 'authenticated') return <ApplicationShell user={state.user} signOut={signOut} path={path} navigate={navigate} />
  if (state.status === 'anonymous') return <AuthForm signIn={login} />
  return <Flex vertical align="center" justify="center" gap="middle" style={{ minHeight: '100vh', padding: 24 }}>
    {state.status === 'checking' && <><Spin /><Typography.Text>正在检查登录状态…</Typography.Text></>}
    {state.status === 'error' && <><Alert type="error" title={state.message} /><Button onClick={() => void check()}>重试登录状态检查</Button></>}
    {state.status === 'logging_out' && (state.pending ? <><Spin /><Typography.Text>正在退出…</Typography.Text></>
      : <><Alert type="error" title={state.message} /><Button onClick={() => void signOut()}>重试退出</Button></>)}
  </Flex>
}

function currentPathIsUnknown() {
  return !['/research', '/research/publications', '/data', '/data/mo-option-chain', '/data/mo-premium-plane', '/backtesting'].includes(window.location.pathname)
}

function App() {
  return <AppUiProvider><AuthenticationGate /></AppUiProvider>
}

export default App
