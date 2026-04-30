from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from trader1.runtime.boot.safe_launcher import (
    ROOT_LAUNCHER_SPECS,
    build_launcher_report,
    launcher_dashboard_paths,
    load_json,
    validate_launcher_report,
    write_launcher_runtime_bundle,
)
from trader1.validation.mvp0_validators import run_validators


SAFE_SMOKE_VALIDATORS = [
    "authority_integrity_validator",
    "registry_validator",
    "schema_validator",
    "root_launcher_guard_validator",
    "root_launcher_surface_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
]


def _false_live_flags(value: dict[str, Any]) -> bool:
    return not any(
        value.get(field) is True
        for field in (
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
            "order_submission_allowed",
            "exchange_account_call_allowed",
        )
    )


def _runtime_bundle_smoke_checks(temp_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for launcher_name in sorted(ROOT_LAUNCHER_SPECS):
        report = build_launcher_report(launcher_name)
        validation = validate_launcher_report(report)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report, temp_root)
        summary = load_json(dashboard_paths["summary"])
        heartbeat = load_json(dashboard_paths["heartbeat"])
        dashboard_shell = load_json(dashboard_paths["dashboard_shell"])
        dashboard_html_exists = dashboard_paths["dashboard_html"].exists()
        scoped_paths = launcher_dashboard_paths(report, temp_root)
        paths_are_scoped = all(str(report["session_id"]) in str(path) for path in scoped_paths.values())
        checks.append(
            {
                "launcher_name": launcher_name,
                "validation_status": validation.status,
                "exchange": report["exchange"],
                "market_type": report["market_type"],
                "mode": report["mode"],
                "session_id": report["session_id"],
                "report_written": report_path.exists(),
                "summary_written": dashboard_paths["summary"].exists(),
                "heartbeat_written": dashboard_paths["heartbeat"].exists(),
                "dashboard_shell_written": dashboard_paths["dashboard_shell"].exists(),
                "dashboard_html_written": dashboard_html_exists,
                "paths_are_session_scoped": paths_are_scoped,
                "final_action": report["final_action"],
                "launcher_status": report["launcher_status"],
                "heartbeat_status": heartbeat.get("heartbeat_status"),
                "dashboard_display_truth_only": dashboard_shell.get("display_only") is True
                and dashboard_shell.get("dashboard_truth_only") is True
                and dashboard_shell.get("truth_role") == "dashboard_serving_truth",
                "summary_final_action": summary.get("final_action"),
                "live_launcher_hard_blocked": report.get("live_launcher_hard_blocked"),
                "live_path_hard_blocked": report.get("live_path_hard_blocked"),
                "live_flags_false": _false_live_flags(report) and _false_live_flags(summary) and _false_live_flags(heartbeat),
            }
        )
    return checks


def run_safe_smoke(*, include_validators: bool = True) -> dict[str, Any]:
    with TemporaryDirectory(prefix="trader1_safe_smoke_") as tmp:
        temp_root = Path(tmp)
        bundle_checks = _runtime_bundle_smoke_checks(temp_root)
    validators = run_validators(SAFE_SMOKE_VALIDATORS) if include_validators else []
    bundle_pass = all(
        check["validation_status"] == "PASS"
        and check["report_written"]
        and check["summary_written"]
        and check["heartbeat_written"]
        and check["dashboard_shell_written"]
        and check["dashboard_html_written"]
        and check["paths_are_session_scoped"]
        and check["dashboard_display_truth_only"] is True
        and check["final_action"] == "NO_TRADE"
        and check["live_path_hard_blocked"] is True
        and check["live_flags_false"] is True
        for check in bundle_checks
    )
    validator_pass = all(result.get("status") == "PASS" for result in validators)
    status = "PASS" if bundle_pass and validator_pass else "FAIL"
    return {
        "schema_id": "trader1.safe_smoke_report.v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project_id": "TRADER_1",
        "status": status,
        "execution_mode": "TEMP_RUNTIME_BUNDLE_AND_LOCAL_VALIDATORS_ONLY",
        "root_launchers_checked": len(bundle_checks),
        "temporary_runtime_bundles_checked": len(bundle_checks),
        "validators_requested": SAFE_SMOKE_VALIDATORS if include_validators else [],
        "validators_run": validators,
        "runtime_bundle_checks": bundle_checks,
        "zip_reproducibility_status": "PASS" if status == "PASS" else "FAIL",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "external_calls_attempted": False,
        "credential_load_attempted": False,
        "live_order_api_attempted": False,
    }
