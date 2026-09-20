import type { Config, Layout, ScatterData } from 'plotly.js'
import type { ExpiryGroup, OptionChain } from './api/moOptionChain'
import { projectExpiry } from './expiryChartData'
import type { OptionPoint } from './api/moOptionChain'
import { formatPrice } from './priceDisplay'

function optionTrace(points: OptionPoint[], side: 'Call' | 'Put', color: string): ScatterData {
  return {
    type: 'scatter',
    mode: 'lines+markers',
    name: `${side}s`,
    x: points.map((point) => point.strike),
    y: points.map((point) => point.price),
    customdata: points.map((point) => point.instrument_id),
    connectgaps: false,
    line: { color, width: 2, shape: 'linear' },
    marker: { color, size: 8 },
    hovertemplate: `%{customdata}<br>${side} · Strike %{x:.1f} · Price %{y:.1f}<extra></extra>`,
  }
}

export function buildExpiryPlot(
  group: ExpiryGroup,
  underlying: OptionChain['underlying'],
  xDomain: [number, number],
) {
  const chart = projectExpiry(group, xDomain)
  const data: ScatterData[] = [
    optionTrace(group.calls, 'Call', '#2563eb'),
    optionTrace(group.puts, 'Put', '#ea580c'),
  ]
  const futures = group.futures
  const layout: Partial<Layout> = {
    autosize: true,
    dragmode: false,
    hovermode: 'closest',
    margin: { t: 48, r: 24, b: 52, l: 62 },
    xaxis: {
      title: { text: 'Strike' }, type: 'linear', range: xDomain, fixedrange: true,
      tickformat: '.1f', tick0: 0, dtick: 200, showgrid: true, gridcolor: '#e5e7eb',
    },
    yaxis: {
      title: { text: 'Price' }, type: 'linear', range: chart.yDomain, fixedrange: true,
      tickformat: '.1f', tick0: 0, dtick: 200, showgrid: true,
      gridcolor: '#e5e7eb', griddash: 'dash', side: 'left',
      minor: { tick0: 0, dtick: 100, showgrid: true, gridcolor: '#e5e7eb', griddash: 'dash' },
    },
    legend: { orientation: 'h', x: 0, y: 1.18 },
    shapes: [
      {
        type: 'line', xref: 'x', yref: 'paper',
        x0: underlying.price, x1: underlying.price, y0: 0, y1: 1,
        line: { color: '#64748b', width: 2, dash: 'solid' },
      },
      ...(futures === null ? [] : [{
        type: 'line' as const, xref: 'x' as const, yref: 'paper' as const,
        x0: futures.price, x1: futures.price, y0: 0, y1: 1,
        line: { color: '#7c3aed', dash: 'dot' as const },
      }]),
    ],
    annotations: [
      { xref: 'x', yref: 'paper', x: underlying.price, y: 1, text: `Spot ${formatPrice(underlying.price)}`, showarrow: false, xanchor: 'right', yanchor: 'bottom', font: { color: '#475569' } },
      ...(futures === null ? [] : [{
        xref: 'x' as const, yref: 'paper' as const, x: futures.price, y: 0,
        text: `IM ${formatPrice(futures.price)}`, showarrow: false,
        xanchor: 'right' as const, yanchor: 'top' as const,
        font: { color: '#6d28d9' },
      }]),
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
