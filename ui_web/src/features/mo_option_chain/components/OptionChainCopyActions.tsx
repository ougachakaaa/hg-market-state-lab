import { useState } from 'react'
import { downloadCsv } from '../../../shared/csv/csv'
import { optionChainCsv } from '../model/csvExport'
import { Button, Flex, Typography } from 'antd'
import type { OptionChain } from '../api/moOptionChain'
import { optionChainForGpt } from '../model/copyText'
import { serializeJson } from '../../../shared/clipboard/text'
import { useClipboardWrite } from '../../../shared/clipboard/useClipboardWrite'

export function OptionChainCopyActions({ chain }: { chain: OptionChain }) {
  const { copy, pending, feedback } = useClipboardWrite()
  const [exportFeedback, setExportFeedback] = useState('')
  function exportCsv() {
    setExportFeedback('')
    try {
      const { csv, filename } = optionChainCsv(chain)
      downloadCsv(csv, filename)
      setExportFeedback('Download started')
    } catch {
      setExportFeedback('Export failed')
    }
  }
  return (
    <Flex role="group" aria-label="MO Option Chain copy actions" align="center" gap="small" wrap>
      <Button disabled={pending} onClick={() => void copy(() => serializeJson(chain))}>Copy JSON</Button>
      <Button disabled={pending} onClick={() => void copy(() => optionChainForGpt(chain))}>Copy for GPT</Button>
      <Button disabled={pending} onClick={exportCsv}>Export CSV</Button>
      {exportFeedback && <Typography.Text role="status" type={exportFeedback === 'Export failed' ? 'danger' : 'success'}>{exportFeedback}</Typography.Text>}
      {feedback && <Typography.Text role="status" type={feedback === 'Copied' ? 'success' : 'danger'}>{feedback}</Typography.Text>}
    </Flex>
  )
}
