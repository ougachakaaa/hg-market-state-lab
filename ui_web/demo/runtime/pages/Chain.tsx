import { OptionChainPresentation, useOptionChainPresentation, validateOptionChain, type OptionChain } from '../../../src/features/mo_option_chain/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { ResultIdentity } from '../results'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => validateOptionChain(b.result)
function ChainResult({ data, identity }: { data: OptionChain; identity: ResultIdentity }) {
  const state = useOptionChainPresentation(data)
  return <OptionChainPresentation state={{ ...state, page: { status: 'ready', chain: data } }} query={{ mode: 'static', selectedDate: data.target_trade_date, sourceDisclosure: disclose(identity) }} />
}
export default function Chain({ store }: StaticPageProps) {
  return <AsyncContent resource={store.get('chain', adapt)}>{value => <ChainResult {...value} />}</AsyncContent>
}
