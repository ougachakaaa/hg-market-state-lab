import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Report } from './Report'
import { validateReportData } from './validate'
import { readerFixture } from './reader.fixture'
// Keep the reader's real mode state; stub only the shared renderer/control boundary.
vi.mock('../../../shared/visualization', () => ({
  ChartView: ({ options }: any) => <div data-testid="chart-mode" data-disclosure={options?.dateEventsDisclosure?.description}>{options?.ordinalDates ? 'trading' : 'calendar'}</div>,
  DateAxisControl: ({ value, onChange, label }: any) => <div aria-label={label}>
    {[['trading', 'Trading Days'], ['calendar', 'Calendar Days']].map(([mode, text]) =>
      <button key={mode} onClick={() => onChange(mode)}>{text}</button>)}
    <span data-testid="chart-mode-state">{value}</span>
  </div>,
  DEFAULT_DATE_AXIS_MODE: 'trading',
}))
afterEach(cleanup)
describe('shared reader', () => {
  it.each(['online', 'demo'] as const)('renders one compact report with charts before means (%s)', mode => {
    const { container } = render(<Report data={readerFixture()} mode={mode} />)
    expect(container.querySelectorAll('.ant-card')).toHaveLength(1)
    expect(screen.queryByRole('navigation', { name: '报告章节' })).toBeNull()
    const toggle = screen.getByRole('button', { name: '指标定义与公式' })
    expect(toggle.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(toggle)
    expect(toggle.getAttribute('aria-expanded')).toBe('true')
    const history = screen.getByTestId('history-charts')
    const mean = screen.getByRole('heading', { name: '各 Slot 统计均值' })
    expect(history.compareDocumentPosition(mean) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.queryByText('Producer Report Request')).toBeNull()
    expect(screen.queryByText('数据完整性（各自单位，不相加）')).toBeNull()
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

it.each(['online', 'offline', 'demo'] as const)('defaults all history charts to Trading Days and switches together (%s)', mode => {
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
  const { container } = render(<Report data={data} mode="offline" />)
  expect(screen.getByText('15.3%')).toBeTruthy()
  expect(screen.getByText('Mean：15.3%')).toBeTruthy()
  expect(screen.getByText('-8.7%')).toBeTruthy()
  expect(screen.getByText('[-10.0%, 0.0%)')).toBeTruthy()
  expect(screen.getAllByText('0.5').length).toBeGreaterThan(0) // Quantile probability remains raw.
  fireEvent.click(container.querySelector('#section-3 .ant-table-row-expand-icon')!)
  expect(screen.getAllByText('Mean：15.3%')).toHaveLength(3)
  expect(data).toEqual(before)
})

it('keeps compact local interactions on the static route and suppresses repeated source disclosure', () => {
  window.history.replaceState(null, '', '/#/research/futures-basis')
  render(<Report data={readerFixture()} mode="demo" sourceDisclosure="private source" />)
  fireEvent.click(screen.getByText('Calendar Days'))
  fireEvent.click(screen.getByRole('button', { name: '指标定义与公式' }))
  expect(window.location.hash).toBe('#/research/futures-basis')
  expect(screen.queryByText('private source')).toBeNull()
})

it('retains all six offline sections and fragment links', () => {
  const { container } = render(<Report data={readerFixture()} mode="offline" />)
  expect(container.querySelectorAll('[id^="section-"]')).toHaveLength(6)
  expect(within(screen.getByRole('navigation', { name: '报告章节' })).getAllByRole('link')).toHaveLength(6)
})

it('warns for partial results and presents empty results honestly', () => {
  const data = readerFixture()
  data.status = 'partial'
  data.distributions = []
  render(<Report data={data} mode="online" />)
  expect(screen.getByText(/Partial：研究执行已完成，部分统计方法失败/)).toBeTruthy()
  expect(screen.getByText('无可用分布结果')).toBeTruthy()
})

it.each(['demo', 'online'] as const)('renders producer distribution Count and Frequency with history (%s)', mode => {
  const data = readerFixture()
  data.formulas = ['producer formula']
  data.distributions = [{ request: { analysis_id: 'a', metric: 'basis_value', slot: 'M0' }, candidates: [], binding: [], methods: [{ spec: { method: 'mean' }, failure_category: null, reason: null, result: { method: 'mean', unit: 'index_points', sample_count: 1, value: 12 } }] }]
  data.views.histograms = { 'a/count': data.views.history.basis_value, 'a/frequency': data.views.history.basis_value }
  const before = structuredClone(data)
  render(<Report data={data} mode={mode} />)
  expect(screen.getAllByTestId('chart-mode')).toHaveLength(5)
  expect(screen.getByRole('combobox', { name: 'Distribution metric' })).toBeTruthy()
  expect(screen.getByRole('combobox', { name: 'Distribution slot' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '指标定义与公式' }))
  expect(screen.getByText('producer formula')).toBeTruthy()
  expect(data).toEqual(before)
})

it.each(['online', 'demo', 'offline'] as const)('configures only compact history disclosures (%s)', mode => {
  render(<Report data={readerFixture()} mode={mode} />)
  const configured = screen.getAllByTestId('chart-mode').filter(el => el.hasAttribute('data-disclosure'))
  expect(configured).toHaveLength(mode === 'offline' ? 0 : 3)
})
