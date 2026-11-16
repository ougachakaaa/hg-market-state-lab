import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ChartView } from './ChartView'
import { fixtures } from './fixtures'
import { extendedFixtureV2, fixtureV2 } from './fixturesV2'
import { cleanup, fireEvent } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(cleanup)

vi.mock('react-plotly.js', () => ({ default: ({ data }: { data: unknown[] }) => <div data-testid="plot">{data.length} traces</div> }))
describe('ChartView React entry', () => {
  it('passes the validated figure to Plotly', () => {
    render(<ChartView view={fixtures.mixed} />)
    expect(screen.getByTestId('plot').textContent).toBe('2 traces')
  })
  it('rejects an invalid View before rendering', () => {
    expect(() => render(<ChartView view={fixtures.invalid} />)).toThrow(/unknown axis/)
  })
  it('shows null reasons and separate ordered literal event details', () => {
    render(<ChartView view={extendedFixtureV2()} />)
    expect(screen.getByTestId('plot').textContent).toBe('4 traces')
    fireEvent.click(screen.getByText('Series A — 2026-01-06 — No value'))
    expect(screen.getByText('Reason: Not supplied')).toBeTruthy()
    fireEvent.click(screen.getByText('e2 — 2026-01-05 — Same date'))
    const literal = screen.getByText('Note: <b>literal event</b>')
    expect(literal.querySelector('b')).toBeNull()
    expect(literal.nextElementSibling?.textContent).toBe('Note: Second detail')
    expect(screen.getByText('e1 — 2026-01-05 — Boundary')).toBeTruthy()
    expect(screen.getByText('e3 — 2026-01-12 — Event only date')).toBeTruthy()
  })
  it('explicitly presents empty and all-null content', () => {
    const v = structuredClone(fixtureV2)
    v.layers.forEach(b => b.layer.data.forEach(m => { m.y = null }))
    render(<ChartView view={v} />)
    expect(screen.getByText('No numeric data')).toBeTruthy()
    cleanup(); render(<ChartView view={{ ...v, axes: [], layers: [], events: [] }} />)
    expect(screen.getByText('No numeric data')).toBeTruthy()
  })
})

it('wraps complete ordered events in an initially closed local disclosure', () => {
  const view = extendedFixtureV2()
  const original = structuredClone(view)
  render(<ChartView view={view} options={{ dateEventsDisclosure: { description: 'Explanation' } }} />)
  const toggle = screen.getByRole('button', { name: '日期事件（Date Events）' })
  expect(toggle.getAttribute('aria-expanded')).toBe('false')
  expect(screen.queryByText('Explanation')).toBeNull()
  expect(screen.queryByText(/e1 ?/)).toBeNull()
  fireEvent.click(toggle)
  expect(screen.getByText('Explanation')).toBeTruthy()
  const buttons = view.events.map(e => screen.getByRole('button', { name: `${e.id} — ${e.x} — ${e.label}` }))
  for (let i = 1; i < buttons.length; i++) expect(buttons[i - 1].compareDocumentPosition(buttons[i]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  fireEvent.click(buttons[1])
  expect(screen.getByText('Note: <b>literal event</b>')).toBeTruthy()
  fireEvent.click(toggle)
  expect(toggle.getAttribute('aria-expanded')).toBe('false')
  expect(view).toEqual(original)
  cleanup()
  render(<ChartView view={{ ...view, events: [] }} options={{ dateEventsDisclosure: { description: 'Explanation' } }} />)
  expect(screen.queryByText('日期事件（Date Events）')).toBeNull()
})

it('optionally folds null dates twice without inferring expiry or mutating evidence', () => {
 const view = extendedFixtureV2()
 const nulls = view.layers.flatMap(b => b.layer.data.filter(m => m.y === null).map(m => ({ b, m })))
 nulls[0].m.details = [{ label: 'Reason', value: 'expiry_day' }, { label: 'Other', value: 'unavailable' }]
 const original = structuredClone(view)
 const fetch = vi.fn(); vi.stubGlobal('fetch', fetch)
 render(<ChartView view={view} options={{ missingValuesDisclosure: { title: '无有效指标值日期', description: '具体原因见日期详情' } }} />)
 const outer = screen.getByRole('button', { name: '无有效指标值日期' })
 expect(outer.getAttribute('aria-expanded')).toBe('false')
 expect(screen.queryByText('Reason: expiry_day')).toBeNull()
 fireEvent.click(outer)
 for (const { b, m } of nulls) expect(screen.getByRole('button', { name: `${b.label} — ${m.x}` }).getAttribute('aria-expanded')).toBe('false')
 fireEvent.click(screen.getByRole('button', { name: `${nulls[0].b.label} — ${nulls[0].m.x}` }))
 expect(screen.getByText('Reason: expiry_day')).toBeTruthy()
 expect(screen.getByText('Other: unavailable')).toBeTruthy()
 expect(screen.queryByText('到期日')).toBeNull()
 expect(fetch).not.toHaveBeenCalled()
 expect(view).toEqual(original)
 vi.unstubAllGlobals()
})
