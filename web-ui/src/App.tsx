import { useEffect, useRef, useState } from 'react'
import { ChainRequestError, loadMoOptionChain } from './api/moOptionChain'
import type { ChainErrorKind, ExpiryGroup, OptionChain, OptionPoint } from './api/moOptionChain'
import ExpiryChart from './ExpiryChart'
import { formatPrice } from './priceDisplay'
import { MIN_STRIKE_HALF_RANGE_POINTS, STRIKE_HALF_RANGE_STEP, strikeViewport } from './strikeViewport'

type PageState =
  | { status: 'idle' }
  | { status: 'loading'; date: string }
  | { status: 'success'; chain: OptionChain }
  | { status: 'error'; date: string; error: ChainRequestError }

const errorTitles: Record<ChainErrorKind, string> = {
  invalid_request: '请求日期或参数无效',
  unsupported_query: '当前不支持此查询',
  date_not_available: '该日期无可用数据',
  option_chain_unavailable: '当前无法生成完整期权链',
  service_not_wired: '数据服务尚未接线',
}

function errorTitle(error: ChainRequestError): string {
  if (error.kind === 'network') return '无法连接数据服务'
  if (error.kind === 'invalid_response') return '数据服务响应异常'
  return errorTitles[error.kind]
}

function OptionTable({ title, points }: { title: string; points: OptionPoint[] }) {
  return (
    <section className="option-list">
      <h4>{title}</h4>
      <table>
        <thead><tr><th scope="col">合约标识</th><th scope="col">行权价</th><th scope="col">价格</th></tr></thead>
        <tbody>
          {points.map((point) => (
            <tr key={point.instrument_id}>
              <td>{point.instrument_id}</td>
              <td>{formatPrice(point.strike)}</td>
              <td>{formatPrice(point.price)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function ExpirySummary({ group, underlying, xDomain }: {
  group: ExpiryGroup
  underlying: OptionChain['underlying']
  xDomain: [number, number]
}) {
  return (
    <section className="expiry" aria-label={`${group.expiry_date} 到期日`}>
      <h3>{group.expiry_date}</h3>
      <p className="expiry-counts">Call {group.calls.length} · Put {group.puts.length}</p>
      <ExpiryChart group={group} underlying={underlying} xDomain={xDomain} />
      <details className="contract-details">
        <summary>合约明细</summary>
        <div className="expiry-content">
          <OptionTable title="Calls" points={group.calls} />
          <OptionTable title="Puts" points={group.puts} />
        </div>
      </details>
    </section>
  )
}

function App() {
  const [selectedDate, setSelectedDate] = useState('')
  const [page, setPage] = useState<PageState>({ status: 'idle' })
  const [strikeHalfRangePoints, setStrikeHalfRangePoints] = useState(MIN_STRIKE_HALF_RANGE_POINTS)
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  function selectDate(date: string) {
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
  }

  const xDomain = page.status === 'success'
    ? strikeViewport(page.chain.underlying.price, strikeHalfRangePoints)
    : null

  return (
    <main>
      <header>
        <p className="eyebrow">hg-market-state-lab</p>
        <h1>MO 期权链</h1>
        <p>选择交易日，查看中证 1000 指数参考价与各到期日的期权合约。</p>
      </header>

      <label className="date-field" htmlFor="target-date">目标交易日</label>
      <input
        id="target-date"
        type="date"
        value={selectedDate}
        onChange={(event) => selectDate(event.currentTarget.value)}
      />

      {page.status === 'idle' && <p role="status">请选择目标交易日。</p>}
      {page.status === 'loading' && <p role="status">正在加载 {page.date} 的期权链…</p>}
      {page.status === 'error' && (
        <section className="message error" role="alert">
          <h2>{errorTitle(page.error)}</h2>
          <p>目标日期：{page.date}</p>
          {page.error.kind !== 'network' && page.error.kind !== 'invalid_response' && (
            <p>{page.error.message}</p>
          )}
        </section>
      )}
      {page.status === 'success' && xDomain !== null && (
        <section className="results" aria-label="期权链结果">
          <h2>{page.chain.target_trade_date} · {page.chain.option_product}</h2>
          <dl className="facts">
            <div><dt>价格口径</dt><dd>{page.chain.price_type}</dd></div>
            <div><dt>标的指数</dt><dd>{page.chain.underlying.instrument_id}</dd></div>
            <div><dt>参考价</dt><dd>{formatPrice(page.chain.underlying.price)}</dd></div>
            <div><dt>到期日数量</dt><dd>{page.chain.expiries.length}</dd></div>
          </dl>
          <div className="strike-control" role="group" aria-label="行权价视窗半宽">
            <span>行权价视窗：±{strikeHalfRangePoints} 点</span>
            <button type="button" aria-label="缩小行权价视窗" disabled={strikeHalfRangePoints === MIN_STRIKE_HALF_RANGE_POINTS} onClick={() => setStrikeHalfRangePoints((value) => Math.max(MIN_STRIKE_HALF_RANGE_POINTS, value - STRIKE_HALF_RANGE_STEP))}>−</button>
            <button type="button" aria-label="扩大行权价视窗" onClick={() => setStrikeHalfRangePoints((value) => value + STRIKE_HALF_RANGE_STEP)}>+</button>
          </div>
          <h3>到期日</h3>
          {page.chain.expiries.map((group) => <ExpirySummary key={group.expiry_date} group={group} underlying={page.chain.underlying} xDomain={xDomain} />)}
        </section>
      )}
    </main>
  )
}

export default App
