export function parseEdges(text: string): number[] | undefined {
  if (!text.trim()) return undefined
  const value: unknown = JSON.parse(text)
  if (!Array.isArray(value) || value.length < 2 || value.length > 128 || !value.every((n, i) => typeof n === 'number' && Number.isFinite(n) && (i === 0 || n > value[i - 1]))) throw new Error('Histogram Edges 必须是 2–128 个严格递增有限数值的 JSON 数组。')
  return value
}
