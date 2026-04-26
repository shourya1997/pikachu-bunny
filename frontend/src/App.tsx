import './styles.css';

import { useEffect, useState } from 'react';

import { fetchAudit, fetchDemoAudit, fetchJob, startDemoImport } from './api';
import type { AuditSummary, Finding, JobStatus } from './types';

const POLL_INTERVAL_MS = 250;
const MAX_POLL_ATTEMPTS = 40;

export function App() {
  const [audit, setAudit] = useState<AuditSummary | null>(null);
  const [status, setStatus] = useState('Loading local audit engine...');
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    let ignore = false;
    fetchDemoAudit()
      .then((summary) => {
        if (ignore) {
          return;
        }
        setAudit(summary);
        setStatus('Ready. Files stay local.');
      })
      .catch((error: unknown) => {
        if (!ignore) {
          setStatus(error instanceof Error ? error.message : 'Audit failed.');
        }
      })
      .finally(() => {
        if (!ignore) {
          setIsLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  async function runSampleAudit() {
    setIsRunning(true);
    setStatus('Processing sample files locally. You can come back later for updates.');
    try {
      const job = await startDemoImport();
      setStatus(`Job ${job.state}. Progress ${job.progress}%.`);
      const completedJob = job.state === 'completed' ? job : await waitForJob(job.job_id);
      setStatus(`Job ${completedJob.state}. Progress ${completedJob.progress}%.`);
      setAudit(await fetchAudit(completedJob.audit_id));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Audit failed.');
    } finally {
      setIsRunning(false);
    }
  }

  const findings = audit?.findings ?? [];

  return (
    <main className="app-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Local EPF contribution audit</p>
        <h1 id="page-title">Check salary slip PF against EPF passbook credits.</h1>
        <p className="lede">Files stay on this device. V1.0 checks only EPF contribution records and shows masked evidence snippets.</p>
      </section>

      <section className="control-room" aria-label="Financial Control Room">
        <aside className="panel">
          <p className="panel-label">Import guide</p>
          <button type="button" onClick={runSampleAudit} disabled={isLoading || isRunning}>
            {isRunning ? 'Running local audit...' : 'Run sample audit'}
          </button>
          <button type="button" disabled>Add salary slip</button>
          <button type="button" disabled>Add EPF passbook</button>
          <p className="small">No cloud upload required for core reconciliation.</p>
          <p className="small" role="status">{status}</p>
        </aside>

        <section className="panel primary">
          <p className="panel-label">Dashboard</p>
          <div className="score">{audit ? audit.truth_score : '...'}</div>
          <p>{audit?.scoped_score_copy ?? 'Truth score checks only EPF contribution records in V1.0.'}</p>
          <p className="state-pill">{(audit?.state ?? 'empty').replace(/_/g, ' ')}</p>
          <ul>
            <li>{audit?.clean_months ?? 0} clean months</li>
            <li>{audit?.open_findings ?? 0} open findings</li>
            <li>{audit?.evidence_ready_findings ?? 0} evidence-ready findings</li>
          </ul>
        </section>

        <aside className="panel">
          <p className="panel-label">Evidence drawer</p>
          {findings.length > 0 ? (
            <FindingList findings={findings} />
          ) : (
            <p>Masked snippets will appear here after import.</p>
          )}
          <p className="small">PAN, UAN, account numbers, phone, email, address, and employee IDs are masked by default.</p>
        </aside>
      </section>
    </main>
  );
}

async function waitForJob(jobId: string): Promise<JobStatus> {
  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
    const job = await fetchJob(jobId);
    if (job.state === 'completed') {
      return job;
    }
    if (job.state === 'failed' || job.state === 'cancelled') {
      throw new Error(`Audit job ${job.state}.`);
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  throw new Error('Audit job is still processing. Come back later for updates.');
}

function FindingList({ findings }: { findings: Finding[] }) {
  return (
    <ul className="findings">
      {findings.map((finding) => (
        <li key={finding.id}>
          <strong>{finding.title}</strong>
          <span>{finding.period ?? 'unknown period'}</span>
          <p>{finding.explanation}</p>
        </li>
      ))}
    </ul>
  );
}
