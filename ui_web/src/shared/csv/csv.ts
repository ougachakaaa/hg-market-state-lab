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

export function safeCsvFilename(filename: string): string {
  // Control characters are invalid filename content.
  // oxlint-disable-next-line no-control-regex
  return filename.replace(/[<>:"/\\|?*\u0000-\u001f\u007f]/g, '_').replace(/[. ]+$/g, '_')
}

export function downloadCsv(csv: string, filename: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  let url: string | undefined
  let anchor: HTMLAnchorElement | undefined
  const cleanup = () => {
    try { anchor?.remove() } finally { if (url !== undefined) URL.revokeObjectURL(url) }
  }
  try {
    url = URL.createObjectURL(blob)
    anchor = document.createElement('a')
    anchor.href = url
    anchor.download = safeCsvFilename(filename)
    anchor.hidden = true
    document.body.appendChild(anchor)
    anchor.click()
    setTimeout(cleanup, 0)
  } catch (error) {
    cleanup()
    throw error
  }
}
