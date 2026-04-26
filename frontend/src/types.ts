export type AuditState =
  | 'empty'
  | 'processing'
  | 'partial'
  | 'clean'
  | 'confirmed_mismatch'
  | 'needs_review'
  | 'unsupported'
  | 'failed'
  | 'cancelled';

export type AuditSummary = {
  audit_id: string;
  state: AuditState;
  truth_score: number;
  scoped_score_copy: string;
  clean_months: number;
  open_findings: number;
  evidence_ready_findings: number;
};
