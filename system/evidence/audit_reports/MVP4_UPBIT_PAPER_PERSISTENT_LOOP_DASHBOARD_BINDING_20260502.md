# MVP4 Upbit PAPER Persistent Loop Dashboard Binding Audit

created_at_utc: 2026-05-02T01:56:25Z
patch_id: MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING_20260502_001

Patch:
- Writes a canonical Upbit PAPER persistent loop report at paper_runtime/upbit_paper_persistent_loop_report.json.
- Loads the scoped canonical/latest persistent loop report through the safe launcher.
- Adds a read-only dashboard panel and schema for paper_persistent_loop_status.
- Keeps the bounded PAPER loop separated from long-run evidence, LIVE_READY, live orders, and scale-up.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live orders, live config mutation, LIVE_READY writer, or scale-up
