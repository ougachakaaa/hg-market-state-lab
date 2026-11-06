import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Report } from './Report'
import type { ReportData } from './types'

afterEach(cleanup)

vi.mock('../../shared/visualization', () => ({ ChartView: () => <div>Producer ChartView</div> }))

function fixture(): ReportData {
  const empty = { version: 2 as const, axes: [], layers: [], events: [], layout: { title: '' }, presentation: { show_legend: true, zoom: true, pan: true, reset: true } }
  return {
    profile: 'futures_basis_report_evidence_v1', status: 'partial', fingerprint: 'retained-fingerprint', definition_version: 'futures_basis_definition_v1',
    summary: '<script>window.injected=true</script>', sources: 'retained source', formulas: ['producer formula'], limitations: ['producer limitation'],
    request: { observation: { product_code: 'IM', start_date: '2024-10-18', end_date: '2024-10-21' } }, candidate_dates: [], coverage: {}, accounting: [],
    distributions: [{ request: { analysis_id: 'basis_value-M0', metric: 'basis_value', slot: 'M0' }, candidates: [], binding: [], methods: [
      { spec: { method: 'mean' }, failure_category: 'CalculationFailure', reason: 'safe producer failure', result: { method: 'mean', value: 999, sample_count: 0, unit: 'index_points' } },
      { spec: { method: 'quantile' }, failure_category: 'no_eligible_sample', reason: 'No eligible candidate dates', result: null },
    ] }],
    comparisons: [{ request: { analysis_id: 'pair', metric: 'basis_value', slots: ['M0', 'M1'] }, common_dates: [], dropped: [['retained-reference']], left_methods: [], right_methods: [], dropped_details: [{ date: '2024-10-18', left: { slot: 'M0', outcome: { status: 'not_applicable', reason: 'expiry_day' } }, right: { slot: 'M1', outcome: { status: 'eligible', reason: null } } }] }],
    persistence: [{ slot: 'M0', complete: [], censored: [{ slot: 'M0', start: '2024-10-18', end: '2024-10-21', observed_trading_sessions: 2, left_boundary: 'window', right_boundary: 'gap', transitions: [] }] }],
    views: { history: { basis_value: empty, basis_ratio: empty, annualized_basis_ratio: empty }, histograms: {} },
  }
}

describe('R01-A reader', () => {
  it('renders six sections, producer failures and empty samples without using a failed raw result', () => {
    const { container } = render(<Report data={fixture()} />)
    expect(container.querySelectorAll('[id^="section-"]')).toHaveLength(6)
    expect(screen.getAllByText('CalculationFailure').length).toBeGreaterThan(0)
    expect(screen.getByText('no_eligible_sample')).toBeTruthy()
    expect(screen.queryByText('999')).toBeNull()
    expect(screen.getByText('safe producer failure')).toBeTruthy()
    expect(screen.getByText('producer limitation')).toBeTruthy()
    expect(screen.getByText('<script>window.injected=true</script>')).toBeTruthy()
    expect(container.querySelector('script')).toBeNull()
  })
  it('exposes common-date loss and censored run limits', () => {
    const { container } = render(<Report data={fixture()} />)
    fireEvent.click(container.querySelector('.ant-table-row-expand-icon')!)
    expect(screen.getByText('M0: not_applicable expiry_day')).toBeTruthy()
    expect(screen.getByText('共同日期：无')).toBeTruthy()
    expect(screen.getByText('window')).toBeTruthy()
    expect(screen.getByText('gap')).toBeTruthy()
  })
})
