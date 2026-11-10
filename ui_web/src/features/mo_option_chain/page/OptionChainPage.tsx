import { Empty, Flex, Space, Spin, Typography } from 'antd'
import { OptionChainCopyActions } from '../components/OptionChainCopyActions'
import { OptionChainQueryControl } from '../components/OptionChainControls'
import { OptionChainError, OptionChainSummary } from '../components/OptionChainResults'
import { OptionChainVisualization } from '../components/OptionChainVisualization'
import { useOptionChain } from '../hooks/useOptionChain'

export default function OptionChainPage() {
  const state = useOptionChain()

  return (
    <div className="option-chain-page">
      <Space orientation="vertical" size="small" style={{ display: 'flex', minWidth: 0 }}>
        <header>
          <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>MO 期权链</Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>选择交易日，查看中证 1000 指数参考价与各到期日的期权合约。</Typography.Paragraph>
        </header>
        <OptionChainQueryControl selectedDate={state.selectedDate} selectDate={state.selectDate} />

        {state.page.status === 'idle' && <div role="status"><Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择观察日期，选择后自动加载。" /></div>}
        {state.page.status === 'loading' && <Flex gap="small" align="center" role="status" aria-live="polite" aria-busy="true"><Spin size="small" />正在加载 {state.page.date} 的期权链…</Flex>}
        {state.page.status === 'error' && <OptionChainError date={state.page.date} error={state.page.error} />}
        {state.page.status === 'success' && state.xDomain !== null && (
          <section aria-label="期权链结果">
            <Space orientation="vertical" size="small" style={{ display: 'flex', minWidth: 0 }}>
              <Typography.Text type="secondary" role="status" aria-live="polite">已加载 {state.page.chain.target_trade_date} · {state.page.chain.price_type}</Typography.Text>
              <Flex gap="small" wrap align="center" justify="space-between">
                <OptionChainSummary chain={state.page.chain} />
                <OptionChainCopyActions chain={state.page.chain} />
              </Flex>
              {state.page.chain.expiries.length === 0
                ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该期权链没有到期日。" />
                : <OptionChainVisualization chain={state.page.chain} selectedExpiries={state.selectedExpiries}
                    selectedSet={state.selectedSet} selectedGroups={state.selectedGroups} xDomain={state.xDomain}
                    halfRangePoints={state.strikeHalfRangePoints} shrink={state.shrinkViewport} expand={state.expandViewport}
                    seriesColors={state.seriesColors} toggleExpiry={state.toggleExpiry}
                    changeSeriesColor={state.changeSeriesColor} />}
            </Space>
          </section>
        )}
      </Space>
    </div>
  )
}
