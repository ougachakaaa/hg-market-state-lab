// Presentation acceptance only. Reuses authenticated real HTTP harness and its
// producer report; explicit GET fault/lifecycle fixtures never imply live readiness.
import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

export async function polishAcceptance(page, context, output, sourceId) {
  const base = 'http://127.0.0.1:5173'
  const api = '/api/research/futures-basis/runs'
  const sourceRun = await (await context.request.get(`${base}${api}/${sourceId}`)).json()
  const sourceReport = await (await context.request.get(`${base}${api}/${sourceId}/report`)).json()
  assert.equal(sourceRun.status, 'COMPLETED')
  const checks = []
  for (const viewport of [{ width: 1440, height: 900 }, { width: 1024, height: 768 }]) {
    const directory = resolve(output, 'wp3b', `${viewport.width}x${viewport.height}`)
    await mkdir(directory, { recursive: true })
    await page.setViewportSize(viewport)
    const shot = async (name, fullPage = false) => page.screenshot({ path: resolve(directory, `${name}.png`), fullPage, animations: 'disabled' })
    let posts = 0
    let reads = 0
    const countPost = request => { if (request.method() === 'GET' && request.url().includes(api)) reads++; if (request.method() === 'POST' && request.url().endsWith(api)) posts++ }
    page.on('request', countPost)
    await page.goto(`${base}/research/futures-basis`)
    await page.getByRole('button', { name: /生成研究/ }).waitFor()
    assert.equal(await page.getByRole('button', { name: /生成研究/ }).isEnabled(), false)
    await shot('initial-query')
    await page.getByRole('combobox', { name: '品种', exact: true }).click()
    await page.getByTitle('IM', { exact: true }).click()
    for (const [label, value] of [['开始日期', '2024-10-18'], ['结束日期', '2024-10-21']]) {
      await page.getByRole('textbox', { name: label, exact: true }).fill(value)
      await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
    }
    assert.equal(posts, 0)
    // Deliver a genuine POST, hold its genuine 202 for a deterministic submitting
    // screenshot, then use only explicit GET fixtures for visual state coverage.
    let accepted
    let release
    const held = new Promise(done => { release = done })
    let delivered
    const delivery = new Promise(done => { delivered = done })
    await page.route(`**${api}`, async route => {
      const response = await route.fetch()
      assert.equal(response.status(), 202)
      accepted = await response.json()
      delivered()
      await held
      await route.fulfill({ response })
    })
    let fixtureRun
    let reportFault = false
    let statusFault = false
    let reportPayload
    const statusRoute = `**${api}/*`
    const reportRoute = `**${api}/*/report`
    await page.route(statusRoute, async route => {
      if (statusFault) return route.fulfill({ status: 503, json: { error: { kind: 'unavailable', detail: 'Synthetic status-read outage', param: null } } })
      await route.fulfill({ json: fixtureRun })
    })
    await page.route(reportRoute, async route => {
      if (reportFault) return route.fulfill({ status: 503, json: { error: { kind: 'read_busy', detail: 'Synthetic reader capacity fixture', param: null } } })
      await route.fulfill({ json: reportPayload })
    })
    await page.getByRole('button', { name: /生成研究/ }).click()
    await delivery
    await page.getByText('正在提交 · SUBMITTING', { exact: true }).waitFor()
    assert.equal(await page.getByRole('button', { name: /生成研究/ }).isEnabled(), false)
    await shot('submitting')
    fixtureRun = { ...sourceRun, ...accepted, started_at: null, finished_at: null, result_available: false, result_status: null, failure: null }
    reportPayload = { ...sourceReport, run_id: accepted.run_id }
    release()
    await page.getByText('已接受，等待执行', { exact: true }).waitFor()
    await shot('pending')
    fixtureRun = { ...fixtureRun, status: 'RUNNING', started_at: sourceRun.started_at }
    await page.getByText('正在执行', { exact: true }).waitFor()
    await shot('running')
    fixtureRun = { ...sourceRun, run_id: accepted.run_id }
    await page.locator('#section-5').waitFor()
    await page.locator('#section-1 .nsewdrag').first().waitFor()
    await page.evaluate(() => window.scrollTo(0, 0))
    await shot('completed')
    await shot('full-report', true)
    assert.equal(await page.getByRole('heading', { level: 1 }).count(), 0)
    assert.equal(await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).count(), 1)
    const readsBeforeNavigation = reads
    for (let i = 0; i < 6; i++) {
      await page.getByRole('navigation', { name: '报告章节' }).getByRole('link').nth(i).click()
      assert.equal(await page.locator(`#section-${i}`).count(), 1)
    }
    await page.locator('#section-5').getByText('Producer Report Request', { exact: true }).click()
    await page.locator('#section-5 code').waitFor()
    await page.locator('#section-5 code').scrollIntoViewIfNeeded()
    await shot('expanded-evidence')
    assert.equal(reads, readsBeforeNavigation, 'Section navigation never reloads the Run')
    const before = posts
    const readsBeforeControls = reads
    await page.getByRole('combobox', { name: 'Distribution metric', exact: true }).click()
    await page.getByTitle('basis_ratio', { exact: true }).click()
    await page.getByRole('combobox', { name: 'Distribution slot', exact: true }).click()
    await page.getByTitle('Q1', { exact: true }).click()
    await page.locator('#section-2').scrollIntoViewIfNeeded()
    await shot('distribution-table')
    assert.equal(posts, before)
    assert.equal(reads, readsBeforeControls, 'Metric/Slot selection never fetches source data')
    await page.locator('#section-3 .ant-table-row-expand-icon').first().click()
    await page.locator('#section-3').scrollIntoViewIfNeeded()
    await shot('comparison-details')
    await page.locator('#section-1 .js-plotly-plot').first().scrollIntoViewIfNeeded()
    await shot('history-chart')
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'No page-level horizontal overflow')
    const navigate = async () => {
      await page.goto(`${base}/research/futures-basis?run_id=${accepted.run_id}`)
      await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
    }
    // Synthetic completed partial with original failed-method evidence. All other
    // producer values stay byte-for-byte equal to the real synthetic report.
    fixtureRun = { ...fixtureRun, result_status: 'partial' }
    reportPayload = structuredClone(reportPayload)
    reportPayload.result_status = reportPayload.data.status = 'partial'
    const method = reportPayload.data.distributions[0].methods[0]
    method.failure_category = 'CalculationFailure'; method.reason = 'Synthetic producer method failure'; method.result = null
    await navigate()
    await page.getByText(/Partial：研究执行已完成/).waitFor()
    await shot('partial')
    assert.ok(await page.getByText('Synthetic producer method failure').count() > 0)
    for (const status of ['FAILED', 'INTERRUPTED']) {
      fixtureRun = { ...fixtureRun, status, result_available: false, result_status: null, failure: { stage: 'execution', category: status === 'FAILED' ? 'internal_failure' : 'interrupted', dependency: null, reason: 'Synthetic safe execution failure' } }
      await navigate()
      await page.getByRole('button', { name: '使用原请求创建新 Run', exact: true }).waitFor()
      assert.equal(await page.getByRole('button', { name: '重新读取报告', exact: true }).count(), 0)
      await shot(status.toLowerCase())
    }
    statusFault = true
    await navigate()
    await page.getByRole('button', { name: '重新读取状态', exact: true }).waitFor()
    await shot('status-error')
    fixtureRun = { ...sourceRun, run_id: accepted.run_id }
    reportPayload = { ...sourceReport, run_id: accepted.run_id }
    statusFault = false; reportFault = true
    await page.getByRole('button', { name: '重新读取状态', exact: true }).click()
    await page.getByRole('button', { name: '重新读取报告', exact: true }).waitFor()
    await shot('report-error')
    reportFault = false
    await page.getByRole('button', { name: '重新读取报告', exact: true }).click()
    await page.locator('#section-5').waitFor()
    assert.equal(posts, 1, 'Manual GET retries and report controls never POST')
    assert.deepEqual(reportPayload.data, sourceReport.data, 'Original producer numerical content retained')
    await page.unroute(`**${api}`)
    await page.unroute(statusRoute)
    await page.unroute(reportRoute)
    page.off('request', countPost)
    // Actual worker must finish before another actual POST is attempted.
    for (let n = 0; n < 60; n++) {
      const actual = await (await context.request.get(`${base}${api}/${accepted.run_id}`)).json()
      if (actual.status === 'COMPLETED') break
      assert.ok(n < 59)
      await page.waitForTimeout(250)
    }
    checks.push({ viewport, status: 'PASS', directory, fixtures: 'real POST and producer payload; explicit synthetic GET lifecycle/fault fixtures' })
  }
  await writeFile(resolve(output, 'wp3b', 'acceptance.json'), JSON.stringify(checks, null, 2))
  console.log('PASS: WP3-B two-viewports query, submitting, pending/running, complete/partial, failed/interrupted, read errors, report controls, charts/tables and expanded evidence')
}
