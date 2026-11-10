import { Empty, Flex, Space, Spin, Typography } from 'antd'
import { PremiumCopyActions } from '../components/PremiumCopyActions'
import { PremiumExpirySelector, PremiumPresentationControls, PremiumQueryControls } from '../components/PremiumControls'
import { PremiumError, PremiumPlaneTable, PremiumSummary, RawResponseInspector } from '../components/PremiumResults'
import { usePremiumPlane } from '../hooks/usePremiumPlane'

export default function PremiumPlanePage() {
  const state = usePremiumPlane()

  return (
    <div className="premium-page">
      <Space orientation="vertical" size="small" style={{ display: 'flex', minWidth: 0 }}>
        <header>
          <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>MO 年化权利金平面</Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>选择观察日期与价格口径，查看稀疏期权权利金数据。</Typography.Paragraph>
        </header>
        <PremiumQueryControls selectedDate={state.selectedDate} priceType={state.priceType}
          selectDate={state.selectDate} selectPriceType={state.selectPriceType} />

        {state.page.status === 'idle' && <div role="status"><Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择观察日期，选择后自动加载。" /></div>}
        {state.page.status === 'loading' && <Flex gap="small" align="center" role="status" aria-live="polite" aria-busy="true"><Spin size="small" />正在加载 {state.page.asOf} · {state.page.priceType} 的权利金平面…</Flex>}
        {state.page.status === 'error' && <PremiumError asOf={state.page.asOf} priceType={state.page.priceType} error={state.page.error} />}
        {state.page.status === 'success' && state.projection !== null && (
          <section aria-label="Premium plane results">
            <Space orientation="vertical" size="small" style={{ display: 'flex', minWidth: 0 }}>
              <Typography.Text type="secondary" role="status" aria-live="polite">已加载 {state.page.plane.observation.value} · {state.page.plane.price_type}</Typography.Text>
              <Flex gap="small" wrap align="center" justify="space-between">
                <PremiumSummary plane={state.page.plane} />
                <PremiumCopyActions plane={state.page.plane} rawPayload={state.page.rawPayload} />
              </Flex>
              <PremiumPresentationControls optionType={state.selectedOptionType}
                referenceBasis={state.selectedReferenceBasis} valueBasis={state.selectedValueBasis}
                timeNormalization={state.selectedTimeNormalization} representation={state.selectedRepresentation}
                setOptionType={state.setSelectedOptionType} setReferenceBasis={state.setSelectedReferenceBasis}
                setValueBasis={state.setSelectedValueBasis} setTimeNormalization={state.setSelectedTimeNormalization}
                setRepresentation={state.setSelectedRepresentation} />
              <PremiumExpirySelector expiries={state.page.plane.expiries} selectedExpiries={state.selectedExpiries}
                toggleExpiry={state.toggleExpiry} />
              <PremiumPlaneTable plane={state.page.plane} projection={state.projection}
                representation={state.selectedRepresentation} />
              <Typography.Text type="secondary">空白 = 无 Point；— = 真实 Point 的指标不可用。</Typography.Text>
              <RawResponseInspector key={`${state.page.plane.observation.value}-${state.page.plane.price_type}`}
                payload={state.page.rawPayload} />
            </Space>
          </section>
        )}
      </Space>
    </div>
  )
}
