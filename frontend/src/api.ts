import type { AuditSummary } from './types';

function isAuditSummary(value: unknown): value is AuditSummary {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.audit_id === 'string' &&
    typeof candidate.state === 'string' &&
    typeof candidate.truth_score === 'number' &&
    typeof candidate.scoped_score_copy === 'string' &&
    typeof candidate.clean_months === 'number' &&
    typeof candidate.open_findings === 'number' &&
    typeof candidate.evidence_ready_findings === 'number'
  );
}

export async function fetchDemoAudit(): Promise<AuditSummary> {
  const response = await fetch('/api/audits/demo');
  if (!response.ok) {
    throw new Error('Local audit engine is unavailable.');
  }
  const data: unknown = await response.json();
  if (!isAuditSummary(data)) {
    throw new Error('Local audit engine returned an invalid audit summary.');
  }
  return data;
}
