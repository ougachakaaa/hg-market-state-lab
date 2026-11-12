import { useExplorer } from '../hooks/useExplorer'
import { ResearchExplorerPresentation } from './ResearchExplorerPresentation'

export default function ResearchExplorerPage() {
  const explorer = useExplorer()
  return <ResearchExplorerPresentation controller={explorer} mode="production" />
}
