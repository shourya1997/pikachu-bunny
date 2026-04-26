import './styles.css';

import type { AuditState } from './types';

const stateLabels = [
  'empty',
  'processing',
  'partial',
  'clean',
  'confirmed_mismatch',
  'needs_review',
  'unsupported',
  'failed',
  'cancelled',
] satisfies AuditState[];

export function App() {
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
          <button type="button">Add salary slip</button>
          <button type="button">Add EPF passbook</button>
          <p className="small">No cloud upload required for core reconciliation.</p>
        </aside>

        <section className="panel primary">
          <p className="panel-label">Dashboard</p>
          <div className="score">0</div>
          <p>Truth score checks only EPF contribution records in V1.0.</p>
          <ul>
            {stateLabels.map((state) => (
              <li key={state}>{state.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </section>

        <aside className="panel">
          <p className="panel-label">Evidence drawer</p>
          <p>Masked snippets will appear here after import.</p>
          <p className="small">PAN, UAN, account numbers, phone, email, address, and employee IDs are masked by default.</p>
        </aside>
      </section>
    </main>
  );
}
