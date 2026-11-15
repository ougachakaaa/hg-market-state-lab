import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { FuturesBasisPresentation } from './FuturesBasisPresentation'
import { useStaticFuturesBasis } from '../static/useStaticFuturesBasis'
import { validateEmbeddedReport } from '../api/validateResult'
import type { EmbeddedReportPayload } from '../api/validateResult'
import {
  embeddedReportPayload,
  mismatchedReportPayload,
  testOnlyDisclosure,
  testOnlyRequest,
} from '../testing/embeddedReportFixture'

vi.mock('../report/Report', () => ({
  Report: ({ mode, sectionNavigation }: { mode: string; sectionNavigation?: string }) =>
    <div data-testid="report">{`${mode}/${sectionNavigation ?? 'fragment'}`}</div>,
}))
afterEach(cleanup)

function Static({ payload = embeddedReportPayload, disclosure }: {
  payload?: EmbeddedReportPayload
  disclosure?: string
}) {
  const state = useStaticFuturesBasis(payload)
  return <FuturesBasisPresentation mode="static" state={state} disclosure={disclosure} />
}

it('composes the Production execution regions into the shared page presentation', () => {
  render(<FuturesBasisPresentation mode="production"
    parameters={<div>生产参数区</div>}
    run={<div>生产 Run 区</div>}
    request={testOnlyRequest}
    report={undefined}
    reportKey={undefined} />)
  expect(screen.getByRole('heading', { name: 'Futures Basis Research' })).toBeTruthy()
  expect(screen.getByText('研究参数')).toBeTruthy()
  expect(screen.getByText('生产参数区')).toBeTruthy()
  expect(screen.getByText('当前 Run')).toBeTruthy()
  expect(screen.getByText('生产 Run 区')).toBeTruthy()
  expect(screen.getByText('当前 Run').closest('.ant-card')!.querySelectorAll('.ant-descriptions-item-label')).toHaveLength(2)
  expect(screen.getByText('IM')).toBeTruthy()
  expect(screen.getByText('2024-10-18 至 2024-10-21')).toBeTruthy()
  expect(screen.queryByText('r01a_standard_v1')).toBeNull()
  expect(screen.queryByText('研究 Case')).toBeNull()
  expect(screen.queryByTestId('report')).toBeNull()
  expect(screen.queryByText('Embedded Report 已通过静态校验')).toBeNull()
  expect(screen.queryByText(/请求窗口 ≠ 实际观测覆盖/)).toBeNull()
})

it('renders the validated online Report through the same presentation', () => {
  const { report } = validateEmbeddedReport(embeddedReportPayload)
  render(<FuturesBasisPresentation mode="production"
    parameters={<div>生产参数区</div>}
    run={<div>生产 Run 区</div>}
    request={testOnlyRequest}
    report={report}
    reportKey="run-identity" />)
  expect(screen.getByTestId('report').textContent).toBe('online/fragment')
})

it('shows two fields and the prescribed disclaimer', () => {
  render(<Static disclosure={testOnlyDisclosure} />)
  const card = screen.getByText('固定研究参数').closest('.ant-card')!
  expect(card.querySelectorAll('.ant-descriptions-item-label')).toHaveLength(2)
  expect(screen.getByText('本页面为静态研究成果展示。数据不保证准确，不构成任何投资建议，仅供项目功能演示。')).toBeTruthy()
  expect(screen.queryByText(testOnlyDisclosure)).toBeNull()
  expect(screen.queryByText('请求窗口与实际观测覆盖')).toBeNull()
})
it('retains the validation error', () => {
  render(<Static payload={mismatchedReportPayload} />)
  expect(screen.getByText('静态研究报告未通过校验')).toBeTruthy()
  expect(screen.queryByTestId('report')).toBeNull()
})

it.each(['production', 'static'] as const)('keeps the %s introduction local and preserves the report', mode => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  const { report } = validateEmbeddedReport(embeddedReportPayload)
  const props = mode === 'production'
    ? { mode, parameters: <div>parameters</div>, run: <div>run</div>, request: testOnlyRequest, report, reportKey: 'same-run' }
    : { mode, state: { status: 'validated' as const, data: validateEmbeddedReport(embeddedReportPayload) } }
  const url = window.location.href
  render(<FuturesBasisPresentation {...props} />)
  const reportNode = screen.getByTestId('report')
  const toggle = screen.getByRole('button', { name: '关于本研究' })
  expect(toggle.getAttribute('aria-expanded')).toBe('false')
  fireEvent.click(toggle)
  const panel = toggle.closest('.ant-collapse-item')! as HTMLElement
  expect(within(panel).getByText('研究目的')).toBeTruthy()
  expect(within(panel).getByText('研究方式')).toBeTruthy()
  expect(panel.querySelectorAll('.ant-descriptions-item-label')).toHaveLength(2)
  expect(within(panel).getByText('观察股指期货相对现货指数的价格偏离，理解不同合约期限下的贴水特征及其历史变化。')).toBeTruthy()
  expect(within(panel).getByText('基于历史交易日数据，统计并可视化不同期限合约的基差、分布和贴水持续区间。')).toBeTruthy()
  fireEvent.click(toggle)
  expect(screen.getByTestId('report')).toBe(reportNode)
  expect(window.location.href).toBe(url)
  expect(fetch).not.toHaveBeenCalled()
  vi.unstubAllGlobals()
})
