import { ResearchOverviewPresentation, useStaticCatalog, validateEmbeddedCatalog, type EmbeddedCatalogPayload } from '../../../src/features/research_catalog/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { ResultIdentity } from '../results'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => { const payload = b.result as EmbeddedCatalogPayload; validateEmbeddedCatalog(payload); return payload }
function CatalogResult({ data, identity, navigate }: { data: EmbeddedCatalogPayload; identity: ResultIdentity } & Pick<StaticPageProps, 'navigate'>) {
  const controller = useStaticCatalog(data)
  return <ResearchOverviewPresentation controller={controller} mode="static" navigation={{ openExplorer: () => navigate('/research/publications'), openFuturesBasis: () => navigate('/research/futures-basis'), openCalendarSpread: () => navigate('/research/calendar-spread-relative-value') }} sourceDisclosure={disclose(identity)} />
}
export default function Catalog({ store, navigate }: StaticPageProps) {
  return <AsyncContent resource={store.get('catalog', adapt)}>{value => <CatalogResult {...value} navigate={navigate} />}</AsyncContent>
}
