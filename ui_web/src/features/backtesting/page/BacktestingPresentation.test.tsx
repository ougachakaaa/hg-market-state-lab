import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import fixture from '../api/result.fixture.json'
import type { BacktestResult } from '../api/validateResult'
import { useStaticBacktesting } from '../static/useStaticBacktesting'
import {
  embeddedBacktestResultPayload,
  invalidBacktestResultPayload,
  mismatchedBacktestResultPayload,
  testOnlyDisclosure,
} from '../testing/backtestingFixture'
import { BacktestingPresentation } from './BacktestingPresentation'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plotly" /> }))
afterEach(cleanup)
const result = fixture as unknown as BacktestResult
const request = result.request

function Static({ payload = embeddedBacktestResultPayload }: { payload?: typeof embeddedBacktestResultPayload }) {
  const state = useStaticBacktesting(payload)
  return <BacktestingPresentation mode="static" state={state} disclosure={testOnlyDisclosure} />
}

it('composes the Production execution regions into the shared page presentation', () => {
  render(<BacktestingPresentation mode="production"
    parameters={<div>生产参数区</div>}
    readiness={<div>生产 Preflight 区</div>}
    run={<div>生产 Run 区</div>}
    request={request}
    result={result}
    resultKey="run-identity" />)
  expect(screen.getByRole('heading', { name: '期货展期做多回测' })).toBeTruthy()
  expect(screen.getByText('回测参数')).toBeTruthy()
  expect(screen.getByText('生产参数区')).toBeTruthy()
  expect(screen.getByText('数据准备状态')).toBeTruthy()
  expect(screen.getByText('生产 Preflight 区')).toBeTruthy()
  expect(screen.getByText('当前 Run 状态')).toBeTruthy()
  expect(screen.getByText('生产 Run 区')).toBeTruthy()
  expect(screen.queryByText('请求窗口与实际观测')).toBeNull()
  expect(screen.getByTestId('backtest-result')).toBeTruthy()
  expect(screen.getAllByTestId('plotly')).toHaveLength(2)
  expect(screen.queryByText(testOnlyDisclosure)).toBeNull()
  expect(screen.queryByText(/Embedded Backtest Result 已通过正式契约校验/)).toBeNull()
})

it('renders the validated fixed request and compact Result in static mode', () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  render(<Static />)
  expect(screen.getByRole('heading', { name: '期货展期做多回测' })).toBeTruthy()
  expect(screen.getByText(testOnlyDisclosure)).toBeTruthy()
  expect(screen.getByText('固定回测参数')).toBeTruthy()
  const facts = screen.getByText('固定回测参数').closest('.ant-card')!
  expect(facts.querySelectorAll('.ant-descriptions-item-label')).toHaveLength(3)
  expect(facts.textContent).toContain('到期换入次月合约（M0 → M1）')
  expect(screen.queryByText('expiry_to_M1_v1')).toBeNull()
  expect(screen.queryByText('futures_roll_long_v1')).toBeNull()
  expect(screen.queryByText('请求窗口与实际观测')).toBeNull()
  expect(screen.queryByText('Embedded Backtest Result 已通过正式契约校验')).toBeNull()
  expect(screen.getAllByTestId('backtest-result')).toHaveLength(1)
  expect(screen.getAllByTestId('plotly')).toHaveLength(2)
  expect(screen.getByText('¥22,000.00')).toBeTruthy()
  expect(screen.getByTestId('backtest-result').querySelector('table')).toBeNull()
  fireEvent.click(screen.getByText('策略规则与收益口径'))
  expect(screen.getByText(/未考虑手续费、滑点、保证金与融资成本/)).toBeTruthy()
  expect(screen.queryByText('当前 Run 状态')).toBeNull()
  expect(screen.queryByText('开始回测')).toBeNull()
  expect(screen.queryByText(/Run ID/)).toBeNull()
  expect(screen.queryByText(/PENDING|RUNNING|COMPLETED/)).toBeNull()
  expect(fetch).not.toHaveBeenCalled()
  vi.unstubAllGlobals()
})

it.each([
  ['invalid Result', invalidBacktestResultPayload],
  ['mismatched fixed request', mismatchedBacktestResultPayload],
])('shows an explicit rejection for an %s and no Result region', (_, payload) => {
  render(<Static payload={payload} />)
  expect(screen.getByText('静态回测结果未通过校验')).toBeTruthy()
  expect(screen.queryByText('固定回测参数')).toBeNull()
  expect(screen.queryByText('请求窗口与实际观测')).toBeNull()
  expect(screen.queryByText('Embedded Backtest Result 已通过正式契约校验')).toBeNull()
  expect(screen.queryByTestId('backtest-result')).toBeNull()
  expect(screen.queryByText(/Run ID/)).toBeNull()
})

it('preserves explicit source disclosure alongside the compact report', () => {
  const disclosure = 'Historical Real Market Data · Source: Tushare · Private'
  render(<BacktestingPresentation mode="static" state={{ status: 'validated', data: { request, result } }} sourceDisclosure={disclosure} />)
  fireEvent.click(screen.getByText('策略规则与收益口径'))
  expect(screen.getByText(new RegExp(disclosure))).toBeTruthy()
  expect(screen.queryByText(/Embedded Synthetic Example/)).toBeNull()
  expect(screen.getByText(/未考虑手续费、滑点、保证金与融资成本/)).toBeTruthy()
})
