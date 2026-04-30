# MVP4 Dashboard Long-Run Status Semantics Audit

created_at_utc: 2026-04-30T07:00:56Z
patch_id: MVP4_DASHBOARD_LONG_RUN_STATUS_SEMANTICS_20260430_001

Finding:
- The visible UI label had been clarified, but dashboard_shell.json could still expose VALIDATED_STABLE for a clean display-history window.
- Machine readers or future UI panels could misread that as actual long-run runtime evidence.

Patch:
- Added DISPLAY_HISTORY_STABLE as the display-history-only machine state.
- Kept VALIDATED_STABLE reserved for actual duration and stable-sample floors.
- The blocker for display-history-only state is ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING.
- Schema, validator, tests, and regenerated dashboard artifacts now agree on the distinction.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
