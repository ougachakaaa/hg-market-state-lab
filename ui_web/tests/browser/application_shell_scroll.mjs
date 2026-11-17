// Targeted shared-Shell acceptance; no backend or Demo Bundle required.
import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import react from '@vitejs/plugin-react'
import { chromium } from 'playwright'

const server = await createServer({ configFile: false,
  root: fileURLToPath(new URL('../static/scroll', import.meta.url)),
  cacheDir: fileURLToPath(new URL('../../.build/cache/scroll', import.meta.url)),
  plugins: [react()], server: { host: '127.0.0.1', port: 0,
    fs: { allow: [fileURLToPath(new URL('../..', import.meta.url))] } },
})
let browser
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  await server.listen()
  const base = `http://127.0.0.1:${server.httpServer.address().port}`
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  for (const mode of ['production', 'static']) for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 720 })
    await page.goto(`${base}/?mode=${mode}#/research`)
    const content = page.locator('.ant-layout-content')
    const sider = page.locator('.ant-layout-sider')
    const header = page.locator('.ant-layout-header')
    await content.waitFor()
    await page.getByRole('button', { name: width === 390 ? '展开导航' : '折叠导航' }).waitFor()
    await page.waitForTimeout(400) // Wait for the existing Sider breakpoint transition.
    const before = [await sider.boundingBox(), await header.boundingBox()]
    await content.hover()
    await page.mouse.wheel(0, 600)
    await page.waitForFunction(() => document.querySelector('.ant-layout-content').scrollTop > 100)
    assert.deepEqual([await sider.boundingBox(), await header.boundingBox()], before)
    const documentState = () => page.evaluate(() => ({ top: document.scrollingElement.scrollTop,
      excess: document.scrollingElement.scrollHeight - innerHeight,
      horizontal: document.scrollingElement.scrollWidth - innerWidth }))
    assert.deepEqual(await documentState(), { top: 0, excess: 0, horizontal: 0 })
    await content.evaluate(el => { el.scrollTop = 0 })
    const hash = await page.evaluate(() => location.hash)
    await page.getByRole('button', { name: '章节跳转' }).click()
    assert.equal(await page.evaluate(() => location.hash), hash)
    await page.waitForTimeout(300)
    const target = await page.locator('#chapter').boundingBox()
    const bounds = await content.boundingBox()
    assert.ok(target.y >= bounds.y - 1 && target.y + target.height <= bounds.y + bounds.height)
    assert.equal((await documentState()).top, 0)
    await content.evaluate(el => { el.scrollTop = 0 })
    assert.ok(await page.getByTestId('horizontal').evaluate(el => { el.scrollLeft = 200; return el.scrollLeft > 0 }))
    if (width === 1440) await page.getByRole('button', { name: '折叠导航' }).click()
    await page.getByRole('menuitem', { name: '回测', exact: true }).click()
    await page.getByRole('link', { name: '回测总览', exact: true }).last().click()
    await page.waitForFunction(() => document.querySelector('h1').textContent === '/backtesting')
    assert.ok((await page.evaluate(() => location.href)).includes(mode === 'static' ? '#/backtesting' : '/backtesting'))
    await page.getByRole('button', { name: '展开导航' }).click()
    await page.getByRole('button', { name: '折叠导航' }).waitFor()
    await page.setViewportSize({ width, height: 300 })
    const navigation = page.getByRole('menu', { name: '业务导航' }).locator('..')
    // Open each group so short viewports actually overflow the navigation.
    for (const name of ['日常数据', '研究']) await page.getByRole('menuitem', { name, exact: true }).click()
    await page.waitForTimeout(400)
    assert.ok(await navigation.evaluate(el => { el.scrollTop = 200; return el.scrollTop > 0 }))
    assert.equal((await sider.boundingBox()).y, 0)
    console.log(`PASS ${mode} ${width}: content/document ownership, fixed chrome, chapter, horizontal scroll, popup/collapse/navigation and short menu`)
  }
  assert.deepEqual(errors, [])
} finally {
  await browser?.close()
  await server.close()
}
