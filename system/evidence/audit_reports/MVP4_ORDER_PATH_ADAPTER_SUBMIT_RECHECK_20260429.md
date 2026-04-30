# MVP4 Order Path Adapter Submit Recheck

created_at_utc: 2026-04-29T09:00:56Z
patch_id: MVP4_ORDER_PATH_ADAPTER_SUBMIT_RECHECK_20260429_001

Findings:
- The order path decision previously always reported external_submit_attempted=false, even if input evidence said an adapter submit had already been attempted.
- The tests did not prove that an order_adapter object is never inspected before live-enabling evidence.

Patch:
- Existing order_adapter_submit_attempted/external_submit_attempted/live_order_api_attempted evidence now adds LIVE_FINAL_GUARD_FAILED and is surfaced in the decision.
- Added tests for prior submit-attempt evidence and an adapter whose submit_order property fails if touched.
- Strengthened single_writer_order_path_validator to cover prior submit-attempt evidence.

Audit:
- prior_attempt_external_submit_attempted: True
- prior_attempt_blockers: ['LIVE_FINAL_GUARD_FAILED', 'LIVE_READY_MISSING']
- all_green_order_adapter_called: False
- all_green_primary_blocker_code: LIVE_ENABLING_EVIDENCE_MISSING

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
