vi.mock('react-plotly.js', () => ({ default: () => null }))
import { it, expect, vi } from 'vitest'
import { rm, readFile } from 'node:fs/promises'
import { fixture } from './dataset.fixture'
import { registry } from './registry'
import { adaptBundles } from '../runtime/dataAdapter'
import { buildDemo } from './build.mjs'
it('maps seven Results and rejects missing or malformed data', async () => {
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
  } finally { await rm(data.root, { recursive: true, force: true }) }
}, 120000)
