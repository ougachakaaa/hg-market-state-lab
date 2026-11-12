import { describe, expect, it } from 'vitest'
import type { Analysis } from './validateResearch'
import {
  validateEmbeddedPublicationSet,
  type EmbeddedPublicationSetPayload,
} from './validateEmbeddedPublication'
import {
  publicationAnalyses,
  publicationList,
  publicationManifest,
  publicationViews,
} from '../testing/publicationFixture'

function payload(): EmbeddedPublicationSetPayload {
  return {
    pages: [structuredClone(publicationList)],
    manifests: [structuredClone(publicationManifest)],
    analyses: structuredClone(publicationAnalyses),
    views: structuredClone(publicationViews),
  }
}
function analysis(value: EmbeddedPublicationSetPayload, index = 0): Analysis {
  return value.analyses[index] as Analysis
}

describe('Embedded Publication set validation', () => {
  it('validates a complete set and retains published order', () => {
    const result = validateEmbeddedPublicationSet(payload())
    expect(result.pages[0]).toEqual(publicationList)
    expect(result.publicationIds.has('pub-static-one')).toBe(true)
    expect(result.manifests.get('pub-static-one')).toEqual(publicationManifest)
    expect(result.analyses.get('pub-static-one')?.get('analysis-quantile')).toEqual(publicationAnalyses[0])
    expect(result.views.get('pub-static-one')?.get('frequency-id')).toEqual(publicationViews[2].view)
  })

  it('accepts an explicit empty set, and missing Manifest/Analysis/View records', () => {
    expect(validateEmbeddedPublicationSet({ pages: [{ data: [], next_cursor: null }], manifests: [], analyses: [], views: [] }))
      .toBeTruthy()
    const missingManifest = { ...payload(), manifests: [], analyses: [], views: [] }
    expect(validateEmbeddedPublicationSet(missingManifest).manifests.size).toBe(0)
    const missingAnalysis = { ...payload(), analyses: [] }
    expect(validateEmbeddedPublicationSet(missingAnalysis).analyses.size).toBe(0)
    const missingView = { ...payload(), views: [] }
    expect(validateEmbeddedPublicationSet(missingView).views.size).toBe(0)
  })

  it('rejects empty pages, invalid list payloads and duplicate publication identities', () => {
    expect(() => validateEmbeddedPublicationSet({ ...payload(), pages: [] })).toThrow()
    const invalid = payload()
    invalid.pages = [{ data: [{ publication_id: 'x', status: 'bogus' }], next_cursor: null }]
    expect(() => validateEmbeddedPublicationSet(invalid)).toThrow()
    const duplicate = payload()
    duplicate.pages = [publicationList, publicationList]
    expect(() => validateEmbeddedPublicationSet(duplicate)).toThrow(/Duplicate embedded publication_id/)
  })

  it('rejects a Manifest outside the list, duplicate Manifests and status disagreement', () => {
    const outside = payload()
    const outsideManifest = structuredClone(publicationManifest)
    outsideManifest.publication_id = 'not-listed'
    outside.manifests = [outsideManifest]
    expect(() => validateEmbeddedPublicationSet(outside)).toThrow(/not listed/)

    const duplicate = payload()
    duplicate.manifests = [publicationManifest, publicationManifest]
    expect(() => validateEmbeddedPublicationSet(duplicate)).toThrow(/Duplicate embedded Manifest/)

    const inconsistent = payload()
    const failed = structuredClone(publicationManifest)
    failed.status = 'failed'
    inconsistent.manifests = [failed]
    expect(() => validateEmbeddedPublicationSet(inconsistent)).toThrow(/status does not match/)
  })

  it('rejects broken Job/Analysis associations and ambiguous View ownership', () => {
    const missingReference = payload()
    const missingManifest = structuredClone(publicationManifest)
    missingManifest.jobs[0].analyses = ['missing-analysis']
    missingReference.manifests = [missingManifest]
    expect(() => validateEmbeddedPublicationSet(missingReference)).toThrow(/unpublished Analysis/)

    const identityMismatch = payload()
    const mismatched = structuredClone(publicationManifest)
    mismatched.jobs[0].job_identity = { ...mismatched.jobs[0].job_identity, subject: 'ZZZ' }
    identityMismatch.manifests = [mismatched]
    expect(() => validateEmbeddedPublicationSet(identityMismatch)).toThrow(/does not match its published Job identity/)

    const duplicateJob = payload()
    const duplicated = structuredClone(publicationManifest)
    duplicated.jobs[1].job_identity = structuredClone(duplicated.jobs[0].job_identity)
    duplicateJob.manifests = [duplicated]
    expect(() => validateEmbeddedPublicationSet(duplicateJob)).toThrow(/Duplicate embedded Job identity/)

    const sharedView = payload()
    const shared = structuredClone(publicationManifest)
    shared.analyses[1].views.push({ measure: 'quantile', view_id: 'quantile-id' })
    sharedView.manifests = [shared]
    expect(() => validateEmbeddedPublicationSet(sharedView)).toThrow(/multiple Analyses/)
  })

  it('rejects duplicate, unlisted and inconsistent Analysis records', () => {
    const duplicate = payload()
    duplicate.analyses = [publicationAnalyses[0], publicationAnalyses[0]]
    expect(() => validateEmbeddedPublicationSet(duplicate)).toThrow(/Duplicate embedded Analysis/)

    const unlisted = payload()
    const unlistedAnalysis = structuredClone(publicationAnalyses[0])
    unlistedAnalysis.summary.analysis_id = 'not-listed'
    unlisted.analyses = [unlistedAnalysis]
    expect(() => validateEmbeddedPublicationSet(unlisted)).toThrow(/not in its Manifest/)

    const noManifest = payload()
    const orphan = structuredClone(publicationAnalyses[0])
    orphan.publication_id = 'other-publication'
    noManifest.analyses = [orphan]
    expect(() => validateEmbeddedPublicationSet(noManifest)).toThrow(/no embedded Manifest/)

    const mismatch = payload()
    const changed = structuredClone(publicationAnalyses[0])
    changed.summary.status = 'failed'
    mismatch.analyses = [changed]
    expect(() => validateEmbeddedPublicationSet(mismatch)).toThrow(/summary does not match/)

    const resultMismatch = payload()
    const outcome = structuredClone(publicationAnalyses[0])
    const outcomeManifest = structuredClone(publicationManifest)
    outcomeManifest.analyses[0].status = 'failed'
    outcome.summary.status = 'failed'
    outcome.outcome = 'failed'
    resultMismatch.manifests = [outcomeManifest]
    resultMismatch.analyses = [outcome]
    expect(() => validateEmbeddedPublicationSet(resultMismatch)).toThrow(/result presence/)
  })

  it('rejects invalid, duplicate and unlisted ChartViews', () => {
    const invalid = payload()
    invalid.views = [{ ...invalid.views[0], view: { version: 2 } }]
    expect(() => validateEmbeddedPublicationSet(invalid)).toThrow()

    const duplicate = payload()
    duplicate.views = [publicationViews[0], publicationViews[0]]
    expect(() => validateEmbeddedPublicationSet(duplicate)).toThrow(/Duplicate embedded ChartView/)

    const unlisted = payload()
    unlisted.views = [{ ...publicationViews[0], publication_id: 'other-publication' }]
    expect(() => validateEmbeddedPublicationSet(unlisted)).toThrow(/no embedded Manifest/)
  })

  it('does not mutate the embedded records', () => {
    const input = payload()
    const before = structuredClone(input)
    validateEmbeddedPublicationSet(input)
    expect(input).toEqual(before)
    expect(analysis(input).summary.analysis_id).toBe('analysis-quantile')
  })
})
