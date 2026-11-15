import { createInterface } from 'node:readline'
import { readFile, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { join } from 'node:path'
import { registry } from './registry'
import presets from './presets.json'
import { canonicalBytes, parseStrict } from './json'
import { matchesResponse as basisResponse, validateReaderReport } from '../../src/features/futures_basis_research/api/validateResult'
import { matchesResponse as backtestResponse, validateResultResponse, validateRunState, type Run } from '../../src/features/backtesting/api/validateResult'
import { matchesResponse as catalogResponse } from '../../src/features/research_catalog/api/validateCatalog'
import { matchesResponse as publicationResponse } from '../../src/features/research_explorer/api/validateResearch'
import { validateOptionChain } from '../../src/features/mo_option_chain/api/validateOptionChain'
import { validatePremiumPlane } from '../../src/features/mo_option_premium/api/validatePremiumPlane'
import Ajv2020 from 'ajv/dist/2020.js'
import authContract from '../../src/app/auth/api/auth.openapi.json'
import basisContract from '../../src/features/futures_basis_research/api/futuresBasis.openapi.json'
import backtestContract from '../../src/features/backtesting/api/backtesting.openapi.json'

// Payloads stay in this process. Only navigation values cross back to Python.
type RecordValue = Record<string, any>
export class CollectorBridge {
  private responses: RecordValue[] = []
  private authIdentity = new Ajv2020({ strictSchema: false }).compile({
    ...authContract.components.schemas.ActiveIdentity, components: authContract.components,
  })

  private configuration() {
    const ajv = new Ajv2020({ strictSchema: false, formats: {
      date: (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value,
    } })
    for (const entry of registry) {
      const request: RecordValue = presets[entry.preset_id].request
      const contract = entry.validator === 'validateEmbeddedReport' ? basisContract : backtestContract
      if (['validateEmbeddedReport', 'validateEmbeddedBacktestResult'].includes(entry.validator)) {
        const schema = entry.validator === 'validateEmbeddedReport'
          ? basisContract.components.schemas.FuturesBasisRunRequest : backtestContract.components.schemas.FuturesRollRunRequest
        if (!ajv.validate({ ...schema, components: contract.components }, request) || request.start_date > request.end_date) throw new Error('invalid_preset')
      }
      if (['validateOptionChain', 'validatePremiumPlane'].includes(entry.validator)) {
        const date = request.target_trade_date ?? request.as_of
        if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(date)) || new Date(date).toISOString().slice(0, 10) !== date ||
          request.option_product !== 'MO' || !['open', 'high', 'low', 'close'].includes(request.price_type)) throw new Error('invalid_preset')
      }
    }
    return { registry, presets }
  }

  async execute(command: RecordValue): Promise<unknown> {
    if (command.op === 'config') return this.configuration()
    if (command.op === 'response') {
      const bytes = Buffer.from(command.bytes, 'base64')
      if (bytes.subarray(0, 3).equals(Buffer.from([239, 187, 191]))) throw new Error('invalid_utf8')
      const body = parseStrict(new TextDecoder('utf-8', { fatal: true }).decode(bytes)) as RecordValue
      const { route, method, status } = command
      let valid = false
      if (route.startsWith('/research/futures-basis/')) valid = basisResponse(method, route, status, body)
      else if (route.startsWith('/backtesting/')) valid = backtestResponse(method, route, status, body)
      else if (route.startsWith('/research/capabilities')) valid = catalogResponse(route, status, body)
      else if (route.startsWith('/research/publications')) valid = publicationResponse(route, status, body)
      else if (route === '/mo-option-chain') { validateOptionChain(body); valid = true }
      else if (route === '/mo-option-premium-plane') { validatePremiumPlane(body); valid = true }
      else if (route === '/auth/login' || route === '/auth/me') {
        valid = this.authIdentity(body) === true
      }
      if (!valid) throw new Error('invalid_response')
      if (command.expectedRun && body.run_id !== command.expectedRun) throw new Error('run_mismatch')
      if (command.expectedRequest && !canonicalBytes(body.request).equals(canonicalBytes(command.expectedRequest))) throw new Error('request_mismatch')
      if (command.expectedResultStatus && body.result_status !== command.expectedResultStatus) throw new Error('result_status_mismatch')
      if (route.startsWith('/backtesting/') && route.endsWith('/{run_id}')) validateRunState(body as Run)
      if (route.startsWith('/research/futures-basis/') && route.endsWith('/{run_id}')) {
        const complete = body.status === 'COMPLETED'
        const active = ['PENDING', 'RUNNING'].includes(body.status)
        const failed = ['FAILED', 'INTERRUPTED'].includes(body.status)
        if (body.result_available !== complete || (complete ? !['complete', 'partial'].includes(body.result_status) : body.result_status !== null) ||
          (body.status === 'PENDING' && body.started_at !== null) || (body.status === 'RUNNING' && body.started_at === null) ||
          (active ? body.finished_at !== null : body.finished_at === null) || (failed ? body.failure === null : body.failure !== null)) throw new Error('invalid_run')
      }
      if (route.endsWith('/report')) validateReaderReport(body.data, body.request, body.result_status)
      if (route.endsWith('/result')) validateResultResponse(body)
      const ref = this.responses.push(body) - 1
      // These fields contain routing identities only. Financial data is never returned.
      return { ref, id: body.id, username: body.username, status: body.status,
        run_id: body.run_id, request: body.request, result_status: body.result_status, next_cursor: body.next_cursor,
        capabilities: Array.isArray(body) ? body.map(item => item.id) : undefined,
        publications: route === '/research/publications' ? body.data.map((item: any) => item.publication_id) : undefined,
        analyses: route === '/research/publications/{publication_id}' ? body.data.analyses.map((item: any) => ({
          id: item.analysis_id, views: item.views.map((view: any) => view.view_id),
        })) : undefined }
    }
    if (command.op === 'bundle') {
      const entry = registry.find(item => item.bundle_id === command.id)
      if (!entry) throw new Error('invalid_identity')
      const resolveReferences = (value: any): any => {
        if (Array.isArray(value)) return value.map(resolveReferences)
        if (value && typeof value === 'object') {
          if (Object.hasOwn(value, '$ref')) {
            const body = this.responses[value.$ref]
            if (body === undefined) throw new Error('invalid_reference')
            return value.field ? body[value.field] : body
          }
          return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, resolveReferences(item)]))
        }
        return value
      }
      const envelope = { bundle_format: 'demo_bundle_v1', ...entry,
        source: { kind: 'formal_http', description: 'Explicit authenticated HTTP capture. Publication pages are sequential reads without Store snapshot isolation; distribution authorization is separate.' },
        request: resolveReferences(command.request), result: resolveReferences(command.result) }
      const { validator: _validator, path: _path, ...bundle } = envelope
      await writeFile(join(command.directory, entry.path), canonicalBytes(bundle))
      return null
    }
    if (command.op === 'manifest') {
      const bundles = []
      for (const entry of registry) bundles.push({ bundle_id: entry.bundle_id, path: entry.path,
        sha256: createHash('sha256').update(await readFile(join(command.directory, entry.path))).digest('hex') })
      await writeFile(join(command.directory, 'manifest.json'), canonicalBytes({ manifest_format: 'demo_manifest_v1', bundles }))
      return null
    }
    throw new Error('invalid_operation')
  }
}

export async function serve(): Promise<void> {
  const bridge = new CollectorBridge()
  for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
    try { process.stdout.write(JSON.stringify({ ok: true, data: await bridge.execute(JSON.parse(line)) }) + '\n') }
    catch (error) {
      const safe = new Set(['unsafe_number', 'duplicate_key', 'invalid_json', 'invalid_utf8', 'run_mismatch', 'request_mismatch'])
      process.stdout.write(JSON.stringify({ ok: false, reason: error instanceof Error && safe.has(error.message) ? error.message : 'validation_failed',
        fieldPath: (error as { fieldPath?: unknown })?.fieldPath }) + '\n')
    }
  }
}
