import { Alert, Card, Collapse, Descriptions, Flex, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { ImmutableRequest } from '../api/validateResult'
import { STATIC_BASIS_DISCLOSURE } from '../model/basisPresentation'
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
    /** Retained composition input; the Demo notice uses the fixed feature disclaimer. */
    disclosure?: string
    /** Validated source statement for the shared reader. */
    sourceDisclosure?: string
  }

function RequestFacts({ request }: { request: ImmutableRequest }) {
  return <Descriptions size="small" column={{ xs: 1, md: 2 }} items={[
    { key: 'product', label: '品种', children: request.product_code },
    { key: 'window', label: '请求范围（含首尾）', children: `${request.start_date} 至 ${request.end_date}` },
  ]} />
}

function Header({ mode }: { mode: 'production' | 'static' }) {
  return <Flex vertical gap="small">
    <Typography.Title level={2} style={{ margin: 0 }}>Futures Basis Research</Typography.Title>
    <Typography.Text type="secondary">{mode === 'production'
      ? '期货基差研究 · 选择参数、提交 Run，再阅读报告与证据。'
      : '期货基差研究 · 固定 Example 请求与已验证嵌入报告；只读，不执行服务器研究。'}</Typography.Text>
    <Collapse items={[{ key: 'introduction', label: '关于本研究', children:
      <Descriptions size="small" column={1} items={[
        { key: 'purpose', label: '研究目的', children: '观察股指期货相对现货指数的价格偏离，理解不同合约期限下的贴水特征及其历史变化。' },
        { key: 'method', label: '研究方式', children: '基于历史交易日数据，统计并可视化不同期限合约的基差、分布和贴水持续区间。' },
      ]} />,
    }]} />
  </Flex>
}

function StaticView({ state, sourceDisclosure }: { sourceDisclosure?: string; state: StaticFuturesBasisState; disclosure?: string }) {
  return <>
    <Alert showIcon type="warning" title="嵌入研究示例 · 静态只读"
      description={<Typography.Text>{STATIC_BASIS_DISCLOSURE}</Typography.Text>} />
    {state.status === 'invalid'
      ? <Alert showIcon type="error" title="静态研究报告未通过校验"
        description="嵌入的 Producer Reader Payload 或固定请求关联未通过正式契约校验，已拒绝展示；未执行任何 HTTP 请求，也不会回退到在线服务。" />
      : <StaticReport state={state} sourceDisclosure={sourceDisclosure} />}
  </>
}

function StaticReport({ state, sourceDisclosure }: { sourceDisclosure?: string; state: Extract<StaticFuturesBasisState, { status: 'validated' }> }) {
  return <>
    <Card title="固定研究参数" size="small">
      <RequestFacts request={state.data.request} />
    </Card>
    <Report data={state.data.report} sourceDisclosure={sourceDisclosure} mode="demo" sectionNavigation="local" />
  </>
}

export function FuturesBasisPresentation(props: FuturesBasisPresentationProps) {
  if (props.mode === 'static') {
    return <Flex vertical gap="large" style={{ minWidth: 0 }}>
      <Header mode="static" />
      <StaticView state={props.state} disclosure={props.disclosure} sourceDisclosure={props.sourceDisclosure} />
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
