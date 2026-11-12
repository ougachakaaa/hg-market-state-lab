import { FileSearchOutlined, LineChartOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Empty, Flex, List, Skeleton, Tag, Typography } from 'antd'
import { CapabilityDetails } from '../components/CapabilityDetails'
import { LocalCaseDetails } from '../components/LocalCaseDetails'
import { localCases } from '../model/localCases'
import {
  STATIC_CATALOG_DISCLOSURE,
  type ResearchOverviewController,
  type ResearchOverviewMode,
  type ResearchOverviewNavigation,
} from '../model/catalogPresentation'

export function ResearchOverviewPresentation({ controller, mode, navigation, sourceDisclosure }: {
  controller: ResearchOverviewController
  mode: ResearchOverviewMode
  navigation: ResearchOverviewNavigation
  sourceDisclosure?: string
}) {
  const { list, detail, selection } = controller
  const staticMode = mode === 'static'
  const selectedLocal = selection?.kind === 'local' ? localCases.find(item => item.id === selection.id) : undefined
  const selectedOnlineId = selection?.kind === 'online' && list.status === 'success'
    && list.data.some(item => item.id === selection.id) ? selection.id : null

  return <Flex vertical gap="large" style={{ minWidth: 0, overflowWrap: 'anywhere' }}>
    <Flex vertical gap={0}>
      <Typography.Title level={2} style={{ margin: 0 }}>研究总览</Typography.Title>
      <Typography.Paragraph type="secondary">探索研究主题、可用能力与访问方式。研究结果是否发布独立于实现能力。</Typography.Paragraph>
      {staticMode && <Typography.Paragraph type="secondary" role="note" style={{ marginBottom: 0 }}>{sourceDisclosure ?? STATIC_CATALOG_DISCLOSURE}</Typography.Paragraph>}
    </Flex>

    <Card title="描述性研究主题">
      <Flex vertical gap="small">
        <section aria-label="在线能力发现">
          {list.status === 'loading' && <Skeleton active paragraph={{ rows: 2 }} />}
          {list.status === 'error' && (staticMode
            ? <Alert type="error" title="静态能力示例暂不可用" description="嵌入示例读取失败；静态演示不会重试在线请求。" showIcon />
            : <Alert type="error" title="在线能力目录暂不可用" description="未能读取在线列表；本地案例仍可查看。" action={<Button icon={<ReloadOutlined aria-hidden="true" />} onClick={() => controller.retryList?.()}>重试目录</Button>} showIcon />)}
          {list.status === 'invalid' && <Alert type="error" title="静态能力示例无效" description="嵌入的能力列表、详情或 ID 关联未通过正式契约校验，已拒绝展示；未执行在线请求。" showIcon />}
          {list.status === 'success' && (list.data.length === 0
            ? <Empty description={staticMode ? '嵌入的静态能力示例为空；这不代表当前在线服务没有已发布能力。' : '暂无已发布的在线能力。'} />
            : <List rowKey="id" dataSource={list.data} renderItem={item => {
              const selected = selection?.kind === 'online' && selection.id === item.id
              return <List.Item actions={[
                <Button key="details" aria-pressed={selected} type={selected ? 'primary' : 'default'} onClick={() => controller.selectOnline(item.id)}>查看详情</Button>,
              ]}>
                <List.Item.Meta title={<Flex align="center" gap="small" wrap><Typography.Text strong>{item.name}</Typography.Text><Tag>{staticMode ? '嵌入能力示例' : '在线描述发现'}</Tag><Tag>实现：{item.status}</Tag><Tag>live readiness: {item.live_readiness}</Tag></Flex>}
                  description={<><Typography.Text code>{item.id}</Typography.Text><br />{item.purpose}<br />访问路径：{staticMode ? '静态嵌入描述（非在线发现）' : '认证 HTTP 描述读取'}</>} />
              </List.Item>
            }} />)}
        </section>
        <section aria-label="本地研究与离线工作流">
          <List rowKey="id" dataSource={[...localCases]} renderItem={item => {
            const selected = selection?.kind === 'local' && selection.id === item.id
            return <List.Item actions={[
              <Button key="details" aria-pressed={selected} type={selected ? 'primary' : 'default'} onClick={() => controller.selectLocal(item.id)}>查看详情</Button>,
              ...(item.id === 'futures_basis_v1' ? [<Button key="open" type="primary" icon={<LineChartOutlined aria-hidden="true" />} onClick={navigation.openFuturesBasis}>进入历史基差研究</Button>] : []),
            ]}>
              <List.Item.Meta title={<Flex align="center" gap="small" wrap><Typography.Text strong>{item.name}</Typography.Text><Tag>{item.readiness}</Tag>{item.planned && <Tag>{item.planned}</Tag>}</Flex>}
                description={<><Typography.Text code>{item.id}</Typography.Text><br />{item.purpose}<br />访问路径：{item.id === 'price_segmentation_v1' ? '本地 Python' : '独立在线页面 / 本地离线报告'}</>} />
            </List.Item>
          }} />
        </section>
      </Flex>
    </Card>

    {(selectedLocal || selectedOnlineId !== null) && <Card title="所选研究详情" role="region" aria-label="所选研究详情">
      {selectedLocal && <LocalCaseDetails item={selectedLocal} mode={mode} />}
      {selectedOnlineId !== null && <>
        {detail.status === 'loading' && <Skeleton active paragraph={{ rows: 5 }} />}
        {detail.status === 'error' && <Alert type="error" title="能力详情暂不可用" description="未能读取所选能力描述。" action={staticMode ? undefined : <Button icon={<ReloadOutlined aria-hidden="true" />} onClick={() => controller.retryDetail?.()}>重试详情</Button>} showIcon />}
        {detail.status === 'success' && (detail.data.id === selectedOnlineId
          ? <CapabilityDetails capability={detail.data} mode={mode} />
          : <Alert type="error" title="能力身份不匹配" description={staticMode ? '嵌入详情 ID 与所选能力不一致，已拒绝展示。' : undefined} showIcon />)}
        {detail.status === 'missing' && <Alert type="warning" title="静态能力详情未嵌入" description="所选能力在静态示例中没有对应的详情记录；这不表示在线服务缺少该能力，也不会回退请求 HTTP。" showIcon />}
      </>}
    </Card>}

    <Card title="已有研究结果">
      <Flex vertical gap="small" align="start">
        <Typography.Text type="secondary">浏览已发布的 Publications、Analyses、研究证据和 ChartViews。</Typography.Text>
        {staticMode && <Typography.Text type="secondary">静态演示保留导航入口，不读取在线 Publications。</Typography.Text>}
        <Button icon={<FileSearchOutlined aria-hidden="true" />} onClick={navigation.openExplorer}>浏览已发布研究结果</Button>
      </Flex>
    </Card>
  </Flex>
}
