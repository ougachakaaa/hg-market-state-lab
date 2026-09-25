import { useEffect, useRef, useState } from 'react'
import { loadMoOptionPremiumPlane, PremiumRequestError } from './api/moOptionPremium'
import type { PremiumErrorKind, PremiumPlane, PremiumPriceType } from './api/moOptionPremium'
import {
  classifyStrikeRelativeToReference,
  formatMetric,
  formatPlaneNumber,
  projectPremiumPlane,
} from './premiumPlane'
import type {
  SelectedOptionType,
  SelectedRepresentation,
  SelectedValueBasis,
} from './premiumPlane'

type PageState =
  | { status: 'idle' }
  | { status: 'loading'; asOf: string; priceType: PremiumPriceType }
  | { status: 'success'; plane: PremiumPlane; rawPayload: unknown }
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

function RawResponseInspector({ payload }: { payload: unknown }) {
  const [copyFeedback, setCopyFeedback] = useState('')
  const prettyJson = JSON.stringify(payload, null, 2)

  async function copyJson() {
    try {
      await navigator.clipboard.writeText(prettyJson)
      setCopyFeedback('已复制')
    } catch {
      setCopyFeedback('复制失败')
    }
  }

  return (
    <details className="raw-response-inspector">
      <summary>查看原始响应</summary>
      <div className="raw-response-toolbar">
        <strong>Raw backend response</strong>
        <button type="button" onClick={() => void copyJson()}>复制 JSON</button>
        {copyFeedback && <span role="status">{copyFeedback}</span>}
      </div>
      <pre>{prettyJson}</pre>
    </details>
  )
}

function App() {
  const [selectedDate, setSelectedDate] = useState('')
  const [priceType, setPriceType] = useState<PremiumPriceType>('close')
  const [page, setPage] = useState<PageState>({ status: 'idle' })
  const [selectedOptionType, setSelectedOptionType] = useState<SelectedOptionType>('call')
  const [selectedValueBasis, setSelectedValueBasis] = useState<SelectedValueBasis>('total')
  const [selectedRepresentation, setSelectedRepresentation] = useState<SelectedRepresentation>('points')
  const [selectedExpiries, setSelectedExpiries] = useState<string[]>([])
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  function resetPresentation() {
    setSelectedOptionType('call')
    setSelectedValueBasis('total')
    setSelectedRepresentation('points')
    setSelectedExpiries([])
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
    void loadMoOptionPremiumPlane(asOf, requestedPriceType, controller.signal).then((result) => {
      if (nextRequestId.current === id && !controller.signal.aborted) {
        setSelectedExpiries(result.plane.expiries.map((expiry) => expiry.expiry_date))
        setPage({ status: 'success', plane: result.plane, rawPayload: result.rawPayload })
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
      selectedValueBasis,
      selectedRepresentation,
      selectedExpirySet,
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
              <legend>价值口径</legend>
              <label><input type="radio" name="premium-value-basis" value="total" checked={selectedValueBasis === 'total'} onChange={() => setSelectedValueBasis('total')} />总价值</label>
              <label><input type="radio" name="premium-value-basis" value="time_value" checked={selectedValueBasis === 'time_value'} onChange={() => setSelectedValueBasis('time_value')} />时间价值</label>
            </fieldset>
            <fieldset>
              <legend>表示方式</legend>
              <label><input type="radio" name="premium-representation" value="points" checked={selectedRepresentation === 'points'} onChange={() => setSelectedRepresentation('points')} />点数</label>
              <label><input type="radio" name="premium-representation" value="yield" checked={selectedRepresentation === 'yield'} onChange={() => setSelectedRepresentation('yield')} />收益率</label>
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

          {projection.rows.length === 0 ? (
            <p className="plane-empty">当前选择下无 analytical observation。</p>
          ) : (
            <div className="premium-table-wrap">
              <table className="premium-table">
                <thead>
                  <tr>
                    <th scope="col">
                      <span>行权价</span>
                      <small>标的现价 · {formatPlaneNumber(page.plane.underlying.price)}</small>
                    </th>
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
                      <th
                        scope="row"
                        className={classifyStrikeRelativeToReference(
                          row.strike,
                          page.plane.underlying.price,
                        )}
                      >{formatPlaneNumber(row.strike)}</th>
                      {row.cells.map((cell, index) => {
                        const expiry = projection.expiries[index]
                        const expiryDate = expiry.expiry_date
                        const referenceClass = classifyStrikeRelativeToReference(
                          row.strike,
                          expiry.futures?.price ?? null,
                        )
                        if (cell.kind === 'absent') return <td className={referenceClass} key={expiryDate} aria-label={`${expiryDate} 无 Point`} />
                        if (cell.kind === 'unavailable') return <td className={referenceClass} key={expiryDate} aria-label={`${expiryDate} metric unavailable`}>—</td>
                        return <td className={referenceClass} key={expiryDate}>{formatMetric(cell.value, selectedRepresentation)}</td>
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="plane-legend">空白 = 无 Point；— = Point 存在但 metric unavailable。</p>
          <RawResponseInspector
            key={`${page.plane.observation.value}-${page.plane.price_type}`}
            payload={page.rawPayload}
          />
        </section>
      )}
    </main>
  )
}

export default App
