const priceFormatter = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  useGrouping: false,
})

export function formatPrice(value: number | null): string {
  return value === null ? '—' : priceFormatter.format(value)
}
