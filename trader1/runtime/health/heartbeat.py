from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


HEARTBEAT_SCHEMA_ID = "trader1.heartbeat.v1"
HEALTH_COMPONENTS = (
    "cpu",
    "memory",
    "disk",
    "event_latency",
    "queue_backlog",
    "rest_health",
    "websocket_health",
    "private_stream_health",
    "rate_limit_pressure",
    "watchdog_heartbeat",
)


@dataclass(frozen=True)
class HeartbeatValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def heartbeat_hash(heartbeat: dict[str, Any]) -> str:
    payload = dict(heartbeat)
    payload.pop("heartbeat_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _component(status: str = "PASS", message: str | None = None, observed_at_utc: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "observed_at_utc": observed_at_utc,
    }


def _component_statuses(overrides: dict[str, dict[str, Any]] | None, observed_at_utc: str) -> dict[str, dict[str, Any]]:
    components = {name: _component(observed_at_utc=observed_at_utc) for name in HEALTH_COMPONENTS}
    for name, value in (overrides or {}).items():
        if name in components:
            merged = dict(components[name])
            merged.update(value)
            components[name] = merged
    return components


def build_heartbeat(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    config_hash: str | None,
    registry_hash: str | None,
    schema_bundle_hash: str | None,
    source_tree_hash: str | None,
    engine_state: str = "BOOTSTRAP_READ_ONLY",
    startup_probe_phase: str = "STARTUP_PROBE_GATE_BLOCKED",
    component_overrides: dict[str, dict[str, Any]] | None = None,
    stale_after_seconds: int = 30,
    heartbeat_age_seconds: float = 0.0,
) -> dict[str, Any]:
    now = utc_now()
    components = _component_statuses(component_overrides, now)
    bad_components = [
        name
        for name, component in components.items()
        if component.get("status") not in {"PASS", "WARN"}
    ]
    stale = heartbeat_age_seconds > stale_after_seconds
    primary_blocker = None
    if stale:
        primary_blocker = "LATENCY_TTL_EXPIRED"
    elif bad_components:
        primary_blocker = "RESOURCE_LIMIT"

    heartbeat = {
        "schema_id": HEARTBEAT_SCHEMA_ID,
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "config_hash": config_hash,
        "registry_hash": registry_hash,
        "schema_bundle_hash": schema_bundle_hash,
        "source_tree_hash": source_tree_hash,
        "engine_state": engine_state,
        "startup_probe_phase": startup_probe_phase,
        "heartbeat_status": "BLOCKED" if primary_blocker else "PASS",
        "last_heartbeat_at_utc": now,
        "stale_after_seconds": stale_after_seconds,
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "dashboard_truth_only": True,
        "can_trade": False,
        "can_live_trade": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "components": components,
        "primary_blocker_code": primary_blocker,
        "blockers": []
        if primary_blocker is None
        else [
            {
                "code": primary_blocker,
                "severity": "HIGH",
                "message": "heartbeat status blocks trading decisions",
            }
        ],
        "final_action": "NO_TRADE" if primary_blocker else "SAFE_MODE",
        "next_action": "investigate heartbeat blocker" if primary_blocker else "continue read-only monitoring",
        "heartbeat_hash": "",
    }
    heartbeat["heartbeat_hash"] = heartbeat_hash(heartbeat)
    return heartbeat


def validate_heartbeat(
    heartbeat: dict[str, Any],
    allowed_blockers: set[str] | None = None,
    *,
    now: datetime | None = None,
) -> HeartbeatValidationResult:
    if heartbeat.get("schema_id") != HEARTBEAT_SCHEMA_ID:
        return HeartbeatValidationResult("FAIL", "heartbeat schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if heartbeat.get("heartbeat_hash") != heartbeat_hash(heartbeat):
        return HeartbeatValidationResult("FAIL", "heartbeat hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if heartbeat.get("dashboard_truth_only") is not True:
        return HeartbeatValidationResult("FAIL", "heartbeat must remain dashboard serving truth only", "LIVE_FINAL_GUARD_FAILED")
    if heartbeat.get("live_order_ready") or heartbeat.get("live_order_allowed") or heartbeat.get("can_live_trade"):
        return HeartbeatValidationResult("BLOCKED", "heartbeat attempted to create live permission", "LIVE_FINAL_GUARD_FAILED")
    if heartbeat.get("can_trade"):
        return HeartbeatValidationResult("BLOCKED", "heartbeat cannot permit trading", "LIVE_FINAL_GUARD_FAILED")

    components = heartbeat.get("components")
    if not isinstance(components, dict):
        return HeartbeatValidationResult("FAIL", "heartbeat components must be an object", "SCHEMA_IDENTITY_MISMATCH")
    missing_components = sorted(set(HEALTH_COMPONENTS) - set(components))
    if missing_components:
        return HeartbeatValidationResult("BLOCKED", f"heartbeat missing components: {missing_components}", "HARD_TRUTH_MISSING")

    blockers = heartbeat.get("blockers", [])
    if not isinstance(blockers, list):
        return HeartbeatValidationResult("FAIL", "heartbeat blockers must be a list", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return HeartbeatValidationResult("FAIL", f"unknown heartbeat blocker: {code}", "UNKNOWN_BLOCKED")

    stale_after = heartbeat.get("stale_after_seconds")
    age = heartbeat.get("heartbeat_age_seconds")
    if not isinstance(stale_after, int) or stale_after < 1:
        return HeartbeatValidationResult("FAIL", "heartbeat stale_after_seconds is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(age, (int, float)) or age < 0:
        return HeartbeatValidationResult("FAIL", "heartbeat_age_seconds is invalid", "SCHEMA_IDENTITY_MISMATCH")

    generated_at = _parse_utc(heartbeat.get("generated_at_utc"))
    if generated_at is None:
        return HeartbeatValidationResult("FAIL", "heartbeat generated_at_utc is invalid", "SCHEMA_IDENTITY_MISMATCH")
    actual_now = now or datetime.now(timezone.utc)
    generated_age = max(0.0, (actual_now - generated_at).total_seconds())
    is_stale = age > stale_after or generated_age > stale_after
    if is_stale and heartbeat.get("heartbeat_status") == "PASS":
        return HeartbeatValidationResult("BLOCKED", "stale heartbeat cannot remain PASS", "LATENCY_TTL_EXPIRED")
    if is_stale and heartbeat.get("primary_blocker_code") not in {"LATENCY_TTL_EXPIRED", "RESOURCE_LIMIT"}:
        return HeartbeatValidationResult("BLOCKED", "stale heartbeat must expose a blocker", "LATENCY_TTL_EXPIRED")

    bad_components = [
        name
        for name, component in components.items()
        if not isinstance(component, dict) or component.get("status") not in {"PASS", "WARN"}
    ]
    if bad_components and heartbeat.get("heartbeat_status") == "PASS":
        return HeartbeatValidationResult("BLOCKED", "component failure cannot leave heartbeat PASS", "RESOURCE_LIMIT")
    if bad_components and heartbeat.get("primary_blocker_code") is None:
        return HeartbeatValidationResult("BLOCKED", "component failure must expose a blocker", "RESOURCE_LIMIT")

    if heartbeat.get("heartbeat_status") == "PASS" and heartbeat.get("primary_blocker_code") is not None:
        return HeartbeatValidationResult("FAIL", "PASS heartbeat cannot have a primary blocker", "LIVE_FINAL_GUARD_FAILED")
    return HeartbeatValidationResult("PASS", "heartbeat is dashboard-only and fail-closed", None)

