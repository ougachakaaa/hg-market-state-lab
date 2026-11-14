import { afterEach, describe, expect, it } from 'vitest'
import { mkdtemp, readFile, writeFile, rm, symlink, rename, mkdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { canonicalBytes, parseStrict } from './json'
import { registry } from './registry'
import presets from './presets.json'
import { validateDirectory } from './validate'
import { chain } from '../../src/features/mo_option_chain/testing/chainFixture'
import { plane } from '../../src/features/mo_option_premium/testing/planeFixture'
import { readerFixture } from '../../src/features/futures_basis_research/report/reader.fixture'
import backtest from '../../src/features/backtesting/api/result.fixture.json'
import { embeddedCatalog } from '../../src/features/research_catalog/testing/catalogFixture'
import { embeddedPublicationSet } from '../../src/features/research_explorer/testing/publicationFixture'

// Test-only assemblies written exclusively to temporary directories. No market capture.
const roots: string[] = []
afterEach(async () => { for (const root of roots.splice(0)) await rm(root, { recursive: true, force: true }) })
async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'ddb02-test-only-'))
  roots.push(root)
  const data = new Map<string, any>()
  for (const entry of registry) {
    let request: Record<string, unknown> = structuredClone(presets[entry.preset_id].request)
    let result: unknown
    switch (entry.bundle_id) {
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
async function changeManifest(root: string, change: (value: any) => void) {
  const path = join(root, 'manifest.json')
  const manifest = JSON.parse(await readFile(path, 'utf8'))
  change(manifest)
  await writeFile(path, canonicalBytes(manifest))
}
async function rawBundle(root: string, id: string, bytes: Buffer) {
  await writeFile(join(root, `${id}.json`), bytes)
  await changeManifest(root, value => { value.bundles.find((item: any) => item.bundle_id === id).sha256 = createHash('sha256').update(bytes).digest('hex') })
}
describe('strict JSON', () => {
  it.each(['{"x":1,"x":2}', '{"x":{"a":1,"\\u0061":2}}', '{"__proto__":1,"__proto__":2}'])('rejects duplicate keys %s', value => {
    expect(() => parseStrict(value)).toThrow('duplicate_key')
  })
  it.each(['9007199254740993', '9007199254740992', '0.10000000000000001', '1e400', '1e-400', '-0', '-0.0'])('rejects numeric loss %s', value => {
    expect(() => parseStrict(value)).toThrow('unsafe_number')
  })
  it.each(['NaN', 'Infinity', '[1,]', '{"a":1,}', '01', 'true false', '"\n"'])('rejects malformed JSON %s', value => {
    expect(() => parseStrict(value)).toThrow()
  })
  it('preserves decimals, strings, null, arrays and integer-like key ordering', () => {
    const value = parseStrict('{"2":0.1,"10":1e-7,"x":[null,0,"9007199254740993"],"__proto__":true}')
    const bytes = canonicalBytes(value)
    expect(bytes.toString().indexOf('"10"')).toBeLessThan(bytes.toString().indexOf('"2"'))
    expect(parseStrict(bytes.toString())).toEqual(value)
    expect(parseStrict('9007199254740991')).toBe(Number.MAX_SAFE_INTEGER)
  })
})
describe('seven Bundle admission', () => {
  it('admits complete formal Result fixtures offline', async () => {
    await expect(validateDirectory((await fixture()).root)).resolves.toBeUndefined()
  })
  it.each(registry.map(entry => entry.bundle_id))('rejects missing required Bundle %s', async id => {
    const { root } = await fixture()
    await rm(join(root, `${id}.json`))
    await expect(validateDirectory(root)).rejects.toThrow(`FAIL ${id} file missing_file`)
  })
  it.each([
    ['duplicate ID', (m: any) => { m.bundles[1].bundle_id = m.bundles[0].bundle_id }],
    ['duplicate path', (m: any) => { m.bundles[1].path = m.bundles[0].path }],
    ['unknown ID', (m: any) => { m.bundles[0].bundle_id = 'unknown' }],
    ['missing entry', (m: any) => { m.bundles.pop() }],
    ['wrong path', (m: any) => { m.bundles[0].path = 'other.json' }],
    ['traversal', (m: any) => { m.bundles[0].path = '../basis.json' }],
    ['absolute', (m: any) => { m.bundles[0].path = 'C:/basis.json' }],
    ['POSIX absolute', (m: any) => { m.bundles[0].path = '/basis.json' }],
    ['separator', (m: any) => { m.bundles[0].path = 'sub\\basis.json' }],
    ['invalid hash', (m: any) => { m.bundles[0].sha256 = 'abc' }],
    ['extra field', (m: any) => { m.secret = 'test secret' }],
    ['format', (m: any) => { m.manifest_format = 'v0' }],
    ['order', (m: any) => { m.bundles.reverse() }],
  ] as const)('rejects manifest %s', async (name, change) => {
    const { root } = await fixture()
    await changeManifest(root, change)
    await expect(validateDirectory(root)).rejects.toThrow(name === 'missing entry'
      ? 'FAIL publications manifest missing_bundle' : 'FAIL dataset manifest')
  })
  it('rejects missing Manifest', async () => {
    const { root } = await fixture()
    await rm(join(root, 'manifest.json'))
    await expect(validateDirectory(root)).rejects.toThrow('FAIL dataset manifest')
  })
  it('rejects extra files', async () => {
    const { root } = await fixture()
    await writeFile(join(root, 'extra.json'), '{}')
    await expect(validateDirectory(root)).rejects.toThrow('unexpected_files')
  })
  it('hashes original bytes', async () => {
    const { root } = await fixture()
    const path = join(root, 'chain.json')
    await writeFile(path, (await readFile(path, 'utf8')) + '\n')
    await expect(validateDirectory(root)).rejects.toThrow('FAIL chain hash invalid_hash')
  })
  it.each([
    ['missing field', (e: any) => { delete e.source }], ['extra field', (e: any) => { e.extra = true }],
    ['format', (e: any) => { e.bundle_format = 'v0' }], ['ID', (e: any) => { e.bundle_id = 'premium' }],
    ['preset', (e: any) => { e.preset_id = 'premium' }], ['contract', (e: any) => { e.result_contract = 'other' }],
    ['source', (e: any) => { e.source.kind = 'synthetic' }],
  ] as const)('rejects envelope %s', async (_name, change) => {
    const { root, data, save } = await fixture()
    change(data.get('chain')); await save()
    await expect(validateDirectory(root)).rejects.toThrow('FAIL chain envelope')
  })
  it.each([
    ['chain', (e: any) => { e.request.target_trade_date = '2026-11-10' }],
    ['chain', (e: any) => { e.result.target_trade_date = '2026-11-10' }],
    ['chain', (e: any) => { delete e.result.expiries }],
    ['premium', (e: any) => { e.result.observation.value = '2026-11-10' }],
    ['premium', (e: any) => { e.result.points = [] }],
    ['basis', (e: any) => { e.result.request.observation.product_code = 'IF' }],
    ['basis', (e: any) => { e.result.profile = 'unsupported' }],
    ['basis', (e: any) => { e.result.views.history.basis_value.version = 99 }],
    ['expiry_to_M1_v1', (e: any) => { e.result.profile = 'unsupported' }],
    ['expiry_to_Q1_v1', (e: any) => { e.request.strategy_profile = 'expiry_to_M1_v1' }],
    ['expiry_to_Q1_v1', (e: any) => { e.result.request = { ...e.result.request, end_date: '2026-11-10' } }],
    ['expiry_to_M1_v1', (e: any) => { e.result.views.returns.version = 99 }],
    ['catalog', (e: any) => { e.result.details = [] }],
    ['catalog', (e: any) => { e.result.details[0] = { ...e.result.details[0], title: 'different' } }],
    ['publications', (e: any) => { e.result.manifests = [] }],
    ['publications', (e: any) => { e.result.analyses.pop() }],
    ['publications', (e: any) => { e.result.views.pop() }],
    ['publications', (e: any) => { e.result.pages[0].next_cursor = 'opaque-unfinished' }],
  ] as const)('rejects %s business mutation %# after recomputing Hash', async (id, change) => {
    const { root, data, save } = await fixture()
    change(data.get(id)); await save()
    await expect(validateDirectory(root)).rejects.toThrow(`FAIL ${id} result`)
  })
  it.each([
    ['duplicate_key', '{"x":1,"x":2}'], ['unsafe_number', '{"nested":{"unknown":0.10000000000000001}}'],
    ['invalid_json', '{'], ['noncanonical_json', '{}'], ['invalid_utf8', '\ufeff{}'],
  ])('rejects raw bytes %s after valid Hash', async (reason, raw) => {
    const { root } = await fixture()
    await rawBundle(root, 'chain', Buffer.from(raw))
    await expect(validateDirectory(root)).rejects.toThrow(`FAIL chain envelope ${reason}`)
  })
  it('rejects invalid UTF-8', async () => {
    const { root } = await fixture()
    await rawBundle(root, 'chain', Buffer.from([0xff]))
    await expect(validateDirectory(root)).rejects.toThrow('invalid_utf8')
  })
  it('admits empty Catalog and actual empty terminal Publication page', async () => {
    const { root, data, save } = await fixture()
    data.get('catalog').result = { list: [], details: [] }
    data.get('publications').result = { pages: [{ data: [], next_cursor: null }], manifests: [], analyses: [], views: [] }
    await save()
    await expect(validateDirectory(root)).resolves.toBeUndefined()
  })
  it('retains an actual terminal empty page after opaque continuation', async () => {
    const { root, data, save } = await fixture()
    const pages = data.get('publications').result.pages
    pages[0].next_cursor = 'opaque-value'
    pages.push({ data: [], next_cursor: null })
    await save()
    await expect(validateDirectory(root)).resolves.toBeUndefined()
  })
  it('rejects repeated opaque cursors', async () => {
    const { root, data, save } = await fixture()
    const pages = data.get('publications').result.pages
    pages[0].next_cursor = 'opaque-value'
    pages.push({ data: [], next_cursor: 'opaque-value' }, { data: [], next_cursor: null })
    await save()
    await expect(validateDirectory(root)).rejects.toThrow('repeated_cursor')
  })
  it('rejects pages after a terminal page', async () => {
    const { root, data, save } = await fixture()
    data.get('publications').result.pages.push({ data: [], next_cursor: null })
    await save()
    await expect(validateDirectory(root)).rejects.toThrow('FAIL publications result')
  })
  it('rejects nested duplicate keys in Manifest', async () => {
    const { root } = await fixture()
    await writeFile(join(root, 'manifest.json'), '{"bundles":[{"path":1,"path":2}]}')
    await expect(validateDirectory(root)).rejects.toThrow('FAIL dataset manifest duplicate_key')
  })
  it('rejects Bundle directory junctions', async () => {
    const { root } = await fixture()
    const original = root + '-original'
    await mkdir(original)
    roots.push(original)
    await rm(join(root, 'chain.json'))
    await symlink(original, join(root, 'chain.json'), process.platform === 'win32' ? 'junction' : 'dir')
    await expect(validateDirectory(root)).rejects.toThrow('FAIL chain file linked_path')
  })
  it('rejects directory junctions', async () => {
    const { root } = await fixture()
    const alias = root + '-alias'; roots.push(alias)
    await symlink(root, alias, process.platform === 'win32' ? 'junction' : 'dir')
    await expect(validateDirectory(alias)).rejects.toThrow('linked_path')
  })
  it('rejects linked Bundle files', async context => {
    const { root } = await fixture()
    const original = root + '-original'; await mkdir(original); roots.push(original)
    await rename(join(root, 'chain.json'), join(original, 'chain.json'))
    try { await symlink(join(original, 'chain.json'), join(root, 'chain.json'), 'file') }
    catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'EPERM') { context.skip(); return }
      throw error
    }
    await expect(validateDirectory(root)).rejects.toThrow('linked_path')
  })
  it('runs actual offline CLI, safe rejection and registry export', async () => {
    const { root } = await fixture()
    const invoke = (...args: string[]) => spawnSync(process.execPath, [resolve('scripts/demo_check.mjs'), ...args], { encoding: 'utf8', env: { ...process.env, TUSHARE_TOKEN: '' } })
    const valid = invoke('--dir', root)
    expect(valid.stderr).toBe(''); expect(valid.status).toBe(0); expect(valid.stdout).toContain('PASS')
    await rawBundle(root, 'chain', Buffer.from('{"secret":"test-only-secret","secret":2}'))
    const invalid = invoke('--dir', root)
    expect(invalid.status).toBe(1); expect(invalid.stderr).toContain('FAIL chain envelope duplicate_key')
    expect(invalid.stderr).not.toContain('test-only-secret')
    const exported = invoke('--registry')
    expect(exported.status).toBe(0); expect(JSON.parse(exported.stdout)).toEqual(registry)
    expect(invoke('--unknown').status).toBe(1)
  }, 30000)
})
