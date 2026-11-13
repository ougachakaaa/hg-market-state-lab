import { useCallback, useEffect, useRef, useState } from 'react'
import { getCapability, listCapabilities } from '../api/catalog'
import type {
  CatalogDetailState,
  CatalogListState,
  CatalogSelection,
  ResearchOverviewController,
} from '../model/catalogPresentation'

// Production query controller. It owns authenticated HTTP access, independent list and
// detail lifecycle, retries, cancellation and stale-response isolation. Local selection
// retires any online detail request without issuing a detail GET.
export function useCatalog(): ResearchOverviewController {
  const [list, setList] = useState<CatalogListState>({ status: 'loading' })
  const [listRevision, setListRevision] = useState(0)
  const [selection, setSelection] = useState<CatalogSelection>(null)
  const [detail, setDetail] = useState<CatalogDetailState>({ status: 'idle' })
  const [detailRevision, setDetailRevision] = useState(0)
  const listRequest = useRef(0)
  const detailRequest = useRef(0)
  const selectedId = selection?.kind === 'online' ? selection.id : null

  useEffect(() => {
    const request = ++listRequest.current
    const controller = new AbortController()
    listCapabilities(controller.signal).then(data => {
      if (!controller.signal.aborted && request === listRequest.current) setList({ status: 'success', data })
    }, error => {
      if (!controller.signal.aborted && request === listRequest.current) setList({ status: 'error', error })
    })
    return () => controller.abort()
  }, [listRevision])

  useEffect(() => {
    if (selectedId === null) return
    const request = ++detailRequest.current
    const controller = new AbortController()
    getCapability(selectedId, controller.signal).then(data => {
      if (!controller.signal.aborted && request === detailRequest.current) setDetail({ status: 'success', data })
    }, error => {
      if (!controller.signal.aborted && request === detailRequest.current) setDetail({ status: 'error', error })
    })
    return () => controller.abort()
  }, [selectedId, detailRevision])

  const selectOnline = useCallback((id: string) => {
    detailRequest.current += 1
    setSelection({ kind: 'online', id })
    setDetail({ status: 'loading' })
    setDetailRevision(revision => revision + 1)
  }, [])
  const selectLocal = useCallback((id: string) => {
    detailRequest.current += 1
    setSelection({ kind: 'local', id })
    setDetail({ status: 'idle' })
  }, [])
  const retryList = useCallback(() => {
    listRequest.current += 1
    setList({ status: 'loading' })
    setListRevision(revision => revision + 1)
  }, [])
  const retryDetail = useCallback(() => {
    detailRequest.current += 1
    setDetail({ status: 'loading' })
    setDetailRevision(revision => revision + 1)
  }, [])

  return { list, detail, selection, selectOnline, selectLocal, retryList, retryDetail }
}
