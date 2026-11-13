import { Button, Flex, Typography } from 'antd'
import { createRoot } from 'react-dom/client'
import AppUiProvider from '../../../src/app/AppUiProvider'
import { useHashRoute } from '../../../src/demo/shell/hashRoutes'
import { ResearchOverviewPresentation, useStaticCatalog } from '../../../src/features/research_catalog/presentation'
import { embeddedCatalog } from '../../../src/features/research_catalog/testing/catalogFixture'
import '../../../src/index.css'

const TEST_ONLY_DISCLOSURE =
  '静态测试数据 · 非正式 D3 Capability Example · 非在线发现 · 浏览器未执行认证 GET，也未探测 Provider、Token 或缓存。'

export function StaticCatalogHarness() {
  const { path, navigate } = useHashRoute()
  const controller = useStaticCatalog(embeddedCatalog)
  if (path !== '/research') return <Flex vertical gap="middle" style={{ padding: 24 }}>
    <Typography.Title level={2} style={{ margin: 0 }}>静态导航目标</Typography.Title>
    <Typography.Paragraph>已通过 D1 Hash Router 导航到 <Typography.Text code data-testid="static-route">{path}</Typography.Text>。本测试入口不实现目标业务页面。</Typography.Paragraph>
    <Button onClick={() => navigate('/research')}>返回研究总览</Button>
  </Flex>
  return <Flex vertical gap="middle" style={{ padding: 24 }}>
    <Typography.Title level={1} style={{ margin: 0, fontSize: 20 }}>D2-C 静态验证入口</Typography.Title>
    <ResearchOverviewPresentation controller={controller} mode="static"
      navigation={{
        openExplorer: () => navigate('/research/publications'),
        openFuturesBasis: () => navigate('/research/futures-basis'),
      }}
      sourceDisclosure={TEST_ONLY_DISCLOSURE} />
  </Flex>
}

createRoot(document.getElementById('root')!).render(<AppUiProvider><StaticCatalogHarness /></AppUiProvider>)
