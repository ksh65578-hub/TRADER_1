# MVP4 Optimizer Run Guardrail Schema Hardening Audit

created_at_utc: 2026-04-29T03:57:16Z
patch_id: MVP4_OPTIMIZER_RUN_GUARDRAIL_SCHEMA_HARDENING_20260429_001

Findings:
- Optimizer run report schema was still scaffold-level and did not require non-live source modes or explicit no-live/no-scale fields.
- A completed optimizer run could be presented as a generic PASS without proving that it was analysis-only, net-EV-after-cost based, and unable to call exchange account paths.
- The optimizer guardrail dependency chain did not include an optimizer_run_report_validator even though the registry listed the validator id.

Patch:
- Hardened optimizer_run_report schema with run scope, stage, output type, NET_EV_AFTER_COST objective basis, source mode separation, resource/recovery statuses, NOT_LIVE_READY status, and dashboard-display-truth-only marking.
- Added optimizer_run_report_validator and made optimizer_guardrail_validator depend on it.
- Added PASS and negative fixtures for live flag drift, LIVE mode, misleading LIVE_READY wording, missing blockers, LIVE_READY writer attempts, and raw-PnL objective use.
- Added unit tests and a standalone validator runner for optimizer run guardrails.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
