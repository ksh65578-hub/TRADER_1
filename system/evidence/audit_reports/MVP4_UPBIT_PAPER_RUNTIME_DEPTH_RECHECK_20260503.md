# MVP4 Upbit PAPER Runtime Depth Recheck

created_at_utc: 2026-05-03T12:25:31Z
patch_id: MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK_20260503_001

Finding:
- Persistent PAPER loop summaries did not require the full public source, feature, regime, selected-candidate, and strategy/regime/cost linkage evidence carried by each runtime cycle report.

Patch:
- Added runtime-depth fields to cycle_results.
- Tightened persistent-loop validation and schema for source/runtime hash binding, canonical event depth, and linkage live blockers.
- Added negative tests for static fixture role mutation, missing depth, hash mismatch, and linkage live permission.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
