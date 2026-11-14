// Frontend discovery metadata; completion describes Web entry availability only.
type ResearchStudy = {
  title: string
  description: string
} & ({ status: 'completed'; route: '/research/futures-basis' } | { status: 'incomplete'; route?: never })

export const researchStudies = [
  {
    title: '历史基差研究',
    description: '研究股指期货基差的历史变化、期限结构、分布及持续性，观察不同合约与时间区间的基差特征。',
    status: 'completed',
    route: '/research/futures-basis',
  },
  {
    title: '价格分段研究',
    description: '通过价格序列的重要转折点与分段结构，观察市场走势的方向、幅度和持续时间。',
    status: 'incomplete',
  },
  {
    title: '指数滚动收益研究',
    description: '研究指数在不同交易日窗口下的历史累计收益及其统计分布特征。',
    status: 'incomplete',
  },
] as const satisfies readonly ResearchStudy[]
