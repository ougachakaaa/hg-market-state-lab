import { downloadText, safeDownloadFilename } from '../download/download'

export type CsvCell = string | number | boolean | null

function encodeCell(value: CsvCell): string {
  let text = value === null ? 'null' : String(value)
  // Control characters are deliberately recognized for spreadsheet formula safety.
  // oxlint-disable-next-line no-control-regex
  if (typeof value === 'string' && (/^[=+\-@\t\r\n]/.test(text) || /^[\s\u0000-\u001f\u007f]*[=+\-@]/u.test(text))) {
    text = `'${text}`
  }
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

export function serializeCsv(header: readonly string[], rows: readonly (readonly CsvCell[])[]): string {
  return '\uFEFF' + [header, ...rows].map((row) => {
    if (row.length !== header.length) throw new Error('CSV row width mismatch')
    return row.map(encodeCell).join(',') + '\r\n'
  }).join('')
}

export const safeCsvFilename = safeDownloadFilename

export function downloadCsv(csv: string, filename: string): void {
  downloadText(csv, filename, 'text/csv;charset=utf-8')
}
