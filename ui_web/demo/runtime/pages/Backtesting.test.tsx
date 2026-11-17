import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import Backtesting from './Backtesting'
import { bundleStore } from '../resources'
import type { BundleLoaders } from '../results'
import m1 from '../../bundles/expiry_to_M1_v1.json'
import q1 from '../../bundles/expiry_to_Q1_v1.json'

vi.mock('react-plotly.js', () => ({ default: () => <div /> }))
afterEach(cleanup)
it('loads Q1 only when selected, hides stale results and reuses validated results on return', async () => {
  let finishQ1!: (value: { default: typeof q1 }) => void
  const loadM1 = vi.fn(async () => ({ default: m1 }))
  const loadQ1 = vi.fn(() => new Promise<{ default: typeof q1 }>(done => { finishQ1 = done }))
  const loaders = { expiry_to_M1_v1: loadM1, expiry_to_Q1_v1: loadQ1 } as unknown as BundleLoaders
  render(<Backtesting store={bundleStore(loaders)} navigate={vi.fn()} />)
  await screen.findByTestId('backtest-result')
  expect(loadM1).toHaveBeenCalledOnce()
  expect(loadQ1).not.toHaveBeenCalled()
  const select = (title: RegExp) => {
    fireEvent.mouseDown(screen.getByRole('combobox', { name: '已计算策略结果' }))
    fireEvent.click(screen.getByText(title, { selector: '.ant-select-item-option-content' }))
  }
  select(/M0 → Q1/)
  expect(screen.queryByTestId('backtest-result')).toBeNull()
  await waitFor(() => expect(loadQ1).toHaveBeenCalledOnce())
  select(/M0 → M1/)
  await screen.findByTestId('backtest-result')
  await act(async () => finishQ1({ default: q1 }))
  expect(within(screen.getByTestId('backtest-result')).getByText((m1.result.summary.gross_return * 100).toFixed(1) + '%')).toBeTruthy()
  select(/M0 → Q1/)
  await screen.findByTestId('backtest-result')
  expect(within(screen.getByTestId('backtest-result')).getByText((q1.result.summary.gross_return * 100).toFixed(1) + '%')).toBeTruthy()
  expect(loadQ1).toHaveBeenCalledOnce()
  expect(loadM1).toHaveBeenCalledOnce()
})
