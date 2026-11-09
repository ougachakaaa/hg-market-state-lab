import { vi } from 'vitest'
vi.mock('react-plotly.js', () => ({ default: () => null }))
import { afterEach, beforeEach, expect, it } from 'vitest'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import { getAnalysis, getChartView, getPublication, listPublications } from './research'
import views from '../../../../../market_research/tests/fixtures/publication_visualization_v1.json'
let release: () => void
const unauthorized = vi.fn()
beforeEach(() => { unauthorized.mockReset(); release = installRequestBoundary(createRequestBoundary(unauthorized)) })
afterEach(() => { release(); vi.unstubAllGlobals() })
const response = (body: unknown, status = 200) => ({ status, ok: status === 200, json: async () => body }) as Response
it('uses opaque cursor and same-origin credentials, validates response', async () => {
  const fetch = vi.fn().mockResolvedValue(response({ data: [], next_cursor: null }))
  vi.stubGlobal('fetch', fetch)
  await expect(listPublications('a+/=', new AbortController().signal)).resolves.toEqual({ data: [], next_cursor: null })
  expect(fetch.mock.calls[0][0]).toBe('/api/research/publications?after=a%2B%2F%3D')
  expect(fetch.mock.calls[0][1].credentials).toBe('same-origin')
})
it.each(['corrupt', 'inconsistent', 'unsupported_version', 'response_too_large', 'verification_budget_exceeded', 'unavailable'] as const)('preserves safe %s failure', async kind => {
  const status = ['corrupt', 'inconsistent', 'unsupported_version'].includes(kind) ? 409 : kind === 'response_too_large' ? 413 : 503
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind, detail: 'safe', param: null } }, status)))
  await expect(listPublications(null, new AbortController().signal)).rejects.toMatchObject({ kind })
  expect(unauthorized).not.toHaveBeenCalled()
})
it('validates backend View against shared contract', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ data: views[0] })))
  await expect(getChartView('pub', 'view', new AbortController().signal)).resolves.toEqual(views[0])
})
it('rejects malformed successful data', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ data: 'wrong' })))
  await expect(listPublications(null, new AbortController().signal)).rejects.toMatchObject({ kind: 'invalid_response' })
})
it('401 invalidates application boundary; 403 does not', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(response({ error: { kind: 'origin_forbidden', detail: '', param: null } }, 403)).mockResolvedValueOnce(response({ error: { kind: 'authentication_required', detail: '', param: null } }, 401))
  vi.stubGlobal('fetch', fetch)
  await expect(listPublications(null, new AbortController().signal)).rejects.toMatchObject({ kind: 'origin_forbidden' })
  expect(unauthorized).not.toHaveBeenCalled()
  await expect(listPublications(null, new AbortController().signal)).rejects.toMatchObject({ kind: 'authentication_required' })
  expect(unauthorized).toHaveBeenCalledOnce()
})
it('classifies a malformed View payload distinctly from other malformed responses', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ data: { version: 2 } })))
  await expect(getChartView('pub', 'view', new AbortController().signal)).rejects.toMatchObject({ kind: 'invalid_view' })
})

it.each([
  ['list', (s: AbortSignal) => listPublications(null, s)],
  ['manifest', (s: AbortSignal) => getPublication('pub', s)],
  ['analysis', (s: AbortSignal) => getAnalysis('pub', 'analysis', s)],
  ['view', (s: AbortSignal) => getChartView('pub', 'view', s)],
])('%s 401 closes the active application boundary', async (_name, call) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind: 'authentication_required', detail: '', param: null } }, 401)))
  await expect(call(new AbortController().signal)).rejects.toMatchObject({ kind: 'authentication_required' })
  expect(unauthorized).toHaveBeenCalledOnce()
})

it('classifies unreadable successful View JSON as an incompatible View', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status: 200, ok: true, json: async () => { throw new SyntaxError('invalid') } }))
  await expect(getChartView('pub', 'view', new AbortController().signal)).rejects.toMatchObject({ kind: 'invalid_view' })
})
