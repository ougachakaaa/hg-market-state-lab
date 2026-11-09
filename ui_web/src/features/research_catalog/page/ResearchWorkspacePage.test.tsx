import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import descriptor from '../api/catalog.fixture.json'
import ResearchWorkspacePage from './ResearchWorkspacePage'

const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const error = (kind: string, status: number) => reply({ error: { kind, detail: 'safe', param: null } }, status)
function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(done => { resolve = done })
  return { promise, resolve }
}
let release: () => void
beforeEach(() => { release = installRequestBoundary(createRequestBoundary(vi.fn())) })
afterEach(() => { cleanup(); release(); vi.unstubAllGlobals() })

describe('Research Workspace catalog', () => {
  it('loads a published descriptor and fetches detail only on selection', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(reply([descriptor])).mockResolvedValueOnce(reply(descriptor))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchWorkspacePage openExplorer={vi.fn()} />)
    const online = screen.getByRole('region', { name: 'Available online' })
    await within(online).findByText(descriptor.name)
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch.mock.calls[0][0]).toBe('/api/research/capabilities')
    expect(screen.getByText('Local / Python only')).toBeTruthy()
    expect(screen.getByText('Local / Python only · Report generation available')).toBeTruthy()
    expect(screen.getByText('Authority / implementation pending: online application')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Generate|Execute|Open report/ })).toBeNull()
    fireEvent.click(within(online).getByRole('button', { name: 'View details' }))
    await screen.findByText(/live readiness: not_probed/)
    expect(fetch.mock.calls[1][0]).toBe('/api/research/capabilities/trailing_cumulative_return_v1')
    expect(screen.getByText(/No Web execution form/)).toBeTruthy()
    expect(screen.getByText(/not a default/)).toBeTruthy()
  })

  it('describes local Python and offline report access without a fake link', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([])))
    render(<ResearchWorkspacePage openExplorer={vi.fn()} />)
    const local = screen.getByRole('region', { name: 'Local and offline' })
    fireEvent.click(within(local).getAllByRole('button', { name: 'View details' })[0])
    expect(screen.getByText(/observe_price_segments/)).toBeTruthy()
    fireEvent.click(within(local).getAllByRole('button', { name: 'View details' })[1])
    expect(screen.getByText(/futures_basis_report.py/)).toBeTruthy()
    expect(screen.getByText(/No report instance is served/)).toBeTruthy()
    expect(screen.queryByRole('link', { name: /report/i })).toBeNull()
  })

  it('shows empty online state while keeping local cases and Explorer action', async () => {
    const openExplorer = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([])))
    render(<ResearchWorkspacePage openExplorer={openExplorer} />)
    await screen.findByText('No published online capabilities.')
    expect(screen.getByText('Price Segmentation')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Open Research Explorer' }))
    expect(openExplorer).toHaveBeenCalledOnce()
  })

  it('retries list and detail failures manually', async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(reply([descriptor]))
      .mockResolvedValueOnce(error('internal_error', 500)).mockResolvedValueOnce(reply(descriptor))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchWorkspacePage openExplorer={vi.fn()} />)
    await screen.findByText('Capability catalog unavailable')
    expect(fetch).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Retry catalog' }))
    const online = screen.getByRole('region', { name: 'Available online' })
    await within(online).findByText(descriptor.name)
    fireEvent.click(within(online).getByRole('button', { name: 'View details' }))
    await screen.findByText('Capability detail unavailable')
    fireEvent.click(screen.getByRole('button', { name: 'Retry detail' }))
    await screen.findByText(/live readiness: not_probed/)
    expect(fetch).toHaveBeenCalledTimes(4)
  })

  it('rejects an invalid descriptor instead of presenting invented capability data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([{ id: 'fabricated' }])))
    render(<ResearchWorkspacePage openExplorer={vi.fn()} />)
    await screen.findByText('Capability catalog unavailable')
    expect(screen.queryByText('fabricated')).toBeNull()
  })

  it('aborts a selected detail when switching to a local case', async () => {
    const pending = deferred<Response>()
    let detailSignal: AbortSignal | undefined
    const fetch = vi.fn().mockResolvedValueOnce(reply([descriptor]))
      .mockImplementationOnce((_url, init) => { detailSignal = init.signal; return pending.promise })
    vi.stubGlobal('fetch', fetch)
    render(<ResearchWorkspacePage openExplorer={vi.fn()} />)
    const online = screen.getByRole('region', { name: 'Available online' })
    await within(online).findByText(descriptor.name)
    fireEvent.click(within(online).getByRole('button', { name: 'View details' }))
    await waitFor(() => expect(detailSignal).toBeDefined())
    fireEvent.click(within(screen.getByRole('region', { name: 'Local and offline' })).getAllByRole('button', { name: 'View details' })[0])
    expect(detailSignal?.aborted).toBe(true)
    pending.resolve(reply(descriptor))
    expect(screen.getByText(/observe_price_segments/)).toBeTruthy()
    expect(screen.queryByText(/live readiness: not_probed/)).toBeNull()
  })
})
