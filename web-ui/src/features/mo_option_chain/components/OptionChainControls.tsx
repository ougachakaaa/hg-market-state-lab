import { Button, Card, Checkbox, ColorPicker, Flex, Form, Input, Space, Typography } from 'antd'
import type { ExpiryGroup } from '../api/moOptionChain'
import type { ExpiryColors } from '../charts/expiryPalette'
import type { SeriesColors } from '../model/presentationState'
import { MIN_STRIKE_HALF_RANGE_POINTS } from '../model/strikeViewport'

export function OptionChainQueryControl({ selectedDate, selectDate }: {
  selectedDate: string
  selectDate: (date: string) => void
}) {
  return (
    <Form layout="vertical">
      <Form.Item label="目标交易日" htmlFor="target-date" style={{ marginBottom: 0 }}>
        <Input id="target-date" type="date" value={selectedDate}
          onChange={(event) => selectDate(event.currentTarget.value)} style={{ maxWidth: 240 }} />
      </Form.Item>
    </Form>
  )
}

export function ExpirySwatches({ colors, hasFutures }: { colors: ExpiryColors; hasFutures: boolean }) {
  return (
    <span className="expiry-swatches" aria-hidden="true">
      <span className="expiry-swatch" style={{ backgroundColor: colors.call }} />
      <span className="expiry-swatch" style={{ backgroundColor: colors.put }} />
      {hasFutures && <span className="expiry-swatch" style={{ backgroundColor: colors.futures }} />}
    </span>
  )
}

export function StrikeViewportControl({ halfRangePoints, shrink, expand }: {
  halfRangePoints: number
  shrink: () => void
  expand: () => void
}) {
  return (
    <Flex align="center" gap="small" wrap role="group" aria-label="行权价视窗半宽">
      <Typography.Text strong>行权价视窗：±{halfRangePoints} 点</Typography.Text>
      <Space.Compact>
        <Button aria-label="缩小行权价视窗" disabled={halfRangePoints === MIN_STRIKE_HALF_RANGE_POINTS}
          onClick={shrink}>−</Button>
        <Button aria-label="扩大行权价视窗" onClick={expand}>+</Button>
      </Space.Compact>
    </Flex>
  )
}

export function ExpirySelector({ expiries, selectedExpiries, palette, toggleExpiry }: {
  expiries: ExpiryGroup[]
  selectedExpiries: string[]
  palette: Record<string, ExpiryColors>
  toggleExpiry: (expiryDate: string) => void
}) {
  const selectedSet = new Set(selectedExpiries)
  return (
    <Card size="small" title="显示到期日">
      <Flex gap="small" wrap>
        {expiries.map((group) => (
          <Checkbox key={group.expiry_date} checked={selectedSet.has(group.expiry_date)}
              disabled={selectedSet.has(group.expiry_date) && selectedExpiries.length === 1}
              onChange={() => toggleExpiry(group.expiry_date)}>
            <ExpirySwatches colors={palette[group.expiry_date]} hasFutures={group.futures !== null} />
            <span>{group.expiry_date}</span>
          </Checkbox>
        ))}
      </Flex>
    </Card>
  )
}

export function SeriesColorControls({ colors, changeColor }: {
  colors: SeriesColors
  changeColor: (side: keyof SeriesColors, color: string) => void
}) {
  return (
    <Card size="small" title="图表颜色">
      <Space size="large" wrap role="group" aria-label="图表颜色">
        {(['call', 'put', 'futures'] as const).map((side) => (
          <Flex key={side} align="center" gap="small">
            <Typography.Text strong>{side === 'call' ? 'Call' : side === 'put' ? 'Put' : 'Futures'}</Typography.Text>
            <ColorPicker value={colors[side]} onChangeComplete={(color) => changeColor(side, color.toHexString())}>
              <Button aria-label={`${side === 'call' ? 'Call' : side === 'put' ? 'Put' : 'Futures'} 颜色`}>
                <span className="series-color-swatch" style={{ backgroundColor: colors[side] }} aria-hidden="true" />
                {colors[side]}
              </Button>
            </ColorPicker>
          </Flex>
        ))}
      </Space>
    </Card>
  )
}
