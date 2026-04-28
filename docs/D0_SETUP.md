# Day 0 — Pre-flight Setup

**Goal:** Provision all external accounts, secrets, and tooling so Day 1 implementation runs without blockers.

**Time budget:** 2-3 hours, parallel work possible.

**Outputs:** A working `.env`, validated PocketBase binary, confirmed PDF extraction, Fly.io account ready.

---

## Checklist (skim before starting)

- [ ] D0.1 Supabase project provisioned + Google provider enabled
- [ ] D0.2 Google OAuth verification submitted (4-6 week review starts now)
- [ ] D0.3 Fly.io account + CLI + volume + secrets
- [ ] D0.4 PocketBase binary downloaded + collections schema written
- [ ] D0.5 pdfplumber smoke test passing on 3 fixture PDFs
- [ ] `.env` file at `/home/shourya/code/.env` with all required vars

---

## D0.1 — Supabase project + Google OAuth wiring

**Owner:** You (browser, ~20 min)
**Outputs:** `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`

### Step 1 — Create Supabase project

1. Visit https://supabase.com → "Sign up" (use GitHub or Google for SSO).
2. Click **New Project**:
   - **Name:** `auditos`
   - **Database password:** click "Generate a password" → save in password manager (you'll rarely use this; PocketBase replaces Supabase DB for our app).
   - **Region:** `Southeast Asia (Singapore)` — closest to India users.
   - **Plan:** Free.
3. Wait ~2 min for provisioning. Dashboard opens automatically.

### Step 2 — Grab project URL + publishable key

1. Sidebar → **Project Settings** (gear icon) → **API**.
2. Copy **Project URL** → save as `SUPABASE_URL`.
3. Same page → click **API Keys** tab.
4. Click **Create new API Keys** (top right) if no publishable key exists yet.
5. Copy the `sb_publishable_...` key → save as `SUPABASE_PUBLISHABLE_KEY`.

> **Why publishable, not anon?** Supabase is migrating from legacy HS256 + anon key to modern asymmetric (ES256/RS256) + publishable key. JWKS endpoint replaces shared JWT secret. Future-proof from day one.

### Step 3 — Get Supabase callback URL for Google

1. Sidebar → **Authentication** → **Providers** → click **Google**.
2. Copy the **Callback URL (for OAuth)** — looks like:
   ```
   https://<project-ref>.supabase.co/auth/v1/callback
   ```
   `<project-ref>` is the unique slug in your `SUPABASE_URL`.

### Step 4 — Create Google OAuth client

1. Visit https://console.cloud.google.com → create new project `auditos-auth` (or reuse existing).
2. Sidebar → **APIs & Services** → **OAuth consent screen**:
   - **User type:** External → Create.
   - **App name:** AuditOS
   - **User support email:** your email
   - **App logo:** optional (helps with verification)
   - **Application home page:** `https://yourdomain.com` (placeholder OK now)
   - **Developer contact email:** your email
   - Click **Save and Continue**.
3. **Scopes** step → Add `openid`, `email`, `profile` → Save and Continue.
4. **Test users** → Add your Gmail address (and 1-2 friends). Required until verification approved.
5. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**:
   - **Type:** Web application
   - **Name:** AuditOS Supabase
   - **Authorized JavaScript origins:** add `http://localhost:5173` (dev) and `https://yourdomain.com` (prod, if known)
   - **Authorized redirect URIs:** paste the Supabase callback URL from Step 3
   - Click **Create**.
6. Copy **Client ID** and **Client Secret** from the popup → save as `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`.

### Step 5 — Wire Google secrets into Supabase

1. Back to Supabase → **Authentication** → **Providers** → **Google**:
   - Toggle **Enable Sign in with Google** ON.
   - Paste **Client ID (for OAuth)**.
   - Paste **Client Secret (for OAuth)**.
   - Click **Save**.

### Step 6 — Configure Site URL + redirect allowlist

1. Supabase → **Authentication** → **URL Configuration**:
   - **Site URL:** `http://localhost:5173` (dev). Change to `https://yourdomain.com` later.
   - **Redirect URLs:** add all of:
     - `http://localhost:5173/**`
     - `https://yourdomain.com/**`
     - `https://auditos.fly.dev/**`
   - Click **Save**.

> Without redirect allowlist, OAuth completes at Supabase but redirect to your app fails silently.

### Validation

```bash
python3 <<'EOF'
import json, urllib.request
env = {}
with open("/home/shourya/code/.env") as f:
    for line in f:
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.strip().partition("=")
            env[k.strip()] = v.strip()

base = env["SUPABASE_URL"]
pub = env["SUPABASE_PUBLISHABLE_KEY"]

# JWKS endpoint should return ES256 keys
with urllib.request.urlopen(f"{base}/auth/v1/.well-known/jwks.json", timeout=5) as r:
    keys = json.loads(r.read()).get("keys", [])
    assert len(keys) >= 1, "JWKS empty"
    print(f"JWKS: {len(keys)} keys, alg={keys[0].get('alg')}")

# Auth settings should show Google enabled
req = urllib.request.Request(f"{base}/auth/v1/settings", headers={"apikey": pub})
with urllib.request.urlopen(req, timeout=5) as r:
    data = json.loads(r.read())
    assert data["external"]["google"], "Google provider not enabled"
    print(f"Google provider: enabled")

print("\nD0.1 PASSED")
EOF
```

**Pass criteria:** Output shows `JWKS: N keys, alg=ES256` and `Google provider: enabled`.

---

## D0.2 — Google OAuth verification (start NOW, completes in 4-6 weeks)

**Owner:** You (browser, ~30 min one-time)
**Why:** Unverified OAuth app caps signups at 100 test users. Verification removes the cap.

### Steps

1. Google Cloud Console → **APIs & Services** → **OAuth consent screen** → **Edit App**.
2. Confirm app info is complete:
   - App logo uploaded (recommended, speeds review)
   - Privacy policy URL: must be hosted publicly. If no domain, use a Notion/Google Doc page with "AuditOS Privacy Policy".
   - Terms of service URL: same approach.
   - Authorized domains: add your domain root (e.g., `yourdomain.com`).
3. **Scopes** tab → confirm only `openid`, `email`, `profile`. (Don't request restricted scopes like Drive yet — auto-rejects.)
4. Click **Submit for verification**.
5. Google emails questions within ~1 week. Respond promptly. Total review: 4-6 weeks.

### Mitigation while pending

- 100-user test cap is fine for V1 launch (more than enough for first feedback batch).
- Test users list (added in D0.1 Step 4.4) can be expanded any time without verification.

---

## D0.3 — Fly.io account + CLI + volume + secrets

**Owner:** You (CLI, ~15 min)

### Step 1 — Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
# Add to PATH if installer didn't (check ~/.fly/bin)
export PATH="$HOME/.fly/bin:$PATH"
fly version
```

### Step 2 — Sign up + login

```bash
fly auth signup    # opens browser; or `fly auth login` if you have account
```

Free Fly tier: 3 shared-cpu VMs, 3GB persistent storage, 160GB bandwidth/month.

### Step 3 — Create app + volume

```bash
cd /home/shourya/code/pikachu-bunny

# Create app (without deploying)
fly launch --no-deploy --name auditos --region bom --copy-config

# Create persistent volume (10GB, Mumbai region)
fly volumes create auditos_data --region bom --size 10
```

Confirm with `fly volumes list`.

### Step 4 — Set production secrets

```bash
# Read values from local .env (don't paste secrets in shell history)
set -a; source /home/shourya/code/.env; set +a

fly secrets set \
  SUPABASE_URL="$SUPABASE_URL" \
  SUPABASE_PUBLISHABLE_KEY="$SUPABASE_PUBLISHABLE_KEY" \
  PB_ADMIN_EMAIL="$PB_ADMIN_EMAIL" \
  PB_ADMIN_PASSWORD="$PB_ADMIN_PASSWORD"
```

### Validation

```bash
fly secrets list   # shows 4 secrets, values masked
fly volumes list   # shows auditos_data, 10GB, region bom
```

**Pass criteria:** 4 secrets listed (no `SUPABASE_JWT_SECRET` legacy), volume exists.

> **Skip Step 3-4 if not deploying yet.** D0.3 can be deferred to D3 if you want to focus on local dev first. But Fly account creation is fast — do at least Step 1-2 now.

---

## D0.4 — PocketBase binary + collections schema

**Owner:** You (CLI, ~20 min)
**Outputs:** Working PocketBase running on `localhost:8090`, all 5 collections created.

### Step 1 — Download PocketBase binary

```bash
mkdir -p /home/shourya/code/pikachu-bunny/infra/pocketbase
cd /home/shourya/code/pikachu-bunny/infra/pocketbase

# v0.22+ Linux amd64
curl -L -o pb.zip \
  https://github.com/pocketbase/pocketbase/releases/download/v0.22.21/pocketbase_0.22.21_linux_amd64.zip
unzip -o pb.zip
chmod +x pocketbase
rm pb.zip CHANGELOG.md LICENSE.md
./pocketbase --version
```

### Step 2 — Add to .gitignore

Append to `/home/shourya/code/pikachu-bunny/.gitignore`:
```
infra/pocketbase/pocketbase
infra/pocketbase/pb_data/
```

### Step 3 — First-run admin setup

```bash
cd /home/shourya/code/pikachu-bunny/infra/pocketbase
./pocketbase serve --http=0.0.0.0:8090
```

Open http://localhost:8090/_/ in browser:
- First load shows "Create admin" form
- Use the email + password from `PB_ADMIN_EMAIL` and `PB_ADMIN_PASSWORD` in `.env`
- Click **Create and login**

### Step 4 — Create 5 collections

In PocketBase admin UI, sidebar → **Collections** → **+ New collection** for each below. Use type "Base collection" for all.

#### Collection: `audits`
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| user_id | text | yes | Indexed |
| state | text | yes | enum value (empty/processing/clean/etc.) |
| truth_score | number | yes | 0-100 |
| scoped_score_copy | text | yes | display copy |
| clean_months | number | no | default 0 |
| open_findings | number | no | default 0 |
| evidence_ready_findings | number | no | default 0 |

Indexes: create `idx_audits_user` on `user_id`.

#### Collection: `sources`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | text (or relation→audits) | yes |
| source_type | text | yes |
| filename | text | yes |
| content_hash | text | yes |

Indexes: `idx_sources_user_audit` on `(user_id, audit_id)`.

#### Collection: `evidence_snippets`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | text | yes |
| source_id | text | yes |
| text | text | yes |
| period | text | no |
| label | text | no |
| masked | bool | no |

Indexes: `idx_evidence_user_audit` on `(user_id, audit_id)`.

#### Collection: `findings`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | text | yes |
| state | text | yes |
| severity | text | yes |
| title | text | yes |
| explanation | text | yes |
| result_code | text | yes |
| period | text | no |
| evidence_ids | json | no |

Indexes: `idx_findings_user_audit` on `(user_id, audit_id)`.

#### Collection: `jobs`
| Field | Type | Required |
|-------|------|----------|
| user_id | text | yes |
| audit_id | text | yes |
| status | text | yes (queued/running/completed/failed/interrupted) |
| error_message | text | no |

Indexes: `idx_jobs_status` on `status`, `idx_jobs_user` on `user_id`.

### Step 5 — Leave collection rules empty

For each collection, leave **API Rules** blank (no listRule, viewRule, createRule, etc.). The FastAPI backend uses admin token + manual `user_id` filter — collection rules would be defense-in-depth but for V1 they're not required.

> **Critical:** Manual `user_id` filter in `pocketbase_client.py` is the ONLY isolation. Day 1 tests must verify cross-user reads return empty.

### Validation

```bash
python3 <<'EOF'
import json, urllib.request
collections = ["audits", "sources", "evidence_snippets", "findings", "jobs"]
for col in collections:
    try:
        with urllib.request.urlopen(f"http://localhost:8090/api/collections/{col}/records?perPage=1", timeout=3) as r:
            data = json.loads(r.read())
            print(f"  {col}: OK (totalItems={data.get('totalItems', 0)})")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  {col}: exists (403 = rules empty, expected)")
        elif e.code == 404:
            print(f"  {col}: MISSING")
        else:
            print(f"  {col}: HTTP {e.code}")
print("\nD0.4 PASSED if all 5 show OK or '403 = rules empty'")
EOF
```

**Pass criteria:** 5 collections respond (200 with empty list, or 403 rules-empty — both fine).

---

## D0.5 — pdfplumber smoke test (CRITICAL)

**Owner:** You (CLI, ~5 min)
**Why:** pdfplumber on Indian salary slips is unproven. If extraction fails, swap library before D1.5 wires upload endpoint.

### Step 1 — Install pdfplumber

```bash
cd /home/shourya/code/pikachu-bunny/backend
pip install pdfplumber
```

### Step 2 — Run extraction smoke test

```bash
python3 <<'EOF'
import pdfplumber
fixtures = [
    "tests/fixtures/personas/ananya-salary-slip.pdf",
    "tests/fixtures/personas/rohan-salary-slip.pdf",
    "tests/fixtures/personas/meera-salary-slip.pdf",
]
expected_keywords = ["basic", "pf", "epf", "provident", "salary", "wage"]
results = []
for f in fixtures:
    try:
        with pdfplumber.open(f) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        char_count = len(text)
        text_lower = text.lower()
        matches = [kw for kw in expected_keywords if kw in text_lower]
        ok = char_count > 100 and len(matches) >= 2
        results.append((f, ok, char_count, matches))
        flag = "PASS" if ok else "FAIL"
        print(f"  [{flag}] {f.split('/')[-1]}: {char_count} chars, keywords={matches}")
    except Exception as e:
        results.append((f, False, 0, []))
        print(f"  [ERROR] {f}: {e}")

failed = [r for r in results if not r[1]]
if failed:
    print(f"\nD0.5 FAILED: {len(failed)} fixture(s) did not extract usable text.")
    print("Mitigation: try `pip install pypdf` or `pip install pymupdf` and retest with that library.")
else:
    print(f"\nD0.5 PASSED: pdfplumber extracts text from all {len(fixtures)} fixtures.")
EOF
```

### Pass criteria

- All 3 fixtures extract >100 chars
- All 3 contain ≥2 expected keywords (basic, pf, epf, etc.)

### Failure mitigation

If pdfplumber returns empty/garbled text:

1. Try **pypdf** (different parser, sometimes better on certain PDFs):
   ```bash
   pip install pypdf
   python3 -c "from pypdf import PdfReader; print(PdfReader('tests/fixtures/personas/ananya-salary-slip.pdf').pages[0].extract_text()[:500])"
   ```
2. Try **pymupdf** (fastest, best fidelity, GPL license caveat):
   ```bash
   pip install pymupdf
   python3 -c "import fitz; doc=fitz.open('tests/fixtures/personas/ananya-salary-slip.pdf'); print(doc[0].get_text()[:500])"
   ```
3. If all 3 libraries fail: fixtures may be image-only (scanned). V1 rejects OCR-only PDFs anyway (per `TODOS.md`). Document the limitation and ship with text-PDF-only support.

Update `IMPLEMENTATION_PLAN.md` D1.1 dependency list with whichever library passes.

---

## Final D0 checklist

Run all validations, then check off:

- [ ] **D0.1:** JWKS reachable, Google provider enabled (validation script passed)
- [ ] **D0.2:** OAuth verification submitted (email confirmation received from Google)
- [ ] **D0.3:** `fly secrets list` shows 4 secrets, `fly volumes list` shows volume
- [ ] **D0.4:** All 5 PocketBase collections exist (validation script passed)
- [ ] **D0.5:** pdfplumber extracts text from all 3 fixture PDFs (or alternate library chosen)

**`.env` final state** at `/home/shourya/code/.env`:
```
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
GOOGLE_OAUTH_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-...
PB_ADMIN_EMAIL=admin@auditos.local
PB_ADMIN_PASSWORD=<strong-password-no-angle-brackets>
POCKETBASE_URL=http://localhost:8090
```

> `GOOGLE_OAUTH_CLIENT_*` are kept for reference / future re-config of Supabase. Backend never reads them — only Supabase dashboard does.

> Do NOT include `SUPABASE_ANON_KEY` or `SUPABASE_JWT_SECRET` (legacy HS256 path; we use JWKS).

---

## Troubleshooting

### "OAuth Error: redirect_uri_mismatch"
- Google OAuth client's "Authorized redirect URIs" doesn't include the exact Supabase callback URL.
- Fix: copy URL from Supabase → Auth → Providers → Google → paste into Google Cloud Console credentials.

### "Provider is not enabled"
- Supabase → Auth → Providers → Google toggle is OFF.
- Fix: enable + save.

### PocketBase admin UI shows "Database is locked"
- Another `pocketbase serve` process running.
- Fix: `pkill -f pocketbase` then restart.

### pdfplumber returns empty string
- PDF is image-only (scanned). No text layer.
- Fix: V1 rejects these. Use text-PDF fixtures only.

### Fly volume creation fails: "region not available"
- Free tier may not have Mumbai. Try `sin` (Singapore) or `nrt` (Tokyo).
- Fix: `fly volumes create auditos_data --region sin --size 10`

---

## Next: Day 1 (backend implementation)

After all D0 checks pass, proceed to `IMPLEMENTATION_PLAN.md` → "Day 1 — Backend".

D1 needs: working Supabase JWKS (D0.1), running PocketBase (D0.4), confirmed PDF extraction library (D0.5). D0.3 (Fly.io) can wait until D3.
