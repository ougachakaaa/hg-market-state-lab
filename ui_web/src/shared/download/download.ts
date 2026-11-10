export function safeDownloadFilename(filename: string): string {
  // Control characters are invalid filename content.
  // oxlint-disable-next-line no-control-regex
  return filename.replace(/[<>:"/\\|?*\u0000-\u001f\u007f]/g, '_').replace(/[. ]+$/g, '_')
}

export function downloadText(text: string, filename: string, mimeType: string): void {
  const blob = new Blob([text], { type: mimeType })
  let url: string | undefined
  let anchor: HTMLAnchorElement | undefined
  const cleanup = () => {
    try { anchor?.remove() } finally { if (url !== undefined) URL.revokeObjectURL(url) }
  }
  try {
    url = URL.createObjectURL(blob)
    anchor = document.createElement('a')
    anchor.href = url
    anchor.download = safeDownloadFilename(filename)
    anchor.hidden = true
    document.body.appendChild(anchor)
    anchor.click()
    setTimeout(cleanup, 0)
  } catch (error) {
    cleanup()
    throw error
  }
}
