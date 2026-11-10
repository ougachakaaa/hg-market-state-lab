import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Report } from './Report'
import { validateReportData } from './validate'
import { readerFixture } from './reader.fixture'
vi.mock('../../../shared/visualization', () => ({ ChartView: ({ options }: any) => <div data-testid="chart-mode">{options?.ordinalDates ? 'trading' : 'calendar'}</div> }))
afterEach(cleanup)
describe('shared reader', () => {
  it('renders six online sections, explicit empty coverage and online-only disclosure', () => {
    const { container } = render(<Report data={readerFixture()} mode="online" />)
    expect(container.querySelectorAll('[id^="section-"]')).toHaveLength(6)
    expect(screen.getByText('0；无..无')).toBeTruthy()
    expect(screen.getByText(/完整离线证据包及 Verify/)).toBeTruthy()
    expect(screen.queryByText(/相邻 inputs.canonical.json/)).toBeNull()
  })
  it('retains offline evidence disclosure with the identical reader', () => {
    render(<Report data={readerFixture()} mode="offline" />)
    expect(screen.getByText(/相邻 inputs.canonical.json/)).toBeTruthy()
  })
  it('validates V1 and V2 Views and rejects malformed reader presentation fields', () => {
    const data = readerFixture()
    validateReportData(data)
    data.views.histograms['synthetic/count'] = { version: 1, axes: [], layers: [], layout: { title: '' }, presentation: { show_legend: true } }
    // Reuse the generic V1 validator rather than defining another chart schema.
    expect(() => validateReportData(data)).not.toThrow()
    for (const change of [
      (d: any) => { d.views.history.basis_value.version = 99 },
      (d: any) => { d.comparisons = [{ request: {} }] },
      (d: any) => { d.coverage = { futures: { requested_units: 'bad' } } },
      (d: any) => { d.persistence = [{ slot: 'M0', complete: [{}], censored: [] }] },
      (d: any) => { d.distributions = [{ request: { analysis_id: 'a', metric: 'b' }, candidates: [], binding: [], methods: [] }] },
    ]) {
      const invalid = structuredClone(readerFixture()); change(invalid)
      expect(() => validateReportData(invalid)).toThrow()
    }
  })
})

it('composes a standalone offline title and subordinate online report title without mutating producer data', () => {
  const data = readerFixture()
  const before = structuredClone(data)
  const online = render(<Report data={data} mode="online" />)
  expect(screen.queryByRole('heading', { level: 1 })).toBeNull()
  expect(screen.getByRole('heading', { level: 3, name: '研究报告' })).toBeTruthy()
  online.unmount()
  render(<Report data={data} mode="offline" />)
  expect(screen.getByRole('heading', { level: 1, name: 'IM 历史基差研究报告' })).toBeTruthy()
  expect(data).toEqual(before)
})

it.each(['online', 'offline'] as const)('defaults all history charts to Trading Days and switches together (%s)', mode => {
  const data = readerFixture(); const before = structuredClone(data)
  render(<Report data={data} mode={mode} />)
  expect(screen.getAllByTestId('chart-mode').map(e => e.textContent)).toEqual(['trading', 'trading', 'trading'])
  fireEvent.click(screen.getByText('Calendar Days'))
  expect(screen.getAllByTestId('chart-mode').map(e => e.textContent)).toEqual(['calendar', 'calendar', 'calendar'])
  fireEvent.click(screen.getByText('Trading Days'))
  expect(screen.getAllByTestId('chart-mode').map(e => e.textContent)).toEqual(['trading', 'trading', 'trading'])
  expect(data).toEqual(before)
})

it('formats Overview, quantiles, intervals and paired means by explicit result unit', () => {
  const data = readerFixture()
  const methods = [
    { spec: { method: 'mean' }, failure_category: null, reason: null, result: { method: 'mean', unit: 'decimal_ratio', sample_count: 2, value: .15342 } },
    { spec: { method: 'quantile' }, failure_category: null, reason: null, result: { method: 'quantile', unit: 'decimal_ratio', sample_count: 2, points_and_values: [[.5, -.0868] as [number, number]] } },
    { spec: { method: 'interval_count' }, failure_category: null, reason: null, result: { method: 'interval_count', unit: 'decimal_ratio', sample_count: 2, edges: [-.1, 0], bins: [{ left: -.1, right: 0, left_inclusive: true, right_inclusive: false, count: 1, frequency: .5 }], underflow_count: 0, overflow_count: 1, underflow_frequency: 0, overflow_frequency: .5 } },
  ]
  // Result units drive presentation even when no metric-name mapping is available.
  data.distributions = [{ request: { analysis_id: 'ratio', metric: 'basis_value', slot: 'M0' }, candidates: [], binding: [], methods }]
  data.comparisons = [{ request: { analysis_id: 'pair', metric: 'basis_value', slots: ['M0', 'M1'] }, common_dates: [], dropped: [], dropped_details: [], left_methods: methods, right_methods: methods }]
  const before = structuredClone(data)
  const { container } = render(<Report data={data} mode="online" />)
  expect(screen.getByText('15.3%')).toBeTruthy()
  expect(screen.getByText('Mean：15.3%')).toBeTruthy()
  expect(screen.getByText('-8.7%')).toBeTruthy()
  expect(screen.getByText('[-10.0%, 0.0%)')).toBeTruthy()
  expect(screen.getAllByText('0.5').length).toBeGreaterThan(0) // Quantile probability remains raw.
  fireEvent.click(container.querySelector('#section-3 .ant-table-row-expand-icon')!)
  expect(screen.getAllByText('Mean：15.3%')).toHaveLength(3)
  expect(data).toEqual(before)
})
