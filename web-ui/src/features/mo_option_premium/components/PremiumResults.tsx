import { useState } from 'react'
import type { PremiumErrorKind, PremiumPlane } from '../api/moOptionPremium'
import { PremiumRequestError } from '../api/moOptionPremium'
import { classifyStrikeRelativeToReference, formatMetric, formatPlaneNumber } from '../model/premiumPlane'
import type { PremiumPlaneProjection, SelectedRepresentation } from '../model/premiumPlane'

const errorTitles: Record<PremiumErrorKind, string> = {
  invalid_request: 'Invalid request',
  unsupported_query: 'Unsupported query',
  date_not_available: 'No data for this date',
  premium_plane_unavailable: 'Premium plane unavailable',
}

export function PremiumError({ asOf, priceType, error }: {
  asOf: string
  priceType: string
  error: PremiumRequestError
}) {
  const title = error.kind === 'network' ? 'Cannot reach the data service'
    : error.kind === 'invalid_response' ? 'Invalid data-service response'
      : errorTitles[error.kind]
  return <section className="message error" role="alert"><h2>{title}</h2><p>{asOf} · {priceType}</p><p>{error.message}</p></section>
}

export function PremiumSummary({ plane }: { plane: PremiumPlane }) {
  return (
    <>
      <h2>{plane.observation.value} · {plane.option_product}</h2>
      <dl className="facts">
        <div><dt>Observation</dt><dd>{plane.observation.value}</dd></div>
        <div><dt>Price type</dt><dd>{plane.price_type}</dd></div>
        <div><dt>Underlying</dt><dd>{plane.underlying.instrument_id}</dd></div>
        <div><dt>Spot</dt><dd>{formatPlaneNumber(plane.underlying.price)}</dd></div>
      </dl>
    </>
  )
}

export function PremiumPlaneTable({ plane, projection, representation }: {
  plane: PremiumPlane
  projection: PremiumPlaneProjection
  representation: SelectedRepresentation
}) {
  if (projection.rows.length === 0) {
    return <p className="plane-empty">No analytical observation for this presentation.</p>
  }
  return (
    <div className="premium-table-wrap"><table className="premium-table"><thead><tr>
      <th scope="col"><span>Strike</span><small>Spot · {formatPlaneNumber(plane.underlying.price)}</small></th>
      {projection.expiries.map((expiry) => <th scope="col" key={expiry.expiry_date}>
        <span>{expiry.expiry_date}</span><small>DTE {expiry.dte}</small>
        <small>{expiry.futures === null ? 'No eligible futures reference' : `${expiry.futures.instrument_id} · ${formatPlaneNumber(expiry.futures.price)}`}</small>
      </th>)}
    </tr></thead><tbody>{projection.rows.map((row) => <tr key={row.strike}>
      <th scope="row" className={classifyStrikeRelativeToReference(row.strike, plane.underlying.price)}>{formatPlaneNumber(row.strike)}</th>
      {row.cells.map((cell, index) => {
        const expiry = projection.expiries[index]
        const referenceClass = classifyStrikeRelativeToReference(row.strike, expiry.futures?.price ?? null)
        if (cell.kind === 'absent') return <td className={referenceClass} key={expiry.expiry_date} aria-label={`${expiry.expiry_date} no Point`} />
        if (cell.kind === 'unavailable') return <td className={referenceClass} key={expiry.expiry_date} aria-label={`${expiry.expiry_date} metric unavailable`}>—</td>
        return <td className={referenceClass} key={expiry.expiry_date}>{formatMetric(cell.value, representation)}</td>
      })}
    </tr>)}</tbody></table></div>
  )
}

export function RawResponseInspector({ payload }: { payload: unknown }) {
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
