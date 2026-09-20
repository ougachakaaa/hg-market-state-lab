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
      ['scatter', 'lines+markers', 'Calls'],
      ['scatter', 'lines+markers', 'Puts'],
    ])
    expect(data[0].x).toEqual([7000, 8000])
    expect(data[0].y).toEqual([null, 9])
    expect(data[0].customdata).toEqual(['C-null', 'C-outside'])
    expect(data[1].x).toEqual([7100])
    expect(data[1].y).toEqual([0])
    expect(data[1].customdata).toEqual(['P-zero'])
    expect(data[0].marker).not.toEqual(data[1].marker)
    expect(data[0].line).not.toEqual(data[1].line)
    expect(data[0].connectgaps).toBe(false)
    expect(data[1].connectgaps).toBe(false)
    expect(projectExpiry(group, [7000, 7700]).missingPriceCount).toBe(1)
    expect(layout.xaxis?.range).toEqual([7000, 7700])
    expect(layout.yaxis?.range).toEqual([-2, 100])
  })

  it('uses raw reference coordinates and one-decimal display rules', () => {
    const { data, layout, config } = buildExpiryPlot(group, underlying, [7000, 7700])

    expect(layout.shapes?.map((shape) => [shape.x0, shape.x1, shape.line?.dash])).toEqual([
      [7312.45, 7312.45, 'solid'],
      [7560.25, 7560.25, 'dot'],
    ])
    expect(layout.annotations?.map((annotation) => [annotation.x, annotation.text])).toEqual([
      [7312.45, 'Spot 7312.5'],
      [7560.25, 'IM 7560.3'],
    ])
    expect(layout.xaxis?.tickformat).toBe('.1f')
    expect(layout.yaxis?.tickformat).toBe('.1f')
    expect(layout.xaxis).toMatchObject({ tick0: 0, dtick: 200, showgrid: true, gridcolor: '#e5e7eb' })
    expect(layout.yaxis).toMatchObject({
      tick0: 0, dtick: 200, showgrid: true, gridcolor: '#e5e7eb', griddash: 'dash',
      side: 'left',
      minor: { tick0: 0, dtick: 100, showgrid: true, gridcolor: '#e5e7eb', griddash: 'dash' },
    })
    expect(layout.yaxis?.anchor).not.toBe('free')
    expect(data[0].hovertemplate).toContain('Call · Strike %{x:.1f} · Price %{y:.1f}')
    expect(data[1].hovertemplate).toContain('Put · Strike %{x:.1f} · Price %{y:.1f}')
    expect(data[0].hovertemplate).toContain('%{customdata}')
    expect(layout.xaxis?.fixedrange).toBe(true)
    expect(layout.dragmode).toBe(false)
    expect(config).toMatchObject({ responsive: true, scrollZoom: false, doubleClick: false, displayModeBar: false })
  })

  it('keeps option points and Spot without an IM reference', () => {
    const { data, layout } = buildExpiryPlot({ ...group, futures: null }, underlying, [7000, 7700])
    expect(data.map((trace) => trace.name)).toEqual(['Calls', 'Puts'])
    expect(layout.shapes?.map((shape) => [shape.x0, shape.line?.dash])).toEqual([
      [7312.45, 'solid'],
    ])
    expect(layout.annotations?.map((annotation) => annotation.text)).toEqual(['Spot 7312.5'])
  })

  it('breaks a side line at a missing price without joining Calls to Puts', () => {
    const lines = {
      ...group,
      calls: [
        { instrument_id: 'C1', strike: 7000, price: 10 },
        { instrument_id: 'C2', strike: 7100, price: null },
        { instrument_id: 'C3', strike: 7200, price: 20 },
      ],
      puts: [{ instrument_id: 'P1', strike: 7000, price: 5 }],
    }
    const { data } = buildExpiryPlot(lines, underlying, [6900, 7300])
    expect(data).toHaveLength(2)
    expect(data[0].y).toEqual([10, null, 20])
    expect(data[0].connectgaps).toBe(false)
    expect(data[1].y).toEqual([5])
  })
})
