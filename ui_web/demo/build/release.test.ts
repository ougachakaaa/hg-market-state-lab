import { test, expect } from 'vitest'
import { mkdtemp, cp, readFile, writeFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { validateRelease } from '../release/validate'
const web = process.cwd()
test('current real dataset meets independent requirements', async () => {
  await validateRelease(web)
})
test.each(['date', 'product', 'strategy', 'coverage', 'schema', 'hash', 'visualization', 'identity'])(
  'rejects %s mismatch without altering active data', async kind => {
    const root = await mkdtemp(resolve(tmpdir(), 'demo-release-test-'))
    try {
      const directory = resolve(root, 'bundles'), requirements = resolve(root, 'requirements.json')
      await cp(resolve(web, 'demo/bundles'), directory, { recursive: true })
      const rules = JSON.parse(await readFile(resolve(web, 'demo/release/requirements.json'), 'utf8'))
      if (kind === 'date') rules.bundles.chain.request.target_trade_date = '2026-09-29'
      if (kind === 'product') rules.bundles.basis.request.product_code = 'IC'
      if (kind === 'strategy') rules.bundles.expiry_to_Q1_v1.request.strategy_profile = 'expiry_to_M1_v1'
      if (kind === 'coverage') rules.bundles.basis.coverage.first = '2026-03-03'
      if (kind === 'schema') rules.extra = true
      if (['hash', 'visualization', 'identity'].includes(kind)) {
        const path = resolve(directory, 'basis.json')
        const b = JSON.parse(await readFile(path, 'utf8'))
        if (kind === 'visualization') b.result.views = { history: {}, histograms: {} }
        else b.request.product_code = 'IC'
        // Canonical keys already ordered; preserve DDB serialization for mutation.
        const bytes = JSON.stringify(b, null, 2) + '\n'
        await writeFile(path, bytes)
        if (kind !== 'hash') {
          const { createHash } = await import('node:crypto')
          const manifestPath = resolve(directory, 'manifest.json')
          const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
          manifest.bundles.find((entry: {bundle_id: string}) => entry.bundle_id === 'basis').sha256 = createHash('sha256').update(bytes).digest('hex')
          await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n')
        }
      }
      await writeFile(requirements, JSON.stringify(rules))
      await expect(validateRelease(web, directory, requirements)).rejects.toThrow()
    } finally { await rm(root, { recursive: true, force: true }) }
  }, 30000)

test('rejects a formally legal empty Daily capture as unsuitable release content', async () => {
  const root = await mkdtemp(resolve(tmpdir(), 'wp7-empty-release-'))
  try {
    const directory = resolve(root, 'bundles')
    await cp(resolve(web, 'demo/bundles'), directory, { recursive: true })
    const path = resolve(directory, 'calendar_spread_daily.json')
    const bundle = JSON.parse(await readFile(path, 'utf8'))
    bundle.result.day.observations = bundle.result.day.observations.map((row: any) => ({ ...row, near: null, far: null, delta_days: null, near_dte_days: null, expiry_stage: null, metrics: null, outcome: 'not_applicable', reason: 'no_active_contract' }))
    bundle.result.accounting = { candidate_count: 6, valid_count: 0, not_applicable_count: 6, excluded_count: 0 }
    const { canonicalBytes } = await import('./json')
    const { createHash } = await import('node:crypto')
    const bytes = canonicalBytes(bundle)
    await writeFile(path, bytes)
    const manifestPath = resolve(directory, 'manifest.json')
    const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
    manifest.bundles.find((row: any) => row.bundle_id === bundle.bundle_id).sha256 = createHash('sha256').update(bytes).digest('hex')
    await writeFile(manifestPath, canonicalBytes(manifest))
    const { validateDirectory } = await import('./validate')
    await expect(validateDirectory(directory)).resolves.toBeUndefined()
    await expect(validateRelease(web, directory)).rejects.toThrow('six_valid_market_pairs')
  } finally { await rm(root, { recursive: true, force: true }) }
})
