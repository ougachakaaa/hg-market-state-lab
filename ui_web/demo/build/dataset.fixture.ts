import dailyCapture from '../bundles/calendar_spread_daily.json'
import historicalCapture from '../bundles/calendar_spread_relative_value.json'
import { mkdtemp, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createHash } from 'node:crypto'
import { canonicalBytes } from './json'
import { registry } from './registry'
import presets from './presets.json'
import { chain } from '../../src/features/mo_option_chain/testing/chainFixture'
import { plane } from '../../src/features/mo_option_premium/testing/planeFixture'
import { readerFixture } from '../../src/features/futures_basis_research/report/reader.fixture'
import backtest from '../../src/features/backtesting/api/result.fixture.json'
import { embeddedCatalog } from '../../src/features/research_catalog/testing/catalogFixture'
import { embeddedPublicationSet } from '../../src/features/research_explorer/testing/publicationFixture'
export async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'ddb02-test-only-'))
  const data = new Map<string, any>()
  for (const entry of registry) {
    let request: Record<string, unknown> = structuredClone(presets[entry.preset_id].request)
    let result: unknown
    switch (entry.bundle_id) {
      case 'calendar_spread_daily': result = structuredClone(dailyCapture.result); break
      case 'calendar_spread_relative_value': result = structuredClone(historicalCapture.result); break
      case 'chain': result = { ...structuredClone(chain), ...request }; break
      case 'premium': result = { ...structuredClone(plane), observation: { kind: 'trade_date', value: request.as_of } }; break
      case 'basis': {
        request = { ...request, case: 'futures_basis_v1', analysis_profile: 'r01a_standard_v1' }
        const report = readerFixture()
        report.request.observation = { ...report.request.observation, ...presets.basis.request }
        result = report
        break
      }
      case 'catalog': result = structuredClone(embeddedCatalog); break
      case 'publications': result = structuredClone(embeddedPublicationSet); break
      default: {
        request = { ...request, case: 'futures_roll_long_v1' }
        result = { ...structuredClone(backtest), request }
      }
    }
    data.set(entry.bundle_id, { bundle_format: 'demo_bundle_v1', bundle_id: entry.bundle_id,
      preset_id: entry.preset_id, result_contract: entry.result_contract,
      source: { kind: 'formal_http', description: 'TEST ONLY simulated HTTP payload; no capture or distribution evidence' }, request, result })
  }
  async function save() {
    const bundles = []
    for (const entry of registry) {
      const bytes = canonicalBytes(data.get(entry.bundle_id))
      await writeFile(join(root, entry.path), bytes)
      bundles.push({ bundle_id: entry.bundle_id, path: entry.path, sha256: createHash('sha256').update(bytes).digest('hex') })
    }
    await writeFile(join(root, 'manifest.json'), canonicalBytes({ manifest_format: 'demo_manifest_v1', bundles }))
  }
  await save()
  return { root, data, save }
}
