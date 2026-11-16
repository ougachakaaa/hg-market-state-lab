vi.mock('react-plotly.js', () => ({ default: () => null }))
import { it, expect, vi } from 'vitest'
import { rm, readFile, writeFile, mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { fixture } from './dataset.fixture'
import { verifyBrowser } from './browserAcceptance.mjs'
import { registry } from './registry'
import { adaptBundles } from '../runtime/dataAdapter'
import { buildDemo, lock } from './build.mjs'
it('maps nine Results and rejects missing or malformed data', async () => {
  const data = await fixture()
  try {
    const bundles = [...data.data.values()]
    const adapted = adaptBundles(bundles)
    expect(Object.keys(adapted.identities).sort()).toEqual(registry.map(entry => entry.bundle_id))
    expect(adapted.m1.request).not.toEqual(adapted.q1.request)
    expect(() => adaptBundles(bundles.slice(1))).toThrow()
    expect(() => adaptBundles(bundles.map(value => value.bundle_id === 'chain' ? { ...value, result: {} } : value))).toThrow()
  } finally { await rm(data.root, { recursive: true, force: true }) }
})
it('builds an offline artifact from a private snapshot', async () => {
  const data = await fixture()
  try {
    await buildDemo({ dataset: data.root })
    expect(await readFile('.build/demo/build-complete.json', 'utf8')).toContain('ddb04_static_build_v1')
    const graph = await readFile('.build/demo/runtime-dependencies.json', 'utf8')
    expect(graph).not.toMatch(/shared\/http|\.fixture|\/testing\//)
    if (process.env.DDB_BROWSER_ACCEPTANCE === '1') await verifyBrowser()
  } finally { await rm(data.root, { recursive: true, force: true }) }
}, 120000)

it.each(['missing', 'hash', 'contract'])('fails the build on %s input', async kind => {
  const data = await fixture()
  try {
    if (kind === 'missing') await rm(data.root + '/chain.json')
    if (kind === 'hash') await writeFile(data.root + '/chain.json', '{}')
    if (kind === 'contract') { data.data.get('chain').result = {}; await data.save() }
    await expect(buildDemo({ dataset: data.root })).rejects.toThrow('snapshot_admission_failed')
  } finally { await rm(data.root, { recursive: true, force: true }) }
}, 20000)
it('freezes bytes before allowing Collector changes and excludes concurrent builds', async () => {
  const data = await fixture()
  try {
    await buildDemo({ dataset: data.root, compile: async (snapshot: string, artifact: string) => {
      const bytes = await readFile(snapshot + '/chain.json')
      const release = await lock(fileURLToPath(new URL('../../.build/demo-collection/dataset.lock', import.meta.url)))
      try { await writeFile(data.root + '/chain.json', 'changed after snapshot') } finally { await release() }
      expect(await readFile(snapshot + '/chain.json')).toEqual(bytes)
      await expect(buildDemo({ dataset: data.root })).rejects.toThrow('busy')
      await mkdir(artifact + '/assets', { recursive: true }); await writeFile(artifact + '/index.html', 'test-only artifact')
    } })
  } finally { await rm(data.root, { recursive: true, force: true }) }
})

it('removes formal output when Vite fails', async () => {
  const data = await fixture()
  try {
    await expect(buildDemo({ dataset: data.root, compile: async () => { throw new Error('controlled_vite_failure') } })).rejects.toThrow('controlled_vite_failure')
    await expect(readFile('.build/demo/build-complete.json')).rejects.toThrow()
  } finally { await rm(data.root, { recursive: true, force: true }) }
})
