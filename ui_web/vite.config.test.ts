import { describe, expect, it } from 'vitest'
import type { UserConfig } from 'vite'
import config from './vite.config.ts'

const backendTarget = 'http://127.0.0.1:8011'
const frontendConsumedRoutes = [
  '/auth',
  '/mo-option-chain',
  '/mo-option-premium-plane',
] as const

describe('local development backend routes', () => {
  it.each(frontendConsumedRoutes)('proxies %s to the backend runtime', (route) => {
    const proxy = (config as UserConfig).server?.proxy
    expect(proxy?.[route]).toBe(backendTarget)
  })
  it('rewrites Research API requests without capturing workspace documents', () => {
    const proxy = (config as UserConfig).server?.proxy?.['/api/research']
    expect(proxy).toBeTruthy()
    expect(typeof proxy === 'object' && proxy.target).toBe(backendTarget)
    expect(typeof proxy === 'object' && proxy.rewrite?.('/api/research/publications?after=x')).toBe('/research/publications?after=x')
    expect((config as UserConfig).server?.proxy?.['/research']).toBeUndefined()
  })
})
