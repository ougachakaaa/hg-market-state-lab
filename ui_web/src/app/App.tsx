import { Button, Flex, Layout, theme } from 'antd'
import { useState } from 'react'
import OptionChainPage from '../features/mo_option_chain'
import PremiumPlanePage from '../features/mo_option_premium'
import AppUiProvider from './AppUiProvider'

type Feature = 'option-chain' | 'premium-plane'

function ApplicationShell() {
  const [feature, setFeature] = useState<Feature>('option-chain')
  const { token } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Header style={{ height: 'auto', padding: `${token.paddingSM}px ${token.paddingLG}px 0`, background: token.colorBgLayout }}>
        <Flex component="nav" gap="small" wrap aria-label="产品功能导航"
          style={{ width: '100%', maxWidth: 1400, margin: '0 auto' }}>
          <Button type={feature === 'option-chain' ? 'primary' : 'default'}
            aria-pressed={feature === 'option-chain'} onClick={() => setFeature('option-chain')}>
            MO Option Chain
          </Button>
          <Button type={feature === 'premium-plane' ? 'primary' : 'default'}
            aria-pressed={feature === 'premium-plane'} onClick={() => setFeature('premium-plane')}>
            MO Premium Plane
          </Button>
        </Flex>
      </Layout.Header>
      <Layout.Content style={{ width: '100%', maxWidth: 1400, margin: '0 auto', padding: token.paddingLG, boxSizing: 'border-box' }}>
        {feature === 'option-chain' ? <OptionChainPage /> : <PremiumPlanePage />}
      </Layout.Content>
    </Layout>
  )
}

function App() {
  return <AppUiProvider><ApplicationShell /></AppUiProvider>
}

export default App
