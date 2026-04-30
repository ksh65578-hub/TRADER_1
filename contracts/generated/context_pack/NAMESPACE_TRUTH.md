# NAMESPACE_TRUTH

context_pack_id: NAMESPACE_TRUTH
task_class: MVP0_CONTRACT_BASELINE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_NAMESPACE", "SECTION_TRUTH_HIERARCHY", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-NAMESPACE-TRUTH"]
included_schema_ids: ["trader1.validator_result.v1", "trader1.patch_result.v1"]
included_validator_ids: ["path_namespace_validator", "truth_hierarchy_validator"]
included_artifact_ids: ["trader1/validation/namespace.py", "tests/namespace/test_namespace_truth.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- artifacts are scoped by exchange, market_type, mode, and session where required
- cross-mode, cross-exchange, cross-market_type, and cross-session joins are blocked
- dashboard serving truth cannot override execution truth
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- real runtime artifact production
- ledger implementation
- exchange reconciliation
- live-enabling evidence

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T12:54:51Z
