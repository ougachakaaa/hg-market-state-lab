import { preview } from 'vite'
import { readFile, lstat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { web, assertUnlinked } from './build.mjs'
export async function previewDemo(port = 4173, { outputRoot = resolve(web, '.build') } = {}) {
  const output = resolve(outputRoot, 'demo')
  await assertUnlinked(output)
  try { await lstat(resolve(outputRoot, 'demo-output.lock')); throw new Error('build_in_progress_or_interrupted') }
  catch (error) { if (error.code !== 'ENOENT') throw error }
  const marker = JSON.parse(await readFile(resolve(output, 'build-complete.json'), 'utf8'))
  if (marker.format !== 'ddb04_static_build_v1') throw new Error('invalid_build_marker')
  return preview({ configFile: false, root: web, base: '/hg-market-state-lab/',
    publicDir: false, envDir: false, build: { outDir: output },
    preview: { host: '127.0.0.1', port, strictPort: true } })
}
if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  try { const server = await previewDemo(); server.printUrls() }
  catch { console.error('FAIL demo preview requires a complete successful build and no output lock'); process.exitCode = 1 }
}
