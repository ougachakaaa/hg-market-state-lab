import { createHash } from 'node:crypto'
import { lstat, readdir, readFile, realpath } from 'node:fs/promises'
import { spawnSync } from 'node:child_process'
import { dirname, parse, resolve } from 'node:path'
import { registry, type RegistryEntry } from './registry'
import presets from './presets.json'
import { canonicalBytes, parseStrict } from './json'
import { validateOptionChain } from '../../src/features/mo_option_chain/api/validateOptionChain'
import { validatePremiumPlane } from '../../src/features/mo_option_premium/api/validatePremiumPlane'
import { validateEmbeddedReport } from '../../src/features/futures_basis_research/api/validateResult'
import { validateEmbeddedBacktestResult } from '../../src/features/backtesting/api/validateResult'
import { validateEmbeddedCatalog } from '../../src/features/research_catalog/api/validateCatalog'
import { validateEmbeddedPublicationSet } from '../../src/features/research_explorer/api/validateEmbeddedPublication'

export class AdmissionError extends Error {
  bundleId: string
  stage: string
  reason: string
  constructor(bundleId: string, stage: string, reason: string) {
    super(`FAIL ${bundleId} ${stage} ${reason}`)
    this.bundleId = bundleId
    this.stage = stage
    this.reason = reason
  }
}
function requireCondition(condition: unknown, reason: string): asserts condition {
  if (!condition) throw new Error(reason)
}
function object(value: unknown): Record<string, unknown> {
  requireCondition(typeof value === 'object' && value !== null && !Array.isArray(value), 'invalid_object')
  return value as Record<string, unknown>
}
function closed(value: unknown, keys: string[]): Record<string, unknown> {
  const record = object(value)
  requireCondition(Object.keys(record).length === keys.length && keys.every(key => Object.hasOwn(record, key)), 'invalid_fields')
  return record
}
function equal(left: unknown, right: unknown): boolean { return canonicalBytes(left).equals(canonicalBytes(right)) }
async function stage<T>(id: string, name: string, action: () => T | Promise<T>): Promise<T> {
  try { return await action() } catch (error) {
    if (error instanceof AdmissionError) throw error
    if ((error as NodeJS.ErrnoException)?.code === 'ENOENT') {
      throw new AdmissionError(id, name, name === 'directory' ? 'missing_directory' : 'missing_file')
    }
    // Never include Feature errors: some interpolate untrusted identifiers and payloads.
    const safe = new Set(['invalid_json', 'duplicate_key', 'unsafe_number', 'invalid_utf8', 'noncanonical_json',
      'invalid_object', 'invalid_fields', 'unsupported_format', 'invalid_identity', 'invalid_hash', 'invalid_manifest',
      'unsafe_path', 'linked_path', 'unexpected_files', 'missing_file', 'preset_mismatch', 'incomplete_catalog',
      'incomplete_publications', 'nonterminal_pages', 'repeated_cursor'])
    const reason = error instanceof Error && safe.has(error.message) ? error.message : 'validation_failed'
    throw new AdmissionError(id, name, reason)
  }
}
async function plainPath(path: string): Promise<void> {
  const parent = dirname(path)
  if (parent !== path) await plainPath(parent)
  const info = await lstat(path)
  requireCondition(!info.isSymbolicLink(), 'linked_path')
  // Windows junctions are reported as symbolic links. realpath also catches redirected targets.
  const actual = await realpath(path)
  requireCondition(process.platform === 'win32'
    ? resolve(actual).toLowerCase() === resolve(path).toLowerCase()
    : resolve(actual) === resolve(path), 'linked_path')
}
function rejectWindowsReparsePoints(root: string): void {
  if (process.platform !== 'win32') return
  const paths = [resolve(root, 'manifest.json'), ...registry.map(entry => resolve(root, entry.path))]
  let current = root
  while (true) {
    paths.push(current)
    const parent = dirname(current)
    if (parent === current) break
    current = parent
  }
  // Node exposes links/junctions through lstat, but not every Windows reparse tag.
  // Pass paths as data over stdin to the platform filesystem attribute reader.
  const command = `
    [Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
    $paths = [Console]::In.ReadToEnd() | ConvertFrom-Json
    for ($index = 0; $index -lt $paths.Count; $index++) {
      $path = $paths[$index]
      if (Test-Path -LiteralPath $path) {
        $item = Get-Item -Force -LiteralPath $path -ErrorAction Stop
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
          Write-Output $index
          exit 2
        }
      }
    }
    exit 0
  `
  const check = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', command],
  { input: JSON.stringify(paths), encoding: 'utf8', windowsHide: true })
  if (check.status === 2) {
    const entry = registry[Number(check.stdout.trim()) - 1]
    throw new AdmissionError(entry?.bundle_id ?? 'dataset', entry ? 'file' : 'directory', 'linked_path')
  }
  if (check.status !== 0) throw new AdmissionError('dataset', 'directory', 'reparse_check_failed')
}
function decode(bytes: Buffer): unknown {
  requireCondition(!(bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf), 'invalid_utf8')
  let text: string
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes) } catch { throw new Error('invalid_utf8') }
  const value = parseStrict(text)
  requireCondition(canonicalBytes(value).equals(bytes), 'noncanonical_json')
  return value
}

function formalResult(entry: RegistryEntry, envelope: Record<string, unknown>): void {
  const { request, result } = envelope
  const expected = presets[entry.preset_id].request
  const actual = object(request)
  requireCondition(Object.entries(expected).every(([key, value]) => Object.hasOwn(actual, key) && equal(actual[key], value)), 'preset_mismatch')
  switch (entry.validator) {
    case 'validateOptionChain': {
      requireCondition(equal(request, expected), 'preset_mismatch')
      const data = validateOptionChain(result)
      requireCondition(data.target_trade_date === actual.target_trade_date && data.option_product === actual.option_product && data.price_type === actual.price_type, 'invalid_identity')
      break
    }
    case 'validatePremiumPlane': {
      requireCondition(equal(request, expected), 'preset_mismatch')
      const { plane } = validatePremiumPlane(result)
      requireCondition(plane.observation.kind === 'trade_date' && plane.observation.value === actual.as_of && plane.option_product === actual.option_product && plane.price_type === actual.price_type, 'invalid_identity')
      break
    }
    case 'validateEmbeddedReport': validateEmbeddedReport({ request, report: result }); break
    case 'validateEmbeddedBacktestResult': validateEmbeddedBacktestResult({ request, result }); break
    case 'validateEmbeddedCatalog': {
      requireCondition(equal(request, expected), 'preset_mismatch')
      const payload = closed(result, ['list', 'details'])
      const data = validateEmbeddedCatalog(payload as unknown as Parameters<typeof validateEmbeddedCatalog>[0])
      requireCondition(data.capabilities.every(item => data.details.has(item.id) && equal(item, data.details.get(item.id))), 'incomplete_catalog')
      break
    }
    case 'validateEmbeddedPublicationSet': {
      requireCondition(equal(request, expected), 'preset_mismatch')
      const payload = closed(result, ['pages', 'manifests', 'analyses', 'views'])
      const data = validateEmbeddedPublicationSet(payload as unknown as Parameters<typeof validateEmbeddedPublicationSet>[0])
      requireCondition(data.unembeddedCursor === null, 'nonterminal_pages')
      const cursors = data.pages.map(page => page.next_cursor).filter(cursor => cursor !== null)
      requireCondition(new Set(cursors).size === cursors.length, 'repeated_cursor')
      for (const id of data.publicationIds) {
        const manifest = data.manifests.get(id)
        requireCondition(manifest, 'incomplete_publications')
        for (const summary of manifest.analyses) {
          requireCondition(data.analyses.get(id)?.has(summary.analysis_id), 'incomplete_publications')
          for (const reference of summary.views) requireCondition(data.views.get(id)?.has(reference.view_id), 'incomplete_publications')
        }
      }
      break
    }
  }
}

export async function validateDirectory(directory: string): Promise<void> {
  const root = resolve(directory)
  await stage('dataset', 'directory', async () => {
    rejectWindowsReparsePoints(root)
    await plainPath(root)
    requireCondition((await lstat(root)).isDirectory(), 'unsafe_path')
  })
  const manifest = await stage('dataset', 'manifest', async () => {
    const path = resolve(root, 'manifest.json')
    await plainPath(path)
    return closed(decode(await readFile(path)), ['manifest_format', 'bundles'])
  })
  const entries = await stage('dataset', 'manifest', () => {
    requireCondition(manifest.manifest_format === 'demo_manifest_v1', 'unsupported_format')
    requireCondition(Array.isArray(manifest.bundles), 'invalid_manifest')
    const values = manifest.bundles.map(value => closed(value, ['bundle_id', 'path', 'sha256']))
    const ids = values.map(item => item.bundle_id)
    const paths = values.map(item => item.path)
    requireCondition(new Set(ids).size === ids.length && new Set(paths).size === paths.length, 'invalid_manifest')
    for (const value of values) {
      requireCondition(typeof value.path === 'string' && !parse(value.path).root && !/[\\/:]/.test(value.path) && !value.path.includes('..'), 'unsafe_path')
      requireCondition(typeof value.sha256 === 'string' && /^[0-9a-f]{64}$/.test(value.sha256), 'invalid_hash')
    }
    requireCondition(ids.every(id => registry.some(entry => entry.bundle_id === id)), 'invalid_manifest')
    for (const entry of registry) {
      if (!ids.includes(entry.bundle_id)) throw new AdmissionError(entry.bundle_id, 'manifest', 'missing_bundle')
    }
    requireCondition(equal(ids, registry.map(item => item.bundle_id)), 'invalid_manifest')
    requireCondition(values.every((value, index) => value.path === registry[index].path), 'invalid_identity')
    return values
  })
  await stage('dataset', 'directory', async () => {
    const files = await readdir(root)
    for (const entry of registry) {
      if (!files.includes(entry.path)) throw new AdmissionError(entry.bundle_id, 'file', 'missing_file')
    }
    requireCondition(equal(files.sort(), ['manifest.json', ...registry.map(item => item.path)].sort()), 'unexpected_files')
  })
  for (const [index, entry] of registry.entries()) {
    const bytes = await stage(entry.bundle_id, 'file', async () => {
      const path = resolve(root, entry.path)
      await plainPath(path)
      requireCondition((await lstat(path)).isFile(), 'missing_file')
      return readFile(path)
    })
    await stage(entry.bundle_id, 'hash', () => {
      requireCondition(createHash('sha256').update(bytes).digest('hex') === entries[index].sha256, 'invalid_hash')
    })
    const envelope = await stage(entry.bundle_id, 'envelope', () => {
      const data = closed(decode(bytes), ['bundle_format', 'bundle_id', 'preset_id', 'request', 'result_contract', 'source', 'result'])
      requireCondition(data.bundle_format === 'demo_bundle_v1', 'unsupported_format')
      requireCondition(data.bundle_id === entry.bundle_id && data.preset_id === entry.preset_id && data.result_contract === entry.result_contract, 'invalid_identity')
      const source = closed(data.source, ['kind', 'description'])
      requireCondition(source.kind === 'formal_http' && typeof source.description === 'string' && source.description.trim().length > 0, 'invalid_fields')
      return data
    })
    await stage(entry.bundle_id, 'result', () => formalResult(entry, envelope))
  }
}
