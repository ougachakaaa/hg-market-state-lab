import { it, expect } from 'vitest'
import { mkdtemp, writeFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { spawn } from 'node:child_process'
import { chain } from '../../src/features/mo_option_chain/testing/chainFixture'
import { plane } from '../../src/features/mo_option_premium/testing/planeFixture'
import { readerFixture } from '../../src/features/futures_basis_research/report/reader.fixture'
import backtest from '../../src/features/backtesting/api/result.fixture.json'
import { embeddedCatalog } from '../../src/features/research_catalog/testing/catalogFixture'
import { embeddedPublicationSet } from '../../src/features/research_explorer/testing/publicationFixture'
import presets from './presets.json'
import { canonicalBytes, parseStrict } from './json'
import { CollectorBridge } from './collectorBridge'

it('reads the existing configuration and rejects mismatched full HTTP Run envelopes', async () => {
  const bridge = new CollectorBridge()
  const configuration = await bridge.execute({ op: 'config' }) as { presets: unknown }
  expect(configuration.presets).toEqual(presets)
  const body = { run_id: '00000000000000000000000000000001', status: 'PENDING',
    request: { ...presets.basis.request, case: 'futures_basis_v1', analysis_profile: 'r01a_standard_v1' },
    created_at: '2026-11-15T00:00:00Z' }
  const command = { op: 'response', route: '/research/futures-basis/runs', method: 'post', status: 202,
    bytes: Buffer.from(JSON.stringify(body)).toString('base64') }
  await expect(bridge.execute({ ...command, expectedRun: 'foreign-run' })).rejects.toThrow('run_mismatch')
  await expect(bridge.execute({ ...command, expectedRequest: { ...body.request, product_code: 'IF' } })).rejects.toThrow('request_mismatch')
  await expect(bridge.execute({ ...command, bytes: Buffer.from('{"run_id":false}').toString('base64') })).rejects.toThrow('invalid_response')
})

it('preserves Unicode key ordering, decimal identities and stable exact bytes', () => {
  const raw = '{"\\ue000":0.1,"😀":1e-7,"2":[null,0,1.25],"10":"中文"}'
  const bytes = canonicalBytes(parseStrict(raw))
  expect(bytes.toString('utf8')).toBe('{\n  "10": "中文",\n  "2": [\n    null,\n    0,\n    1.25\n  ],\n  "😀": 1e-7,\n  "\ue000": 0.1\n}\n')
  expect(canonicalBytes(parseStrict(bytes.toString('utf8')))).toEqual(bytes)
})

it('collects controlled HTTP fixtures through independent Preflight and exercises failure/recovery', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ddb03-controlled-'))
  try {
    const report = readerFixture()
    report.request.observation = { ...report.request.observation, ...presets.basis.request }
    const payload = { chain: { ...chain, ...presets.chain.request },
      premium: { ...plane, observation: { kind: 'trade_date', value: presets.premium.request.as_of } },
      basis: report, backtest, catalog: embeddedCatalog, publications: embeddedPublicationSet }
    const path = join(directory, 'controlled-fixtures.json')
    await writeFile(path, JSON.stringify(payload))
    const python = process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python'
    const result = await new Promise<{ code: number | null; output: string }>((done, reject) => {
      const child = spawn(resolve(python), ['demo/build/test_collect.py', path], { cwd: process.cwd(), windowsHide: true })
      let output = ''
      child.stdout.on('data', data => { output += data })
      child.stderr.on('data', data => { output += data })
      child.on('error', reject)
      child.on('close', code => done({ code, output }))
    })
    expect(result.output).toContain('OK')
    expect(result.code, result.output).toBe(0)
  } finally { await rm(directory, { recursive: true, force: true }) }
}, 180_000)
