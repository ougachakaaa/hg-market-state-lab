import { useCatalog } from '../hooks/useCatalog'
import { ResearchOverviewPresentation } from './ResearchOverviewPresentation'

export default function ResearchWorkspacePage({ openExplorer, openFuturesBasis }: {
  openExplorer: () => void
  openFuturesBasis: () => void
}) {
  const catalog = useCatalog()
  return <ResearchOverviewPresentation controller={catalog} mode="production"
    navigation={{ openExplorer, openFuturesBasis }} />
}
