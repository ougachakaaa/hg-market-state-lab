export function serializeJson(payload: unknown): string {
  const json = JSON.stringify(payload, null, 2)
  if (json === undefined) throw new Error('No JSON value')
  return json
}

export function jsonFence(json: string): string {
  let longestRun = 0
  for (const match of json.matchAll(/`+/g)) longestRun = Math.max(longestRun, match[0].length)
  const fence = '`'.repeat(Math.max(3, longestRun + 1))
  return `${fence}json\n${json}\n${fence}`
}
