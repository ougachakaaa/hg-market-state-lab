import { OptionChainQueryControl, StrikeViewportControl } from '../components/OptionChainControls'
import { OptionChainError, OptionChainSummary } from '../components/OptionChainResults'
import { OptionChainVisualization } from '../components/OptionChainVisualization'
import { useOptionChain } from '../hooks/useOptionChain'

export default function OptionChainPage() {
  const state = useOptionChain()

  return (
    <main className="option-chain-page">
      <header>
        <p className="eyebrow">hg-market-state-lab</p>
        <h1>MO 期权链</h1>
        <p>选择交易日，查看中证 1000 指数参考价与各到期日的期权合约。</p>
      </header>
      <OptionChainQueryControl selectedDate={state.selectedDate} selectDate={state.selectDate} />

      {state.page.status === 'idle' && <p role="status">请选择目标交易日。</p>}
      {state.page.status === 'loading' && <p role="status">正在加载 {state.page.date} 的期权链…</p>}
      {state.page.status === 'error' && <OptionChainError date={state.page.date} error={state.page.error} />}
      {state.page.status === 'success' && state.xDomain !== null && (
        <section className="results" aria-label="期权链结果">
          <OptionChainSummary chain={state.page.chain} />
          <StrikeViewportControl halfRangePoints={state.strikeHalfRangePoints}
            shrink={state.shrinkViewport} expand={state.expandViewport} />
          {state.page.chain.expiries.length === 0 ? <p className="chart-empty">该期权链没有到期日。</p> : (
            <>
              <OptionChainVisualization chain={state.page.chain} selectedExpiries={state.selectedExpiries}
                selectedSet={state.selectedSet} selectedGroups={state.selectedGroups} xDomain={state.xDomain}
                seriesColors={state.seriesColors} toggleExpiry={state.toggleExpiry}
                changeSeriesColor={state.changeSeriesColor} />
            </>
          )}
        </section>
      )}
    </main>
  )
}
