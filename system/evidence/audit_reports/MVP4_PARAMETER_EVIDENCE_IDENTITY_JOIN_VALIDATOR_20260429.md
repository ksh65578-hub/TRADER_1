# MVP4 Parameter Evidence Identity Join Validator

created_at_utc: 2026-04-29T14:51:15Z
patch_id: MVP4_PARAMETER_EVIDENCE_IDENTITY_JOIN_VALIDATOR_20260429_001

Hidden defect found:
- Parameter narrowing could previously pass based on source_evidence_id naming conventions without proving exact cross-artifact identity joins.

Patch applied:
- Added candidate_id and source_evidence_identity_bindings to parameter_narrowing_report.
- Validator now requires exact candidate, strategy, previous/proposed parameter hash, timeframe, regime, exchange, market_type, source mode, and PASS identity status for each source evidence id.
- Added missing-binding, identity-mismatch, and stale-identity negative coverage.
- Resolved PARAMETER_EVIDENCE_IDENTITY_JOIN_GAP.

Safety:
- No live order path was enabled.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
