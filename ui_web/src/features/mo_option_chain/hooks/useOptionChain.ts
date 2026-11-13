import { useCallback, useEffect, useRef, useState } from 'react'
import { ChainRequestError, loadMoOptionChain } from '../api/moOptionChain'
import { useOptionChainPresentation } from './useOptionChainPresentation'
import type { OptionChain } from '../api/moOptionChain'

export type OptionChainPageState =
  | { status: 'idle' }
  | { status: 'loading'; date: string }
  | { status: 'success'; chain: OptionChain }
  | { status: 'error'; date: string; error: ChainRequestError }

function useOptionChainQuery() {
  const [selectedDate, setSelectedDate] = useState('')
  const [page, setPage] = useState<OptionChainPageState>({ status: 'idle' })
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  const selectDate = useCallback((date: string) => {
    request.current?.abort()
    const id = ++nextRequestId.current
    setSelectedDate(date)

    if (!date) {
      request.current = null
      setPage({ status: 'idle' })
      return
    }

    const controller = new AbortController()
    request.current = controller
    setPage({ status: 'loading', date })
    void loadMoOptionChain(date, controller.signal).then((chain) => {
      if (nextRequestId.current === id && !controller.signal.aborted) {
        setPage({ status: 'success', chain })
      }
    }).catch((error: unknown) => {
      if (nextRequestId.current !== id || controller.signal.aborted) return
      setPage({
        status: 'error',
        date,
        error: error instanceof ChainRequestError
          ? error
          : new ChainRequestError('network', '无法连接数据服务'),
      })
    })
  }, [])

  return { selectedDate, page, selectDate }
}

export function useOptionChain() {
  const query = useOptionChainQuery()
  const presentation = useOptionChainPresentation(query.page.status === 'success' ? query.page.chain : null)
  return { ...query, ...presentation }
}
