import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { bundleStore, resource } from './resources'
import { AsyncContent } from './AsyncContent'
import { InvalidBundleError } from './dataAdapter'
import { registry } from '../build/registry'
import type { BundleLoaders } from './results'

afterEach(cleanup)
function catalog() {
  const entry = registry.find(entry => entry.bundle_id === 'catalog')!
  return { bundle_format: 'demo_bundle_v1', bundle_id: entry.bundle_id, preset_id: entry.preset_id,
    result_contract: entry.result_contract, source: { kind: 'formal_http', description: 'Test-only source' }, request: {}, result: { list: [], details: [] } }
}
function loaders(load = vi.fn(async () => ({ default: catalog() }))) {
  return Object.fromEntries(registry.map(entry => [entry.bundle_id, entry.bundle_id === 'catalog' ? load : vi.fn(() => { throw new Error('unrelated consumer loaded') })])) as unknown as BundleLoaders
}
it('loads and validates only its consumer, sharing in-flight and completed adaptation', async () => {
  const load = vi.fn(async () => ({ default: catalog() }))
  const inputs = loaders(load)
  const store = bundleStore(inputs)
  const adapt = vi.fn(() => ({ list: [], details: [] }))
  const entry = store.get('catalog', adapt)
  expect(load).not.toHaveBeenCalled()
  const a = entry.load(), b = store.get('catalog', adapt).load()
  expect(a).toBe(b)
  const result = await a
  expect(result.identity.id).toBe('catalog')
  expect(await entry.load()).toBe(result)
  expect(load).toHaveBeenCalledOnce()
  expect(adapt).toHaveBeenCalledOnce()
  for (const [id, load] of Object.entries(inputs)) if (id !== 'catalog') expect(load).not.toHaveBeenCalled()
})
it('rejects mismatched envelopes and invalid formal results without caching success', async () => {
  const wrong = catalog(); wrong.bundle_id = 'basis' as 'catalog'
  const load = vi.fn().mockResolvedValueOnce({ default: wrong }).mockResolvedValue({ default: catalog() })
  const adapt = vi.fn(() => { throw new Error('/private/provider-details') })
  const entry = bundleStore(loaders(load)).get('catalog', adapt)
  await expect(entry.load()).rejects.toBeInstanceOf(InvalidBundleError)
  expect(adapt).not.toHaveBeenCalled()
  await expect(entry.load()).rejects.toBeInstanceOf(InvalidBundleError)
  expect(adapt).toHaveBeenCalledOnce()
  expect(load).toHaveBeenCalledTimes(2)
})
it('shows safe loading failures and retries only after explicit activation', async () => {
  const load = vi.fn<() => Promise<string>>().mockRejectedValueOnce(new Error('/private/network-details')).mockResolvedValueOnce('ready')
  render(<AsyncContent resource={resource(load)}>{data => <p>{data}</p>}</AsyncContent>)
  await screen.findByText('静态资源加载失败，请重试。')
  expect(screen.queryByText(/private/)).toBeNull()
  expect(load).toHaveBeenCalledOnce()
  fireEvent.click(screen.getByRole('button', { name: '重试静态资源' }))
  await screen.findByText('ready')
  expect(load).toHaveBeenCalledTimes(2)
})
it('distinguishes invalid data from unavailable static resources', async () => {
  render(<AsyncContent resource={resource(async () => { throw new InvalidBundleError() })}>{() => <p>fabricated result</p>}</AsyncContent>)
  await screen.findByText('静态结果未通过校验，已停止展示。')
  expect(screen.queryByText('fabricated result')).toBeNull()
})
it('hides previous results immediately and isolates late completions after switching consumers', async () => {
  let finishA!: (value: string) => void, finishB!: (value: string) => void
  const a = resource(() => new Promise<string>(done => { finishA = done }))
  const b = resource(() => new Promise<string>(done => { finishB = done }))
  const view = render(<AsyncContent resource={a}>{text => <p>{text}</p>}</AsyncContent>)
  await waitFor(() => expect(finishA).toBeTypeOf('function'))
  view.rerender(<AsyncContent resource={b}>{text => <p>{text}</p>}</AsyncContent>)
  await waitFor(() => expect(finishB).toBeTypeOf('function'))
  await act(async () => finishA('obsolete result'))
  expect(screen.queryByText('obsolete result')).toBeNull()
  await act(async () => finishB('current result'))
  expect(screen.getByText('current result')).toBeTruthy()
  view.rerender(<AsyncContent resource={a}>{text => <p>{text}</p>}</AsyncContent>)
  expect(screen.queryByText('current result')).toBeNull()
  await screen.findByText('obsolete result')
})
