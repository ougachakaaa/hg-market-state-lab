import { Alert, Flex, Typography } from 'antd'
import ApplicationShell from '../../../src/app/ApplicationShell'
import AppUiProvider from '../../../src/app/AppUiProvider'
import DailyDataLanding from '../../../src/app/DailyDataLanding'
import { workspaceRoutes } from '../../../src/app/routeInventory'
import { staticHref, useHashRoute } from '../../../src/demo/shell/hashRoutes'

export default function StaticShellHarness() {
  const { path, navigate } = useHashRoute()
  const route = workspaceRoutes.find(route => route.path === path)!
  return <AppUiProvider>
    <ApplicationShell path={path} navigate={navigate} href={staticHref} header={
      <Typography.Text type="secondary">D1 静态 Shell 验证 · 匿名 · 无业务数据</Typography.Text>
    }>
      <Flex vertical gap="large">
        <Alert type="info" title="D1 验证入口" description="仅验证共享布局与路由；占位内容不是 Demo V2 业务页面，也不提供 Synthetic Example 结果。" />
        {path === '/data' ? <DailyDataLanding navigate={navigate} /> : <section aria-label="路由验证内容" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
          <Typography.Title level={1}>{route.title}</Typography.Title>
          <Typography.Paragraph>当前路由：<code data-testid="route-identity">{path}</code></Typography.Paragraph>
          <Typography.Paragraph type="secondary">业务展示与静态 Example 接入留待后续任务。</Typography.Paragraph>
        </section>}
      </Flex>
    </ApplicationShell>
  </AppUiProvider>
}
