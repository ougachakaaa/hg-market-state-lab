import { useEffect, useState } from 'react'
import { getCapability, listCapabilities, type Capability } from '../api/catalog'

type Load<T> = { status: 'loading' | 'idle' } | { status: 'success'; data: T } | { status: 'error'; error: unknown }

export function useCatalog() {
  const [list, setList] = useState<Load<Capability[]>>({ status: 'loading' })
  const [listRevision, setListRevision] = useState(0)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<Load<Capability>>({ status: 'idle' })
  const [detailRevision, setDetailRevision] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    listCapabilities(controller.signal).then(data => {
      if (!controller.signal.aborted) setList({ status: 'success', data })
    }, error => {
      if (!controller.signal.aborted) setList({ status: 'error', error })
    })
    return () => controller.abort()
  }, [listRevision])

  useEffect(() => {
    if (selectedId === null) return
    const controller = new AbortController()
    getCapability(selectedId, controller.signal).then(data => {
      if (!controller.signal.aborted) setDetail({ status: 'success', data })
    }, error => {
      if (!controller.signal.aborted) setDetail({ status: 'error', error })
    })
    return () => controller.abort()
  }, [selectedId, detailRevision])

  return {
    list, detail, selectedId,
    select: (id: string) => { setSelectedId(id); setDetail({ status: 'loading' }); setDetailRevision(n => n + 1) },
    clearDetail: () => { setSelectedId(null); setDetail({ status: 'idle' }) },
    retryList: () => { setList({ status: 'loading' }); setListRevision(n => n + 1) },
    retryDetail: () => { setDetail({ status: 'loading' }); setDetailRevision(n => n + 1) },
  }
}
