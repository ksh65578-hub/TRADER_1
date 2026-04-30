# MVP4 Dashboard Exploration Policy Visibility

created_at_utc: 2026-04-29T05:53:19Z
patch_id: MVP4_DASHBOARD_EXPLORATION_POLICY_VISIBILITY_20260429_001

Findings:
- Exploration/exploitation policy was validated as a guardrail artifact, but the operator dashboard did not expose dependency closure, candidate budget, or PAPER ranking review scope.
- This created a user misjudgment risk: PAPER exploitation review could be mistaken for LIVE_READY, or budget pressure could be hidden from the first screen.

Patch:
- Added Exploration / Exploitation Policy to the read-only dashboard shell schema, builder, validator, and HTML.
- Added fail-closed tests for live/scale drift, false eligibility without dependency closure, dependency count mismatch, and candidate budget breach.
- Kept all dashboard data display-only; no live order, live config mutation, order submission, or scale-up permission is created.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
