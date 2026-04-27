# Pikachu Bunny

Privacy-first EPF contribution audit for Indian salaried employees.

V1.0 focuses on one narrow truth check: salary slip PF expectations versus EPF passbook credits. Files stay local. The app stores normalized facts, findings, source metadata, hashes, and masked evidence snippets, not raw documents by default.

## Current Status

Phase 3 import flow is complete:

- FastAPI backend with import/job/audit endpoints and SQLite storage
- React/Vite frontend with working sample import and mismatch detection
- Docker production image and dev compose skeleton
- Synthetic EPF/salary fixtures, parsers, redaction, reconciliation, and full test coverage
- Graphify local code navigation integrated

See [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) for Phase 4 hardening and release preparation.

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
