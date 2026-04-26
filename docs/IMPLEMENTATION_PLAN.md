# Phased Implementation Plan

## Phase 1: Foundation

Goal: create a runnable, testable shell with contracts shared by backend and frontend.

- FastAPI app with health and contract metadata endpoints.
- Typed backend contracts for audit states, job states, result codes, sources, facts, evidence, and findings.
- React/Vite shell with static AuditOS-inspired UI placeholders.
- Dockerfile, production compose, dev compose, and Docker privacy check.
- CI skeleton for backend, frontend, Docker privacy, and image publish.

Exit criteria:

- `pytest` passes.
- `npm test -- --run` passes.
- `python3 scripts/check-docker-privacy.py` passes.
- Commit and push to `main`.
- Save context.

## Phase 2: Truth Engine

Goal: implement synthetic fixtures, parsers, normalization, redaction, storage, and reconciliation.

- Synthetic salary slip and EPF passbook fixtures.
- Text parsers with typed `Result` objects.
- Amount/month/employer normalization.
- SQLite storage for sources, facts, snippets, findings, and audits.
- Redaction service for PAN, UAN, account numbers, phone, email, address, employee ID.
- EPF reconciliation decision tree.

Exit criteria:

- Parser, storage, redaction, and reconciliation pytest coverage.
- Commit and push.
- Save context.

## Phase 3: Product Flow

Goal: connect the engine to the user-facing app.

- Import endpoint, job status endpoint, audit read endpoint.
- One active job per audit, bounded queue, cancel support.
- UI import guide, job progress, dashboard states, timeline, evidence drawer.
- Frontend state tests for loading, partial, clean, mismatch, needs review, unsupported, failed, cancelled.

Exit criteria:

- Backend and frontend tests pass.
- Critical path works locally.
- Commit and push.
- Save context.

## Phase 4: Review, QA, Hardening

Goal: run review and QA loops, then fix what they find.

- Run `/review` equivalent on the diff.
- Implement review fixes.
- Run `/qa` equivalent: backend tests, frontend tests, Docker privacy, Docker build, and browser smoke if available.
- Implement QA fixes.
- Final commit, push, readiness report.
