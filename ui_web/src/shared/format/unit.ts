/** Presentation only: callers must supply the value's explicit semantic unit. */
export function formatUnit(value: number | null | undefined, unit?: string, missing = '不适用'): string {
  if (value == null || !Number.isFinite(value)) return missing
  if (unit !== 'decimal_ratio') return String(value)
  const rounded = (value * 100).toFixed(1)
  return `${Number(rounded) === 0 ? '0.0' : rounded}%`
}
