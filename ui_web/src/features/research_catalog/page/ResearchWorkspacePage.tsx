import { useCatalog } from '../hooks/useCatalog'
import { ResearchOverviewPresentation } from './ResearchOverviewPresentation'

export default function ResearchWorkspacePage({ openExplorer, openFuturesBasis, openCalendarSpread }: {
  openExplorer: () => void
  openFuturesBasis: () => void
  openCalendarSpread?: () => void
}) {
  const catalog = useCatalog()
  return <ResearchOverviewPresentation controller={catalog} mode="production"
    navigation={{ openExplorer, openFuturesBasis, openCalendarSpread }} />
}
