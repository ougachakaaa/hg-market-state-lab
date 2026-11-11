// Generic chrome only: analytical marks and semantic status colors are excluded.
import assert from 'node:assert/strict'
import { writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

function channels(color) {
  const values = color.match(/[\d.]+/g)?.map(Number)
  assert.ok(values?.length >= 3, `Expected RGB color: ${color}`)
  return values.slice(0, 3)
}
function neutral(color) {
  const rgb = channels(color)
  assert.ok(Math.max(...rgb) - Math.min(...rgb) <= 1, `Neutral chrome: ${color}`)
}
function contrast(a, b) {
  const luminance = color => channels(color).map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4)
    .reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0)
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (values[0] + .05) / (values[1] + .05)
}
const style = locator => locator.evaluate(el => {
  const s = getComputedStyle(el)
  return { background: s.backgroundColor, color: s.color, border: s.borderTopColor, outline: s.outlineColor, outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth }
})

export async function neutralDarkAcceptance(page, output) {
  const evidence = []
  for (const [width, height] of [[1440, 900], [1024, 768]]) {
    await page.setViewportSize({ width, height })
    await page.goto('http://127.0.0.1:5173/research')
    const open = page.getByRole('button', { name: '打开研究结果浏览', exact: true })
    await open.waitFor()
    const card = page.locator('.ant-card').last()
    const shell = await style(page.locator('.ant-layout-header'))
    const sidebar = await style(page.locator('.ant-layout-sider'))
    const surface = await style(card)
    assert.equal(shell.background, 'rgb(16, 16, 16)')
    assert.equal(sidebar.background, shell.background)
    assert.equal(surface.background, 'rgb(21, 21, 21)')
    assert.ok(contrast(surface.color, surface.background) >= 4.5)
    const primary = await style(open)
    neutral(primary.background)
    assert.ok(contrast(primary.color, primary.background) >= 4.5)
    const navigation = page.getByRole('menu', { name: '业务导航' })
    assert.equal(await navigation.getByRole('img').count(), 0, 'Decorative navigation icons are hidden')
    const icons = navigation.locator('.anticon')
    assert.ok(await icons.count() >= 3)
    assert.ok(await icons.evaluateAll(nodes => nodes.every(n => n.getAttribute('aria-hidden') === 'true')))
    const toggle = page.getByRole('button', { name: width === 1024 ? '展开导航' : '折叠导航', exact: true })
    // Tab away and back to exercise the actual keyboard focus indicator.
    await toggle.focus()
    await page.keyboard.press('Tab')
    await page.keyboard.press('Shift+Tab')
    const focus = await style(toggle)
    assert.notEqual(focus.outlineStyle, 'none')
    assert.ok(parseFloat(focus.outlineWidth) >= 2)
    neutral(focus.outline)
    assert.ok(contrast(focus.outline, shell.background) >= 3)
    await page.screenshot({ animations: 'disabled', path: resolve(output, `neutral-keyboard-focus-${width}.png`) })
    if (width === 1440) await toggle.click()
    await page.getByRole('menuitem', { name: '研究', exact: true }).click()
    const popup = page.locator('.ant-menu-submenu-popup:visible')
    await popup.waitFor()
    await popup.evaluate(el => Promise.all(el.getAnimations({ subtree: true }).map(a => a.finished)))
    await page.getByRole('menuitem', { name: 'Research Explorer', exact: true }).waitFor()
    const selected = await style(page.locator('.ant-menu-item-selected:visible'))
    neutral(selected.background)
    assert.ok(contrast(selected.color, selected.background) >= 4.5)
    assert.equal(await page.locator('.ant-menu-item-selected').count(), 1)
    await page.screenshot({ animations: 'disabled', path: resolve(output, `neutral-collapsed-menu-${width}.png`) })
    await page.goto('http://127.0.0.1:5173/data/mo-premium-plane')
    const date = page.getByRole('textbox', { name: '观察日期', exact: true })
    await date.waitFor()
    const picker = page.locator('.ant-picker').first()
    const control = await style(picker)
    neutral(control.background)
    assert.ok(contrast(control.border, control.background) >= 3, 'Control boundary contrast')
    await date.click()
    const calendar = page.locator('.ant-picker-dropdown:visible')
    await calendar.waitFor()
    await calendar.evaluate(el => Promise.all(el.getAnimations({ subtree: true }).map(a => a.finished)))
    await page.screenshot({ animations: 'disabled', path: resolve(output, `neutral-date-focus-${width}.png`) })
    await page.keyboard.press('Escape')
    await calendar.waitFor({ state: 'hidden' })
    await page.getByRole('combobox', { name: '价格口径', exact: true }).click()
    const dropdown = page.locator('.ant-select-dropdown:visible')
    await dropdown.waitFor()
    await dropdown.evaluate(el => Promise.all(el.getAnimations({ subtree: true }).map(a => a.finished)))
    const option = await style(page.locator('.ant-select-item-option-selected').first())
    neutral(option.background)
    assert.ok(contrast(option.color, option.background) >= 4.5)
    await page.screenshot({ animations: 'disabled', path: resolve(output, `neutral-select-${width}.png`) })
    await page.keyboard.press('Escape')
    evidence.push({ width, height, shell, surface, primary, focus, control, option })
  }
  await writeFile(resolve(output, 'neutral-dark-acceptance.json'), JSON.stringify({ status: 'PASS', evidence }, null, 2))
  console.log('PASS: Neutral chrome, primary/control/focus contrast, decorative icons and collapsed menus at both desktop sizes')
}
