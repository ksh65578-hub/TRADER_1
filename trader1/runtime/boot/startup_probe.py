from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


STARTUP_PROBE_SCHEMA_ID = "trader1.startup_probe.v1"
HARD_TRUTH_FIELDS = (
    "engine_state",
    "mode",
    "exchange",
    "market_type",
    "session_id",
    "config_hash",
    "registry_hash",
    "schema_id",
    "ledger_write_status",
    "startup_probe_phase",
)


@dataclass(frozen=True)
class StartupProbeValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def startup_probe_hash(probe: dict[str, Any]) -> str:
    payload = dict(probe)
    payload.pop("probe_hash", None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def _hard_truth_status(value: Any) -> dict[str, Any]:
    present = value not in {None, ""}
    status = "PASS" if present else "MISSING"
    return {"status": status, "present": present}


def build_startup_probe(
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
    ledger_write_status: str | None = None,
    startup_probe_phase: str = "STARTUP_PROBE_IN_PROGRESS",
    can_start: bool = False,
) -> dict[str, Any]:
    hard_truth_values = {
        "engine_state": engine_state,
        "mode": mode,
        "exchange": exchange,
        "market_type": market_type,
        "session_id": session_id,
        "config_hash": config_hash,
        "registry_hash": registry_hash,
        "schema_id": STARTUP_PROBE_SCHEMA_ID,
        "ledger_write_status": ledger_write_status,
        "startup_probe_phase": startup_probe_phase,
    }
    hard_truth = {field: _hard_truth_status(hard_truth_values.get(field)) for field in HARD_TRUTH_FIELDS}
    missing = [field for field, result in hard_truth.items() if result["status"] != "PASS"]
    startup_probe_passed = not missing and can_start
    primary_blocker = None if startup_probe_passed else "HARD_TRUTH_MISSING"
    phase = "PASS" if startup_probe_passed else "STARTUP_PROBE_GATE_BLOCKED"
    probe = {
        "schema_id": STARTUP_PROBE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "config_hash": config_hash,
        "registry_hash": registry_hash,
        "schema_bundle_hash": schema_bundle_hash,
        "source_tree_hash": source_tree_hash,
        "engine_state_before": engine_state,
        "engine_state_after_probe": "BOOTSTRAP_READ_ONLY" if startup_probe_passed else "SAFE_MODE",
        "startup_probe_phase": phase,
        "startup_probe_passed": startup_probe_passed,
        "can_start": startup_probe_passed,
        "can_run_engine": startup_probe_passed,
        "can_trade": False,
        "can_live_trade": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "dashboard_truth_only": True,
        "hard_truth": hard_truth,
        "missing_hard_truth": missing,
        "primary_blocker_code": primary_blocker,
        "blockers": [] if primary_blocker is None else [{"code": primary_blocker, "severity": "HIGH", "message": "hard truth missing blocks startup"}],
        "final_action": "NO_TRADE" if primary_blocker else "SAFE_MODE",
        "next_action": "provide missing hard truth and rerun startup probe" if primary_blocker else "continue read-only boot",
        "probe_hash": "",
    }
    probe["probe_hash"] = startup_probe_hash(probe)
    return probe


def validate_startup_probe(probe: dict[str, Any], allowed_blockers: set[str] | None = None) -> StartupProbeValidationResult:
    if probe.get("schema_id") != STARTUP_PROBE_SCHEMA_ID:
        return StartupProbeValidationResult("FAIL", "startup_probe schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if probe.get("probe_hash") != startup_probe_hash(probe):
        return StartupProbeValidationResult("FAIL", "startup_probe hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if probe.get("dashboard_truth_only") is not True:
        return StartupProbeValidationResult("FAIL", "startup_probe must remain dashboard serving truth only", "LIVE_FINAL_GUARD_FAILED")
    if probe.get("live_order_ready") or probe.get("live_order_allowed") or probe.get("can_live_trade"):
        return StartupProbeValidationResult("BLOCKED", "startup_probe attempted to create live permission", "LIVE_FINAL_GUARD_FAILED")
    if probe.get("can_trade"):
        return StartupProbeValidationResult("BLOCKED", "startup_probe PASS is not sufficient for trading", "LIVE_FINAL_GUARD_FAILED")

    blockers = probe.get("blockers", [])
    if not isinstance(blockers, list):
        return StartupProbeValidationResult("FAIL", "startup_probe blockers must be a list", "SCHEMA_IDENTITY_MISMATCH")
    for blocker in blockers:
        code = blocker.get("code") if isinstance(blocker, dict) else None
        if allowed_blockers is not None and code not in allowed_blockers:
            return StartupProbeValidationResult("FAIL", f"unknown startup blocker: {code}", "UNKNOWN_BLOCKED")

    missing = probe.get("missing_hard_truth", [])
    if missing and probe.get("startup_probe_passed"):
        return StartupProbeValidationResult("BLOCKED", "startup_probe passed while hard truth is missing", "HARD_TRUTH_MISSING")
    if missing and probe.get("primary_blocker_code") != "HARD_TRUTH_MISSING":
        return StartupProbeValidationResult("BLOCKED", "missing hard truth must expose HARD_TRUTH_MISSING", "HARD_TRUTH_MISSING")
    if not probe.get("startup_probe_passed") and probe.get("engine_state_after_probe") == "RUNNING":
        return StartupProbeValidationResult("BLOCKED", "RUNNING before startup_probe PASS is forbidden", "PREFLIGHT_FAILED")
    if probe.get("startup_probe_passed") and probe.get("engine_state_after_probe") == "RUNNING":
        return StartupProbeValidationResult("BLOCKED", "startup_probe alone cannot move engine to RUNNING", "PREFLIGHT_FAILED")
    return StartupProbeValidationResult("PASS", "startup_probe is fail-closed", None)
