import { formatDecimal, formatInteger, formatPercent } from './number'

export type UnitKind = 'ratio' | 'count' | 'decimal' | 'plain'

const ratioUnits = new Set(['decimal_ratio', 'probability', 'frequency'])
const countUnits = new Set(['count'])
const plainUnits = new Set(['date', 'category'])

/** Classify an explicit Visualization/statistical unit for display formatting only. */
export function unitKind(unit?: string): UnitKind {
  if (unit && ratioUnits.has(unit)) return 'ratio'
  if (unit && countUnits.has(unit)) return 'count'
  if (unit && plainUnits.has(unit)) return 'plain'
  return 'decimal'
}

export function isRatioUnit(unit?: string): boolean {
  return unitKind(unit) === 'ratio'
}

/** Presentation only: callers must supply the value's explicit semantic unit. */
export function formatUnit(value: number | null | undefined, unit?: string, missing = '不适用'): string {
  if (value == null || !Number.isFinite(value)) return missing
  switch (unitKind(unit)) {
    case 'ratio': return formatPercent(value, missing)
    case 'count': return formatInteger(value, missing)
    case 'plain': return String(value)
    default: return formatDecimal(value, missing)
  }
}
