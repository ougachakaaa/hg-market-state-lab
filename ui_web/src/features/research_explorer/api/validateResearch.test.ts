import { describe, expect, it } from 'vitest'
import views from '../../../../../market_research/tests/fixtures/publication_visualization_v1.json'
import {
  validateAnalysis,
  validateChartViewData,
  validateChartViewResponse,
  validateManifest,
  validatePublicationList,
} from './validateResearch'
import {
  publicationAnalyses,
  publicationList,
  publicationManifest,
} from '../testing/publicationFixture'

describe('Research Publication generated-contract validation', () => {
  it('accepts the formal list, manifest and Analysis responses', () => {
    expect(validatePublicationList(publicationList)).toBe(publicationList)
    expect(validateManifest(publicationManifest)).toBe(publicationManifest)
    expect(validateAnalysis(publicationAnalyses[0])).toBe(publicationAnalyses[0])
  })

  it('rejects malformed list, manifest and Analysis payloads', () => {
    expect(() => validatePublicationList({ data: 'wrong' })).toThrow()
    const manifest = structuredClone(publicationManifest)
    Reflect.deleteProperty(manifest.scope, 'metric')
    expect(() => validateManifest(manifest)).toThrow()
    const analysis = structuredClone(publicationAnalyses[0])
    Reflect.deleteProperty(analysis, 'outcome')
    expect(() => validateAnalysis(analysis)).toThrow()
  })

  it('retains the generated date-format check', () => {
    const manifest = structuredClone(publicationManifest)
    manifest.jobs[0].job_identity.start_date = '2020/01/01'
    expect(() => validateManifest(manifest)).toThrow()
  })

  it('validates both the generated View envelope and the shared ChartView contract', () => {
    expect(validateChartViewData(views[0])).toBe(views[0])
    expect(() => validateChartViewData({ ...views[0], version: 2 })).toThrow()
    expect(validateChartViewResponse({ data: views[1] })).toBe(views[1])
    expect(() => validateChartViewResponse({ data: { version: 2 } })).toThrow()
    expect(() => validateChartViewResponse({ data: 'wrong' })).toThrow()
  })
})
