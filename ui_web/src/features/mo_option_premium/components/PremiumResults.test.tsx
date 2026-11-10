import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RawResponseInspector } from './PremiumResults'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  Reflect.deleteProperty(navigator, 'clipboard')
})

describe('RawResponseInspector', () => {
  it.each([
    ['Copied', false],
    ['Copy failed', true],
  ])('copies the complete payload and reports %s', async (feedback, rejects) => {
    const writeText = rejects ? vi.fn().mockRejectedValue(new Error('denied')) : vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
    const payload = { complete: true, nested: { value: 0 } }
    render(<RawResponseInspector payload={payload} />)

    fireEvent.click(screen.getByRole('button', { name: 'View raw response' }))
    fireEvent.click(screen.getByRole('button', { name: 'Copy JSON' }))

    expect((await screen.findByRole('status')).textContent).toBe(feedback)
    expect(writeText).toHaveBeenCalledWith(JSON.stringify(payload, null, 2))
  })
})

it('reports Clipboard unavailability in the Inspector', async () => {
  Reflect.deleteProperty(navigator, 'clipboard')
  render(<RawResponseInspector payload={{ value: null }} />)
  fireEvent.click(screen.getByRole('button', { name: 'View raw response' }))
  fireEvent.click(screen.getByRole('button', { name: 'Copy JSON' }))
  expect((await screen.findByRole('status')).textContent).toBe('Copy failed')
})

it.each([false, true])('does not transfer pending Inspector feedback to a remounted result (reject=%s)', async (rejects) => {
  let finish!: () => void
  let fail!: (error: Error) => void
  const writeText = vi.fn(() => new Promise<void>((resolve, reject) => { finish = resolve; fail = reject }))
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
  const view = render(<RawResponseInspector key="old" payload={{ old: true }} />)
  fireEvent.click(screen.getByRole('button', { name: 'View raw response' }))
  fireEvent.click(screen.getByRole('button', { name: 'Copy JSON' }))
  expect(screen.queryByRole('status')).toBeNull()
  expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Copy JSON' }).disabled).toBe(true)
  view.rerender(<RawResponseInspector key="new" payload={{ current: true }} />)
  fireEvent.click(screen.getByRole('button', { name: 'View raw response' }))
  await act(async () => { if (rejects) fail(new Error('private')); else finish() })
  expect(screen.queryByRole('status')).toBeNull()
  expect(screen.getByRole<HTMLButtonElement>('button', { name: 'Copy JSON' }).disabled).toBe(false)
})
