import { Alert, Card, Descriptions, Flex, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { ImmutableRequest } from '../api/validateResult'
import {
  observedCoverage,
  STATIC_BASIS_DISCLOSURE,
  STATIC_BASIS_SOURCE_NOTE,
} from '../model/basisPresentation'
import { Report } from '../report/Report'
import type { ReportData } from '../report/types'
import type { StaticFuturesBasisState } from '../static/useStaticFuturesBasis'

// One formal Futures Basis page presentation. Production supplies only its execution
// region (query form, preflight, Submit and real Run lifecycle); static composition supplies
// the validated fixed request and Embedded Report. Neither composition duplicates the page.
export type FuturesBasisPresentationProps =
  | {
    mode: 'production'
    /** Production execution region: query form, preflight, submit feedback. */
    parameters: ReactNode
    /** Production Run lifecycle region: phase, accepted identity, reads and retries. */
    run: ReactNode
    /** Immutable request of the accepted Run; the editable query form is not this identity. */
    request: ImmutableRequest | null
    /** Validated online Report. */
    report?: ReportData
    /** Report identity used to reset reader-local state for a different Run. */
    reportKey?: string
  }
  | {
    mode: 'static'
    /** Validation result of the fixed request plus Embedded Report. */
    state: StaticFuturesBasisState
    /** Explicit static source statement; defaults to the feature disclosure. */
    disclosure?: string
  }

function RequestFacts({ request }: { request: ImmutableRequest }) {
  return <Descriptions size="small" column={{ xs: 1, md: 2 }} items={[
    { key: 'product', label: '品种', children: request.product_code },
    { key: 'window', label: '请求范围（含首尾）', children: `${request.start_date} 至 ${request.end_date}` },
    { key: 'case', label: '研究 Case', children: request.case },
    { key: 'profile', label: '分析 Profile', children: request.analysis_profile },
  ]} />
}

function Header({ mode }: { mode: 'production' | 'static' }) {
  return <Flex vertical gap="small">
    <Typography.Title level={2} style={{ margin: 0 }}>Futures Basis Research</Typography.Title>
    <Typography.Text type="secondary">{mode === 'production'
      ? '期货基差研究 · 选择参数、提交 Run，再阅读报告与证据。'
      : '期货基差研究 · 固定 Example 请求与已验证嵌入报告；只读，不执行服务器研究。'}</Typography.Text>
  </Flex>
}

function StaticView({ state, disclosure }: { state: StaticFuturesBasisState; disclosure?: string }) {
  return <>
    <Alert showIcon type="warning" title="嵌入研究示例 · 静态只读"
      description={<Flex vertical gap="small" role="note">
        <Typography.Text>{disclosure ?? STATIC_BASIS_DISCLOSURE}</Typography.Text>
        <Typography.Text>{STATIC_BASIS_SOURCE_NOTE}</Typography.Text>
      </Flex>} />
    {state.status === 'invalid'
      ? <Alert showIcon type="error" title="静态研究报告未通过校验"
        description="嵌入的 Producer Reader Payload 或固定请求关联未通过正式契约校验，已拒绝展示；未执行任何 HTTP 请求，也不会回退到在线服务。" />
      : <StaticReport state={state} />}
  </>
}

function StaticReport({ state }: { state: Extract<StaticFuturesBasisState, { status: 'validated' }> }) {
  const coverage = observedCoverage(state.data.report)
  return <>
    <Card title="固定研究参数" size="small">
      <Flex vertical gap="small">
        <RequestFacts request={state.data.request} />
        <Typography.Text type="secondary">Example 参数固定，不可编辑、不可提交；本页不会创建服务器 Run。</Typography.Text>
      </Flex>
    </Card>
    <Card title="请求窗口与实际观测覆盖" size="small">
      <Flex vertical gap="small">
        <Descriptions size="small" column={1} items={[
          { key: 'requested', label: '请求窗口（固定 Example）', children: `${state.data.request.product_code} · ${state.data.request.start_date} 至 ${state.data.request.end_date}` },
          { key: 'observed', label: '实际观测覆盖（Producer）', children: `${coverage.candidateCount} 个候选交易日；${coverage.firstCandidate ?? '无'}..${coverage.lastCandidate ?? '无'}` },
          { key: 'status', label: '报告状态 / 定义版本', children: `${coverage.status} / ${coverage.definitionVersion}` },
          { key: 'profile', label: 'Report Profile', children: coverage.reportProfile },
          { key: 'fingerprint', label: '输入指纹（证据标识）', children: <Typography.Text copyable>{coverage.fingerprint}</Typography.Text> },
          { key: 'coverage', label: '来源 Coverage', children: coverage.complete ? '全部来源 complete' : '存在不完整来源；详见报告 Overview' },
        ]} />
        <Typography.Text type="secondary">请求窗口 ≠ 实际观测覆盖：候选交易日、覆盖率与报告状态来自 Producer Report；浏览器不补齐缺失日期，也不重新计算 Basis、DTE、年化基差率、统计或贴水持续区间。</Typography.Text>
        <Alert showIcon type="success" title="Embedded Report 已通过静态校验"
          description="展示成功表示嵌入报告通过正式契约与固定请求关联校验，不代表浏览器完成了一次服务器研究执行，也不代表在线服务就绪。" />
      </Flex>
    </Card>
    <Report data={state.data.report} mode="demo" sectionNavigation="local" />
  </>
}

export function FuturesBasisPresentation(props: FuturesBasisPresentationProps) {
  if (props.mode === 'static') {
    return <Flex vertical gap="large" style={{ minWidth: 0 }}>
      <Header mode="static" />
      <StaticView state={props.state} disclosure={props.disclosure} />
    </Flex>
  }
  return <Flex vertical gap="large" style={{ minWidth: 0 }}>
    <Header mode="production" />
    <Card title="研究参数" size="small">{props.parameters}</Card>
    <Card title="当前 Run" size="small">
      <Flex vertical gap="middle" style={{ minWidth: 0 }}>
        {props.request && <RequestFacts request={props.request} />}
        {props.run}
      </Flex>
    </Card>
    {props.report && <Report key={props.reportKey} data={props.report} mode="online" />}
  </Flex>
}
