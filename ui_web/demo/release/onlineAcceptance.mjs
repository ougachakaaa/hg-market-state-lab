import assert from 'node:assert/strict'
export async function verifyPublicFiles(receipt, read) {
  for (const item of receipt.files) {
    console.log(`Checking public bytes: ${item.file}`)
    const actual = await read(item.file)
    assert.equal(actual.size, item.size, `Public size mismatch: ${item.file}`)
    assert.equal(actual.sha256, item.sha256, `Public hash mismatch: ${item.file}`)
  }
}
export async function verifyOnline(base, receipt) {
  const url = new URL(base)
  assert.equal(url.protocol, 'https:')
  const { chromium } = await import('playwright')
  const browser = await chromium.launch({ headless: true })
  try {
    const page = await browser.newPage()
    const response = await page.goto(url.href)
    assert.ok(response?.ok(), 'Public homepage unavailable')
    await verifyPublicFiles(receipt, file => page.evaluate(async href => {
      const response = await fetch(href, { cache: 'no-store', signal: AbortSignal.timeout(30000) })
      if (!response.ok) throw new Error('Public file unavailable')
      const bytes = await response.arrayBuffer()
      const digest = await crypto.subtle.digest('SHA-256', bytes)
      return { size: bytes.byteLength, sha256: Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('') }
    }, new URL(file, url).href))
  } finally { await browser.close() }
}
