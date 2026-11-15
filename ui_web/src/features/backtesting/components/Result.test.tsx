import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { Result } from './Result'
import type { BacktestResult } from '../api/backtesting'
import fixture from '../api/result.fixture.json'

// Mount the actual shared ChartView/control; replace only the Plotly DOM engine and
// report the projected x coordinate type so both charts' mappings stay observable.
vi.mock('react-plotly.js', () => ({ default: ({ data }: { data: { x?: unknown[] }[] }) =>
  <div data-testid="chart-mode">{typeof data[0]?.x?.[0] === 'number' ? 'trading' : 'calendar'}</div> }))
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

const result = fixture as BacktestResult
const modes = () => screen.getAllByTestId('chart-mode').map(node => node.textContent)

it('defaults both charts to Trading Days and switches them together repeatedly', () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  const before = structuredClone(result)
  render(<Result data={result} />)
  expect(modes()).toEqual(['trading', 'trading'])
  for (let round = 0; round < 3; round++) {
    fireEvent.click(screen.getByText('Calendar Days'))
    expect(modes()).toEqual(['calendar', 'calendar'])
    fireEvent.click(screen.getByText('Trading Days'))
    expect(modes()).toEqual(['trading', 'trading'])
  }
  // Presentation state only: no request, no producer result mutation.
  expect(fetch).not.toHaveBeenCalled()
  expect(result).toEqual(before)
})

it('restores the default Trading Days when a different Run remounts the result', () => {
  const second = structuredClone(result)
  second.summary.total_pnl = 1
  const { rerender } = render(<Result key="run-a" data={result} />)
  fireEvent.click(screen.getByText('Calendar Days'))
  expect(modes()).toEqual(['calendar', 'calendar'])
  rerender(<Result key="run-b" data={second} />)
  expect(modes()).toEqual(['trading', 'trading'])
  expect(second.summary.total_pnl).toBe(1)
})

it.each(['expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const)('presents compact report for %s', profile => {
  const data = structuredClone(result)
  data.request.strategy_profile = profile
  const { container } = render(<Result data={data} />)
  expect(screen.getAllByTestId('backtest-result')).toHaveLength(1)
  expect(container.querySelectorAll('.ant-card')).toHaveLength(1)
  expect(screen.queryByRole('table')).toBeNull()
  expect(screen.queryByText(/首个 CFFEX 交易日买入/)).toBeNull()
  fireEvent.click(screen.getByText('策略规则与收益口径'))
  expect(screen.getByText(/首个 CFFEX 交易日买入 M1/)).toBeTruthy()
  expect(screen.getByText(profile === 'expiry_to_M1_v1' ? /换入当天 M1/ : /换入当天 Q1/)).toBeTruthy()
  expect(screen.getByText('核心统计结果').compareDocumentPosition(screen.getAllByTestId('chart-mode')[1]) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy()
})
