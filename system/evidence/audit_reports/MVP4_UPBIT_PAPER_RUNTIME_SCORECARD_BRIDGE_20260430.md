# MVP4 Upbit PAPER Runtime Scorecard Bridge Audit

created_at_utc: 2026-04-30T14:18:58Z
patch_id: MVP4_UPBIT_PAPER_RUNTIME_SCORECARD_BRIDGE_20260430_001

Finding:
- Candidate scorecard schema and validators existed, but actual Upbit PAPER runtime cycle output did not have a direct runtime-to-scorecard builder/artifact bridge. This left the profitability improvement loop dependent on fixtures and reports rather than actual PAPER candidate evidence.

Patch:
- Added a PAPER-only candidate scorecard builder from validated Upbit PAPER runtime cycles.
- Added tests proving runtime-generated scorecards are NET_EV_AFTER_COST based, live-blocked, robustness-blocked by default, and cannot be created from invalid runtime cycles.
- Extended candidate_scorecard_validator to validate a runtime-generated scorecard, not just static fixtures.
- Wrote latest runtime candidate scorecard artifact under the UPBIT/KRW_SPOT/PAPER session namespace.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- Runtime scorecards are still PAPER evidence only. OOS, walk-forward, bootstrap, overfit, long-run PAPER/SHADOW evidence, official API verification, read-only burn-in, manual order evidence, and operator approval remain required before any later live review.
