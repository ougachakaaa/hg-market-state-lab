// Packaging parser only. Business schemas remain with their Feature owners.
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json }

function decimalIdentity(token: string): string {
  const [mantissa, exponent = '0'] = token.toLowerCase().split('e')
  const negative = mantissa.startsWith('-')
  const unsigned = negative ? mantissa.slice(1) : mantissa
  const [whole, fraction = ''] = unsigned.split('.')
  let digits = (whole + fraction).replace(/^0+/, '')
  if (!digits) return '0'
  let scale = BigInt(exponent) - BigInt(fraction.length)
  const trailing = digits.length - digits.replace(/0+$/, '').length
  digits = digits.slice(0, digits.length - trailing)
  scale += BigInt(trailing)
  return `${negative ? '-' : ''}${digits}e${scale}`
}

export function parseStrict(text: string): Json {
  let offset = 0
  const fail = (): never => { throw new Error('invalid_json') }
  const whitespace = () => { while (/[\x20\t\r\n]/.test(text[offset] ?? '\0')) offset++ }
  function string(): string {
    const start = offset++
    while (offset < text.length) {
      const char = text[offset++]
      if (char === '"') return JSON.parse(text.slice(start, offset)) as string
      if (char === '\\') offset++
    }
    return fail()
  }
  function value(): Json {
    whitespace()
    if (text[offset] === '"') return string()
    if (text[offset] === '{') {
      offset++
      const object: Record<string, Json> = Object.create(null)
      whitespace()
      if (text[offset] === '}') { offset++; return object }
      while (offset < text.length) {
        whitespace()
        if (text[offset] !== '"') return fail()
        const key = string()
        if (Object.hasOwn(object, key)) throw new Error('duplicate_key')
        whitespace()
        if (text[offset++] !== ':') return fail()
        object[key] = value()
        whitespace()
        const separator = text[offset++]
        if (separator === '}') return object
        if (separator !== ',') return fail()
      }
      return fail()
    }
    if (text[offset] === '[') {
      offset++
      const array: Json[] = []
      whitespace()
      if (text[offset] === ']') { offset++; return array }
      while (offset < text.length) {
        array.push(value())
        whitespace()
        const separator = text[offset++]
        if (separator === ']') return array
        if (separator !== ',') return fail()
      }
      return fail()
    }
    for (const [literal, result] of [['true', true], ['false', false], ['null', null]] as const) {
      if (text.startsWith(literal, offset)) { offset += literal.length; return result }
    }
    const match = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(text.slice(offset))
    if (!match) return fail()
    const token = match[0]
    offset += token.length
    const number = Number(token)
    if (!Number.isFinite(number) || Object.is(number, -0) ||
      (Number.isInteger(number) && !Number.isSafeInteger(number)) ||
      decimalIdentity(token) !== decimalIdentity(JSON.stringify(number))) throw new Error('unsafe_number')
    return number
  }
  const result = value()
  whitespace()
  if (offset !== text.length) return fail()
  return result
}

export function canonical(value: unknown, depth = 0): string {
  const indent = '  '.repeat(depth)
  const childIndent = indent + '  '
  if (Array.isArray(value)) {
    return value.length ? `[\n${value.map(item => childIndent + canonical(item, depth + 1)).join(',\n')}\n${indent}]` : '[]'
  }
  if (typeof value === 'object' && value !== null) {
    const entries = Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
    return entries.length ? `{\n${entries.map(([key, item]) => `${childIndent}${JSON.stringify(key)}: ${canonical(item, depth + 1)}`).join(',\n')}\n${indent}}` : '{}'
  }
  if (typeof value === 'number' && (!Number.isFinite(value) || Object.is(value, -0) ||
    (Number.isInteger(value) && !Number.isSafeInteger(value)))) throw new Error('unsafe_number')
  const encoded = JSON.stringify(value)
  if (encoded === undefined) throw new Error('invalid_json')
  return encoded
}
export const canonicalBytes = (value: unknown): Buffer => Buffer.from(canonical(value) + '\n', 'utf8')
