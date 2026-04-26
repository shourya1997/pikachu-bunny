---
status: REVIEW_INPUT
source: DESIGN.md + design-board feedback
---

# Financial Truth App Plan Review Input

Generated for `/plan-ceo-review` on 2026-04-26.

## Product Thesis

Build a privacy-first app for Indian salaried employees that reconciles financial and employment records across bank statements, EPF/UAN passbooks, salary slips, Form 16, AIS, and Form 26AS.

The product should act as a local financial truth checker. It should find mismatches, explain what evidence supports each finding, and produce action-ready packets for HR, EPFO, or CA review.

## Target User

Indian salaried employees who have scattered salary, tax, and provident fund records and do not know whether their employer, bank, EPF, and tax records agree.

## Core Outcome

The user should answer three questions quickly:

1. Are my salary, PF, and tax records consistent?
2. If not, what exactly is wrong and where is the evidence?
3. What should I do next, and what message or packet can I send?

## Selected Product Direction

The current approved direction is:

- Dashboard first.
- Month-wise audit second.
- Action packet third.

The primary layout is the Financial Control Room dashboard. It shows a truth score, clean months, open issues, ready packets, and local mode. It also shows priority findings and a recommended next action.

The secondary layout is the Timeline Investigator drilldown. Each dashboard finding opens a month-wise detail view that explains what matched, what failed, and which documents produced the conclusion.

The action-packet layer generates redacted packets and draft emails, but it is downstream of the dashboard and timeline.

## Design System

Use `AuditOS`, a hybrid of:

- Stripe-inspired financial precision.
- Linear-inspired workflow clarity.
- Revolut-inspired consumer fintech energy.

The interface should feel modern, trustworthy, private, and action-oriented. It should not feel like a government portal, spreadsheet, or crypto app.

## Long-Term Functional Scope

The long-term app should support:

- Local document import for bank statements, EPF/UAN passbooks, salary slips, Form 16, AIS, and Form 26AS.
- Canonical extraction of monthly salary, PF, employer, TDS, and tax reporting facts.
- A local reconciliation model that compares facts across sources.
- A dashboard summary with truth score, clean months, open issues, ready packets, and local mode.
- A priority findings queue.
- A month-wise audit drilldown.
- Evidence chips and an inspectable evidence trail.
- Redaction controls before export.
- Draft HR/EPFO/CA messages.
- Exportable dispute or review packets.

## V1 Accepted Scope

V1 is narrower than the long-term scope. The first useful product is an EPF contribution truth checker:

- Supported sources: salary slip fixtures and EPF passbook fixtures.
- Supported comparison: monthly employee PF and employer PF expected from salary slip versus credited in EPF passbook.
- Supported output for V1.0: dashboard finding, month-wise timeline, evidence drawer, scoped Truth score copy, local API job states, and masked evidence snippets.
- Supported output for V1.1: redaction preview, packet review screen, and packet export for the selected finding.
- Unsupported in v1: bank statements, Form 16, AIS, Form 26AS, CA workflows, browser automation, credential capture, and multi-bank support.

## Release Slices

Proof 0:

- Import one salary slip fixture and one EPF passbook fixture.
- Extract canonical facts from both.
- Run one reconciliation rule.
- Show one finding view with evidence references.
- No packet export, no contributor guide, no browser automation.

V1.0:

- Add local FastAPI API plus web UI, dashboard, timeline, confidence states, partial states, unsupported states, bounded background jobs, local storage versioning, and masked evidence snippets.
- Add fixture corpus with golden outputs for one EPF passbook format and two salary slip formats.
- Add pytest backend tests, Vitest frontend state tests, and Playwright critical-path E2E tests.
- Add Docker support: multi-container docker-compose for development (FastAPI + UI hot-reload), single production image via Dockerfile, GitHub Actions CI that builds and publishes to ghcr.io on merge to main.
- Data volume: mount `~/.audit-os/data` on the host to `/app/data` in the container. Container must bind to `127.0.0.1` only, never `0.0.0.0`.

V1.1:

- Add redaction preview, packet export, factual message templates, and contributor guide.
- This remains in the reviewed plan, but it should not block the first proof.

## Constraints

- Privacy-first and local-first by default.
- No external upload required for core reconciliation.
- Redacted exports only when the user chooses to share.
- The product must clearly separate confirmed mismatches from review-needed warnings.
- The product must not present generated text as legal, tax, or accounting advice.

## Open Questions

- Which packaging layer should follow Docker: desktop wrapper (electron/tauri) or signed installer, now that Docker is the V1.0 distribution path?
- Which source connector should ship first: EPF/UAN, bank statements, salary slips, Form 16, AIS, or Form 26AS?
- What canonical schema should be public and stable for open-source contributors?
- How should the app verify source authenticity without collecting credentials?
- What is the minimum useful packet that an HR team, EPFO grievance, or CA can act on?

## Known User Feedback

The user preferred the dashboard with all information and findings. The user also liked the month-wise detailed view.

## Not Yet Planned

- Exact parser libraries for the first EPF passbook and salary slip fixture formats.
- Public contributor-facing canonical schema.
- Desktop wrapper or signed installer after Docker distribution is validated.
- Docker image signing and attestation (cosign) after the initial ghcr.io publish workflow is stable.
- Threat model.
- Contributor workflow for open-source connectors.
- Regulatory disclaimers and guardrails.

## V1 Product Definitions

Truth score:

- `100`: all supported months match across salary slip and EPF passbook.
- `70-99`: at least one low-confidence source or review-needed item, but no confirmed mismatch.
- `1-69`: one or more confirmed contribution mismatches.
- `0`: no audit can run because required sources are missing or unreadable.

Clean month:

- A month where salary slip PF facts and EPF passbook contribution facts match within the configured rupee tolerance and both sources have confidence `high` or `medium`.

Priority finding:

- Ordered by confirmed mismatch first, then missing EPF month, then employer identity conflict, then low-confidence review item. Ties sort by latest month first.

Ready packet:

- A packet is ready only when every included evidence snippet has passed redaction preview and every finding has confidence `confirmed` or `needs_review`. No packet may include raw PAN, UAN, bank account number, or full document dump by default.

Confidence states:

- `confirmed`: two supported sources disagree or agree with high-confidence parsed facts.
- `needs_review`: facts are plausible but source confidence, employer identity, or parser coverage is not enough for a confirmed conclusion.
- `unsupported`: the file format or data shape is outside v1 support.
- `failed`: the source could not be parsed safely.

## V1 Data Contracts

Canonical fact:

```json
{
  "id": "fact_...",
  "sourceId": "source_...",
  "sourceType": "salary_slip|epf_passbook",
  "period": "YYYY-MM",
  "employerName": "string",
  "employeePfAmount": 0,
  "employerPfAmount": 0,
  "currency": "INR",
  "confidence": "confirmed|needs_review|unsupported|failed",
  "evidenceRef": "evidence_..."
}
```

Finding:

```json
{
  "id": "finding_...",
  "period": "YYYY-MM",
  "type": "pf_amount_mismatch|missing_epf_month|employer_identity_conflict|low_confidence_parse",
  "severity": "high|medium|low",
  "status": "confirmed|needs_review",
  "sourceFactIds": ["fact_..."],
  "recommendedAction": "contact_hr|review_source|export_packet"
}
```

Storage version:

- Store local data under a versioned root: `{ "schemaVersion": 1, "sources": [], "facts": [], "findings": [] }`.
- Any future schema change must include a local migration or a clear reset path before release.

Redaction checklist:

- Mask PAN, UAN, bank account numbers, full address, phone numbers, email addresses, and employee IDs by default.
- Show amount, month, employer name, and contribution category unless the user manually masks them.
- Block export if any required redaction rule has not run.

## V1 Acceptance Criteria

Proof 0 passes when:

- A supported salary slip fixture imports without credentials or network access.
- A supported EPF passbook fixture imports without credentials or network access.
- Both fixtures produce canonical facts that match the schema above.
- One exact-match case returns no confirmed finding.
- One mismatch case returns a confirmed `pf_amount_mismatch` finding.
- The finding view shows month, expected amount, observed amount, source labels, confidence, and evidence references.
- Unsupported fixture formats return `unsupported`, not a false mismatch.

V1.0 passes when:

- Dashboard shows truth score, clean months, open findings, partial import state, and unsupported source state.
- Timeline groups findings by month and distinguishes confirmed from needs-review states.
- Evidence drawer opens for every finding and never reads raw connector-specific parser output directly.
- Local storage includes `schemaVersion: 1` and can reload sources, facts, and findings.
- Fixture tests cover nil input, empty file, unsupported layout, invalid month, duplicate file, exact match, mismatch, and employer identity conflict.

V1.1 passes when:

- Packet export is blocked until redaction preview runs.
- Default redaction masks PAN, UAN, account numbers, address, phone, email, and employee ID.
- Packet language states evidence and uncertainty without giving legal, tax, or accounting advice.
- Export failures show a user-safe error and do not lose local audit data.

---

# CEO Review Report

Status: REVIEWED
Mode: SELECTIVE EXPANSION
Selected approach: Connector toolkit plus local truth graph vertical slice
First wedge: EPF contribution check, salary slip PF versus EPF passbook

## System Audit

This workspace is not currently a git repository, so there is no base branch, diff, PR target, commit history, or stash to inspect. I found `DESIGN.md`, `CLAUDE.md`, the saved design board decision, and no existing `TODOS.md` or architecture document.

Relevant project artifacts:

- `/Users/shourya/personal/DESIGN.md`
- `/Users/shourya/.gstack/projects/personal/designs/financial-truth-graph-20260426-132158/approved-direction.json`
- `/Users/shourya/.gstack/projects/personal/ceo-plans/2026-04-26-financial-truth-app-review-input.md`

Landscape check: existing tax apps like ClearTax, EZTax, and TaxBuddy focus heavily on ITR filing, Form 16 upload, AIS/Form 26AS checks, and filing assistance. The white space is not "another tax filing app." The white space is a privacy-first local evidence engine that explains salary, EPF, and tax truth before a user files, complains, or asks HR.

## 0A. Premise Challenge

Premise 1: Indian salaried employees have real reconciliation pain.

Verdict: valid. Search results show recurring Form 16, AIS, Form 26AS, and EPF mismatch problems that can cause tax notices, refund delays, HR corrections, and EPFO grievances.

Premise 2: A local-first app is meaningfully differentiated.

Verdict: valid but must be earned. Privacy matters here because the documents include PAN, UAN, salary, employer, bank, and tax data. The product cannot merely say "local-first"; it needs visible redaction, no credential capture, and source confidence states.

Premise 3: "All banks, EPF, UAN, etc." is a good v1 scope.

Verdict: too broad. That phrase is the long-term ambition, not the first wedge. Day one should prove one high-value mismatch very well: salary slip PF versus EPF passbook.

Premise 4: Action-ready packets are the user-facing payoff.

Verdict: valid. Finding a mismatch is not enough. The user needs the evidence, plain-English explanation, and a safe message or packet they can send to HR or EPFO.

## 0B. Existing Code Leverage

There is no application code to reuse yet. The reusable assets are product and design artifacts.

| Sub-problem | Existing leverage | Gap |
|---|---|---|
| Visual direction | `DESIGN.md` defines AuditOS and the B+D layout direction | Needs screen specs and states |
| Product positioning | Prior `/office-hours` work and this plan define privacy-first reconciliation | Needs a sharper first wedge |
| User feedback | `approved-direction.json` records dashboard and timeline preference | Needs implementation-ready flows |
| Skill routing | `CLAUDE.md` includes gstack routing rules | No repo/build scaffolding yet |
| Connector quality | None | Needs fixtures and golden outputs |
| Reconciliation model | None | Needs canonical fact schema and confidence model |

## 0C. Dream State Mapping

```text
CURRENT STATE
User manually compares salary slips, EPF passbook, Form 16, AIS, Form 26AS,
and bank statements. Errors are found late, usually during tax filing or after
EPF balance anxiety.

        |
        v

THIS PLAN
Local-first EPF truth checker with connector contracts, fixtures, a small
truth graph, confidence states, dashboard, timeline drilldown, redacted packet,
and no credential capture.

        |
        v

12-MONTH IDEAL
Open-source Indian financial truth graph toolkit. Contributors add connectors.
Users run private audits across salary, EPF, tax, and bank records. The app
produces evidence-backed packets for HR, EPFO, CAs, and personal records.
```

## 0C-bis. Implementation Alternatives

Approach A: Minimal vertical slice

- Summary: Build only EPF plus salary slip reconciliation with a small dashboard.
- Effort: S
- Risk: Low
- Pros: fastest proof, smallest parser surface, fewer design states.
- Cons: too narrow for the open-source connector toolkit promise, may feel like a demo.
- Reuses: `DESIGN.md` layout direction.

Approach B: Connector toolkit plus local truth graph vertical slice

- Summary: Build EPF plus salary slip reconciliation on top of a reusable connector contract, fixture corpus, fact schema, confidence states, and evidence trail.
- Effort: M
- Risk: Medium
- Pros: creates reusable foundation, supports open-source learning, still ships one real user outcome.
- Cons: more up-front schema and test design.
- Reuses: `DESIGN.md`, approved dashboard plus timeline direction.

Approach C: Full financial control room

- Summary: Build broad imports, dashboard, timeline, packet composer, tax review, CA handoff, and many document types from day one.
- Effort: XL
- Risk: High
- Pros: closest to the final product vision, strongest demo if fully executed.
- Cons: too much surface before one connector is trustworthy, likely to stall.
- Reuses: `DESIGN.md`, but little else.

Recommendation: Approach B. It is the right wedge: real product, real architecture, real learning loop.

## 0D. Selective Expansion Decisions

| # | Proposal | Decision | Reasoning |
|---|---|---|---|
| 1 | Redacted fixture corpus with golden outputs | ACCEPTED | Makes connector quality testable without private user data. |
| 2 | Source authenticity and confidence states | ACCEPTED | Prevents weak evidence from being presented as confirmed truth. |
| 3 | Import instructions for official portals | ACCEPTED WITH STAGING | Start with manual instructions. Keep architecture ready for user-controlled browser assistance, then full automation only later if safe. |
| 4 | Redaction-first packet export | ACCEPTED | Packets are the moment private data leaves the device. Preview and control are mandatory. |
| 5 | Legal and tax advice guardrails | ACCEPTED | The app should state evidence and mismatches, not pretend to be a CA or lawyer. |
| 6 | First wedge: EPF contribution check | ACCEPTED | Salary slip PF versus EPF passbook is concrete, painful, and action-ready. |

## Accepted Scope

- EPF contribution truth check: salary slip PF versus EPF passbook.
- Connector contract for source parsers.
- Local canonical fact schema for salary month, employee PF, employer PF, employer identity, document source, date, and confidence.
- Local truth graph storing extracted facts, evidence pointers, confidence states, and mismatch conclusions.
- Redacted fixture corpus with golden outputs.
- AuditOS dashboard using Financial Control Room as the home screen.
- Timeline Investigator drilldown for month-wise mismatch explanation.
- Source authenticity and confidence states.
- Manual import instructions for EPF passbook and salary slips.
- Architecture extension point for later user-controlled browser-assisted imports.
- Redaction-first packet export in V1.1.
- Guardrails that separate factual mismatch language from legal, tax, or accounting advice.

## Deferred to TODOS.md

- Fully automated portal login or scraping.
- Browser-assisted import beyond user-controlled guidance.
- Tax TDS check across Form 16, AIS, and Form 26AS.
- Salary credit check across bank statements and salary slips.
- CA marketplace, HR directory, or third-party filing workflow.
- Multi-bank connector support.
- Mobile app packaging.

## 0E. Milestone Interrogation

```text
MILESTONE 1: Foundation
  Local web app shell, source connector interface, canonical fact schema,
  fixture folder structure, and local storage version.

MILESTONE 2: First truth check
  Salary slip and EPF passbook fixture parsers, golden outputs, fact
  validation, and PF mismatch rules.

MILESTONE 3: Trust UI
  Dashboard, timeline drilldown, confidence labels, partial states,
  unsupported states, and evidence drawer.

MILESTONE 4: Safe action
  Redaction preview, packet export for selected findings, factual message
  templates, tests, and contributor guide.
```

Key decision resolved now: start as a local web app with manual file import, not credential automation. This keeps privacy real and lets browser assistance arrive later without contaminating the core architecture.

V1 support limit: one EPF passbook format and two salary slip fixture formats are enough for the first milestone. The fixture corpus should make unsupported formats visible instead of pretending the parser is universal.

## Section 1: Architecture Review

Recommended architecture:

```text
Web UI
  |-- import guide
  |-- dashboard
  |-- timeline investigator
  |-- evidence drawer
  |
  v
Local FastAPI API
  |-- import endpoints
  |-- bounded job queue
  |-- polling job status
  |-- audit read endpoints
  |
  v
Built-in source connectors
  |-- salary-slip parser
  |-- epf-passbook parser
  |-- no runtime plugin loading in V1.0
  |
  v
Canonical records
  |-- sources
  |-- facts
  |-- findings
  |-- evidence snippets
  |-- audit states
  |
  v
Reconciliation rules
  |
  +--> Dashboard finding queue
  +--> Timeline Investigator
  +--> Evidence drawer
```

Happy path:

```text
Valid salary slip + valid EPF passbook
  -> FastAPI import job parses facts
  -> normalize employer/month/amounts
  -> persist normalized records and bounded evidence snippets
  -> compare employee PF and employer PF
  -> emit match or mismatch
  -> show dashboard finding
  -> open month-wise evidence
```

Nil path:

```text
Missing source file
  -> reject import
  -> show "Add salary slip" or "Add EPF passbook"
  -> no reconciliation run
```

Empty path:

```text
Readable file with zero extracted contribution rows
  -> store import attempt as failed parse
  -> show parser confidence "unsupported or empty"
  -> no confirmed mismatch
```

Error path:

```text
Parser exception or malformed file
  -> capture parser error with source type and fixture case
  -> show user-safe message
  -> preserve local debug artifact only if user opts in
```

Architecture finding: the plan needs hard boundaries between UI, API jobs, connectors, storage, and reconciliation. Connectors extract facts. Reconciliation decides audit state. The UI never reads raw parser output or full raw documents directly.

Decision: accepted into plan.

Engineering review update: V1.0 runtime is a local FastAPI API plus web UI. The API owns import jobs, parsing, normalization, local persistence, reconciliation, and audit read models. The UI owns interaction state, evidence navigation, and scoped product copy.

## Section 2: Error & Rescue Map

Normal parser and reconciliation failures are typed results, not exception-driven control flow. Unexpected crashes may still raise exceptions internally, but all API and UI-facing states use stable error codes.

| Method/codepath | What can go wrong | Result code | Rescue action | User sees |
|---|---|---|---|---|
| `POST /api/imports` | Missing file | `missing_file` | Reject import | "Choose a file to import." |
| `POST /api/imports` | Unsupported file type | `unsupported_file_type` | Reject import | "This source is not supported yet." |
| `parseSalarySlip()` | Layout not recognized | `unsupported_layout` | Mark unsupported | "We could not read this salary slip format." |
| `parseEpfPassbook()` | Empty contribution table | `no_contribution_rows` | Mark source incomplete | "No PF rows found in this file." |
| `normalizeFacts()` | Month/date cannot be parsed | `invalid_period` | Mark fact invalid | "This source has an unclear month." |
| `reconcileContributions()` | Conflicting employer names | `employer_identity_conflict` | Require review | "Employer identity needs review." |
| `redactEvidence()` | Evidence contains unmasked identifiers | `redaction_required` | Mask or block display/export | "Private identifiers were masked." |
| `GET /api/jobs/{id}` | Job cancelled | `cancelled` | Leave audit data unchanged | "Import cancelled. No audit data was changed." |

Critical rule: no catch-all user-facing parser failures. Result objects must include source type, parser version, fixture case if applicable, error code, safe user message, and whether local audit data changed.

## Section 3: Security & Threat Model

| Threat | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| Sensitive document leakage | Medium | High | Local-first processing, no default uploads, redaction preview before export. |
| Credential capture pressure | Medium | High | v1 manual import only. Later browser assistance must be user-controlled. |
| Malicious file upload | Medium | Medium | Parse in sandboxed worker, reject scripts/macros, cap file size. |
| Prompt injection in imported text | Low initially | Medium | Do not let document text directly instruct any AI system. Treat imported text as data. |
| Bad packet language treated as advice | Medium | High | Templates must state evidence, uncertainty, and "not legal/tax advice." |
| Contributor parser exfiltrates data | Medium | High | Connector contract forbids network access by default and tests run offline fixtures. |

Security finding: open-source connectors are the biggest future risk. v1 should define connector permissions early, even if the implementation is simple.

Decision: accepted into plan.

## Section 4: Data Flow & Interaction Edge Cases

```text
FILE INPUT -> VALIDATE -> PARSE -> NORMALIZE -> STORE FACTS -> RECONCILE -> DISPLAY -> EXPORT
    |            |          |          |             |             |          |          |
 missing?    wrong type? unsupported? invalid?    duplicate?    conflict?  empty?  unredacted?
 empty?      too large?  exception?   low conf?    stale?       partial?   long?   write fail?
```

Interaction edge cases:

| Interaction | Edge case | Required handling |
|---|---|---|
| Import file | User imports same file twice | Detect duplicate content hash and explain. |
| Import pair | Salary slip exists, EPF passbook missing | Show partial state, no confirmed mismatch. |
| Run audit | Parser confidence low | Show "needs review", not "confirmed problem." |
| Open finding | Evidence source missing | Keep finding but mark evidence unavailable. |
| Export packet, V1.1 | Redaction not reviewed | Block export until user confirms. |
| Mobile timeline | Long employer names or many months | Wrap names and collapse months by year. |

Finding: partial states are product states, not errors. The plan must design "one source imported" and "low-confidence parse" explicitly.

Decision: accepted into plan.

## Section 5: Code Quality Review

No code exists yet, so this section defines constraints for implementation.

Required module boundary:

- `connectors/*`: source-specific parsing only.
- `schema/*`: canonical fact types and validation.
- `truth-graph/*`: local storage and fact relationships.
- `reconciliation/*`: mismatch rules and confidence logic.
- `packets/*`: redaction and export generation.
- `ui/*`: dashboard, timeline, evidence, packet composer.

Code quality finding: do not let connector-specific weirdness leak into UI state. The UI should render canonical facts and findings only.

Decision: accepted into plan.

## Section 6: Test Review

New UX flows:

- Import salary slip.
- Import EPF passbook.
- See audit summary.
- Open mismatch finding.
- Inspect month-wise evidence.
- Preview redacted packet in V1.1.
- Export packet in V1.1.

New data flows:

- File to parsed raw fields.
- Raw fields to canonical facts.
- Canonical facts to truth graph.
- Truth graph to mismatch finding.
- Finding to evidence drawer.
- Evidence to redacted packet in V1.1.

New codepaths:

- Missing file.
- Unsupported file type.
- Unsupported salary slip layout.
- Empty EPF contribution rows.
- Month parse failure.
- Employer identity conflict.
- Amount mismatch.
- Exact match.
- Low confidence parse.
- Redaction block.

Test plan:

| Area | Test type | Required cases |
|---|---|---|
| Connector fixtures | Unit | Each fixture produces expected canonical facts. |
| Schema validation | Unit | Nil, empty, invalid date, invalid amount, unknown employer. |
| Reconciliation | Unit | Exact match, missing EPF month, amount mismatch, employer conflict. |
| Truth graph | Integration | Facts store locally and preserve evidence pointers. |
| Dashboard | Component/system | Clean state, mismatch state, partial import state, low-confidence state. |
| Timeline | Component/system | Month grouping, long labels, missing evidence. |
| Packet export | Integration | Redaction required, redaction accepted, write failure. |
| Import guide | E2E | User can import both source types without credentials. |

Hostile QA test: import a salary slip with `₹1,800.00`, an EPF row with `1800`, a different employer spelling, and an OCR-like month string. The app must not create a false mismatch if normalization can confidently resolve the values.

Chaos test: import 24 months of salary slips, then an EPF passbook missing 3 months and containing one duplicate row. The app should produce 3 missing-month findings, ignore the duplicate safely, and keep the dashboard responsive.

Finding: fixture corpus is mandatory for confidence. Without it, this app cannot be trusted.

Decision: accepted into plan.

## Section 7: Performance Review

The first version is local and file-based, so server load is not the issue. The first performance risks are file size, parser runtime, UI responsiveness, and excessive graph recomputation.

Plan requirements:

- Cap import file size per source.
- Parse in a worker or async boundary so the UI does not freeze.
- Store normalized facts separately from raw imported artifacts.
- Recompute only affected months after a new source import.
- Keep packet generation bounded to selected findings, not the full document corpus.

Finding: do not build the truth graph as a giant recompute-on-every-import object. Month-level invalidation is enough for v1.

Decision: accepted into plan.

## Section 8: Observability & Debuggability Review

For a local-first app, observability means local debug visibility, not remote telemetry by default.

Required local debug events:

- Import attempted.
- File rejected.
- Parser selected.
- Parser confidence assigned.
- Facts extracted.
- Reconciliation run.
- Finding produced.
- Packet export blocked or completed.

Debug artifact rule: if debug export exists, it must be user-triggered and redacted by default.

Finding: contributors need parser diagnostics, but users need privacy. Keep those channels separate.

Decision: accepted into plan.

## Section 9: Deployment & Rollout Review

Recommended first packaging: local web app or desktop-wrapped web app with manual file import. Do not start with hosted SaaS.

Rollout sequence:

1. Fixture corpus and schema.
2. EPF passbook connector.
3. Salary slip connector.
4. Reconciliation rules.
5. Dashboard and timeline.
6. Evidence-ready state in V1.0, redaction-first packet export in V1.1.
7. Contributor guide.

Rollback posture: since this is greenfield and local, rollback means versioned local storage plus export/import of user data. The plan must define storage versioning before real users import private documents.

Finding: storage schema versioning is easy to forget and painful to add later.

Decision: accepted into plan.

## Section 10: Long-Term Trajectory Review

Reversibility rating: 4/5 if connector contracts and canonical facts stay simple. 2/5 if UI, parsers, and reconciliation share source-specific types.

Phase 2 after EPF wedge:

- Add Form 16 versus AIS/Form 26AS TDS reconciliation.
- Add user-controlled browser-assisted import for official portals.
- Add bank salary credit check only after statement fixture coverage exists.

Phase 3:

- Multi-employer job switch handling.
- CA review packet mode.
- Connector marketplace or registry.
- Advanced browser automation only if legal, safe, and user-controlled.

Finding: the public open-source contract should be the connector contract plus fixture format, not the UI.

Decision: accepted into plan.

## Section 11: Design & UX Review

Information hierarchy:

1. Truth score and whether action is needed.
2. Priority finding with amount, month, and source conflict.
3. Evidence and confidence.
4. Recommended next action.
5. Packet export.

User flow:

```text
Start
  |
  v
Import guide
  |
  +--> Add salary slips
  |
  +--> Add EPF passbook
  |
  v
Audit dashboard
  |
  +--> Clean months
  |
  +--> Open finding
          |
          v
      Timeline Investigator
          |
          v
      Evidence drawer
          |
          v
      Evidence ready state
          |
          v
      V1.1 redaction preview and packet export
```

Interaction state coverage:

| Feature | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| Import guide | Needed | Needed | Needed | Needed | Needed |
| Dashboard | Needed | Needed | Needed | Needed | Needed |
| Timeline | Needed | Needed | Needed | Needed | Needed |
| Evidence drawer | Needed | Needed | Needed | Needed | Needed |
| Packet export | Needed | Needed | Needed | Needed | Needed |

Design finding: `DESIGN.md` is strong on atmosphere and layout, but implementation needs explicit empty, partial, and low-confidence states. These are where trust is built.

Decision: accepted into plan. Run `/plan-design-review` next before implementation.

## Design Plan Review Addendum

Status: IN_PROGRESS
Visual baseline: use the approved B+D direction from the design board. Financial Control Room is the primary screen, Timeline Investigator is the drilldown, and action packet export is third. Image generation was unavailable because the gstack designer had no OpenAI API key, so fallback HTML review artifacts were created under `~/.gstack/projects/personal/designs/financial-truth-plan-review-20260426/`.

### What Already Exists

- `DESIGN.md` defines AuditOS: off-white product canvas, white surfaces, black primary actions, purple system actions, green success, blue evidence links, red danger, amber review warnings, Inter typography, issue rows, source badges, evidence drawer, and packet composer.
- The approved product direction is dashboard first, month-wise audit second, action packet third.
- No application components exist yet, so implementation should reuse design decisions rather than code.

### Pass 1: Information Architecture

Rating before: 7/10.
Rating after: 9/10.

Decision: desktop uses a three-pane Financial Control Room. Mobile uses a single finding feed with a sticky bottom action area.

Desktop structure:

```text
APP SHELL
  |
  +-- Top summary strip
  |     +-- Truth score
  |     +-- Clean months
  |     +-- Open findings
  |     +-- Evidence-ready findings
  |     +-- Local-only status
  |
  +-- Main workspace
        |
        +-- Left pane: priority finding queue
        |     +-- confirmed mismatches first
        |     +-- missing EPF months second
        |     +-- needs-review parser/employer items third
        |
        +-- Center pane: selected finding
        |     +-- month, expected amount, observed amount
        |     +-- confidence label
        |     +-- recommended next action
        |     +-- timeline preview
        |
        +-- Right pane: evidence and action
              +-- source snippets
              +-- rule trace
              +-- masking status
              +-- V1.1 packet export controls
```

Mobile structure:

```text
TOP
  +-- Truth status
  +-- Local-only indicator

FEED
  +-- One finding card per screen section
  +-- Expandable month evidence
  +-- Expandable source snippets

STICKY BOTTOM ACTION
  +-- Primary next action
  +-- Secondary "View evidence"
  +-- Disabled export until redaction preview passes
```

The first screen must answer four questions in order:

1. Am I okay?
2. What is wrong?
3. Why does the app believe that?
4. What should I do next?

### Pass 2: Interaction State Coverage

Rating before: 4/10.
Rating after: 9/10.

Decision: every major UI surface gets explicit loading, empty, error, success, and partial states.

| Feature | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| Import guide | Show two source slots with progress text: "Reading salary slip locally..." or "Reading EPF passbook locally..." | Show two large import actions: "Add salary slip" and "Add EPF passbook", plus privacy note: "Files stay on this device." | Show source-specific user-safe message, such as "We could not read this salary slip format yet." Include "Try another file" and "See supported formats." | Show imported source cards with month range, parser confidence, and duplicate status. | If one source is imported, show "One more file needed before we can confirm a mismatch." Do not show a truth score as final. |
| Dashboard | Show skeleton summary strip and disabled finding queue with copy: "Building local audit..." | Show first-run empty state: "Start with salary slips and EPF passbook." Primary action: "Import files." | Show non-destructive banner: "Audit could not complete. Your imported files are still saved locally." | Show truth score with scoped EPF copy, clean months, open findings, evidence-ready findings, and local-only mode. | Show partial dashboard with missing source callout, no confirmed mismatch count, and a "Complete audit" action. |
| Timeline Investigator | Show month placeholders with muted status chips while facts load. | If no months exist, show "No months to inspect yet" with import action. | Show "Timeline unavailable for this finding" and keep the selected finding visible. | Show clean, mismatch, needs-review, unsupported, and missing months with distinct status colors. | Show known months and grey unknown months. Missing EPF months must not look like confirmed mismatches until source coverage is known. |
| Evidence drawer | Show source snippet placeholders and rule trace placeholder. | Show "No evidence yet" only when the finding is not confirmed. Explain what source is missing. | Show "Evidence source unavailable" and preserve finding status with lower confidence if needed. | Show salary slip snippet, EPF snippet, source labels, confidence, and rule trace. Mask PAN, UAN, employee ID, phone, email, address, and account numbers. | Show available snippets and a missing-source notice. V1.0 does not expose packet export. |
| Packet export | Show redaction scan progress: "Checking identifiers before export..." | Show "No packet ready" with reason: no confirmed or review-ready finding selected. | Show save failure with retry and "choose another location." Never discard audit data. | Show packet preview, redaction checklist, factual message template, and export button. | Show disabled export button with exact blocker: "Review redactions first" or "Evidence missing." |

Copy rule: state labels must describe what the user can do, not the backend status. Prefer "Add EPF passbook to confirm August" over "partial data."

Trust rule: unsupported and failed sources never create confirmed findings. They create review-needed or failed states with clear recovery actions.

### Pass 3: User Journey & Emotional Arc

Rating before: 5/10.
Rating after: 9/10.

Decision: design the journey as a shift from anxiety to control. The interface should never shame the user for missing documents or not knowing EPF terminology.

| Step | User does | User likely feels | UI must provide |
|---|---|---|---|
| 1 | Opens the app | Worried about salary, EPF, or tax records | Immediate privacy reassurance: "Files stay on this device." Show only two first actions, import salary slip and import EPF passbook. |
| 2 | Imports first source | Unsure whether the app understood the file | Source card with parsed month range, parser confidence, masked identifiers, and "one more file needed." |
| 3 | Imports second source | Wants a quick answer | Summary strip with truth score, clean months, open findings, and clear "action needed" or "no confirmed mismatch" result. |
| 4 | Sees a finding | Anxious, possibly angry at employer or confused by EPF records | Priority finding copy must be factual: "August PF credit is missing from EPF passbook" instead of accusatory language. |
| 5 | Opens timeline | Looking for when records stopped agreeing | Month-wise view with clean, mismatch, needs-review, unsupported, and missing states. Each month must show what matched or failed. |
| 6 | Opens evidence | Needs proof before acting | Evidence drawer with source snippets, amounts, confidence, and rule trace. Mask private identifiers by default. |
| 7 | Previews packet | Worried about sharing too much private data | Redaction checklist before export. User must see exactly what is visible and masked. |
| 8 | Exports or copies message | Wants a safe next action | Factual HR/EPFO message template with uncertainty stated plainly and no legal, tax, or accounting advice. |

Time-horizon design:

- First 5 seconds: user sees local-only privacy, current audit status, and the next best action.
- First 5 minutes: user can import two files, understand whether there is a confirmed issue, and inspect the evidence.
- Five-year relationship: user trusts the product because it never overstates weak evidence, never hides redaction, and keeps records local by default.

Tone rules:

- Use calm factual language: "missing from EPF passbook" instead of "employer failed to deposit."
- Separate uncertainty from failure: "needs review" is not "wrong."
- Put recovery actions next to every blocked state.
- Do not use celebratory language for money problems. A clean audit can say "Records match" rather than "Great news!"

### Pass 4: AI Slop Risk

Rating before: 6/10.
Rating after: 9/10.

Decision: add anti-slop UI constraints to keep the app from becoming a generic fintech dashboard.

Classifier: APP UI. This is a task-focused audit workspace, not a marketing landing page.

Hard rules:

- No generic dashboard-card mosaic as the first impression. The first impression is a workspace: status, priority finding queue, selected finding, evidence/action.
- Cards must earn their pixels. Allowed card-like surfaces are issue rows, source panels, evidence snippets, redaction checklist items, packet controls, and import source slots.
- Summary metrics are allowed only in the top strip and must stay secondary to the priority finding.
- No decorative icon circles, emoji bullets, crypto gradients, blobs, or ornamental charts.
- No centered-everything layout. The app should use left-aligned workflow language and dense but readable panes.
- No charts before evidence. A chart cannot replace the finding queue or month-wise timeline.
- No default "Welcome to..." hero. First-run copy should be useful: "Import salary slips and EPF passbook to check PF credits locally."
- Motion, if added later, must clarify hierarchy: drawer open, row selection, redaction checklist progress. No decorative motion.

Approved visual language:

- Top strip: compact status metrics.
- Left pane: Linear-style issue rows.
- Center pane: selected finding and timeline preview.
- Right pane: evidence drawer or packet safety panel.
- Mobile: single finding feed with clear sections and sticky action, not stacked desktop cards.

Premium test: the UI should still feel trustworthy if all decorative shadows are removed. Trust should come from hierarchy, copy, status clarity, and redaction visibility.

### Pass 5: Design System Alignment

Rating before: 7/10.
Rating after: 8/10.

Decision: keep `DESIGN.md` as the single source of truth for AuditOS tokens and component styling. Do not duplicate the full token map in this plan.

Implementation rule: before building UI, read `DESIGN.md` and use its named vocabulary:

- Issue rows for findings.
- Source badges for Salary, EPF/UAN, Bank, Form 16, AIS, and Form 26AS.
- Evidence drawer for source snippets, rule trace, and redaction controls.
- Packet composer for message preview, attachment checklist, and export controls.
- Black primary actions, purple system actions, green matched/progress states, blue evidence links, red confirmed mismatches, and amber needs-review states.

If implementation introduces a new UI component that does not fit this vocabulary, update `DESIGN.md` first rather than inventing local styling in the component.

### Pass 6: Responsive & Accessibility

Rating before: 4/10.
Rating after: 9/10.

Decision: specify responsive and accessibility requirements before implementation.

Responsive rules:

| Viewport | Layout | Required behavior |
|---|---|---|
| Desktop, 1200px and up | Three-pane control room | Summary strip stays visible. Finding queue, selected finding, and evidence/action pane are visible together. |
| Tablet, 768px to 1199px | Two-pane workspace | Finding queue and selected finding share the main view. Evidence drawer opens as a side sheet or bottom sheet. |
| Mobile, under 768px | Single finding feed | Summary becomes compact. Each finding is a section. Timeline and evidence expand inline. Primary action stays in a sticky bottom bar. |

Mobile requirements:

- Touch targets must be at least 44px tall.
- The sticky bottom action must never cover evidence text or redaction controls.
- Long employer names wrap to two lines before truncating.
- Timeline months collapse by year when there are more than 12 months.
- Export controls stay disabled until redaction preview is complete, with the blocker visible near the button.

Keyboard requirements:

- Tab order follows: import actions, summary strip, finding queue, selected finding, timeline, evidence drawer, redaction controls, export action.
- Finding rows are keyboard-selectable and show a visible focus state.
- Evidence drawer can be opened, navigated, and closed without a mouse.
- Packet preview and redaction checklist must be reachable before export.

Screen-reader requirements:

- Use landmarks for header, main audit workspace, finding navigation, evidence region, and packet actions.
- Status chips must expose text labels, not color alone. Example: "Confirmed mismatch", "Needs review", "Unsupported source", "Clean month."
- Amount differences must be announced with source context: "Salary slip expected 1,800 rupees. EPF passbook observed 0 rupees."
- Redaction status must be announced before export: "PAN masked, UAN masked, employee ID masked."

Contrast and label requirements:

- Body text must meet 4.5:1 contrast.
- Status color cannot be the only signal. Pair color with label and icon or shape.
- Form inputs and file inputs must have visible labels. Placeholder-only labels are not allowed.
- Links must preserve visited and unvisited distinction where the app links to instructions or local help pages.

### Pass 7: Unresolved Design Decisions

Rating before: 6/10.
Rating after: 9/10.

Decision for V1.1: packet export starts from the right pane but must be confirmed in a dedicated packet review screen. V1.0 stops at evidence-ready state.

Packet export flow:

```text
Selected finding
  |
  +-- Right pane action: "Prepare packet"
        |
        v
Dedicated packet review screen
  |
  +-- Evidence included
  +-- Redaction checklist
  +-- Message preview
  +-- Attachment/export format
  +-- Final "Export packet" action
```

Packet review requirements:

- The review screen must show what is visible and what is masked before export.
- Export remains blocked until redaction checks pass.
- Long evidence snippets and message templates must be readable on mobile without horizontal scrolling.
- The final action copy must be explicit: "Export redacted packet", not "Done" or "Continue."
- The packet screen must restate: "This is factual evidence, not legal, tax, or accounting advice."

Remaining deferred design decisions:

| Decision | If deferred, what happens | Status |
|---|---|---|
| Local web app versus desktop wrapper | Packaging may affect file access, offline behavior, and trust cues. | Deferred to implementation planning. |
| Exact packet export format, PDF, HTML, ZIP, or Markdown | Builder may pick a format that is hard for HR/EPFO/CA users to act on. | Deferred until packet content is defined. |
| Full browser-assisted import UI | Could create credential-capture anxiety if designed too early. | Deferred until manual import works. |
| Multi-source tax and bank views | Dashboard may overfit EPF-only state if expanded too late. | Deferred until EPF wedge ships. |

### NOT In Scope For This Design Review

- Final visual polish for a coded app, because no app UI exists yet.
- Tax, AIS, Form 26AS, bank, CA, and multi-bank screen design, because V1 starts with salary slip plus EPF passbook.
- Automated portal login or credential capture UI, because V1 is manual import only.
- Production copy for every packet template, because factual packet content needs implementation fixtures first.

### Outside Design Voice Findings

Codex status: unavailable on this machine.
Claude subagent status: issues found.
Outside score: 8/10.
Hard rejections: none.

Litmus scorecard:

| Check | Claude | Codex | Consensus |
|---|---|---|---|
| Brand/product unmistakable in first screen? | YES | unavailable | single-model yes |
| One strong visual anchor present? | YES, but must be enforced | unavailable | needs enforcement |
| Page understandable by scanning headlines only? | NOT SPECIFIED | unavailable | needs fix |
| Each section has one job? | YES | unavailable | single-model yes |
| Are cards actually necessary? | YES, if restricted to functional surfaces | unavailable | single-model yes |
| Does motion improve hierarchy? | NOT SPECIFIED | unavailable | needs fix |
| Premium without decorative shadows? | YES | unavailable | single-model yes |
| Hard rejections triggered? | NO | unavailable | clean |

Fixes accepted:

- First-screen mismatch state is finding-first, not metric-first. The primary visual anchor is a sentence like: "Records need review: August PF credit is missing." The primary action follows immediately: "Review evidence" or "Prepare packet." Truth score remains visible but secondary.
- Partial import state remains import-progress-first: "Add EPF passbook to confirm August." This prevents the app from implying a confirmed mismatch before both sources exist.
- Clean audit state shows a scoped audit record, not an empty dashboard. It must include matched month range, sources checked, fields checked, confidence, evidence sample, and next actions: "Save audit record" and "Import another month."
- Desktop pane ratio should start at roughly 24% finding queue, 46% selected finding and timeline, 30% evidence/action. Implementers may adjust for content, but the selected finding stays dominant.
- Default selected finding is the highest-priority confirmed mismatch. If there is no confirmed mismatch, select the highest-priority needs-review item. If there are no findings, show the clean audit record.
- Section headings must be scannable: "Needs action", "Why we believe this", "Month timeline", "Packet safety", and "What you can do next."

Additional edge states:

| Edge state | User sees | Required recovery |
|---|---|---|
| Duplicate import | "This file was already imported on [date]." | Keep existing source, offer "replace file" if the user wants newer data. |
| Replaced source file | "Replacing this file will rerun affected months." | Confirm before replacing and preserve prior audit record if saved. |
| Stale source data | "This EPF passbook ends in July. August cannot be checked yet." | Show missing month as unknown, not mismatch. |
| Redaction rule failure by field | "UAN redaction failed. Export blocked." | Let user manually mask or remove the field before export. |
| User cancels parsing | "Import cancelled. No audit data was changed." | Return to import guide with previous data intact. |
| Packet export cancelled | "Export cancelled. Packet preview is still available." | Keep preview and redaction choices locally. |

Uncertainty copy patterns:

- Partial: "Not enough evidence yet. Add EPF passbook to confirm this month."
- Needs review: "The records look different, but we need review before calling this confirmed."
- Unsupported: "This file format is not supported yet. No mismatch was created from it."
- Failed: "We could not read this file safely. Your existing audit data was not changed."

Focus and motion requirements:

- Drawers and bottom sheets must return focus to the triggering row when closed.
- Packet review must not trap keyboard users. Escape closes non-destructive overlays, but not an in-progress export.
- Progress updates for import and redaction must be announced to assistive technology.
- Respect reduced-motion settings. If reduced motion is enabled, replace slide/scale transitions with opacity or instant state changes.
- Motion may clarify drawer open, row selection, and redaction progress only. Decorative motion is out of scope.

### Design Plan Review Completion Summary

```text
+====================================================================+
|         DESIGN PLAN REVIEW - COMPLETION SUMMARY                    |
+====================================================================+
| System Audit         | DESIGN.md exists, UI scope confirmed         |
| Step 0               | 6/10 initial rating, full review selected    |
| Visual Mockups       | gstack designer installed, API key missing   |
| Fallback Board       | HTML board written under ~/.gstack/designs   |
| Pass 1  (Info Arch)  | 7/10 -> 9/10 after fixes                     |
| Pass 2  (States)     | 4/10 -> 9/10 after fixes                     |
| Pass 3  (Journey)    | 5/10 -> 9/10 after fixes                     |
| Pass 4  (AI Slop)    | 6/10 -> 9/10 after fixes                     |
| Pass 5  (Design Sys) | 7/10 -> 8/10 after decision                  |
| Pass 6  (Responsive) | 4/10 -> 9/10 after fixes                     |
| Pass 7  (Decisions)  | packet export resolved, 4 deferred          |
+--------------------------------------------------------------------+
| NOT in scope         | written, 4 items                             |
| What already exists  | written                                     |
| TODOS.md updates     | 2 items proposed and accepted                |
| Approved Mockups     | fallback HTML board, B+D baseline approved   |
| Decisions made       | 8 added to plan                              |
+====================================================================+
```

Design review status: DONE_WITH_CONCERNS.

Concern: PNG mockup generation could not run because `OPENAI_API_KEY` is not configured for the gstack designer. The fallback HTML board and prior approved B+D direction were used instead.

## Engineering Plan Review Addendum

Status: DONE_WITH_CONCERNS.
Mode: FULL_REVIEW.
First implementation target: V1.0, not Proof 0.

### Accepted Engineering Decisions

| Area | Decision |
|---|---|
| Runtime | V1.0 is a local FastAPI API plus web UI. No cloud API is required for core reconciliation. |
| UI/API split | UI owns interaction states. FastAPI owns import jobs, parsing, normalization, storage, reconciliation, and audit read models. |
| Storage | Store normalized facts, findings, source metadata, content hashes, and bounded evidence snippets only. Do not persist full raw documents by default. |
| Connectors | V1.0 uses built-in reviewed connectors only. No runtime plugin loading or remote connector packages. |
| Processing | One active import/reconcile job per audit, bounded queue, explicit cancel, simple polling for progress. |
| State model | One canonical audit state vocabulary shared across API, reconciliation, timeline, dashboard, and tests. |
| Local records | Implement the truth graph as normalized records plus selector/query functions, not a graph library. |
| Error model | Parser and reconciliation outcomes return typed `Result` objects/error codes. Exceptions are for unexpected crashes only. |
| Redaction | Shared redaction service is required in V1.0 for evidence display and reused later for packet export. |
| Tests | pytest for FastAPI/backend, Vitest for frontend state, Playwright for critical E2E flows. |
| OCR | OCR-only and scanned documents are unsupported in V1.0. Use file size caps and clear unsupported states. |
| Score language | Keep "Truth score" only with scoped copy that says V1.0 checked EPF contribution records, not all financial truth. |
| Packet export | Packet export UI is removed from V1.0. V1.0 shows evidence readiness. V1.1 owns packet review and export. |
| Docker | Multi-container docker-compose for development (FastAPI + UI hot-reload containers). Single production image published to ghcr.io via GitHub Actions. Container binds to 127.0.0.1 only. Data volume: `~/.audit-os/data` on host → `/app/data` in container. |

### Updated V1.0 Architecture

```text
User
  |
  v
Web UI
  |-- import guide
  |-- dashboard
  |-- timeline investigator
  |-- evidence drawer
  |
  v
Local FastAPI API
  |-- POST /api/imports
  |-- GET  /api/jobs/{job_id}
  |-- GET  /api/audits/{audit_id}
  |
  v
Bounded job queue
  |-- one active job per audit
  |-- queued / running / cancelled / failed / completed
  |
  v
Built-in connectors
  |-- salary slip parser
  |-- EPF passbook parser
  |
  v
Canonical records + selectors
  |-- sources
  |-- facts
  |-- evidence snippets
  |-- findings
  |-- audit states
```

### Docker Topology (V1.0)

```text
DEVELOPMENT (docker-compose.dev.yml)
  ┌──────────────────────────────────────────┐
  │  audit-api container                     │
  │  FastAPI + uvicorn --reload              │
  │  port: 127.0.0.1:8000                    │
  │  volume: ~/.audit-os/data -> /app/data   │
  └──────────────────────────────────────────┘
  ┌──────────────────────────────────────────┐
  │  audit-ui container                      │
  │  Vite dev server with hot reload         │
  │  port: 127.0.0.1:5173                    │
  │  proxies /api/* -> audit-api:8000        │
  └──────────────────────────────────────────┘

PRODUCTION (docker-compose.yml / single image)
  ┌──────────────────────────────────────────┐
  │  ghcr.io/shourya1997/pikachu-bunny:tag   │
  │  FastAPI serves /api/* + static UI build │
  │  port: 127.0.0.1:8000 ONLY              │
  │  volume: ~/.audit-os/data -> /app/data   │
  └──────────────────────────────────────────┘

CI (GitHub Actions on merge to main)
  build → test → docker build → push to ghcr.io
  tag: latest + sha-short

PRIVACY RULE: container MUST NOT bind to 0.0.0.0.
Any port binding outside 127.0.0.1 exposes raw
financial evidence to the local network.
```

### EPF Reconciliation Decision Tree

```text
Salary slip month + EPF passbook month
  |
  +-- missing source?
  |     -> partial, no confirmed mismatch
  |
  +-- unsupported / OCR-only / parser failed?
  |     -> unsupported or failed, no confirmed mismatch
  |
  +-- employer identity unclear?
  |     -> needs_review
  |
  +-- delayed credit / arrears / duplicate row / job switch signal?
  |     -> needs_review with reason
  |
  +-- EPS split / wage ceiling / VPF shape detected?
  |     -> needs_review unless fixture rule covers it
  |
  +-- normalized employee PF and employer PF match tolerance?
  |     -> clean month
  |
  +-- otherwise
        -> confirmed mismatch
```

### What Already Exists

| Sub-problem | Existing artifact | Reuse decision |
|---|---|---|
| Product wedge | This plan's CEO review | Reuse, but V1.0 starts as local FastAPI plus web UI. |
| Visual system | `DESIGN.md` AuditOS | Reuse as UI source of truth. |
| UI layout | Design review addendum | Reuse Financial Control Room and Timeline Investigator. |
| Deferred work | `TODOS.md` | Update stale packaging TODO and keep non-V1.0 scope deferred. |
| Application code | None | No code to reuse. Build with small explicit modules. |

### NOT In Scope For V1.0

- Packet export, packet review screen, and HR/EPFO/CA message export, deferred to V1.1 because V1.0 must prove audit truth and evidence first.
- Bank statements, Form 16, AIS, Form 26AS, CA workflows, browser automation, credential capture, and multi-bank support, deferred because they expand connector and legal surface.
- OCR for scanned documents, deferred because it adds accuracy, dependency, and performance risk before text-based parsing is trusted.
- Runtime third-party connector plugins or remote connector packages, deferred until connector permissions, review rules, and fixture gates exist.
- Desktop wrapper, signed installer, and auto-update, deferred until local FastAPI web app works end to end.

### Test Coverage Diagram

```text
CODE PATHS                                           USER FLOWS
[+] FastAPI import API                               [+] V1.0 audit journey
  +-- [GAP] missing file -> missing_file               +-- [GAP] import salary slip fixture
  +-- [GAP] unsupported type -> unsupported_file_type  +-- [GAP] import EPF passbook fixture
  +-- [GAP] file too large -> unsupported              +-- [GAP] see running job state
  +-- [GAP] OCR-only -> unsupported                    +-- [GAP] cancel import, no data changed
  +-- [GAP] duplicate import -> duplicate_source       +-- [GAP] dashboard clean state
  +-- [GAP] replace source -> rerun affected months    +-- [GAP] dashboard mismatch state

[+] Parser + normalization                           [+] Timeline + evidence
  +-- [GAP] salary slip fixture -> facts               +-- [GAP] highest-priority finding selected
  +-- [GAP] EPF passbook fixture -> facts              +-- [GAP] month timeline groups states
  +-- [GAP] invalid period -> invalid_period           +-- [GAP] keyboard row navigation
  +-- [GAP] amount normalization Rs 1,800.00 -> 1800   +-- [GAP] evidence drawer opens/closes focus
  +-- [GAP] employer spelling -> needs_review          +-- [GAP] identifiers are masked in snippets

[+] Reconciliation                                   [+] Error and recovery states
  +-- [GAP] exact match -> clean                       +-- [GAP] local API unavailable
  +-- [GAP] amount mismatch -> confirmed               +-- [GAP] storage write failure
  +-- [GAP] missing EPF month -> needs_review/missing  +-- [GAP] corrupt local DB
  +-- [GAP] delayed credit -> needs_review             +-- [GAP] user-cleared local data
  +-- [GAP] EPS/VPF/arrears/job switch -> needs_review

COVERAGE: 0/29 paths tested because no application code exists yet.
QUALITY TARGET: all parser/reconciliation/storage paths get pytest; UI state mapping gets Vitest; critical user journey gets Playwright.
```

### Test Requirements Added To Plan

| Layer | Tool | Required coverage |
|---|---|---|
| Backend API | pytest + FastAPI TestClient | import endpoint, job status endpoint, audit read endpoint, typed error codes, cancellation, no-data-mutated guarantees. |
| Parsers | pytest | supported salary slip fixtures, supported EPF passbook fixtures, unsupported layout, OCR-only file, invalid period, invalid amount, empty rows. |
| Reconciliation | pytest | exact match, amount mismatch, missing EPF month, duplicate row, delayed credit, EPS split, wage ceiling, VPF, arrears, employer drift, job switch. |
| Storage | pytest | schema version, reload, duplicate hash, replace source, corrupt DB, write failure, user-cleared data, migration/reset path. |
| Redaction | pytest + Vitest | PAN, UAN, account number, phone, email, address, employee ID, unknown identifier fallback, masked evidence display. |
| Frontend state | Vitest | loading, partial, clean, confirmed mismatch, needs review, unsupported, failed, API unavailable, cancelled. |
| User journey | Playwright | import both fixtures, poll jobs, dashboard, timeline, evidence drawer, keyboard navigation, redaction visibility. |

Test plan artifact written for QA:

```text
~/.gstack/projects/personal/shourya-unknown-eng-review-test-plan-20260426-194500.md
```

### Failure Modes

| Codepath | Production failure | Test required | Handling required | User sees |
|---|---|---:|---:|---|
| `POST /api/imports` | Missing or unsupported file | Yes | Yes | Clear import error, no audit mutation. |
| `GET /api/jobs/{job_id}` | Job cancelled mid-parse | Yes | Yes | "Import cancelled. No audit data was changed." |
| Parser | OCR-only salary slip | Yes | Yes | Unsupported state, no confirmed mismatch. |
| Parser | Malformed PDF or CSV | Yes | Yes | Failed state with safe message. |
| Normalizer | Invalid month string | Yes | Yes | Needs review or failed source, no false mismatch. |
| Reconciliation | Delayed EPF credit | Yes | Yes | Needs review, not confirmed mismatch. |
| Reconciliation | EPS/VPF/arrears/job switch | Yes | Yes | Needs review or unsupported rule, not accusation. |
| Storage | SQLite write failure or corrupt DB | Yes | Yes | Recovery message, existing audit not silently changed. |
| Evidence | Snippet contains UAN/PAN/email/account | Yes | Yes | Masked snippet or blocked evidence display. |
| UI | Local API unavailable | Yes | Yes | Local engine unavailable with retry/start instructions. |
| Docker | Container binds to 0.0.0.0 instead of 127.0.0.1 | Yes | Yes | [P0] Private financial evidence exposed to local network. Dockerfile MUST set `--host 127.0.0.1`. |
| Docker | Data volume not mounted, container restarted | Yes | Yes | User sees empty audit with no error. README must warn; healthcheck must verify /app/data is writable. |
| Docker | ghcr.io push fails in CI | Yes | Yes | GitHub Actions build step fails visibly; no silent publish of a broken image. |

Critical gaps flagged: none after accepted review decisions, assuming implementation adds the tests above before release. Docker binding to 0.0.0.0 is a P0 privacy risk and must be caught by CI.

### Worktree Parallelization Strategy

| Step | Modules touched | Depends on |
|---|---|---|
| Backend scaffold | `api/`, `storage/`, `jobs/` | runtime decision |
| Schema and states | `schema/`, `shared/` | backend scaffold |
| Parser fixtures | `connectors/`, `fixtures/`, `tests/` | schema and states |
| Reconciliation | `reconciliation/`, `tests/` | parser fixtures |
| Docker | `Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml`, `.github/workflows/docker.yml` | backend scaffold + frontend shell |
| Frontend shell | `ui/`, `shared/` | schema and states |
| Dashboard/timeline/evidence | `ui/` | frontend shell, API read models |
| E2E tests | `e2e/`, `tests/` | backend + frontend flows |

Parallel lanes:

```text
Lane A: backend scaffold -> storage/jobs (sequential, shared api/storage)
Lane B: schema and state vocabulary (blocks A, C, D)
Lane C: frontend shell -> dashboard/timeline/evidence (after B)
Lane D: parser fixtures -> reconciliation (after B)
Lane E: E2E tests (after A + C + D)
```

Execution order: start Lane A and Lane B together only if the schema contract is coordinated tightly. Then run Lane C and Lane D in parallel. Run Lane E last.

Conflict flags: Lane C and Lane D both depend on shared state names. Lock `schema/` and shared audit-state vocabulary before parallel UI/parser work starts.

### Completion Summary

- Step 0: Scope Challenge — scope accepted as V1.0 first target.
- Architecture Review: 4 issues found and resolved.
- Code Quality Review: 4 issues found and resolved.
- Test Review: diagram produced, 29 gaps identified as required tests because no app code exists.
- Performance Review: 3 issues found and resolved.
- NOT in scope: written.
- What already exists: written.
- TODOS.md updates: packaging, fixtures, OCR, and connector plugin follow-ups identified.
- Failure modes: 0 critical silent gaps remain if required tests and handlers are implemented.
- Outside voice: ran via Claude subagent; substantive findings integrated after user decisions.
- Parallelization: 5 lanes, 2 possible parallel workstreams after schema lock, E2E sequential at end.
- Lake Score: 18/20 recommendations accepted. Deviations: V1.0 chosen over Proof 0, and Truth score kept with scoped copy.

## Completion Summary

| Area | Verdict | Action |
|---|---|---|
| Product wedge | Strong after narrowing | Build V1.0 EPF contribution audit first. |
| Architecture | Updated by eng review | Local FastAPI API plus web UI, normalized records, bounded jobs. |
| Trust model | Must be first-class | Add confidence states and source provenance. |
| Privacy | Direction is right | Store facts/snippets only, no raw documents by default. |
| Open-source quality | Needs fixtures | Start synthetic, add redacted-real contribution process later. |
| UI | Strong direction | Add state coverage and scoped Truth score copy before build. |
| Legal/tax risk | Manageable | Add factual-language and advice guardrails. |

## Recommendation

Build the V1.0 EPF contribution audit as a local FastAPI engine plus web UI. The foundation is built-in connectors, synthetic fixture corpus, canonical records, shared audit states, typed result codes, bounded local jobs, masked evidence snippets, and full pytest/Vitest/Playwright coverage.

Packet export, OCR, runtime connector plugins, and desktop packaging come later. First prove one painful mismatch with enough rigor that every future connector has a standard to live up to.

## GSTACK REVIEW REPORT

| Review | Runs | Last Run | Status | Required |
|---|---:|---|---|---|
| Eng Review | 1 | 2026-04-26 14:52 UTC | CLEAR (PLAN) | YES |
| CEO Review | 1 | 2026-04-26 08:38 UTC | CLEAR | no |
| Design Review | 1 | 2026-04-26 08:57 UTC | ISSUES FOUND (FULL), fallback HTML used | no |
| Adversarial | 0 | - | - | no |
| Outside Voice | 1 | 2026-04-26 14:52 UTC | ISSUES FOUND, integrated by user decisions | no |

Verdict: CLEARED for implementation planning. Eng Review passed with 0 unresolved decisions and 0 critical silent gaps, assuming implementation adds the required tests and handlers listed above.
