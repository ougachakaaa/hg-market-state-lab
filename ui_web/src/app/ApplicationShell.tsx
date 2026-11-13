import { AppstoreOutlined, DatabaseOutlined, DotChartOutlined, ExperimentOutlined, HistoryOutlined, LineChartOutlined, MenuFoldOutlined, MenuUnfoldOutlined, ReadOutlined, TableOutlined } from '@ant-design/icons'
import { Breadcrumb, Button, Flex, Layout, Menu, Typography, theme } from 'antd'
import { useState, type ReactNode } from 'react'
import { isWorkspacePath, workspaceRoutes, workspaceAreas, workspaceCategories, type WorkspacePath, type NavigationIcon } from './routeInventory'

const icons: Record<NavigationIcon, ReactNode> = {
  overview: <AppstoreOutlined aria-hidden="true" />, data: <DatabaseOutlined aria-hidden="true" />,
  chain: <DotChartOutlined aria-hidden="true" />, research: <ExperimentOutlined aria-hidden="true" />,
  backtesting: <HistoryOutlined aria-hidden="true" />, basis: <LineChartOutlined aria-hidden="true" />,
  premium: <TableOutlined aria-hidden="true" />, explorer: <ReadOutlined aria-hidden="true" />,
}

export default function ApplicationShell({ path, navigate, href, header, children }: {
  path: WorkspacePath;
  navigate: (path: WorkspacePath) => void;
  href: (path: WorkspacePath) => string;
  header: ReactNode;
  children: ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(() => window.matchMedia('(max-width: 1199.98px)').matches)
  const { token } = theme.useToken()
  const route = workspaceRoutes.find(route => route.path === path)!
  const area = route.area
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
  const areaTitle = workspaceAreas[area].title
  const leaf = (route: typeof workspaceRoutes[number]) => ({
    key: route.path, icon: icons[route.icon],
    label: <a href={href(route.path)} onClick={event => event.preventDefault()}>{route.title}</a>,
  })
  const groupedArea = (area: '/research' | '/data') => ({
    key: `area:${area}`, label: workspaceAreas[area].title, icon: icons[workspaceAreas[area].icon],
    children: [
      ...workspaceRoutes.filter(route => route.area === area && !route.category).map(leaf),
      ...Object.entries(workspaceCategories).filter(([, category]) => category.area === area).map(([key, category]) => ({
        type: 'group' as const, key, label: category.title,
        children: workspaceRoutes.filter(route => route.category === key).map(leaf),
      })),
    ],
  })
  return <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
    <Layout.Sider collapsed={collapsed} collapsedWidth={64} width={232} breakpoint="xl"
      onBreakpoint={broken => { setCollapsed(broken); setPopupKeys([]) }} trigger={null}
      theme="dark" style={{ borderRight: `1px solid ${token.colorBorderSecondary}` }}>
      <Flex align="center" justify="center" style={{ minHeight: 64, paddingInline: token.paddingSM }}>
        <Typography.Text strong aria-label="Market State Lab">{collapsed ? 'MSL' : 'Market State Lab'}</Typography.Text>
      </Flex>
      <Menu aria-label="业务导航" mode="inline" theme="dark" triggerSubMenuAction="click" selectedKeys={[path]}
        openKeys={collapsed ? popupKeys : openKeys}
        onOpenChange={collapsed ? setPopupKeys : setOpenKeys} inlineCollapsed={collapsed}
        style={{ background: 'transparent', borderInlineEnd: 0 }}
        onClick={({ key }) => { if (isWorkspacePath(key)) navigate(key) }}
        items={[
          groupedArea('/research'), groupedArea('/data'),
          ...workspaceRoutes.filter(route => route.area === '/backtesting').map(leaf),
        ]} />
    </Layout.Sider>
    <Layout style={{ minWidth: 0 }}>
      <Layout.Header style={{ paddingInline: token.paddingLG, paddingBlock: token.paddingSM,
        lineHeight: 'normal',
        borderBottom: `1px solid ${token.colorBorderSecondary}`, height: 'auto', minHeight: 64 }}>
        <Flex justify="space-between" align="center" wrap gap="small">
          <Flex align="center" gap="middle" style={{ minWidth: 0 }}>
            <Button icon={collapsed ? <MenuUnfoldOutlined aria-hidden="true" /> : <MenuFoldOutlined aria-hidden="true" />} aria-label={collapsed ? '展开导航' : '折叠导航'} aria-expanded={!collapsed}
              onClick={toggleSidebar}>{collapsed ? '展开' : '折叠'}</Button>
            <Breadcrumb style={{ minWidth: 0, overflowWrap: 'anywhere' }} items={path === '/backtesting' ? [{ title: '回测' }] : [
              { title: path === area ? areaTitle : <a href={href(area)} onClick={(event) => { event.preventDefault(); navigate(area) }}>{areaTitle}</a> },
              { title: route.title },
            ]} />
          </Flex>
          {header}
        </Flex>
      </Layout.Header>
      <Layout.Content style={{ minWidth: 0, width: '100%', maxWidth: 1500, margin: '0 auto',
        padding: token.paddingLG, boxSizing: 'border-box' }}>
        {children}
      </Layout.Content>
    </Layout>
  </Layout>
}
