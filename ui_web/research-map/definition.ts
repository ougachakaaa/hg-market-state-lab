import type { WorkspaceReferencePath } from '../src/app/routeInventory.ts'

export type Planning = 'planned' | 'defined' | 'in-progress'
export type Implementation = 'none' | 'partial' | 'available'
export type Evidence = 'pending' | 'available' | 'accepted'
export type ConclusionStatus = 'pending' | 'supported' | 'rejected' | 'inconclusive'
export type NodeKind = 'strategy' | 'baseline' | 'dimension' | 'study' | 'finding'
export type EdgeKind = 'branch' | 'attach' | 'derived_from'

type NamedNote = { name: string; note: string }
type Analysis = NamedNote & { availability: 'planned' | 'available' }
export type ResearchReference =
  | { kind: 'navigation'; target: 'workspace'; label: string; value: WorkspaceReferencePath }
  | { kind: 'source' | 'result' | 'report'; target: 'repository'; label: string; value: string }

export type ResearchNode = {
  id: string
  kind: NodeKind
  title: string
  purpose: string
  questions: string[]
  analyses?: Analysis[]
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

export function isEvidenceReference({ kind }: ResearchReference) {
  return kind === 'result' || kind === 'report'
}
