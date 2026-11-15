import assert from 'node:assert/strict'
export async function verifyDateEvents(page, count) {
 const panels = page.locator('section[aria-label="Date events"]')
 assert.equal(await panels.count(), count)
 for (const panel of await panels.all()) {
  const toggle = panel.getByRole('button', { name: '日期事件（Date Events）', exact: true })
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false')
  const description = panel.locator('.ant-typography')
  assert.equal(await description.isVisible(), false)
  await toggle.click()
  await description.waitFor()
  assert.match(await description.textContent(), /标记/)
  const events = panel.locator('.ant-collapse').nth(1).getByRole('button')
  assert.ok(await events.count() > 0)
  await events.first().click()
  assert.equal(await events.first().getAttribute('aria-expanded'), 'true')
  await toggle.click()
  await description.waitFor({ state: 'hidden' })
 }
}
