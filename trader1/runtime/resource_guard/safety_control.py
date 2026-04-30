from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


SAFETY_CONTROL_SCHEMA_ID = "trader1.safety_control_report.v1"
RESOURCE_HEALTH_STATES = {"PASS", "WARN", "LIMITED", "CRITICAL", "UNKNOWN"}
KILL_SWITCH_STATES = {"AVAILABLE", "ENGAGED", "UNAVAILABLE"}
SAFE_FINAL_DECISIONS = {"NO_TRADE", "SAFE_MODE", "KILL_SWITCH", "BLOCKED", "TRADE_DISABLED", "RECONCILE_REQUIRED"}


@dataclass(frozen=True)
class SafetyControlValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safety_control_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("safety_control_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _resource_state(metrics: dict[str, Any] | None) -> tuple[str, str | None]:
    if not metrics:
        return "PASS", None
    if metrics.get("critical") is True:
        return "CRITICAL", "RESOURCE_LIMIT_BLOCK"
    if metrics.get("memory_danger") is True or metrics.get("disk_full") is True:
        return "CRITICAL", "RESOURCE_LIMIT_BLOCK"
    if metrics.get("cpu_pressure") == "CRITICAL" or metrics.get("queue_backlog") == "CRITICAL":
        return "CRITICAL", "RESOURCE_LIMIT_BLOCK"
    if metrics.get("limited") is True:
        return "LIMITED", "RESOURCE_LIMIT"
    if metrics.get("warn") is True:
        return "WARN", None
    return "PASS", None


def build_safety_control_report(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    operator_action: str | None = None,
    kill_switch_available: bool = True,
    kill_switch_engaged: bool = False,
    resource_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resource_health_state, resource_blocker = _resource_state(resource_metrics)
    kill_switch_state = "AVAILABLE"
    kill_blocker = None
    if not kill_switch_available:
        kill_switch_state = "UNAVAILABLE"
        kill_blocker = "KILL_SWITCH_ACTIVE"
    elif kill_switch_engaged or operator_action == "manual_stop":
        kill_switch_state = "ENGAGED"
        kill_blocker = "KILL_SWITCH_ACTIVE"

    blockers: list[dict[str, str]] = []
    if kill_blocker:
        blockers.append(_blocker(kill_blocker, "kill switch blocks new orders", "CRITICAL"))
    if resource_blocker:
        blockers.append(_blocker(resource_blocker, "resource guard blocks new entries", "HIGH"))

    primary_blocker = blockers[0]["code"] if blockers else None
    if kill_blocker:
        final_decision = "KILL_SWITCH"
    elif resource_blocker:
        final_decision = "NO_TRADE"
    elif operator_action == "manual_safe_mode":
        final_decision = "SAFE_MODE"
    else:
        final_decision = "SAFE_MODE"

    report = {
        "schema_id": SAFETY_CONTROL_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "operator_action": operator_action,
        "kill_switch_state": kill_switch_state,
        "kill_switch_available": kill_switch_available,
        "kill_switch_engaged": kill_switch_state == "ENGAGED",
        "resource_health_state": resource_health_state,
        "resource_block_new_entries": resource_health_state in {"LIMITED", "CRITICAL"},
        "safe_mode_required": bool(blockers) or operator_action == "manual_safe_mode",
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "final_decision": final_decision,
        "primary_blocker_code": primary_blocker,
        "blockers": blockers,
        "next_action": "continue read-only monitoring" if not blockers else "resolve safety blocker before trading review",
        "safety_control_hash": "",
    }
    report["safety_control_hash"] = safety_control_hash(report)
    return report


def validate_safety_control_report(
    report: dict[str, Any],
    allowed_blockers: set[str] | None = None,
) -> SafetyControlValidationResult:
    if report.get("schema_id") != SAFETY_CONTROL_SCHEMA_ID:
        return SafetyControlValidationResult("FAIL", "safety control schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("safety_control_hash") != safety_control_hash(report):
        return SafetyControlValidationResult("FAIL", "safety control hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("dashboard_truth_only") is not True:
        return SafetyControlValidationResult("FAIL", "safety control report must remain dashboard serving truth only", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("can_submit_order"):
        return SafetyControlValidationResult("BLOCKED", "safety control attempted to create live or order permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("order_adapter_called"):
        return SafetyControlValidationResult("BLOCKED", "safety control cannot call order adapter", "LIVE_FINAL_GUARD_FAILED")
    if report.get("kill_switch_state") not in KILL_SWITCH_STATES:
        return SafetyControlValidationResult("FAIL", "unknown kill switch state", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("resource_health_state") not in RESOURCE_HEALTH_STATES:
        return SafetyControlValidationResult("FAIL", "unknown resource health state", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("final_decision") not in SAFE_FINAL_DECISIONS:
        return SafetyControlValidationResult("FAIL", "safety control final_decision is not fail-closed", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return SafetyControlValidationResult("FAIL", "safety control blockers must be a list", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return SafetyControlValidationResult("FAIL", f"unknown safety blocker: {code}", "UNKNOWN_BLOCKED")

    kill_switch_state = report.get("kill_switch_state")
    if kill_switch_state in {"ENGAGED", "UNAVAILABLE"}:
        if report.get("primary_blocker_code") != "KILL_SWITCH_ACTIVE":
            return SafetyControlValidationResult("BLOCKED", "kill switch state must expose KILL_SWITCH_ACTIVE", "KILL_SWITCH_ACTIVE")
        if report.get("final_decision") != "KILL_SWITCH":
            return SafetyControlValidationResult("BLOCKED", "kill switch must force KILL_SWITCH final decision", "KILL_SWITCH_ACTIVE")
        if report.get("safe_mode_required") is not True:
            return SafetyControlValidationResult("BLOCKED", "kill switch must require safe mode", "KILL_SWITCH_ACTIVE")
    if kill_switch_state == "AVAILABLE" and report.get("kill_switch_available") is not True:
        return SafetyControlValidationResult("FAIL", "available kill switch has inconsistent availability flag", "SCHEMA_IDENTITY_MISMATCH")

    resource_health_state = report.get("resource_health_state")
    if resource_health_state == "CRITICAL":
        codes = {blocker.get("code") for blocker in blockers if isinstance(blocker, dict)}
        if "RESOURCE_LIMIT_BLOCK" not in codes:
            return SafetyControlValidationResult("BLOCKED", "critical resource state must expose RESOURCE_LIMIT_BLOCK", "RESOURCE_LIMIT_BLOCK")
        if report.get("resource_block_new_entries") is not True:
            return SafetyControlValidationResult("BLOCKED", "critical resource state must block new entries", "RESOURCE_LIMIT_BLOCK")
    if resource_health_state == "LIMITED" and report.get("resource_block_new_entries") is not True:
        return SafetyControlValidationResult("BLOCKED", "limited resource state must block new entries", "RESOURCE_LIMIT")
    if resource_health_state in {"PASS", "WARN"} and report.get("resource_block_new_entries") is True:
        return SafetyControlValidationResult("FAIL", "resource block flag inconsistent with non-blocking state", "SCHEMA_IDENTITY_MISMATCH")

    primary = report.get("primary_blocker_code")
    if blockers and primary is None:
        return SafetyControlValidationResult("BLOCKED", "safety blockers require primary_blocker_code", "UNKNOWN_BLOCKED")
    if not blockers and primary is not None:
        return SafetyControlValidationResult("FAIL", "primary blocker set without blockers", "LIVE_FINAL_GUARD_FAILED")
    return SafetyControlValidationResult("PASS", "safety controls keep kill switch and resource guard fail-closed", None)
