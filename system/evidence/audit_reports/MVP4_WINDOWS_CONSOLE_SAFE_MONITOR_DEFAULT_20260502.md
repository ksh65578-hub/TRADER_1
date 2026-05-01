# MVP4 Windows Console Safe Monitor Default Audit

created_at_utc: 2026-05-01T18:41:06Z
patch_id: MVP4_WINDOWS_CONSOLE_SAFE_MONITOR_DEFAULT_20260502_001

Finding:
- Root launchers in interactive console sessions still used a one-heartbeat default, so Windows/double-click users could see the console close immediately after safe boot.

Patch:
- Interactive launcher sessions now default to SAFE_MONITOR continuous heartbeat until Ctrl+C.
- Non-interactive automation remains bounded to one heartbeat by default.
- Tests mock the continuous emitter to verify default routing without hanging.
- Live flags remain false and no order adapter submit path is enabled.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
