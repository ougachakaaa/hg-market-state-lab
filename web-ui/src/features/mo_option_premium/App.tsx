import { useEffect, useRef, useState } from 'react'
import { loadMoOptionPremiumPlane, PremiumRequestError } from './api/moOptionPremium'
import type { PremiumErrorKind, PremiumPlane, PremiumPriceType } from './api/moOptionPremium'
import {
  formatMetric,
  formatPlaneNumber,
  MIN_STRIKE_HALF_RANGE_POINTS,
  projectPremiumPlane,
  STRIKE_HALF_RANGE_STEP,
} from './premiumPlane'
import type { SelectedMetric, SelectedOptionType } from './premiumPlane'

type PageState =
  | { status: 'idle' }
  | { status: 'loading'; asOf: string; priceType: PremiumPriceType }
  | { status: 'success'; plane: PremiumPlane }
  | { status: 'error'; asOf: string; priceType: PremiumPriceType; error: PremiumRequestError }

const errorTitles: Record<PremiumErrorKind, string> = {
  invalid_request: '请求日期或参数无效',
  unsupported_query: '当前不支持此查询',
  date_not_available: '该日期无可用数据',
  premium_plane_unavailable: '当前无法生成权利金平面',
}

function errorTitle(error: PremiumRequestError): string {
  if (error.kind === 'network') return '无法连接数据服务'
  if (error.kind === 'invalid_response') return '数据服务响应异常'
  return errorTitles[error.kind]
}

function App() {
  const [selectedDate, setSelectedDate] = useState('')
  const [priceType, setPriceType] = useState<PremiumPriceType>('close')
  const [page, setPage] = useState<PageState>({ status: 'idle' })
  const [selectedOptionType, setSelectedOptionType] = useState<SelectedOptionType>('call')
  const [selectedMetric, setSelectedMetric] = useState<SelectedMetric>('annualized_premium_points')
  const [selectedExpiries, setSelectedExpiries] = useState<string[]>([])
  const [strikeHalfRangePoints, setStrikeHalfRangePoints] = useState(MIN_STRIKE_HALF_RANGE_POINTS)
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  function resetPresentation() {
    setSelectedOptionType('call')
    setSelectedMetric('annualized_premium_points')
    setSelectedExpiries([])
    setStrikeHalfRangePoints(MIN_STRIKE_HALF_RANGE_POINTS)
  }

  function load(asOf: string, requestedPriceType: PremiumPriceType) {
    request.current?.abort()
    const id = ++nextRequestId.current

    if (!asOf) {
      request.current = null
      setPage({ status: 'idle' })
      resetPresentation()
      return
    }

    const controller = new AbortController()
    request.current = controller
    setPage({ status: 'loading', asOf, priceType: requestedPriceType })
    resetPresentation()
    void loadMoOptionPremiumPlane(asOf, requestedPriceType, controller.signal).then((plane) => {
      if (nextRequestId.current === id && !controller.signal.aborted) {
        setSelectedExpiries(plane.expiries.map((expiry) => expiry.expiry_date))
        setPage({ status: 'success', plane })
      }
    }).catch((error: unknown) => {
      if (nextRequestId.current !== id || controller.signal.aborted) return
      setPage({
        status: 'error',
        asOf,
        priceType: requestedPriceType,
        error: error instanceof PremiumRequestError
          ? error
          : new PremiumRequestError('invalid_response', '页面无法处理数据服务响应'),
      })
    })
  }

  function selectDate(asOf: string) {
    setSelectedDate(asOf)
    load(asOf, priceType)
  }

  function selectPriceType(value: PremiumPriceType) {
    setPriceType(value)
    if (selectedDate) load(selectedDate, value)
  }

  function toggleExpiry(expiryDate: string) {
    setSelectedExpiries((current) => current.includes(expiryDate)
      ? current.length > 1 ? current.filter((date) => date !== expiryDate) : current
      : [...current, expiryDate])
  }

  const selectedExpirySet = new Set(selectedExpiries)
  const projection = page.status === 'success'
    ? projectPremiumPlane(
      page.plane,
      selectedOptionType,
      selectedMetric,
      selectedExpirySet,
      strikeHalfRangePoints,
    )
    : null

  return (
    <main className="premium-page">
      <header>
        <p className="eyebrow">hg-market-state-lab</p>
        <h1>MO 年化权利金平面</h1>
        <p>选择 observation 与取价口径，检视真实合约构成的稀疏数值平面。</p>
      </header>

      <div className="premium-query">
        <label htmlFor="premium-as-of">Observation 日期
          <input id="premium-as-of" type="date" value={selectedDate}
            onChange={(event) => selectDate(event.currentTarget.value)} />
        </label>
        <label htmlFor="premium-price-type">价格口径
          <select id="premium-price-type" value={priceType}
            onChange={(event) => selectPriceType(event.currentTarget.value as PremiumPriceType)}>
            <option value="open">open</option>
            <option value="high">high</option>
            <option value="low">low</option>
            <option value="close">close</option>
          </select>
        </label>
      </div>

      {page.status === 'idle' && <p role="status">请选择 Observation 日期。</p>}
      {page.status === 'loading' && (
        <p role="status">正在加载 {page.asOf} · {page.priceType} 的权利金平面…</p>
      )}
      {page.status === 'error' && (
        <section className="message error" role="alert">
          <h2>{errorTitle(page.error)}</h2>
          <p>查询：{page.asOf} · {page.priceType}</p>
          {page.error.kind !== 'network' && page.error.kind !== 'invalid_response' && <p>{page.error.message}</p>}
        </section>
      )}
      {page.status === 'success' && projection !== null && (
        <section className="results premium-results" aria-label="权利金平面结果">
          <h2>{page.plane.observation.value} · {page.plane.option_product}</h2>
          <dl className="facts">
            <div><dt>Observation</dt><dd>{page.plane.observation.value}</dd></div>
            <div><dt>价格口径</dt><dd>{page.plane.price_type}</dd></div>
            <div><dt>标的指数</dt><dd>{page.plane.underlying.instrument_id}</dd></div>
            <div><dt>标的价格</dt><dd>{formatPlaneNumber(page.plane.underlying.price)}</dd></div>
          </dl>

          <div className="premium-controls">
            <fieldset>
              <legend>期权类型</legend>
              <label><input type="radio" name="premium-side" value="call" checked={selectedOptionType === 'call'} onChange={() => setSelectedOptionType('call')} />Call</label>
              <label><input type="radio" name="premium-side" value="put" checked={selectedOptionType === 'put'} onChange={() => setSelectedOptionType('put')} />Put</label>
            </fieldset>
            <fieldset>
              <legend>展示指标</legend>
              <label><input type="radio" name="premium-metric" value="annualized_premium_points" checked={selectedMetric === 'annualized_premium_points'} onChange={() => setSelectedMetric('annualized_premium_points')} />年化权利金点数</label>
              <label><input type="radio" name="premium-metric" value="annualized_seller_premium_yield" checked={selectedMetric === 'annualized_seller_premium_yield'} onChange={() => setSelectedMetric('annualized_seller_premium_yield')} />卖方年化权利金收益率</label>
            </fieldset>
          </div>

          <fieldset className="expiry-selector premium-expiry-selector">
            <legend>显示到期日</legend>
            <div className="expiry-choices">
              {page.plane.expiries.map((expiry) => (
                <label key={expiry.expiry_date} className="expiry-choice">
                  <input type="checkbox" checked={selectedExpirySet.has(expiry.expiry_date)}
                    disabled={selectedExpirySet.has(expiry.expiry_date) && selectedExpiries.length === 1}
                    onChange={() => toggleExpiry(expiry.expiry_date)} />
                  <span>{expiry.expiry_date}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="strike-control" role="group" aria-label="Premium 行权价视窗半宽">
            <span>行权价视窗：±{strikeHalfRangePoints} 点</span>
            <button type="button" aria-label="缩小 Premium 行权价视窗" disabled={strikeHalfRangePoints === MIN_STRIKE_HALF_RANGE_POINTS} onClick={() => setStrikeHalfRangePoints((value) => Math.max(MIN_STRIKE_HALF_RANGE_POINTS, value - STRIKE_HALF_RANGE_STEP))}>−</button>
            <button type="button" aria-label="扩大 Premium 行权价视窗" onClick={() => setStrikeHalfRangePoints((value) => value + STRIKE_HALF_RANGE_STEP)}>+</button>
          </div>

          {projection.rows.length === 0 ? (
            <p className="plane-empty">当前选择与行权价范围内无 analytical observation。</p>
          ) : (
            <div className="premium-table-wrap">
              <table className="premium-table">
                <thead>
                  <tr>
                    <th scope="col">行权价</th>
                    {projection.expiries.map((expiry) => (
                      <th scope="col" key={expiry.expiry_date}>
                        <span>{expiry.expiry_date}</span>
                        <small>DTE {expiry.dte}</small>
                        <small>{expiry.futures === null
                          ? '无合法 futures reference'
                          : `${expiry.futures.instrument_id} · ${formatPlaneNumber(expiry.futures.price)}`}</small>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {projection.rows.map((row) => (
                    <tr key={row.strike}>
                      <th scope="row">{formatPlaneNumber(row.strike)}</th>
                      {row.cells.map((cell, index) => {
                        const expiryDate = projection.expiries[index].expiry_date
                        if (cell.kind === 'absent') return <td key={expiryDate} aria-label={`${expiryDate} 无 Point`} />
                        if (cell.kind === 'unavailable') return <td key={expiryDate} aria-label={`${expiryDate} metric unavailable`}>—</td>
                        return <td key={expiryDate}>{formatMetric(cell.value, selectedMetric)}</td>
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="plane-legend">空白 = 无 Point；— = Point 存在但 metric unavailable。</p>
        </section>
      )}
    </main>
  )
}

export default App
