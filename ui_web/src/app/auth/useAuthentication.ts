import { useCallback, useEffect, useRef, useState } from 'react'
import { createRequestBoundary, installRequestBoundary } from '../../shared/http/protectedRequest'
import { login, logout, me } from './api/auth'
import type { CurrentUser, LoginRequest } from './api/auth'
import { AuthRequestError, authErrorMessage } from './api/authError'

type State =
  | { status: 'checking' | 'anonymous' }
  | { status: 'error'; message: string }
  | { status: 'authenticated'; user: CurrentUser }
  | { status: 'logging_out'; message?: string; pending: boolean }

export function useAuthentication() {
  const [state, setState] = useState<State>({ status: 'checking' })
  const generation = useRef(0)
  const request = useRef<AbortController | null>(null)
  const release = useRef<(() => void) | null>(null)
  const boundary = useRef<ReturnType<typeof createRequestBoundary> | null>(null)

  const begin = useCallback(() => {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    const id = ++generation.current
    return { controller, current: () => id === generation.current && !controller.signal.aborted }
  }, [])

  const authenticated = useCallback((user: CurrentUser) => {
    release.current?.()
    const next = createRequestBoundary(() => {
      ++generation.current
      request.current?.abort()
      setState({ status: 'anonymous' })
    })
    boundary.current = next
    release.current = installRequestBoundary(next)
    setState({ status: 'authenticated', user })
  }, [])

  const check = useCallback(async () => {
    const task = begin()
    try {
      const user = await me(task.controller.signal)
      if (task.current()) authenticated(user)
    } catch (error) {
      if (!task.current()) return
      setState(error instanceof AuthRequestError && error.status === 401
        ? { status: 'anonymous' }
        : { status: 'error', message: authErrorMessage(error) })
    }
  }, [begin, authenticated])

  const dispose = useCallback(() => {
    ++generation.current
    request.current?.abort()
    release.current?.()
  }, [])

  useEffect(() => {
    // Synchronize the server session once per mounted lifecycle; state writes follow await.
    // oxlint-disable-next-line react/set-state-in-effect
    void check()
    return dispose
  }, [check, dispose])

  const signIn = useCallback(async (credentials: LoginRequest) => {
    const task = begin()
    const user = await login(credentials, task.controller.signal)
    if (task.current()) authenticated(user)
  }, [begin, authenticated])

  const signOut = useCallback(async () => {
    boundary.current?.close()
    const task = begin()
    setState({ status: 'logging_out', pending: true })
    try {
      await logout(task.controller.signal)
      if (task.current()) setState({ status: 'anonymous' })
    } catch (error) {
      if (task.current()) setState({ status: 'logging_out', pending: false,
        message: `退出失败，尚未确认服务端 Cookie 已清除。${authErrorMessage(error)}` })
    }
  }, [begin])

  const retryCheck = () => { setState({ status: 'checking' }); return check() }
  return { state, check: retryCheck, signIn, signOut }
}
