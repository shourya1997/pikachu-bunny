import './styles.css'

import { useState } from 'react'
import { AuthGuard } from './components/AuthGuard'
import { UploadForm } from './components/UploadForm'
import { AuditList } from './components/AuditList'
import { useJobPolling } from './hooks/useJobPolling'

function Dashboard() {
  const [activeJob, setActiveJob] = useState<{ jobId: string; auditId: string } | null>(null)
  const { status, error } = useJobPolling(activeJob?.jobId ?? null)

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: 24 }}>
      <h1>AuditOS</h1>
      <UploadForm onJobStarted={(jobId, auditId) => setActiveJob({ jobId, auditId })} />
      {status === 'running' && <p>Processing your audit...</p>}
      {status === 'completed' && <p>Done! Check below.</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <h2>Your audits</h2>
      <AuditList onSelect={(id) => console.log('selected', id)} />
    </div>
  )
}

export default function App() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  )
}
