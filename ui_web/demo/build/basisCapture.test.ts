import { expect, it } from 'vitest'
import bundle from '../bundles/basis.json'
import { validateEmbeddedReport } from '../../src/features/futures_basis_research/api/validateResult'
import { BIN_PRESETS, histogramAggregation, TAIL_EXCLUSION_OPTIONS, type BasisMetric } from '../../src/features/futures_basis_research/model/histogramAggregation'

it('preserves the captured original population across every width and tail setting', () => {
  const { report } = validateEmbeddedReport({ request: bundle.request, report: bundle.result })
  const before = JSON.stringify(report)
  expect(report.distributions).toHaveLength(16)
  expect(report.comparisons).toHaveLength(24)
  expect(Object.keys(report.views.history)).toHaveLength(4)
  for (const metric of Object.keys(BIN_PRESETS) as BasisMetric[]) {
    for (const width of BIN_PRESETS[metric].widths) for (const tail of TAIL_EXCLUSION_OPTIONS) {
      const projection = histogramAggregation(report, metric, width, tail)
      expect(['ready', 'capacity']).toContain(projection.status)
      if (projection.status !== 'ready' && projection.status !== 'capacity') throw new Error(projection.status)
      if (projection.status === 'capacity') console.log(`CAPACITY ${metric} width=${width} tail=${tail}`)
      for (const [i, selection] of projection.selections.entries()) {
        expect(selection.original.length).toBe(selection.retained.length + selection.excluded.length)
        if (projection.status === 'ready') {
          const histogram = projection.slots[i]
          expect(histogram.n).toBe(selection.retained.length)
          expect(histogram.bins.reduce((n, b) => n + b.count, 0)).toBe(histogram.n)
          for (const bin of histogram.bins) expect(bin.frequency).toBe(bin.count / histogram.n)
        }
        for (const row of selection.excluded) {
          expect(row.product).toBe('IM')
          expect(row.metric).toBe(metric)
          expect(report.candidate_dates).toContain(row.date)
          expect(row.direction === 'lower' ? row.value < selection.lowerCutoff! : row.value > selection.upperCutoff!).toBe(true)
        }
      }
    }
  }
  expect(JSON.stringify(report)).toBe(before)
})
