import { FileTextOutlined } from '@ant-design/icons'
import { Button, Card, Flex, Typography } from 'antd'
import type { WorkspacePath } from './routeInventory'

export default function DailyDataLanding({ navigate }: { mode?: 'production' | 'static'; navigate: (path: WorkspacePath) => void }) {
  return <Flex vertical gap="large">
    <header>
      <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>数据总览</Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
        查看每日数据产品；完成状态仅表示 Web 页面已交付，不代表数据源已准备完整。
      </Typography.Paragraph>
    </header>
    <Flex gap="middle" wrap>
      <Card title="MO Option Chain" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Text type="success">已完成</Typography.Text>
        <Typography.Paragraph type="secondary">查看期权链价格分布与同到期 Futures 参考。</Typography.Paragraph>
        <Button icon={<FileTextOutlined aria-hidden="true" />} onClick={() => navigate('/data/mo-option-chain')}>打开 MO Option Chain</Button>
      </Card>
      <Card title="MO Premium Plane" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Text type="success">已完成</Typography.Text>
        <Typography.Paragraph type="secondary">查看多维权利金稀疏数值平面。</Typography.Paragraph>
        <Button icon={<FileTextOutlined aria-hidden="true" />} onClick={() => navigate('/data/mo-premium-plane')}>打开 MO Premium Plane</Button>
      </Card>
      <Card title="Futures Calendar Spread" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Text type="success">已完成</Typography.Text>
        <Typography.Paragraph type="secondary">查看指定产品、日期的六组真实合约跨期价差。</Typography.Paragraph>
        <Button icon={<FileTextOutlined aria-hidden="true" />} onClick={() => navigate('/data/futures-calendar-spread')}>打开 Futures Calendar Spread</Button>
      </Card>
    </Flex>
  </Flex>
}
