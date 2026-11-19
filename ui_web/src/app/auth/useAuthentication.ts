import { useCallback, useEffect, useRef, useState } from 'react'
import { createRequestBoundary, installRequestBoundary } from '../../shared/http/protectedRequest'
import { getMode, login, logout, me } from './api/auth'
import type { CurrentUser, LoginRequest } from './api/auth'
import { AuthRequestError, authErrorMessage } from './api/authError'

type State =
  | { status: 'checking' | 'anonymous' }
  | { status: 'error'; message: string }
  | { status: 'local' }
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

  const openWorkspace = useCallback((workspace: Extract<State, { status: 'local' | 'authenticated' }>) => {
    release.current?.()
    const next = createRequestBoundary(() => {
      ++generation.current
      request.current?.abort()
      setState(workspace.status === 'local'
        ? { status: 'error', message: '本地模式的业务请求意外返回 401，请重试访问检查。' }
        : { status: 'anonymous' })
    })
    boundary.current = next
    release.current = installRequestBoundary(next)
    setState(workspace)
  }, [])

  const check = useCallback(async () => {
    const task = begin()
    let checkingSession = false
    try {
      const mode = await getMode(task.controller.signal)
      if (!task.current()) return
      if (mode === 'local') {
        openWorkspace({ status: 'local' })
        return
      }
      checkingSession = true
      const user = await me(task.controller.signal)
      if (task.current()) openWorkspace({ status: 'authenticated', user })
    } catch (error) {
      if (!task.current()) return
      setState(checkingSession && error instanceof AuthRequestError && error.status === 401
        ? { status: 'anonymous' }
        : { status: 'error', message: checkingSession ? authErrorMessage(error) : '无法确认工作区访问模式，请重试。' })
    }
  }, [begin, openWorkspace])

  const dispose = useCallback(() => {
    ++generation.current
    request.current?.abort()
    release.current?.()
  }, [])

  useEffect(() => {
    // Discover the access mode once per mounted lifecycle; state writes follow await.
    // oxlint-disable-next-line react/set-state-in-effect
    void check()
    return dispose
  }, [check, dispose])

  const signIn = useCallback(async (credentials: LoginRequest) => {
    const task = begin()
    const user = await login(credentials, task.controller.signal)
    if (task.current()) openWorkspace({ status: 'authenticated', user })
  }, [begin, openWorkspace])

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
