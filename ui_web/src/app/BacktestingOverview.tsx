import { FileTextOutlined } from '@ant-design/icons'
import { Button, Card, Flex, Typography } from 'antd'
import type { WorkspacePath } from './routeInventory'

export default function BacktestingOverview({ navigate }: { navigate: (path: WorkspacePath) => void }) {
  return <Flex vertical gap="large">
    <Typography.Title level={2} style={{ margin: 0 }}>回测总览</Typography.Title>
    <Card title="期货展期做多回测">
      <Flex vertical gap="middle" align="start">
        <Typography.Text type="success">已完成</Typography.Text>
        <Typography.Paragraph type="secondary" style={{ margin: 0 }}>
          回测股指期货展期做多策略，查看收益、回撤、交易与展期记录。
        </Typography.Paragraph>
        <Button icon={<FileTextOutlined aria-hidden="true" />} onClick={() => navigate('/backtesting/futures-roll-long')}>查看回测</Button>
      </Flex>
    </Card>
    <Typography.Text type="secondary" style={{ fontSize: 12 }}>完成状态仅表示独立 Web 页面已开放；不代表数据已就绪或回测执行成功。</Typography.Text>
  </Flex>
}
