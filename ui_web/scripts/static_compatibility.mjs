// No private input and no business execution: inspect the real entry's build graph.
import { build } from 'vite'
import react from '@vitejs/plugin-react'
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'
import { staticPresentationIsolation } from './staticPresentationIsolation.ts'
import { privateDemoIsolation } from './private_demo_isolation.mjs'
const testRoot = resolve('.build/tests')
mkdirSync(testRoot, { recursive: true })
const output = mkdtempSync(resolve(testRoot, 'static-contract-'))
try {
  await build({ configFile: resolve('vite.demo.config.ts'), plugins: [staticPresentationIsolation(
    'futures_basis_research',
    /\/testing\/|\/api\/|\/hooks\/|\/page\/.*Page\.tsx$/,
    ['src/demo/futures_basis/index.html', 'src/demo/futures_basis/main.tsx', 'src/demo/futures_basis/fixture.ts', 'src/demo/futures_basis/report.v1.json', 'src/demo/futures_basis/demo.css'],
  )], build: { outDir: resolve(output, 'public') } })
  await build({ configFile: false, root: resolve('src/demo/private'), publicDir: false, envDir: false,
    plugins: [react(), {
      name: 'invalid-test-only-envelope',
      resolveId(id) { if (id === 'virtual:private-examples') return '\0test-only-envelope' },
      load(id) { if (id === '\0test-only-envelope') return 'export default {}' },
    }, privateDemoIsolation()],
    build: { outDir: resolve(output, 'private'), sourcemap: false },
  })
  await build({ configFile: false, root: resolve('src/demo/public'), publicDir: false, envDir: false, plugins: [react(), { name: 'invalid-public-probe', resolveId(id) { if (id === 'virtual:public-examples') return '\0public-probe' }, load(id) { if (id === '\0public-probe') return 'export default {}' } }, privateDemoIsolation('public')], build: { outDir: resolve(output, 'public-graph'), sourcemap: false } })
  console.log('PASS: actual private/public entry dependency graph (no market payload; no browser acceptance claim)')
} finally { rmSync(output, { recursive: true, force: true }) }
