import { spawnSync } from 'node:child_process'
import { preview } from 'vite'
import { chromium } from 'playwright'
import { verifyBrowser } from './browserAcceptance.mjs'
import { verifyOverviewLayout } from '../../tests/browser/research_overview_layout.mjs'
import { web } from './build.mjs'

// Review existing Demo output first, then the shared Presentation in both modes.
await verifyBrowser(undefined, { reviewOverview: true })
const built = spawnSync('npm', ['run', 'test:catalog-static'], {
  cwd: web, stdio: 'inherit', shell: process.platform === 'win32', windowsHide: true,
})
if (built.status !== 0) throw new Error('Catalog Presentation harness build failed')
const server = await preview({ configFile: false, root: web, envDir: false, publicDir: false,
  base: '/hg-market-state-lab/', build: { outDir: '.build/tests/catalog' },
  preview: { host: '127.0.0.1', port: 0, strictPort: true } })
let browser
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const base = `http://127.0.0.1:${server.httpServer.address().port}/hg-market-state-lab/`
  await verifyOverviewLayout(browser, base + '?mode=production#/research', { mode: 'production', label: 'production' })
  for (const [label, disclosure] of [['chinese', '中文披露'.repeat(180)], ['english', 'LongUnbrokenEnglishDisclosure'.repeat(100)]]) {
    await verifyOverviewLayout(browser, base + '?disclosure=' + encodeURIComponent(disclosure) + '#/research', { disclosure, label })
  }
} finally {
  await browser?.close()
  await new Promise(done => server.httpServer.close(done))
}
