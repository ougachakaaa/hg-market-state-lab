import { readerFixture } from '../report/reader.fixture'
const report = readerFixture()
report.candidate_dates = ['2024-10-18', '2024-10-21']
report.coverage.futures = { requested_units: 2, successful_units: 2, missing_units: 0, pending_units: 0, failed_units: 0, complete: true }
export const fixture = { report }
import type { EmbeddedReportPayload, ImmutableRequest } from '../api/validateResult'

// Independent business-test input; never a Demo dataset.
export const testOnlyRequest: ImmutableRequest = {
  case: 'futures_basis_v1',
  product_code: 'IM',
  start_date: '2024-10-18',
  end_date: '2024-10-21',
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
