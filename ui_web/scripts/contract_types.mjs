import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import openapiTS, { astToString, COMMENT_HEADER } from 'openapi-typescript'

const contracts = [
  {
    name: 'MO Option Chain',
    input: 'src/features/mo_option_chain/api/moOptionChain.openapi.json',
    output: 'src/features/mo_option_chain/api/moOptionChain.generated.ts',
  },
  {
    name: 'MO Premium Plane',
    input: 'src/features/mo_option_premium/api/moOptionPremium.openapi.json',
    output: 'src/features/mo_option_premium/api/moOptionPremium.generated.ts',
  },
]

const check = process.argv.includes('--check')
let stale = false

function normalizeNewlines(value) {
  return value.replace(/\r\n/g, '\n')
}

for (const contract of contracts) {
  const source = JSON.parse(await readFile(resolve(contract.input), 'utf8'))
  const generated = COMMENT_HEADER + astToString(await openapiTS(source))
  const output = resolve(contract.output)

  if (check) {
    let committed
    try {
      committed = await readFile(output, 'utf8')
    } catch (error) {
      if (error?.code !== 'ENOENT') throw error
      committed = null
    }
    if (committed === null || normalizeNewlines(committed) !== normalizeNewlines(generated)) {
      console.error(`Stale ${contract.name} generated TypeScript: ${output}`)
      stale = true
    } else {
      console.log(`${contract.name} generated TypeScript is current: ${output}`)
    }
    continue
  }

  await writeFile(output, generated, { encoding: 'utf8' })
  console.log(`Wrote ${contract.name} generated TypeScript: ${output}`)
}

if (stale) process.exitCode = 1
