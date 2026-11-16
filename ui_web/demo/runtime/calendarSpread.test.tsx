import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { adaptBundles, disclose } from './dataAdapter'
import { StaticWorkspace } from './StaticWorkspace'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
const files = import.meta.glob('../bundles/*.json', { eager: true, import: 'default' })
afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.location.hash = '' })

it.each(['/data/futures-calendar-spread', '/research/calendar-spread-relative-value'])(
  'renders the retained Bundle at %s without HTTP or execution controls', async path => {
    const fetch = vi.fn(() => { throw new Error('Static Demo attempted a request') })
    vi.stubGlobal('fetch', fetch)
    const data = adaptBundles(Object.entries(files).filter(([name]) => !name.endsWith('/manifest.json')).map(([, value]) => value))
    window.location.hash = path
    render(<StaticWorkspace data={data} disclose={disclose} header="Demo" notice={null} />)
    await screen.findByText(/静态快照不会获取实时行情/)
    expect(screen.queryByRole('button', { name: '查询' })).toBeNull()
    expect(screen.queryByRole('button', { name: '开始研究' })).toBeNull()
    if (path.startsWith('/research/')) {
      fireEvent.click(screen.getByText('Calendar Days'))
      fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Pair' }))
      fireEvent.click(screen.getByText('Q1/Q2', { selector: '.ant-select-item-option-content' }))
    }
    expect(fetch).not.toHaveBeenCalled()
  },
)
