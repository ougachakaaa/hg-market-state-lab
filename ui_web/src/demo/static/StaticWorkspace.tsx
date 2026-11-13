import { useState, type ReactNode } from 'react'
import type { WorkspacePath } from '../../app/routeInventory'
import { Flex, Select, Typography } from 'antd'
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
import type { ResultIdentity, StaticData } from './results'

function Chain({ data, disclose }: StaticProps) {
  const state = useOptionChainPresentation(data.chain)
  return <OptionChainPresentation state={{ ...state, page: { status: 'ready', chain: data.chain } }} query={{ mode: 'static', selectedDate: data.chain.target_trade_date, sourceDisclosure: disclose(data.identities.chain) }} />
}
function Premium({ data, disclose }: StaticProps) {
  const state = usePremiumPresentation(data.premium.plane)
  return <PremiumPlanePresentation state={{ ...state, page: { status: 'ready', ...data.premium } }} query={{ mode: 'static', selectedDate: data.premium.plane.observation.value, priceType: data.premium.plane.price_type, sourceDisclosure: disclose(data.identities.premium) }} />
}
function Catalog({ data, navigate, disclose }: StaticContext) {
  const controller = useStaticCatalog(data.catalogPayload)
  return <ResearchOverviewPresentation controller={controller} mode="static" navigation={{ openExplorer: () => navigate('/research/publications'), openFuturesBasis: () => navigate('/research/futures-basis') }} sourceDisclosure={disclose(data.identities.catalog)} />
}
function Explorer({ data, disclose }: StaticProps) {
  const controller = useStaticExplorer(data.publicationPayload)
  return <ResearchExplorerPresentation controller={controller} mode="static" sourceDisclosure={`${disclose(data.identities.publications)} 正式结果的静态阅读；Analysis 与 View 选择仅使用已装载数据。`} />
}
function Backtesting({ data, disclose }: StaticProps) {
  const [strategy, setStrategy] = useState<'expiry_to_M1_v1' | 'expiry_to_Q1_v1'>('expiry_to_M1_v1')
  const disclosure = disclose(data.identities[strategy])
  return <Flex vertical gap="middle">
    <Typography.Text>本地选择已计算的正式 Result；不会提交回测任务。</Typography.Text>
    <Select aria-label="已计算策略结果" value={strategy} onChange={setStrategy} options={(['expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const).map(value => ({ value, label: value }))} style={{ width: 260 }} />
    <BacktestingPresentation key={strategy} mode="static" state={{ status: 'validated', data: strategy === 'expiry_to_M1_v1' ? data.m1 : data.q1 }} disclosure={disclosure} sourceDisclosure={disclosure} />
  </Flex>
}
type StaticProps = { data: StaticData; disclose: (identity: ResultIdentity) => string }
type StaticContext = StaticProps & { navigate: ReturnType<typeof useHashRoute>['navigate'] }
// Compile-time exhaustive coverage comes from the formal application inventory.
const staticRoutePresentations = {
  '/research': ({ data, navigate, disclose }) => <Catalog data={data} navigate={navigate} disclose={disclose} />,
  '/research/futures-basis': ({ data, disclose }) => <FuturesBasisPresentation mode="static" state={{ status: 'validated', data: data.basis }} disclosure={disclose(data.identities.basis)} sourceDisclosure={disclose(data.identities.basis)} />,
  '/research/publications': ({ data, disclose }) => <Explorer data={data} disclose={disclose} />,
  '/data': ({ navigate }) => <DailyDataLanding navigate={navigate} />,
  '/data/mo-option-chain': ({ data, disclose }) => <Chain data={data} disclose={disclose} />,
  '/data/mo-premium-plane': ({ data, disclose }) => <Premium data={data} disclose={disclose} />,
  '/backtesting': ({ data, disclose }) => <Backtesting data={data} disclose={disclose} />,
} satisfies Record<WorkspacePath, (context: StaticContext) => ReactNode>

export function StaticWorkspace({ data, disclose, header, notice }: StaticProps & { header: string; notice: ReactNode }) {
  const { path, navigate } = useHashRoute()
  return <AppUiProvider><ApplicationShell path={path} navigate={navigate} href={staticHref} header={<Typography.Text type="secondary">{header}</Typography.Text>}>
    <Flex vertical gap="large" style={{ minWidth: 0, maxWidth: '100%', overflowX: 'auto' }}>
      {notice}
      {staticRoutePresentations[path]({ data, navigate, disclose })}
    </Flex>
  </ApplicationShell></AppUiProvider>
}
