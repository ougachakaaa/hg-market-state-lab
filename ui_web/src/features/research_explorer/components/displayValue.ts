export function displayValue(value: unknown): string {
  return value === null || value === undefined ? 'N/A' : typeof value === 'object' ? JSON.stringify(value) : String(value)
}
