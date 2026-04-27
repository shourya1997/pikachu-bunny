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

## Phase 3: Product Flow (Completed)

Goal: connect the engine to the user-facing app.

- Import endpoint, job status endpoint, audit read endpoint.
- One active job per audit, bounded queue, cancel support.
- UI import guide, job progress, dashboard states, timeline, evidence drawer.
- Frontend state tests for loading, partial, clean, mismatch, needs review, unsupported, failed, cancelled.

Exit criteria:

- ✅ Backend and frontend tests pass.
- ✅ Critical path works locally.
- ✅ Committed and pushed (`afd309a`, `dc96bea`).
- ✅ Context saved.

## Phase 4: Review, QA, Hardening (Completed)

Goal: run review and QA loops, then fix what they find.

- ✅ Review fixes: test DB isolation, route shadowing removed, evidence hydration, cancel race fixed.
- ✅ QA fixes: input validation, CORS hardening, redaction fallback patterns.
- ✅ Backend tests: 39 passed.
- ✅ Frontend tests: 4 passed.
- ✅ Docker privacy check passed.
- ✅ HTTP smoke test passed.
- ✅ Committed and pushed (`dc96bea`).

## Phase 5: Release Preparation

Goal: finalize documentation and prepare for first release.

- Update all documentation to reflect current state.
- Browser-based QA verification.
- Docker image build verification.
- Version bump decision.
- Release notes preparation.
