import Plot from 'react-plotly.js'
import type { ExpiryGroup, OptionChain } from './api/moOptionChain'
import { projectExpiry } from './expiryChartData'
import { buildExpiryPlot } from './expiryPlot'
import { formatPrice } from './priceDisplay'

export default function ExpiryChart({ group, underlying, xDomain }: {
  group: ExpiryGroup
  underlying: OptionChain['underlying']
  xDomain: [number, number]
}) {
  const chart = projectExpiry(group)
  const hasDrawablePrice = chart.calls.length + chart.puts.length > 0
  const futuresDescription = group.futures === null
    ? '无同到期 IM 合约'
    : `Futures ${group.futures.instrument_id} ${formatPrice(group.futures.price)}`

  return (
    <section className="expiry-chart" aria-label={`${group.expiry_date} 散点图`}>
      <h4>价格分布</h4>
      <div className="chart-references">
        <p className="chart-reference spot-reference">Spot：{underlying.instrument_id} · {formatPrice(underlying.price)}</p>
        {group.futures === null
          ? <p className="chart-reference">无同到期 IM 合约</p>
          : <p className="chart-reference futures-reference">Futures：{group.futures.instrument_id} · {formatPrice(group.futures.price)}</p>}
      </div>
      {chart.missingPriceCount > 0 && (
        <p className="missing-price">{chart.missingPriceCount} 个合约缺少所选价格，未绘制为散点；可在合约明细中查看。</p>
      )}
      {hasDrawablePrice ? (
        <div className="chart-frame" role="group" aria-label={`${group.expiry_date} Call 与 Put 价格散点图；横轴 Strike，纵轴 Price；Spot ${underlying.instrument_id} ${formatPrice(underlying.price)}；${futuresDescription}`}>
          <Plot {...buildExpiryPlot(group, underlying, xDomain)} style={{ width: '100%', height: '100%' }} useResizeHandler />
        </div>
      ) : (
        <p className="chart-empty">该到期日没有可绘制的价格。</p>
      )}
    </section>
  )
}
