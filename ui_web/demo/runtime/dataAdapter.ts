import type { ResultIdentity, ExampleKey } from './results'
import { registry } from '../build/registry'

export type Bundle = {
  bundle_format: 'demo_bundle_v1'
  bundle_id: ExampleKey
  preset_id: string
  result_contract: string
  source: ResultIdentity['source']
  request: unknown
  result: unknown
}
export class InvalidBundleError extends Error {
  constructor() { super('Invalid static Bundle') }
}
export function validateBundle(id: ExampleKey, input: unknown): Bundle {
  const entry = registry.find(entry => entry.bundle_id === id)
  const value = input as Partial<Bundle> | null
  if (!entry || !value || typeof value !== 'object' || Array.isArray(value) ||
    Object.keys(value).length !== 7 || !Object.hasOwn(value, 'request') || !Object.hasOwn(value, 'result') ||
    value.bundle_id !== id || value.bundle_format !== 'demo_bundle_v1' ||
    value.preset_id !== entry.preset_id || value.result_contract !== entry.result_contract ||
    value.source?.kind !== 'formal_http' || Object.keys(value.source).length !== 2 ||
    typeof value.source.description !== 'string' || !value.source.description.trim()) throw new InvalidBundleError()
  return value as Bundle
}
export function identity(bundle: Bundle): ResultIdentity {
  return { id: bundle.bundle_id, preset_id: bundle.preset_id, result_contract: bundle.result_contract, source: bundle.source }
}
export function disclose(identity: ResultIdentity): string {
  return `${identity.id} · ${identity.source.description} · 构建前已通过结构与完整性校验。静态只读，不进行实时金融计算。数据不保证准确，仅供项目功能展示，不构成投资建议。`
}
