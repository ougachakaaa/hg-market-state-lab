import assert from 'node:assert/strict'
import { readFileSync, writeFileSync } from 'node:fs'
import { chromium } from 'playwright'
import { sha } from './public_release.mjs'
const base = process.argv[2]
const receipt = JSON.parse(readFileSync(new URL('../src/demo/futures_basis/rollback-inventory.json',import.meta.url)))
const browser = await chromium.launch({ headless: true })
const evidence = { status:'RUNNING', url:base, recoveryDigest:receipt.archiveDigest, errors:[] }
try {
  const context = await browser.newContext()
  let failure
  for(let attempt=0;attempt<12;attempt++) {
    try {
      for(const f of receipt.files) {
        const response = await context.request.get(new URL(f.file,base).href)
        assert.equal(response.status(),200)
        assert.equal(sha(await response.body()),f.sha256)
      }
      failure=null;break
    } catch(error) { failure=error;if(attempt<11)await new Promise(done=>setTimeout(done,5000)) }
  }
  if(failure)throw failure
  await context.route('**/*',async route=>{
    const request=route.request(),url=new URL(request.url())
    if(url.origin!==new URL(base).origin||!url.pathname.startsWith('/hg-market-state-lab/')||request.method()!=='GET'||['xhr','fetch','websocket'].includes(request.resourceType())) { evidence.errors.push(url.pathname);await route.abort() }
    else await route.continue()
  })
  const page=await context.newPage()
  page.on('pageerror',e=>evidence.errors.push(String(e)))
  page.on('console',m=>{if(m.type()==='error')evidence.errors.push(m.text())})
  await page.goto(base)
  const disclosure = page.getByRole('link', { name: '查看合成演示数据声明' })
  await disclosure.waitFor()
  assert.match(await disclosure.textContent(), /Synthetic Demo/)
  await page.locator('#section-1 .js-plotly-plot').first().waitFor()
  for(let i=0;i<6;i++)assert.equal(await page.locator(`#section-${i}`).count(),1)
  assert.deepEqual(evidence.errors,[])
  assert.deepEqual(await context.cookies(),[])
  evidence.status='PASS'
} catch(error) { evidence.status='FAIL';evidence.failure=String(error);throw error }
finally { writeFileSync('v1-recovery-online.json',JSON.stringify(evidence,null,2)+'\n');await browser.close() }
