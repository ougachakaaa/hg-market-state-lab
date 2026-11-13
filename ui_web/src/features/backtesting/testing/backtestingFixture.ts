import fixture from '../api/result.fixture.json'
import type { BacktestResult, EmbeddedBacktestResultPayload, ImmutableRequest } from '../api/validateResult'

// Test-only embedded input for D2-F. The Result payload is the existing serialized producer
// regression fixture, reused verbatim with its original 2025-02-17..2025-03-25 request and
// five-session observed window. It is not an official D3 Example, not real market
// performance and not the 2026 target window. Validation must prove the fixed request below
// is exactly the Result's producer request.
const testOnlyResult = fixture as unknown as BacktestResult

export const testOnlyRequest: ImmutableRequest = testOnlyResult.request

export const embeddedBacktestResultPayload: EmbeddedBacktestResultPayload = {
  request: testOnlyRequest,
  result: testOnlyResult,
}

// Negative browser fixture: a fixed request that does not answer the embedded Result.
export const mismatchedBacktestResultPayload: EmbeddedBacktestResultPayload = {
  request: { ...testOnlyRequest, end_date: '2025-03-26' },
  result: testOnlyResult,
}

// Negative browser fixture: the complete Result does not satisfy the published profile.
export const invalidBacktestResultPayload: EmbeddedBacktestResultPayload = {
  request: testOnlyRequest,
  result: { ...structuredClone(testOnlyResult), profile: 'futures_roll_long_result_v0' },
}

export const testOnlyDisclosure =
  'Test-only 静态测试数据 · 非正式 D3 Backtesting Example · 复用既有生产者 Test Fixture（2025-02-17 至 2025-03-25，5 个 CFFEX 交易日）· 非真实市场业绩 · 非 2026 目标窗口 · 未创建服务器 Run · 未执行 Preflight 或 W2 回测。'
