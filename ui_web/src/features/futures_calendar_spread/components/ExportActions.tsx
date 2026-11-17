import { Button, Flex, Typography } from 'antd'
import { useState } from 'react'
import type { Result } from '../api/validateResult'
import { useClipboardWrite } from '../../../shared/clipboard/useClipboardWrite'
import { serializeJson } from '../../../shared/clipboard/text'
import { downloadText } from '../../../shared/download/download'
import { downloadCsv } from '../../../shared/csv/csv'
import { contextJson, exportFilename, resultCsv } from '../model/export'

export function ExportActions({ result }: { result: Result }) {
  const { copy, pending, feedback } = useClipboardWrite()
  const [downloadFeedback, setDownloadFeedback] = useState('')
  const [action, setAction] = useState<'copy' | 'download'>('copy')
  function copyResult(context: boolean) {
    setAction('copy')
    void copy(() => context ? contextJson(result) : serializeJson(result))
  }
  function download(context: boolean) {
    setAction('download')
    try {
      if (context) downloadText(contextJson(result), exportFilename(result, true), 'application/json;charset=utf-8')
      else downloadCsv(resultCsv(result), exportFilename(result))
      setDownloadFeedback('已开始下载')
    } catch { setDownloadFeedback('导出失败') }
  }
  return <Flex vertical gap="small">
    <Flex wrap gap="small">
      <Button disabled={pending} onClick={() => copyResult(false)}>复制原始 JSON</Button>
      <Button disabled={pending} onClick={() => copyResult(true)}>复制上下文 JSON</Button>
      <Button disabled={pending} onClick={() => download(false)}>导出 CSV</Button>
      <Button disabled={pending} onClick={() => download(true)}>导出上下文 JSON</Button>
    </Flex>
    <Typography.Text role="status">{action === 'download' ? downloadFeedback : feedback === 'Copied' ? '复制成功' : feedback === 'Copy failed' ? '复制失败' : ''}</Typography.Text>
  </Flex>
}
