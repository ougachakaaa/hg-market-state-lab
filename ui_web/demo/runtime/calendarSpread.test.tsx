import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { StaticWorkspace } from './StaticWorkspace'
import type { BundleLoaders } from './results'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
const files = import.meta.glob('../bundles/*.json', { eager: true, import: 'default' })
afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.location.hash = '' })

it.each(['/data/futures-calendar-spread', '/research/calendar-spread-relative-value'])(
  'loads only the retained consumer at %s without business HTTP or execution controls', async path => {
    const fetch = vi.fn(() => { throw new Error('Static Demo attempted a business request') })
    vi.stubGlobal('fetch', fetch)
    const loaders = Object.fromEntries(Object.entries(files).filter(([name]) => !name.endsWith('/manifest.json')).map(([name, data]) => [name.split('/').at(-1)!.slice(0, -5), vi.fn(async () => ({ default: data }))])) as unknown as BundleLoaders
    window.location.hash = path
    render(<StaticWorkspace loaders={loaders} header="Demo" notice={null} />)
    await screen.findByText(/静态快照不会获取实时行情/)
    expect(screen.queryByRole('button', { name: '查询' })).toBeNull()
    expect(screen.queryByRole('button', { name: '开始研究' })).toBeNull()
    if (path.startsWith('/research/')) {
      fireEvent.click(screen.getByText('Calendar Days'))
      fireEvent.mouseDown(screen.getByRole('combobox', { name: '合约对' }))
      fireEvent.click(screen.getByText('Q1/Q2', { selector: '.ant-select-item-option-content' }))
    }
    const expected = path.startsWith('/research/') ? 'calendar_spread_relative_value' : 'calendar_spread_daily'
    for (const [id, load] of Object.entries(loaders)) expect(load).toHaveBeenCalledTimes(id === expected ? 1 : 0)
    expect(fetch).not.toHaveBeenCalled()
  },
)
it.each(['/data', '/backtesting'])('renders overview %s without loading a business Bundle', async path => {
  const load = vi.fn(() => { throw new Error('Overview loaded business data') })
  const loaders = new Proxy({} as unknown as BundleLoaders, { get: () => load })
  window.location.hash = path
  render(<StaticWorkspace loaders={loaders} header="Demo" notice={null} />)
  await screen.findByRole('heading', { name: path === '/data' ? '数据总览' : '回测总览' })
  expect(load).not.toHaveBeenCalled()
})
