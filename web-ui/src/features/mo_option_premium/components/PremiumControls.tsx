import type { PremiumExpiry, PremiumPriceType } from '../api/moOptionPremium'
import type {
  SelectedOptionType,
  SelectedReferenceBasis,
  SelectedRepresentation,
  SelectedTimeNormalization,
  SelectedValueBasis,
} from '../model/premiumPlane'

export function PremiumQueryControls({ selectedDate, priceType, selectDate, selectPriceType }: {
  selectedDate: string
  priceType: PremiumPriceType
  selectDate: (date: string) => void
  selectPriceType: (priceType: PremiumPriceType) => void
}) {
  return (
    <div className="premium-query">
      <label htmlFor="premium-as-of">Observation 日期
        <input id="premium-as-of" type="date" value={selectedDate}
          onChange={(event) => selectDate(event.currentTarget.value)} />
      </label>
      <label htmlFor="premium-price-type">价格口径
        <select id="premium-price-type" value={priceType}
          onChange={(event) => selectPriceType(event.currentTarget.value as PremiumPriceType)}>
          <option value="open">open</option><option value="high">high</option>
          <option value="low">low</option><option value="close">close</option>
        </select>
      </label>
    </div>
  )
}

export function PremiumPresentationControls({ optionType, referenceBasis, valueBasis, timeNormalization,
  representation, setOptionType, setReferenceBasis, setValueBasis, setTimeNormalization, setRepresentation }: {
  optionType: SelectedOptionType
  referenceBasis: SelectedReferenceBasis
  valueBasis: SelectedValueBasis
  timeNormalization: SelectedTimeNormalization
  representation: SelectedRepresentation
  setOptionType: (value: SelectedOptionType) => void
  setReferenceBasis: (value: SelectedReferenceBasis) => void
  setValueBasis: (value: SelectedValueBasis) => void
  setTimeNormalization: (value: SelectedTimeNormalization) => void
  setRepresentation: (value: SelectedRepresentation) => void
}) {
  return (
    <div className="premium-controls">
      <fieldset><legend>Option type</legend>
        <label><input type="radio" name="premium-side" checked={optionType === 'call'} onChange={() => setOptionType('call')} />Call</label>
        <label><input type="radio" name="premium-side" checked={optionType === 'put'} onChange={() => setOptionType('put')} />Put</label>
      </fieldset>
      <fieldset className="premium-metric-controls"><legend>Metric settings</legend>
        <div><strong>Reference basis</strong>
          <label><input type="radio" name="premium-reference-basis" checked={referenceBasis === 'underlying_spot'} onChange={() => setReferenceBasis('underlying_spot')} />Underlying spot</label>
          <label><input type="radio" name="premium-reference-basis" checked={referenceBasis === 'expiry_futures'} onChange={() => setReferenceBasis('expiry_futures')} />Same-expiry futures</label>
        </div>
        <div><strong>Calculation basis</strong>
          <label><input type="radio" name="premium-value-basis" checked={valueBasis === 'total'} onChange={() => setValueBasis('total')} />Total value</label>
          <label><input type="radio" name="premium-value-basis" checked={valueBasis === 'time_value'} onChange={() => setValueBasis('time_value')} />Time value</label>
          <strong>Time normalization</strong>
          <label><input type="radio" name="premium-time-normalization" checked={timeNormalization === 'unannualized'} onChange={() => setTimeNormalization('unannualized')} />Unannualized</label>
          <label><input type="radio" name="premium-time-normalization" checked={timeNormalization === 'annualized'} onChange={() => setTimeNormalization('annualized')} />Annualized</label>
        </div>
        <div><strong>Representation</strong>
          <label><input type="radio" name="premium-representation" checked={representation === 'points'} onChange={() => setRepresentation('points')} />Points</label>
          <label><input type="radio" name="premium-representation" checked={representation === 'yield'} onChange={() => setRepresentation('yield')} />Yield</label>
        </div>
      </fieldset>
    </div>
  )
}

export function PremiumExpirySelector({ expiries, selectedExpiries, toggleExpiry }: {
  expiries: PremiumExpiry[]
  selectedExpiries: string[]
  toggleExpiry: (expiryDate: string) => void
}) {
  const selectedSet = new Set(selectedExpiries)
  return (
    <fieldset className="expiry-selector premium-expiry-selector">
      <legend>Visible expiries</legend>
      <div className="expiry-choices">{expiries.map((expiry) => (
        <label key={expiry.expiry_date} className="expiry-choice">
          <input type="checkbox" checked={selectedSet.has(expiry.expiry_date)}
            disabled={selectedSet.has(expiry.expiry_date) && selectedExpiries.length === 1}
            onChange={() => toggleExpiry(expiry.expiry_date)} />
          <span>{expiry.expiry_date}</span>
        </label>
      ))}</div>
    </fieldset>
  )
}
