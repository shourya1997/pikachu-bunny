import { useEffect, useState } from 'react'
import { fetchJobAuth } from '../api'

type JobStatus = 'running' | 'completed' | 'failed' | 'interrupted'

interface UseJobPollingResult {
  status: JobStatus | null
  error: string | null
}

export function useJobPolling(jobId: string | null): UseJobPollingResult {
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    let cancelled = false

    async function poll() {
      try {
        const job = await fetchJobAuth(jobId!)
        if (cancelled) return
        setStatus(job.status as JobStatus)
        if (job.status === 'failed' || job.status === 'interrupted') {
          setError((job as any).error_message ?? 'Job failed')
        }
        if (job.status === 'running') {
          setTimeout(poll, 2000)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Poll failed')
      }
    }

    poll()
    return () => {
      cancelled = true
    }
  }, [jobId])

  return { status, error }
}
