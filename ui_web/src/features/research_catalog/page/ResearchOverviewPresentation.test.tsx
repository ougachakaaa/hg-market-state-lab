import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import descriptor from '../api/catalog.fixture.json'
import {
  ResearchOverviewPresentation,
  useStaticCatalog,
  type EmbeddedCatalogPayload,
  type ResearchOverviewNavigation,
} from '../presentation'
import { embeddedCatalog } from '../testing/catalogFixture'

function Static({ payload = embeddedCatalog, navigation = { openExplorer: vi.fn(), openFuturesBasis: vi.fn() } }: {
  payload?: EmbeddedCatalogPayload
  navigation?: ResearchOverviewNavigation
}) {
  const controller = useStaticCatalog(payload)
  return <ResearchOverviewPresentation controller={controller} mode="static" navigation={navigation} />
}
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

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
  fireEvent.click(screen.getByRole('button', { name: '浏览已发布研究结果' }))
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
  expect(within(selected).getByText('静态能力详情未嵌入')).toBeTruthy()
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
