import { fileURLToPath } from 'node:url'
export default {
  test: {
    environment: 'node',
    include: [fileURLToPath(new URL('./result_v2.contract.test.ts', import.meta.url))],
  },
}
