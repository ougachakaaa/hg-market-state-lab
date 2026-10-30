// A boundary belongs to one authenticated application lifetime. Capturing it at
// request start prevents a late 401 from invalidating a later login.
export function createRequestBoundary(onUnauthorized: () => void) {
  let closed = false
  const pending = new Set<AbortController>()
  return {
    get closed() { return closed },
    pending,
    close() {
      closed = true
      for (const controller of pending) controller.abort()
      pending.clear()
    },
    unauthorized() {
      if (closed) return
      this.close()
      onUnauthorized()
    },
  }
}

type Boundary = ReturnType<typeof createRequestBoundary>
let current: Boundary | undefined

export function installRequestBoundary(boundary: Boundary) {
  if (current !== boundary) current?.close()
  current = boundary
  return () => {
    boundary.close()
    if (current === boundary) current = undefined
  }
}

export async function protectedRequest(url: string, signal?: AbortSignal): Promise<Response> {
  const boundary = current
  if (!boundary || boundary.closed || signal?.aborted) throw new DOMException('Request cancelled', 'AbortError')
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  boundary?.pending.add(controller)
  try {
    const response = await fetch(url, { signal: controller.signal, credentials: 'same-origin' })
    if (controller.signal.aborted || boundary?.closed) throw new DOMException('Request cancelled', 'AbortError')
    if (response.status === 401) boundary?.unauthorized()
    return response
  } finally {
    signal?.removeEventListener('abort', abort)
    boundary?.pending.delete(controller)
  }
}
