# MVP4 Residual MVP5 Entry Duration Policy

created_at_utc: 2026-05-05T11:31:53Z
patch_id: MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY_20260505_001

Finding:
- The previous 120h PAPER/SHADOW criterion was too costly as the MVP5 review-entry threshold.

Patch:
- Lowered MVP5 review-entry to 48h / 17280 ticks / 8 PAPER-SHADOW windows.
- Preserved the 24h profile as trial-only.
- Moved 120h to optional extended observation or scale-up confidence only.

Safety:
- duration_only_live_ready_allowed=false
- external_live_evidence_still_required=true
- command_executed_by_this_patch=false
- operator_run_completed_by_this_patch=false
- operator_run_evidence_ready_for_mvp5=false
- current_evidence_write_allowed=false
- gap_closure_allowed_by_this_patch=false
- live_ready_write_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
