# AuditOS V1 — Implementation Plan

**Source design:** `~/.gstack/projects/shourya1997-pikachu-bunny/shourya-main-design-20260428-025937.md`
**Status:** Design APPROVED (CEO + Eng cleared). Ready to implement.
**Branch:** main
**Generated:** 2026-04-28

## Goal

Ship AuditOS V1 (Fast Lane): Google login + PDF upload + user-isolated audits at a public URL.

## Stack (locked)

| Layer | Tech | Notes |
|-------|------|-------|
| Auth | Supabase Auth (JWT) | Google OAuth provider |
| DB | PocketBase (co-located on Fly.io) | ~1ms HTTP, admin UI |
| Backend | FastAPI | Existing parse engine reused |
| PDF extraction | pdfplumber | New dep, smoke-tested |
| Frontend | React + Vite + @supabase/supabase-js | JWT in Bearer header |
| Deploy | Fly.io single machine | Persistent volume `auditos_data` |
| CDN | Cloudflare proxy | Free SSL, DDoS, 5-min setup |

## Privacy posture

- Server deletes raw PDFs after parsing (`os.unlink` in `finally`)
- Findings (PF amounts, employer names, periods) persist in PocketBase
- Claim: "We never store your salary slip after we've read it" (correct, not zero-knowledge)

## Pre-flight checklist

- [ ] Supabase account created, new project provisioned
- [ ] Google Cloud Console: OAuth client ID + secret generated
- [ ] Supabase → Auth → Providers → Google: enabled with client ID/secret
- [ ] Fly.io account, `fly` CLI installed and authenticated
- [ ] PocketBase v0.22+ binary downloaded (~30MB Go binary)
- [ ] Cloudflare account (free tier) for DNS proxy
- [ ] Domain registered (or use `*.fly.dev` for V1)

---

# Day 0 — Setup (2-3 hours, parallel work)

## D0.1 — Supabase project provisioning

**Owner:** You (manual, browser)
**Output:** `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` (modern asymmetric JWKS path)

Steps:
1. Sign up at https://supabase.com
2. Create new project (region: closest to India — Mumbai or Singapore)
3. Project Settings → API → copy `URL` → save as `SUPABASE_URL`
4. Project Settings → API Keys → **API Keys** tab → "Create new API Keys" → copy `sb_publishable_...` → save as `SUPABASE_PUBLISHABLE_KEY`
5. JWKS endpoint auto-available at `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` — no secret to copy
6. Authentication → Providers → Google → Enable
   - Add Google client ID + secret (from Google Cloud Console OAuth)
   - Authorized redirect URL: `https://<project>.supabase.co/auth/v1/callback`

**Note:** Legacy HS256 path (anon key + JWT secret) still works but deprecated. We use modern asymmetric (RS256/ES256) via JWKS — no shared secret on backend.

**Validation:** Test login from Supabase dashboard "Auth" → Users panel.

## D0.2 — Google OAuth verification request

**Owner:** You (manual)
**Why:** Unverified app = 100 test-user cap. Verification takes 4-6 weeks.

Steps:
1. Google Cloud Console → APIs & Services → OAuth consent screen
2. Fill app info: name, logo, privacy policy URL, terms URL, support email
3. Add scopes: `openid`, `email`, `profile`
4. Submit for verification
5. **Note:** Cap of 100 users until approved. Plan accordingly.

## D0.3 — Fly.io volume + secrets

**Owner:** You (CLI)

```bash
# Login
fly auth login

# Create persistent volume (10GB, in same region as app)
fly volumes create auditos_data --region bom --size 10

# Set secrets (gather values from D0.1 + D0.4)
fly secrets set \
  SUPABASE_URL="https://<project>.supabase.co" \
  SUPABASE_PUBLISHABLE_KEY="sb_publishable_..." \
  PB_ADMIN_EMAIL="admin@yourdomain.com" \
  PB_ADMIN_PASSWORD="<strong_password_min_10_chars>"
```

**Validation:** `fly secrets list` shows all 4.

## D0.4 — PocketBase binary download

**Owner:** You (manual)

```bash
mkdir -p infra/pocketbase
cd infra/pocketbase

# Download v0.22+ Linux amd64 binary
curl -L -o pb.zip https://github.com/pocketbase/pocketbase/releases/download/v0.22.21/pocketbase_0.22.21_linux_amd64.zip
unzip pb.zip
chmod +x pocketbase
rm pb.zip CHANGELOG.md LICENSE.md

# Test locally
./pocketbase serve --http=0.0.0.0:8090
# Open http://localhost:8090/_/ → create admin account
```

Add to `.gitignore`:
```
infra/pocketbase/pocketbase
infra/pocketbase/pb_data/
```

## D0.5 — PDF extraction smoke test (CRITICAL)

**Owner:** You (CLI)
**Why:** pdfplumber on Indian salary slips is untested. Must pass before wiring upload endpoint.

```bash
cd backend
pip install pdfplumber

python -c "
import pdfplumber
fixtures = [
    'tests/fixtures/personas/ananya-salary-slip.pdf',
    'tests/fixtures/personas/rohan-salary-slip.pdf',
    'tests/fixtures/personas/meera-salary-slip.pdf',
]
for f in fixtures:
    with pdfplumber.open(f) as pdf:
        text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert len(text) > 100, f'{f}: extraction too short ({len(text)} chars)'
    print(f'{f}: OK ({len(text)} chars)')
"
```

**Pass criteria:** All 3 fixtures extract >100 chars and contain recognizable salary fields (Basic, PF, etc.).

**Fail mitigation:** If extraction returns empty/garbled, swap pdfplumber for `pypdf` or `pymupdf`. Fix before D1.4.

---

# Day 1 — Backend (8-10 hours)

## D1.1 — Add dependencies

**File:** `backend/pyproject.toml` (or `requirements.txt`)

Add:
```
pyjwt[crypto]>=2.8.0
cryptography>=42.0.0
httpx>=0.27.0
pdfplumber>=0.11.0
python-multipart>=0.0.9
```

```bash
cd backend
pip install -e .
# OR
pip install -r requirements.txt
```

## D1.2 — Auth dependency

**File:** `backend/app/auth.py` (NEW) — JWKS asymmetric verification

```python
from __future__ import annotations

import os
from typing import Annotated

import jwt
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

SUPABASE_URL = os.environ["SUPABASE_URL"]
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"

# Cache JWKS at module load — refreshes on key rotation via PyJWKClient internals
_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True, lifespan=3600)


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            issuer=f"{SUPABASE_URL}/auth/v1",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing 'sub' claim.")
    return user_id
```

**Tests:** `backend/tests/test_auth.py`
- Valid JWT → returns user_id
- Missing header → 401
- Bearer typo → 401
- Expired token → 401
- Wrong audience → 401
- Wrong issuer → 401
- Tampered signature → 401
- Mock JWKS endpoint with `respx` or fixture keys for offline testing

## D1.3 — PocketBase client

**File:** `backend/app/pocketbase_client.py` (NEW, replaces `engine/storage.py`)

```python
from __future__ import annotations

import os
from typing import Any

import httpx

POCKETBASE_URL = os.environ.get("POCKETBASE_URL", "http://localhost:8090")
PB_ADMIN_EMAIL = os.environ["PB_ADMIN_EMAIL"]
PB_ADMIN_PASSWORD = os.environ["PB_ADMIN_PASSWORD"]


class PocketBaseClient:
    def __init__(self, base_url: str = POCKETBASE_URL):
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._admin_token: str | None = None

    async def __aenter__(self) -> "PocketBaseClient":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        await self._authenticate_admin()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _authenticate_admin(self) -> None:
        assert self._client
        r = await self._client.post(
            "/api/admins/auth-with-password",
            json={"identity": PB_ADMIN_EMAIL, "password": PB_ADMIN_PASSWORD},
        )
        r.raise_for_status()
        self._admin_token = r.json()["token"]
        self._client.headers["Authorization"] = self._admin_token

    async def get(self, collection: str, record_id: str, user_id: str) -> dict | None:
        """Fetch single record. user_id filter MANDATORY for isolation."""
        assert self._client
        r = await self._client.get(
            f"/api/collections/{collection}/records/{record_id}",
            params={"filter": f"(user_id='{user_id}')"},
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def list(self, collection: str, user_id: str, filter_extra: str = "") -> list[dict]:
        """List records, always filtered by user_id."""
        assert self._client
        filt = f"(user_id='{user_id}')"
        if filter_extra:
            filt = f"{filt} && {filter_extra}"
        r = await self._client.get(
            f"/api/collections/{collection}/records",
            params={"filter": filt, "sort": "-created"},
        )
        r.raise_for_status()
        return r.json().get("items", [])

    async def create(self, collection: str, data: dict, user_id: str) -> dict:
        """Create record with user_id always set server-side."""
        assert self._client
        payload = {**data, "user_id": user_id}
        r = await self._client.post(f"/api/collections/{collection}/records", json=payload)
        r.raise_for_status()
        return r.json()

    async def update(self, collection: str, record_id: str, data: dict, user_id: str) -> dict:
        """Update record. Verify ownership before patching."""
        assert self._client
        existing = await self.get(collection, record_id, user_id)
        if not existing:
            raise ValueError(f"Record {record_id} not owned by {user_id}")
        r = await self._client.patch(
            f"/api/collections/{collection}/records/{record_id}",
            json=data,
        )
        r.raise_for_status()
        return r.json()
```

**Tests:** `backend/tests/test_pocketbase_client.py`
- CRUD with user_id filter
- Cross-user read returns None
- Create always sets user_id (no override)

## D1.4 — PocketBase collections

**Tool:** PocketBase admin UI at `http://localhost:8090/_/` OR migration JSON.

Collections to create:

### `audits`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| state | text | yes |
| truth_score | number | yes |
| scoped_score_copy | text | yes |
| clean_months | number | no |
| open_findings | number | no |
| evidence_ready_findings | number | no |

### `sources`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | relation→audits | yes |
| source_type | text | yes |
| filename | text | yes |
| content_hash | text | yes |

### `evidence_snippets`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | relation→audits | yes |
| source_id | relation→sources | yes |
| text | text | yes |
| period | text | no |
| label | text | no |
| masked | bool | no |

### `findings`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | relation→audits | yes |
| state | text | yes |
| severity | text | yes |
| title | text | yes |
| explanation | text | yes |
| result_code | text | yes |
| period | text | no |
| evidence_ids | json | no |

### `jobs`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | relation→audits | yes |
| status | text (queued/running/completed/failed/interrupted) | yes |
| error_message | text | no |

**Important:** Do NOT set collection-level rules. Admin token bypasses them anyway. user_id filter in client is the ONLY isolation. Verify with two-account test.

## D1.5 — PDF upload endpoint

**File:** `backend/app/main.py` (modify) + `backend/app/services/upload_service.py` (NEW)

```python
# In main.py, replace existing import_audit endpoint:

import os
import tempfile
import uuid
from typing import Annotated

from fastapi import BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.auth import get_current_user
from app.services.upload_service import process_upload

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB


@app.post("/api/import/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_audit(
    background_tasks: BackgroundTasks,
    salary_slip_pdf: Annotated[UploadFile, File()],
    epf_passbook_pdf: Annotated[UploadFile, File()],
    user_id: Annotated[str, Depends(get_current_user)],
) -> dict[str, str]:
    # Size check via Content-Length is brittle for multipart; check after read
    salary_bytes = await salary_slip_pdf.read()
    if len(salary_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="salary_slip_pdf exceeds 10MB.")
    epf_bytes = await epf_passbook_pdf.read()
    if len(epf_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="epf_passbook_pdf exceeds 10MB.")

    # Server-generated IDs
    audit_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    # Persist to temp files
    salary_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    epf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    with open(salary_path, "wb") as f:
        f.write(salary_bytes)
    with open(epf_path, "wb") as f:
        f.write(epf_bytes)

    # Schedule background processing
    background_tasks.add_task(
        process_upload,
        user_id=user_id,
        audit_id=audit_id,
        job_id=job_id,
        salary_path=salary_path,
        epf_path=epf_path,
    )

    return {"job_id": job_id, "audit_id": audit_id}
```

**File:** `backend/app/services/upload_service.py` (NEW)

```python
from __future__ import annotations

import logging
import os

import pdfplumber

from app.engine.parsers import parse_epf_passbook_text, parse_salary_slip_text
from app.engine.reconcile import reconcile_epf
from app.pocketbase_client import PocketBaseClient

logger = logging.getLogger(__name__)


def extract_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


async def process_upload(
    *,
    user_id: str,
    audit_id: str,
    job_id: str,
    salary_path: str,
    epf_path: str,
) -> None:
    async with PocketBaseClient() as pb:
        await pb.create("jobs", {"id": job_id, "audit_id": audit_id, "status": "running"}, user_id)

        try:
            salary_text = extract_text(salary_path)
            epf_text = extract_text(epf_path)
            if not salary_text.strip() or not epf_text.strip():
                raise ValueError("PDF text extraction returned empty.")

            salary = parse_salary_slip_text(f"{audit_id}:salary", "salary-slip.pdf", salary_text)
            epf = parse_epf_passbook_text(f"{audit_id}:epf", "epf-passbook.pdf", epf_text)
            if not salary.result.ok:
                raise ValueError(salary.result.message)
            if not epf.result.ok:
                raise ValueError(epf.result.message)

            summary = reconcile_epf(audit_id, [salary, epf])

            # Persist audit + sources + evidence + findings
            await pb.create("audits", {
                "id": audit_id,
                "state": summary.state.value,
                "truth_score": summary.truth_score,
                "scoped_score_copy": summary.scoped_score_copy,
                "clean_months": summary.clean_months,
                "open_findings": summary.open_findings,
                "evidence_ready_findings": summary.evidence_ready_findings,
            }, user_id)

            for source in summary.sources:
                await pb.create("sources", {
                    "id": source.id,
                    "audit_id": audit_id,
                    "source_type": source.source_type.value,
                    "filename": source.filename,
                    "content_hash": source.content_hash,
                }, user_id)

            for snip in summary.evidence:
                await pb.create("evidence_snippets", {
                    "id": snip.id,
                    "audit_id": audit_id,
                    "source_id": snip.source_id,
                    "text": snip.text,
                    "label": snip.label,
                    "masked": snip.masked,
                }, user_id)

            for finding in summary.findings:
                await pb.create("findings", {
                    "id": finding.id,
                    "audit_id": audit_id,
                    "state": finding.state.value,
                    "severity": finding.severity.value,
                    "title": finding.title,
                    "explanation": finding.explanation,
                    "result_code": finding.result_code.value,
                    "period": finding.period,
                    "evidence_ids": finding.evidence_ids,
                }, user_id)

            await pb.update("jobs", job_id, {"status": "completed"}, user_id)
            logger.info("job.completed", extra={"user_id": user_id, "audit_id": audit_id, "job_id": job_id})

        except Exception as exc:
            logger.exception("job.failed", extra={"user_id": user_id, "job_id": job_id})
            await pb.update("jobs", job_id, {"status": "failed", "error_message": str(exc)}, user_id)
        finally:
            for path in (salary_path, epf_path):
                try:
                    os.unlink(path)
                    logger.info("pdf_temp.deleted", extra={"path": path})
                except OSError:
                    logger.warning("pdf_temp.delete_failed", extra={"path": path})
```

## D1.6 — Audit + job endpoints (user-scoped)

**File:** `backend/app/main.py` (modify)

```python
@app.get("/api/audits")
async def list_audits(
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[dict]:
    async with PocketBaseClient() as pb:
        return await pb.list("audits", user_id)


@app.get("/api/audits/{audit_id}")
async def get_audit(
    audit_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
) -> dict:
    async with PocketBaseClient() as pb:
        audit = await pb.get("audits", audit_id, user_id)
        if not audit:
            raise HTTPException(status_code=404, detail="Audit not found.")
        # Hydrate findings + evidence
        audit["findings"] = await pb.list("findings", user_id, filter_extra=f"audit_id='{audit_id}'")
        audit["evidence"] = await pb.list("evidence_snippets", user_id, filter_extra=f"audit_id='{audit_id}'")
        return audit


@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
) -> dict:
    async with PocketBaseClient() as pb:
        job = await pb.get("jobs", job_id, user_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return job
```

**Remove:** old `import_audit`, `cancel_job`, `audit_service()` factory, `app.state.audit_service`.

## D1.7 — Startup sweep (interrupted jobs)

**File:** `backend/app/main.py` (modify)

```python
@app.on_event("startup")
async def startup_sweep() -> None:
    async with PocketBaseClient() as pb:
        # Find all running jobs across all users (admin scope)
        # Mark as interrupted
        r = await pb._client.get(  # type: ignore[union-attr]
            "/api/collections/jobs/records",
            params={"filter": "(status='running')", "perPage": 200},
        )
        items = r.json().get("items", [])
        for job in items:
            await pb._client.patch(
                f"/api/collections/jobs/records/{job['id']}",
                json={"status": "interrupted", "error_message": "Server restarted mid-job."},
            )
        if items:
            logger.warning("job.interrupted_on_startup", extra={"count": len(items)})
```

## D1.8 — Test gates

```bash
cd backend
pytest -v                           # 39 existing tests must still pass
pytest tests/test_auth.py -v         # New: 6 auth tests
pytest tests/test_pocketbase_client.py -v  # New: CRUD + isolation tests
pytest tests/test_upload.py -v       # New: upload flow + size limits
```

**Pass criteria:** All green. Coverage ≥80%.

## D1 Checkpoint

- [ ] `get_current_user` rejects bad/missing/expired JWTs
- [ ] PocketBase client refuses ops without user_id
- [ ] Two test accounts cannot read each other's audits
- [ ] Upload endpoint creates audit_id + job_id, returns 202
- [ ] Background job parses PDF, persists findings, deletes temp file
- [ ] Startup sweep marks orphaned jobs as `interrupted`
- [ ] All 39 original tests still pass

---

# Day 2 — Frontend (8-10 hours)

## D2.1 — Add Supabase client

**File:** `frontend/package.json`

```bash
cd frontend
npm install @supabase/supabase-js
```

**File:** `frontend/.env.local` (NEW, gitignored)

```
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

**File:** `frontend/src/lib/supabase.ts` (NEW)

```typescript
import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL as string
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string

if (!url || !publishableKey) {
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_PUBLISHABLE_KEY')
}

export const supabase = createClient(url, publishableKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
})
```

## D2.2 — Auth guard + login page

**File:** `frontend/src/components/AuthGuard.tsx` (NEW)

```typescript
import { useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { LoginPage } from './LoginPage'

export function AuthGuard({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setLoading(false)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => setSession(s))
    return () => sub.subscription.unsubscribe()
  }, [])

  if (loading) return <div>Loading...</div>
  if (!session) return <LoginPage />
  return <>{children}</>
}
```

**File:** `frontend/src/components/LoginPage.tsx` (NEW)

```typescript
import { supabase } from '../lib/supabase'

export function LoginPage() {
  async function signIn() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    })
  }
  return (
    <div style={{ padding: 32, textAlign: 'center' }}>
      <h1>AuditOS</h1>
      <p>Audit your EPF contributions in 60 seconds.</p>
      <button onClick={signIn}>Sign in with Google</button>
    </div>
  )
}
```

**Modify:** `frontend/src/App.tsx` to wrap content in `<AuthGuard>`.

## D2.3 — JWT injection in API calls

**File:** `frontend/src/api.ts` (modify)

Wrap every fetch:

```typescript
import { supabase } from './lib/supabase'

async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('Not authenticated')
  return { Authorization: `Bearer ${token}` }
}

export async function uploadAudit(salarySlip: File, epfPassbook: File) {
  const formData = new FormData()
  formData.append('salary_slip_pdf', salarySlip)
  formData.append('epf_passbook_pdf', epfPassbook)
  const res = await fetch('/api/import/upload', {
    method: 'POST',
    headers: await authHeaders(),
    body: formData,
  })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  return res.json() as Promise<{ job_id: string; audit_id: string }>
}

export async function fetchJob(jobId: string) {
  const res = await fetch(`/api/jobs/${jobId}`, { headers: await authHeaders() })
  if (!res.ok) throw new Error(`Job fetch failed: ${res.status}`)
  return res.json()
}

export async function fetchAudit(auditId: string) {
  const res = await fetch(`/api/audits/${auditId}`, { headers: await authHeaders() })
  if (!res.ok) throw new Error(`Audit fetch failed: ${res.status}`)
  return res.json()
}

export async function listAudits() {
  const res = await fetch('/api/audits', { headers: await authHeaders() })
  if (!res.ok) throw new Error(`Audit list failed: ${res.status}`)
  return res.json()
}
```

## D2.4 — Upload UI

**File:** `frontend/src/components/UploadForm.tsx` (NEW)

```typescript
import { useState } from 'react'
import { uploadAudit } from '../api'

export function UploadForm({ onJobStarted }: { onJobStarted: (jobId: string, auditId: string) => void }) {
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
```

## D2.5 — Job polling

**File:** `frontend/src/hooks/useJobPolling.ts` (NEW)

```typescript
import { useEffect, useState } from 'react'
import { fetchJob } from '../api'

type JobStatus = 'running' | 'completed' | 'failed' | 'interrupted'

export function useJobPolling(jobId: string | null) {
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    let cancelled = false

    async function poll() {
      try {
        const job = await fetchJob(jobId!)
        if (cancelled) return
        setStatus(job.status)
        if (job.status === 'failed' || job.status === 'interrupted') {
          setError(job.error_message ?? 'Job failed')
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
```

## D2.6 — Audit list / history view

**File:** `frontend/src/components/AuditList.tsx` (NEW)

```typescript
import { useEffect, useState } from 'react'
import { listAudits } from '../api'

export function AuditList({ onSelect }: { onSelect: (auditId: string) => void }) {
  const [audits, setAudits] = useState<any[]>([])
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
        <li key={a.id} onClick={() => onSelect(a.id)}>
          {a.created} — {a.state} — Truth score: {a.truth_score}
        </li>
      ))}
    </ul>
  )
}
```

## D2.7 — Wire it up in App.tsx

```typescript
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
```

## D2.8 — Local dev test

```bash
# Terminal 1: PocketBase
cd infra/pocketbase && ./pocketbase serve

# Terminal 2: FastAPI
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend && npm run dev
```

Open http://localhost:5173 → Sign in with Google → upload 2 PDFs → watch job poll → see audit appear.

## D2 Checkpoint

- [ ] Unauthenticated user sees login page
- [ ] Google OAuth completes, redirects back with session
- [ ] All API calls include `Authorization: Bearer <jwt>`
- [ ] Upload form rejects empty files, accepts 2 PDFs
- [ ] Job poll updates UI from `running` → `completed`
- [ ] Audit list shows only current user's audits
- [ ] Two test users see separate data

---

# Day 3 — Deploy (4-6 hours)

## D3.1 — Dockerfile updates

**File:** `Dockerfile` (modify)

```dockerfile
FROM python:3.12-slim AS backend-build

WORKDIR /app
COPY backend/pyproject.toml backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_PUBLISHABLE_KEY
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

# PocketBase binary
COPY infra/pocketbase/pocketbase /usr/local/bin/pocketbase
RUN chmod +x /usr/local/bin/pocketbase

# Backend
COPY --from=backend-build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-build /app /app

# Frontend static
COPY --from=frontend-build /app/dist /app/static

# Supervisord runs both pocketbase + uvicorn
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*
COPY infra/supervisord.conf /etc/supervisor/conf.d/auditos.conf

EXPOSE 8000
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/auditos.conf"]
```

**File:** `infra/supervisord.conf` (NEW)

```ini
[supervisord]
nodaemon=true
user=root

[program:pocketbase]
command=/usr/local/bin/pocketbase serve --http=0.0.0.0:8090 --dir=/data/pb
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:uvicorn]
command=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

## D3.2 — fly.toml updates

**File:** `fly.toml` (modify)

```toml
app = "auditos"
primary_region = "bom"

[build]
  dockerfile = "Dockerfile"
  [build.args]
    VITE_SUPABASE_URL = "https://<project>.supabase.co"
    VITE_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_..."

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = false
  min_machines_running = 1
  max_machines_running = 1

[[mounts]]
  source = "auditos_data"
  destination = "/data"

[env]
  AUDITOS_DATA_DIR = "/data"
  POCKETBASE_DATA_DIR = "/data/pb"
  POCKETBASE_URL = "http://localhost:8090"
  AUDITOS_CORS_ORIGINS = "https://auditos.fly.dev,https://<custom-domain>"

[[vm]]
  size = "shared-cpu-1x"
  memory = "1gb"
```

## D3.3 — Deploy

```bash
# Verify secrets are set (from D0.3)
fly secrets list

# Deploy
fly deploy

# Watch logs
fly logs

# Open app
fly open
```

**Validation:**
- App reachable at `https://auditos.fly.dev`
- `https://auditos.fly.dev/api/health` returns `{"status":"ok"}`
- PocketBase admin UI accessible via SSH tunnel: `fly proxy 8090:8090` then http://localhost:8090/_/

## D3.4 — Configure PocketBase collections in production

```bash
# SSH into Fly machine
fly ssh console

# Inside container:
# PocketBase admin UI is at http://localhost:8090/_/
# Create collections (D1.4) via admin UI
# OR import migration JSON
```

Faster: use PocketBase migrations. Create `infra/pocketbase/pb_migrations/1700000000_collections.js` with all 5 collections, ship in Docker image.

## D3.5 — Cloudflare DNS

1. Cloudflare dashboard → Add site → enter your domain
2. Update nameservers at registrar
3. DNS → Add A record → `@` → `<fly.io IP>` (get from `fly ips list`) → Proxy: ON
4. SSL/TLS → Full (strict)
5. Caching → Auto Minify: HTML/CSS/JS

**Validation:** `https://yourdomain.com` loads with Cloudflare proxy headers.

## D3.6 — Smoke test (3 Google accounts)

Create or borrow 3 Google accounts. For each:
1. Open `https://yourdomain.com`
2. Sign in with Google
3. Upload `tests/fixtures/personas/ananya-salary-slip.pdf` + `ananya-epf-passbook.pdf`
4. Wait for job to complete
5. Verify audit appears in list
6. **Critical:** Sign out, sign in as account #2, verify account #1's audit is NOT visible

**Pass criteria:**
- All 3 logins succeed
- All 3 uploads complete
- Each user sees only their own audits
- `fly logs` shows `pdf_temp.deleted` log line for each upload

## D3.7 — Post-launch monitoring (Day 3 evening)

```bash
# Log tail
fly logs --tail

# Check disk usage
fly ssh console -C "du -sh /data/pb"

# Check job table for stuck jobs
# (use admin UI or curl with admin token)
```

Set up:
- UptimeRobot ping on `https://yourdomain.com/api/health` (free, 5-min interval)
- Cloudflare email alert for traffic spikes

## D3 Checkpoint

- [ ] App reachable at public URL with HTTPS
- [ ] Google login completes for 3 test accounts
- [ ] Upload + audit flow works end-to-end
- [ ] User isolation verified (account A cannot see account B's data)
- [ ] PDF temp files deleted (log confirms)
- [ ] Cloudflare proxy active (check response headers for `cf-ray`)

---

# Post-launch Hardening (Week 2 — before public announcement)

From `TODOS.md` (Cloud Deployment Follow-Ups):

1. **Rate limiting** on `POST /api/import/upload` (slowapi, 1 req/10s per user)
2. **pdfplumber timeout** (30s via `concurrent.futures.ThreadPoolExecutor`)
3. **Data deletion** endpoint `DELETE /api/me` (DPDP compliance)
4. **Phase 2 storage decision** (Cloudflare R2 vs Google Drive)
5. **Google OAuth verification** (started Day 0, takes 4-6 weeks)

# Phase 2 — Backup Storage (after first 10 real users)

See design doc section "Phase 2 — Drive / R2".

---

# Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| pdfplumber fails on real PDFs | M | H | D0.5 smoke test; fallback to pypdf/pymupdf |
| Supabase rate limits free tier | L | M | Free tier = 50K MAU; sufficient for V1 |
| Single Fly machine = SPOF | H | M | Acceptable for V1 (privacy > uptime) |
| PocketBase corrupts on crash | L | H | Persistent volume snapshots via `fly volumes snapshot` |
| Google OAuth verification rejected | M | H | 100-user cap until approved; throttle signups |
| User isolation bug leaks data | L | C | D1.2 + D1.3 tests; D3.6 manual verification |

---

# Daily standup template

End of each day, log to a session note:

```
Day N — YYYY-MM-DD
Done:
  - [ ] task
Blocked:
  - [ ] task — reason
Tomorrow:
  - [ ] task
Tests passing: X/Y
```
