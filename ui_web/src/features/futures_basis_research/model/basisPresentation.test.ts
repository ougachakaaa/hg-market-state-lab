import { describe, expect, it } from 'vitest'
import { fixture } from '../testing/embeddedReportFixture'
import { observedCoverage } from './basisPresentation'
import { validateReportData } from '../report/validate'
import type { ReportData } from '../report/types'

function report(): ReportData {
  const value: unknown = structuredClone(fixture.report)
  validateReportData(value)
  return value
}

describe('shared Futures Basis coverage projection', () => {
  it('exposes producer coverage facts without recomputation', () => {
    const source = report()
    const before = structuredClone(source)
    expect(observedCoverage(source)).toEqual({
      reportProfile: 'futures_basis_report_evidence_v1',
      definitionVersion: 'futures_basis_definition_v1',
      status: 'complete',
      fingerprint: source.fingerprint,
      candidateCount: 2,
      firstCandidate: '2024-10-18',
      lastCandidate: '2024-10-21',
      complete: true,
    })
    expect(source).toEqual(before)
  })

  it('retains an incomplete dependency and an empty candidate set as producer facts', () => {
    const incomplete = report()
    incomplete.coverage.futures = { ...incomplete.coverage.futures, missing_units: 2, successful_units: 0, complete: false }
    expect(observedCoverage(incomplete).complete).toBe(false)

    const empty = report()
    empty.candidate_dates = []
    expect(observedCoverage(empty)).toMatchObject({ candidateCount: 0, firstCandidate: null, lastCandidate: null })
  })
})
