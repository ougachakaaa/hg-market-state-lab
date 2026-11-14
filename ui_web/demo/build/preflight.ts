import { registry } from './registry'
import { AdmissionError, validateDirectory } from './validate'

export async function main(args: string[], defaultDirectory: string): Promise<number> {
  if (args.length === 1 && args[0] === '--registry') {
    console.log(JSON.stringify(registry))
    return 0
  }
  if (args.length !== 0 && !(args.length === 2 && args[0] === '--dir' && args[1])) {
    console.error('FAIL dataset arguments invalid_arguments')
    return 1
  }
  try {
    await validateDirectory(args[1] ?? defaultDirectory)
    console.log('PASS seven Bundles admitted')
    return 0
  } catch (error) {
    console.error(error instanceof AdmissionError ? error.message : 'FAIL dataset admission validation_failed')
    return 1
  }
}
