# UPBIT_LIVE_REVIEW

context_pack_id: UPBIT_LIVE_REVIEW
task_class: MVP4_UPBIT_LIVE_REVIEW_DISPLAY_TRUTH_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LIVE_GATE_ACTIVE", "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE", "SECTION_LIVE_PREFLIGHT_ACTIVE", "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST"]
included_requirement_ids: ["REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.live_preflight_report.v1", "trader1.live_review_dashboard.v1"]
included_validator_ids: ["upbit_live_review_preflight_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/runtime/readiness/live_preflight.py", "trader1/dashboard/live_review_dashboard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- MVP-4 live review remains review-only
- preflight_status must remain BLOCKED
- primary_blocker_code must be present in blockers
- readiness_surface blocker must match preflight truth
- live review dashboard first line must remain LIVE TRADING: BLOCKED
- display-only dashboard cannot create live permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false

known_omissions_by_design:
- no exchange credentials
- no official API PASS evidence
- no manual order test
- no operator approval
- no read-only burn-in evidence
- no LIVE_READY snapshot write
- no live order submission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T21:40:07Z
