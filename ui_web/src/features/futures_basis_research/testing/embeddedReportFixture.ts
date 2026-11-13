import fixture from '../../../demo/futures_basis/report.v1.json'
import type { EmbeddedReportPayload, ImmutableRequest } from '../api/validateResult'

// Test-only embedded input for D2-E. The report payload is the committed V1 synthetic
// fixture, reused verbatim with its original 2024 window and profile. It is not an official
// D3 Example, not the 2026 target window, not current market data and not newly executed
// research. The fixed request below is the Example's declared identity; validation must
// prove it matches the report observation.
export const testOnlyRequest: ImmutableRequest = {
  case: 'futures_basis_v1',
  product_code: 'IM',
  start_date: '2024-09-02',
  end_date: '2024-10-31',
  analysis_profile: 'r01a_standard_v1',
}

export const embeddedReportPayload: EmbeddedReportPayload = {
  request: testOnlyRequest,
  report: fixture.report,
}

// Negative browser fixture: a deliberately mismatched fixed request. It is displayed only
// as a rejected static payload, never as a valid report or a claimed target window.
export const mismatchedReportPayload: EmbeddedReportPayload = {
  request: { ...testOnlyRequest, start_date: '2024-09-03' },
  report: fixture.report,
}

export const testOnlyDisclosure =
  '静态测试数据 · 非正式 D3 Research Example · 固定 2024 Synthetic Fixture 请求 · 未创建服务器 Run · 未执行 Preflight 或研究 · 不代表当前市场数据或在线服务状态。'
