import { existsSync, appendFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createServer } from 'vite'
import { loadPublicPackage, packageRoot, web } from './public_release.mjs'
let admitted = false
if (existsSync(resolve(packageRoot, 'package.json'))) {
  const { envelope } = loadPublicPackage()
  const server = await createServer({ root: web, configFile: false, logLevel: 'silent', server: { middlewareMode: true }, appType: 'custom' })
  try { const { admitPublicEnvelope } = await server.ssrLoadModule('/src/demo/public/admission.ts'); await admitPublicEnvelope(envelope); admitted = true }
  finally { await server.close() }
}
console.log(admitted ? 'PASS: public admission' : 'BLOCKED: public V2 rights/package missing. No deployment; existing V1 retained.')
if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `admitted=${admitted}\n`)
if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, admitted ? 'Public V2 admission PASS.\n' : '**Public Demo V2 BLOCKED** — no reviewed public package. V1 unchanged.\n')
