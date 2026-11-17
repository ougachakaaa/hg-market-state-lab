import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import ApplicationShell from './ApplicationShell'
import AppUiProvider from './AppUiProvider'

afterEach(cleanup)
it('orders areas and directly exposes implemented studies with selection and collapse', () => {
  const navigate = vi.fn()
  const { container, rerender } = render(<AppUiProvider>
    <ApplicationShell path="/research/futures-basis" href={path => path} navigate={navigate}
      header={null}>Study</ApplicationShell>
  </AppUiProvider>)
  const menu = screen.getByRole('menu', { name: '业务导航' })
  expect([...menu.children].map(item => item.textContent)).toEqual([
    expect.stringContaining('日常数据'), expect.stringContaining('研究'), expect.stringContaining('回测'),
  ])
  expect(container.querySelector('.ant-menu-item-selected')?.textContent).toBe('历史基差研究')
  expect(screen.queryByText('DESCRIPTIVE RESEARCH')).toBeNull()
  fireEvent.click(screen.getByRole('link', { name: '研究总览' }))
  expect(navigate).toHaveBeenCalledWith('/research')
  fireEvent.click(screen.getByRole('button', { name: '折叠导航' }))
  expect(screen.getByRole('button', { name: '展开导航' }).getAttribute('aria-expanded')).toBe('false')
  fireEvent.click(screen.getByRole('button', { name: '展开导航' }))
  rerender(<AppUiProvider>
    <ApplicationShell path="/data" href={path => path} navigate={navigate} header={null}>Data</ApplicationShell>
  </AppUiProvider>)
  expect(container.querySelector('.ant-menu-item-selected')?.textContent).toBe('数据总览')
})
it('composes arbitrary header/content and receives runtime-specific navigation hrefs', () => {
  const navigate = vi.fn()
  const { container, rerender } = render(<AppUiProvider>
    <ApplicationShell path="/research/publications" href={path => `#${path}`} navigate={navigate}
      header={<span>Anonymous disclosure</span>}><h1>Injected content</h1></ApplicationShell>
  </AppUiProvider>)
  expect(screen.getByText('Anonymous disclosure')).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'Injected content' })).toBeTruthy()
  expect(container.querySelector('.ant-menu-item-selected')).toBeNull()
  expect(screen.getByText('Research Explorer')).toBeTruthy()
  const breadcrumb = screen.getByRole('link', { name: '研究' })
  expect(breadcrumb.getAttribute('href')).toBe('#/research')
  fireEvent.click(breadcrumb)
  expect(navigate).toHaveBeenCalledWith('/research')
  expect(screen.queryByRole('link', { name: 'Research Explorer' })).toBeNull()
  rerender(<AppUiProvider>
    <ApplicationShell path="/research/publications" href={path => path} navigate={navigate}
      header={<span>Production identity</span>}><h1>Other content</h1></ApplicationShell>
  </AppUiProvider>)
  expect(screen.getByRole('link', { name: '研究' }).getAttribute('href')).toBe('/research')
  expect(screen.queryByText('Anonymous disclosure')).toBeNull()
  expect(screen.getByText('Production identity')).toBeTruthy()
})

it('groups Backtesting overview and instance with matching icon roles and breadcrumb navigation', () => {
  const navigate = vi.fn()
  const { container } = render(<AppUiProvider>
    <ApplicationShell path="/backtesting/futures-roll-long" href={path => path} navigate={navigate} header={null}>Result</ApplicationShell>
  </AppUiProvider>)
  expect(container.querySelector('.ant-menu-item-selected')?.textContent).toBe('期货展期做多回测')
  const overview = screen.getByRole('link', { name: '回测总览' }).closest('li')!
  const instance = screen.getByRole('link', { name: '期货展期做多回测' }).closest('li')!
  expect(overview.querySelector('[data-icon="appstore"]')).toBeTruthy()
  expect(instance.querySelector('[data-icon="file-text"]')).toBeTruthy()
  fireEvent.click(screen.getByRole('link', { name: '回测' }))
  expect(navigate).toHaveBeenCalledWith('/backtesting')
  fireEvent.click(screen.getByRole('button', { name: '折叠导航' }))
  fireEvent.click(screen.getByRole('button', { name: '展开导航' }))
  expect(screen.getByRole('link', { name: '回测总览' })).toBeTruthy()
})

it('keeps a source link in the shared header', () => {
  const { container } = render(<ApplicationShell path="/research" href={path => path} navigate={vi.fn()} header={null}>Study</ApplicationShell>)
  const link = screen.getByRole('link', { name: '查看源码（GitHub）' })
  expect(link.getAttribute('href')).toBe('https://github.com/ougachakaaa/hg-market-state-lab')
  expect(link.getAttribute('target')).toBe('_blank')
  expect(link.getAttribute('rel')).toBe('noopener noreferrer')
  expect((container.querySelector('.ant-layout-header') as HTMLElement).style.flexShrink).toBe('0')
})

it.each(['production', 'static'] as const)('bounds %s workspace scrolling to Content and navigation', mode => {
  const { container } = render(<ApplicationShell mode={mode} path="/research" href={path => path} navigate={vi.fn()} header={null}>Long content</ApplicationShell>)
  const root = container.firstElementChild as HTMLElement
  expect(['100vh', '100dvh']).toContain(root.style.height)
  expect(root.style.minHeight).toBe('0px')
  expect(root.style.overflow).toBe('hidden')
  const content = container.querySelector('.ant-layout-content') as HTMLElement
  expect(content.style.overflowY).toBe('auto')
  expect(content.style.minHeight).toBe('0px')
  expect(content.style.minWidth).toBe('0px')
  expect(content.style.maxWidth).toBe('1500px')
  const navigation = screen.getByRole('menu', { name: '业务导航' }).parentElement!
  expect(navigation.style.overflowY).toBe('auto')
  expect(navigation.style.minHeight).toBe('0px')
})

it('shows Calendar Spread in both admitted runtimes', () => {
  const props = { path: '/research' as const, href: (path: string) => path, navigate: vi.fn(), header: null, children: 'Content' }
  const { rerender } = render(<ApplicationShell {...props} />)
  expect(screen.getByRole('link', { name: '历史跨期相对价值研究' })).toBeTruthy()
  rerender(<ApplicationShell {...props} mode="static" />)
  expect(screen.getByRole('link', { name: '历史跨期相对价值研究' })).toBeTruthy()
  expect(screen.getByRole('link', { name: '历史基差研究' })).toBeTruthy()
})
