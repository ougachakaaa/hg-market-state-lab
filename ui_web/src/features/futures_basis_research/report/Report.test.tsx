import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Report } from './Report'
import { validateReportData } from './validate'
import { readerFixture } from './reader.fixture'
vi.mock('../../../shared/visualization', () => ({ ChartView: () => <div>Producer ChartView</div> }))
afterEach(cleanup)
describe('shared reader', () => {
  it('renders six online sections, explicit empty coverage and online-only disclosure', () => {
    const { container } = render(<Report data={readerFixture()} mode="online" />)
    expect(container.querySelectorAll('[id^="section-"]')).toHaveLength(6)
    expect(screen.getByText('0；无..无')).toBeTruthy()
    expect(screen.getByText(/完整离线证据包及 Verify/)).toBeTruthy()
    expect(screen.queryByText(/相邻 inputs.canonical.json/)).toBeNull()
  })
  it('retains offline evidence disclosure with the identical reader', () => {
    render(<Report data={readerFixture()} mode="offline" />)
    expect(screen.getByText(/相邻 inputs.canonical.json/)).toBeTruthy()
  })
  it('validates V1 and V2 Views and rejects malformed reader presentation fields', () => {
    const data = readerFixture()
    validateReportData(data)
    data.views.histograms['synthetic/count'] = { version: 1, axes: [], layers: [], layout: { title: '' }, presentation: { show_legend: true } }
    // Reuse the generic V1 validator rather than defining another chart schema.
    expect(() => validateReportData(data)).not.toThrow()
    for (const change of [
      (d: any) => { d.views.history.basis_value.version = 99 },
      (d: any) => { d.comparisons = [{ request: {} }] },
      (d: any) => { d.coverage = { futures: { requested_units: 'bad' } } },
      (d: any) => { d.persistence = [{ slot: 'M0', complete: [{}], censored: [] }] },
      (d: any) => { d.distributions = [{ request: { analysis_id: 'a', metric: 'b' }, candidates: [], binding: [], methods: [] }] },
    ]) {
      const invalid = structuredClone(readerFixture()); change(invalid)
      expect(() => validateReportData(invalid)).toThrow()
    }
  })
})
