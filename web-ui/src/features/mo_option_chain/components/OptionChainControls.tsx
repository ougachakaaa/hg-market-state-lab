import type { ExpiryGroup } from '../api/moOptionChain'
import type { ExpiryColors } from '../charts/expiryPalette'
import type { SeriesColors } from '../model/presentationState'
import { MIN_STRIKE_HALF_RANGE_POINTS } from '../model/strikeViewport'

export function OptionChainQueryControl({ selectedDate, selectDate }: {
  selectedDate: string
  selectDate: (date: string) => void
}) {
  return (
    <>
      <label className="date-field" htmlFor="target-date">目标交易日</label>
      <input id="target-date" type="date" value={selectedDate}
        onChange={(event) => selectDate(event.currentTarget.value)} />
    </>
  )
}

export function ExpirySwatches({ colors, hasFutures }: { colors: ExpiryColors; hasFutures: boolean }) {
  return (
    <span className="expiry-swatches" aria-hidden="true">
      <span className="expiry-swatch" style={{ backgroundColor: colors.call }} />
      <span className="expiry-swatch" style={{ backgroundColor: colors.put }} />
      {hasFutures && <span className="expiry-swatch" style={{ backgroundColor: colors.futures }} />}
    </span>
  )
}

export function StrikeViewportControl({ halfRangePoints, shrink, expand }: {
  halfRangePoints: number
  shrink: () => void
  expand: () => void
}) {
  return (
    <div className="strike-control" role="group" aria-label="行权价视窗半宽">
      <span>行权价视窗：±{halfRangePoints} 点</span>
      <button type="button" aria-label="缩小行权价视窗"
        disabled={halfRangePoints === MIN_STRIKE_HALF_RANGE_POINTS} onClick={shrink}>−</button>
      <button type="button" aria-label="扩大行权价视窗" onClick={expand}>+</button>
    </div>
  )
}

export function ExpirySelector({ expiries, selectedExpiries, palette, toggleExpiry }: {
  expiries: ExpiryGroup[]
  selectedExpiries: string[]
  palette: Record<string, ExpiryColors>
  toggleExpiry: (expiryDate: string) => void
}) {
  const selectedSet = new Set(selectedExpiries)
  return (
    <fieldset className="expiry-selector">
      <legend>显示到期日</legend>
      <div className="expiry-choices">
        {expiries.map((group) => (
          <label key={group.expiry_date} className="expiry-choice">
            <input type="checkbox" checked={selectedSet.has(group.expiry_date)}
              disabled={selectedSet.has(group.expiry_date) && selectedExpiries.length === 1}
              onChange={() => toggleExpiry(group.expiry_date)} />
            <ExpirySwatches colors={palette[group.expiry_date]} hasFutures={group.futures !== null} />
            <span>{group.expiry_date}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}

export function SeriesColorControls({ colors, changeColor }: {
  colors: SeriesColors
  changeColor: (side: keyof SeriesColors, color: string) => void
}) {
  return (
    <div className="series-color-controls" role="group" aria-label="图表颜色">
      <label>Call 颜色
        <input type="color" value={colors.call} onChange={(event) => changeColor('call', event.currentTarget.value)} />
      </label>
      <label>Put 颜色
        <input type="color" value={colors.put} onChange={(event) => changeColor('put', event.currentTarget.value)} />
      </label>
      <label>Futures 颜色
        <input type="color" value={colors.futures} onChange={(event) => changeColor('futures', event.currentTarget.value)} />
      </label>
    </div>
  )
}
