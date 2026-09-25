import { PremiumExpirySelector, PremiumPresentationControls, PremiumQueryControls } from '../components/PremiumControls'
import { PremiumError, PremiumPlaneTable, PremiumSummary, RawResponseInspector } from '../components/PremiumResults'
import { usePremiumPlane } from '../hooks/usePremiumPlane'

export default function PremiumPlanePage() {
  const state = usePremiumPlane()

  return (
    <main className="premium-page">
      <header>
        <p className="eyebrow">hg-market-state-lab</p>
        <h1>MO 年化权利金平面</h1>
        <p>Select an observation and price type to inspect real, sparse option observations.</p>
      </header>
      <PremiumQueryControls selectedDate={state.selectedDate} priceType={state.priceType}
        selectDate={state.selectDate} selectPriceType={state.selectPriceType} />

      {state.page.status === 'idle' && <p role="status">Select an observation date.</p>}
      {state.page.status === 'loading' && <p role="status">Loading {state.page.asOf} · {state.page.priceType} premium plane…</p>}
      {state.page.status === 'error' && <PremiumError asOf={state.page.asOf} priceType={state.page.priceType} error={state.page.error} />}
      {state.page.status === 'success' && state.projection !== null && (
        <section className="results premium-results" aria-label="Premium plane results">
          <PremiumSummary plane={state.page.plane} />
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
          <p className="plane-legend">Blank = no Point; — = metric unavailable for a real Point.</p>
          <RawResponseInspector key={`${state.page.plane.observation.value}-${state.page.plane.price_type}`}
            payload={state.page.rawPayload} />
        </section>
      )}
    </main>
  )
}
