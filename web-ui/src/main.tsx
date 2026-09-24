import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './features/mo_option_chain/index.css'
import App from './features/mo_option_chain/App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
