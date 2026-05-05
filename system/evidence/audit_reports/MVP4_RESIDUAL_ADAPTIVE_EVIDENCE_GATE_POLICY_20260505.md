# MVP4 Residual Adaptive Evidence Gate Policy

created_at_utc: 2026-05-05T12:10:12Z
patch_id: MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_20260505_001

Finding:
- Fixed PAPER/SHADOW hour counts are too blunt as the MVP5 review-entry threshold.

Patch:
- Removed the fixed MVP5 review-entry duration, heartbeat tick, and PAPER-SHADOW window hard floors.
- Set review-entry to ADAPTIVE_EVIDENCE_QUALITY_GATE: evidence artifacts and validators decide whether enough paper/shadow evidence exists.
- Preserved the 24h profile as trial-only.
- Moved 120h to optional extended observation or scale-up confidence only.

Safety:
- fixed_duration_gate_removed=true
- adaptive_evidence_gate_enabled=true
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
