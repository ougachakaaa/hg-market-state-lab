import { readerFixture } from '../report/reader.fixture'
import { BIN_PRESETS, SLOTS, type BasisMetric } from './histogramAggregation'

export function histogramFixture(samples: (number | null)[][], metric: BasisMetric = 'basis_value') {
  const report = readerFixture()
  const n = Math.max(0, ...samples.map(s => s.length))
  const dates = Array.from({ length: n }, (_, i) => `2024-10-${String(i + 1).padStart(2, '0')}`)
  report.candidate_dates = dates
  const unit = BIN_PRESETS[metric].unit
  const keys = (slot: string, selected: string[]) => selected.map(date => ['IM', date, slot])
  report.views.history[metric] = {
    version: 2, axes: [{ id: 'x', orientation: 'x', coordinate: { kind: 'date', unit: 'date' } }, { id: 'y', orientation: 'y', coordinate: { kind: 'number', unit } }],
    layers: SLOTS.map((slot, i) => ({ id: slot, label: slot, x_axis: 'x', y_axis: 'y', layer: { type: 'line', version: 2, x: { kind: 'date', unit: 'date' }, y: { kind: 'number', unit }, data: dates.map((x, j) => ({ x, y: samples[i]?.[j] ?? null, segment_id: 'one', details: [] })) } })),
    events: [], layout: { title: '' }, presentation: { show_legend: true, zoom: true, pan: true, reset: true },
  }
  SLOTS.forEach((slot, i) => {
    const eligible = dates.filter((_, j) => samples[i]?.[j] != null)
    report.distributions.push({ request: { analysis_id: `${metric}/${slot}`, metric, slot, histogram: { unit } }, candidates: keys(slot, dates), binding: keys(slot, eligible), methods: [{ spec: { method: 'interval_count' }, failure_category: eligible.length ? null : 'no_eligible_sample', reason: null, result: eligible.length ? { method: 'interval_count', unit, sample_count: eligible.length } : null }] })
    report.accounting.push({ metric, slot, candidate_count: n, outcomes: ['eligible', 'unavailable', 'excluded', 'not_applicable'].map(status => ({ status, candidate_ratio: null, identities: keys(slot, status === 'eligible' ? eligible : status === 'not_applicable' ? dates.filter(d => !eligible.includes(d)) : []) })) })
  })
  return report
}
