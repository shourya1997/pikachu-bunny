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
  sources: SourceMetadata[];
  evidence: EvidenceSnippet[];
  findings: Finding[];
};

export type SourceMetadata = {
  id: string;
  source_type: 'salary_slip' | 'epf_passbook';
  filename: string;
  content_hash: string;
  confidence: 'high' | 'medium' | 'low';
  month_range: string[];
};

export type EvidenceSnippet = {
  id: string;
  source_id: string;
  fact_id?: string | null;
  label: string;
  text: string;
  masked: boolean;
};

export type Finding = {
  id: string;
  period?: string | null;
  state: AuditState;
  severity: 'info' | 'warning' | 'high';
  title: string;
  explanation: string;
  evidence_ids: string[];
  result_code: string;
};

export type JobStatus = {
  job_id: string;
  audit_id: string;
  state: 'queued' | 'running' | 'cancelled' | 'failed' | 'completed';
  progress: number;
};
