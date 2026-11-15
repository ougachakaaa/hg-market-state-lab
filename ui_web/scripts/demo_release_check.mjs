import { build } from 'vite'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { resolve } from 'node:path'
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises'
import { readFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { buildDemo, lock } from '../demo/build/build.mjs'
import { checkPublicSafety } from './public_asset_safety.mjs'
import { checkoutIdentity, scanDemo, verifyDemo } from './demo_artifact.mjs'
import { sha } from './artifact_integrity.mjs'
const web = fileURLToPath(new URL('../', import.meta.url))
const evidence = resolve(web, '.build/demo-release.json')
let temporary, releaseLock
try {
  await mkdir(resolve(web, '.build'), { recursive: true })
  releaseLock = await lock(resolve(web, '.build/demo-release.lock'))
  await rm(evidence, { force: true })
  temporary = await mkdtemp(resolve(web, '.build/release-tools-'))
  await build({ configFile: false, root: web, logLevel: 'silent', build: {
    ssr: resolve(web, 'demo/release/validate.ts'), outDir: temporary, minify: false,
    rolldownOptions: { output: { entryFileNames: 'validate.mjs' } },
  } })
  const { main } = await import(pathToFileURL(resolve(temporary, 'validate.mjs')).href)
  await main(process.argv.slice(2), web)
  checkPublicSafety()
  await buildDemo()
  const identity = checkoutIdentity()
  const requirements = readFileSync(resolve(web, 'demo/release/requirements.json'))
  const committed = execFileSync('git', ['show', `${identity.sourceCommit}:ui_web/demo/release/requirements.json`], { cwd: web })
  if (sha(requirements) !== sha(committed)) throw new Error('Requirements differ from committed checkout')
  const receipt = scanDemo(resolve(web, '.build/demo'), identity)
  verifyDemo(resolve(web, '.build/demo'), receipt, identity)
  await writeFile(resolve(web, '.build/demo-receipt.json'), JSON.stringify(receipt, null, 2) + '\n')
  await writeFile(evidence, JSON.stringify({ ...identity, requirementsSha256: sha(requirements), receipt, result: 'PASS' }, null, 2) + '\n')
  console.log('PASS Release Gate, build and Artifact Receipt')
} catch (error) {
  console.error(error.message)
  process.exitCode = 1
} finally {
  if (temporary) await rm(temporary, { recursive: true, force: true })
  if (releaseLock) await releaseLock()
}
