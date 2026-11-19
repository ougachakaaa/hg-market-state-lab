// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { resolveConfig, type UserConfig } from 'vite'
import config from './vite.config.ts'

const backendTarget = 'http://127.0.0.1:8011'
const frontendConsumedRoutes = [
  '/auth',
  '/mo-option-chain',
  '/mo-option-premium-plane',
] as const

describe('local development backend routes', () => {
  it('rejects a non-loopback online development listener', async () => {
    await expect(resolveConfig({ server: { host: '0.0.0.0' } }, 'serve')).rejects.toThrow('127.0.0.1:5173')
  })

  it('rejects a non-loopback preview listener before serving the online proxy', async () => {
    await expect(resolveConfig({ preview: { host: '0.0.0.0' } }, 'serve')).rejects.toThrow('loopback listener')
  })

  it.each(frontendConsumedRoutes)('proxies %s while retaining the browser-facing Host', (route) => {
    const proxy = (config as UserConfig).server?.proxy
    expect(proxy?.[route]).toMatchObject({ target: backendTarget, changeOrigin: false })
  })
  it('rewrites Research API requests without capturing workspace documents', () => {
    const proxy = (config as UserConfig).server?.proxy?.['/api/research']
    expect(proxy).toBeTruthy()
    expect(typeof proxy === 'object' && proxy.target).toBe(backendTarget)
    expect(typeof proxy === 'object' && proxy.changeOrigin).toBe(false)
    expect(typeof proxy === 'object' && proxy.rewrite?.('/api/research/publications?after=x')).toBe('/research/publications?after=x')
    expect((config as UserConfig).server?.proxy?.['/research']).toBeUndefined()
  })
})
