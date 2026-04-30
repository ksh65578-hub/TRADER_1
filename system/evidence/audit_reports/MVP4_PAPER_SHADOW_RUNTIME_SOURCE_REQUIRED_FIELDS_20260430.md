# MVP4 Paper/Shadow Runtime Source Required Fields Audit

created_at_utc: 2026-04-30T07:57:02Z
patch_id: MVP4_PAPER_SHADOW_RUNTIME_SOURCE_REQUIRED_FIELDS_20260430_001

Finding:
- A legacy or partial paper_shadow_evidence_accumulation_report could omit actual_runtime_source_evidence_ids, actual_runtime_source_status, or supporting_source_evidence_ids.
- If the evidence hash was recomputed, the direct validator and schema validator previously allowed that report to PASS for paper scorecard input.

Patch:
- Made actual runtime source ids, actual runtime source status, and supporting source ids required schema fields.
- Made the direct paper/shadow evidence validator require the same fields.
- Added regression coverage and refreshed fixtures to the current schema generation.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
