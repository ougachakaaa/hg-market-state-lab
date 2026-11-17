export function dependencyInventory(ids, repositoryRoot) {
  const root = repositoryRoot.replaceAll('\\', '/')
  return [...ids].map(id => id.replaceAll('\\', '/').replace(root, '')).sort()
}
