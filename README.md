# Pikachu Bunny

Privacy-first EPF contribution audit for Indian salaried employees.

V1.0 focuses on one narrow truth check: salary slip PF expectations versus EPF passbook credits. Files stay local. The app stores normalized facts, findings, source metadata, hashes, and masked evidence snippets, not raw documents by default.

## Current Status — v0.1.1 (QA-verified, Docker ship-ready)

Exhaustive browser QA pass completed against the production Docker image. All critical and high findings fixed:

- **Core flow**: POST import → background job → poll → GET audit works end-to-end in Docker
- **Persistence**: audit survives container restart via `~/.audit-os/data` host volume
- **Privacy**: port binds `127.0.0.1:8000` only — verified in smoke tests and CI gate
- **Accessibility**: keyboard focus ring (`button:focus-visible`) added — WCAG 2.1 AA
- **Responsive**: mobile/tablet breakpoints improved; buttons go full-width at ≤900px
- **Page title**: "AuditOS — Local EPF Audit" (was internal codename)
- **Multi-arch Docker**: `linux/amd64` and `linux/arm64` both build and pass smoke tests
- **CI**: PR builds use fast single-arch; main push triggers multi-arch buildx push to GHCR

All 39 backend tests and 4 frontend tests pass. Docker image runs as non-root `appuser` with a passing healthcheck.

See [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) for remaining deferred scope.

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Docker

Development, with API and UI hot reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Production-style local run:

```bash
mkdir -p ~/.audit-os/data
docker compose up --build
```

The host port must bind to `127.0.0.1`, not all network interfaces. The app handles private financial evidence.

## Graphify

Graphify is configured as the local code navigation index. The generated files live in `graphify-out/` and are intentionally ignored by Git.

```bash
graphify update .
graphify hook status
```

The post-commit hook runs `graphify update .` after commits so the local graph stays current. Before broad codebase exploration, read `graphify-out/GRAPH_REPORT.md` and query `graphify-out/graph.json`.

## Tests

```bash
pytest
cd frontend && npm test -- --run
python3 scripts/check-docker-privacy.py
```
