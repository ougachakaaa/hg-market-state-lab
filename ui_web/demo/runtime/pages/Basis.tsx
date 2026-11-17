import { FuturesBasisPresentation, validateEmbeddedReport } from '../../../src/features/futures_basis_research/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => validateEmbeddedReport({ request: b.request, report: b.result })
export default function Basis({ store }: StaticPageProps) {
  return <AsyncContent resource={store.get('basis', adapt)}>{({ data, identity }) =>
    <FuturesBasisPresentation mode="static" state={{ status: 'validated', data }} sourceDisclosure={disclose(identity)} />
  }</AsyncContent>
}
