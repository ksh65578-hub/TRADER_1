# MVP4 Scorecard Not Live Ready UX Guard Audit

created_at_utc: 2026-04-29T03:31:22Z
patch_id: MVP4_SCORECARD_NOT_LIVE_READY_UX_GUARD_20260429_001

Findings:
- The dashboard can now show SCORECARD_INPUT_READY after scoped PAPER evidence, but that wording can be misread as LIVE_READY without a separate readiness scope.
- Existing HTML safety test was too broad: it blocked any LIVE_READY text, including explicit "not LIVE_READY" safety wording.
- The dashboard validator required the LIVE_READY token in the warning but did not require the explicit negation "not LIVE_READY", allowing misleading warning drift.

Patch:
- Added profitability_maturity.scorecard_scope with PAPER_SCORECARD_INPUT_ONLY and display-only fallback states.
- Added profitability_maturity.live_readiness_status=NOT_LIVE_READY as a schema-required constant.
- Added profitability_maturity.operator_warning and validator logic requiring "not LIVE_READY" plus "live orders".
- Added negative tests for misleading LIVE_READY wording, missing warning, live-readiness status drift, and ineligible scorecard scope.
- Regenerated root launcher dashboard artifacts so runtime dashboards carry the new scope and warning fields.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
