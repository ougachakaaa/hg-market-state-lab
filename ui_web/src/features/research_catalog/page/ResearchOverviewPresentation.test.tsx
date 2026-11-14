import { cleanup, fireEvent, render as baseRender, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import descriptor from '../api/catalog.fixture.json'
import {
  ResearchOverviewPresentation,
  useStaticCatalog,
  type EmbeddedCatalogPayload,
  type ResearchOverviewNavigation,
} from '../presentation'
import { embeddedCatalog } from '../testing/catalogFixture'
import type { ResearchOverviewController } from '../model/catalogPresentation'
import { validateCapabilityDetail } from '../api/validateCatalog'

function Static({ payload = embeddedCatalog, navigation = { openExplorer: vi.fn(), openFuturesBasis: vi.fn() } }: {
  payload?: EmbeddedCatalogPayload
  navigation?: ResearchOverviewNavigation
}) {
  const controller = useStaticCatalog(payload)
  return <ResearchOverviewPresentation controller={controller} mode="static" navigation={navigation} />
}
function render(ui: Parameters<typeof baseRender>[0]) {
  const result = baseRender(ui)
  fireEvent.click(screen.getByRole('button', { name: '能力与访问方式（技术详情）' }))
  return result
}

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

it.each(['loading', 'success', 'error', 'invalid'] as const)('keeps study cards independent of %s capability discovery', status => {
  const controller: ResearchOverviewController = {
    list: status === 'success' ? { status, data: [] }
      : status === 'loading' ? { status } : { status, error: new Error('fixture') },
    detail: { status: 'idle' }, selection: null,
    selectOnline: vi.fn(), selectLocal: vi.fn(), retryList: vi.fn(),
  }
  const navigation = { openFuturesBasis: vi.fn(), openExplorer: vi.fn() }
  const { container } = baseRender(<ResearchOverviewPresentation controller={controller} mode="production" navigation={navigation} />)
  expect(screen.getByRole('button', { name: '能力与访问方式（技术详情）' }).getAttribute('aria-expanded')).toBe('false')
  for (const [title, status] of [['历史基差研究', '已完成'], ['价格分段研究', '未完成'], ['指数滚动收益研究', '未完成']]) {
    const heading = screen.getByRole('heading', { name: title })
    const card = heading.closest('.ant-card')!
    expect(within(card as HTMLElement).getByText(status)).toBeTruthy()
    if (status === '未完成') expect(card.querySelector('button, a, [tabindex]')).toBeNull()
  }
  const action = screen.getByRole('button', { name: '查看历史基差研究' })
  action.focus()
  expect(document.activeElement).toBe(action)
  fireEvent.click(action)
  expect(navigation.openFuturesBasis).toHaveBeenCalledOnce()
  fireEvent.click(screen.getByRole('button', { name: '浏览研究成果' }))
  expect(navigation.openExplorer).toHaveBeenCalledOnce()
  expect(controller.selectOnline).not.toHaveBeenCalled()
  expect(controller.selectLocal).not.toHaveBeenCalled()
  expect(container.textContent).not.toContain('live readiness')
  if (status === 'error' || status === 'invalid') expect(screen.getByRole('alert')).toBeTruthy()
})

it.each(['error', 'missing', 'mismatch'] as const)('keeps %s detail feedback visible while technical details are collapsed', state => {
  const capability = validateCapabilityDetail(descriptor)
  const controller: ResearchOverviewController = {
    list: { status: 'success', data: [capability] },
    detail: state === 'error' ? { status: 'error', error: new Error('fixture') }
      : state === 'missing' ? { status: 'missing', id: descriptor.id }
        : { status: 'success', data: { ...capability, id: 'mismatched' } },
    selection: { kind: 'online', id: descriptor.id },
    selectOnline: vi.fn(), selectLocal: vi.fn(), retryDetail: vi.fn(),
  }
  baseRender(<ResearchOverviewPresentation controller={controller} mode="static"
    navigation={{ openExplorer: vi.fn(), openFuturesBasis: vi.fn() }} sourceDisclosure="Explicit source fixture" />)
  expect(screen.getByRole('alert').textContent).toContain(state === 'error' ? '能力详情暂不可用'
    : state === 'missing' ? '静态能力详情未嵌入' : '能力身份不匹配')
  expect(screen.getByText('Explicit source fixture')).toBeTruthy()
  expect(screen.getByRole('button', { name: '能力与访问方式（技术详情）' }).getAttribute('aria-expanded')).toBe('false')
})

it('renders validated embedded capability facts with explicit static origin and no request', () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  render(<Static />)
  expect(screen.getByText(/Embedded Capability Example · 静态能力描述，不代表当前服务状态/)).toBeTruthy()
  expect(screen.getByText(descriptor.name)).toBeTruthy()
  expect(screen.getByText('实现：supported')).toBeTruthy()
  expect(screen.getByText('live readiness: not_probed')).toBeTruthy()
  expect(screen.getByText('嵌入能力示例')).toBeTruthy()
  expect(screen.getByText('Price Segmentation')).toBeTruthy()
  expect(screen.getByText('独立在线页面 · 独立离线报告生成')).toBeTruthy()
  expect(screen.queryByRole('button', { name: '重试目录' })).toBeNull()

  fireEvent.click(within(screen.getByRole('region', { name: '在线能力发现' })).getByRole('button', { name: '查看详情' }))
  const selected = screen.getByRole('region', { name: '所选研究详情' })
  expect(within(selected).getByText(descriptor.id)).toBeTruthy()
  expect(within(selected).getByText(/supported · live readiness: not_probed/)).toBeTruthy()
  expect(within(selected).getByText(/静态演示不执行认证 GET/)).toBeTruthy()
  expect(within(selected).getByText(/不是默认值/)).toBeTruthy()
  expect(screen.getAllByText(/Embedded Capability Example/)).toHaveLength(2)
  fireEvent.click(within(selected).getByRole('button', { name: '完整能力描述（原始字段）' }))
  expect(JSON.parse(within(selected).getByText(text => text.startsWith('{') && text.includes('statistics_validator')).textContent!)).toEqual(descriptor)
  expect(fetch).not.toHaveBeenCalled()
})

it('selects local cases without retaining online detail and invokes injected navigation', () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  const openExplorer = vi.fn()
  const openFuturesBasis = vi.fn()
  render(<Static navigation={{ openExplorer, openFuturesBasis }} />)
  const online = screen.getByRole('region', { name: '在线能力发现' })
  fireEvent.click(within(online).getByRole('button', { name: '查看详情' }))
  expect(screen.getByText(/supported · live readiness: not_probed/)).toBeTruthy()

  const local = screen.getByRole('region', { name: '本地研究与离线工作流' })
  fireEvent.click(within(local).getAllByRole('button', { name: '查看详情' })[0])
  const selected = screen.getByRole('region', { name: '所选研究详情' })
  expect(within(selected).getByText(/observe_price_segments/)).toBeTruthy()
  expect(within(selected).queryByText(/supported · live readiness: not_probed/)).toBeNull()
  expect(within(selected).queryByText('静态能力详情未嵌入')).toBeNull()
  expect(within(selected).getByText(/静态演示不执行 Python、在线 Run 或报告生成/)).toBeTruthy()
  expect(fetch).not.toHaveBeenCalled()

  fireEvent.click(within(local).getByRole('button', { name: '进入历史基差研究' }))
  expect(openFuturesBasis).toHaveBeenCalledOnce()
  fireEvent.click(screen.getByRole('button', { name: '浏览研究成果' }))
  expect(openExplorer).toHaveBeenCalledOnce()
})

it('shows an explicit static empty list without implying an online query', () => {
  render(<Static payload={{ list: [], details: [] }} />)
  expect(screen.getByText('嵌入的静态能力示例为空；这不代表当前在线服务没有已发布能力。')).toBeTruthy()
  expect(screen.getByText('Price Segmentation')).toBeTruthy()
  expect(screen.queryByRole('button', { name: '重试目录' })).toBeNull()
  expect(within(screen.getByRole('region', { name: '在线能力发现' })).queryByRole('button', { name: '查看详情' })).toBeNull()
})

it('shows an honest missing-detail state instead of fabricating a successful response', () => {
  render(<Static payload={{ list: [descriptor], details: [] }} />)
  fireEvent.click(within(screen.getByRole('region', { name: '在线能力发现' })).getByRole('button', { name: '查看详情' }))
  const selected = screen.getByRole('region', { name: '所选研究详情' })
  expect(screen.getByText('静态能力详情未嵌入')).toBeTruthy()
  expect(within(selected).queryByText('身份与用途')).toBeNull()
  expect(within(selected).queryByRole('button', { name: '完整能力描述（原始字段）' })).toBeNull()
  expect(screen.queryByRole('button', { name: '重试详情' })).toBeNull()
})

it.each([
  ['invalid list', { list: [{ id: 'fabricated' }], details: [] }],
  ['invalid detail', { list: [descriptor], details: [{ id: 'broken' }] }],
  ['duplicate list identity', { list: [descriptor, descriptor], details: [] }],
  ['duplicate detail identity', { list: [descriptor], details: [descriptor, descriptor] }],
  ['detail outside the list', { list: [descriptor], details: [{ ...descriptor, id: 'not_in_list' }] }],
] as const)('rejects an %s as a static error instead of a ready result', (_label, payload) => {
  render(<Static payload={payload as EmbeddedCatalogPayload} />)
  expect(screen.getByText('静态能力示例无效')).toBeTruthy()
  expect(screen.queryByText(descriptor.name)).toBeNull()
  expect(within(screen.getByRole('region', { name: '在线能力发现' })).queryByRole('button', { name: '查看详情' })).toBeNull()
  expect(screen.queryByRole('button', { name: /重试/ })).toBeNull()
})
