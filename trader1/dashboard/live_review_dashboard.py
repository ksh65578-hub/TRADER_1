from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import render_first_line


LIVE_REVIEW_DASHBOARD_SCHEMA_ID = "trader1.live_review_dashboard.v1"
FORBIDDEN_WORDING = {
    "profit guaranteed",
    "automatic profit",
    "converged to profit",
    "self-optimizing live",
    "safe to scale automatically",
    "ready to size up",
    "LIVE READY",
}


@dataclass(frozen=True)
class LiveReviewDashboardValidationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def live_review_dashboard_hash(dashboard: dict[str, Any]) -> str:
    payload = dict(dashboard)
    payload.pop("dashboard_hash", None)
    return _sha256_json(payload)


def build_live_review_dashboard(
    *,
    authority: dict[str, str],
    preflight_report: dict[str, Any],
    dashboard_id: str = "mvp4-upbit-live-review-dashboard",
) -> dict[str, Any]:
    first_line = render_first_line(preflight_report["readiness_surface"])
    dashboard = {
        "schema_id": LIVE_REVIEW_DASHBOARD_SCHEMA_ID,
        "dashboard_id": dashboard_id,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": preflight_report["exchange"],
        "market_type": preflight_report["market_type"],
        "mode": preflight_report["mode"],
        "session_id": preflight_report["session_id"],
        "display_only": True,
        "first_line": first_line,
        "can_live_review": bool(preflight_report.get("can_live_review")),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_controls_present": False,
        "forbidden_wording_present": any(text.lower() in first_line.lower() for text in FORBIDDEN_WORDING),
        "preflight_status": preflight_report["preflight_status"],
        "primary_blocker_code": preflight_report["primary_blocker_code"],
        "blockers": preflight_report["blockers"],
        "dashboard_hash": "",
    }
    dashboard["dashboard_hash"] = live_review_dashboard_hash(dashboard)
    return dashboard


def validate_live_review_dashboard(dashboard: dict[str, Any]) -> LiveReviewDashboardValidationResult:
    if dashboard.get("schema_id") != LIVE_REVIEW_DASHBOARD_SCHEMA_ID:
        return LiveReviewDashboardValidationResult("FAIL", "live review dashboard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if dashboard.get("dashboard_hash") != live_review_dashboard_hash(dashboard):
        return LiveReviewDashboardValidationResult("FAIL", "live review dashboard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if dashboard.get("exchange") != "UPBIT" or dashboard.get("market_type") != "KRW_SPOT" or dashboard.get("mode") != "LIVE":
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if dashboard.get("display_only") is not True or dashboard.get("order_controls_present") is True:
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard must be display-only", "LIVE_FINAL_GUARD_FAILED")
    if dashboard.get("live_order_ready") or dashboard.get("live_order_allowed") or dashboard.get("can_live_trade"):
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard cannot create live permission", "LIVE_FINAL_GUARD_FAILED")
    first_line = dashboard.get("first_line", "")
    if dashboard.get("preflight_status") != "BLOCKED":
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard must display blocked preflight truth", "LIVE_FINAL_GUARD_FAILED")
    blockers = dashboard.get("blockers")
    if not isinstance(blockers, list) or not blockers:
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard must display live blockers", "LIVE_FINAL_GUARD_FAILED")
    blocker_codes = [blocker.get("code") for blocker in blockers if isinstance(blocker, dict)]
    if dashboard.get("primary_blocker_code") not in blocker_codes:
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard primary blocker must match displayed blockers", "LIVE_FINAL_GUARD_FAILED")
    if not first_line.startswith("LIVE TRADING: BLOCKED - "):
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard first line must remain live-blocked", "LIVE_FINAL_GUARD_FAILED")
    if first_line in {"READY", "LIVE READY", "BUNDLE READY", "RELEASE READY"}:
        return LiveReviewDashboardValidationResult("BLOCKED", "standalone READY display is forbidden", "LIVE_FINAL_GUARD_FAILED")
    if dashboard.get("forbidden_wording_present") is True:
        return LiveReviewDashboardValidationResult("BLOCKED", "live review dashboard contains forbidden wording", "LIVE_FINAL_GUARD_FAILED")
    if dashboard.get("can_live_review") is True and dashboard.get("live_order_ready") is True:
        return LiveReviewDashboardValidationResult("BLOCKED", "live review cannot imply live readiness", "LIVE_FINAL_GUARD_FAILED")
    return LiveReviewDashboardValidationResult("PASS", "live review dashboard is display-only and live-blocked")
