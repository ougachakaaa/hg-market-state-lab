import type { Config, Layout, ScatterData } from 'plotly.js'
import type { ExpiryGroup, OptionChain } from './api/moOptionChain'
import { projectExpiry } from './expiryChartData'
import type { ChartPoint } from './expiryChartData'
import { formatPrice } from './priceDisplay'

function optionTrace(points: ChartPoint[], side: ChartPoint['side'], color: string): ScatterData {
  return {
    type: 'scatter',
    mode: 'markers',
    name: `${side}s`,
    x: points.map((point) => point.strike),
    y: points.map((point) => point.price),
    customdata: points.map((point) => point.instrument_id),
    marker: { color, size: 8 },
    hovertemplate: `%{customdata}<br>${side} · Strike %{x:.1f} · Price %{y:.1f}<extra></extra>`,
  }
}

export function buildExpiryPlot(
  group: ExpiryGroup,
  underlying: OptionChain['underlying'],
  xDomain: [number, number],
) {
  const chart = projectExpiry(group)
  const data: ScatterData[] = [
    optionTrace(chart.calls, 'Call', '#2563eb'),
    optionTrace(chart.puts, 'Put', '#ea580c'),
  ]
  const layout: Partial<Layout> = {
    autosize: true,
    dragmode: false,
    hovermode: 'closest',
    margin: { t: 48, r: 24, b: 52, l: 62 },
    xaxis: { title: { text: 'Strike' }, type: 'linear', range: xDomain, fixedrange: true, tickformat: '.1f', showgrid: true },
    yaxis: { title: { text: 'Price' }, type: 'linear', range: chart.yDomain, fixedrange: true, tickformat: '.1f', showgrid: true },
    legend: { orientation: 'h', x: 0, y: 1.18 },
    shapes: [
      { type: 'line', xref: 'x', yref: 'paper', x0: underlying.price, x1: underlying.price, y0: 0, y1: 1, line: { color: '#64748b', dash: 'dash' } },
      { type: 'line', xref: 'x', yref: 'paper', x0: group.futures.price, x1: group.futures.price, y0: 0, y1: 1, line: { color: '#7c3aed', dash: 'dot' } },
    ],
    annotations: [
      { xref: 'x', yref: 'paper', x: underlying.price, y: 1, text: `Spot ${formatPrice(underlying.price)}`, showarrow: false, xanchor: 'right', yanchor: 'bottom', font: { color: '#475569' } },
      { xref: 'x', yref: 'paper', x: group.futures.price, y: 0, text: `IM ${formatPrice(group.futures.price)}`, showarrow: false, xanchor: 'right', yanchor: 'top', font: { color: '#6d28d9' } },
    ],
  }
  const config: Partial<Config> = {
    responsive: true,
    displayModeBar: false,
    scrollZoom: false,
    doubleClick: false,
  }

  return { data, layout, config }
}
