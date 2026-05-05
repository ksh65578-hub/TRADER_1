# MVP4 Dashboard Live Availability Reason Audit

created_at_utc: 2026-05-05T03:18:30Z
patch_id: MVP4_DASHBOARD_LIVE_AVAILABILITY_REASON_20260505_001

Finding:
- The first dashboard view showed live execution as blocked, but the answer could still read like a status label instead of a direct operator answer.

Patch:
- Changed the quick Live card answer to "No" when live orders cannot run.
- Added an explicit "No. Live orders cannot run." line to the Live Execution card.
- Added a plain summary that all live and scale permissions are false.
- Preserved the raw blocker and next action for audit traceability.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no scale-up
