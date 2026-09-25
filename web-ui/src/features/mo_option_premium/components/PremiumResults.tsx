import { useState } from 'react'
import { Alert, Button, Card, Collapse, Descriptions, Empty, Flex, Space, Table, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import type { PremiumErrorKind, PremiumPlane } from '../api/moOptionPremium'
import { PremiumRequestError } from '../api/moOptionPremium'
import { classifyStrikeRelativeToReference, formatMetric, formatPlaneNumber } from '../model/premiumPlane'
import type { PremiumPlaneProjection, PremiumPlaneRow, SelectedRepresentation } from '../model/premiumPlane'

const errorTitles: Record<PremiumErrorKind, string> = {
  invalid_request: 'Invalid request',
  unsupported_query: 'Unsupported query',
  date_not_available: 'No data for this date',
  premium_plane_unavailable: 'Premium plane unavailable',
}

export function PremiumError({ asOf, priceType, error }: {
  asOf: string
  priceType: string
  error: PremiumRequestError
}) {
  const title = error.kind === 'network' ? 'Cannot reach the data service'
    : error.kind === 'invalid_response' ? 'Invalid data-service response'
      : errorTitles[error.kind]
  return <Alert type="error" showIcon role="alert" title={title} description={<Space orientation="vertical" size={0}>
    <span>{asOf} · {priceType}</span><span>{error.message}</span>
  </Space>} />
}

export function PremiumSummary({ plane }: { plane: PremiumPlane }) {
  return (
    <Card size="small" title={`${plane.observation.value} · ${plane.option_product}`}>
      <Descriptions size="small" column={{ xs: 1, sm: 2, lg: 4 }} items={[
        { key: 'observation', label: 'Observation', children: plane.observation.value },
        { key: 'price-type', label: 'Price type', children: plane.price_type },
        { key: 'underlying', label: 'Underlying', children: plane.underlying.instrument_id },
        { key: 'spot', label: 'Spot', children: formatPlaneNumber(plane.underlying.price) },
      ]} />
    </Card>
  )
}

export function PremiumPlaneTable({ plane, projection, representation }: {
  plane: PremiumPlane
  projection: PremiumPlaneProjection
  representation: SelectedRepresentation
}) {
  if (projection.rows.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No analytical observation for this presentation." />
  }

  const columns: TableColumnsType<PremiumPlaneRow> = [
    {
      key: 'strike', dataIndex: 'strike', fixed: 'left', width: 140, rowScope: 'row',
      title: <Space orientation="vertical" size={0}><span>Strike</span><Typography.Text type="secondary">
        Spot · {formatPlaneNumber(plane.underlying.price)}
      </Typography.Text></Space>,
      render: formatPlaneNumber,
      onCell: (row) => ({ className: classifyStrikeRelativeToReference(row.strike, plane.underlying.price) }),
    },
    ...projection.expiries.map((expiry, index) => ({
      key: expiry.expiry_date,
      width: 180,
      title: <Space orientation="vertical" size={0}>
        <span>{expiry.expiry_date}</span>
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
    scroll={{ x: 'max-content' }} />
}

export function RawResponseInspector({ payload }: { payload: unknown }) {
  const [copyFeedback, setCopyFeedback] = useState('')
  const prettyJson = JSON.stringify(payload, null, 2)

  async function copyJson() {
    try {
      await navigator.clipboard.writeText(prettyJson)
      setCopyFeedback('Copied')
    } catch {
      setCopyFeedback('Copy failed')
    }
  }

  return (
    <Collapse size="small" items={[{
      key: 'raw-response',
      label: 'View raw response',
      children: <Space orientation="vertical" style={{ display: 'flex' }}>
        <Flex align="center" gap="small" wrap>
          <Typography.Text strong>Raw backend response</Typography.Text>
          <Button onClick={() => void copyJson()}>Copy JSON</Button>
          {copyFeedback && <Typography.Text role="status" type={copyFeedback === 'Copied' ? 'success' : 'danger'}>{copyFeedback}</Typography.Text>}
        </Flex>
        <pre className="raw-response-code">{prettyJson}</pre>
      </Space>,
    }]} />
  )
}
