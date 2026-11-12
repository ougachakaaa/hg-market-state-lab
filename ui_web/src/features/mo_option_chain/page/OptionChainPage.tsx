import { useOptionChain } from '../hooks/useOptionChain'
import { OptionChainPresentation } from './OptionChainPresentation'

export default function OptionChainPage() {
  const state = useOptionChain()
  return <OptionChainPresentation state={state}
    query={{ mode: 'production', selectedDate: state.selectedDate, selectDate: state.selectDate }} />
}
