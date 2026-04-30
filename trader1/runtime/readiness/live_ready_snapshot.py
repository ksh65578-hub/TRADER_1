from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


LIVE_READY_SNAPSHOT_SCHEMA_ID = "trader1.live_ready_snapshot.v1"
WRITER_INPUT_SCHEMA_ID = "trader1.live_ready_candidate_writer_input.v1"
VALID_WRITER_INPUT_TYPE = "LIVE_READY_CANDIDATE_WRITER_INPUT"
WRITER_PASS_STATUS = {"PASS", "SKIPPED_NOT_APPLICABLE"}
FRESH_BLOCKING_STATUSES = {"FAIL", "BLOCKED", "UNTESTED", "STALE", "TIMEOUT"}
PLACEHOLDER_MARKERS = ("placeholder", "unverified", "mvp0-blocked", "example.invalid")

WRITER_REQUIRED_FIELDS = frozenset(
    {
        "schema_id",
        "writer_input_id",
        "created_at_utc",
        "promotion_input_type",
        "exchange",
        "market_type",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "risk_profile",
        "timeframe_scope",
        "regime_scope",
        "registry_hash",
        "schema_bundle_hash",
        "source_tree_hash",
        "promotion_threshold_status",
        "paper_live_parity_status",
        "execution_quality_status",
        "cost_after_edge_status",
        "evidence_manifest_hash",
        "validator_results_fresh",
        "high_contract_gap_count",
        "critical_contract_gap_count",
        "manual_or_operator_requirements_preserved",
        "live_ready_snapshot_writer_status",
        "blockers",
        "writer_input_hash",
    }
)


@dataclass(frozen=True)
class SnapshotValidationResult:
    status: str
    message: str
    blocker_code: str | None = None
    live_order_ready: bool = False
    live_order_allowed: bool = False
    can_live_trade: bool = False


@dataclass(frozen=True)
class SnapshotWriterResult:
    status: str
    message: str
    blocker_code: str
    would_write_snapshot: bool = False
    snapshot: dict[str, Any] | None = None
    blockers: list[str] = field(default_factory=list)
    live_order_ready: bool = False
    live_order_allowed: bool = False
    can_live_trade: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def writer_input_hash(writer_input: dict[str, Any]) -> str:
    payload = dict(writer_input)
    payload.pop("writer_input_hash", None)
    return _sha256_json(payload)


def attach_writer_input_hash(writer_input: dict[str, Any]) -> dict[str, Any]:
    payload = dict(writer_input)
    payload["writer_input_hash"] = writer_input_hash(payload)
    return payload


def _is_placeholder_value(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def _placeholder_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if _is_placeholder_value(payload.get(field))]


def blocked_writer_result(message: str, blocker_code: str, blockers: list[str] | None = None) -> SnapshotWriterResult:
    return SnapshotWriterResult(
        status="BLOCKED",
        message=message,
        blocker_code=blocker_code,
        blockers=blockers or [blocker_code],
    )


def build_writer_input(
    *,
    authority: dict[str, str],
    exchange: str,
    market_type: str,
    strategy_id: str,
    strategy_build_id: str,
    parameter_hash: str,
    risk_profile: str,
    registry_hash: str,
    schema_bundle_hash: str,
    source_tree_hash: str,
    writer_input_id: str = "mvp0_writer_input",
    timeframe_scope: str = "15m",
    regime_scope: str | None = None,
) -> dict[str, Any]:
    del authority  # writer input identity is source-hash verified by surrounding evidence manifests.
    writer_input = {
        "schema_id": WRITER_INPUT_SCHEMA_ID,
        "writer_input_id": writer_input_id,
        "created_at_utc": utc_now(),
        "promotion_input_type": VALID_WRITER_INPUT_TYPE,
        "exchange": exchange,
        "market_type": market_type,
        "strategy_id": strategy_id,
        "strategy_build_id": strategy_build_id,
        "parameter_hash": parameter_hash,
        "risk_profile": risk_profile,
        "timeframe_scope": timeframe_scope,
        "regime_scope": regime_scope,
        "registry_hash": registry_hash,
        "schema_bundle_hash": schema_bundle_hash,
        "source_tree_hash": source_tree_hash,
        "promotion_threshold_status": "PASS",
        "paper_live_parity_status": "SKIPPED_NOT_APPLICABLE",
        "execution_quality_status": "PASS",
        "cost_after_edge_status": "PASS",
        "evidence_manifest_hash": "mvp0-evidence-placeholder",
        "validator_results_fresh": True,
        "high_contract_gap_count": 0,
        "critical_contract_gap_count": 0,
        "manual_or_operator_requirements_preserved": True,
        "live_ready_snapshot_writer_status": "UNTESTED",
        "blockers": ["LIVE_READY_SNAPSHOT_WRITER_UNTESTED"],
        "writer_input_hash": "",
    }
    return attach_writer_input_hash(writer_input)


def evaluate_live_ready_snapshot_writer(
    writer_input: dict[str, Any],
    *,
    expected_scope: dict[str, str] | None = None,
    evidence_manifest_present: bool = False,
    allow_snapshot_write: bool = False,
) -> SnapshotWriterResult:
    if writer_input.get("schema_id") == LIVE_READY_SNAPSHOT_SCHEMA_ID:
        return blocked_writer_result("LIVE_READY snapshot was provided where writer input is required", "SNAPSHOT_WRITER_INPUT_NOT_SNAPSHOT")
    if writer_input.get("schema_id") != WRITER_INPUT_SCHEMA_ID:
        return blocked_writer_result("writer input schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")

    missing = sorted(WRITER_REQUIRED_FIELDS - set(writer_input))
    if missing:
        return blocked_writer_result(f"writer input missing required fields: {missing}", "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    if writer_input.get("writer_input_hash") != writer_input_hash(writer_input):
        return blocked_writer_result("writer input hash mismatch", "SCHEMA_IDENTITY_MISMATCH")

    if writer_input.get("promotion_input_type") != VALID_WRITER_INPUT_TYPE:
        return blocked_writer_result("writer input promotion_input_type is not LIVE_READY_CANDIDATE_WRITER_INPUT", "PROMOTION_INPUT_TYPE_INVALID")

    if writer_input.get("live_ready_snapshot_writer_status") in FRESH_BLOCKING_STATUSES:
        return blocked_writer_result(
            f"writer status is not PASS: {writer_input.get('live_ready_snapshot_writer_status')}",
            "LIVE_READY_SNAPSHOT_WRITER_UNTESTED"
            if writer_input.get("live_ready_snapshot_writer_status") in {"UNTESTED", "STALE", "TIMEOUT"}
            else "LIVE_READY_SNAPSHOT_WRITER_FAILED",
        )

    if writer_input.get("blockers"):
        return blocked_writer_result("writer input carries blockers and cannot become a snapshot", "LIVE_READY_SNAPSHOT_WRITER_FAILED", list(writer_input["blockers"]))

    if writer_input.get("promotion_threshold_status") != "PASS":
        return blocked_writer_result("promotion threshold status is not PASS", "PROMOTION_INPUT_TYPE_INVALID")
    if writer_input.get("paper_live_parity_status") not in WRITER_PASS_STATUS:
        return blocked_writer_result("paper/live parity status is not PASS or SKIPPED_NOT_APPLICABLE", "LIVE_READY_SNAPSHOT_WRITER_FAILED")
    if writer_input.get("execution_quality_status") != "PASS":
        return blocked_writer_result("execution quality status is not PASS", "EXECUTION_QUALITY_UNTESTED")
    if writer_input.get("cost_after_edge_status") != "PASS":
        return blocked_writer_result("cost-after-edge status is not PASS", "COST_AFTER_EDGE_UNVERIFIED")
    placeholder_fields = _placeholder_fields(
        writer_input,
        ("registry_hash", "schema_bundle_hash", "source_tree_hash", "evidence_manifest_hash"),
    )
    if placeholder_fields:
        return blocked_writer_result(
            f"writer input contains placeholder or unverified evidence fields: {placeholder_fields}",
            "LIVE_READY_SNAPSHOT_WRITER_FAILED",
        )
    if not writer_input.get("evidence_manifest_hash") or not evidence_manifest_present:
        return blocked_writer_result("fresh evidence manifest is required before snapshot write", "LIVE_READY_SNAPSHOT_WRITER_FAILED")
    if writer_input.get("validator_results_fresh") is not True:
        return blocked_writer_result("validator results are missing, stale, or untested", "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")
    if writer_input.get("high_contract_gap_count") != 0:
        return blocked_writer_result("HIGH contract gaps remain open", "CONTRACT_GAP_HIGH")
    if writer_input.get("critical_contract_gap_count") != 0:
        return blocked_writer_result("CRITICAL contract gaps remain open", "CONTRACT_GAP_CRITICAL")
    if writer_input.get("manual_or_operator_requirements_preserved") is not True:
        return blocked_writer_result("manual or operator requirements were not preserved", "OPERATOR_APPROVAL_MISSING")

    if expected_scope:
        for key in ("exchange", "market_type", "strategy_id", "risk_profile", "parameter_hash"):
            expected = expected_scope.get(key)
            if expected is not None and writer_input.get(key) != expected:
                return blocked_writer_result(f"writer input scope mismatch for {key}", "SNAPSHOT_SCOPE_MISMATCH")

    if not allow_snapshot_write:
        return blocked_writer_result("snapshot write remains disabled outside LIVE_ENABLING_PATCH", "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")

    return blocked_writer_result("LIVE_READY snapshot creation is not enabled by this MVP-0 implementation", "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")


def build_blocked_live_ready_snapshot(
    *,
    exchange: str,
    market_type: str,
    registry_hash: str,
    schema_bundle_hash: str,
    source_tree_hash: str,
    snapshot_id: str = "mvp0_blocked_snapshot",
) -> dict[str, Any]:
    return {
        "schema_id": LIVE_READY_SNAPSHOT_SCHEMA_ID,
        "snapshot_id": snapshot_id,
        "created_at_utc": utc_now(),
        "expires_at_utc": utc_now(),
        "exchange": exchange,
        "market_type": market_type,
        "mode_source": "PAPER",
        "strategy_id": "mvp0_strategy",
        "strategy_build_id": "mvp0_build",
        "parameter_hash": "mvp0_parameter_hash",
        "risk_profile": "CONSERVATIVE",
        "build_id": "mvp0_build",
        "source_tree_hash": source_tree_hash,
        "registry_hash": registry_hash,
        "schema_bundle_hash": schema_bundle_hash,
        "validation_results": {
            "validator_rollup_status": "UNTESTED",
            "validator_result_ids": [],
            "passed_validator_ids": [],
            "failed_validator_ids": [],
            "blocked_validator_ids": ["live_ready_snapshot_writer_validator"],
            "untested_validator_ids": ["live_ready_snapshot_writer_validator"],
            "stale_validator_ids": [],
        },
        "performance_summary": {},
        "risk_limits": {},
        "sizing_limits": {},
        "manual_order_test_required": True,
        "manual_order_test_id": None,
        "operator_approval_required": True,
        "operator_approval_id": None,
        "official_api_verification_id": None,
        "read_only_burn_in_id": None,
        "emergency_protection_evidence_id": None,
        "live_ready": False,
        "live_order_allowed": False,
        "invalidated_by": ["LIVE_READY_SNAPSHOT_WRITER_UNTESTED"],
        "validator_rollup_status": "UNTESTED",
        "manifest_hash": "mvp0-blocked-manifest",
    }


def validate_live_ready_snapshot(snapshot: dict[str, Any]) -> SnapshotValidationResult:
    if snapshot.get("schema_id") != LIVE_READY_SNAPSHOT_SCHEMA_ID:
        return SnapshotValidationResult("FAIL", "live_ready_snapshot schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    required = {
        "snapshot_id",
        "created_at_utc",
        "expires_at_utc",
        "exchange",
        "market_type",
        "mode_source",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "risk_profile",
        "build_id",
        "source_tree_hash",
        "registry_hash",
        "schema_bundle_hash",
        "validation_results",
        "performance_summary",
        "risk_limits",
        "sizing_limits",
        "manual_order_test_required",
        "operator_approval_required",
        "live_ready",
        "live_order_allowed",
        "invalidated_by",
        "validator_rollup_status",
        "manifest_hash",
    }
    missing = sorted(required - set(snapshot))
    if missing:
        return SnapshotValidationResult("BLOCKED", f"live_ready_snapshot missing fields: {missing}", "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    if snapshot.get("live_order_allowed") is True and snapshot.get("live_ready") is not True:
        return SnapshotValidationResult("BLOCKED", "live_order_allowed requires live_ready=true", "LIVE_FINAL_GUARD_FAILED")

    if snapshot.get("live_ready") is True:
        if not snapshot.get("official_api_verification_id"):
            return SnapshotValidationResult("BLOCKED", "live_ready requires official API verification", "API_UNVERIFIED")
        if snapshot.get("manual_order_test_required") is True and not snapshot.get("manual_order_test_id"):
            return SnapshotValidationResult("BLOCKED", "live_ready requires manual order test evidence", "MANUAL_ORDER_TEST_MISSING")
        if snapshot.get("operator_approval_required") is True and not snapshot.get("operator_approval_id"):
            return SnapshotValidationResult("BLOCKED", "live_ready requires operator approval evidence", "OPERATOR_APPROVAL_MISSING")
        if not snapshot.get("read_only_burn_in_id"):
            return SnapshotValidationResult("BLOCKED", "live_ready requires read-only burn-in evidence", "READ_ONLY_BURN_IN_MISSING")
        if not snapshot.get("emergency_protection_evidence_id"):
            return SnapshotValidationResult("BLOCKED", "live_ready requires emergency protection evidence", "EMERGENCY_FLATTEN_UNAVAILABLE")
        placeholder_fields = _placeholder_fields(
            snapshot,
            (
                "official_api_verification_id",
                "manual_order_test_id",
                "operator_approval_id",
                "read_only_burn_in_id",
                "emergency_protection_evidence_id",
                "manifest_hash",
                "registry_hash",
                "schema_bundle_hash",
                "source_tree_hash",
            ),
        )
        if placeholder_fields:
            return SnapshotValidationResult(
                "BLOCKED",
                f"live_ready snapshot contains placeholder or unverified evidence fields: {placeholder_fields}",
                "LIVE_READY_SNAPSHOT_WRITER_FAILED",
            )
        if snapshot.get("validator_rollup_status") != "PASS":
            return SnapshotValidationResult("BLOCKED", "validator rollup must be PASS for live_ready", "LIVE_READY_SNAPSHOT_WRITER_FAILED")
        if snapshot.get("invalidated_by"):
            return SnapshotValidationResult("BLOCKED", "invalidated snapshot cannot claim live_ready", "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    return SnapshotValidationResult(
        "PASS",
        "live_ready_snapshot is fail-closed",
        None,
        live_order_ready=bool(snapshot.get("live_ready")),
        live_order_allowed=bool(snapshot.get("live_order_allowed")),
        can_live_trade=False,
    )
