import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import FuturesBasisPage from './FuturesBasisPage'
import { useFuturesBasis } from '../hooks/useFuturesBasis'
import { ResearchError } from '../api/futuresBasis'
vi.mock('../hooks/useFuturesBasis', () => ({ useFuturesBasis: vi.fn() }))
vi.mock('../report/Report', () => ({ Report: () => <div>Retained report</div> }))
afterEach(cleanup)
const request = { product_code: 'IC' as const, start_date: '2024-10-18', end_date: '2024-10-21', case: 'futures_basis_v1' as const, analysis_profile: 'r01a_standard_v1' as const }
function state(overrides: Record<string, unknown> = {}) {
  const value = { phase: 'IDLE', id: '', feedback: undefined, submitting: false, submit: vi.fn(), retry: vi.fn(), ...overrides }
  vi.mocked(useFuturesBasis).mockReturnValue(value as unknown as ReturnType<typeof useFuturesBasis>)
  return value
}
describe('Run presentation and manual actions', () => {
  it('starts with explicit empty controls and never submits on Enter', () => {
    const s = state()
    render(<FuturesBasisPage />)
    expect(screen.getByRole('button', { name: /生成研究/ }).hasAttribute('disabled')).toBe(true)
    for (const label of ['开始日期', '结束日期']) fireEvent.keyDown(screen.getByLabelText(label), { key: 'Enter' })
    expect(s.submit).not.toHaveBeenCalled()
    expect(screen.getByText(/选择品种和起止日期/)).toBeTruthy()
  })
  it.each([['STATUS_ERROR', false, '重新读取状态'], ['REPORT_ERROR', true, '重新读取报告']])('keeps %s recovery as a read', (phase, report, label) => {
    const s = state({ phase, id: 'a'.repeat(32), error: new ResearchError('network') })
    render(<FuturesBasisPage />)
    fireEvent.click(screen.getByRole('button', { name: label as string }))
    expect(s.retry).toHaveBeenCalledWith(report)
    expect(s.submit).not.toHaveBeenCalled()
    expect(screen.getByText('a'.repeat(32))).toBeTruthy()
  })
  it.each(['FAILED', 'INTERRUPTED'])('uses the immutable request for explicit %s execution retry', phase => {
    const s = state({ phase, run: { run_id: 'a'.repeat(32), request, created_at: '2026-11-09T00:00:00Z', failure: { stage: 'execution', category: 'interrupted', dependency: null, reason: 'Safe reason' } } })
    render(<FuturesBasisPage />)
    expect(screen.getByText('Safe reason')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '使用原请求创建新 Run' }))
    expect(s.submit).toHaveBeenCalledWith({ product_code: 'IC', start_date: request.start_date, end_date: request.end_date })
    expect(s.retry).not.toHaveBeenCalled()
  })
  it('retains the existing report while a new submission is pending or rejected', () => {
    state({ phase: 'COMPLETED', report: { run_id: 'a', data: {} }, submitting: true, feedback: new ResearchError('run_busy') })
    render(<FuturesBasisPage />)
    expect(screen.getByText('Retained report')).toBeTruthy()
    expect(screen.getByText(/BUSY：/)).toBeTruthy()
    expect(screen.getByRole('button', { name: /生成研究/ }).hasAttribute('disabled')).toBe(true)
  })
})

it('retries an unavailable status read as status even when the last accepted Run was completed', () => {
  const s = state({ phase: 'UNAVAILABLE', errorRead: 'status', run: { run_id: 'a', status: 'COMPLETED', request, created_at: '2026-11-09T00:00:00Z' }, error: new ResearchError('unavailable') })
  render(<FuturesBasisPage />)
  fireEvent.click(screen.getByRole('button', { name: '重新读取状态' }))
  expect(s.retry).toHaveBeenCalledWith(false)
  expect(s.submit).not.toHaveBeenCalled()
})
