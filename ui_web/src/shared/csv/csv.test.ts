import { afterEach, describe, expect, it, vi } from 'vitest'
import { downloadCsv, safeCsvFilename, serializeCsv } from './csv'
import { captureCsvDownloads, readBlobBytes } from '../../test/csvDownload'

afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('CSV scalar and record encoding', () => {
  it('encodes BOM, headers, CRLF, Unicode, null and unrounded numeric facts', () => {
    expect(serializeCsv(['text', 'nil', 'zero', 'negative', 'precise', 'present'], [
      ['中文', null, 0, -3.45, 0.1234567890123456, false],
    ])).toBe('\uFEFFtext,nil,zero,negative,precise,present\r\n中文,null,0,-3.45,0.1234567890123456,false\r\n')
    expect(serializeCsv(['only'], [])).toBe('\uFEFFonly\r\n')
  })
  it('quotes comma, doubles quotes, and preserves embedded CR and LF', () => {
    expect(serializeCsv(['h,1', 'h"2', 'h3'], [['a,b', 'say "yes"', 'a\r\nb\rc\nd']]))
      .toBe('\uFEFF"h,1","h""2",h3\r\n"a,b","say ""yes""","a\r\nb\rc\nd"\r\n')
  })
  it.each(['=1+1', '+SUM(A1)', '-12', '@SUM(A1)', '\tvalue', '\rvalue', '\nvalue', '  =1', '\u0000+1', '\u007f@x', '\u00a0-1'])('protects risky text %j before quoting', (value) => {
    const encoded = /[",\r\n]/.test(value) ? `"'${value.replaceAll('"', '""')}"` : `'${value}`
    expect(serializeCsv(['text'], [[value]])).toBe(`\uFEFFtext\r\n${encoded}\r\n`)
  })
  it('preserves ordinary text, numeric negatives and all 20000 rows', () => {
    const rows = Array.from({ length: 20000 }, (_, i) => ['MO-C', -i])
    const csv = serializeCsv(['id', 'value'], rows)
    expect(csv.startsWith('\uFEFFid,value\r\nMO-C,0\r\n')).toBe(true)
    expect(csv.endsWith('MO-C,-19999\r\n')).toBe(true)
    expect(csv.split('\r\n')).toHaveLength(20002)
    expect(() => serializeCsv(['a'], [[1, 2]])).toThrow('width')
  })
  it('replaces unsafe filename characters', () => {
    expect(safeCsvFilename('mo/\\<>:"|?*\u0000.csv')).toBe('mo__________.csv')
    expect(safeCsvFilename('name. ')).toBe('name_')
  })
})

describe('CSV browser download', () => {
  it('downloads one UTF-8 Blob with BOM and releases resources on the next loop', async () => {
    const capture = captureCsvDownloads()
    const csv = serializeCsv(['名称'], [['数据']])
    downloadCsv(csv, 'unsafe/name.csv')
    expect(capture.create).toHaveBeenCalledTimes(1)
    expect(capture.filenames).toEqual(['unsafe_name.csv'])
    expect(capture.blobs[0].type).toBe('text/csv;charset=utf-8')
    expect(Array.from((await readBlobBytes(capture.blobs[0])).slice(0, 3))).toEqual([239, 187, 191])
    expect(await capture.text()).toBe(csv)
    await vi.waitFor(() => expect(capture.revoke).toHaveBeenCalledWith('blob:csv-1'))
    expect(document.querySelector('a[download]')).toBeNull()
  })
  it.each(['url', 'create', 'append', 'click'])('cleans allocated resources after %s failure', (stage) => {
    const capture = captureCsvDownloads()
    if (stage === 'url') capture.create.mockImplementation(() => { throw new Error('fail') })
    if (stage === 'create') vi.spyOn(document, 'createElement').mockImplementation(() => { throw new Error('fail') })
    if (stage === 'append') vi.spyOn(document.body, 'appendChild').mockImplementation(() => { throw new Error('fail') })
    if (stage === 'click') vi.mocked(HTMLAnchorElement.prototype.click).mockImplementation(() => { throw new Error('fail') })
    expect(() => downloadCsv('csv', 'name.csv')).toThrow('fail')
    expect(capture.revoke).toHaveBeenCalledTimes(stage === 'url' ? 0 : 1)
    expect(document.querySelector('a[download]')).toBeNull()
  })
})
