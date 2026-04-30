# MVP4 Dashboard Legacy Runtime Artifact Hygiene Audit

created_at_utc: 2026-04-30T05:43:57Z
patch_id: MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE_20260430_001

Finding:
- A legacy dashboard shell exists at system/runtime/upbit/krw_spot/paper/dashboard_shell.json without a session_id path segment.
- A user or tool opening this legacy path could see stale or incomplete dashboard state instead of the current launcher-scoped dashboard.

Patch:
- Added a runtime dashboard artifact hygiene report schema and builder.
- Added runtime_dashboard_artifact_hygiene_validator.
- Added tests for current classification, unsafe legacy live-flag mutation, and unknown dashboard shell paths.
- Wrote the legacy shell as retained, non-authoritative, display-disabled audit material rather than deleting it.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
