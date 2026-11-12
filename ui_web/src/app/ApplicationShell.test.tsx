import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import ApplicationShell from './ApplicationShell'
import AppUiProvider from './AppUiProvider'

afterEach(cleanup)
it('composes arbitrary header/content and receives runtime-specific navigation hrefs', () => {
  const navigate = vi.fn()
  const { container, rerender } = render(<AppUiProvider>
    <ApplicationShell path="/research/publications" href={path => `#${path}`} navigate={navigate}
      header={<span>Anonymous disclosure</span>}><h1>Injected content</h1></ApplicationShell>
  </AppUiProvider>)
  expect(screen.getByText('Anonymous disclosure')).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'Injected content' })).toBeTruthy()
  expect(container.querySelector('.ant-menu-item-selected')?.textContent).toBe('Research Explorer')
  const breadcrumb = screen.getByRole('link', { name: '研究' })
  expect(breadcrumb.getAttribute('href')).toBe('#/research')
  fireEvent.click(breadcrumb)
  expect(navigate).toHaveBeenCalledWith('/research')
  expect(screen.getByRole('link', { name: 'Research Explorer' }).getAttribute('href')).toBe('#/research/publications')
  rerender(<AppUiProvider>
    <ApplicationShell path="/research/publications" href={path => path} navigate={navigate}
      header={<span>Production identity</span>}><h1>Other content</h1></ApplicationShell>
  </AppUiProvider>)
  expect(screen.getByRole('link', { name: '研究' }).getAttribute('href')).toBe('/research')
  expect(screen.queryByText('Anonymous disclosure')).toBeNull()
  expect(screen.getByText('Production identity')).toBeTruthy()
})
