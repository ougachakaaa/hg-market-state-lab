import { LineChartOutlined } from '@ant-design/icons'
import { Button, Card, Col, Flex, Row, Tag, Typography } from 'antd'
import { researchStudies } from '../model/researchStudies'
import {
  STATIC_CATALOG_DISCLOSURE,
  type ResearchOverviewController,
  type ResearchOverviewMode,
  type ResearchOverviewNavigation,
} from '../model/catalogPresentation'

export function ResearchOverviewPresentation({ mode, navigation, sourceDisclosure }: {
  controller: ResearchOverviewController
  mode: ResearchOverviewMode
  navigation: ResearchOverviewNavigation
  sourceDisclosure?: string
}) {
  const staticMode = mode === 'static'

  return <Flex vertical gap="large" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
    <Typography.Title level={2} style={{ margin: 0 }}>研究总览</Typography.Title>
    <Row gutter={[24, 24]}>
      {researchStudies.map(study => <Col key={study.title} xs={24} md={12}>
        <Card style={{ height: '100%' }}>
          <Flex vertical gap="middle" align="start">
            <Flex gap="small" align="center" wrap>
              <Typography.Title level={3} style={{ margin: 0 }}>{study.title}</Typography.Title>
              <Tag>{study.status === 'completed' ? '已完成' : '未完成'}</Tag>
            </Flex>
            <Typography.Paragraph type="secondary" style={{ margin: 0 }}>{study.description}</Typography.Paragraph>
            {study.status === 'completed' && <Button icon={<LineChartOutlined aria-hidden="true" />}
              aria-label="查看历史基差研究" onClick={navigation.openFuturesBasis}>查看研究</Button>}
          </Flex>
        </Card>
      </Col>)}
    </Row>
    <Flex vertical gap="small" role="note">
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>完成状态仅表示独立 Web 页面已开放；不代表数据源就绪、计算成功或研究方法开发完毕。研究内容仅供研究参考。</Typography.Text>
      {staticMode && <Typography.Text type="secondary" style={{ fontSize: 12 }}>{sourceDisclosure ?? STATIC_CATALOG_DISCLOSURE}</Typography.Text>}
    </Flex>
  </Flex>
}
