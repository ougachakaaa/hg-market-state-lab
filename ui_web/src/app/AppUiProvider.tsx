import { ConfigProvider } from 'antd'
import type { PropsWithChildren } from 'react'
import { applicationTheme } from '../shared/ui/theme'

export default function AppUiProvider({ children }: PropsWithChildren) {
  return (
    <ConfigProvider componentSize="small" theme={applicationTheme}>
      {children}
    </ConfigProvider>
  )
}
