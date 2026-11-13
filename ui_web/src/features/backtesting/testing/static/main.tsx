import { Flex, Typography } from 'antd'
import { createRoot } from 'react-dom/client'
import AppUiProvider from '../../../../app/AppUiProvider'
import { BacktestingPresentation, useStaticBacktesting } from '../../presentation'
import {
  embeddedBacktestResultPayload,
  invalidBacktestResultPayload,
  mismatchedBacktestResultPayload,
  testOnlyDisclosure,
} from '../backtestingFixture'
import '../../../../index.css'

// D2-F verification harness only. It mounts the shared feature presentation with the static
// controller; it is not a second Demo page, not a D3 Example and not the public V1 entry.
export function StaticBacktestingHarness() {
  const invalid = new URLSearchParams(window.location.search).get('invalid')
  const payload = invalid === 'result'
    ? invalidBacktestResultPayload
    : invalid === 'request' ? mismatchedBacktestResultPayload : embeddedBacktestResultPayload
  const state = useStaticBacktesting(payload)
  return <Flex vertical gap="middle" style={{ padding: 24 }}>
    <Typography.Title level={2} style={{ margin: 0, fontSize: 20 }}>D2-F 静态验证入口</Typography.Title>
    <BacktestingPresentation mode="static" state={state} disclosure={testOnlyDisclosure} />
  </Flex>
}

createRoot(document.getElementById('root')!).render(<AppUiProvider><StaticBacktestingHarness /></AppUiProvider>)
