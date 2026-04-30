"""Runtime artifact hygiene helpers for dashboard truth separation.

The helpers in this module classify dashboard shell artifacts without deleting
legacy files. Legacy artifacts are retained for audit, but they must not become
execution truth or dashboard-serving truth.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ID = "trader1.runtime_dashboard_artifact_hygiene_report.v1"
PROJECT_ID = "TRADER_1"

ACTIVE_DASHBOARD_SHELLS = {
    "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
}

MODE_SEGMENTS = {"paper", "live", "shadow", "replay"}


@dataclass(frozen=True)
class RuntimeDashboardArtifactHygieneValidation:
    status: str
    message: str
    blocking_reasons: tuple[str, ...]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest().upper()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _load_json(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except Exception as exc:  # pragma: no cover - exact exception is platform dependent.
        return {}, f"{type(exc).__name__}: {exc}"
    if not isinstance(value, dict):
        return {}, "JSON root is not an object"
    return value, None


def _bool_true(payload: dict[str, Any], key: str) -> bool:
    return payload.get(key) is True


def _runtime_requirement_count(payload: dict[str, Any]) -> int:
    boundary = payload.get("runtime_evidence_boundary")
    if not isinstance(boundary, dict):
        return 0
    requirements = boundary.get("evidence_requirements")
    if not isinstance(requirements, list):
        return 0
    return len(requirements)


def _freshness_status(payload: dict[str, Any]) -> str:
    freshness = payload.get("freshness")
    if isinstance(freshness, dict):
        status = freshness.get("status")
        if isinstance(status, str) and status:
            return status
    return "UNKNOWN"


def _base_item(path: Path, root: Path, payload: dict[str, Any], load_error: str | None) -> dict[str, Any]:
    return {
        "artifact_path": _relative(path, root),
        "load_status": "FAIL" if load_error else "PASS",
        "load_error": load_error or "",
        "schema_id": str(payload.get("schema_id", "")),
        "exchange": str(payload.get("exchange", "")),
        "market_type": str(payload.get("market_type", "")),
        "mode": str(payload.get("mode", "")),
        "session_id": str(payload.get("session_id", "")),
        "freshness_status": _freshness_status(payload),
        "runtime_evidence_requirement_count": _runtime_requirement_count(payload),
        "live_order_ready": _bool_true(payload, "live_order_ready"),
        "live_order_allowed": _bool_true(payload, "live_order_allowed"),
        "can_live_trade": _bool_true(payload, "can_live_trade"),
        "scale_up_allowed": _bool_true(payload, "scale_up_allowed"),
    }


def _is_unscoped_mode_dashboard(path: Path) -> bool:
    return path.name == "dashboard_shell.json" and path.parent.name.lower() in MODE_SEGMENTS


def build_runtime_dashboard_artifact_hygiene_report(
    root: Path | str = ROOT,
    active_dashboard_shells: Iterable[str] | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    active_set = set(active_dashboard_shells or ACTIVE_DASHBOARD_SHELLS)
    runtime_root = root_path / "system" / "runtime"
    active_items: list[dict[str, Any]] = []
    legacy_items: list[dict[str, Any]] = []
    unknown_items: list[dict[str, Any]] = []

    dashboard_paths = sorted(runtime_root.glob("**/dashboard_shell.json")) if runtime_root.exists() else []
    for path in dashboard_paths:
        payload, load_error = _load_json(path)
        item = _base_item(path, root_path, payload, load_error)
        rel_path = item["artifact_path"]
        if rel_path in active_set:
            item.update(
                {
                    "classification": "ACTIVE_SESSION_SCOPED",
                    "session_scoped": True,
                    "execution_authority": False,
                    "dashboard_serving_truth": True,
                    "operator_action": "Use this session-scoped launcher dashboard for display only.",
                    "reason": "recognized session-scoped launcher dashboard shell",
                }
            )
            active_items.append(item)
        elif _is_unscoped_mode_dashboard(path):
            item.update(
                {
                    "classification": "LEGACY_UNSESSIONED_RETAINED",
                    "session_scoped": False,
                    "execution_authority": False,
                    "dashboard_serving_truth": False,
                    "operator_action": "Open the session-scoped launcher dashboard instead.",
                    "reason": "path omits session_id segment and is retained only for audit continuity",
                }
            )
            legacy_items.append(item)
        else:
            item.update(
                {
                    "classification": "UNKNOWN_RUNTIME_DASHBOARD_SHELL",
                    "session_scoped": False,
                    "execution_authority": False,
                    "dashboard_serving_truth": False,
                    "operator_action": "Block dashboard serving until artifact ownership is classified.",
                    "reason": "dashboard shell path is not recognized by active launcher scope rules",
                }
            )
            unknown_items.append(item)

    active_unsafe = [
        item["artifact_path"]
        for item in active_items
        if item["load_status"] != "PASS"
        or item["runtime_evidence_requirement_count"] < 8
        or item["live_order_ready"]
        or item["live_order_allowed"]
        or item["can_live_trade"]
        or item["scale_up_allowed"]
    ]
    legacy_unsafe = [
        item["artifact_path"]
        for item in legacy_items
        if item["load_status"] != "PASS"
        or item["execution_authority"]
        or item["dashboard_serving_truth"]
        or item["live_order_ready"]
        or item["live_order_allowed"]
        or item["can_live_trade"]
        or item["scale_up_allowed"]
    ]
    unknown_unsafe = [item["artifact_path"] for item in unknown_items]
    blocking_reasons: list[str] = []
    if active_unsafe:
        blocking_reasons.append("ACTIVE_DASHBOARD_SHELL_UNSAFE_OR_INCOMPLETE")
    if legacy_unsafe:
        blocking_reasons.append("LEGACY_DASHBOARD_SHELL_NOT_SAFE_TO_RETAIN")
    if unknown_unsafe:
        blocking_reasons.append("UNKNOWN_DASHBOARD_SHELL_ARTIFACT")

    status = "BLOCKED" if blocking_reasons else ("PASS_WITH_LEGACY_RETAINED" if legacy_items else "PASS")
    report: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "generated_at_utc": _utc_now(),
        "project_id": PROJECT_ID,
        "authority": {
            "trader1_sha256": _sha256_file(root_path / "TRADER_1.md"),
            "agents_sha256": _sha256_file(root_path / "AGENTS.md"),
        },
        "scan_root": str(runtime_root),
        "active_session_dashboard_shells": active_items,
        "legacy_retained_dashboard_shells": legacy_items,
        "unknown_dashboard_shells": unknown_items,
        "active_count": len(active_items),
        "legacy_retained_count": len(legacy_items),
        "unknown_count": len(unknown_items),
        "active_unsafe_paths": active_unsafe,
        "legacy_unsafe_paths": legacy_unsafe,
        "unknown_unsafe_paths": unknown_unsafe,
        "blocking_reasons": blocking_reasons,
        "status": status,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    report["report_hash"] = _hash_payload({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_runtime_dashboard_artifact_hygiene_report(
    report: dict[str, Any],
) -> RuntimeDashboardArtifactHygieneValidation:
    reasons: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        reasons.append("SCHEMA_ID_MISMATCH")

    expected_hash = _hash_payload({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        reasons.append("REPORT_HASH_MISMATCH")

    if report.get("live_order_ready") is not False:
        reasons.append("LIVE_ORDER_READY_NOT_FALSE")
    if report.get("live_order_allowed") is not False:
        reasons.append("LIVE_ORDER_ALLOWED_NOT_FALSE")
    if report.get("can_live_trade") is not False:
        reasons.append("CAN_LIVE_TRADE_NOT_FALSE")
    if report.get("scale_up_allowed") is not False:
        reasons.append("SCALE_UP_ALLOWED_NOT_FALSE")

    active_items = report.get("active_session_dashboard_shells")
    legacy_items = report.get("legacy_retained_dashboard_shells")
    unknown_items = report.get("unknown_dashboard_shells")
    if not isinstance(active_items, list):
        reasons.append("ACTIVE_ITEMS_NOT_LIST")
        active_items = []
    if not isinstance(legacy_items, list):
        reasons.append("LEGACY_ITEMS_NOT_LIST")
        legacy_items = []
    if not isinstance(unknown_items, list):
        reasons.append("UNKNOWN_ITEMS_NOT_LIST")
        unknown_items = []

    if report.get("active_count") != len(active_items):
        reasons.append("ACTIVE_COUNT_MISMATCH")
    if report.get("legacy_retained_count") != len(legacy_items):
        reasons.append("LEGACY_COUNT_MISMATCH")
    if report.get("unknown_count") != len(unknown_items):
        reasons.append("UNKNOWN_COUNT_MISMATCH")

    for item in active_items:
        if not isinstance(item, dict):
            reasons.append("ACTIVE_ITEM_NOT_OBJECT")
            continue
        if item.get("classification") != "ACTIVE_SESSION_SCOPED":
            reasons.append("ACTIVE_ITEM_CLASSIFICATION_INVALID")
        if item.get("session_scoped") is not True:
            reasons.append("ACTIVE_ITEM_NOT_SESSION_SCOPED")
        if item.get("dashboard_serving_truth") is not True:
            reasons.append("ACTIVE_ITEM_NOT_DASHBOARD_SERVING_TRUTH")
        if item.get("execution_authority") is not False:
            reasons.append("ACTIVE_ITEM_EXECUTION_AUTHORITY_TRUE")
        if item.get("runtime_evidence_requirement_count", 0) < 8:
            reasons.append("ACTIVE_ITEM_RUNTIME_REQUIREMENTS_INCOMPLETE")
        for key in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if item.get(key) is not False:
                reasons.append(f"ACTIVE_ITEM_{key.upper()}_NOT_FALSE")

    for item in legacy_items:
        if not isinstance(item, dict):
            reasons.append("LEGACY_ITEM_NOT_OBJECT")
            continue
        if item.get("classification") != "LEGACY_UNSESSIONED_RETAINED":
            reasons.append("LEGACY_ITEM_CLASSIFICATION_INVALID")
        if item.get("session_scoped") is not False:
            reasons.append("LEGACY_ITEM_SESSION_SCOPED_TRUE")
        if item.get("execution_authority") is not False:
            reasons.append("LEGACY_ITEM_EXECUTION_AUTHORITY_TRUE")
        if item.get("dashboard_serving_truth") is not False:
            reasons.append("LEGACY_ITEM_DASHBOARD_SERVING_TRUTH_TRUE")
        for key in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if item.get(key) is not False:
                reasons.append(f"LEGACY_ITEM_{key.upper()}_NOT_FALSE")

    if unknown_items:
        reasons.append("UNKNOWN_DASHBOARD_SHELL_ARTIFACT_PRESENT")

    for field in ("active_unsafe_paths", "legacy_unsafe_paths", "unknown_unsafe_paths", "blocking_reasons"):
        value = report.get(field)
        if not isinstance(value, list):
            reasons.append(f"{field.upper()}_NOT_LIST")
        elif value:
            reasons.append(f"{field.upper()}_NON_EMPTY")

    if report.get("status") not in {"PASS", "PASS_WITH_LEGACY_RETAINED"}:
        reasons.append("REPORT_STATUS_NOT_PASS")

    if reasons:
        unique_reasons = tuple(sorted(set(reasons)))
        return RuntimeDashboardArtifactHygieneValidation(
            status="BLOCKED",
            message="runtime dashboard artifact hygiene blocked",
            blocking_reasons=unique_reasons,
        )
    return RuntimeDashboardArtifactHygieneValidation(
        status="PASS",
        message="runtime dashboard artifacts are session-scoped or explicitly retained as non-authoritative legacy artifacts",
        blocking_reasons=(),
    )
