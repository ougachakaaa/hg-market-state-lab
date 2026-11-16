import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import BacktestingOverview from './BacktestingOverview'
import DailyDataLanding from './DailyDataLanding'

afterEach(cleanup)

it('shows completed data products in success text with their existing navigation', () => {
  const navigate = vi.fn()
  render(<DailyDataLanding navigate={navigate} />)
  expect(screen.getAllByText('已完成')).toHaveLength(3)
  for (const status of screen.getAllByText('已完成')) expect(status.classList.contains('ant-typography-success')).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: '打开 Futures Calendar Spread' }))
  expect(navigate).toHaveBeenLastCalledWith('/data/futures-calendar-spread')
  fireEvent.click(screen.getByRole('button', { name: '打开 MO Option Chain' }))
  expect(navigate).toHaveBeenLastCalledWith('/data/mo-option-chain')
  fireEvent.click(screen.getByRole('button', { name: '打开 MO Premium Plane' }))
  expect(navigate).toHaveBeenLastCalledWith('/data/mo-premium-plane')
})

it('presents the implemented backtest card with success text and explicit navigation', () => {
  const navigate = vi.fn()
  render(<BacktestingOverview navigate={navigate} />)
  expect(screen.getByRole('heading', { name: '回测总览' })).toBeTruthy()
  expect(screen.getByText('已完成').classList.contains('ant-typography-success')).toBe(true)
  expect(navigate).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: '查看回测' }))
  expect(navigate).toHaveBeenCalledWith('/backtesting/futures-roll-long')
})

it('keeps Static Daily overview limited to admitted pages', () => {
  render(<DailyDataLanding mode="static" navigate={vi.fn()} />)
  expect(screen.getAllByText('已完成')).toHaveLength(3)
  expect(screen.getByRole('button', { name: '打开 Futures Calendar Spread' })).toBeTruthy()
})
