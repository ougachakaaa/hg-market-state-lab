import Ajv2020 from 'ajv/dist/2020.js'
import openApi from './auth.openapi.json'
import type { components, operations } from './auth.generated'
import { AuthRequestError } from './authError'

export type RegisterRequest = operations['register_auth_user']['requestBody']['content']['application/json']
export type RegisterResponse = operations['register_auth_user']['responses'][202]['content']['application/json']
export type LoginRequest = operations['login_auth_user']['requestBody']['content']['application/json']
export type LoginResponse = operations['login_auth_user']['responses'][200]['content']['application/json']
export type CurrentUser = operations['get_auth_user']['responses'][200]['content']['application/json']
export type LogoutResponse = operations['logout_auth_user']['responses'][204]['content']
export type AuthErrorResponse = components['schemas']['AuthErrorResponse']

const ajv = new Ajv2020({ strictSchema: false })
const validateIdentity = ajv.compile({ ...openApi.components.schemas.ActiveIdentity, components: openApi.components })
const validateAccepted = ajv.compile(openApi.components.schemas.Accepted)
const validateError = ajv.compile({ ...openApi.components.schemas.AuthErrorResponse, components: openApi.components })

async function request(path: string, method: 'GET' | 'POST', signal?: AbortSignal, body?: LoginRequest) {
  let response: Response
  try {
    response = await fetch(`/auth/${path}`, {
      method, signal, credentials: 'same-origin', cache: 'no-store',
      ...(body ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new AuthRequestError('network')
  }
  if (response.status === 204 && path === 'logout') return undefined
  let payload: unknown
  try { payload = await response.json() } catch { /* status remains authoritative */ }
  if (!response.ok) {
    throw new AuthRequestError(response.status, response.headers.get('Retry-After'),
      validateError(payload) ? payload as AuthErrorResponse : undefined)
  }
  if ((response.status === 202 && path === 'register' && validateAccepted(payload)) ||
      (response.status === 200 && (path === 'login' || path === 'me') && validateIdentity(payload))) return payload
  throw new AuthRequestError('invalid_response')
}

export const register = (body: RegisterRequest, signal?: AbortSignal) =>
  request('register', 'POST', signal, body) as Promise<RegisterResponse>
export const login = (body: LoginRequest, signal?: AbortSignal) =>
  request('login', 'POST', signal, body) as Promise<LoginResponse>
export const me = (signal?: AbortSignal) => request('me', 'GET', signal) as Promise<CurrentUser>
export const logout = (signal?: AbortSignal) => request('logout', 'POST', signal) as Promise<LogoutResponse>
