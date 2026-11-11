import { CopyOutlined, DownloadOutlined } from '@ant-design/icons'
import { downloadText } from '../../../shared/download/download'
import { useState } from 'react'
import { downloadCsv } from '../../../shared/csv/csv'
import { optionChainCsv } from '../model/csvExport'
import { Button, Flex, Typography } from 'antd'
import type { OptionChain } from '../api/moOptionChain'
import { optionChainContextJson, optionChainContextFilename } from '../model/copyText'
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
  function exportContextJson() {
    setExportFeedback('')
    try {
      downloadText(optionChainContextJson(chain), optionChainContextFilename(chain), 'application/json;charset=utf-8')
      setExportFeedback('Download started')
    } catch {
      setExportFeedback('Export failed')
    }
  }
  return (
    <Flex role="group" aria-label="MO Option Chain copy actions" align="center" gap="small" wrap>
      <Button icon={<CopyOutlined aria-hidden="true" />} disabled={pending} onClick={() => void copy(() => serializeJson(chain))}>Copy Raw JSON</Button>
      <Button icon={<CopyOutlined aria-hidden="true" />} disabled={pending} onClick={() => void copy(() => optionChainContextJson(chain))}>Copy Context JSON</Button>
      <Button icon={<DownloadOutlined aria-hidden="true" />} disabled={pending} onClick={exportCsv}>Export CSV</Button>
      <Button icon={<DownloadOutlined aria-hidden="true" />} disabled={pending} onClick={exportContextJson}>Export Context JSON</Button>
      {exportFeedback && <Typography.Text role="status" type={exportFeedback === 'Export failed' ? 'danger' : 'success'}>{exportFeedback}</Typography.Text>}
      {feedback && <Typography.Text role="status" type={feedback === 'Copied' ? 'success' : 'danger'}>{feedback}</Typography.Text>}
    </Flex>
  )
}
