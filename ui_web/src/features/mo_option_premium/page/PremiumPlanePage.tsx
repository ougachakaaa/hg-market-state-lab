import { usePremiumPlane } from '../hooks/usePremiumPlane'
import { PremiumPlanePresentation } from './PremiumPlanePresentation'

export default function PremiumPlanePage() {
  const state = usePremiumPlane()
  return <PremiumPlanePresentation state={state} query={{ mode: 'production',
    selectedDate: state.selectedDate, priceType: state.priceType,
    selectDate: state.selectDate, selectPriceType: state.selectPriceType }} />
}
