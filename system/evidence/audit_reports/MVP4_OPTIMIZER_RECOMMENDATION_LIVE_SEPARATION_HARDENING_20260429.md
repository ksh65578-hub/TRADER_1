# MVP4 Optimizer Recommendation Live Separation Hardening Audit

created_at_utc: 2026-04-29T03:46:37Z
patch_id: MVP4_OPTIMIZER_RECOMMENDATION_LIVE_SEPARATION_HARDENING_20260429_001

Findings:
- Optimizer recommendation report schema was still scaffold-level and did not require explicit non-live scope fields.
- A recommendation could be interpreted by an operator or downstream component as a live-ready recommendation if the artifact only exposed a generic status.
- Optimizer guardrail dependencies did not include an optimizer_recommendation_validator.

Patch:
- Hardened optimizer_recommendation_report schema with recommendation scope/action/output type, NOT_LIVE_READY status, explicit no-live/no-scale fields, and no live writer permission.
- Added optimizer_recommendation_validator and made optimizer_guardrail_validator depend on it.
- Added PASS and negative fixtures for live flag drift, misleading LIVE_READY wording, action/scope mismatch, and LIVE_READY writer attempts.
- Added unit tests and a standalone validator runner for optimizer recommendation reports.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
