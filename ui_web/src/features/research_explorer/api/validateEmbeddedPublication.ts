import type { ChartView as ChartViewContract } from '../../../shared/visualization/contract'
import {
  validateAnalysis,
  validateChartViewData,
  validateManifest,
  validatePublicationList,
  type Analysis,
  type Manifest,
  type PublicationList,
} from './validateResearch'

export interface EmbeddedChartViewRecord {
  publication_id: string
  view_id: string
  view: unknown
}

export interface EmbeddedPublicationSetPayload {
  pages: readonly unknown[]
  manifests: readonly unknown[]
  analyses: readonly unknown[]
  views: readonly EmbeddedChartViewRecord[]
}

export interface ValidatedPublicationSet {
  pages: readonly PublicationList[]
  publicationIds: ReadonlySet<string>
  manifests: ReadonlyMap<string, Manifest>
  analyses: ReadonlyMap<string, ReadonlyMap<string, Analysis>>
  views: ReadonlyMap<string, ReadonlyMap<string, ChartViewContract>>
  /**
   * Declared continuation of the final embedded page, or null when that page ends the
   * online cursor chain. A non-null value means the embedded set stops before pages the
   * online store still declares; it is never a claim that the online list ended.
   */
  unembeddedCursor: string | null
}

function nonempty(value: unknown, field: string): asserts value is string {
  if (typeof value !== 'string' || value.length === 0) throw new Error(`Embedded ${field} must be a nonempty string`)
}

function sameValue(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) return true
  if (typeof left !== 'object' || left === null || typeof right !== 'object' || right === null) return false
  if (Array.isArray(left) || Array.isArray(right)) {
    if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) return false
    return left.every((value, index) => sameValue(value, right[index]))
  }
  const leftKeys = Object.keys(left).sort()
  const rightKeys = Object.keys(right).sort()
  if (leftKeys.length !== rightKeys.length || leftKeys.some((key, index) => key !== rightKeys[index])) return false
  return leftKeys.every(key => sameValue(
    (left as Record<string, unknown>)[key],
    (right as Record<string, unknown>)[key],
  ))
}

function nested<T>(map: Map<string, Map<string, T>>, publicationId: string): Map<string, T> {
  let values = map.get(publicationId)
  if (!values) {
    values = new Map()
    map.set(publicationId, values)
  }
  return values
}

// Validate identities that the Manifest itself owns before checking optional embedded
// detail records. Every Analysis summary belongs to exactly one published Job, repeated
// Job identities are ambiguous, and a View reference has one Analysis owner. The returned
// map is the publication's formal View Reference set.
function validateManifestRelations(manifest: Manifest): ReadonlyMap<string, string> {
  const requests = new Map<string, Manifest['scope']['analysis_requests'][number]>()
  for (const request of manifest.scope.analysis_requests) {
    nonempty(request.request_id, 'request_id')
    if (requests.has(request.request_id)) throw new Error(`Duplicate embedded request_id: ${request.request_id}`)
    requests.set(request.request_id, request)
  }

  const summaries = new Map<string, Manifest['analyses'][number]>()
  const viewOwners = new Map<string, string>()
  for (const summary of manifest.analyses) {
    nonempty(summary.analysis_id, 'analysis_id')
    if (summaries.has(summary.analysis_id)) throw new Error(`Duplicate embedded analysis_id: ${summary.analysis_id}`)
    summaries.set(summary.analysis_id, summary)
    const request = requests.get(summary.request_id)
    if (!request || !sameValue(request.spec, summary.spec)) {
      throw new Error(`Analysis ${summary.analysis_id} is not declared by the publication scope`)
    }
    const viewIds = new Set<string>()
    for (const reference of summary.views) {
      nonempty(reference.view_id, 'view_id')
      if (viewIds.has(reference.view_id)) throw new Error(`Duplicate View reference: ${reference.view_id}`)
      viewIds.add(reference.view_id)
      const owner = viewOwners.get(reference.view_id)
      if (owner !== undefined && owner !== summary.analysis_id) {
        throw new Error(`View ${reference.view_id} is associated with multiple Analyses`)
      }
      viewOwners.set(reference.view_id, summary.analysis_id)
    }
  }

  const jobIdentities: unknown[] = []
  const referenced = new Set<string>()
  for (const job of manifest.jobs) {
    if (jobIdentities.some(identity => sameValue(identity, job.job_identity))) {
      throw new Error('Duplicate embedded Job identity')
    }
    jobIdentities.push(job.job_identity)
    for (const analysisId of job.analyses) {
      const summary = summaries.get(analysisId)
      if (!summary) throw new Error(`Job references an unpublished Analysis: ${analysisId}`)
      if (!sameValue(summary.job_identity, job.job_identity)) {
        throw new Error(`Analysis ${analysisId} does not match its published Job identity`)
      }
      if (referenced.has(analysisId)) throw new Error(`Analysis ${analysisId} is referenced by multiple Jobs`)
      referenced.add(analysisId)
    }
  }
  for (const analysisId of summaries.keys()) {
    if (!referenced.has(analysisId)) throw new Error(`Analysis ${analysisId} is not referenced by a published Job`)
  }
  return viewOwners
}

// Embedded pages are a contiguous prefix of the online cursor chain: only the final
// embedded page may declare the chain's end, and it may also stop before pages the online
// store still declares. Page bytes, including opaque cursor values, are never created,
// decoded or rewritten here; the declared cursor is returned unchanged.
function validatePageContinuation(pages: readonly PublicationList[]): string | null {
  for (const [index, page] of pages.entries()) {
    if (page.next_cursor !== null && index === pages.length - 1) return page.next_cursor
    if (page.next_cursor === null && index < pages.length - 1) {
      throw new Error(`Embedded page ${index + 1} declares no next page but embedded page ${index + 2} follows it`)
    }
  }
  return null
}

function validateAnalysisRelations(analysis: Analysis, manifest: Manifest) {
  const summary = manifest.analyses.find(item => item.analysis_id === analysis.summary.analysis_id)
  if (!summary) throw new Error(`Analysis ${analysis.summary.analysis_id} is not in its Manifest`)
  if (!sameValue(summary, analysis.summary)) throw new Error(`Analysis ${analysis.summary.analysis_id} summary does not match its Manifest`)
  if (analysis.outcome !== summary.status) throw new Error(`Analysis ${analysis.summary.analysis_id} outcome does not match its summary`)
  if ((analysis.result !== null) !== (analysis.outcome === 'success')) {
    throw new Error(`Analysis ${analysis.summary.analysis_id} result presence does not match its outcome`)
  }
  if (analysis.result !== null) {
    if (analysis.result.method !== summary.spec.method) throw new Error(`Analysis ${analysis.summary.analysis_id} result method does not match its spec`)
    if (analysis.result.method === 'interval_count' && (summary.spec.method !== 'interval_count' || analysis.result.unit !== summary.spec.unit)) {
      throw new Error(`Analysis ${analysis.summary.analysis_id} result unit does not match its spec`)
    }
  }
}

export function validateEmbeddedPublicationSet(payload: EmbeddedPublicationSetPayload): ValidatedPublicationSet {
  if (typeof payload !== 'object' || payload === null ||
    !Array.isArray(payload.pages) || payload.pages.length === 0 ||
    !Array.isArray(payload.manifests) || !Array.isArray(payload.analyses) || !Array.isArray(payload.views)) {
    throw new Error('Invalid embedded Publication set')
  }

  const pages = payload.pages.map(validatePublicationList)
  const publicationIds = new Set<string>()
  const navigation = new Map<string, PublicationList['data'][number]>()
  for (const page of pages) {
    for (const item of page.data) {
      nonempty(item.publication_id, 'publication_id')
      if (publicationIds.has(item.publication_id)) throw new Error(`Duplicate embedded publication_id: ${item.publication_id}`)
      publicationIds.add(item.publication_id)
      navigation.set(item.publication_id, item)
    }
  }
  const unembeddedCursor = validatePageContinuation(pages)

  const manifests = new Map<string, Manifest>()
  const viewReferences = new Map<string, ReadonlyMap<string, string>>()
  for (const raw of payload.manifests) {
    const manifest = validateManifest(raw)
    nonempty(manifest.publication_id, 'publication_id')
    if (!publicationIds.has(manifest.publication_id)) throw new Error(`Manifest publication is not listed: ${manifest.publication_id}`)
    if (manifests.has(manifest.publication_id)) throw new Error(`Duplicate embedded Manifest: ${manifest.publication_id}`)
    if (navigation.get(manifest.publication_id)!.status !== manifest.status) {
      throw new Error(`Publication ${manifest.publication_id} status does not match its Manifest`)
    }
    viewReferences.set(manifest.publication_id, validateManifestRelations(manifest))
    manifests.set(manifest.publication_id, manifest)
  }

  const analyses = new Map<string, Map<string, Analysis>>()
  for (const raw of payload.analyses) {
    const analysis = validateAnalysis(raw)
    nonempty(analysis.publication_id, 'publication_id')
    const manifest = manifests.get(analysis.publication_id)
    if (!manifest) throw new Error(`Analysis publication has no embedded Manifest: ${analysis.publication_id}`)
    validateAnalysisRelations(analysis, manifest)
    const records = nested(analyses, analysis.publication_id)
    if (records.has(analysis.summary.analysis_id)) throw new Error(`Duplicate embedded Analysis: ${analysis.summary.analysis_id}`)
    records.set(analysis.summary.analysis_id, analysis)
  }

  const views = new Map<string, Map<string, ChartViewContract>>()
  for (const record of payload.views) {
    if (typeof record !== 'object' || record === null) throw new Error('Invalid embedded ChartView record')
    nonempty(record.publication_id, 'publication_id')
    nonempty(record.view_id, 'view_id')
    if (!manifests.has(record.publication_id)) throw new Error(`View publication has no embedded Manifest: ${record.publication_id}`)
    // An embedded ChartView is only legal when its own publication's Manifest declares a
    // formal View Reference with that ID. A published reference without an embedded View
    // stays a legal missing detail; the reverse is an illegal embedded set.
    if (!viewReferences.get(record.publication_id)?.has(record.view_id)) {
      throw new Error(`Embedded ChartView ${record.view_id} has no published View reference`)
    }
    const view = validateChartViewData(record.view)
    const records = nested(views, record.publication_id)
    if (records.has(record.view_id)) throw new Error(`Duplicate embedded ChartView: ${record.view_id}`)
    records.set(record.view_id, view)
  }

  return { pages, publicationIds, manifests, analyses, views, unembeddedCursor }
}
