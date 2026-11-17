import { it, expect, beforeAll, afterAll } from 'vitest'
import { rm, readFile, writeFile, mkdir, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { isolatedOutput, developerOutputDigest } from './output.fixture'
import { fixture } from './dataset.fixture'
import { buildDemo, lock } from './build.mjs'
let developerBefore: string
beforeAll(async () => { developerBefore = await developerOutputDigest() })
afterAll(async () => { expect(await developerOutputDigest()).toBe(developerBefore) })
it('builds an offline artifact from a private snapshot', async () => {
  const data = await fixture()
  const isolated = await isolatedOutput()
  try {
    await buildDemo({ ...isolated, dataset: data.root })
    expect(await readFile(resolve(isolated.output, 'build-complete.json'), 'utf8')).toContain('ddb04_static_build_v1')
    const graph = await readFile(resolve(isolated.output, 'runtime-dependencies.json'), 'utf8')
    expect(graph).not.toMatch(/shared\/http|\.fixture|\/testing\//)
    expect((await readdir(isolated.outputRoot)).sort()).toEqual(['demo', 'demo-collection'])
  } finally { await rm(data.root, { recursive: true, force: true }); await isolated.cleanup() }
}, 120000)

it.each(['missing', 'hash', 'contract'])('fails the build on %s input', async kind => {
  const data = await fixture()
  const isolated = await isolatedOutput()
  try {
    if (kind === 'missing') await rm(data.root + '/chain.json')
    if (kind === 'hash') await writeFile(data.root + '/chain.json', '{}')
    if (kind === 'contract') { data.data.get('chain').result = {}; await data.save() }
    await expect(buildDemo({ ...isolated, dataset: data.root })).rejects.toThrow('snapshot_admission_failed')
    expect(await readdir(isolated.outputRoot)).toEqual(['demo-collection'])
  } finally { await rm(data.root, { recursive: true, force: true }); await isolated.cleanup() }
}, 20000)
it('freezes bytes before allowing Collector changes and excludes concurrent builds', async () => {
  const data = await fixture()
  const isolated = await isolatedOutput()
  try {
    await buildDemo({ ...isolated, dataset: data.root, compile: async (snapshot: string, artifact: string) => {
      const bytes = await readFile(snapshot + '/chain.json')
      const release = await lock(resolve(isolated.work, 'dataset.lock'))
      try { await writeFile(data.root + '/chain.json', 'changed after snapshot') } finally { await release() }
      expect(await readFile(snapshot + '/chain.json')).toEqual(bytes)
      await expect(buildDemo({ ...isolated, dataset: data.root })).rejects.toThrow('busy')
      await mkdir(artifact + '/assets', { recursive: true }); await writeFile(artifact + '/index.html', 'test-only artifact')
    } })
  } finally { await rm(data.root, { recursive: true, force: true }); await isolated.cleanup() }
})

it('removes formal output when Vite fails', async () => {
  const data = await fixture()
  const isolated = await isolatedOutput()
  try {
    await expect(buildDemo({ ...isolated, dataset: data.root, compile: async () => { throw new Error('controlled_vite_failure') } })).rejects.toThrow('controlled_vite_failure')
    await expect(readFile(resolve(isolated.output, 'build-complete.json'))).rejects.toThrow()
    expect(await readdir(isolated.outputRoot)).toEqual(['demo-collection'])
  } finally { await rm(data.root, { recursive: true, force: true }); await isolated.cleanup() }
})
