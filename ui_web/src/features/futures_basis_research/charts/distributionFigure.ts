import type { Data } from 'plotly.js'
import { BIN_PRESETS, type BasisMetric, type HistogramProjection } from '../model/histogramAggregation'
import { formatUnit } from '../../../shared/format/unit'

const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

/** Feature-owned Plotly encoding; no formal Visualization contract is synthesized. */
export function distributionTraces(projection: Extract<HistogramProjection, { status: 'ready' }>, metric: BasisMetric): Data[] {
  const ratio = BIN_PRESETS[metric].unit === 'decimal_ratio'
  const boundary = (value: number) => ratio ? formatUnit(value, 'decimal_ratio') : `${formatUnit(value)} 点`
  return projection.slots.map(({ slot, n, bins, failure, layerIndex }) => {
    const available = n > 0 && !failure
    // Two vertices per interval preserve horizontal extent and exact edge closures.
    // customdata repeats metadata at both vertices, while the model counts each bin once.
    const points = available ? bins.flatMap(b => [b.left, b.right]) : []
    return {
      type: 'scatter', mode: 'lines', name: slot, uid: slot, legendgroup: slot,
      x: points.length ? points : [null],
      y: available ? bins.flatMap(b => [b.frequency, b.frequency]) : [null],
      // Reuse the Slot's history Binding color, never a second Slot-to-color mapping.
      line: { color: colors[layerIndex % colors.length], width: 2 },
      customdata: available ? bins.flatMap(b => {
        const row = [`[${boundary(b.left)}, ${boundary(b.right)}${b.rightInclusive ? ']' : ')'}`, b.count, b.frequency, n]
        return [row, row]
      }) : [],
      hovertemplate: `${slot}<br>区间：%{customdata[0]}<br>Count：%{customdata[1]:d}<br>Frequency：%{customdata[2]:.1%}<br>Eligible N：%{customdata[3]:d}<extra></extra>`,
      connectgaps: false,
    } as Data
  })
}
