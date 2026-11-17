import { identity, InvalidBundleError, validateBundle, type Bundle } from './dataAdapter'
import type { BundleData, BundleLoaders, ExampleKey, ResultIdentity } from './results'

export interface Resource<T> { load: () => Promise<T> }
export function resource<T>(load: () => Promise<T>): Resource<T> {
  let pending: Promise<T> | undefined
  return { load() {
    return pending ??= Promise.resolve().then(load).catch(error => { pending = undefined; throw error })
  } }
}
type LoadedBundle<K extends ExampleKey> = { data: BundleData[K]; identity: ResultIdentity }
export function bundleStore(loaders: BundleLoaders) {
  const cache = new Map<ExampleKey, Resource<unknown>>()
  return { get<K extends ExampleKey>(id: K, adapt: (bundle: Bundle) => BundleData[K]): Resource<LoadedBundle<K>> {
    let found = cache.get(id)
    if (!found) {
      found = resource(async () => {
        const loadStart = performance.now()
        const module = await loaders[id]()
        performance.measure(`demo-bundle:${id}:load`, { start: loadStart, end: performance.now() })
        const validationStart = performance.now()
        try {
          const bundle = validateBundle(id, module.default)
          return { data: adapt(bundle), identity: identity(bundle) }
        } catch { throw new InvalidBundleError() }
        finally { performance.measure(`demo-bundle:${id}:validate`, { start: validationStart, end: performance.now() }) }
      })
      cache.set(id, found)
    }
    return found as Resource<LoadedBundle<K>>
  } }
}
export type BundleStore = ReturnType<typeof bundleStore>
