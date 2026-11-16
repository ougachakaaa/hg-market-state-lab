/** Shared display precision; never mutates or rescales producer facts. */
function fixed(value: number, digits: number): string {
  const normalized = Object.is(value, -0) ? 0 : value
  const text = normalized.toFixed(digits)
  return Number(text) === 0 ? (0).toFixed(digits) : text
}

export function formatPercent(value: number | null | undefined, missing = '不适用'): string {
  if (value == null || !Number.isFinite(value)) return missing
  return `${fixed(value * 100, 1)}%`
}

export function formatDecimal(value: number | null | undefined, missing = '不适用'): string {
  if (value == null || !Number.isFinite(value)) return missing
  return fixed(value, 2)
}

export function formatInteger(value: number | null | undefined, missing = '不适用'): string {
  if (value == null || !Number.isFinite(value)) return missing
  return String(Object.is(value, -0) ? 0 : value)
}
