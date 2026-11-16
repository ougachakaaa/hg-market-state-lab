import { formatDecimal } from '../../../shared/format/number'

export function formatPrice(value: number | null): string {
  return formatDecimal(value, '—')
}
