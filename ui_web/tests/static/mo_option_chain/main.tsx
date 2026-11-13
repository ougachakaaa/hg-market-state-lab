import { createRoot } from 'react-dom/client'
import AppUiProvider from '../../../src/app/AppUiProvider'
import { OptionChainPresentation, useOptionChainPresentation, validateOptionChain } from '../../../src/features/mo_option_chain/presentation'
import { chain as testData } from '../../../src/features/mo_option_chain/testing/chainFixture'
import '../../../src/index.css'

const chain = validateOptionChain(testData)
export function StaticHarness() {
  const presentation = useOptionChainPresentation(chain)
  return <OptionChainPresentation state={{ ...presentation, page: { status: 'ready', chain } }}
    query={{ mode: 'static', selectedDate: chain.target_trade_date,
      sourceDisclosure: '静态测试数据 · 非正式 Synthetic Example · 不代表实时行情；复制和导出使用完整测试 payload。' }} />
}
createRoot(document.getElementById('root')!).render(<AppUiProvider><StaticHarness /></AppUiProvider>)
