import { cleanup, fireEvent, render as baseRender, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import {
  ResearchOverviewPresentation,
  useStaticCatalog,
  type EmbeddedCatalogPayload,
  type ResearchOverviewNavigation,
} from '../presentation'
import { embeddedCatalog } from '../testing/catalogFixture'
import type { ResearchOverviewController } from '../model/catalogPresentation'

function Static({ payload = embeddedCatalog, navigation = { openExplorer: vi.fn(), openFuturesBasis: vi.fn() } }: {
  payload?: EmbeddedCatalogPayload
  navigation?: ResearchOverviewNavigation
}) {
  const controller = useStaticCatalog(payload)
  return <ResearchOverviewPresentation controller={controller} mode="static" navigation={navigation} />
}
function render(ui: Parameters<typeof baseRender>[0]) {
  const result = baseRender(ui)
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
  expect(screen.queryByRole('button', { name: '能力与访问方式（技术详情）' })).toBeNull()
  for (const [title, status] of [['历史基差研究', '已完成'], ['价格分段研究', '未完成'], ['指数滚动收益研究', '未完成']]) {
    const heading = screen.getByRole('heading', { name: title })
    const card = heading.closest('.ant-card')!
    expect(within(card as HTMLElement).getByText(status).classList.contains(status === '已完成' ? 'ant-typography-success' : 'ant-typography-secondary')).toBe(true)
    if (status === '未完成') expect(card.querySelector('button, a, [tabindex]')).toBeNull()
  }
  const action = screen.getByRole('button', { name: '查看历史基差研究' })
  action.focus()
  expect(document.activeElement).toBe(action)
  fireEvent.click(action)
  expect(navigation.openFuturesBasis).toHaveBeenCalledOnce()
  expect(screen.queryByRole('button', { name: '浏览研究成果' })).toBeNull()
  expect(navigation.openExplorer).not.toHaveBeenCalled()
  expect(controller.selectOnline).not.toHaveBeenCalled()
  expect(controller.selectLocal).not.toHaveBeenCalled()
  expect(container.textContent).not.toContain('live readiness')
  expect(screen.queryByRole('alert')).toBeNull()
})


it('preserves static disclosure and makes no request', () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  render(<Static />)
  expect(screen.getByRole('note')).toBeTruthy()
  expect(screen.queryByText(/live readiness/)).toBeNull()
  expect(fetch).not.toHaveBeenCalled()
})

it('routes the new completed Production study through its independent callback and omits it in Static', () => {
  const navigation = { openExplorer: vi.fn(), openFuturesBasis: vi.fn(), openCalendarSpread: vi.fn() }
  const controller = { list: { status: 'success', data: [] }, detail: { status: 'idle' }, selection: null, selectOnline: vi.fn(), selectLocal: vi.fn() } as ResearchOverviewController
  const { rerender } = baseRender(<ResearchOverviewPresentation controller={controller} mode="production" navigation={navigation} />)
  fireEvent.click(screen.getByRole('button', { name: '查看历史跨期相对价值研究' }))
  expect(navigation.openCalendarSpread).toHaveBeenCalledOnce()
  expect(navigation.openFuturesBasis).not.toHaveBeenCalled()
  rerender(<ResearchOverviewPresentation controller={controller} mode="static" navigation={navigation} />)
  expect(screen.queryByRole('heading', { name: '历史跨期相对价值研究' })).toBeNull()
  expect(screen.queryByRole('button', { name: /Explorer/ })).toBeNull()
})
