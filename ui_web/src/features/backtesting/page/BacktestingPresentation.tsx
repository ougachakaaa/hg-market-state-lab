import { Alert, Card, Collapse, Descriptions, Flex, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { BacktestResult, ImmutableRequest } from '../api/validateResult'
import { Result } from '../components/Result'
import { STATIC_BACKTESTING_DISCLOSURE } from '../model/staticPresentation'
import { backtestQuestion, strategyExplanation, strategyLabels, type StrategyProfile } from '../model/strategyPresentation'
import type { StaticBacktestingState } from '../static/useStaticBacktesting'

// One formal Backtesting page presentation. Production supplies only its execution regions
// (query form, preflight, Submit and real Run lifecycle); static composition supplies the
// validated fixed request and Embedded Backtest Result. Neither composition duplicates the
// page or the Result Reader.
export type BacktestingPresentationProps =
  | {
    mode: 'production'
    selectedStrategy?: StrategyProfile
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
    { key: 'product', label: '品种', children: request.product_code },
    { key: 'strategy', label: '策略', children: strategyLabels[request.strategy_profile] },
    { key: 'window', label: '请求范围', children: `${request.start_date} 至 ${request.end_date}` },
  ]} />
}

function Header({ profile }: { profile?: StrategyProfile }) {
  return <header>
    <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>期货展期做多回测</Typography.Title>
    <Collapse items={[{ key: 'about', label: '关于本回测', children: <Descriptions column={1} items={[
      { key: 'purpose', label: '回测目的', children: backtestQuestion },
      { key: 'strategy', label: '策略方式', children: strategyExplanation(profile) },
    ]} /> }]} />
  </header>
}

function StaticView({ state, disclosure, sourceDisclosure }: { sourceDisclosure?: string; state: StaticBacktestingState; disclosure?: string }) {
  return <>
    <Alert showIcon type="warning" title="嵌入回测结果 · 静态只读"
      description={STATIC_BACKTESTING_DISCLOSURE} />
    {disclosure && disclosure !== STATIC_BACKTESTING_DISCLOSURE && <Typography.Text type="secondary">{disclosure}</Typography.Text>}
    {state.status === 'invalid'
      ? <Alert showIcon type="error" title="静态回测结果未通过校验"
        description="嵌入的 Producer Backtest Result、固定请求关联或 V2 View 未通过正式契约校验，已拒绝展示；未执行任何 HTTP 请求，也不会回退到在线服务。" />
      : <StaticResult state={state} sourceDisclosure={sourceDisclosure} />}
  </>
}

function StaticResult({ state, sourceDisclosure }: { sourceDisclosure?: string; state: Extract<StaticBacktestingState, { status: 'validated' }> }) {
  return <>
    <Card title="固定回测参数" size="small">
      <RequestFacts request={state.data.request} />
    </Card>
    <Result key={state.data.request.strategy_profile} data={state.data.result} mode="static" sourceDisclosure={sourceDisclosure} />
  </>
}

export function BacktestingPresentation(props: BacktestingPresentationProps) {
  if (props.mode === 'static') {
    return <Flex vertical gap="large" style={{ minWidth: 0 }}>
      <Header profile={props.state.status === 'validated' ? props.state.data.request.strategy_profile : undefined} />
      <StaticView state={props.state} disclosure={props.disclosure} sourceDisclosure={props.sourceDisclosure} />
    </Flex>
  }
  return <Flex vertical gap="large" style={{ minWidth: 0 }}>
    <Header profile={props.selectedStrategy} />
    <Card title="回测参数" size="small">{props.parameters}</Card>
    <Card title="数据准备状态" size="small">{props.readiness}</Card>
    <Card title="当前 Run 状态" size="small">
      <Flex vertical gap="middle" style={{ minWidth: 0 }}>
        {props.request && <RequestFacts request={props.request} />}
        {props.run}
      </Flex>
    </Card>
    {props.result && <Result key={props.resultKey} data={props.result} />}
  </Flex>
}
