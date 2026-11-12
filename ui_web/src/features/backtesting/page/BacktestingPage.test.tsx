import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import BacktestingPage from './BacktestingPage'
import { useBacktesting } from '../hooks/useBacktesting'
import { usePreflight } from '../hooks/usePreflight'
import { BacktestingError, type BacktestResult } from '../api/backtesting'
import { Result } from '../components/Result'
import fixture from '../api/result.fixture.json'
vi.mock('../hooks/useBacktesting', () => ({ useBacktesting: vi.fn() }))
vi.mock('../hooks/usePreflight', () => ({ usePreflight: vi.fn() }))
// Mount actual shared ChartView; replace only the Plotly DOM engine in jsdom.
vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plotly" /> }))
afterEach(cleanup)
function state(overrides: Record<string, unknown> = {}) {
  vi.mocked(usePreflight).mockReturnValue({ checking: false, result: undefined, error: undefined, refresh: vi.fn() })
  const value = { phase: 'IDLE', id: '', submitting: false, submit: vi.fn(), retry: vi.fn(), ...overrides }
  vi.mocked(useBacktesting).mockReturnValue(value as unknown as ReturnType<typeof useBacktesting>)
  return value
}
it('renders four empty controls without defaults or implicit submit', () => {
  const s = state(); render(<BacktestingPage />)
  expect(screen.getAllByRole('combobox')).toHaveLength(2)
  expect(screen.getByLabelText('开始日期')).toHaveProperty('value', '')
  expect(screen.getByLabelText('结束日期')).toHaveProperty('value', '')
  expect(screen.getByRole('button', { name: '开始回测' }).hasAttribute('disabled')).toBe(true)
  fireEvent.submit(screen.getByLabelText('开始日期').closest('form')!)
  fireEvent.keyDown(screen.getByLabelText('结束日期'), { key: 'Enter' })
  expect(s.submit).not.toHaveBeenCalled()
})
it.each(['FAILED', 'INTERRUPTED'])('shows real %s failure without a result', phase => {
  state({ phase, run: { run_id: 'a'.repeat(32), request: fixture.request, created_at: '2026-11-12T00:00:00Z', failure: { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'internal_failure' } } })
  render(<BacktestingPage />)
  expect(screen.getByText(phase)).toBeTruthy(); expect(screen.getByText('回测未产生结果')).toBeTruthy()
  expect(screen.queryByTestId('backtest-result')).toBeNull()
})
it.each([['STATUS_ERROR', 'status', false], ['RESULT_ERROR', 'result', true]])('retries %s only as GET', (phase, errorRead, result) => {
  const s = state({ phase, errorRead, error: new BacktestingError('read_busy') })
  render(<BacktestingPage />)
  fireEvent.click(screen.getByRole('button', { name: result ? '重新读取结果' : '重新读取状态' }))
  expect(s.retry).toHaveBeenCalledWith(result); expect(s.submit).not.toHaveBeenCalled()
})
it('formats producer summary and mounts both existing V2 charts, trades and evidence', () => {
  render(<Result data={fixture as BacktestResult} />)
  expect(screen.getAllByTestId('plotly')).toHaveLength(2)
  expect(screen.getByText('¥22,000.00')).toBeTruthy()
  expect(screen.getByText('1.8%')).toBeTruthy()
  expect(screen.getAllByText('IM2504.CFX').length).toBeGreaterThan(0)
  fireEvent.click(screen.getByText('研究证据与限制 · Evidence / Limitations'))
  expect(screen.getByText(fixture.evidence.input_fingerprint)).toBeTruthy()
  expect(screen.getByText(/不包含手续费、滑点和保证金机制/)).toBeTruthy()
  expect(screen.getByText(/这里是在线证据摘要/)).toBeTruthy()
})
