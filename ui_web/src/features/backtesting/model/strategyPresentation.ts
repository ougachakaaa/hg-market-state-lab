import type { ImmutableRequest } from '../api/validateResult'

export type StrategyProfile = ImmutableRequest['strategy_profile']
export const strategyLabels = {
  expiry_to_M1_v1: '到期换入次月合约（M0 → M1）',
  expiry_to_Q1_v1: '到期换入首个后续季月合约（M0 → Q1）',
} satisfies Record<StrategyProfile, string>

export const backtestQuestion = '长期持有并按规则展期的股指期货多头，历史毛收益表现能否优于对应现货指数？'

export function strategyExplanation(profile?: StrategyProfile) {
  const target = profile === undefined
    ? '根据所选策略换入当天 M1 或 Q1 合约'
    : profile === 'expiry_to_M1_v1' ? '换入当天 M1（次月）合约' : '换入当天 Q1（首个未被 M0/M1 占用的后续季月）合约'
  return `首个 CFFEX 交易日买入 M1 合约一手，按真实合约代码持仓。相对 Slot 变化不触发交易。在所持合约最后交易日收盘卖出旧合约，并${target}。最后一个回测交易日平仓，不再换入新合约。`
}

// Copy only presentation-bearing fields; event identities and coordinates stay attached.
export function strategyView(view: import('../../../shared/visualization/contractV2').ViewV2) {
  const label = (text: string) => text.replace(/expiry_to_M1_v1|expiry_to_Q1_v1/g,
    value => strategyLabels[value as StrategyProfile])
  const details = (items: { label: string; value: string }[]) => items.map(item => ({ ...item, value: label(item.value) }))
  return {
    ...view,
    layers: view.layers.map(binding => ({ ...binding, label: label(binding.label), layer: {
      ...binding.layer, data: binding.layer.data.map(mark => ({ ...mark, details: details(mark.details) })),
    } })),
    events: view.events.map(event => ({ ...event, label: label(event.label), details: details(event.details) })),
  }
}
