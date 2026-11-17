import type { ReportData } from './types'

// Synthetic V2 producer-shaped input. No market metric is derived in this fixture.
export function readerFixture(): ReportData {
  const metrics = ['basis_value', 'basis_ratio', 'annualized_basis_ratio', 'annualized_basis_value']
  const units = ['index_points', 'decimal_ratio', 'decimal_ratio', 'index_points_per_year']
  const slots = ['M0', 'M1', 'Q1', 'Q2']
  const history = Object.fromEntries(metrics.map((metric, i) => {
    const x = { kind: 'date' as const, unit: 'date' as const }
    const y = { kind: 'number' as const, unit: units[i] }
    return [metric, {
      version: 2 as const,
      axes: [{ id: 'x', orientation: 'x' as const, coordinate: x }, { id: 'y', orientation: 'y' as const, coordinate: y }],
      layers: slots.map(slot => ({
        id: slot, label: slot, x_axis: 'x', y_axis: 'y',
        layer: { version: 2 as const, type: 'line' as const, x, y, data: [] },
      })),
      events: [], layout: { title: '' },
      presentation: { show_legend: true, zoom: true, pan: true, reset: true },
    }]
  }))
  return {
    profile: 'futures_basis_report_evidence_v2', status: 'complete',
    fingerprint: 'synthetic-input-fingerprint', definition_version: 'futures_basis_definition_v2',
    summary: 'Synthetic empty research', sources: 'Synthetic public facts',
    formulas: [], limitations: ['Synthetic fixture only'],
    request: {
      observation: { case: 'futures_basis_v1', product_code: 'IM', start_date: '2024-10-18', end_date: '2024-10-21' },
      quantile: { method: 'quantile', points: [0, .25, .5, .75, 1] },
      histograms: units.map(unit => ({ method: 'interval_count', unit, edges: [-100, 0, 100] })),
    },
    candidate_dates: [], coverage: {}, accounting: [],
    distributions: metrics.flatMap((metric, i) => slots.map(slot => ({
      request: { analysis_id: `${metric}/${slot}`, metric, slot, histogram: { unit: units[i] } },
      candidates: [], binding: [],
      methods: [{ spec: { method: 'interval_count' }, failure_category: 'no_eligible_sample', reason: null, result: null }],
    }))),
    comparisons: [], persistence: [], views: { history, histograms: {} },
  }
}
