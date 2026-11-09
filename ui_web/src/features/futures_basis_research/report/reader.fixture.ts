import type { ReportData } from './types'
export function readerFixture(): ReportData {
  const empty = { version: 2 as const, axes: [], layers: [], events: [], layout: { title: '' }, presentation: { show_legend: true, zoom: true, pan: true, reset: true } }
  return {
    profile: 'futures_basis_report_evidence_v1', status: 'complete', fingerprint: 'synthetic-input-fingerprint', definition_version: 'futures_basis_definition_v1',
    summary: 'Synthetic empty research', sources: 'Synthetic public facts', formulas: [], limitations: ['Synthetic fixture only'],
    request: { observation: { case: 'futures_basis_v1', product_code: 'IM', start_date: '2024-10-18', end_date: '2024-10-21' }, quantile: { method: 'quantile', points: [0, 0.5, 1] }, histograms: [{ method: 'interval_count', unit: 'index_points', edges: [-100, 0, 100] }] },
    candidate_dates: [], coverage: {}, accounting: [], distributions: [], comparisons: [], persistence: [],
    views: { history: { basis_value: empty, basis_ratio: empty, annualized_basis_ratio: empty }, histograms: {} },
  }
}
