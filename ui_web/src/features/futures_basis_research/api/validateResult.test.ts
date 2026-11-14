import { describe, expect, it } from 'vitest'
import { fixture } from '../testing/embeddedReportFixture'
import {
  matchesResponse,
  products,
  REPORT_PROFILE,
  validateEmbeddedReport,
  validateImmutableRequest,
  validateReaderReport,
} from './validateResult'
import { testOnlyRequest } from '../testing/embeddedReportFixture'

function payload() {
  return { request: structuredClone(testOnlyRequest), report: structuredClone(fixture.report) }
}

describe('Futures Basis pure result validation', () => {
  it('accepts the committed synthetic reader payload under the generated fixed request', () => {
    const input = payload()
    const before = structuredClone(input)
    const result = validateEmbeddedReport(input)
    expect(result.report.profile).toBe(REPORT_PROFILE)
    expect(result.report.definition_version).toBe('futures_basis_definition_v1')
    expect(result.report.status).toBe('complete')
    expect(result.report.request.observation).toMatchObject({
      product_code: 'IM', start_date: '2024-10-18', end_date: '2024-10-21', case: 'futures_basis_v1',
    })
    expect(result.request).toEqual(testOnlyRequest)
    expect(input).toEqual(before)
  })

  it('rejects a request that is not the published generated contract', () => {
    expect(products).toEqual(['IM', 'IC', 'IF', 'IH'])
    for (const request of [
      { ...testOnlyRequest, analysis_profile: 'other_profile' },
      { ...testOnlyRequest, product_code: 'ZZ' },
      { ...testOnlyRequest, case: 'other_case' },
      { ...testOnlyRequest, start_date: '2024/09/02' },
      { ...testOnlyRequest, extra: true },
      { case: testOnlyRequest.case, product_code: testOnlyRequest.product_code, start_date: testOnlyRequest.start_date, end_date: testOnlyRequest.end_date },
    ]) {
      expect(() => validateImmutableRequest(request)).toThrow(/immutable request/)
    }
    expect(validateImmutableRequest(testOnlyRequest)).toBe(testOnlyRequest)
  })

  it('rejects a payload whose observation does not answer the fixed request', () => {
    const mismatched = payload()
    mismatched.report.request.observation.end_date = '2024-11-29'
    expect(() => validateEmbeddedReport(mismatched)).toThrow(/observation does not match/)

    const wrongCase = payload()
    wrongCase.report.request.observation.case = 'other_case'
    expect(() => validateEmbeddedReport(wrongCase)).toThrow(/Unsupported case/)

    const wrongProduct = payload()
    wrongProduct.request = { ...testOnlyRequest, product_code: 'IC' }
    expect(() => validateEmbeddedReport(wrongProduct)).toThrow(/observation does not match/)
  })

  it('rejects unsupported profiles, statuses and reader shapes instead of casting', () => {
    const profile = payload()
    profile.report.profile = 'other_profile'
    expect(() => validateEmbeddedReport(profile)).toThrow()

    const status = payload()
    status.report.status = 'failed'
    expect(() => validateEmbeddedReport(status)).toThrow()

    const definition = payload()
    definition.report.definition_version = '  '
    expect(() => validateEmbeddedReport(definition)).toThrow(/definition version/)

    const view = payload()
    Object.assign(view.report.views.history.basis_value, { version: 99 })
    expect(() => validateEmbeddedReport(view)).toThrow()

    expect(() => validateEmbeddedReport({ request: testOnlyRequest, report: null })).toThrow()
    expect(() => validateEmbeddedReport(null as never)).toThrow(/embedded report payload/)
  })

  it('keeps Production report association and HTTP envelope validation on the same contract', () => {
    const data = structuredClone(fixture.report)
    expect(validateReaderReport(data, testOnlyRequest)).toBe(data)
    expect(() => validateReaderReport(data, testOnlyRequest, 'partial')).toThrow(/status does not match/)

    const request = structuredClone(testOnlyRequest)
    const envelope = { run_id: 'a'.repeat(32), request, result_status: 'complete', data }
    expect(matchesResponse('get', '/research/futures-basis/runs/{run_id}/report', 200, envelope)).toBe(true)
    // The generated envelope schema only checks envelope shape; the reader payload itself is
    // owned by the shared reader validator used above, not by a second wire schema.
    expect(matchesResponse('get', '/research/futures-basis/runs/{run_id}/report', 200, { ...envelope, run_id: 'short' })).toBe(false)
    expect(matchesResponse('get', '/research/futures-basis/runs/{run_id}/report', 200, { ...envelope, result_status: 'failed' })).toBe(false)
    expect(matchesResponse('get', '/research/futures-basis/runs/{run_id}/report', 200, { ...envelope, request: { ...request, analysis_profile: 'other' } })).toBe(false)
  })
})
