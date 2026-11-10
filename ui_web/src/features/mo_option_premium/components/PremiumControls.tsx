import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import zhCN from 'antd/es/date-picker/locale/zh_CN'
import { Checkbox, Flex, Form, DatePicker, Radio, Select, Space, Typography } from 'antd'
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
    <Flex vertical gap="small" role="group" aria-label="权利金展示设置">
      <Typography.Text type="secondary">展示设置 · 仅调整当前结果</Typography.Text>
      <Flex gap="middle" align="center" role="group" aria-label="期权类型">
        <Typography.Text strong>期权类型</Typography.Text>
        <Radio.Group name="premium-side" aria-label="Option type" optionType="button" buttonStyle="solid" value={optionType}
          onChange={(event) => setOptionType(event.target.value as SelectedOptionType)} options={[
            { value: 'call', label: 'Call' }, { value: 'put', label: 'Put' },
          ]} />
      </Flex>
      <Space orientation="vertical" size="small" role="group" aria-label="指标设置">
        <Typography.Text strong>指标设置</Typography.Text>
        <Flex gap="large" wrap>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>参考标的</Typography.Text>
            <Radio.Group name="premium-reference-basis" aria-label="Reference basis" value={referenceBasis}
              onChange={(event) => setReferenceBasis(event.target.value as SelectedReferenceBasis)} options={[
                { value: 'underlying_spot', label: <span aria-label='Underlying spot'>现货标的</span> },
                { value: 'expiry_futures', label: <span aria-label='Same-expiry futures'>同到期 Futures</span> },
              ]} />
          </Space>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>价值口径</Typography.Text>
            <Radio.Group name="premium-value-basis" aria-label="Calculation basis" value={valueBasis}
              onChange={(event) => setValueBasis(event.target.value as SelectedValueBasis)} options={[
                { value: 'total', label: <span aria-label='Total value'>总价值</span> }, { value: 'time_value', label: <span aria-label='Time value'>时间价值</span> },
              ]} />
          </Space>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>时间标准</Typography.Text>
            <Radio.Group name="premium-time-normalization" aria-label="Time normalization" value={timeNormalization}
              onChange={(event) => setTimeNormalization(event.target.value as SelectedTimeNormalization)} options={[
                { value: 'unannualized', label: <span aria-label='Unannualized'>未年化</span> }, { value: 'annualized', label: <span aria-label='Annualized'>年化</span> },
              ]} />
          </Space>
          <Space orientation="vertical" size="small">
            <Typography.Text strong>表示方式</Typography.Text>
            <Radio.Group name="premium-representation" aria-label="Representation" value={representation}
              onChange={(event) => setRepresentation(event.target.value as SelectedRepresentation)} options={[
                { value: 'points', label: <span aria-label='Points'>点数</span> }, { value: 'yield', label: <span aria-label='Yield'>收益率</span> },
              ]} />
          </Space>
        </Flex>
      </Space>
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
    <Space orientation="vertical" size="small" role="group" aria-label="显示到期日">
      <Typography.Text strong>显示到期日</Typography.Text>
      <Flex gap="small" wrap>{expiries.map((expiry) => (
        <Checkbox key={expiry.expiry_date} checked={selectedSet.has(expiry.expiry_date)}
          disabled={selectedSet.has(expiry.expiry_date) && selectedExpiries.length === 1}
          onChange={() => toggleExpiry(expiry.expiry_date)}>
          {expiry.expiry_date}
        </Checkbox>
      ))}</Flex>
    </Space>
  )
}
