import { createRoot } from 'react-dom/client'
import AppUiProvider from '../../../src/app/AppUiProvider'
import { PremiumPlanePresentation, usePremiumPresentation, validatePremiumPlane } from '../../../src/features/mo_option_premium/presentation'
import { plane as testData } from '../../../src/features/mo_option_premium/testing/planeFixture'
import '../../../src/index.css'

const result = validatePremiumPlane(testData)
export function StaticHarness() {
  const presentation = usePremiumPresentation(result.plane)
  return <PremiumPlanePresentation state={{ ...presentation, page: { status: 'ready', ...result } }}
    query={{ mode: 'static', selectedDate: result.plane.observation.value, priceType: result.plane.price_type,
      sourceDisclosure: '静态测试数据 · 非正式 Synthetic Example · 不代表实时行情；复制和导出使用完整测试 payload。' }} />
}
createRoot(document.getElementById('root')!).render(<AppUiProvider><StaticHarness /></AppUiProvider>)
