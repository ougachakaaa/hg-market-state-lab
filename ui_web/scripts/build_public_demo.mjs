import assert from 'node:assert/strict'
import { build, createServer } from 'vite'
import react from '@vitejs/plugin-react'
import { mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'
import { execFileSync } from 'node:child_process'
import { loadPublicPackage, web, repository, output, sha, inventory, verifyArtifact } from './public_release.mjs'
import { privateDemoIsolation } from './private_demo_isolation.mjs'
assert.equal(process.argv.length, 2, 'Public build accepts no alternate/private input paths')
const { envelope, files: inputs } = loadPublicPackage()
const server = await createServer({ configFile: false, root: web, logLevel: 'silent', server: { middlewareMode: true }, appType: 'custom' })
try {
  const { admitPublicEnvelope } = await server.ssrLoadModule('/src/demo/public/admission.ts')
  await admitPublicEnvelope(envelope)
} finally { await server.close() }
process.env.NODE_ENV = 'production'
rmSync(output, { recursive: true, force: true })
mkdirSync(output, { recursive: true })
await build({ configFile: false, root: resolve(web, 'src/demo/public'), base: '/hg-market-state-lab/', envDir: false, publicDir: false,
  plugins: [react(), { name: 'reviewed-public-examples', resolveId(id) { if (id === 'virtual:public-examples') return '\0public-examples' }, load(id) { if (id === '\0public-examples') return `export default ${JSON.stringify(envelope)}` } }, privateDemoIsolation('public')],
  build: { outDir: resolve(output, 'site'), sourcemap: false },
})
const git = (...args) => execFileSync('git', args, { cwd: repository, encoding: 'utf8' }).trim()
const files = inventory(resolve(output, 'site'))
const receipt = { status: 'PASS', version: 'public-release-v1', sourceSha: git('rev-parse', 'HEAD'), base: '/hg-market-state-lab/', node: process.version,
  npm: execFileSync(process.env.npm_execpath ? process.execPath : 'npm', process.env.npm_execpath ? [process.env.npm_execpath, '--version'] : ['--version'], { encoding: 'utf8' }).trim(), lockfiles: Object.fromEntries(['poetry.lock', 'ui_web/package-lock.json'].map(p=>[p,sha(readFileSync(resolve(repository,p)))])),
  inputs, examples: Object.values(envelope.examples).map(r=>({ identity: r.identity, reviewDigest: sha(JSON.stringify(r.review)) })), files, artifactDigest: sha(JSON.stringify(files)) }
verifyArtifact(resolve(output, 'site'), receipt)
writeFileSync(resolve(output, 'release.json'), JSON.stringify(receipt, null, 2)+'\n')
console.log(`PASS: public V2 ${receipt.sourceSha} ${receipt.artifactDigest}`)
