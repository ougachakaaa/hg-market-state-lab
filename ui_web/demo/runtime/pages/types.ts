import type { WorkspacePath } from '../../../src/app/routeInventory'
import type { BundleStore } from '../resources'
export type StaticPageProps = { store: BundleStore; navigate: (path: WorkspacePath) => void }
