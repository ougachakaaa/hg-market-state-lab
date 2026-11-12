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
  expect(screen.getByText('请求窗口与实际观测')).toBeTruthy()
  expect(screen.getByTestId('backtest-result')).toBeTruthy()
  expect(screen.getAllByTestId('plotly')).toHaveLength(2)
  expect(screen.queryByText(testOnlyDisclosure)).toBeNull()
  expect(screen.queryByText(/Embedded Backtest Result 已通过正式契约校验/)).toBeNull()
})

it('renders the validated fixed request, requested-vs-observed window and complete Result in static mode', () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  render(<Static />)
  expect(screen.getByRole('heading', { name: '期货展期做多回测' })).toBeTruthy()
  expect(screen.getByText(testOnlyDisclosure)).toBeTruthy()
  expect(screen.getByText('固定回测参数')).toBeTruthy()
  expect(screen.getByText('固定回测参数').closest('.ant-card')!.textContent).toContain('不可编辑、不可提交')
  expect(screen.getAllByText('IM').length).toBeGreaterThan(0)
  expect(screen.getAllByText('expiry_to_M1_v1').length).toBeGreaterThan(0)
  expect(screen.getByText('futures_roll_long_v1')).toBeTruthy()
  expect(screen.getByText('请求窗口与实际观测')).toBeTruthy()
  expect(screen.getByText('2025-02-17 至 2025-03-25（5 个 CFFEX 交易日）')).toBeTruthy()
  expect(screen.getByText('futures_roll_long_result_v1')).toBeTruthy()
  expect(screen.getByText('futures_roll_long_definition_v1')).toBeTruthy()
  expect(screen.getByText('Embedded Backtest Result 已通过正式契约校验')).toBeTruthy()
  expect(screen.getAllByText(/不代表浏览器运行过 W2 Backtest Core/).length).toBe(2)
  expect(screen.getByTestId('backtest-result')).toBeTruthy()
  expect(screen.getAllByTestId('plotly')).toHaveLength(2)
  expect(screen.getByText('¥22,000.00')).toBeTruthy()
  fireEvent.click(screen.getByText('研究证据与限制 · Evidence / Limitations'))
  expect(screen.getByText(/Embedded Synthetic Example/)).toBeTruthy()
  expect(screen.getByText(/未执行服务器回测/)).toBeTruthy()
  expect(screen.getByText(/不包含手续费、滑点和保证金机制/)).toBeTruthy()
  expect(screen.getByText(result.evidence.input_fingerprint)).toBeTruthy()
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
