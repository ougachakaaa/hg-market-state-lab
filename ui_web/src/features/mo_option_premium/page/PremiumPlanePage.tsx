import { Empty, Flex, Space, Spin, Typography } from 'antd'
import { PremiumCopyActions } from '../components/PremiumCopyActions'
import { PremiumExpirySelector, PremiumPresentationControls, PremiumQueryControls } from '../components/PremiumControls'
import { PremiumError, PremiumPlaneTable, PremiumSummary, RawResponseInspector } from '../components/PremiumResults'
import { usePremiumPlane } from '../hooks/usePremiumPlane'

export default function PremiumPlanePage() {
  const state = usePremiumPlane()

  return (
    <div className="premium-page">
      <Space orientation="vertical" size="large" style={{ display: 'flex' }}>
        <header>
          <Typography.Text type="secondary">hg-market-state-lab</Typography.Text>
          <Typography.Title level={1}>MO 年化权利金平面</Typography.Title>
          <Typography.Paragraph>Select an observation and price type to inspect real, sparse option observations.</Typography.Paragraph>
        </header>
        <PremiumQueryControls selectedDate={state.selectedDate} priceType={state.priceType}
          selectDate={state.selectDate} selectPriceType={state.selectPriceType} />

        {state.page.status === 'idle' && <div role="status"><Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select an observation date." /></div>}
        {state.page.status === 'loading' && <Flex gap="small" align="center" role="status"><Spin size="small" />Loading {state.page.asOf} · {state.page.priceType} premium plane…</Flex>}
        {state.page.status === 'error' && <PremiumError asOf={state.page.asOf} priceType={state.page.priceType} error={state.page.error} />}
        {state.page.status === 'success' && state.projection !== null && (
          <section aria-label="Premium plane results">
            <Space orientation="vertical" size="middle" style={{ display: 'flex' }}>
              <PremiumSummary plane={state.page.plane} />
              <PremiumCopyActions plane={state.page.plane} rawPayload={state.page.rawPayload} />
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
              <Typography.Text type="secondary">Blank = no Point; — = metric unavailable for a real Point.</Typography.Text>
              <RawResponseInspector key={`${state.page.plane.observation.value}-${state.page.plane.price_type}`}
                payload={state.page.rawPayload} />
            </Space>
          </section>
        )}
      </Space>
    </div>
  )
}
