# MVP4 Upbit PAPER Persistent Runtime Recovery Preflight Audit

created_at_utc: 2026-05-01T18:58:32Z
patch_id: MVP4_UPBIT_PAPER_PERSISTENT_RUNTIME_RECOVERY_PREFLIGHT_20260502_001

Findings:
- The recovery guard could detect corrupt or unreconciled runtime state, but the persistent loop performed new cycle writes before the guard was checked.
- This allowed a blocked prior state to produce fresh-looking current PAPER artifacts before reconciliation.

Patch:
- Detects prior runtime state before loop execution.
- Runs recovery preflight when prior runtime state exists.
- Blocks new current cycle/latest/ledger writes when preflight is BLOCKED.
- Keeps clean PAPER-only resume working and records preflight status in the loop report.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live orders, live config mutation, LIVE_READY writer, or scale-up
