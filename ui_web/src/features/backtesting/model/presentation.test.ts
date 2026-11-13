import { expect, it } from 'vitest'
import { credentialAction, failurePresentation, readinessPresentation } from './presentation'

it('requires the exact confirmed credential signal and preserves historical fallback', () => {
 const failure = { stage: 'ensure', category: 'upstream_operation', dependency: 'calendar_cffex', reason: 'credential_missing' } as const
 expect(failurePresentation('FAILED', failure)).toEqual({ title: '行情数据获取失败', description: '无法获取 CFFEX 交易日历，因为后端未配置 Tushare Token。', action: credentialAction })
 for (const other of [{ ...failure, stage: 'export' as const }, { ...failure, reason: 'operation_unavailable' }, { ...failure, reason: 'future_reason' }]) expect(failurePresentation('FAILED', other).description).not.toContain('未配置')
 expect(failurePresentation('INTERRUPTED', failure).description).toContain('未生成成功结果')
 expect(failurePresentation('FAILED').title).toBe('回测执行失败')
})
it('uses dataset target units and explains unknown without claiming missing data', () => {
 for (const [dependency, unit] of [['calendar_cffex', '自然日'], ['futures', '产品×日期'], ['index', '指数×日期']] as const) {
  const result = readinessPresentation({ dependency, state: 'incomplete', reason: 'cache_incomplete', coverage: { requested_units: 43, successful_units: 0, missing_units: 43, pending_units: 0, failed_units: 0, complete: false } })
  expect(result.coverage).toBe(`已缓存 0 / 43 个${unit}目标`)
 }
 const unknown = readinessPresentation({ dependency: 'futures', state: 'unknown', reason: 'calendar_target_unknown', coverage: null })
 expect(unknown.label).toBe('暂无法判断'); expect(unknown.coverage).toBeUndefined()
 expect(unknown.description).toContain('暂无法确定')
})

it('identifies incomplete dependencies and safely maps internal and historical reasons', () => {
 const failure = { stage: 'export', category: 'incomplete_input', dependency: 'calendar_sse', reason: 'final_export_incomplete' } as const
 expect(failurePresentation('FAILED', failure).description).toContain('SSE 交易日历')
 expect(failurePresentation('FAILED', { ...failure, category: 'internal_failure', reason: 'internal_failure' }).description).toBe('回测执行失败。请查看技术详情或联系维护人员。')
 expect(failurePresentation('FAILED', { ...failure, category: 'invalid_public_input', reason: 'historical' }).description).not.toContain('historical')
})
