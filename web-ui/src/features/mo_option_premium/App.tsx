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
  SelectedReferenceBasis,
  SelectedRepresentation,
  SelectedTimeNormalization,
  SelectedValueBasis,
} from './premiumPlane'

type PageState =
  | { status: 'idle' }
  | { status: 'loading'; asOf: string; priceType: PremiumPriceType }
  | { status: 'success'; plane: PremiumPlane; rawPayload: unknown }
  | { status: 'error'; asOf: string; priceType: PremiumPriceType; error: PremiumRequestError }

const errorTitles: Record<PremiumErrorKind, string> = {
  invalid_request: 'Invalid request',
  unsupported_query: 'Unsupported query',
  date_not_available: 'No data for this date',
  premium_plane_unavailable: 'Premium plane unavailable',
}

function errorTitle(error: PremiumRequestError): string {
  if (error.kind === 'network') return 'Cannot reach the data service'
  if (error.kind === 'invalid_response') return 'Invalid data-service response'
  return errorTitles[error.kind]
}

function RawResponseInspector({ payload }: { payload: unknown }) {
  const [copyFeedback, setCopyFeedback] = useState('')
  const prettyJson = JSON.stringify(payload, null, 2)

  async function copyJson() {
    try {
      await navigator.clipboard.writeText(prettyJson)
      setCopyFeedback('Copied')
    } catch {
      setCopyFeedback('Copy failed')
    }
  }

  return (
    <details className="raw-response-inspector">
      <summary>View raw response</summary>
      <div className="raw-response-toolbar">
        <strong>Raw backend response</strong>
        <button type="button" onClick={() => void copyJson()}>Copy JSON</button>
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
  const [selectedReferenceBasis, setSelectedReferenceBasis] = useState<SelectedReferenceBasis>('underlying_spot')
  const [selectedValueBasis, setSelectedValueBasis] = useState<SelectedValueBasis>('total')
  const [selectedTimeNormalization, setSelectedTimeNormalization] = useState<SelectedTimeNormalization>('annualized')
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
    setSelectedReferenceBasis('underlying_spot')
    setSelectedValueBasis('total')
    setSelectedTimeNormalization('annualized')
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
          : new PremiumRequestError('invalid_response', 'The page could not process the response'),
      })
    })
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
      selectedReferenceBasis,
      selectedValueBasis,
      selectedTimeNormalization,
      selectedRepresentation,
      selectedExpirySet,
    )
    : null

  return (
    <main className="premium-page">
      <header>
        <p className="eyebrow">hg-market-state-lab</p>
        <h1>MO 年化权利金平面</h1>
        <p>Select an observation and price type to inspect real, sparse option observations.</p>
      </header>
      <div className="premium-query">
        <label htmlFor="premium-as-of">Observation 日期
          <input id="premium-as-of" type="date" value={selectedDate}
            onChange={(event) => { setSelectedDate(event.currentTarget.value); load(event.currentTarget.value, priceType) }} />
        </label>
        <label htmlFor="premium-price-type">价格口径
          <select id="premium-price-type" value={priceType}
            onChange={(event) => { const value = event.currentTarget.value as PremiumPriceType; setPriceType(value); if (selectedDate) load(selectedDate, value) }}>
            <option value="open">open</option><option value="high">high</option>
            <option value="low">low</option><option value="close">close</option>
          </select>
        </label>
      </div>

      {page.status === 'idle' && <p role="status">Select an observation date.</p>}
      {page.status === 'loading' && <p role="status">Loading {page.asOf} · {page.priceType} premium plane…</p>}
      {page.status === 'error' && <section className="message error" role="alert"><h2>{errorTitle(page.error)}</h2><p>{page.asOf} · {page.priceType}</p><p>{page.error.message}</p></section>}
      {page.status === 'success' && projection !== null && (
        <section className="results premium-results" aria-label="Premium plane results">
          <h2>{page.plane.observation.value} · {page.plane.option_product}</h2>
          <dl className="facts">
            <div><dt>Observation</dt><dd>{page.plane.observation.value}</dd></div>
            <div><dt>Price type</dt><dd>{page.plane.price_type}</dd></div>
            <div><dt>Underlying</dt><dd>{page.plane.underlying.instrument_id}</dd></div>
            <div><dt>Spot</dt><dd>{formatPlaneNumber(page.plane.underlying.price)}</dd></div>
          </dl>

          <div className="premium-controls">
            <fieldset><legend>Option type</legend>
              <label><input type="radio" name="premium-side" checked={selectedOptionType === 'call'} onChange={() => setSelectedOptionType('call')} />Call</label>
              <label><input type="radio" name="premium-side" checked={selectedOptionType === 'put'} onChange={() => setSelectedOptionType('put')} />Put</label>
            </fieldset>
            <fieldset className="premium-metric-controls"><legend>Metric settings</legend>
              <div><strong>Reference basis</strong>
                <label><input type="radio" name="premium-reference-basis" checked={selectedReferenceBasis === 'underlying_spot'} onChange={() => setSelectedReferenceBasis('underlying_spot')} />Underlying spot</label>
                <label><input type="radio" name="premium-reference-basis" checked={selectedReferenceBasis === 'expiry_futures'} onChange={() => setSelectedReferenceBasis('expiry_futures')} />Same-expiry futures</label>
              </div>
              <div><strong>Calculation basis</strong>
                <label><input type="radio" name="premium-value-basis" checked={selectedValueBasis === 'total'} onChange={() => setSelectedValueBasis('total')} />Total value</label>
                <label><input type="radio" name="premium-value-basis" checked={selectedValueBasis === 'time_value'} onChange={() => setSelectedValueBasis('time_value')} />Time value</label>
                <strong>Time normalization</strong>
                <label><input type="radio" name="premium-time-normalization" checked={selectedTimeNormalization === 'unannualized'} onChange={() => setSelectedTimeNormalization('unannualized')} />Unannualized</label>
                <label><input type="radio" name="premium-time-normalization" checked={selectedTimeNormalization === 'annualized'} onChange={() => setSelectedTimeNormalization('annualized')} />Annualized</label>
              </div>
              <div><strong>Representation</strong>
                <label><input type="radio" name="premium-representation" checked={selectedRepresentation === 'points'} onChange={() => setSelectedRepresentation('points')} />Points</label>
                <label><input type="radio" name="premium-representation" checked={selectedRepresentation === 'yield'} onChange={() => setSelectedRepresentation('yield')} />Yield</label>
              </div>
            </fieldset>
          </div>

          <fieldset className="expiry-selector premium-expiry-selector"><legend>Visible expiries</legend><div className="expiry-choices">
            {page.plane.expiries.map((expiry) => <label key={expiry.expiry_date} className="expiry-choice">
              <input type="checkbox" checked={selectedExpirySet.has(expiry.expiry_date)} disabled={selectedExpirySet.has(expiry.expiry_date) && selectedExpiries.length === 1} onChange={() => toggleExpiry(expiry.expiry_date)} /><span>{expiry.expiry_date}</span>
            </label>)}
          </div></fieldset>

          {projection.rows.length === 0 ? <p className="plane-empty">No analytical observation for this presentation.</p> : (
            <div className="premium-table-wrap"><table className="premium-table"><thead><tr><th scope="col"><span>Strike</span><small>Spot · {formatPlaneNumber(page.plane.underlying.price)}</small></th>
              {projection.expiries.map((expiry) => <th scope="col" key={expiry.expiry_date}><span>{expiry.expiry_date}</span><small>DTE {expiry.dte}</small><small>{expiry.futures === null ? 'No eligible futures reference' : `${expiry.futures.instrument_id} · ${formatPlaneNumber(expiry.futures.price)}`}</small></th>)}
            </tr></thead><tbody>{projection.rows.map((row) => <tr key={row.strike}><th scope="row" className={classifyStrikeRelativeToReference(row.strike, page.plane.underlying.price)}>{formatPlaneNumber(row.strike)}</th>
              {row.cells.map((cell, index) => {
                const expiry = projection.expiries[index]
                const referenceClass = classifyStrikeRelativeToReference(row.strike, expiry.futures?.price ?? null)
                if (cell.kind === 'absent') return <td className={referenceClass} key={expiry.expiry_date} aria-label={`${expiry.expiry_date} no Point`} />
                if (cell.kind === 'unavailable') return <td className={referenceClass} key={expiry.expiry_date} aria-label={`${expiry.expiry_date} metric unavailable`}>—</td>
                return <td className={referenceClass} key={expiry.expiry_date}>{formatMetric(cell.value, selectedRepresentation)}</td>
              })}
            </tr>)}</tbody></table></div>
          )}
          <p className="plane-legend">Blank = no Point; — = metric unavailable for a real Point.</p>
          <RawResponseInspector key={`${page.plane.observation.value}-${page.plane.price_type}`} payload={page.rawPayload} />
        </section>
      )}
    </main>
  )
}

export default App
