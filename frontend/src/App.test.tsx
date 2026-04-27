import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { App } from './App';
import { fetchAudit, fetchDemoAudit, fetchJob, startDemoImport } from './api';
import type { AuditSummary } from './types';

vi.mock('./api', () => ({
  fetchDemoAudit: vi.fn(),
  startDemoImport: vi.fn(),
  fetchJob: vi.fn(),
  fetchAudit: vi.fn(),
}));

const emptyAudit = {
  audit_id: 'demo',
  state: 'empty',
  truth_score: 0,
  scoped_score_copy: 'Truth score checks only EPF contribution records in V1.0.',
  clean_months: 0,
  open_findings: 0,
  evidence_ready_findings: 0,
  sources: [],
  evidence: [],
  findings: [],
} satisfies AuditSummary;

const mismatchAudit = {
  ...emptyAudit,
  state: 'confirmed_mismatch',
  truth_score: 50,
  open_findings: 1,
  evidence_ready_findings: 1,
  findings: [
    {
      id: 'audit-1:2026-03:employer_pf',
      period: '2026-03',
      state: 'confirmed_mismatch',
      severity: 'high',
      title: 'Employer PF mismatch',
      explanation: 'Salary slip reports 6000.00 but EPF passbook reports 5500.00.',
      evidence_ids: ['salary:snippet:employer_pf'],
      result_code: 'invalid_amount',
    },
  ],
} satisfies AuditSummary;

beforeEach(() => {
  vi.mocked(fetchDemoAudit).mockResolvedValue(emptyAudit);
  vi.mocked(startDemoImport).mockResolvedValue({
    job_id: 'job-1',
    audit_id: 'demo',
    state: 'queued',
    progress: 0,
  });
  vi.mocked(fetchJob).mockResolvedValue({
    job_id: 'job-1',
    audit_id: 'demo',
    state: 'completed',
    progress: 100,
  });
  vi.mocked(fetchAudit).mockResolvedValue(mismatchAudit);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

test('renders the local EPF audit shell', async () => {
  render(<App />);

  expect(screen.getByRole('heading', { name: /check salary slip pf/i })).toBeInTheDocument();
  expect(screen.getByText(/files stay on this device/i)).toBeInTheDocument();
  expect(await screen.findByText(/truth score checks only epf/i)).toBeInTheDocument();
  expect(screen.getByText('...')).toBeInTheDocument();
});

test('runs a sample import and shows mismatch evidence state', async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole('button', { name: /run sample audit/i }));

  expect(await screen.findByText(/confirmed mismatch/i)).toBeInTheDocument();
  expect(screen.getByText('50')).toBeInTheDocument();
  expect(screen.getByText(/employer pf mismatch/i)).toBeInTheDocument();
  expect(screen.getByText(/salary slip reports 6000.00/i)).toBeInTheDocument();
});

test('shows startup errors from the local audit engine', async () => {
  vi.mocked(fetchDemoAudit).mockRejectedValueOnce(new Error('Local audit engine is unavailable.'));

  render(<App />);

  expect(await screen.findByRole('status')).toHaveTextContent(/local audit engine is unavailable/i);
});

test('shows failed background job status', async () => {
  vi.mocked(fetchJob).mockResolvedValueOnce({
    job_id: 'job-1',
    audit_id: 'demo',
    state: 'failed',
    progress: 100,
  });

  render(<App />);
  fireEvent.click(await screen.findByRole('button', { name: /run sample audit/i }));

  expect(await screen.findByRole('status')).toHaveTextContent(/audit job failed/i);
});
