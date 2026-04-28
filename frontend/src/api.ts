import { supabase } from './lib/supabase'
import type { AuditSummary, Finding, JobResult, JobStatus } from './types';

const auditStates = ['empty', 'processing', 'partial', 'clean', 'confirmed_mismatch', 'needs_review', 'unsupported', 'failed', 'cancelled'] as const;
const jobStates = ['queued', 'running', 'cancelled', 'failed', 'completed'] as const;
const severities = ['info', 'warning', 'high'] as const;

function isOneOf<const T extends readonly string[]>(value: unknown, allowed: T): value is T[number] {
  return typeof value === 'string' && allowed.includes(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string');
}

function isFinding(value: unknown): value is Finding {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.id === 'string' &&
    (typeof value.period === 'string' || value.period === null || value.period === undefined) &&
    isOneOf(value.state, auditStates) &&
    isOneOf(value.severity, severities) &&
    typeof value.title === 'string' &&
    typeof value.explanation === 'string' &&
    isStringArray(value.evidence_ids) &&
    typeof value.result_code === 'string'
  );
}

function isAuditSummary(value: unknown): value is AuditSummary {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.audit_id === 'string' &&
    isOneOf(value.state, auditStates) &&
    typeof value.truth_score === 'number' &&
    typeof value.scoped_score_copy === 'string' &&
    typeof value.clean_months === 'number' &&
    typeof value.open_findings === 'number' &&
    typeof value.evidence_ready_findings === 'number' &&
    Array.isArray(value.sources) &&
    Array.isArray(value.evidence) &&
    Array.isArray(value.findings) &&
    value.findings.every(isFinding)
  );
}

function isJobResult(value: unknown): value is JobResult {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.ok === 'boolean' &&
    typeof value.code === 'string' &&
    typeof value.message === 'string'
  );
}

function isJobStatus(value: unknown): value is JobStatus {
  if (!isRecord(value)) {
    return false;
  }
  return (
    typeof value.job_id === 'string' &&
    typeof value.audit_id === 'string' &&
    isOneOf(value.state, jobStates) &&
    typeof value.progress === 'number' &&
    (value.result === undefined || value.result === null || isJobResult(value.result))
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

export async function fetchAudit(auditId: string): Promise<AuditSummary> {
  const response = await fetch(`/api/audits/${encodeURIComponent(auditId)}`);
  if (!response.ok) {
    throw new Error('Audit is not available yet.');
  }
  const data: unknown = await response.json();
  if (!isAuditSummary(data)) {
    throw new Error('Local audit engine returned an invalid audit summary.');
  }
  return data;
}

export async function fetchJob(jobId: string): Promise<JobStatus> {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
  if (!response.ok) {
    throw new Error('Audit job is not available.');
  }
  const data: unknown = await response.json();
  if (!isJobStatus(data)) {
    throw new Error('Local audit engine returned an invalid job status.');
  }
  return data;
}

export async function startDemoImport(): Promise<JobStatus> {
  const response = await fetch('/api/audits/demo/imports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      salary_slip_text: demoSalarySlip,
      epf_passbook_text: demoEpfPassbook,
    }),
  });
  if (!response.ok) {
    throw new Error('Could not start the local audit job.');
  }
  const data: unknown = await response.json();
  if (!isJobStatus(data)) {
    throw new Error('Local audit engine returned an invalid job status.');
  }
  return data;
}

// Synthetic demo data only. These values are intentionally non-real placeholders.
const demoSalarySlip = `SALARY SLIP
Employee: Demo Employee
Employee ID: DEMO0001
PAN: XXXXX0000X
UAN: 000000000000
Address: 1 Demo Street, Testville
Month: March 2026
Employer: Demo Payroll Pvt Ltd
Basic Wage: Rs. 50,000
Employee PF: Rs. 6,000
Employer PF: Rs. 6,000`;

const demoEpfPassbook = `EPF PASSBOOK
Member: Demo Employee
UAN: 000000000000
Wage Month: 2026-03
Establishment: Demo Payroll Private Limited
Employee Contribution: 6,000
Employer Contribution: 5,500`;

async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('Not authenticated')
  return { Authorization: `Bearer ${token}` }
}

export async function uploadAudit(salarySlip: File, epfPassbook: File): Promise<{ job_id: string; audit_id: string }> {
  const formData = new FormData()
  formData.append('salary_slip_pdf', salarySlip)
  formData.append('epf_passbook_pdf', epfPassbook)
  const res = await fetch('/api/audits/upload', {
    method: 'POST',
    headers: await authHeaders(),
    body: formData,
  })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  return res.json() as Promise<{ job_id: string; audit_id: string }>
}

export async function fetchJobAuth(jobId: string): Promise<JobStatus> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`, { headers: await authHeaders() })
  if (!res.ok) throw new Error(`Job fetch failed: ${res.status}`)
  const data: unknown = await res.json()
  if (!isJobStatus(data)) throw new Error('Invalid job status')
  return data
}

export async function fetchAuditAuth(auditId: string): Promise<AuditSummary> {
  const res = await fetch(`/api/audits/${encodeURIComponent(auditId)}`, { headers: await authHeaders() })
  if (!res.ok) throw new Error(`Audit fetch failed: ${res.status}`)
  const data: unknown = await res.json()
  if (!isAuditSummary(data)) throw new Error('Invalid audit summary')
  return data
}

export async function listAudits(): Promise<AuditSummary[]> {
  const res = await fetch('/api/audits', { headers: await authHeaders() })
  if (!res.ok) throw new Error(`Audit list failed: ${res.status}`)
  const data: unknown = await res.json()
  if (!Array.isArray(data)) throw new Error('Invalid audit list')
  return data as AuditSummary[]
}
