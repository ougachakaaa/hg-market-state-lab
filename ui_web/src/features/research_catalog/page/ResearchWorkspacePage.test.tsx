import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
    render(<ResearchWorkspacePage openFuturesBasis={vi.fn()} openExplorer={vi.fn()} />)
    const online = screen.getByRole('region', { name: '在线能力发现' })
    await within(online).findByText(descriptor.name)
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch.mock.calls[0][0]).toBe('/api/research/capabilities')
    expect(screen.getByText('仅本地 Python')).toBeTruthy()
    expect(screen.getByText('独立在线页面 · 独立离线报告生成')).toBeTruthy()
    expect(screen.getByText('在线执行入口可用；Provider / Cache 就绪情况未验证')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Generate|Execute|Open report|生成|执行|打开报告/ })).toBeNull()
    fireEvent.click(within(online).getByRole('button', { name: '查看详情' }))
    await within(screen.getByRole('region', { name: '所选研究详情' })).findByText(/live readiness: not_probed/)
    expect(fetch.mock.calls[1][0]).toBe('/api/research/capabilities/trailing_cumulative_return_v1')
    expect(screen.getByText(/此处无 Web 执行表单/)).toBeTruthy()
    expect(screen.getByText(/不是默认值/)).toBeTruthy()
    expect(within(online).getByText('实现：supported')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '完整能力描述（原始字段）' }))
    const raw = await screen.findByText(text => text.startsWith('{') && text.includes('statistics_validator'))
    expect(JSON.parse(raw.textContent!)).toEqual(descriptor)
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('describes local Python and offline report access without a fake link', async () => {
    const openFuturesBasis = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([])))
    render(<ResearchWorkspacePage openFuturesBasis={openFuturesBasis} openExplorer={vi.fn()} />)
    const local = screen.getByRole('region', { name: '本地研究与离线工作流' })
    fireEvent.click(within(local).getAllByRole('button', { name: '查看详情' })[0])
    expect(screen.getByText(/observe_price_segments/)).toBeTruthy()
    fireEvent.click(within(local).getAllByRole('button', { name: '查看详情' })[1])
    expect(screen.getByText(/futures_basis_report.py/)).toBeTruthy()
    expect(screen.getByText(/在线入口可用不代表/)).toBeTruthy()
    expect(screen.queryByRole('link', { name: /report/i })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: '打开 Futures Basis Research' }))
    expect(openFuturesBasis).toHaveBeenCalledOnce()
  })

  it('shows empty online state while keeping local cases and Explorer action', async () => {
    const openExplorer = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([])))
    render(<ResearchWorkspacePage openFuturesBasis={vi.fn()} openExplorer={openExplorer} />)
    await screen.findByText('暂无已发布的在线能力。')
    expect(screen.getByText('Price Segmentation')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '打开研究结果浏览' }))
    expect(openExplorer).toHaveBeenCalledOnce()
  })

  it('retries list and detail failures manually', async () => {
    const fetch = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(reply([descriptor]))
      .mockResolvedValueOnce(error('internal_error', 500)).mockResolvedValueOnce(reply(descriptor))
    vi.stubGlobal('fetch', fetch)
    render(<ResearchWorkspacePage openFuturesBasis={vi.fn()} openExplorer={vi.fn()} />)
    await screen.findByText('在线能力目录暂不可用')
    expect(fetch).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: '重试目录' }))
    const online = screen.getByRole('region', { name: '在线能力发现' })
    await within(online).findByText(descriptor.name)
    fireEvent.click(within(online).getByRole('button', { name: '查看详情' }))
    await screen.findByText('能力详情暂不可用')
    fireEvent.click(screen.getByRole('button', { name: '重试详情' }))
    await within(screen.getByRole('region', { name: '所选研究详情' })).findByText(/live readiness: not_probed/)
    expect(fetch).toHaveBeenCalledTimes(4)
  })

  it('rejects an invalid descriptor instead of presenting invented capability data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply([{ id: 'fabricated' }])))
    render(<ResearchWorkspacePage openFuturesBasis={vi.fn()} openExplorer={vi.fn()} />)
    await screen.findByText('在线能力目录暂不可用')
    expect(screen.queryByText('fabricated')).toBeNull()
  })

  it('aborts a selected detail when switching to a local case', async () => {
    const pending = deferred<Response>()
    let detailSignal: AbortSignal | undefined
    const fetch = vi.fn().mockResolvedValueOnce(reply([descriptor]))
      .mockImplementationOnce((_url, init) => { detailSignal = init.signal; return pending.promise })
    vi.stubGlobal('fetch', fetch)
    render(<ResearchWorkspacePage openFuturesBasis={vi.fn()} openExplorer={vi.fn()} />)
    const online = screen.getByRole('region', { name: '在线能力发现' })
    await within(online).findByText(descriptor.name)
    fireEvent.click(within(online).getByRole('button', { name: '查看详情' }))
    await waitFor(() => expect(detailSignal).toBeDefined())
    fireEvent.click(within(screen.getByRole('region', { name: '本地研究与离线工作流' })).getAllByRole('button', { name: '查看详情' })[0])
    expect(detailSignal?.aborted).toBe(true)
    await act(async () => { pending.resolve(reply(descriptor)) })
    expect(screen.getByText(/observe_price_segments/)).toBeTruthy()
    expect(within(screen.getByRole('region', { name: '所选研究详情' })).queryByText(/live readiness: not_probed/)).toBeNull()
  })
})
