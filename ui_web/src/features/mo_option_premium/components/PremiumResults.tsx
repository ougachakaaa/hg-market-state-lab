import { CopyOutlined } from '@ant-design/icons'
import { Alert, Button, Collapse, Empty, Flex, Space, Table, Typography, theme } from 'antd'
import type { TableColumnsType } from 'antd'
import { serializeJson } from '../../../shared/clipboard/text'
import { useClipboardWrite } from '../../../shared/clipboard/useClipboardWrite'
import type { PremiumPlane } from '../api/moOptionPremium'
import { PremiumRequestError } from '../api/moOptionPremium'
import { classifyStrikeRelativeToReference, formatMetric, formatPlaneNumber } from '../model/premiumPlane'
import type { PremiumPlaneProjection, PremiumPlaneRow, SelectedRepresentation } from '../model/premiumPlane'

const errorTitles: Partial<Record<PremiumRequestError['kind'], string>> = {
  invalid_request: '请求日期或参数无效',
  unsupported_query: '当前不支持此查询',
  date_not_available: '该日期无可用数据',
  premium_plane_unavailable: '当前无法生成完整权利金平面',
}

export function PremiumError({ asOf, priceType, error }: {
  asOf: string
  priceType: string
  error: PremiumRequestError
}) {
  const title = error.kind === 'network' ? '无法连接数据服务'
    : error.kind === 'invalid_response' ? '数据服务响应异常'
      : errorTitles[error.kind] ?? '数据服务访问失败'
  return <Alert type="error" showIcon role="alert" title={title} description={<Space orientation="vertical" size={0}>
    <span>观察日期：{asOf} · {priceType}</span>
    {error.kind !== 'network' && error.kind !== 'invalid_response' && <span>{error.message}</span>}
    <span>请检查日期或数据服务；恢复后可清空日期并重新选择。</span>
  </Space>} />
}

export function PremiumSummary({ plane }: { plane: PremiumPlane }) {
  return (
    <Space size="middle" wrap>
      <Typography.Text strong>{plane.option_product} · {plane.underlying.instrument_id} · Spot {formatPlaneNumber(plane.underlying.price)}</Typography.Text>
      <Typography.Text type="secondary">{plane.expiries.length} 个到期日</Typography.Text>
    </Space>
  )
}

export function PremiumPlaneTable({ plane, projection, representation }: {
  plane: PremiumPlane
  projection: PremiumPlaneProjection
  representation: SelectedRepresentation
}) {
  if (projection.rows.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前选择下无 analytical observation；可调整期权类型或显示到期日。" />
  }

  const columns: TableColumnsType<PremiumPlaneRow> = [
    {
      key: 'strike', dataIndex: 'strike', fixed: 'left', width: 140, align: 'right', rowScope: 'row',
      title: <Space orientation="vertical" size={0}><span>Strike</span><Typography.Text type="secondary">
        Spot · {formatPlaneNumber(plane.underlying.price)}
      </Typography.Text></Space>,
      render: formatPlaneNumber,
      onCell: (row) => ({ className: classifyStrikeRelativeToReference(row.strike, plane.underlying.price) }),
    },
    ...projection.expiries.map((expiry, index) => ({
      key: expiry.expiry_date,
      width: 180,
      align: 'right' as const,
      title: <Space orientation="vertical" size={0}>
        <Typography.Text strong>{expiry.expiry_date}</Typography.Text>
        <Typography.Text type="secondary">DTE {expiry.dte}</Typography.Text>
        <Typography.Text type="secondary">{expiry.futures === null
          ? 'No eligible futures reference'
          : `${expiry.futures.instrument_id} · ${formatPlaneNumber(expiry.futures.price)}`}</Typography.Text>
      </Space>,
      render: (_value: unknown, row: PremiumPlaneRow) => {
        const cell = row.cells[index]
        if (cell.kind === 'absent') return null
        if (cell.kind === 'unavailable') return '—'
        return formatMetric(cell.value, representation)
      },
      onCell: (row: PremiumPlaneRow) => {
        const cell = row.cells[index]
        const ariaLabel = cell.kind === 'absent' ? `${expiry.expiry_date} no Point`
          : cell.kind === 'unavailable' ? `${expiry.expiry_date} metric unavailable` : undefined
        return {
          className: classifyStrikeRelativeToReference(row.strike, expiry.futures?.price ?? null),
          'aria-label': ariaLabel,
        }
      },
    })),
  ]

  return <Table className="premium-table" size="small" bordered columns={columns}
    dataSource={projection.rows} rowKey={(row) => String(row.strike)} pagination={false}
    scroll={{ x: 'max-content', y: 'clamp(320px, 52vh, 600px)' }} />
}

export function RawResponseInspector({ payload }: { payload: unknown }) {
  const { copy, pending, feedback: copyFeedback } = useClipboardWrite()
  const prettyJson = serializeJson(payload)
  const { token } = theme.useToken()

  return (
    <Collapse size="small" items={[{
      key: 'raw-response',
      label: 'View raw response',
      children: <Space orientation="vertical" style={{ display: 'flex' }}>
        <Flex align="center" gap="small" wrap>
          <Typography.Text strong>Raw backend response</Typography.Text>
          <Button icon={<CopyOutlined aria-hidden="true" />} disabled={pending} onClick={() => void copy(() => serializeJson(payload))}>Copy JSON</Button>
          {copyFeedback && <Typography.Text role="status" type={copyFeedback === 'Copied' ? 'success' : 'danger'}>{copyFeedback}</Typography.Text>}
        </Flex>
        <pre className="raw-response-code" style={{ background: token.colorBgLayout, color: token.colorText }}>{prettyJson}</pre>
      </Space>,
    }]} />
  )
}
