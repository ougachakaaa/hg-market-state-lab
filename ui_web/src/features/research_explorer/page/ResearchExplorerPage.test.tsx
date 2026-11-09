import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import ResearchExplorerPage from './ResearchExplorerPage'
import views from '../../../../../market_research/tests/fixtures/publication_visualization_v1.json'
import type { Analysis, Manifest } from '../api/research'

const job = (subject: string) => ({ subject, metric: 'trailing_cumulative_return_v1', metric_parameters: {}, horizon: 2, horizon_unit: 'sessions', start_date: '2020-01-01', end_date: '2020-12-31', bounds: 'inclusive', anchor_meaning: 'end' })
const spec = { method: 'quantile' as const, points: [0.5] }
const summaries: Manifest['analyses'] = [
  { analysis_id: 'analysis-a', request_id: 'same-request', job_identity: job('AAA'), status: 'success', spec, views: [] },
  { analysis_id: 'analysis-b', request_id: 'same-request', job_identity: job('BBB'), status: 'failed', spec, views: [] },
  { analysis_id: 'analysis-c', request_id: 'not-attempted', job_identity: job('BBB'), status: 'not_attempted', spec, views: [] },
]
const manifest: Manifest = { schema_version: 1, publication_id: 'pub-one', status: 'partial_success', context: null,
  source: { sha256: 'digest', size: 123 }, scope: { metric: 'trailing_cumulative_return_v1', metric_parameters: {}, subjects: ['AAA', 'BBB'], horizons: [2], windows: [{ start_date: '2020-01-01', end_date: '2020-12-31' }], analysis_requests: [{ request_id: 'same-request', spec }], on_job_failure: 'continue' },
  jobs: [{ job_identity: job('AAA'), status: 'Success', analyses: ['analysis-a'] }, { job_identity: job('BBB'), status: 'Failed', analyses: ['analysis-b', 'analysis-c'] }], analyses: summaries }
const analysis: Analysis = { schema_version: 1, publication_id: 'pub-one', outcome: 'failed', reason: 'Analysis failed.', result: null, coverage: null, summary: summaries[1] }
const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
const error = (kind: string, status: number) => reply({ error: { kind, detail: 'safe', param: null } }, status)
let release: () => void
beforeEach(() => { release = installRequestBoundary(createRequestBoundary(vi.fn())) })
afterEach(() => { cleanup(); release(); vi.unstubAllGlobals() })

describe('publication discovery', () => {
  it('distinguishes empty store, opaque next page and previous navigation without prefetch', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(reply({ data: [{ publication_id: 'pub-one', status: 'success' }, { publication_id: 'pub-two', status: 'failed' }], next_cursor: 'a+/=' }))
      .mockResolvedValueOnce(reply({ data: [], next_cursor: null }))
      .mockResolvedValueOnce(reply({ data: [{ publication_id: 'pub-one', status: 'success' }], next_cursor: null }))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('pub-one')
    expect(screen.getByText('pub-two')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: '下一页' }))
    await screen.findByText('此页没有 Publication。')
    expect(fetch.mock.calls[1][0]).toBe('/api/research/publications?after=a%2B%2F%3D')
    expect((screen.getByRole('button', { name: '下一页' }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: '上一页' }))
    await screen.findByText('pub-one')
    expect(fetch.mock.calls[2][0]).toBe('/api/research/publications')
  })
  it('can return to the prior page when an opaque cursor has expired', async () => {
    const first = { data: [{ publication_id: 'pub-one', status: 'success' }], next_cursor: 'expired' }
    const fetch = vi.fn().mockResolvedValueOnce(reply(first)).mockResolvedValueOnce(error('invalid_request', 400)).mockResolvedValueOnce(reply(first))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('pub-one')
    fireEvent.click(screen.getByRole('button', { name: '下一页' }))
    await screen.findByText('请求无效或游标已失效。')
    fireEvent.click(screen.getByRole('button', { name: '上一页' }))
    await screen.findByText('pub-one')
    expect(fetch.mock.calls[2][0]).toBe('/api/research/publications')
  })
  it('shows an empty store as empty', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ data: [], next_cursor: null })))
    render(<ResearchExplorerPage />)
    await screen.findByText('Publication Store 为空。')
  })
  it('retries network failure only on request', async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(reply({ data: [], next_cursor: null }))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('无法连接服务。')
    expect(fetch).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: /重\s*试/ }))
    await screen.findByText('Publication Store 为空。')
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})

describe('manifest and failures', () => {
  it('preserves published Job associations when request IDs repeat and loads only the selected Analysis', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(reply({ data: [{ publication_id: 'pub-one', status: 'partial_success' }], next_cursor: null }))
      .mockResolvedValueOnce(reply({ data: manifest })).mockResolvedValueOnce(reply({ data: analysis }))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('pub-one')
    fireEvent.click(screen.getByRole('button', { name: /选\s*择/ }))
    await screen.findByText('声明的 Research scope')
    expect(screen.getAllByText('trailing_cumulative_return_v1').length).toBeGreaterThan(0)
    expect(screen.getByText('digest')).toBeTruthy()
    expect(screen.getAllByText(/same-request —/)).toHaveLength(2)
    expect(screen.getByText('not-attempted — not_attempted')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(2)
    const secondJob = screen.getByText('Job 2 — Failed').closest('.ant-card')!
    fireEvent.click(within(secondJob as HTMLElement).getAllByRole('button', { name: '选择 Analysis' })[0])
    await screen.findByText(/实际结果状态：failed/)
    expect(fetch.mock.calls[2][0]).toBe('/api/research/publications/pub-one/analyses/analysis-b')
    expect(screen.getByText('Coverage unavailable')).toBeTruthy()
    expect(screen.getByText('没有可用的 ChartView')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(3)
  })
  it('allows recovery when a selected Analysis has expired', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(reply({ data: [{ publication_id: 'pub-one', status: 'success' }], next_cursor: null }))
      .mockResolvedValueOnce(reply({ data: manifest })).mockResolvedValueOnce(error('not_found', 404)).mockResolvedValueOnce(reply({ data: analysis }))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('pub-one')
    fireEvent.click(screen.getByRole('button', { name: /选\s*择/ }))
    await screen.findByText('Job 2 — Failed')
    const secondJob = screen.getByText('Job 2 — Failed').closest('.ant-card') as HTMLElement
    fireEvent.click(within(secondJob).getAllByRole('button', { name: '选择 Analysis' })[0])
    await screen.findByText('未找到所选 Analysis。')
    expect(fetch).toHaveBeenCalledTimes(3)
    fireEvent.click(screen.getByRole('button', { name: /重\s*试/ }))
    await screen.findByText(/实际结果状态：failed/)
    expect(fetch.mock.calls[3][0]).toBe('/api/research/publications/pub-one/analyses/analysis-b')
  })
  it.each([
    ['not_found', 404, '未找到所选 Publication。'], ['corrupt', 409, '已存储的内容无效或损坏。'],
    ['inconsistent', 409, 'Publication 的证据关联不一致。'], ['unsupported_version', 409, '不支持此存储版本。'],
    ['response_too_large', 413, '响应超过大小限制。'], ['verification_budget_exceeded', 503, '来源验证容量不足，请稍后手动重试。'],
    ['unavailable', 503, 'Publication 存储或来源不可用。'],
    ['origin_forbidden', 403, '访问被拒绝。'],
  ])('presents %s without treating it as empty and allows returning to list', async (kind, status, message) => {
    const fetch = vi.fn().mockResolvedValueOnce(reply({ data: [{ publication_id: 'pub-one', status: 'success' }], next_cursor: null }))
      .mockResolvedValueOnce(error(kind, status))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('pub-one')
    fireEvent.click(screen.getByRole('button', { name: /选\s*择/ }))
    await screen.findByText(message)
    expect(screen.queryByText('Publication Store 为空。')).toBeNull()
    expect(fetch).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByRole('button', { name: '返回列表' }))
    await waitFor(() => expect(screen.queryByText(message)).toBeNull())
  })
})


describe('selected results and views', () => {
  const intervalSpec = { method: 'interval_count' as const, edges: [-1, 0, 1], unit: 'decimal_ratio' as const }
  const intervalSummary: Manifest['analyses'][number] = { ...summaries[0], spec: intervalSpec, views: [{ measure: 'count', view_id: 'count-id' }, { measure: 'frequency', view_id: 'frequency-id' }] }
  const intervalManifest: Manifest = { ...manifest, analyses: [intervalSummary], jobs: [{ ...manifest.jobs[0], analyses: ['analysis-a'] }] }
  const intervalAnalysis: Analysis = { ...analysis, summary: intervalSummary, outcome: 'success', reason: null, result: { method: 'interval_count', sample_count: 2, unit: 'decimal_ratio', edges: [-1, 0, 1], bins: [{ left: -1, right: 0, left_inclusive: true, right_inclusive: false, count: 0, frequency: 0 }, { left: 0, right: 1, left_inclusive: true, right_inclusive: true, count: 2, frequency: 1 }], underflow_count: 0, underflow_frequency: 0, overflow_count: 0, overflow_frequency: 0 } }
  async function openAnalysis(viewResponses: Response[]) {
    const fetch = vi.fn().mockResolvedValueOnce(reply({ data: [{ publication_id: 'pub-one', status: 'success' }], next_cursor: null }))
      .mockResolvedValueOnce(reply({ data: intervalManifest })).mockResolvedValueOnce(reply({ data: intervalAnalysis }))
    viewResponses.forEach(response => fetch.mockResolvedValueOnce(response))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchExplorerPage />)
    await screen.findByText('pub-one')
    fireEvent.click(screen.getByRole('button', { name: /选\s*择/ }))
    fireEvent.click(await screen.findByRole('button', { name: '选择 Analysis' }))
    await screen.findByText('Bin 1')
    return fetch
  }
  it('loads only the chosen View ID, switches count to frequency and preserves the result table', async () => {
    const fetch = await openAnalysis([reply({ data: views[1] }), reply({ data: views[2] })])
    expect(fetch).toHaveBeenCalledTimes(3)
    fireEvent.click(screen.getByRole('button', { name: 'count' }))
    await screen.findByTestId('plot')
    expect(fetch.mock.calls[3][0]).toBe('/api/research/publications/pub-one/views/count-id')
    fireEvent.click(screen.getByRole('button', { name: 'frequency' }))
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(5))
    await screen.findByTestId('plot')
    expect(fetch.mock.calls[4][0]).toBe('/api/research/publications/pub-one/views/frequency-id')
    expect(screen.getByText('Bin 1')).toBeTruthy()
    expect(screen.getByText('Underflow')).toBeTruthy()
  })
  it('reports a valid View whose bar coordinate the renderer does not support', async () => {
    const unsupported = structuredClone(views[1])
    unsupported.axes[0].coordinate = { kind: 'number', unit: 'index' }
    unsupported.layers[0].layer.x = { kind: 'number', unit: 'index' }
    unsupported.layers[0].layer.data = unsupported.layers[0].layer.data.map((mark, i) => ({ ...mark, x: i }))
    await openAnalysis([reply({ data: unsupported })])
    fireEvent.click(screen.getByRole('button', { name: 'count' }))
    await screen.findByText('当前渲染器不支持此 View。')
    expect(screen.queryByTestId('plot')).toBeNull()
  })
  it('allows manual retry after a capacity error without silently retrying', async () => {
    const fetch = await openAnalysis([error('verification_budget_exceeded', 503), reply({ data: views[1] })])
    fireEvent.click(screen.getByRole('button', { name: 'count' }))
    await screen.findByText('来源验证容量不足，请稍后手动重试。')
    expect(fetch).toHaveBeenCalledTimes(4)
    fireEvent.click(screen.getByRole('button', { name: /重\s*试/ }))
    await screen.findByTestId('plot')
    expect(fetch).toHaveBeenCalledTimes(5)
    expect(fetch.mock.calls[4][0]).toBe('/api/research/publications/pub-one/views/count-id')
  })
  it.each([
    [error('not_found', 404), '未找到所选 View。'],
    [error('verification_budget_exceeded', 503), '来源验证容量不足，请稍后手动重试。'],
    [reply({ data: { version: 2 } }), 'ChartView 格式无效或不兼容。'],
  ])('shows selected View failures without discarding the Analysis', async (failure, message) => {
    const fetch = await openAnalysis([failure])
    fireEvent.click(screen.getByRole('button', { name: 'count' }))
    await screen.findByText(message)
    expect(screen.getByText('Bin 1')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(4)
  })
})
