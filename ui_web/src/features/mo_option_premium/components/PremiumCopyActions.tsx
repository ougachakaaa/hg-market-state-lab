import { useState } from 'react'
import { downloadCsv } from '../../../shared/csv/csv'
import { premiumPlaneCsv } from '../model/csvExport'
import { Button, Flex, Typography } from 'antd'
import type { PremiumPlane } from '../api/moOptionPremium'
import { premiumPlaneForGpt } from '../model/copyText'
import { serializeJson } from '../../../shared/clipboard/text'
import { useClipboardWrite } from '../../../shared/clipboard/useClipboardWrite'

export function PremiumCopyActions({ plane, rawPayload }: { plane: PremiumPlane; rawPayload: unknown }) {
  const { copy, pending, feedback } = useClipboardWrite()
  const [exportFeedback, setExportFeedback] = useState('')
  function exportCsv() {
    setExportFeedback('')
    try {
      const { csv, filename } = premiumPlaneCsv(plane)
      downloadCsv(csv, filename)
      setExportFeedback('Download started')
    } catch {
      setExportFeedback('Export failed')
    }
  }
  return (
    <Flex role="group" aria-label="MO Premium Plane copy actions" align="center" gap="small" wrap>
      <Button disabled={pending} onClick={() => void copy(() => serializeJson(rawPayload))}>Copy JSON</Button>
      <Button disabled={pending} onClick={() => void copy(() => premiumPlaneForGpt(plane, rawPayload))}>Copy for GPT</Button>
      <Button disabled={pending} onClick={exportCsv}>Export CSV</Button>
      {exportFeedback && <Typography.Text role="status" type={exportFeedback === 'Export failed' ? 'danger' : 'success'}>{exportFeedback}</Typography.Text>}
      {feedback && <Typography.Text role="status" type={feedback === 'Copied' ? 'success' : 'danger'}>{feedback}</Typography.Text>}
    </Flex>
  )
}
