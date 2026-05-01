# MVP4_PROFITABILITY_EVIDENCE_MATURITY_RUNTIME_LINKAGE

context_pack_id: MVP4_PROFITABILITY_EVIDENCE_MATURITY_RUNTIME_LINKAGE
task_class: MVP4_PROFITABILITY_EVIDENCE_MATURITY_RUNTIME_LINKAGE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-RUNTIME-LINKAGE"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "profitability_evidence_maturity_rollup_validator", "profitability_optimizer_evidence_gap_validator", "upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/profitability_evidence_maturity_rollup.schema.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_profitability_optimizer_evidence_gap_validator.py", "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json", "tests/validators/fixtures/profitability_runtime_cycle_linkage_pass.json", "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json", "tools/emit_profitability_evidence_runtime_linkage_patch.py", "contracts/generated/context_pack/MVP4_PROFITABILITY_EVIDENCE_MATURITY_RUNTIME_LINKAGE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- profitability maturity rollup contains runtime_linkage_evidence
- runtime_linkage_evidence points to a validating Upbit PAPER runtime cycle report
- runtime cycle hash, market data hash, feature hash, selected candidate, net EV, and cost model source match
- PAPER runtime linkage may allow PAPER scorecard input only
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- runtime linkage is not long-run evidence
- runtime linkage is not live-readiness evidence
- external API verification, read-only burn-in, manual order evidence, and operator approval remain missing

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. Generated context is read cache only.
generated_at_utc: 2026-05-01T12:29:13Z
