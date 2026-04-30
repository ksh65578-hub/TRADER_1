from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


OPERATOR_ACTION_AUDIT_SCHEMA_ID = "trader1.operator_action_audit.v1"
ALLOWED_ACTIONS = {
    "manual_stop",
    "manual_resume_read_only",
    "manual_ack_trade_disabled",
    "manual_unlock_held_market_event",
    "manual_retry_reconcile",
    "manual_safe_mode",
    "manual_disable_strategy",
    "manual_reduce_position",
    "manual_exit_all_positions",
}
HIGH_RISK_ACTIONS = {
    "manual_exit_all_positions",
    "manual_reduce_position",
    "manual_disable_strategy",
    "manual_safe_mode",
    "manual_ack_trade_disabled",
}
ORDER_AFFECTING_ACTIONS = {"manual_reduce_position", "manual_exit_all_positions"}
CONFIRMATION_METHODS = {"NONE", "LOCAL_UI", "CLI_CONFIRM_PHRASE", "TWO_STEP"}
FINAL_DECISIONS = {
    "EXIT_POSITION",
    "REDUCE_POSITION",
    "NO_TRADE",
    "SAFE_MODE",
    "RECONCILE_REQUIRED",
    "TRADE_DISABLED",
    "KILL_SWITCH",
    "BLOCKED",
}
RESULTS = {"ACCEPTED", "REJECTED", "EXECUTED", "FAILED", "BLOCKED"}
LIVE_PERMISSION_KEYS = {"live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order"}


@dataclass(frozen=True)
class OperatorControlValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def operator_action_hash(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("event_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _contains_live_permission(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in LIVE_PERMISSION_KEYS and item is True:
                return True
            if key == "live_trading_status" and item == "LIVE_ACTIVE":
                return True
            if _contains_live_permission(item):
                return True
    if isinstance(value, list):
        return any(_contains_live_permission(item) for item in value)
    return False


def _base_state(**overrides: Any) -> dict[str, Any]:
    state = {
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
    }
    state.update(overrides)
    return state


def _decision_for_action(action_code: str) -> tuple[str | None, str, str | None]:
    if action_code == "manual_stop":
        return "KILL_SWITCH", "BLOCKED", "manual stop keeps trading blocked"
    if action_code == "manual_safe_mode":
        return "SAFE_MODE", "BLOCKED", "manual safe mode keeps trading blocked"
    if action_code == "manual_resume_read_only":
        return "SAFE_MODE", "ACCEPTED", "read-only resume cannot create live permission"
    if action_code == "manual_ack_trade_disabled":
        return "TRADE_DISABLED", "BLOCKED", "trade-disabled acknowledgement keeps live orders blocked"
    if action_code == "manual_disable_strategy":
        return "TRADE_DISABLED", "BLOCKED", "manual strategy disable is risk reducing only"
    if action_code == "manual_retry_reconcile":
        return "RECONCILE_REQUIRED", "BLOCKED", "reconciliation retry cannot trade"
    if action_code == "manual_unlock_held_market_event":
        return "NO_TRADE", "BLOCKED", "held market event unlock still requires preflight"
    if action_code in ORDER_AFFECTING_ACTIONS:
        return "RECONCILE_REQUIRED", "BLOCKED", "order-affecting manual action requires adapter, ledger, and reconciliation"
    return "BLOCKED", "BLOCKED", "unknown operator action blocked"


def build_operator_action_audit(
    *,
    action_id: str,
    operator_id_hash: str,
    action_code: str,
    exchange: str | None = "UPBIT",
    market_type: str | None = "KRW_SPOT",
    mode: str | None = "PAPER",
    session_id: str | None = "mvp1_operator_control",
    target_symbol: str | None = None,
    previous_state: dict[str, Any] | None = None,
    requested_state: dict[str, Any] | None = None,
    risk_veto_result: str = "NOT_APPLICABLE",
    reconciliation_status: str | None = None,
    confirmation_method: str | None = None,
) -> dict[str, Any]:
    high_risk = action_code in HIGH_RISK_ACTIONS
    final_decision_id, result, result_reason = _decision_for_action(action_code)
    if reconciliation_status is None:
        reconciliation_status = "FAIL" if action_code in ORDER_AFFECTING_ACTIONS else "NOT_APPLICABLE"
    if confirmation_method is None:
        confirmation_method = "LOCAL_UI" if high_risk else "NONE"

    previous = _base_state(**(previous_state or {}))
    requested = _base_state(**(requested_state or {}))
    if action_code == "manual_stop":
        requested["kill_switch_state"] = "ENGAGED"
    elif action_code == "manual_safe_mode":
        requested["safe_mode_required"] = True
    elif action_code == "manual_resume_read_only":
        requested["mode"] = "READ_ONLY"
    elif action_code in ORDER_AFFECTING_ACTIONS:
        requested["requires_adapter_path"] = True
        requested["requires_ledger_record"] = True
        requested["requires_reconciliation_after_action"] = True

    record = {
        "schema_id": OPERATOR_ACTION_AUDIT_SCHEMA_ID,
        "action_id": action_id,
        "created_at_utc": utc_now(),
        "operator_id_hash": operator_id_hash,
        "action_code": action_code,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "target_symbol": target_symbol,
        "previous_state": previous,
        "requested_state": requested,
        "risk_veto_result": risk_veto_result,
        "reconciliation_status": reconciliation_status,
        "final_decision_id": final_decision_id,
        "confirmation_required": high_risk,
        "confirmation_method": confirmation_method,
        "result": result,
        "result_reason": result_reason,
        "event_hash": "",
    }
    record["event_hash"] = operator_action_hash(record)
    return record


def validate_operator_action_audit(record: dict[str, Any]) -> OperatorControlValidationResult:
    required = {
        "schema_id",
        "action_id",
        "created_at_utc",
        "operator_id_hash",
        "action_code",
        "confirmation_required",
        "confirmation_method",
        "result",
        "event_hash",
    }
    missing = sorted(required - set(record))
    if missing:
        return OperatorControlValidationResult("FAIL", f"operator audit missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if record.get("schema_id") != OPERATOR_ACTION_AUDIT_SCHEMA_ID:
        return OperatorControlValidationResult("FAIL", "operator audit schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if record.get("event_hash") != operator_action_hash(record):
        return OperatorControlValidationResult("FAIL", "operator audit event_hash mismatch", "SCHEMA_IDENTITY_MISMATCH")

    action_code = record.get("action_code")
    if action_code not in ALLOWED_ACTIONS:
        return OperatorControlValidationResult("BLOCKED", "unknown operator action is blocked", "UNKNOWN_BLOCKED")
    if record.get("confirmation_method") not in CONFIRMATION_METHODS:
        return OperatorControlValidationResult("FAIL", "unknown confirmation method", "SCHEMA_IDENTITY_MISMATCH")
    if record.get("result") not in RESULTS:
        return OperatorControlValidationResult("FAIL", "unknown operator action result", "SCHEMA_IDENTITY_MISMATCH")
    final_decision = record.get("final_decision_id")
    if final_decision is not None and final_decision not in FINAL_DECISIONS:
        return OperatorControlValidationResult("BLOCKED", "operator final decision is not fail-closed", "LIVE_FINAL_GUARD_FAILED")

    for state_key in ("previous_state", "requested_state"):
        state = record.get(state_key)
        if not isinstance(state, dict):
            return OperatorControlValidationResult("FAIL", f"{state_key} must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if _contains_live_permission(state):
            return OperatorControlValidationResult("BLOCKED", "manual action attempted to create live permission", "LIVE_FINAL_GUARD_FAILED")
        if state.get("order_adapter_called") is True:
            return OperatorControlValidationResult("BLOCKED", "operator audit cannot record direct adapter call in MVP-1", "LIVE_FINAL_GUARD_FAILED")

    if record.get("risk_veto_result") == "FAIL":
        if record.get("result") != "BLOCKED" or final_decision not in {"NO_TRADE", "SAFE_MODE", "TRADE_DISABLED", "KILL_SWITCH", "BLOCKED", "RECONCILE_REQUIRED"}:
            return OperatorControlValidationResult("BLOCKED", "risk veto failure must keep operator action blocked", "RISK_VETO")

    if action_code in HIGH_RISK_ACTIONS:
        if record.get("confirmation_required") is not True:
            return OperatorControlValidationResult("BLOCKED", "high-risk operator action requires confirmation", "OPERATOR_APPROVAL_MISSING")
        if record.get("confirmation_method") == "NONE":
            return OperatorControlValidationResult("BLOCKED", "high-risk operator action requires explicit confirmation method", "OPERATOR_APPROVAL_MISSING")
        scope_fields = ("exchange", "market_type", "mode", "session_id")
        if any(record.get(field) in {None, ""} for field in scope_fields):
            return OperatorControlValidationResult("BLOCKED", "high-risk operator action requires explicit target scope", "SNAPSHOT_SCOPE_MISMATCH")

    if action_code == "manual_stop":
        if final_decision != "KILL_SWITCH" or record.get("result") != "BLOCKED":
            return OperatorControlValidationResult("BLOCKED", "manual_stop must force kill switch blocked state", "KILL_SWITCH_ACTIVE")
    if action_code == "manual_safe_mode":
        if final_decision != "SAFE_MODE" or record.get("result") != "BLOCKED":
            return OperatorControlValidationResult("BLOCKED", "manual_safe_mode must keep safe mode blocked state", "LIVE_FINAL_GUARD_FAILED")
    if action_code == "manual_resume_read_only":
        requested = record.get("requested_state", {})
        if requested.get("mode") not in {"READ_ONLY", "SAFE"}:
            return OperatorControlValidationResult("BLOCKED", "manual_resume_read_only cannot resume live mode", "LIVE_FINAL_GUARD_FAILED")
    if action_code in ORDER_AFFECTING_ACTIONS:
        if record.get("result") == "EXECUTED":
            return OperatorControlValidationResult("BLOCKED", "MVP-1 operator control cannot execute order-affecting actions", "LIVE_FINAL_GUARD_FAILED")
        requested = record.get("requested_state", {})
        if not requested.get("requires_adapter_path") or not requested.get("requires_ledger_record"):
            return OperatorControlValidationResult("BLOCKED", "manual reduce/exit requires adapter and ledger record", "LEDGER_UNAVAILABLE")
        if record.get("reconciliation_status") != "PASS":
            return OperatorControlValidationResult("BLOCKED", "manual reduce/exit requires reconciliation before it can proceed", "RECONCILIATION_REQUIRED")

    return OperatorControlValidationResult("PASS", "operator action audit is explicit, auditable, and fail-closed", None)
