# MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD

created_at_utc: 2026-05-03T22:26:01Z
patch_id: MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD_20260504_001

Finding:
- Actual long-run evidence depends on PAPER/SHADOW source artifact paths remaining bound to the exact exchange, market, mode, and session scope.
- A path could still look like a PAPER namespace while pointing at a different session segment unless the runtime validator checked the canonical path.

Patch:
- Tightened the paper/shadow evidence schema path pattern to a single session segment.
- Added a semantic validator check that paper_artifact_path and shadow_artifact_path exactly match the canonical paths derived from report scope.
- Added a negative validator test for path-scope drift with matching source binding drift.

Safety:
- ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY remains OPEN and live-affecting.
- actual_long_run_evidence_created=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
