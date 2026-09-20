import Plot from 'react-plotly.js'
import type { OptionChain } from './api/moOptionChain'
import { projectCombinedChain } from './combinedChartData'
import { buildCombinedPlot } from './combinedPlot'
import { formatPrice } from './priceDisplay'

export default function CombinedExpiryChart({ chain, selectedExpiries, xDomain, palette }: {
  chain: OptionChain
  selectedExpiries: ReadonlySet<string>
  xDomain: [number, number]
  palette: Record<string, string>
}) {
  const projection = projectCombinedChain(chain, selectedExpiries, xDomain)
  return (
    <section className="combined-chart" aria-label="合并到期日分析图">
      <h3>价格分布</h3>
      <p className="chart-reference spot-reference">Spot：{chain.underlying.instrument_id} · {formatPrice(chain.underlying.price)}</p>
      {!projection.hasDrawablePrice && <p className="chart-empty">选中的到期日没有可绘制的价格。</p>}
      <div className="chart-frame" role="group" aria-label="所选到期日 Call 与 Put 价格散点图；横轴 Strike，纵轴 Price">
        <Plot {...buildCombinedPlot(chain, projection, xDomain, palette)} style={{ width: '100%', height: '100%' }} useResizeHandler />
      </div>
    </section>
  )
}
