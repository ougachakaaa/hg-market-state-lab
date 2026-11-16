import { histogramFixture } from '../model/histogramAggregation.fixture'
import { BIN_PRESETS, type BasisMetric } from '../model/histogramAggregation'
import { cleanup, fireEvent, render, screen, within, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Report } from './Report'
import { validateReportData } from './validate'
import { readerFixture } from './reader.fixture'
// Keep the reader's real mode state; stub only the shared renderer/control boundary.
vi.mock('../../../shared/visualization', () => ({
  ChartView: ({ options }: any) => <div data-testid="chart-mode" data-disclosure={options?.dateEventsDisclosure?.description} data-missing={options?.missingValuesDisclosure?.title}>{options?.ordinalDates ? 'trading' : 'calendar'}</div>,
  DateAxisControl: ({ value, onChange, label }: any) => <div aria-label={label}>
    {[['trading', 'Trading Days'], ['calendar', 'Calendar Days']].map(([mode, text]) =>
      <button key={mode} onClick={() => onChange(mode)}>{text}</button>)}
    <span data-testid="chart-mode-state">{value}</span>
  </div>,
  DEFAULT_DATE_AXIS_MODE: 'trading',
}))
vi.mock('react-plotly.js', () => ({ default: ({ data }: any) => <div data-testid="distribution-plot" data-traces={JSON.stringify(data)} /> }))
afterEach(cleanup)
describe('shared reader', () => {
  it.each(['online', 'demo'] as const)('renders one compact report with charts before the summary (%s)', mode => {
    const { container } = render(<Report data={readerFixture()} mode={mode} />)
    expect(container.querySelectorAll('.ant-card')).toHaveLength(1)
    expect(screen.queryByRole('navigation', { name: '报告章节' })).toBeNull()
    const toggle = screen.getByRole('button', { name: '指标定义与公式' })
    expect(toggle.getAttribute('aria-expanded')).toBe('false')
    fireEvent.click(toggle)
    expect(toggle.getAttribute('aria-expanded')).toBe('true')
    const history = screen.getByTestId('history-charts')
    const mean = screen.getByRole('heading', { name: '各 Slot 统计摘要' })
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
  data.distributions = [{ request: { analysis_id: 'ratio', metric: 'basis_value', slot: 'M0' }, candidates: [], binding: [{}, {}], methods }]
  data.comparisons = [{ request: { analysis_id: 'pair', metric: 'basis_value', slots: ['M0', 'M1'] }, common_dates: [], dropped: [], dropped_details: [], left_methods: methods, right_methods: methods }]
  const before = structuredClone(data)
  const { container } = render(<Report data={data} mode="offline" />)
  expect(screen.getByText('15.3%')).toBeTruthy()
  expect(screen.getByText('Mean：15.3%')).toBeTruthy()
  expect(screen.getAllByText('-8.7%')).toHaveLength(2)
  expect(screen.getByText('[-10.0%, 0.0%)')).toBeTruthy()
  expect(screen.queryAllByText('0.5')).toHaveLength(0) // Quantile probability displays as a percentage.
  expect(screen.getAllByText('50.0%').length).toBeGreaterThan(0)
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
  expect(screen.getByText(/展示数据不一致/)).toBeTruthy()
})

it.each(['demo', 'online', 'offline'] as const)('renders four Slots and width controls without producer histogram charts (%s)', mode => {
  const data = histogramFixture([[1, 2], [3], [], [5]])
  const before = structuredClone(data)
  render(<Report data={data} mode={mode} />)
  expect(screen.getAllByTestId('chart-mode')).toHaveLength(3)
  const traces = JSON.parse(screen.getByTestId('distribution-plot').getAttribute('data-traces')!)
  expect(traces.map((t: any) => t.name)).toEqual(['M0', 'M1', 'Q1', 'Q2'])
  expect(screen.getByText('Q1：无有效样本（Eligible N=0）')).toBeTruthy()
  expect(screen.getByRole('combobox', { name: 'Distribution metric' })).toBeTruthy()
  expect(screen.getByRole('combobox', { name: 'Bin width' })).toBeTruthy()
  expect(screen.queryByRole('combobox', { name: 'Distribution slot' })).toBeNull()
  expect(data).toEqual(before)
})

it.each(['online', 'demo', 'offline'] as const)('configures only compact history disclosures (%s)', mode => {
  render(<Report data={readerFixture()} mode={mode} />)
  const configured = screen.getAllByTestId('chart-mode').filter(el => el.hasAttribute('data-disclosure'))
  expect(configured).toHaveLength(mode === 'offline' ? 0 : 3)
})

it.each(['online', 'demo', 'offline'] as const)('shows expiry explanation beside only the annualized chart (%s)', mode => {
  render(<Report data={readerFixture()} mode={mode} />)
  const note = screen.getByText('合约到期日的剩余期限 D=0，年化基差按研究定义主动留空，并非行情数据错误；原始基差仍然保留。')
  expect(note.closest('.ant-collapse')).toBeNull()
  expect(within(note.parentElement!).getAllByTestId('chart-mode')).toHaveLength(1)
  expect(within(note.parentElement!).getByTestId('chart-mode')).toBe(screen.getAllByTestId('chart-mode')[2])
})

it.each(['online', 'demo', 'offline'] as const)('switches four-Slot summaries by Metric independently of Bin Width (%s)', mode => {
  const data = readerFixture()
  data.distributions = ['basis_value', 'basis_ratio'].flatMap(metric => ['M0', 'M1', 'Q1', 'Q2'].map((slot, i) => ({
    request: { analysis_id: `${metric}/${slot}`, metric, slot }, candidates: [{}, {}], binding: [{}, {}], methods: [
      { spec: { method: 'quantile' }, failure_category: null, reason: null, result: {
        method: 'quantile', unit: metric === 'basis_value' ? 'index_points' : 'decimal_ratio', sample_count: 2,
        points_and_values: [[1, .4 + i], [.25, .1 + i], [0, i], [.75, .3 + i], [.5, .2 + i]] as [number, number][],
      } },
      { spec: { method: 'mean' }, failure_category: null, reason: null, result: {
        method: 'mean', unit: metric === 'basis_value' ? 'index_points' : 'decimal_ratio', sample_count: 2, value: .2 + i,
      } },
    ],
  })))
  const before = structuredClone(data)
  render(<Report data={data} mode={mode} />)
  const summary = screen.getByRole('region', { name: '统计摘要' })
  const cells = () => within(summary).getAllByRole('row').slice(1).map(row => within(row).getAllByRole('cell').map(c => c.textContent))
  expect(cells()).toEqual(['M0', 'M1', 'Q1', 'Q2'].map((slot, i) => [slot, '2', `${i}.00`, `${(.1 + i).toFixed(2)}`, `${(.2 + i).toFixed(2)}`, `${(.3 + i).toFixed(2)}`, `${(.4 + i).toFixed(2)}`, `${(.2 + i).toFixed(2)}`]))
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Distribution metric' }))
  fireEvent.click(screen.getByText('basis_ratio', { selector: '.ant-select-item-option-content' }))
  expect(cells()[0]).toEqual(['M0', '2', '0.0%', '10.0%', '20.0%', '30.0%', '40.0%', '20.0%'])
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Bin width' }))
  fireEvent.click(screen.getByText('0.2 个百分点', { selector: '.ant-select-item-option-content' }))
  expect(cells()).toHaveLength(4)
  expect(cells()[0][0]).toBe('M0')
  expect(screen.queryByRole('heading', { name: '各 Slot 统计均值' })).toBeNull()
  expect(data).toEqual(before)
})

it('renders Partial method failures and empty samples without hiding successful statistics', () => {
  const data = readerFixture()
  data.status = 'partial'
  data.distributions = [
    { request: { analysis_id: 'failed', metric: 'basis_value', slot: 'M0' }, candidates: [{}, {}], binding: [{}, {}], methods: [
      { spec: { method: 'mean' }, failure_category: 'CalculationFailure', reason: 'failed', result: { method: 'mean', sample_count: 2, unit: 'index_points', value: 999 } },
      { spec: { method: 'quantile' }, failure_category: null, reason: null, result: { method: 'quantile', sample_count: 2, unit: 'index_points', points_and_values: [[.5, 0]] } },
    ] },
    { request: { analysis_id: 'empty', metric: 'basis_value', slot: 'M1' }, candidates: [], binding: [], methods: [
      { spec: { method: 'mean' }, failure_category: 'no_eligible_sample', reason: 'empty', result: null },
    ] },
  ]
  render(<Report data={data} mode="online" />)
  const rows = within(screen.getByRole('region', { name: '统计摘要' })).getAllByRole('row').slice(1)
  expect(within(rows[0]).getAllByRole('cell').map(c => c.textContent)).toEqual(['M0', '2', '不可用', '不可用', '0.00', '不可用', '不可用', '不可用（CalculationFailure）'])
  expect(within(rows[1]).getAllByRole('cell').map(c => c.textContent)).toEqual(['M1', '0', '不可用', '不可用', '不可用', '不可用', '不可用', '不可用（no_eligible_sample）'])
  expect(screen.getByText(/Partial：/)).toBeTruthy()
})


it('selects every preset and resets width on Metric change without mutating formal summaries', async () => {
  const data = histogramFixture([[-10, 0, 10], [1], [2], [3]])
  for (const metric of ['basis_ratio', 'annualized_basis_ratio'] as const) {
    const fixture = histogramFixture([[.001, 0, -.001], [.01], [.02], [.03]], metric)
    data.views.history[metric] = fixture.views.history[metric]
    data.distributions.push(...fixture.distributions)
    data.accounting.push(...fixture.accounting)
  }
  const before = structuredClone(data)
  render(<Report data={data} mode="demo" />)
  const summary = screen.getByRole('region', { name: '统计摘要' })
  async function select(label: string, text: string) {
    const input = screen.getByRole('combobox', { name: label })
    fireEvent.mouseDown(input)
    await waitFor(() => expect(input.getAttribute('aria-expanded')).toBe('true'))
    fireEvent.click(await screen.findByText(text, { selector: '.ant-select-item-option-content' }))
    await waitFor(() => expect(input.getAttribute('aria-expanded')).toBe('false'))
  }
  for (const metric of Object.keys(BIN_PRESETS) as BasisMetric[]) {
    await select('Distribution metric', metric)
    const unit = metric === 'basis_value' ? '点' : '个百分点'
    expect(screen.getByRole('combobox', { name: 'Bin width' }).closest('.ant-select')?.textContent).toContain(`${BIN_PRESETS[metric].default} ${unit}`)
    const cells = summary.textContent
    for (const width of BIN_PRESETS[metric].widths) {
      await select('Bin width', `${width} ${unit}`)
      expect(summary.textContent).toBe(cells)
      expect(screen.getByTestId('distribution-plot')).toBeTruthy()
    }
  }
  expect(data).toEqual(before)
})

it('stops the entire Metric comparison for a mismatched Slot and retains the summary', () => {
  const data = histogramFixture([[1], [2], [3], [4]])
  data.distributions[2].binding = []
  render(<Report data={data} mode="online" />)
  expect(screen.getByText(/展示数据不一致：Q1/)).toBeTruthy()
  expect(screen.queryByTestId('distribution-plot')).toBeNull()
  expect(screen.getByRole('region', { name: '统计摘要' })).toBeTruthy()
})

it('shows empty and capacity states without a successful plot', () => {
  const first = render(<Report data={histogramFixture([[]])} mode="online" />)
  expect(screen.getByText('无有效样本（Eligible N=0）')).toBeTruthy()
  expect(screen.queryByTestId('distribution-plot')).toBeNull()
  first.unmount()
  render(<Report data={histogramFixture([[0, 1e10]])} mode="online" />)
  expect(screen.getByText(/分箱范围超出展示容量/)).toBeTruthy()
  expect(screen.queryByTestId('distribution-plot')).toBeNull()
})

it('keeps formal IntervalCount failure visible and never plots its stale result', () => {
  const data = histogramFixture([[1], [2], [3], [4]])
  data.status = 'partial'
  data.distributions[0].methods[0].failure_category = 'CalculationFailure'
  render(<Report data={data} mode="online" />)
  expect(screen.getByText('M0：CalculationFailure（Eligible N=1）')).toBeTruthy()
  const traces = JSON.parse(screen.getByTestId('distribution-plot').getAttribute('data-traces')!)
  expect(traces[0].y).toEqual([null])
  expect(traces[1].y).toEqual([1, 1])
})

it('rejects a nonempty Eligible Slot that reports no_eligible_sample instead of hiding its curve', () => {
  const data = histogramFixture([[1], [2], [3], [4]])
  data.distributions[2].methods[0].failure_category = 'no_eligible_sample'
  render(<Report data={data} mode="online" />)
  const status = screen.getByText(/展示数据不一致/)
  expect(status.textContent).toContain('Q1')
  expect(status.textContent).toContain('no_eligible_sample')
  expect(screen.queryByTestId('distribution-plot')).toBeNull()
  expect(screen.getByRole('region', { name: '统计摘要' })).toBeTruthy()
})

it.each(['online', 'demo', 'offline'] as const)('configures all three history disclosures in %s', mode => {
 const data = readerFixture(); const original = structuredClone(data)
 render(<Report data={data} mode={mode} />)
 expect(screen.getAllByTestId('chart-mode').filter(node => node.getAttribute('data-missing') === '无有效指标值日期')).toHaveLength(3)
 expect(data).toEqual(original)
})
