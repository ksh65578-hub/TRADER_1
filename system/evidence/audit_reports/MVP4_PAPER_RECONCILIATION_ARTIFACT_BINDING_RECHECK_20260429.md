# MVP4 Paper Reconciliation Artifact Binding Recheck

created_at_utc: 2026-04-29T09:41:21Z
patch_id: MVP4_PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK_20260429_001

Findings:
- The dashboard could show the Ledger & Reconciliation panel, but root launcher generation did not load session-scoped reconciliation_report.json or restart_recovery_report.json.
- Existing non-session-scoped runtime reports must not be reused by launcher dashboards because that would mix session truth.
- If a wrong-session reconciliation file is placed in the launcher session path, the dashboard must show red INVALID rather than silently treating it as usable evidence.

Patch:
- Added session-scoped reconciliation and restart recovery paths to the root launcher dashboard bundle.
- Added loader plumbing that passes loaded reconciliation/restart artifacts to the dashboard shell.
- Added tests for exact-session PASS binding, mismatch red blocker, cross-session invalid blocker, and restart recovery fallback from scoped paper operation gate.
- Wrote session-scoped PAPER reconciliation artifacts for UPBIT and BINANCE, plus UPBIT restart recovery, then regenerated dashboard HTML/runtime artifacts.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
