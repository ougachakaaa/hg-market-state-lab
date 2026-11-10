import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import zhCN from 'antd/es/date-picker/locale/zh_CN'
import { Card, Checkbox, Flex, Form, DatePicker, Radio, Select, Space, Typography } from 'antd'
import type { PremiumExpiry, PremiumPriceType } from '../api/moOptionPremium'
import type {
  SelectedOptionType,
  SelectedReferenceBasis,
  SelectedRepresentation,
  SelectedTimeNormalization,
  SelectedValueBasis,
} from '../model/premiumPlane'

export function PremiumQueryControls({ selectedDate, priceType, selectDate, selectPriceType }: {
  selectedDate: string
  priceType: PremiumPriceType
  selectDate: (date: string) => void
  selectPriceType: (priceType: PremiumPriceType) => void
}) {
  return (
    <Form layout="vertical" onSubmitCapture={(event) => event.preventDefault()} aria-label="权利金平面查询">
      <Space orientation="vertical" size="small">
        <Flex gap="middle" wrap>
          <Form.Item label="观察日期" htmlFor="premium-as-of" style={{ marginBottom: 0 }}>
            <DatePicker id="premium-as-of" value={selectedDate ? dayjs(selectedDate) : null}
              locale={zhCN} format="YYYY-MM-DD" placeholder="YYYY-MM-DD" preserveInvalidOnBlur
              allowClear
              onChange={(date) => selectDate(date?.isValid() ? date.format('YYYY-MM-DD') : '')}
              style={{ width: 200 }} aria-describedby="premium-query-help" />
          </Form.Item>
          <Form.Item label="价格口径" htmlFor="premium-price-type" style={{ marginBottom: 0 }}>
            <Select id="premium-price-type" aria-label="价格口径" value={priceType} style={{ width: 160 }}
              onChange={(value: PremiumPriceType) => selectPriceType(value)} options={[
                { value: 'open', label: '开盘（Open）' },
                { value: 'high', label: '最高（High）' },
                { value: 'low', label: '最低（Low）' },
                { value: 'close', label: '收盘（Close）' },
              ]} />
          </Form.Item>
        </Flex>
        <Typography.Text type="secondary" id="premium-query-help">选择有效日期后自动加载；更改价格口径会重新查询，清空日期可重置查询。</Typography.Text>
      </Space>
    </Form>
  )
}

export function PremiumPresentationControls({ optionType, referenceBasis, valueBasis, timeNormalization,
  representation, setOptionType, setReferenceBasis, setValueBasis, setTimeNormalization, setRepresentation }: {
  optionType: SelectedOptionType
  referenceBasis: SelectedReferenceBasis
  valueBasis: SelectedValueBasis
  timeNormalization: SelectedTimeNormalization
  representation: SelectedRepresentation
  setOptionType: (value: SelectedOptionType) => void
  setReferenceBasis: (value: SelectedReferenceBasis) => void
  setValueBasis: (value: SelectedValueBasis) => void
  setTimeNormalization: (value: SelectedTimeNormalization) => void
  setRepresentation: (value: SelectedRepresentation) => void
}) {
  return (
    <Flex gap="middle" wrap align="stretch">
      <Card size="small" title="Option type" style={{ flex: '1 1 14rem' }}>
        <Radio.Group name="premium-side" aria-label="Option type" optionType="button" buttonStyle="solid" value={optionType}
          onChange={(event) => setOptionType(event.target.value as SelectedOptionType)} options={[
            { value: 'call', label: 'Call' }, { value: 'put', label: 'Put' },
          ]} />
      </Card>
      <Card size="small" title="Metric settings" style={{ flex: '3 1 42rem' }}>
        <Flex gap="large" wrap>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>Reference basis</Typography.Text>
            <Radio.Group name="premium-reference-basis" aria-label="Reference basis" value={referenceBasis}
              onChange={(event) => setReferenceBasis(event.target.value as SelectedReferenceBasis)} options={[
                { value: 'underlying_spot', label: 'Underlying spot' },
                { value: 'expiry_futures', label: 'Same-expiry futures' },
              ]} />
          </Space>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>Calculation basis</Typography.Text>
            <Radio.Group name="premium-value-basis" aria-label="Calculation basis" value={valueBasis}
              onChange={(event) => setValueBasis(event.target.value as SelectedValueBasis)} options={[
                { value: 'total', label: 'Total value' }, { value: 'time_value', label: 'Time value' },
              ]} />
          </Space>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>Time normalization</Typography.Text>
            <Radio.Group name="premium-time-normalization" aria-label="Time normalization" value={timeNormalization}
              onChange={(event) => setTimeNormalization(event.target.value as SelectedTimeNormalization)} options={[
                { value: 'unannualized', label: 'Unannualized' }, { value: 'annualized', label: 'Annualized' },
              ]} />
          </Space>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>Representation</Typography.Text>
            <Radio.Group name="premium-representation" aria-label="Representation" value={representation}
              onChange={(event) => setRepresentation(event.target.value as SelectedRepresentation)} options={[
                { value: 'points', label: 'Points' }, { value: 'yield', label: 'Yield' },
              ]} />
          </Space>
        </Flex>
      </Card>
    </Flex>
  )
}

export function PremiumExpirySelector({ expiries, selectedExpiries, toggleExpiry }: {
  expiries: PremiumExpiry[]
  selectedExpiries: string[]
  toggleExpiry: (expiryDate: string) => void
}) {
  const selectedSet = new Set(selectedExpiries)
  return (
    <Card size="small" title="Visible expiries">
      <Flex gap="small" wrap>{expiries.map((expiry) => (
        <Checkbox key={expiry.expiry_date} checked={selectedSet.has(expiry.expiry_date)}
          disabled={selectedSet.has(expiry.expiry_date) && selectedExpiries.length === 1}
          onChange={() => toggleExpiry(expiry.expiry_date)}>
          {expiry.expiry_date}
        </Checkbox>
      ))}</Flex>
    </Card>
  )
}
