import { Alert } from 'antd'
import { StaticWorkspace } from '../static/StaticWorkspace'
import { sourceDisclosure, type PrivateData } from './admission'
export function PrivateWorkspace({ data }: { data: PrivateData }) {
  return <StaticWorkspace data={data} disclose={sourceDisclosure} header="Private · Static · Historical Real Market · No Backend" notice={<Alert type="warning" showIcon title="私有真实市场静态 Demo V2" description="Historical Embedded Results · 匿名只读 · 无实时行情或服务器执行 · Publication Rights = BLOCKED；仅限本地验收。" />} />
}
