import { useState } from 'react'
import OptionChainPage from '../features/mo_option_chain'
import PremiumPlanePage from '../features/mo_option_premium'
import './application.css'

type Feature = 'option-chain' | 'premium-plane'

function App() {
  const [feature, setFeature] = useState<Feature>('option-chain')

  return (
    <div className="application">
      <nav className="feature-navigation" aria-label="产品功能导航">
        <button type="button" aria-pressed={feature === 'option-chain'} onClick={() => setFeature('option-chain')}>
          MO Option Chain
        </button>
        <button type="button" aria-pressed={feature === 'premium-plane'} onClick={() => setFeature('premium-plane')}>
          MO Premium Plane
        </button>
      </nav>
      {feature === 'option-chain' ? <OptionChainPage /> : <PremiumPlanePage />}
    </div>
  )
}

export default App
