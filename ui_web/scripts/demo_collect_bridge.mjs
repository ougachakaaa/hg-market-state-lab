import { build } from 'vite'
import { mkdtemp, mkdir, rm } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
await mkdir(resolve(root, '.build/demo-tools'), { recursive: true })
const output = await mkdtemp(resolve(root, '.build/demo-tools/collector-'))
try {
  await build({ configFile: false, root, logLevel: 'silent', build: {
    ssr: resolve(root, 'demo/build/collectorBridge.ts'), outDir: output,
    emptyOutDir: false, minify: false,
    rolldownOptions: { output: { entryFileNames: 'bridge.mjs' } },
  } })
  const { serve } = await import(pathToFileURL(resolve(output, 'bridge.mjs')).href)
  await serve()
} catch {
  process.stderr.write('FAIL dataset bridge tooling_failed\n')
  process.exitCode = 1
} finally {
  await rm(output, { recursive: true, force: true })
}
