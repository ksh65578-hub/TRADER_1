# UPBIT_PAPER_DRY_RUN

context_pack_id: UPBIT_PAPER_DRY_RUN
task_class: MVP2_UPBIT_PAPER_DRY_RUN
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP2_LADDER_ACTIVE", "SECTION_MVP2_SCOPE_ACTIVE", "SECTION_MVP2_FOUNDATION_ACTIVE", "SECTION_MVP2_TEST_LANES_ACTIVE", "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE", "SECTION_MVP2_OUTPUT_ARTIFACT_ACTIVE", "SECTION_MVP2_LEVEL_MAPPING_ACTIVE", "SECTION_AGENTS_MVP2_DRY_RUN", "SECTION_AGENTS_MVP2_REQUIRED_FILES"]
included_requirement_ids: ["REQ-MVP2-UPBIT-PAPER-DRY-RUN"]
included_schema_ids: ["trader1.upbit_paper_dry_run_report.v1", "trader1.ledger_event.v1", "trader1.final_decision.v1"]
included_validator_ids: ["upbit_paper_dry_run_validator"]
included_artifact_ids: ["trader1/adapters/upbit/paper_broker.py", "contracts/schema/upbit_paper_dry_run_report.schema.json", "tests/paper/test_upbit_paper_dry_run.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- Upbit paper dry-run uses public data only
- paper broker remains simulated and cannot call live order adapter
- paper order intent writes paper ledger when simulated entry is allowed
- no-trade and blocked paths log no-trade reasons
- paper/live, exchange, market_type, mode, and session scope remain separated
- strategy promotion and live permission mutation remain blocked
- live flags remain false

known_omissions_by_design:
- no exchange private API call
- no real live order submission
- no paper winner or optimizer output promotion
- restart recovery skeleton is the next MVP-2 task
- retained archive search results were not used as authority and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T15:14:58Z
