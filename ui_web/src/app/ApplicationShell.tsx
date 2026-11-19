import { GithubOutlined, AppstoreOutlined, DatabaseOutlined, ExperimentOutlined, HistoryOutlined, FileTextOutlined, MenuFoldOutlined, MenuUnfoldOutlined, ReadOutlined, ApartmentOutlined } from '@ant-design/icons'
import { Breadcrumb, Button, Flex, Layout, Menu, Typography, theme } from 'antd'
import { useState, type ReactNode } from 'react'
import { isFixedWorkspacePath, workspaceRoutes, workspaceAreas, type WorkspacePath, type NavigationIcon, type RouteMetadata } from './routeInventory'
import type { StrategyRoutes } from './strategyRoutes'

const strategyGroup = { key: 'area:strategy', title: '策略' }

const icons: Record<NavigationIcon, ReactNode> = {
  overview: <AppstoreOutlined aria-hidden="true" />, data: <DatabaseOutlined aria-hidden="true" />,
  research: <ExperimentOutlined aria-hidden="true" />,
  backtesting: <HistoryOutlined aria-hidden="true" />, instance: <FileTextOutlined aria-hidden="true" />,
  roadmap: <ApartmentOutlined aria-hidden="true" />, explorer: <ReadOutlined aria-hidden="true" />,
}

export default function ApplicationShell({ path, navigate, href, header, children, strategies, mode = 'production' }: {
  mode?: 'production' | 'static';
  path: WorkspacePath;
  strategies: StrategyRoutes;
  navigate: (path: WorkspacePath) => void;
  href: (path: WorkspacePath) => string;
  header: ReactNode;
  children: ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(() => window.matchMedia('(max-width: 1199.98px)').matches)
  const { token } = theme.useToken()
  const strategy = strategies.match(path)
  const route = workspaceRoutes.find(route => route.path === path)
  const area = route?.area
  const group = strategy ? strategyGroup.key : `area:${area}`
  const [openKeys, setOpenKeys] = useState<string[]>([group])
  const [popupKeys, setPopupKeys] = useState<string[]>([])
  const [menuPath, setMenuPath] = useState(path)
  // Reconcile navigation before rendering children, including browser history changes.
  if (menuPath !== path) {
    setMenuPath(path)
    setOpenKeys(keys => keys.includes(group) ? keys : [...keys, group])
    setPopupKeys([])
  }
  const toggleSidebar = () => {
    setCollapsed(value => !value)
    setPopupKeys([])
    setOpenKeys(keys => keys.includes(group) ? keys : [...keys, group])
  }
  const leaf = (route: { path: WorkspacePath; title: string; icon: NavigationIcon }) => ({
    key: route.path, icon: icons[route.icon],
    label: <a href={href(route.path)} onClick={event => event.preventDefault()}>{route.title}</a>,
  })
  const groupedArea = (area: keyof typeof workspaceAreas) => ({
    key: `area:${area}`, label: workspaceAreas[area].title, icon: icons[workspaceAreas[area].icon],
    children: workspaceRoutes.filter((route: RouteMetadata) => route.area === area && route.sidebarVisible && (mode === 'production' || !route.productionOnly)).map(leaf),
  })
  return <Layout style={{ height: CSS.supports?.('height', '100dvh') ? '100dvh' : '100vh', minHeight: 0,
    overflow: 'hidden', background: token.colorBgLayout }}>
    <Layout.Sider collapsed={collapsed} collapsedWidth={64} width={232} breakpoint="xl"
      onBreakpoint={broken => { setCollapsed(broken); setPopupKeys([]) }} trigger={null}
      theme="dark" style={{ borderRight: `1px solid ${token.colorBorderSecondary}` }}>
      <Flex vertical style={{ height: '100%', minHeight: 0 }}>
        <Flex align="center" justify="center" style={{ minHeight: 64, flexShrink: 0, paddingInline: token.paddingSM }}>
          <Typography.Text strong aria-label="Market State Lab">{collapsed ? 'MSL' : 'Market State Lab'}</Typography.Text>
        </Flex>
        <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          <Menu aria-label="业务导航" mode="inline" theme="dark" triggerSubMenuAction="click" selectedKeys={strategy || route?.sidebarVisible ? [path] : []}
            openKeys={collapsed ? popupKeys : openKeys}
            onOpenChange={collapsed ? setPopupKeys : setOpenKeys} inlineCollapsed={collapsed}
            style={{ background: 'transparent', borderInlineEnd: 0 }}
            onClick={({ key }) => {
              const target = isFixedWorkspacePath(key) ? key : strategies.match(key)?.path
              if (target) navigate(target)
            }}
            items={[
              { key: strategyGroup.key, label: strategyGroup.title, icon: icons.roadmap,
                children: strategies.entries.map(entry => leaf({ ...entry, icon: 'instance' })) },
              groupedArea('/data'), groupedArea('/research'),
              groupedArea('/backtesting'),
            ]} />
        </div>
      </Flex>
    </Layout.Sider>
    <Layout style={{ minWidth: 0, minHeight: 0 }}>
      <Layout.Header style={{ paddingInline: token.paddingLG, paddingBlock: token.paddingSM,
        lineHeight: 'normal', flexShrink: 0,
        borderBottom: `1px solid ${token.colorBorderSecondary}`, height: 'auto', minHeight: 64 }}>
        <Flex justify="space-between" align="center" wrap gap="small">
          <Flex align="center" gap="middle" style={{ minWidth: 0 }}>
            <Button icon={collapsed ? <MenuUnfoldOutlined aria-hidden="true" /> : <MenuFoldOutlined aria-hidden="true" />} aria-label={collapsed ? '展开导航' : '折叠导航'} aria-expanded={!collapsed}
              onClick={toggleSidebar}>{collapsed ? '展开' : '折叠'}</Button>
            <Breadcrumb style={{ minWidth: 0, overflowWrap: 'anywhere' }} items={[
              ...(strategy ? [{ title: strategyGroup.title }] : area ? [{ title: path === area ? workspaceAreas[area].title : <a href={href(area)} onClick={(event) => { event.preventDefault(); navigate(area) }}>{workspaceAreas[area].title}</a> }] : []),
              { title: strategy?.title ?? route?.title },
            ]} />
          </Flex>
          <Flex align="center" gap="middle" style={{ marginInlineStart: 'auto' }}>
            {header}
            <Button type="link" href="https://github.com/ougachakaaa/hg-market-state-lab"
              target="_blank" rel="noopener noreferrer" icon={<GithubOutlined aria-hidden="true" />}
              aria-label="查看源码（GitHub）" style={{ flexShrink: 0 }}>GitHub</Button>
          </Flex>
        </Flex>
      </Layout.Header>
      <Layout.Content style={{ minWidth: 0, minHeight: 0, overflowY: 'auto', width: '100%', maxWidth: 1500, margin: '0 auto',
        padding: token.paddingLG, boxSizing: 'border-box' }}>
        {children}
      </Layout.Content>
    </Layout>
  </Layout>
}
