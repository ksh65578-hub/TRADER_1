# SUMMARY_SHELL

context_pack_id: SUMMARY_SHELL
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SUMMARY_SCHEMA_SURFACE", "SECTION_SUMMARY_DASHBOARD_TRUTH", "SECTION_MVP1_SUMMARY_SCOPE", "SECTION_MVP1_SUMMARY_OUTPUTS", "SECTION_AGENTS_SUMMARY_FILE"]
included_requirement_ids: ["REQ-MVP1-SUMMARY-SHELL"]
included_schema_ids: ["trader1.summary.v1", "trader1.validator_result.v1"]
included_validator_ids: ["summary_shell_validator"]
included_artifact_ids: ["trader1/dashboard/summary_writer.py", "contracts/schema/summary.schema.json", "tests/dashboard/test_summary_writer.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- summary.json is dashboard serving truth only
- summary cannot create execution truth
- summary cannot emit order-affecting final_action
- summary cannot set live_order_ready
- summary cannot set live_order_allowed

known_omissions_by_design:
- read-only dashboard UI
- root launcher creation
- ledger/WAL implementation
- paper broker
- live key loading
- live order API

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:57:02Z
