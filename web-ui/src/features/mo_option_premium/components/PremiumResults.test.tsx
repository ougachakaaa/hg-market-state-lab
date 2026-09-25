import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RawResponseInspector } from './PremiumResults'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
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

    fireEvent.click(screen.getByRole('button', { name: 'Copy JSON' }))

    expect((await screen.findByRole('status')).textContent).toBe(feedback)
    expect(writeText).toHaveBeenCalledWith(JSON.stringify(payload, null, 2))
  })
})
