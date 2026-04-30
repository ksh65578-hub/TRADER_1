# MVP4 Upbit Public REST Continuity History Audit

created_at_utc: 2026-04-30T12:18:58Z
patch_id: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_HISTORY_20260430_001

Findings:
- Hidden issue: continuity attempts were one-off artifacts and could not show repeated pass/block rates over time.
- Hidden issue: corrupt previous continuity history could be silently overwritten without audit preservation.
- Hidden issue: short continuity evidence needed explicit non-promotion fields so it is not mistaken for long-run evidence.

Patch:
- Added strict continuity history schema, runtime builder, validator, tests, and CLI updater.
- Attempt hashes, pass/blocked counts, duplicate/non-advancing counts, and data unavailable counts are now visible.
- Corrupt or invalid previous history is quarantined before a new history is written.
- History remains PAPER-only and cannot set live readiness, live order permission, live trading, or scale-up.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
