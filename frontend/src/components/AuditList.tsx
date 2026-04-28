import { useEffect, useState } from 'react'
import { listAudits } from '../api'
import type { AuditSummary } from '../types'

interface AuditListProps {
  onSelect: (auditId: string) => void
}

export function AuditList({ onSelect }: AuditListProps) {
  const [audits, setAudits] = useState<AuditSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listAudits().then((items) => {
      setAudits(items)
      setLoading(false)
    })
  }, [])

  if (loading) return <p>Loading audits...</p>
  if (audits.length === 0) return <p>No audits yet. Upload your first one above.</p>

  return (
    <ul>
      {audits.map((a) => (
        <li key={a.audit_id} onClick={() => onSelect(a.audit_id)}>
          {a.audit_id} — {a.state} — Truth score: {a.truth_score}
        </li>
      ))}
    </ul>
  )
}
