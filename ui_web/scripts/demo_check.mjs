import { build } from 'vite'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, resolve } from 'node:path'
import { mkdir, mkdtemp, rm } from 'node:fs/promises'

const root = fileURLToPath(new URL('..', import.meta.url))
const toolRoot = resolve(root, '.build/demo-tools')
let toolDirectory
try {
  await mkdir(toolRoot, { recursive: true })
  toolDirectory = await mkdtemp(resolve(toolRoot, 'invocation-'))
  await build({
    configFile: false, root, logLevel: 'silent',
    build: {
      ssr: resolve(root, 'demo/build/preflight.ts'), outDir: toolDirectory, emptyOutDir: false,
      minify: false, rolldownOptions: { output: { entryFileNames: 'preflight.mjs' } },
    },
  })
  const { main } = await import(pathToFileURL(resolve(toolDirectory, 'preflight.mjs')).href)
  process.exitCode = await main(process.argv.slice(2), resolve(root, 'demo/bundles'))
} catch {
  console.error('FAIL dataset tooling validation_failed')
  process.exitCode = 1
} finally {
  // Only this invocation's compiler output is disposable.
  if (toolDirectory && dirname(toolDirectory) === toolRoot) {
    try { await rm(toolDirectory, { recursive: true, force: true }) } catch {
      console.error('FAIL dataset tooling cleanup_failed')
      process.exitCode = 1
    }
  }
}
