// Presentation summaries trace to the case authorities named in this slice's ARCHITECTURE.md.
// These are local use instructions, never Capability Publication or HTTP response DTOs.
export const localCases = [
  {
    id: 'price_segmentation_v1',
    name: 'Price Segmentation',
    readiness: '仅本地 Python',
    planned: null,
    purpose: '通过重要点与相邻价格分段观察一条完整历史指数日收盘价序列的形态。',
    scope: '显式指定一个规范指数代码、含首尾日期窗口与正 epsilon；以收盘价、自然对数拟合和交易时段时间进行观察。',
    output: '重要点、相邻分段、诊断与保留的输入证据。',
    access: 'Python: market_research.descriptive.cases.price_segmentation.observe_price_segments(SegmentationRequest(...))',
    note: '可能获取来源事实。没有 Capability Publication、HTTP 端点或在线执行界面。',
  },
  {
    id: 'futures_basis_v1',
    name: 'Futures Basis Research (R01-A)',
    readiness: '独立在线页面 · 独立离线报告生成',
    planned: '在线执行入口可用；Provider / Cache 就绪情况未验证',
    purpose: '描述历史同日期货基差、相对期限结构、分布与持续性。',
    scope: '显式指定 IM、IC、IF 或 IH 产品及含首尾日期窗口。在线执行使用服务端标准 profile；离线生成需要显式统计参数。',
    output: '在线 Run 状态与交互报告；独立生成的自包含离线 HTML 及相邻证据。',
    access: '从仓库根目录执行 poetry run python market_research/scripts/futures_basis_report.py，显式指定产品、日期、统计参数和新输出目录；在本地打开生成的 report.html。',
    note: '在独立 Futures Basis Research 页面提交在线 Run。离线报告仍在本地独立生成。在线入口可用不代表实际 Provider / Cache 已就绪。',
  },
] as const
