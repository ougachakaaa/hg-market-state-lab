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
