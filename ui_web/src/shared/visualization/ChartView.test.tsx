import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ChartView } from './ChartView'
import { fixtures } from './fixtures'

vi.mock('react-plotly.js', () => ({ default: ({ data }: { data: unknown[] }) => <div data-testid="plot">{data.length} traces</div> }))
describe('ChartView React entry', () => {
  it('passes the validated figure to Plotly', () => {
    render(<ChartView view={fixtures.mixed} />)
    expect(screen.getByTestId('plot').textContent).toBe('2 traces')
  })
  it('rejects an invalid View before rendering', () => {
    expect(() => render(<ChartView view={fixtures.invalid} />)).toThrow(/unknown axis/)
  })
})
