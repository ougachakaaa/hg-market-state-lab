// Single-file packaging only. No business projection or numerical calculation.
import { build } from 'vite'
import react from '@vitejs/plugin-react'
import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
const output = resolve(process.argv[2])
const data = JSON.parse(await readFile(resolve(output, 'report-data.json'), 'utf8'))
if (data.profile !== 'futures_basis_report_evidence_v1') throw new Error('Unsupported report profile')
const result = await build({
  configFile: false, root, plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: { write: false, minify: true, cssCodeSplit: false, assetsInlineLimit: Infinity,
    lib: { entry: resolve(root, 'src/offline/futures_basis/main.tsx'), name: 'R01AReport', formats: ['iife'] },
    rolldownOptions: { output: { codeSplitting: false } },
  },
})
const bundles = Array.isArray(result) ? result : [result]
const files = bundles.flatMap(b => b.output)
const chunks = files.filter(f => f.type === 'chunk')
if (chunks.length !== 1 || chunks[0].imports.length || chunks[0].dynamicImports.length) throw new Error('Report must have one self-contained script')
const css = files.filter(f => f.type === 'asset' && f.fileName.endsWith('.css')).map(f => String(f.source)).join('\n')
if (files.some(f => f.type === 'asset' && !f.fileName.endsWith('.css'))) throw new Error('Unexpected external asset')
const safeJson = JSON.stringify(data).replace(/[<>&\u2028\u2029]/g, c => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`)
const license = await readFile(resolve(root, 'src/offline/futures_basis/assets/OFL.txt'), 'utf8')
const script = chunks[0].code.replace(/<\/script/gi, '<\\/script')
const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Historical Basis Research</title><style>${css.replace(/<\/style/gi, '<\\/style')}</style></head><body><script id="font-license" type="text/plain">${license}</script><div id="root"></div><script id="report-data" type="application/json">${safeJson}</script><script>${script}</script></body></html>`
await writeFile(resolve(output, 'report.html'), html)
console.log(`Offline HTML: ${resolve(output, 'report.html')}`)
