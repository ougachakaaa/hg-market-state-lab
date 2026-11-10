import { afterEach, expect, it, vi } from 'vitest'
import { downloadText } from './download'
import { captureCsvDownloads, readBlobBytes } from '../../test/csvDownload'

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })

it('downloads exact UTF-8 JSON without BOM and releases resources on the next loop', async () => {
  const capture = captureCsvDownloads()
  const text = JSON.stringify({ text: '中文 🧪', values: [null, 0] }, null, 2)
  downloadText(text, 'unsafe/name_context.json', 'application/json;charset=utf-8')
  expect(capture.filenames).toEqual(['unsafe_name_context.json'])
  expect(capture.blobs[0].type).toBe('application/json;charset=utf-8')
  expect(Array.from(await readBlobBytes(capture.blobs[0]))).toEqual(Array.from(new TextEncoder().encode(text)))
  expect(await capture.text()).toBe(text)
  await vi.waitFor(() => expect(capture.revoke).toHaveBeenCalledWith('blob:csv-1'))
  expect(document.querySelector('a[download]')).toBeNull()
})

it.each(['blob', 'url', 'create', 'append', 'click'])('cleans allocated resources after JSON %s failure', (stage) => {
  const capture = captureCsvDownloads()
  if (stage === 'blob') vi.stubGlobal('Blob', class { constructor() { throw new Error('fail') } })
  if (stage === 'url') capture.create.mockImplementation(() => { throw new Error('fail') })
  if (stage === 'create') vi.spyOn(document, 'createElement').mockImplementation(() => { throw new Error('fail') })
  if (stage === 'append') vi.spyOn(document.body, 'appendChild').mockImplementation(() => { throw new Error('fail') })
  if (stage === 'click') vi.mocked(HTMLAnchorElement.prototype.click).mockImplementation(() => { throw new Error('fail') })
  expect(() => downloadText('{}', 'name.json', 'application/json;charset=utf-8')).toThrow('fail')
  expect(capture.revoke).toHaveBeenCalledTimes(['blob', 'url'].includes(stage) ? 0 : 1)
  expect(document.querySelector('a[download]')).toBeNull()
})
