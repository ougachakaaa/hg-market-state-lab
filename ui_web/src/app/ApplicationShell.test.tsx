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
