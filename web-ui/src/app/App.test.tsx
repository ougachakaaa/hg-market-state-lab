import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import App from './App'

vi.mock('react-plotly.js', () => ({
  default: () => <div data-testid="plot" />,
}))

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('web application shell', () => {
  it('uses Option Chain as the default and exposes both feature surfaces', () => {
    vi.stubGlobal('fetch', vi.fn())
    render(<App />)

    expect(screen.getByRole('heading', { name: 'MO 期权链' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'MO Option Chain' }).getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    expect(screen.getByRole('heading', { name: 'MO 年化权利金平面' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'MO Premium Plane' }).getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(screen.getByRole('button', { name: 'MO Option Chain' }))
    expect(screen.getByRole('heading', { name: 'MO 期权链' })).toBeTruthy()
  })

  it('keeps feature-local state out of the shell', () => {
    vi.stubGlobal('fetch', vi.fn())
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    fireEvent.change(screen.getByLabelText('价格口径'), { target: { value: 'high' } })
    expect((screen.getByLabelText('价格口径') as HTMLSelectElement).value).toBe('high')

    fireEvent.click(screen.getByRole('button', { name: 'MO Option Chain' }))
    fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    expect((screen.getByLabelText('价格口径') as HTMLSelectElement).value).toBe('close')
  })
})
