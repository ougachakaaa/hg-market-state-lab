export function serializeJson(payload: unknown): string {
  const json = JSON.stringify(payload, null, 2)
  if (json === undefined) throw new Error('No JSON value')
  return json
}
