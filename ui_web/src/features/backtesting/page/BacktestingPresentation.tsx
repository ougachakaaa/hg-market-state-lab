import { Alert, Card, Descriptions, Flex, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { BacktestResult, ImmutableRequest } from '../api/validateResult'
import { Result } from '../components/Result'
import { STATIC_BACKTESTING_DISCLOSURE, STATIC_BACKTESTING_SOURCE_NOTE } from '../model/staticPresentation'
import type { StaticBacktestingState } from '../static/useStaticBacktesting'

// One formal Backtesting page presentation. Production supplies only its execution regions
// (query form, preflight, Submit and real Run lifecycle); static composition supplies the
// validated fixed request and Embedded Backtest Result. Neither composition duplicates the
// page or the Result Reader.
export type BacktestingPresentationProps =
  | {
    mode: 'production'
    /** Production query form and explicit Submit feedback. */
    parameters: ReactNode
    /** Production Preflight state. Advisory only; never an execution gate. */
    readiness: ReactNode
    /** Production Run lifecycle: phase, accepted identity, reads, failures and retries. */
    run: ReactNode
    /** Immutable request of the accepted Run; the editable query form is not this identity. */
    request: ImmutableRequest | null
    /** Validated online Result. */
    result?: BacktestResult
    /** Result identity used to reset reader-local state for a different Run. */
    resultKey?: string
  }
  | {
    mode: 'static'
    /** Validation result of the fixed request plus Embedded Backtest Result. */
    state: StaticBacktestingState
    /** Explicit static source statement; defaults to the feature disclosure. */
    disclosure?: string
    /** Validated source statement for the shared reader. */
    sourceDisclosure?: string
  }

function RequestFacts({ request }: { request: ImmutableRequest }) {
  return <Descriptions size="small" column={{ xs: 1, md: 2 }} items={[
    { key: 'product', label: '产品', children: request.product_code },
    { key: 'strategy', label: '策略 Profile', children: request.strategy_profile },
    { key: 'window', label: '请求窗口（含首尾）', children: `${request.start_date} 至 ${request.end_date}` },
    { key: 'case', label: 'Case', children: request.case },
  ]} />
}

function WindowFacts({ request, result }: { request: ImmutableRequest; result: BacktestResult }) {
  return <Card title="请求窗口与实际观测" size="small">
    <Flex vertical gap="small">
      <Descriptions size="small" column={{ xs: 1, md: 2 }} items={[
        { key: 'requested', label: '请求窗口（含首尾）', children: `${request.start_date} 至 ${request.end_date}` },
        { key: 'observed', label: '实际交易观测', children: `${result.window.first_session} 至 ${result.window.last_session}（${result.window.cffex_session_count} 个 CFFEX 交易日）` },
        { key: 'profile', label: 'Result Profile', children: result.profile },
        { key: 'definition', label: 'Definition Version', children: result.definition_version },
      ]} />
      <Typography.Text type="secondary">请求窗口 ≠ 实际观测区间；首尾日期与交易日数来自 Producer Result，浏览器不补齐缺失交易日，也不重新计算 PnL、收益、回撤、Roll 或 Benchmark。</Typography.Text>
    </Flex>
  </Card>
}

function Header({ mode }: { mode: 'production' | 'static' }) {
  return <header>
    <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>期货展期做多回测</Typography.Title>
    <Typography.Paragraph type="secondary">{mode === 'production'
      ? 'Futures Roll Long · 单产品、单策略的理想收盘价历史回测，比较策略毛收益与指数价格基准。'
      : 'Futures Roll Long · 固定 Example 请求与已验证嵌入结果；只读，不执行服务器回测。'}</Typography.Paragraph>
  </header>
}

function StaticView({ state, disclosure, sourceDisclosure }: { sourceDisclosure?: string; state: StaticBacktestingState; disclosure?: string }) {
  return <>
    <Alert showIcon type="warning" title="嵌入回测结果 · 静态只读"
      description={<Flex vertical gap="small" role="note">
        <Typography.Text>{disclosure ?? STATIC_BACKTESTING_DISCLOSURE}</Typography.Text>
        <Typography.Text>{STATIC_BACKTESTING_SOURCE_NOTE}</Typography.Text>
      </Flex>} />
    {state.status === 'invalid'
      ? <Alert showIcon type="error" title="静态回测结果未通过校验"
        description="嵌入的 Producer Backtest Result、固定请求关联或 V2 View 未通过正式契约校验，已拒绝展示；未执行任何 HTTP 请求，也不会回退到在线服务。" />
      : <StaticResult state={state} sourceDisclosure={sourceDisclosure} />}
  </>
}

function StaticResult({ state, sourceDisclosure }: { sourceDisclosure?: string; state: Extract<StaticBacktestingState, { status: 'validated' }> }) {
  return <>
    <Card title="固定回测参数" size="small">
      <Flex vertical gap="small">
        <RequestFacts request={state.data.request} />
        <Typography.Text type="secondary">Example 参数固定，不可编辑、不可提交；本页不会创建服务器 Run，也不会执行 Preflight。</Typography.Text>
      </Flex>
    </Card>
    <WindowFacts request={state.data.request} result={state.data.result} />
    <Alert showIcon type="success" title="Embedded Backtest Result 已通过正式契约校验"
      description="展示成功表示嵌入的 Producer Result 通过正式 Result Profile、Definition Version、Case、固定请求身份与 Returns/Drawdown V2 View 校验；不代表浏览器运行过 W2 Backtest Core，也不代表在线服务、缓存或 Provider 就绪。" />
    <Result data={state.data.result} mode="static" sourceDisclosure={sourceDisclosure} />
  </>
}

export function BacktestingPresentation(props: BacktestingPresentationProps) {
  if (props.mode === 'static') {
    return <Flex vertical gap="large" style={{ minWidth: 0 }}>
      <Header mode="static" />
      <StaticView state={props.state} disclosure={props.disclosure} sourceDisclosure={props.sourceDisclosure} />
    </Flex>
  }
  const request = props.result ? props.request ?? props.result.request : undefined
  return <Flex vertical gap="large" style={{ minWidth: 0 }}>
    <Header mode="production" />
    <Card title="回测参数" size="small">{props.parameters}</Card>
    <Card title="数据准备状态" size="small">{props.readiness}</Card>
    <Card title="当前 Run 状态" size="small">
      <Flex vertical gap="middle" style={{ minWidth: 0 }}>
        {props.request && <RequestFacts request={props.request} />}
        {props.run}
      </Flex>
    </Card>
    {props.result && request && <WindowFacts request={request} result={props.result} />}
    {props.result && <Result key={props.resultKey} data={props.result} />}
  </Flex>
}
