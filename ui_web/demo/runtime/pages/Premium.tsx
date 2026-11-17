import { PremiumPlanePresentation, usePremiumPresentation, validatePremiumPlane } from '../../../src/features/mo_option_premium/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { ResultIdentity } from '../results'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => validatePremiumPlane(b.result)
function PremiumResult({ data, identity }: { data: ReturnType<typeof adapt>; identity: ResultIdentity }) {
  const state = usePremiumPresentation(data.plane)
  return <PremiumPlanePresentation state={{ ...state, page: { status: 'ready', ...data } }} query={{ mode: 'static', selectedDate: data.plane.observation.value, priceType: data.plane.price_type, sourceDisclosure: disclose(identity) }} />
}
export default function Premium({ store }: StaticPageProps) {
  return <AsyncContent resource={store.get('premium', adapt)}>{value => <PremiumResult {...value} />}</AsyncContent>
}
