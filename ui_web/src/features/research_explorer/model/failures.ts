import type { components } from '../api/research.generated'

type Schemas = components['schemas']
export type FailureKind =
  | Schemas['ErrorBody']['kind']
  | Schemas['AuthErrorBody']['kind']
  | 'network'
  | 'invalid_response'
  | 'invalid_view'

export class ResearchError extends Error {
  readonly kind: FailureKind
  constructor(kind: FailureKind) { super(kind); this.kind = kind }
}
