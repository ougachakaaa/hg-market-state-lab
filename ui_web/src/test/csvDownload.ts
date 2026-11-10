import { vi } from 'vitest'

export function readBlobBytes(blob: Blob): Promise<Uint8Array> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer))
    reader.onerror = () => reject(reader.error)
    reader.readAsArrayBuffer(blob)
  })
}

export function captureCsvDownloads() {
  const blobs: Blob[] = []
  const filenames: string[] = []
  // stubGlobal gives each test suite restoration through unstubAllGlobals.
  const create = vi.fn((blob: Blob) => { blobs.push(blob); return `blob:csv-${blobs.length}` })
  const revoke = vi.fn()
  vi.stubGlobal('URL', class extends URL {
    static createObjectURL = create
    static revokeObjectURL = revoke
  })
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
    filenames.push(this.download)
  })
  return {
    blobs, filenames, create, revoke,
    async text(index = blobs.length - 1) {
      return new TextDecoder('utf-8', { ignoreBOM: true }).decode(await readBlobBytes(blobs[index]))
    },
  }
}
