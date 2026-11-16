/** Beijing/Shanghai display timezone; never depends on the browser-local timezone. */
export const BEIJING_TIME_ZONE = 'Asia/Shanghai'
export const BEIJING_TIME_SUFFIX = '（北京时间）'

const DATE_TIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/
const formatter = new Intl.DateTimeFormat('en-US', {
  timeZone: BEIJING_TIME_ZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
})

/**
 * Display a date-time instant in Beijing time. Date-only strings are intentionally
 * rejected: trade dates are calendar facts, not instants to shift across timezones.
 */
export function formatBeijingTime(value: string | Date | null | undefined, missing = '—'): string {
  if (value == null) return missing
  if (typeof value === 'string' && !DATE_TIME.test(value)) return missing
  const date = typeof value === 'string' ? new Date(value) : value
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return missing
  const parts: Record<string, string> = {}
  for (const part of formatter.formatToParts(date)) if (part.type !== 'literal') parts[part.type] = part.value
  const { year, month, day, hour, minute, second } = parts
  if (!year || !month || !day || !hour || !minute || !second) return missing
  return `${year}-${month}-${day} ${hour}:${minute}:${second}${BEIJING_TIME_SUFFIX}`
}
