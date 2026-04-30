# MVP4 Paper/Shadow Actual Runtime Source Identity Hygiene Audit

created_at_utc: 2026-04-30T07:40:00Z
patch_id: MVP4_PAPER_SHADOW_ACTUAL_RUNTIME_SOURCE_IDENTITY_HYGIENE_20260430_001

Finding:
- Existing long-run evidence guards required VALIDATED_NON_LIVE_RUNTIME and source ids, but the ids were still generic strings.
- A dashboard, summary, heartbeat, startup_probe, launcher, or stability-history id could be mislabeled as an actual runtime source unless the validator checked source identity semantics.
- A one-sided PAPER-only runtime source id could also overstate PAPER/SHADOW long-run evidence maturity.

Patch:
- Added semantic actual runtime source id validation for paper/shadow evidence accumulation.
- Added schema conditional requiring at least two actual runtime source ids when status is VALIDATED_NON_LIVE_RUNTIME.
- Added negative tests and validator self-checks for display-truth source ids and one-sided PAPER-only source ids.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
