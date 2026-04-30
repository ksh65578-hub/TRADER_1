# MVP4 Candidate Scorecard Live Separation Hardening Audit

created_at_utc: 2026-04-29T03:38:01Z
patch_id: MVP4_CANDIDATE_SCORECARD_LIVE_SEPARATION_HARDENING_20260429_001

Findings:
- Candidate scorecard artifacts could be ranking_eligible without carrying a structural PAPER-only scope.
- Optimizer inputs could therefore depend on dashboard wording to distinguish scorecard input from LIVE_READY.
- Candidate scorecard validator did not reject misleading operator warning text such as "is LIVE_READY".

Patch:
- Added scorecard_scope, live_readiness_status, and operator_warning to candidate_scorecard schema.
- Updated all candidate scorecard fixtures with PAPER_SCORECARD_INPUT_ONLY and NOT_LIVE_READY fields.
- Added a misleading LIVE_READY wording negative fixture.
- Hardened candidate_scorecard_net_ev_validator so ranking_eligible remains PAPER_SCORECARD_INPUT_ONLY and warnings must say not LIVE_READY.
- Added unit tests for misleading wording and ranking scope drift.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
