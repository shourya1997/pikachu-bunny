import { useState } from 'react'
import { uploadAudit } from '../api'

interface UploadFormProps {
  onJobStarted: (jobId: string, auditId: string) => void
}

export function UploadForm({ onJobStarted }: UploadFormProps) {
  const [salary, setSalary] = useState<File | null>(null)
  const [epf, setEpf] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!salary || !epf) return
    setUploading(true)
    setError(null)
    try {
      const { job_id, audit_id } = await uploadAudit(salary, epf)
      onJobStarted(job_id, audit_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <form onSubmit={submit}>
      <label>
        Salary slip (PDF):
        <input type="file" accept=".pdf" onChange={(e) => setSalary(e.target.files?.[0] ?? null)} />
      </label>
      <label>
        EPF passbook (PDF):
        <input type="file" accept=".pdf" onChange={(e) => setEpf(e.target.files?.[0] ?? null)} />
      </label>
      <button type="submit" disabled={!salary || !epf || uploading}>
        {uploading ? 'Uploading...' : 'Audit my EPF'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  )
}
