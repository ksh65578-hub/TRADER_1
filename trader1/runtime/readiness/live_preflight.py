from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.adapters.upbit.account_readonly import (
    build_read_only_account_snapshot,
    validate_read_only_account_snapshot,
)
from trader1.adapters.upbit.private_stream import build_private_stream_health, validate_private_stream_health
from trader1.adapters.upbit.reconciliation import (
    build_upbit_read_only_reconciliation_path,
    validate_upbit_read_only_reconciliation_path,
)
from trader1.runtime.readiness.live_ready_snapshot import (
    build_blocked_live_ready_snapshot,
    validate_live_ready_snapshot,
)
from trader1.runtime.readiness.official_api_verification import (
    build_official_api_verification_report,
    validate_official_api_verification_report,
)
from trader1.runtime.readiness.readiness_surface import build_readiness_surface, blocker_object
from trader1.security.api_key_permission_check import (
    build_api_key_permission_check_report,
    validate_api_key_permission_check_report,
)


LIVE_PREFLIGHT_SCHEMA_ID = "trader1.live_preflight_report.v1"
BLOCKER_PRIORITY = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "OFFICIAL_API_VERIFICATION_EXPIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "RECONCILIATION_REQUIRED",
    "PRIVATE_WS_UNHEALTHY",
    "HARD_TRUTH_MISSING",
    "PREFLIGHT_FAILED",
    "LIVE_FINAL_GUARD_FAILED",
]


@dataclass(frozen=True)
class LivePreflightValidationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def live_preflight_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("preflight_hash", None)
    return _sha256_json(payload)


def _add_code(codes: list[str], code: str | None) -> None:
    if code and code not in codes:
        codes.append(code)


def _sort_codes(codes: list[str]) -> list[str]:
    priority = {code: index for index, code in enumerate(BLOCKER_PRIORITY)}
    return sorted(codes, key=lambda code: (priority.get(code, len(priority)), code))


def build_upbit_live_review_preflight(
    *,
    authority: dict[str, str],
    preflight_id: str = "mvp4-upbit-live-review-preflight",
    session_id: str = "mvp4_upbit_live_review",
    registry_hash: str | None = None,
    schema_bundle_hash: str | None = None,
    source_tree_hash: str | None = None,
    official_api_verification_report: dict[str, Any] | None = None,
    account_snapshot: dict[str, Any] | None = None,
    private_stream_health: dict[str, Any] | None = None,
    reconciliation_path: dict[str, Any] | None = None,
    api_key_permission_check: dict[str, Any] | None = None,
    manual_order_test_status: str = "MISSING",
    operator_approval_status: str = "MISSING",
    read_only_burn_in_status: str = "MISSING",
) -> dict[str, Any]:
    official_api = official_api_verification_report or build_official_api_verification_report(authority=authority)
    account = account_snapshot or build_read_only_account_snapshot(authority=authority, session_id=session_id)
    stream = private_stream_health or build_private_stream_health(authority=authority, session_id=session_id)
    reconciliation = reconciliation_path or build_upbit_read_only_reconciliation_path(
        authority=authority,
        session_id=session_id,
        account_snapshot_id=account["snapshot_id"],
        private_stream_health_id=stream["stream_health_id"],
    )
    permission_check = api_key_permission_check or build_api_key_permission_check_report(authority=authority)

    codes: list[str] = ["LIVE_READY_MISSING"]
    component_results = [
        validate_official_api_verification_report(official_api),
        validate_read_only_account_snapshot(account),
        validate_private_stream_health(stream),
        validate_upbit_read_only_reconciliation_path(reconciliation),
        validate_api_key_permission_check_report(permission_check),
    ]
    for result in component_results:
        if result.status != "PASS":
            _add_code(codes, result.blocker_code)
    if manual_order_test_status != "PASS":
        _add_code(codes, "MANUAL_ORDER_TEST_MISSING")
    if operator_approval_status != "APPROVED":
        _add_code(codes, "OPERATOR_APPROVAL_MISSING")
    if read_only_burn_in_status != "PASS":
        _add_code(codes, "READ_ONLY_BURN_IN_MISSING")

    blocked_snapshot = build_blocked_live_ready_snapshot(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        registry_hash=registry_hash or "registry-hash-unverified",
        schema_bundle_hash=schema_bundle_hash or "schema-bundle-hash-unverified",
        source_tree_hash=source_tree_hash or "source-tree-hash-unverified",
        snapshot_id="mvp4-blocked-live-ready-snapshot-review",
    )
    snapshot_result = validate_live_ready_snapshot(blocked_snapshot)
    if not snapshot_result.live_order_ready:
        _add_code(codes, "LIVE_READY_MISSING")

    sorted_codes = _sort_codes(codes)
    blockers = [blocker_object(code, source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD") for code in sorted_codes]
    readiness_surface = build_readiness_surface(
        authority=authority,
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="LIVE",
        session_id=session_id,
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        can_start=True,
        can_collect_data=True,
        can_live_review=True,
        blocker_codes=sorted_codes,
    )
    report = {
        "schema_id": LIVE_PREFLIGHT_SCHEMA_ID,
        "preflight_id": preflight_id,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "LIVE",
        "session_id": session_id,
        "can_live_review": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "live_new_order_blocked": True,
        "official_api_verification_report": official_api,
        "account_snapshot": account,
        "private_stream_health": stream,
        "reconciliation_path": reconciliation,
        "api_key_permission_check": permission_check,
        "readiness_surface": readiness_surface,
        "manual_order_test_status": manual_order_test_status,
        "operator_approval_status": operator_approval_status,
        "read_only_burn_in_status": read_only_burn_in_status,
        "preflight_status": "BLOCKED",
        "primary_blocker_code": sorted_codes[0],
        "blockers": blockers,
        "preflight_hash": "",
    }
    report["preflight_hash"] = live_preflight_hash(report)
    return report


def validate_live_preflight_report(report: dict[str, Any]) -> LivePreflightValidationResult:
    if report.get("schema_id") != LIVE_PREFLIGHT_SCHEMA_ID:
        return LivePreflightValidationResult("FAIL", "live preflight schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("preflight_hash") != live_preflight_hash(report):
        return LivePreflightValidationResult("FAIL", "live preflight hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "LIVE":
        return LivePreflightValidationResult("BLOCKED", "live preflight scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "order_adapter_called")
    if any(report.get(field) is True for field in forbidden):
        return LivePreflightValidationResult("BLOCKED", "live preflight attempted to create trading permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("live_new_order_blocked") is not True:
        return LivePreflightValidationResult("BLOCKED", "live preflight must block live new orders", "LIVE_FINAL_GUARD_FAILED")
    if report.get("can_live_review") is not True:
        return LivePreflightValidationResult("BLOCKED", "MVP-4 preflight must expose review-only status", "PREFLIGHT_FAILED")
    if report.get("preflight_status") != "BLOCKED":
        return LivePreflightValidationResult("BLOCKED", "MVP-4 preflight status must remain BLOCKED", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers")
    if not isinstance(blockers, list) or not blockers:
        return LivePreflightValidationResult("BLOCKED", "non-live MVP-4 preflight must carry blockers", "LIVE_FINAL_GUARD_FAILED")
    blocker_codes = [blocker.get("code") for blocker in blockers if isinstance(blocker, dict)]
    if report.get("primary_blocker_code") not in blocker_codes:
        return LivePreflightValidationResult("BLOCKED", "primary blocker must be present in preflight blockers", "LIVE_FINAL_GUARD_FAILED")
    if "LIVE_READY_MISSING" not in blocker_codes:
        return LivePreflightValidationResult("BLOCKED", "MVP-4 preflight cannot omit LIVE_READY blocker", "LIVE_READY_MISSING")

    component_checks = [
        validate_official_api_verification_report(report.get("official_api_verification_report", {})),
        validate_read_only_account_snapshot(report.get("account_snapshot", {})),
        validate_private_stream_health(report.get("private_stream_health", {})),
        validate_upbit_read_only_reconciliation_path(report.get("reconciliation_path", {})),
        validate_api_key_permission_check_report(report.get("api_key_permission_check", {})),
    ]
    component_blockers = {result.blocker_code for result in component_checks if result.status != "PASS"}
    expected_component_blockers = {code for code in component_blockers if code}
    if not expected_component_blockers.issubset(set(blocker_codes)):
        return LivePreflightValidationResult("BLOCKED", "live preflight omitted a component blocker", "PREFLIGHT_FAILED")

    if report.get("manual_order_test_status") != "PASS" and "MANUAL_ORDER_TEST_MISSING" not in blocker_codes:
        return LivePreflightValidationResult("BLOCKED", "manual order test missing was not surfaced", "MANUAL_ORDER_TEST_MISSING")
    if report.get("operator_approval_status") != "APPROVED" and "OPERATOR_APPROVAL_MISSING" not in blocker_codes:
        return LivePreflightValidationResult("BLOCKED", "operator approval missing was not surfaced", "OPERATOR_APPROVAL_MISSING")
    if report.get("read_only_burn_in_status") != "PASS" and "READ_ONLY_BURN_IN_MISSING" not in blocker_codes:
        return LivePreflightValidationResult("BLOCKED", "read-only burn-in missing was not surfaced", "READ_ONLY_BURN_IN_MISSING")

    surface = report.get("readiness_surface", {})
    if (
        surface.get("can_live_review") is not True
        or surface.get("live_order_ready") is not False
        or surface.get("live_order_allowed") is not False
        or surface.get("can_live_trade") is not False
        or surface.get("live_trading_status") != "BLOCKED"
    ):
        return LivePreflightValidationResult("BLOCKED", "readiness surface must be review-only and live-blocked", "LIVE_FINAL_GUARD_FAILED")
    if surface.get("primary_blocker_code") != report.get("primary_blocker_code"):
        return LivePreflightValidationResult("BLOCKED", "readiness surface blocker must match preflight truth", "LIVE_FINAL_GUARD_FAILED")
    return LivePreflightValidationResult("PASS", "Upbit live review preflight is review-only and live-blocked")
