import { describe, expect, it } from 'vitest'
import { projectExpiry } from './expiryChartData'
import { buildExpiryPlot } from './expiryPlot'

const underlying = { instrument_id: '000852.SH', price: 7312.45 }
const group = {
  expiry_date: '2026-09-25',
  futures: { instrument_id: 'IM2609.CFE', price: 7560.25 },
  calls: [
    { instrument_id: 'C-null', strike: 7000, price: null },
    { instrument_id: 'C-outside', strike: 8000, price: 9 },
  ],
  puts: [{ instrument_id: 'P-zero', strike: 7100, price: 0 }],
}

describe('Plotly expiry projection', () => {
  it('keeps complete numeric traces while the shared viewport only clips the view', () => {
    const { data, layout } = buildExpiryPlot(group, underlying, [7000, 7700])

    expect(data.map((trace) => [trace.type, trace.mode, trace.name])).toEqual([
      ['scatter', 'markers', 'Calls'],
      ['scatter', 'markers', 'Puts'],
    ])
    expect(data[0].x).toEqual([8000])
    expect(data[0].y).toEqual([9])
    expect(data[0].customdata).toEqual(['C-outside'])
    expect(data[1].x).toEqual([7100])
    expect(data[1].y).toEqual([0])
    expect(data[1].customdata).toEqual(['P-zero'])
    expect(data[0].marker).not.toEqual(data[1].marker)
    expect(projectExpiry(group).missingPriceCount).toBe(1)
    expect(layout.xaxis?.range).toEqual([7000, 7700])
    expect(layout.yaxis?.range).toEqual(projectExpiry(group).yDomain)
  })

  it('uses raw reference coordinates and one-decimal display rules', () => {
    const { data, layout, config } = buildExpiryPlot(group, underlying, [7000, 7700])

    expect(layout.shapes?.map((shape) => [shape.x0, shape.x1, shape.line?.dash])).toEqual([
      [7312.45, 7312.45, 'dash'],
      [7560.25, 7560.25, 'dot'],
    ])
    expect(layout.annotations?.map((annotation) => [annotation.x, annotation.text])).toEqual([
      [7312.45, 'Spot 7312.5'],
      [7560.25, 'IM 7560.3'],
    ])
    expect(layout.xaxis?.tickformat).toBe('.1f')
    expect(layout.yaxis?.tickformat).toBe('.1f')
    expect(data[0].hovertemplate).toContain('Call · Strike %{x:.1f} · Price %{y:.1f}')
    expect(data[1].hovertemplate).toContain('Put · Strike %{x:.1f} · Price %{y:.1f}')
    expect(data[0].hovertemplate).toContain('%{customdata}')
    expect(layout.xaxis?.fixedrange).toBe(true)
    expect(layout.dragmode).toBe(false)
    expect(config).toMatchObject({ responsive: true, scrollZoom: false, doubleClick: false, displayModeBar: false })
  })
})
