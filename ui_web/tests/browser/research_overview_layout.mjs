import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

// Shared by the real Demo artifact and the Production-mode Presentation harness.
export async function verifyOverviewLayout(browser, url, { mode = 'static', disclosure, label = 'demo' } = {}) {
  const output = resolve('.build/demo-review')
  await mkdir(output, { recursive: true })
  let originalText
  for (const width of [1280, 1024, 768]) {
    const page = await browser.newPage({ viewport: { width, height: 1000 } })
    try {
      await page.goto(url)
      await page.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
      await page.evaluate(async () => {
        await document.fonts.ready
        await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))
      })
      const note = page.getByRole('note')
      const text = await note.textContent()
      originalText ??= text
      assert.equal(text, originalText, 'Disclosure must remain complete across widths')
      assert.ok(text.includes('完成状态仅表示独立 Web 页面已开放；不代表数据源就绪、计算成功或研究方法开发完毕。研究内容仅供研究参考。'))
      assert.equal(await note.locator(':scope > *').count(), mode === 'static' ? 2 : 1)
      if (disclosure) assert.equal(await note.locator(':scope > *').last().textContent(), disclosure)
      const metrics = await note.evaluate(note => {
        const root = note.parentElement
        const elements = [note, ...note.children, root, root.parentElement, document.documentElement]
        return elements.map(element => {
          const style = getComputedStyle(element)
          return { tag: element.tagName, client: element.clientWidth, scroll: element.scrollWidth,
            height: element.clientHeight, scrollHeight: element.scrollHeight,
            overflowX: style.overflowX, overflowY: style.overflowY, textOverflow: style.textOverflow }
        })
      })
      for (const metric of metrics) {
        assert.ok(metric.scroll <= metric.client + 1, `${label} ${width}: ${JSON.stringify(metric)}`)
        assert.ok(!['hidden', 'clip'].includes(metric.overflowX), 'Do not mask overflow')
        assert.notEqual(metric.textOverflow, 'ellipsis')
      }
      for (const metric of metrics.slice(0, mode === 'static' ? 3 : 2)) {
        assert.ok(metric.scrollHeight <= metric.height + 1, 'Disclosure height must grow without clipping')
      }
      // Inner gutter and outer card alignment must survive the containment fix.
      const cards = await page.locator('.ant-card').evaluateAll(cards => cards.map(card => {
        const { left, right, top } = card.getBoundingClientRect()
        return { left, right, top }
      }))
      assert.equal(cards.length, 4)
      assert.ok(Math.abs(cards[0].top - cards[1].top) <= 1)
      assert.ok(Math.abs(cards[1].left - cards[0].right - 24) <= 1)
      const bounds = await note.boundingBox()
      assert.ok(Math.abs(cards[0].left - bounds.x) <= 1)
      assert.ok(Math.abs(cards[1].right - bounds.x - bounds.width) <= 1)
      await page.screenshot({ path: resolve(output, `${label}-${width}.png`), fullPage: true })
      console.log(`PASS ${label} overview ${width}px: full disclosure, natural height, no horizontal overflow`)
    } finally { await page.close() }
  }
}
