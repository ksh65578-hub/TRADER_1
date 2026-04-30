# PAPER_EXPOSURE_QUALITY_REPORT

context_pack_id: PAPER_EXPOSURE_QUALITY_REPORT
task_class: MVP4_PAPER_EXPOSURE_QUALITY_REPORT
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_CONVERGENCE_RISK_SCALE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-EXPOSURE-QUALITY-REPORT"]
included_schema_ids: ["trader1.paper_exposure_quality_report.v1"]
included_validator_ids: ["paper_exposure_quality_report_validator", "profitability_optimizer_evidence_gap_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/paper_exposure_quality_report.schema.json", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_paper_exposure_quality_report_validator.py", "tests/validators/fixtures/paper_exposure_quality_pass.json", "tests/validators/fixtures/paper_exposure_quality_scale_up_fail.json", "tests/validators/fixtures/paper_exposure_quality_missing_evidence_fail.json", "tests/validators/fixtures/paper_exposure_quality_exposure_breach_fail.json", "tests/validators/fixtures/paper_exposure_quality_live_mode_fail.json", "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json", "contracts/generated/context_pack/PAPER_EXPOSURE_QUALITY_REPORT.md"]

acceptance_checklist:
- paper exposure quality is PAPER-only and display-truth-only
- source_evidence_ids are required for paper review
- exposure, concentration, drawdown, idempotency, and recovery failures fail closed
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live evidence collection
- no live config mutation
- no scale-up permission
- no LIVE_READY snapshot write

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T07:42:28Z
