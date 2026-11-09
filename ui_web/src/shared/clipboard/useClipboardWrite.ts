import { useEffect, useRef, useState } from 'react'

// Each successful result owns a mounted instance; cleanup invalidates pending feedback.
export function useClipboardWrite() {
  const [feedback, setFeedback] = useState('')
  const [pending, setPending] = useState(false)
  const operation = useRef(0)
  const busy = useRef(false)

  useEffect(() => () => { operation.current += 1 }, [])

  async function copy(makeText: () => string) {
    if (busy.current) return
    busy.current = true
    const id = ++operation.current
    setPending(true)
    setFeedback('')
    let result = 'Copy failed'
    try {
      await navigator.clipboard.writeText(makeText())
      result = 'Copied'
    } catch {
      // Clipboard availability, permissions and serialization failures share safe feedback.
    }
    if (operation.current !== id) return
    busy.current = false
    setPending(false)
    setFeedback(result)
  }

  return { copy, pending, feedback }
}
