# MVP4 Optimizer Guardrail Report Schema Hardening Audit

created_at_utc: 2026-04-29T04:07:18Z
patch_id: MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING_20260429_001

Findings:
- Optimizer guardrail report schema was still scaffold-level and did not require dependency status disclosure or explicit no-live/no-scale fields.
- A guardrail PASS could be misunderstood as LIVE_READY if it only exposed generic status text.
- Optimizer guardrail dependency chain did not include a validator for the guardrail report artifact itself.

Patch:
- Hardened optimizer_guardrail_report schema with guardrail scope/status/decision, dependency results, source modes, output ranking scope, NOT_LIVE_READY status, dashboard-display-truth-only marking, and explicit no-live/no-scale/no-exchange fields.
- Added optimizer_guardrail_report_validator and made optimizer_guardrail_validator depend on it.
- Added PASS and negative fixtures for live flag drift, dependency override, misleading LIVE_READY wording, missing blockers, LIVE_READY writer attempts, and scale-up attempts.
- Added unit tests and a standalone validator runner for optimizer guardrail reports.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
