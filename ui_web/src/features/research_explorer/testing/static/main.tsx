import { Flex, Typography } from 'antd'
import { createRoot } from 'react-dom/client'
import AppUiProvider from '../../../../app/AppUiProvider'
import { ResearchExplorerPresentation, useStaticExplorer } from '../../presentation'
import { embeddedPublicationSet } from '../publicationFixture'
import '../../../../index.css'

const TEST_ONLY_DISCLOSURE =
  '静态测试数据 · 非正式 D3 Publication Example · 未查询在线 Publication Store · 未执行研究 · 不代表实时服务或 Provider 状态；示例 Provenance / Source Metadata 不证明真实市场来源。'
const empty = new URLSearchParams(window.location.search).get('empty') === '1'
const payload = empty
  ? { pages: [{ data: [], next_cursor: null }], manifests: [], analyses: [], views: [] }
  : embeddedPublicationSet

export function StaticExplorerHarness() {
  const controller = useStaticExplorer(payload)
  return <Flex vertical gap="middle" style={{ padding: 24 }}>
    <Typography.Title level={1} style={{ margin: 0, fontSize: 20 }}>D2-D 静态验证入口</Typography.Title>
    <ResearchExplorerPresentation controller={controller} mode="static" sourceDisclosure={TEST_ONLY_DISCLOSURE} />
  </Flex>
}

createRoot(document.getElementById('root')!).render(<AppUiProvider><StaticExplorerHarness /></AppUiProvider>)
