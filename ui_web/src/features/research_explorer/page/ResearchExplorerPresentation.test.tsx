import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
import {
  ResearchExplorerPresentation,
  useStaticExplorer,
  type EmbeddedPublicationSetPayload,
} from '../presentation'
import { embeddedPublicationSet, publicationList, publicationViews } from '../testing/publicationFixture'

function Static({ payload = embeddedPublicationSet }: { payload?: EmbeddedPublicationSetPayload }) {
  const controller = useStaticExplorer(payload)
  return <ResearchExplorerPresentation controller={controller} mode="static" />
}
function selectPublication() {
  fireEvent.click(screen.getByRole('button', { name: /^选\s*择$/ }))
}
function selectAnalysis(requestId: string) {
  const item = screen.getByText(`${requestId} — success`).closest('.ant-list-item') as HTMLElement
  fireEvent.click(within(item).getByRole('button', { name: '选择 Analysis' }))
}
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

it('renders the complete embedded Reader without network activity', async () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  render(<Static />)
  expect(screen.getByText(/Embedded Publication Example · 静态 Publication 示例/)).toBeTruthy()
  expect(screen.getByText('pub-static-one')).toBeTruthy()
  expect(screen.getByText('嵌入示例 · 发布状态：success')).toBeTruthy()
  expect(screen.queryByRole('button', { name: '刷新' })).toBeNull()
  expect((screen.getByRole('button', { name: '上一页' }) as HTMLButtonElement).disabled).toBe(true)
  expect((screen.getByRole('button', { name: '下一页' }) as HTMLButtonElement).disabled).toBe(true)

  selectPublication()
  expect(await screen.findByText('声明的 Research scope')).toBeTruthy()
  expect(screen.getByText('Jobs 与 Analysis')).toBeTruthy()
  expect(screen.getByText('Job 1 — Success')).toBeTruthy()
  expect(screen.getByText('Job 2 — Success')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Publication 来源证据' }))
  expect(await screen.findByText('a'.repeat(64))).toBeTruthy()
  expect(screen.getByText(/以上为嵌入示例的 Provenance/)).toBeTruthy()

  selectAnalysis('interval-request')
  expect(await screen.findByText('Bin 1')).toBeTruthy()
  expect(screen.getByText('观察总体与覆盖（原始比例）')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'count' }))
  expect(await screen.findByTestId('plot')).toBeTruthy()
  expect(screen.getByText('View ID: count-id')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'frequency' }))
  expect(await screen.findByTestId('plot')).toBeTruthy()
  expect(screen.getByText('View ID: frequency-id')).toBeTruthy()

  selectAnalysis('quantile-request')
  expect(await screen.findByText('325.0%')).toBeTruthy()
  expect(screen.getByText('type7_linear_v1')).toBeTruthy()
  expect(screen.queryByTestId('plot')).toBeNull()
  expect(screen.queryByText('View ID: frequency-id')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'quantile' }))
  expect(await screen.findByTestId('plot')).toBeTruthy()
  expect(screen.getByText('View ID: quantile-id')).toBeTruthy()
  expect(screen.queryByRole('button', { name: /重试/ })).toBeNull()
  expect(fetch).not.toHaveBeenCalled()
})

it('paginates embedded pages locally and preserves the selection contract', async () => {
  const payload: EmbeddedPublicationSetPayload = {
    ...embeddedPublicationSet,
    pages: [
      publicationList,
      { data: [{ publication_id: 'pub-two', status: 'success' }], next_cursor: null },
    ],
  }
  render(<Static payload={payload} />)
  expect(screen.getByText('当前第 1 页')).toBeTruthy()
  expect((screen.getByRole('button', { name: '上一页' }) as HTMLButtonElement).disabled).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: '下一页' }))
  expect(await screen.findByText('pub-two')).toBeTruthy()
  expect(screen.getByText('当前第 2 页')).toBeTruthy()
  expect((screen.getByRole('button', { name: '下一页' }) as HTMLButtonElement).disabled).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: '上一页' }))
  expect(await screen.findByText('pub-static-one')).toBeTruthy()
})

it('selecting a Publication resets Analysis and View; selecting an Analysis resets View', async () => {
  render(<Static />)
  selectPublication()
  selectAnalysis('interval-request')
  fireEvent.click(await screen.findByRole('button', { name: 'count' }))
  expect(await screen.findByTestId('plot')).toBeTruthy()
  selectPublication()
  expect(screen.queryByText('所选 Analysis')).toBeNull()
  expect(screen.queryByTestId('plot')).toBeNull()
  selectAnalysis('interval-request')
  fireEvent.click(await screen.findByRole('button', { name: 'count' }))
  expect(await screen.findByTestId('plot')).toBeTruthy()
  selectAnalysis('quantile-request')
  expect(screen.queryByTestId('plot')).toBeNull()
  expect(screen.queryByRole('button', { name: 'count' })).toBeNull()
})

it('shows explicit static empty and invalid states without fabricating records', () => {
  const { rerender } = render(<Static key="empty" payload={{ pages: [{ data: [], next_cursor: null }], manifests: [], analyses: [], views: [] }} />)
  expect(screen.getByText('当前静态示例未嵌入 Publication；不代表在线 Publication Store 为空。')).toBeTruthy()
  expect(screen.queryByRole('button', { name: '选择' })).toBeNull()
  rerender(<Static key="invalid" payload={{ pages: [{ data: [{ publication_id: 'broken', status: 'bogus' }], next_cursor: null }], manifests: [], analyses: [], views: [] }} />)
  expect(screen.getByText('静态 Publication 示例无效')).toBeTruthy()
  expect(screen.queryByText('broken')).toBeNull()
  expect(screen.queryByRole('button', { name: '刷新' })).toBeNull()
})

it('shows honest missing Manifest, Analysis and ChartView states', async () => {
  const { rerender } = render(<Static key="missing-manifest" payload={{ ...embeddedPublicationSet, manifests: [], analyses: [], views: [] }} />)
  selectPublication()
  expect(await screen.findByText('静态 Manifest 未嵌入')).toBeTruthy()
  expect(screen.queryByText('声明的 Research scope')).toBeNull()

  rerender(<Static key="missing-analysis" payload={{ ...embeddedPublicationSet, analyses: [] }} />)
  selectPublication()
  selectAnalysis('interval-request')
  expect(await screen.findByText('静态 Analysis 未嵌入')).toBeTruthy()
  expect(screen.queryByText('Bin 1')).toBeNull()

  rerender(<Static key="missing-view" payload={{ ...embeddedPublicationSet, views: [] }} />)
  selectPublication()
  selectAnalysis('interval-request')
  fireEvent.click(await screen.findByRole('button', { name: 'count' }))
  expect(await screen.findByText('静态 ChartView 未嵌入')).toBeTruthy()
  expect(screen.queryByTestId('plot')).toBeNull()
  expect(screen.queryByRole('button', { name: /重试/ })).toBeNull()
})

it('renders a valid View that the shared renderer does not support as an explicit warning', async () => {
  const payload: EmbeddedPublicationSetPayload = structuredClone(embeddedPublicationSet)
  const count = payload.views.find(item => item.view_id === 'count-id')!
  const view = count.view as {
    axes: { coordinate: unknown }[]
    layers: { layer: { x: unknown; data: Record<string, unknown>[] } }[]
  }
  view.axes[0].coordinate = { kind: 'number', unit: 'index' }
  view.layers[0].layer.x = { kind: 'number', unit: 'index' }
  view.layers[0].layer.data = view.layers[0].layer.data.map((mark, index) => ({ ...mark, x: index }))
  render(<Static payload={payload} />)
  selectPublication()
  selectAnalysis('interval-request')
  fireEvent.click(await screen.findByRole('button', { name: 'count' }))
  expect(await screen.findByText('当前渲染器不支持此 View。')).toBeTruthy()
  expect(screen.queryByTestId('plot')).toBeNull()
})

it('rejects an invalid embedded ChartView instead of showing it', () => {
  const payload: EmbeddedPublicationSetPayload = structuredClone(embeddedPublicationSet)
  payload.views = [{ ...publicationViews[0], view: { version: 2 } }]
  render(<Static payload={payload} />)
  expect(screen.getByText('静态 Publication 示例无效')).toBeTruthy()
  expect(screen.queryByText('pub-static-one')).toBeNull()
})
