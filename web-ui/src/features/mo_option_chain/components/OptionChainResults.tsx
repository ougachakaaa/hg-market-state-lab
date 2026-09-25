import type { ChainErrorKind, ExpiryGroup, OptionChain, OptionPoint } from '../api/moOptionChain'
import { ChainRequestError } from '../api/moOptionChain'
import type { ExpiryColors } from '../charts/expiryPalette'
import { missingPriceCount } from '../model/combinedChartData'
import { formatPrice } from '../model/priceDisplay'
import { ExpirySwatches } from './OptionChainControls'

const errorTitles: Record<ChainErrorKind, string> = {
  invalid_request: '请求日期或参数无效',
  unsupported_query: '当前不支持此查询',
  date_not_available: '该日期无可用数据',
  option_chain_unavailable: '当前无法生成完整期权链',
  service_not_wired: '数据服务尚未接线',
}

export function OptionChainError({ date, error }: { date: string; error: ChainRequestError }) {
  const title = error.kind === 'network' ? '无法连接数据服务'
    : error.kind === 'invalid_response' ? '数据服务响应异常'
      : errorTitles[error.kind]
  return (
    <section className="message error" role="alert">
      <h2>{title}</h2>
      <p>目标日期：{date}</p>
      {error.kind !== 'network' && error.kind !== 'invalid_response' && <p>{error.message}</p>}
    </section>
  )
}

export function OptionChainSummary({ chain }: { chain: OptionChain }) {
  return (
    <>
      <h2>{chain.target_trade_date} · {chain.option_product}</h2>
      <dl className="facts">
        <div><dt>价格口径</dt><dd>{chain.price_type}</dd></div>
        <div><dt>标的指数</dt><dd>{chain.underlying.instrument_id}</dd></div>
        <div><dt>参考价</dt><dd>{formatPrice(chain.underlying.price)}</dd></div>
        <div><dt>到期日数量</dt><dd>{chain.expiries.length}</dd></div>
      </dl>
    </>
  )
}

function OptionTable({ title, points }: { title: string; points: OptionPoint[] }) {
  return (
    <section className="option-list">
      <h4>{title}</h4>
      <table>
        <thead><tr><th scope="col">合约标识</th><th scope="col">行权价</th><th scope="col">价格</th></tr></thead>
        <tbody>{points.map((point) => (
          <tr key={point.instrument_id}><td>{point.instrument_id}</td><td>{formatPrice(point.strike)}</td><td>{formatPrice(point.price)}</td></tr>
        ))}</tbody>
      </table>
    </section>
  )
}

function ExpirySummary({ group, colors }: { group: ExpiryGroup; colors: ExpiryColors }) {
  const missing = missingPriceCount(group)
  return (
    <section className="expiry" aria-label={`${group.expiry_date} 到期日`}>
      <h3><ExpirySwatches colors={colors} hasFutures={group.futures !== null} />{group.expiry_date}</h3>
      <p className="expiry-counts">Call {group.calls.length} · Put {group.puts.length}</p>
      <p className="chart-reference">{group.futures === null
        ? '无同到期 IM 合约'
        : `Futures：${group.futures.instrument_id} · ${formatPrice(group.futures.price)}`}</p>
      {missing > 0 && <p className="missing-price">{missing} 个合约缺少所选价格，未绘制为散点；可在合约明细中查看。</p>}
      {group.calls.every((point) => point.price === null) && group.puts.every((point) => point.price === null)
        && <p className="chart-empty">该到期日没有可绘制的价格。</p>}
      <details className="contract-details">
        <summary>合约明细</summary>
        <div className="expiry-content"><OptionTable title="Calls" points={group.calls} /><OptionTable title="Puts" points={group.puts} /></div>
      </details>
    </section>
  )
}

export function ExpiryDetails({ groups, palette }: {
  groups: ExpiryGroup[]
  palette: Record<string, ExpiryColors>
}) {
  return (
    <>
      <h3>所选到期日明细</h3>
      {groups.map((group) => <ExpirySummary key={group.expiry_date} group={group} colors={palette[group.expiry_date]} />)}
    </>
  )
}
