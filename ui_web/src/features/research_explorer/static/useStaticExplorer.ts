import { useCallback, useState } from 'react'
import {
  validateEmbeddedPublicationSet,
  type EmbeddedPublicationSetPayload,
  type ValidatedPublicationSet,
} from '../api/validateEmbeddedPublication'
import type { ChartView as ChartViewContract } from '../../../shared/visualization/contract'
import type { Analysis, Manifest, PublicationList } from '../api/validateResearch'
import type {
  ExplorerLoad,
  ResearchExplorerController,
} from '../model/explorerPresentation'

type PublicationState =
  | { status: 'success'; data: ValidatedPublicationSet }
  | { status: 'invalid'; error: unknown }

// Static controller: validates committed records once, then performs only local
// selection and pagination. Missing optional detail records remain explicit missing states.
export function useStaticExplorer(payload: EmbeddedPublicationSetPayload): ResearchExplorerController {
  const [publicationSet] = useState<PublicationState>(() => {
    try {
      return { status: 'success', data: validateEmbeddedPublicationSet(payload) }
    } catch (error) {
      return { status: 'invalid', error }
    }
  })
  const [page, setPage] = useState(0)
  const [publication, setPublication] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [view, setView] = useState<string | null>(null)

  const pages = publicationSet.status === 'success' ? publicationSet.data.pages : []
  const list: ExplorerLoad<PublicationList> = publicationSet.status === 'success'
    ? { status: 'success', data: pages[page] }
    : { status: 'invalid', error: publicationSet.error }
  let manifest: ExplorerLoad<Manifest> = { status: 'idle' }
  let result: ExplorerLoad<Analysis> = { status: 'idle' }
  let chart: ExplorerLoad<ChartViewContract> = { status: 'idle' }
  if (publicationSet.status === 'success' && publication !== null) {
    const foundManifest = publicationSet.data.manifests.get(publication)
    manifest = foundManifest ? { status: 'success', data: foundManifest } : { status: 'missing', id: publication }
    if (analysis !== null) {
      const foundAnalysis = publicationSet.data.analyses.get(publication)?.get(analysis)
      result = foundAnalysis ? { status: 'success', data: foundAnalysis } : { status: 'missing', id: analysis }
      if (view !== null) {
        const foundView = publicationSet.data.views.get(publication)?.get(view)
        chart = foundView ? { status: 'success', data: foundView } : { status: 'missing', id: view }
      }
    }
  }
  const canNext = publicationSet.status === 'success' && page + 1 < pages.length
  const canPrevious = page > 0

  const selectPublication = useCallback((id: string | null) => {
    if (id !== null && (publicationSet.status !== 'success' || !publicationSet.data.publicationIds.has(id))) return
    setPublication(id)
    setAnalysis(null)
    setView(null)
  }, [publicationSet])
  const selectAnalysis = useCallback((id: string | null) => {
    if (id === null) {
      setAnalysis(null)
      setView(null)
      return
    }
    if (publicationSet.status !== 'success' || publication === null) return
    const manifest = publicationSet.data.manifests.get(publication)
    if (!manifest || !manifest.analyses.some(item => item.analysis_id === id)) return
    setAnalysis(id)
    setView(null)
  }, [publicationSet, publication])
  const setViewId = useCallback((id: string) => {
    if (publicationSet.status !== 'success' || publication === null || analysis === null) return
    const summary = publicationSet.data.manifests.get(publication)?.analyses.find(item => item.analysis_id === analysis)
    if (!summary || !summary.views.some(item => item.view_id === id)) return
    setView(id)
  }, [publicationSet, publication, analysis])
  const previous = useCallback(() => {
    if (page > 0) setPage(page - 1)
  }, [page])
  const next = useCallback(() => {
    if (publicationSet.status === 'success' && page + 1 < pages.length) setPage(page + 1)
  }, [page, pages.length, publicationSet.status])

  return {
    list, manifest, result, chart, publication, analysis, view, page,
    canPrevious, canNext, selectPublication, selectAnalysis, setView: setViewId, previous, next,
  }
}
