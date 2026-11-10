import { formatUnit } from './unit'

interface IntervalResult {
  unit: string
  edges?: number[]
  bins?: { left: number; right: number; left_inclusive: boolean; right_inclusive: boolean }[]
}
/** Display labels in producer bin order; identity must remain separate. */
export function intervalLabels(result: IntervalResult): string[] {
  return [
    `< ${formatUnit(result.edges?.[0], result.unit)}`,
    ...(result.bins ?? []).map(b => `${b.left_inclusive ? '[' : '('}${formatUnit(b.left, result.unit)}, ${formatUnit(b.right, result.unit)}${b.right_inclusive ? ']' : ')'}`),
    `> ${formatUnit(result.edges?.at(-1), result.unit)}`,
  ]
}
