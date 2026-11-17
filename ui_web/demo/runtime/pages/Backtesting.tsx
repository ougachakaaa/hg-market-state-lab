import { useState } from 'react'
import { Flex, Select } from 'antd'
import { BacktestingPresentation, strategyLabels, validateEmbeddedBacktestResult } from '../../../src/features/backtesting/presentation'
import type { Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { StaticPageProps } from './types'
const profiles = ['expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const
const adapt = (b: Bundle) => validateEmbeddedBacktestResult({ request: b.request, result: b.result })
export default function Backtesting({ store }: StaticPageProps) {
  const [strategy, setStrategy] = useState<typeof profiles[number]>('expiry_to_M1_v1')
  return <Flex vertical gap="middle">
    <Select aria-label="已计算策略结果" value={strategy} onChange={setStrategy} options={profiles.map(value => ({ value, label: strategyLabels[value] }))} style={{ width: '100%', maxWidth: 460 }} />
    <AsyncContent key={strategy} resource={store.get(strategy, adapt)}>{({ data, identity }) =>
      <BacktestingPresentation mode="static" state={{ status: 'validated', data }} sourceDisclosure={identity.source.description} />
    }</AsyncContent>
  </Flex>
}
