# Graph Report - /Users/shourya/personal  (2026-04-26)

## Corpus Check
- 33 files · ~34,273 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 151 nodes · 292 edges · 19 communities detected
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 110 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]

## God Nodes (most connected - your core abstractions)
1. `parse_salary_slip_text()` - 21 edges
2. `AuditService` - 20 edges
3. `parse_epf_passbook_text()` - 19 edges
4. `reconcile_epf()` - 12 edges
5. `check_compose_file()` - 9 edges
6. `ParsedDocument` - 8 edges
7. `_failure()` - 8 edges
8. `test_storage_round_trip_keeps_masked_evidence()` - 8 edges
9. `AuditSummary` - 7 edges
10. `JobStatus` - 7 edges

## Surprising Connections (you probably didn't know these)
- `failure()` --calls--> `test_result_failure_is_typed()`  [INFERRED]
  /Users/shourya/personal/backend/app/contracts.py → /Users/shourya/personal/backend/tests/test_contracts.py
- `AuditService` --calls--> `client()`  [INFERRED]
  /Users/shourya/personal/backend/app/services/audit_service.py → /Users/shourya/personal/backend/tests/test_health.py
- `Result` --uses--> `ParsedDocument`  [INFERRED]
  /Users/shourya/personal/backend/app/contracts.py → /Users/shourya/personal/backend/app/engine/models.py
- `success()` --calls--> `parse_salary_slip_text()`  [INFERRED]
  /Users/shourya/personal/backend/app/contracts.py → /Users/shourya/personal/backend/app/engine/parsers.py
- `success()` --calls--> `parse_epf_passbook_text()`  [INFERRED]
  /Users/shourya/personal/backend/app/contracts.py → /Users/shourya/personal/backend/app/engine/parsers.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (28): CanonicalFact, SourceMetadata, ParsedDocument, normalize_amount(), normalize_employer(), normalize_period(), _content_hash(), _evidence_line() (+20 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (21): AuditService, Single-process audit job coordinator for the local-only app., BaseModel, AuditState, AuditSummary, Confidence, failure(), FindingSeverity (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.23
Nodes (10): audit_service(), cancel_job(), get_audit(), get_job(), import_audit(), resolve_spa_path(), spa(), test_spa_blocks_path_traversal_outside_static_root() (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.31
Nodes (11): fetchAudit(), fetchDemoAudit(), fetchJob(), isAuditSummary(), isFinding(), isJobStatus(), isOneOf(), isRecord() (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (11): check_compose_file(), leading_spaces(), main(), parse_port_entry(), load_privacy_module(), test_adjacent_long_port_bindings_do_not_share_host_ip(), test_localhost_long_port_binding_passes(), test_localhost_short_port_binding_passes() (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.42
Nodes (6): EvidenceSnippet, init_db(), load_audit_summary(), load_evidence_snippets(), save_audit_summary(), test_storage_round_trip_keeps_masked_evidence()

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (4): contract_metadata(), contracts(), test_contract_metadata_exposes_state_vocabularies(), test_result_failure_is_typed()

### Community 7 - "Community 7"
Cohesion: 0.67
Nodes (5): Finding, _compare_month(), _evidence_ids_by_fact(), _facts_by_period(), reconcile_epf()

### Community 8 - "Community 8"
Cohesion: 0.47
Nodes (4): mask_sensitive(), test_mask_sensitive_does_not_redact_unlabeled_amounts_as_phone_numbers(), test_mask_sensitive_redacts_identifiers(), test_mask_sensitive_redacts_unlabeled_uan_and_indian_phone()

### Community 9 - "Community 9"
Cohesion: 0.4
Nodes (1): client()

### Community 10 - "Community 10"
Cohesion: 0.5
Nodes (1): AuditOS backend package.

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (0): 

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (0): 

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **Thin community `Community 11`** (1 nodes): `vite.config.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `App.test.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `types.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `vite-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `setup.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditService` connect `Community 1` to `Community 9`, `Community 5`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Why does `parse_salary_slip_text()` connect `Community 0` to `Community 1`, `Community 5`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `parse_epf_passbook_text()` connect `Community 0` to `Community 1`, `Community 5`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `parse_salary_slip_text()` (e.g. with `normalize_period()` and `normalize_amount()`) actually correct?**
  _`parse_salary_slip_text()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AuditService` (e.g. with `ImportRequest` and `AuditSummary`) actually correct?**
  _`AuditService` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `parse_epf_passbook_text()` (e.g. with `normalize_period()` and `normalize_amount()`) actually correct?**
  _`parse_epf_passbook_text()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `reconcile_epf()` (e.g. with `AuditSummary` and `Finding`) actually correct?**
  _`reconcile_epf()` has 8 INFERRED edges - model-reasoned connections that need verification._