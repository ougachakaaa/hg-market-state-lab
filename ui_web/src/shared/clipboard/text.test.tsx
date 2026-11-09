import { StrictMode } from 'react'
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { jsonFence, serializeJson } from './text'
import { useClipboardWrite } from './useClipboardWrite'

function Harness({ payload }: { payload: unknown }) {
  const { copy, pending, feedback } = useClipboardWrite()
  return <><button disabled={pending} onClick={() => void copy(() => serializeJson(payload))}>Copy</button><span role="status">{feedback}</span></>
}

afterEach(() => { cleanup(); Reflect.deleteProperty(navigator, 'clipboard') })

it('preserves a large JSON value and writes the complete text in StrictMode', async () => {
  const payload = { items: Array.from({ length: 12000 }, (_, i) => ({ i, price: i % 2 ? null : 0, id: 'x'.repeat(80) })) }
  const writeText = vi.fn().mockResolvedValue(undefined)
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
  render(<StrictMode><Harness payload={payload} /></StrictMode>)
  expect(writeText).not.toHaveBeenCalled()
  await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Copy' })))
  const expected = JSON.stringify(payload, null, 2)
  expect(expected.length).toBeGreaterThan(1_000_000)
  expect(writeText).toHaveBeenCalledExactlyOnceWith(expected)
  expect(screen.getByRole('status').textContent).toBe('Copied')
})

it('protects Markdown fences without changing JSON containing Markdown characters', () => {
  const json = serializeJson({ id: '```json\n# heading\n`````\n~~~\n**text**', many: '` '.repeat(100000) })
  const fenced = jsonFence(json)
  expect(fenced).toBe('``````json\n' + json + '\n``````')
  expect(JSON.parse(json).id).toContain('`````')
})
