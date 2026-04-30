# MVP4 Paper/Shadow Actual Runtime Source Guard Audit

created_at_utc: 2026-04-30T07:14:32Z
patch_id: MVP4_PAPER_SHADOW_ACTUAL_RUNTIME_SOURCE_GUARD_20260430_001

Finding:
- Paper/shadow evidence accumulation blocked short windows, but a report with enough synthetic per-window source ids could still overstate long-run eligibility without an explicit validated non-live persistent runtime source.
- That creates a user-facing and optimizer-facing false-safe risk: paper scorecard input could be confused with actual long-run PAPER/SHADOW evidence.

Patch:
- Added actual_runtime_source_evidence_ids and actual_runtime_source_status to the paper/shadow evidence schema.
- Builder and validator now block long-run eligibility unless actual runtime source status is VALIDATED_NON_LIVE_RUNTIME and source ids exist.
- Added negative tests for long-run claims without actual runtime evidence and for unvalidated actual runtime source ids.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
