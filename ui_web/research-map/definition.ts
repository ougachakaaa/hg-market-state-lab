import type { WorkspacePath } from '../src/app/routeInventory.ts'

export type Planning = 'planned' | 'defined' | 'in-progress'
export type Implementation = 'none' | 'partial' | 'available'
export type Evidence = 'pending' | 'available' | 'accepted'
export type ConclusionStatus = 'pending' | 'supported' | 'rejected' | 'inconclusive'
export type NodeKind = 'strategy' | 'strategy-definition' | 'baseline' | 'evaluation' | 'attribution'
  | 'study' | 'hypothesis' | 'optimization' | 'validation'
export type EdgeKind = 'dependency' | 'motivates' | 'feedback'

type NamedNote = { name: string; note: string }
type Metric = { name: string; availability: 'planned' | 'available'; note?: string }
export type ResearchReference =
  | { kind: 'navigation'; target: 'workspace'; label: string; value: WorkspacePath }
  | { kind: 'source' | 'result' | 'report'; target: 'repository'; label: string; value: string }

export type ResearchNode = {
  id: string
  kind: NodeKind
  title: string
  purpose: string
  questions: string[]
  topics?: NamedNote[]
  metrics: Metric[]
  parameters?: NamedNote[]
  planning: Planning
  implementation: Implementation
  evidence: Evidence
  conclusion: { status: ConclusionStatus; summary: string; review?: string }
  references: ResearchReference[]
}

export type ResearchEdge = { from: string; to: string; kind: EdgeKind; label?: string }
export type ResearchMap = { nodes: ResearchNode[]; edges: ResearchEdge[] }

export function edgeId(edge: ResearchEdge) {
  return `${edge.from}:${edge.to}:${edge.kind}`
}
