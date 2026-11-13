import { DotChartOutlined, TableOutlined } from '@ant-design/icons'
import { Button, Card, Flex, Typography } from 'antd'
import type { WorkspacePath } from './routeInventory'

export default function DailyDataLanding({ navigate }: { navigate: (path: WorkspacePath) => void }) {
  return <Flex vertical gap="large">
    <header>
      <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>数据总览</Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
        查看 MO 数据产品，读取结果后可复制 JSON 或导出数据。
      </Typography.Paragraph>
    </header>
    <Flex gap="middle" wrap>
      <Card title="MO Option Chain" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Paragraph type="secondary">查看期权链价格分布与同到期 Futures 参考。</Typography.Paragraph>
        <Button icon={<DotChartOutlined aria-hidden="true" />} onClick={() => navigate('/data/mo-option-chain')}>打开 MO Option Chain</Button>
      </Card>
      <Card title="MO Premium Plane" style={{ flex: '1 1 280px', minWidth: 0 }}>
        <Typography.Paragraph type="secondary">查看多维权利金稀疏数值平面。</Typography.Paragraph>
        <Button icon={<TableOutlined aria-hidden="true" />} onClick={() => navigate('/data/mo-premium-plane')}>打开 MO Premium Plane</Button>
      </Card>
    </Flex>
  </Flex>
}
