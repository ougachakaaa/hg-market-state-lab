import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// Development-only TypeScript execution. No HTTP listener or asset packaging.
const root = fileURLToPath(new URL('..', import.meta.url))
const packageRoot = resolve(process.argv[2])
const server = await createServer({ root, logLevel: 'silent', configFile: false, server: { middlewareMode: true }, appType: 'custom' })
try {
  const { validateOptionChain } = await server.ssrLoadModule('/src/features/mo_option_chain/api/validateOptionChain.ts')
  const { validatePremiumPlane } = await server.ssrLoadModule('/src/features/mo_option_premium/api/validatePremiumPlane.ts')
  const chainPayload = JSON.parse(readFileSync(resolve(packageRoot, 'chain/response.json'), 'utf8'))
  const premiumPayload = JSON.parse(readFileSync(resolve(packageRoot, 'premium/response.json'), 'utf8'))
  const chain = validateOptionChain(chainPayload)
  const premium = validatePremiumPlane(premiumPayload)
  assert.equal(chain, chainPayload)
  assert.equal(premium.rawPayload, premiumPayload)
  assert.equal(premium.plane, premiumPayload)
  assert.equal(chain.target_trade_date, '2026-11-11')
  assert.deepEqual(premium.plane.observation, { kind: 'trade_date', value: '2026-11-11' })
  for (const body of [chain, premium.plane]) {
    assert.equal(body.option_product, 'MO')
    assert.equal(body.price_type, 'close')
    assert.equal(body.underlying.instrument_id, '000852.SH')
  }
  // Prove the production validator still rejects a structurally valid empty Plane.
  assert.throws(() => validatePremiumPlane({ ...premiumPayload, points: [] }))
  console.log(JSON.stringify({ chain: 'PASS', premium: 'PASS', raw_preservation: 'PASS', nonempty_points: 'PASS' }))
} finally {
  await server.close()
}
