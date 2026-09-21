import { describe, expect, it } from 'vitest'
import type { OptionChain } from './api/moOptionChain'
import { projectCombinedChain } from './combinedChartData'
import { buildCombinedPlot } from './combinedPlot'
import { buildExpiryPalette, DEFAULT_SERIES_COLORS } from './expiryPalette'

const chain: OptionChain = {
  target_trade_date: '2026-09-17', option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', futures: { instrument_id: 'IM2609.CFE', price: 7560.25 },
      calls: [{ instrument_id: 'C1', strike: 7000, price: 10 }, { instrument_id: 'C2', strike: 7100, price: null }, { instrument_id: 'C3', strike: 8000, price: 20 }],
      puts: [{ instrument_id: 'P1', strike: 7000, price: 0 }] },
    { expiry_date: '2026-10-23', futures: { instrument_id: 'IM2610.CFE', price: 7600 },
      calls: [{ instrument_id: 'C4', strike: 7200, price: 450 }],
      puts: [{ instrument_id: 'P2', strike: 7200, price: 5 }] },
  ],
}
const xDomain: [number, number] = [7000, 7700]
const palette = buildExpiryPalette(chain.expiries, DEFAULT_SERIES_COLORS)

function figure(selected: string[]) {
  return buildCombinedPlot(chain, projectCombinedChain(chain, new Set(selected), xDomain), xDomain, palette)
}

describe('combined Plotly figure', () => {
  it('keeps complete traces, null gaps and zero while encoding sides by color', () => {
    const { data, layout, config } = figure(['2026-09-25', '2026-10-23'])
    expect(data.map((trace) => trace.name)).toEqual([
      '2026-09-25 Call', '2026-09-25 Put', '2026-10-23 Call', '2026-10-23 Put',
    ])
    expect(data[0].x).toEqual([7000, 7100, 8000])
    expect(data[0].y).toEqual([10, null, 20])
    expect(data[0].customdata).toEqual(['C1', 'C2', 'C3'])
    expect(data[0].connectgaps).toBe(false)
    expect(data[1].y).toEqual([0])
    expect(data[0].line?.color).toBe(palette['2026-09-25'].call)
    expect(data[0].marker?.color).toBe(palette['2026-09-25'].call)
    expect(data[1].line?.color).toBe(palette['2026-09-25'].put)
    expect(data[1].marker?.color).toBe(palette['2026-09-25'].put)
    expect(data[2].line?.color).toBe(palette['2026-10-23'].call)
    expect(data[0].line?.dash).toBe('solid')
    expect(data[1].line?.dash).toBe('dash')
    expect(data[0].marker?.symbol).toBe('circle')
    expect(data[1].marker?.symbol).toBe('diamond')
    expect(data.every((trace) => trace.showlegend === false)).toBe(true)
    expect(layout.yaxis?.range).toEqual([-12, 600])
    expect(layout.xaxis?.range).toEqual(xDomain)
    expect(layout.showlegend).toBe(false)
    expect(config).toMatchObject({ responsive: true, scrollZoom: false, doubleClick: false, displayModeBar: false })
  })

  it('keeps one raw Spot annotation and selected opacity-linked Futures lines', () => {
    const { layout } = figure(['2026-09-25', '2026-10-23'])
    expect(layout.shapes?.map((shape) => shape.x0)).toEqual([7312.45, 7560.25, 7600])
    expect(layout.shapes?.[0].line?.color).toBe('#64748b')
    expect(layout.shapes?.[1].line?.color).toBe(palette['2026-09-25'].futures)
    expect(layout.shapes?.[2].line?.color).toBe(palette['2026-10-23'].futures)
    expect(layout.annotations?.map((annotation) => annotation.text)).toEqual(['Spot 7312.5'])
    expect(layout.annotations?.map((annotation) => [annotation.y, annotation.yanchor])).toEqual([[0, 'top']])
    const hidden = figure(['2026-09-25'])
    expect(hidden.data).toHaveLength(2)
    expect(hidden.layout.shapes).toHaveLength(2)
    expect(hidden.layout.annotations).toHaveLength(1)
  })

  it('omits an all-null side and a missing IM reference', () => {
    const altered: OptionChain = { ...chain, expiries: [{ ...chain.expiries[0], futures: null, calls: [{ instrument_id: 'C-null', strike: 7000, price: null }] }] }
    const projection = projectCombinedChain(altered, new Set(['2026-09-25']), xDomain)
    const { data, layout } = buildCombinedPlot(altered, projection, xDomain, palette)
    expect(data.map((trace) => trace.name)).toEqual(['2026-09-25 Put'])
    expect(layout.shapes).toHaveLength(1)
    expect(layout.annotations).toHaveLength(1)
  })
})
