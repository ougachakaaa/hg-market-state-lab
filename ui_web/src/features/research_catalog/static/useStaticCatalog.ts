import { useCallback, useState } from 'react'
import {
  validateEmbeddedCatalog,
  type EmbeddedCatalogPayload,
  type ValidatedEmbeddedCatalog,
} from '../api/validateCatalog'
import type {
  CatalogDetailState,
  CatalogSelection,
  ResearchOverviewController,
} from '../model/catalogPresentation'

type CatalogState =
  | { status: 'success'; data: ValidatedEmbeddedCatalog }
  | { status: 'invalid'; error: unknown }

// Static controller: validates the embedded list/details once, then selects locally.
// It never performs a GET, retries a request or fabricates a missing detail result.
export function useStaticCatalog(payload: EmbeddedCatalogPayload): ResearchOverviewController {
  const [catalog] = useState<CatalogState>(() => {
    try {
      return { status: 'success', data: validateEmbeddedCatalog(payload) }
    } catch (error) {
      return { status: 'invalid', error }
    }
  })
  const [selection, setSelection] = useState<CatalogSelection>(null)

  const list = catalog.status === 'success'
    ? { status: 'success' as const, data: catalog.data.capabilities }
    : { status: 'invalid' as const, error: catalog.error }
  let detail: CatalogDetailState = { status: 'idle' }
  if (catalog.status === 'success' && selection?.kind === 'online') {
    const capability = catalog.data.details.get(selection.id)
    detail = capability ? { status: 'success', data: capability } : { status: 'missing', id: selection.id }
  }

  const selectOnline = useCallback((id: string) => {
    if (catalog.status !== 'success' || !catalog.data.capabilities.some(item => item.id === id)) return
    setSelection({ kind: 'online', id })
  }, [catalog])
  const selectLocal = useCallback((id: string) => setSelection({ kind: 'local', id }), [])

  return { list, detail, selection, selectOnline, selectLocal }
}
