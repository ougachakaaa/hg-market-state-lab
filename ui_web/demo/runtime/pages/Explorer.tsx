import { ResearchExplorerPresentation, useStaticExplorer, validateEmbeddedPublicationSet, type EmbeddedPublicationSetPayload } from '../../../src/features/research_explorer/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { ResultIdentity } from '../results'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => { const payload = b.result as EmbeddedPublicationSetPayload; validateEmbeddedPublicationSet(payload); return payload }
function ExplorerResult({ data, identity }: { data: EmbeddedPublicationSetPayload; identity: ResultIdentity }) {
  const controller = useStaticExplorer(data)
  return <ResearchExplorerPresentation controller={controller} mode="static" sourceDisclosure={`${disclose(identity)} 正式结果的静态阅读；Analysis 与 View 选择仅使用已装载数据。`} />
}
export default function Explorer({ store }: StaticPageProps) {
  return <AsyncContent resource={store.get('publications', adapt)}>{value => <ExplorerResult {...value} />}</AsyncContent>
}
