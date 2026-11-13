import { useState } from 'react'
import { Alert, Flex, Select, Typography } from 'antd'
import ApplicationShell from '../../app/ApplicationShell'
import AppUiProvider from '../../app/AppUiProvider'
import DailyDataLanding from '../../app/DailyDataLanding'
import { staticHref, useHashRoute } from '../shell/hashRoutes'
import { OptionChainPresentation, useOptionChainPresentation } from '../../features/mo_option_chain/presentation'
import { PremiumPlanePresentation, usePremiumPresentation } from '../../features/mo_option_premium/presentation'
import { ResearchOverviewPresentation, useStaticCatalog } from '../../features/research_catalog/presentation'
import { ResearchExplorerPresentation, useStaticExplorer } from '../../features/research_explorer/presentation'
import { FuturesBasisPresentation } from '../../features/futures_basis_research/presentation'
import { BacktestingPresentation } from '../../features/backtesting/presentation'
import { sourceDisclosure, type PrivateData } from './admission'

function Chain({ data }: { data: PrivateData }) {
  const state = useOptionChainPresentation(data.chain)
  return <OptionChainPresentation state={{ ...state, page: { status: 'ready', chain: data.chain } }} query={{ mode: 'static', selectedDate: data.chain.target_trade_date, sourceDisclosure: sourceDisclosure(data.identities.chain) }} />
}
function Premium({ data }: { data: PrivateData }) {
  const state = usePremiumPresentation(data.premium.plane)
  return <PremiumPlanePresentation state={{ ...state, page: { status: 'ready', ...data.premium } }} query={{ mode: 'static', selectedDate: data.premium.plane.observation.value, priceType: data.premium.plane.price_type, sourceDisclosure: sourceDisclosure(data.identities.premium) }} />
}
function Catalog({ data, navigate }: { data: PrivateData; navigate: ReturnType<typeof useHashRoute>['navigate'] }) {
  const controller = useStaticCatalog(data.catalogPayload)
  return <ResearchOverviewPresentation controller={controller} mode="static" navigation={{ openExplorer: () => navigate('/research/publications'), openFuturesBasis: () => navigate('/research/futures-basis') }} sourceDisclosure={sourceDisclosure(data.identities.catalog)} />
}
function Explorer({ data }: { data: PrivateData }) {
  const controller = useStaticExplorer(data.publicationPayload)
  return <ResearchExplorerPresentation controller={controller} mode="static" sourceDisclosure={`${sourceDisclosure(data.identities.publications)} 正式 Python Reader 已验证的安全静态导出；不声称在线 HTTP Analysis/View 返回 200，HTTP 4 MiB 预算保持不变。`} />
}
function Backtesting({ data }: { data: PrivateData }) {
  const [strategy, setStrategy] = useState<'expiry_to_M1_v1' | 'expiry_to_Q1_v1'>('expiry_to_M1_v1')
  const disclosure = sourceDisclosure(data.identities[strategy])
  return <Flex vertical gap="middle">
    <Typography.Text>本地选择已计算的正式 Result；不会提交回测任务。</Typography.Text>
    <Select aria-label="已计算策略结果" value={strategy} onChange={setStrategy} options={(['expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const).map(value => ({ value, label: value }))} style={{ width: 260 }} />
    <BacktestingPresentation key={strategy} mode="static" state={{ status: 'validated', data: strategy === 'expiry_to_M1_v1' ? data.m1 : data.q1 }} disclosure={disclosure} sourceDisclosure={disclosure} />
  </Flex>
}
export function PrivateWorkspace({ data }: { data: PrivateData }) {
  const { path, navigate } = useHashRoute()
  return <AppUiProvider><ApplicationShell path={path} navigate={navigate} href={staticHref} header={<Typography.Text type="secondary">Private · Static · Historical Real Market · No Backend</Typography.Text>}>
    <Flex vertical gap="large" style={{ minWidth: 0, maxWidth: '100%', overflowX: 'auto' }}>
      <Alert type="warning" showIcon title="私有真实市场静态 Demo V2" description="Historical Embedded Results · 匿名只读 · 无实时行情或服务器执行 · Publication Rights = BLOCKED；仅限本地验收。" />
      {path === '/research' && <Catalog data={data} navigate={navigate} />}
      {path === '/research/futures-basis' && <FuturesBasisPresentation mode="static" state={{ status: 'validated', data: data.basis }} disclosure={sourceDisclosure(data.identities.basis)} sourceDisclosure={sourceDisclosure(data.identities.basis)} />}
      {path === '/research/publications' && <Explorer data={data} />}
      {path === '/data' && <DailyDataLanding navigate={navigate} />}
      {path === '/data/mo-option-chain' && <Chain data={data} />}
      {path === '/data/mo-premium-plane' && <Premium data={data} />}
      {path === '/backtesting' && <Backtesting data={data} />}
    </Flex>
  </ApplicationShell></AppUiProvider>
}
