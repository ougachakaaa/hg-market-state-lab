import { Button, Flex, Typography } from 'antd'
import { createRoot } from 'react-dom/client'
import AppUiProvider from '../../../../app/AppUiProvider'
import { useHashRoute } from '../../../../demo/shell/hashRoutes'
import { FuturesBasisPresentation, useStaticFuturesBasis } from '../../presentation'
import { embeddedReportPayload, mismatchedReportPayload, testOnlyDisclosure } from '../embeddedReportFixture'
import '../../../../index.css'

// D2-E verification harness only. It mounts the shared feature presentation with the static
// controller; it is not a second Demo page, not a D3 Example and not the public V1 entry.
export function StaticFuturesBasisHarness() {
  const { path, navigate } = useHashRoute()
  const invalid = new URLSearchParams(window.location.search).get('invalid') === '1'
  const state = useStaticFuturesBasis(invalid ? mismatchedReportPayload : embeddedReportPayload)
  if (path !== '/research/futures-basis') return <Flex vertical gap="middle" style={{ padding: 24 }}>
    <Typography.Title level={2} style={{ margin: 0 }}>静态导航目标</Typography.Title>
    <Typography.Paragraph>已通过 D1 Hash Router 导航到 <Typography.Text code data-testid="static-route">{path}</Typography.Text>。本测试入口不实现目标业务页面。</Typography.Paragraph>
    <Button onClick={() => navigate('/research/futures-basis')}>返回历史基差研究</Button>
  </Flex>
  return <Flex vertical gap="middle" style={{ padding: 24 }}>
    <Flex justify="space-between" align="center" wrap gap="small">
      <Typography.Title level={1} style={{ margin: 0, fontSize: 20 }}>D2-E 静态验证入口</Typography.Title>
      <Button onClick={() => navigate('/research')}>导航到研究总览（路由验证）</Button>
    </Flex>
    <FuturesBasisPresentation mode="static" state={state} disclosure={testOnlyDisclosure} />
  </Flex>
}

createRoot(document.getElementById('root')!).render(<AppUiProvider><StaticFuturesBasisHarness /></AppUiProvider>)
