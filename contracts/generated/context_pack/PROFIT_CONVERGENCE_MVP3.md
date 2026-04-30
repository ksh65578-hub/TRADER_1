# PROFIT_CONVERGENCE_MVP3

context_pack_id: PROFIT_CONVERGENCE_MVP3
task_class: PROFIT_CONVERGENCE_MVP3
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_CONVERGENCE_OBJECTIVE", "SECTION_CONVERGENCE_MEMORY", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_LIVE_GATE"]
included_requirement_ids: ["REQ-CONV-MVP0-SCAFFOLD"]
included_schema_ids: ["trader1.readiness_surface.v1", "trader1.live_ready_snapshot.v1", "trader1.manual_order_test_evidence.v1", "trader1.final_decision.v1", "trader1.ledger_event.v1", "trader1.summary.v1", "trader1.evidence_manifest.v1", "trader1.official_api_verification_report.v1", "trader1.validator_result.v1", "trader1.operator_action_audit.v1", "trader1.release_source_identity.v1", "trader1.contract_gap.v1", "trader1.patch_result.v1", "trader1.strategy_candidate.v1", "trader1.candidate_generation_report.v1", "trader1.live_ready_candidate_writer_input.v1", "trader1.validator_fixture_catalog.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "live_ready_snapshot_writer_validator"]
included_artifact_ids: ["contracts/generated/authority_section_map.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- exact retained archive text
- full runtime implementation
- live-enabling evidence
- exact validator logic beyond MVP-0 scaffold

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
