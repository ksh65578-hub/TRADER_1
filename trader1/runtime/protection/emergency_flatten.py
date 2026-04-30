from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


EMERGENCY_FLATTEN_REPORT_SCHEMA_ID = "trader1.emergency_flatten_report.v1"
DRY_RUN_STATUSES = {"PASS", "BLOCKED", "NOT_RUN"}
ORPHAN_STATES = {"NONE", "PRESENT", "UNKNOWN"}
SAFE_FINAL_DECISIONS = {"NO_TRADE", "SAFE_MODE", "RECONCILE_REQUIRED", "BLOCKED"}
LIVE_PERMISSION_KEYS = {"live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order"}
MANDATORY_COMPONENTS = {
    "emergency_flatten": "emergency_flatten_available",
    "manual_exit_all_positions": "manual_exit_all_positions_available",
    "manual_reduce_position": "manual_reduce_position_available",
    "cancel_all_open_orders": "cancel_all_open_orders_available",
    "reduce_only_path_for_futures": "reduce_only_path_available_for_futures",
    "reconciliation_path": "reconciliation_path_available",
    "operator_alert": "operator_alert_available",
    "ledger_recording": "ledger_recording_available",
}


@dataclass(frozen=True)
class EmergencyFlattenValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def emergency_flatten_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("emergency_flatten_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


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


def _component_check(
    component: str,
    available: bool,
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    message: str,
) -> dict[str, Any]:
    return {
        "component": component,
        "available": available,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "message": message,
    }


def _scope_mismatch(report: dict[str, Any]) -> bool:
    expected = {
        "exchange": report.get("exchange"),
        "market_type": report.get("market_type"),
        "mode": report.get("mode"),
        "session_id": report.get("session_id"),
    }
    for check in report.get("component_checks", []):
        if not isinstance(check, dict):
            return True
        for field, value in expected.items():
            if check.get(field) != value:
                return True
    return False


def _dry_run_actions(market_type: str) -> list[dict[str, Any]]:
    actions = [
        "cancel_all_open_orders",
        "manual_exit_all_positions",
        "manual_reduce_position",
    ]
    if market_type == "FUTURES_USDT_M":
        actions.append("futures_reduce_only_flatten")
    return [
        {
            "action": action,
            "would_call_adapter": False,
            "would_create_entry_risk": False,
            "requires_ledger": True,
            "requires_reconciliation": True,
        }
        for action in actions
    ]


def build_emergency_flatten_report(
    *,
    emergency_flatten_id: str,
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    mode: str = "PAPER",
    session_id: str = "mvp1_emergency_flatten",
    emergency_flatten_available: bool = True,
    manual_exit_all_positions_available: bool = True,
    manual_reduce_position_available: bool = True,
    cancel_all_open_orders_available: bool = True,
    reduce_only_path_available_for_futures: bool = True,
    reconciliation_path_available: bool = True,
    operator_alert_available: bool = True,
    ledger_recording_available: bool = True,
    orphan_position_state: str = "NONE",
    orphan_open_order_state: str = "NONE",
    dry_run: bool = True,
    component_scope_overrides: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    component_scope_overrides = component_scope_overrides or {}
    available_by_component = {
        "emergency_flatten": emergency_flatten_available,
        "manual_exit_all_positions": manual_exit_all_positions_available,
        "manual_reduce_position": manual_reduce_position_available,
        "cancel_all_open_orders": cancel_all_open_orders_available,
        "reduce_only_path_for_futures": reduce_only_path_available_for_futures,
        "reconciliation_path": reconciliation_path_available,
        "operator_alert": operator_alert_available,
        "ledger_recording": ledger_recording_available,
    }
    component_checks = []
    for component, available in available_by_component.items():
        scope = {
            "exchange": exchange,
            "market_type": market_type,
            "mode": mode,
            "session_id": session_id,
        }
        scope.update(component_scope_overrides.get(component, {}))
        component_checks.append(
            _component_check(
                component,
                available,
                exchange=scope["exchange"],
                market_type=scope["market_type"],
                mode=scope["mode"],
                session_id=scope["session_id"],
                message="available" if available else "unavailable",
            )
        )

    blockers: list[dict[str, str]] = []
    if not dry_run:
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "MVP-1 emergency flatten must remain dry-run only", "CRITICAL"))
    if orphan_position_state not in ORPHAN_STATES:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "unknown orphan position state", "HIGH"))
    elif orphan_position_state != "NONE":
        blockers.append(_blocker("ORPHAN_POSITION_REVIEW_REQUIRED", "orphan position review is required before emergency flatten readiness", "HIGH"))
    if orphan_open_order_state not in ORPHAN_STATES:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "unknown orphan open order state", "HIGH"))
    elif orphan_open_order_state != "NONE":
        blockers.append(_blocker("ORPHAN_OPEN_ORDER_REVIEW_REQUIRED", "orphan open order review is required before emergency flatten readiness", "HIGH"))

    if market_type != "FUTURES_USDT_M":
        reduce_only_required = False
    else:
        reduce_only_required = True

    missing_mandatory = [
        component
        for component, available in available_by_component.items()
        if not available and (component != "reduce_only_path_for_futures" or reduce_only_required)
    ]
    for component in missing_mandatory:
        if component == "reconciliation_path":
            blockers.append(_blocker("RECONCILIATION_REQUIRED", "emergency protection requires reconciliation path", "HIGH"))
        elif component == "ledger_recording":
            blockers.append(_blocker("LEDGER_UNAVAILABLE", "emergency protection requires ledger recording", "HIGH"))
        else:
            blockers.append(_blocker("EMERGENCY_FLATTEN_UNAVAILABLE", f"emergency protection component unavailable: {component}", "HIGH"))

    probe = {
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "component_checks": component_checks,
    }
    if _scope_mismatch(probe):
        blockers.insert(0, _blocker("SNAPSHOT_SCOPE_MISMATCH", "emergency protection component scope mismatch", "CRITICAL"))

    emergency_protection_available = not blockers
    report = {
        "schema_id": EMERGENCY_FLATTEN_REPORT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "emergency_flatten_id": emergency_flatten_id,
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "emergency_protection_available": emergency_protection_available,
        "emergency_flatten_available": emergency_flatten_available,
        "manual_exit_all_positions_available": manual_exit_all_positions_available,
        "manual_reduce_position_available": manual_reduce_position_available,
        "cancel_all_open_orders_available": cancel_all_open_orders_available,
        "reduce_only_path_available_for_futures": reduce_only_path_available_for_futures,
        "reconciliation_path_available": reconciliation_path_available,
        "operator_alert_available": operator_alert_available,
        "ledger_recording_available": ledger_recording_available,
        "orphan_position_state": orphan_position_state,
        "orphan_open_order_state": orphan_open_order_state,
        "dry_run": dry_run,
        "dry_run_status": "PASS" if emergency_protection_available else "BLOCKED",
        "dry_run_actions": _dry_run_actions(market_type) if dry_run else [],
        "component_checks": component_checks,
        "final_decision": "NO_TRADE" if emergency_protection_available else "BLOCKED",
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "new_entry_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "emergency_flatten_hash": "",
    }
    report["emergency_flatten_hash"] = emergency_flatten_hash(report)
    return report


def validate_emergency_flatten_report(
    report: dict[str, Any],
    allowed_blockers: set[str] | None = None,
) -> EmergencyFlattenValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "emergency_flatten_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "emergency_protection_available",
        "emergency_flatten_available",
        "manual_exit_all_positions_available",
        "manual_reduce_position_available",
        "cancel_all_open_orders_available",
        "reduce_only_path_available_for_futures",
        "reconciliation_path_available",
        "operator_alert_available",
        "ledger_recording_available",
        "orphan_position_state",
        "orphan_open_order_state",
        "dry_run",
        "dry_run_status",
        "dry_run_actions",
        "component_checks",
        "final_decision",
        "primary_blocker_code",
        "blockers",
        "new_entry_allowed",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "order_adapter_called",
        "emergency_flatten_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return EmergencyFlattenValidationResult("FAIL", f"emergency flatten report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != EMERGENCY_FLATTEN_REPORT_SCHEMA_ID:
        return EmergencyFlattenValidationResult("FAIL", "emergency flatten schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("emergency_flatten_hash") != emergency_flatten_hash(report):
        return EmergencyFlattenValidationResult("FAIL", "emergency flatten hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("project_id") != "TRADER_1":
        return EmergencyFlattenValidationResult("FAIL", "emergency flatten project_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("dry_run_status") not in DRY_RUN_STATUSES:
        return EmergencyFlattenValidationResult("FAIL", "unknown emergency dry_run_status", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("final_decision") not in SAFE_FINAL_DECISIONS:
        return EmergencyFlattenValidationResult("BLOCKED", "emergency flatten final_decision is not fail-closed", "LIVE_FINAL_GUARD_FAILED")
    if report.get("new_entry_allowed") is not False:
        return EmergencyFlattenValidationResult("BLOCKED", "emergency flatten cannot allow new entries", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order"):
        return EmergencyFlattenValidationResult("BLOCKED", "emergency flatten attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("order_adapter_called"):
        return EmergencyFlattenValidationResult("BLOCKED", "MVP-1 emergency flatten dry-run cannot call order adapter", "LIVE_FINAL_GUARD_FAILED")
    if report.get("dry_run") is not True:
        return EmergencyFlattenValidationResult("BLOCKED", "MVP-1 emergency flatten must be dry-run only", "LIVE_FINAL_GUARD_FAILED")
    if _contains_live_permission(report.get("component_checks")) or _contains_live_permission(report.get("dry_run_actions")):
        return EmergencyFlattenValidationResult("BLOCKED", "emergency flatten nested evidence attempted live permission", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return EmergencyFlattenValidationResult("FAIL", "emergency flatten blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return EmergencyFlattenValidationResult("FAIL", f"unknown emergency blocker: {code}", "UNKNOWN_BLOCKED")

    checks = report.get("component_checks")
    if not isinstance(checks, list):
        return EmergencyFlattenValidationResult("FAIL", "emergency component_checks must be an array", "SCHEMA_IDENTITY_MISMATCH")
    check_components = {check.get("component") for check in checks if isinstance(check, dict)}
    if check_components != set(MANDATORY_COMPONENTS):
        return EmergencyFlattenValidationResult("BLOCKED", "emergency protection component coverage is incomplete", "EMERGENCY_FLATTEN_UNAVAILABLE")
    if _scope_mismatch(report):
        if report.get("primary_blocker_code") != "SNAPSHOT_SCOPE_MISMATCH":
            return EmergencyFlattenValidationResult("BLOCKED", "component scope mismatch must be primary blocker", "SNAPSHOT_SCOPE_MISMATCH")

    primary = report.get("primary_blocker_code")
    blocker_codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
    if blockers and primary not in blocker_codes:
        return EmergencyFlattenValidationResult("BLOCKED", "primary emergency blocker must match blockers", primary or "UNKNOWN_BLOCKED")
    if not blockers and primary is not None:
        return EmergencyFlattenValidationResult("FAIL", "primary blocker set without blockers", "LIVE_FINAL_GUARD_FAILED")

    action_rows = report.get("dry_run_actions")
    if not isinstance(action_rows, list):
        return EmergencyFlattenValidationResult("FAIL", "emergency dry_run_actions must be an array", "SCHEMA_IDENTITY_MISMATCH")
    for action in action_rows:
        if action.get("would_call_adapter") is not False:
            return EmergencyFlattenValidationResult("BLOCKED", "emergency dry-run cannot call adapter", "LIVE_FINAL_GUARD_FAILED")
        if action.get("would_create_entry_risk") is not False:
            return EmergencyFlattenValidationResult("BLOCKED", "emergency path cannot create entry risk", "LIVE_FINAL_GUARD_FAILED")
        if action.get("requires_ledger") is not True or action.get("requires_reconciliation") is not True:
            return EmergencyFlattenValidationResult("BLOCKED", "emergency actions require ledger and reconciliation", "RECONCILIATION_REQUIRED")

    protection_available = report.get("emergency_protection_available")
    if protection_available:
        if blockers:
            return EmergencyFlattenValidationResult("BLOCKED", "available emergency protection cannot carry blockers", "EMERGENCY_FLATTEN_UNAVAILABLE")
        if report.get("dry_run_status") != "PASS" or report.get("final_decision") != "NO_TRADE":
            return EmergencyFlattenValidationResult("BLOCKED", "available emergency protection must remain NO_TRADE dry-run", "LIVE_FINAL_GUARD_FAILED")
    else:
        if not blockers:
            return EmergencyFlattenValidationResult("BLOCKED", "unavailable emergency protection must expose blocker", "EMERGENCY_FLATTEN_UNAVAILABLE")
        if report.get("dry_run_status") != "BLOCKED" or report.get("final_decision") not in {"BLOCKED", "SAFE_MODE", "RECONCILE_REQUIRED"}:
            return EmergencyFlattenValidationResult("BLOCKED", "unavailable emergency protection must be blocked", "EMERGENCY_FLATTEN_UNAVAILABLE")

    if report.get("orphan_position_state") != "NONE" and "ORPHAN_POSITION_REVIEW_REQUIRED" not in blocker_codes:
        return EmergencyFlattenValidationResult("BLOCKED", "orphan position state must block emergency readiness", "ORPHAN_POSITION_REVIEW_REQUIRED")
    if report.get("orphan_open_order_state") != "NONE" and "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED" not in blocker_codes:
        return EmergencyFlattenValidationResult("BLOCKED", "orphan open order state must block emergency readiness", "ORPHAN_OPEN_ORDER_REVIEW_REQUIRED")

    return EmergencyFlattenValidationResult("PASS", "emergency flatten dry-run is scoped, auditable, and fail-closed", None)
