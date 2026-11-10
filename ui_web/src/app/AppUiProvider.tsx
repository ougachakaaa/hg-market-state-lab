import { ConfigProvider } from 'antd'
import type { PropsWithChildren } from 'react'
import { applicationTheme } from '../shared/ui/theme'

export default function AppUiProvider({ children }: PropsWithChildren) {
  return (
    <ConfigProvider componentSize="small" button={{ autoInsertSpace: false }} theme={applicationTheme}>
      {children}
    </ConfigProvider>
  )
}
