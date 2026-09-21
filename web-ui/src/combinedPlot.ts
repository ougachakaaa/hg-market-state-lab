import type { Config, Layout, ScatterData } from 'plotly.js'
import type { ExpiryGroup, OptionChain, OptionPoint } from './api/moOptionChain'
import type { projectCombinedChain } from './combinedChartData'
import type { ExpiryColors } from './expiryPalette'
import { formatPrice } from './priceDisplay'

type Projection = ReturnType<typeof projectCombinedChain>

function optionTrace(group: ExpiryGroup, points: OptionPoint[], side: 'Call' | 'Put', color: string): ScatterData {
  return {
    type: 'scatter', mode: 'lines+markers', name: `${group.expiry_date} ${side}`,
    showlegend: false,
    legendgroup: group.expiry_date,
    x: points.map((point) => point.strike),
    y: points.map((point) => point.price),
    customdata: points.map((point) => point.instrument_id),
    connectgaps: false,
    line: { color, width: 2, shape: 'linear', dash: side === 'Call' ? 'solid' : 'dash' },
    marker: { color, size: 8, symbol: side === 'Call' ? 'circle' : 'diamond' },
    hovertemplate: `%{customdata}<br>${group.expiry_date} ${side} · Strike %{x:.1f} · Price %{y:.1f}<extra></extra>`,
  }
}

export function buildCombinedPlot(
  chain: OptionChain,
  projection: Projection,
  xDomain: [number, number],
  palette: Record<string, ExpiryColors>,
) {
  const data: ScatterData[] = projection.groups.flatMap((group) => (
    ([['Call', group.calls], ['Put', group.puts]] as const)
      .filter(([, points]) => points.some((point) => point.price !== null))
      .map(([side, points]) => optionTrace(group, points, side,
        side === 'Call' ? palette[group.expiry_date].call : palette[group.expiry_date].put))
  ))
  const futuresGroups = projection.groups.filter((group) => group.futures !== null)
  const layout: Partial<Layout> = {
    autosize: true, dragmode: false, hovermode: 'closest',
    showlegend: false,
    margin: { t: 24, r: 24, b: 76, l: 62 },
    xaxis: {
      title: { text: 'Strike' }, type: 'linear', range: xDomain, fixedrange: true,
      tickformat: '.1f', tick0: 0, dtick: 200, showgrid: true, gridcolor: '#e5e7eb',
    },
    yaxis: {
      title: { text: 'Price' }, type: 'linear', range: projection.yDomain, fixedrange: true,
      tickformat: '.1f', tick0: 0, dtick: 200, showgrid: true,
      gridcolor: '#e5e7eb', griddash: 'dash', side: 'left',
      minor: { tick0: 0, dtick: 100, showgrid: true, gridcolor: '#e5e7eb', griddash: 'dash' },
    },
    shapes: [
      {
        type: 'line', xref: 'x', yref: 'paper',
        x0: chain.underlying.price, x1: chain.underlying.price, y0: 0, y1: 1,
        line: { color: '#64748b', width: 2, dash: 'solid' },
      },
      ...futuresGroups.map((group) => ({
        type: 'line' as const, xref: 'x' as const, yref: 'paper' as const,
        x0: group.futures!.price, x1: group.futures!.price, y0: 0, y1: 1,
        line: { color: palette[group.expiry_date].futures, width: 1.5, dash: 'dot' as const },
      })),
    ],
    annotations: [
      {
        xref: 'x', yref: 'paper', x: chain.underlying.price, y: 0,
        text: `Spot ${formatPrice(chain.underlying.price)}`, showarrow: false,
        xanchor: 'right', yanchor: 'top', font: { color: '#475569' },
      },
    ],
  }
  const config: Partial<Config> = {
    responsive: true, displayModeBar: false, scrollZoom: false, doubleClick: false,
  }
  return { data, layout, config }
}
