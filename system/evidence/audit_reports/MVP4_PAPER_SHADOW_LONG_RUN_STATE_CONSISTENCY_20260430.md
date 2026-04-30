# MVP4 Paper/Shadow Long-Run State Consistency Audit

created_at_utc: 2026-04-30T07:49:51Z
patch_id: MVP4_PAPER_SHADOW_LONG_RUN_STATE_CONSISTENCY_20260430_001

Finding:
- A tampered report with validated PAPER and SHADOW actual runtime source ids could set long_run_evidence_eligible=false while leaving scorecard_input_eligible=true and no blockers.
- The validator previously accepted that contradictory state, creating a dashboard/optimizer truth mismatch risk.

Patch:
- Validator now blocks under-reported long-run eligibility when validated source/window/span evidence is present.
- Existing blocker priority remains specific for short windows and missing actual runtime source evidence.
- Added regression test and validator self-check for the state drift case.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
