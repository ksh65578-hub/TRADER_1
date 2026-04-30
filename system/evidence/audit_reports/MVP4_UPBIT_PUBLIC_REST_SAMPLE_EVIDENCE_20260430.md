# MVP4 Upbit Public REST Sample Evidence Audit

created_at_utc: 2026-04-30T11:57:32Z
patch_id: MVP4_UPBIT_PUBLIC_REST_SAMPLE_EVIDENCE_20260430_001

Findings:
- Hidden issue: public network success/failure was not represented as its own PAPER-only evidence surface.
- Hidden issue: a future operator could confuse public market-data availability with LIVE_READY unless the evidence role is explicit.
- Hidden issue: network failure needed to be operator-visible BLOCKED evidence instead of an ambiguous runtime failure.

Patch:
- Added strict public REST sample schema, runtime builder, validator, tests, and CLI tool.
- Public sample PASS is PAPER input quality evidence only.
- Public sample BLOCKED records network/data unavailability without changing live state.
- Credential, authorization header, private endpoint, order endpoint, order adapter, live, and scale-up mutation are blocked.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
