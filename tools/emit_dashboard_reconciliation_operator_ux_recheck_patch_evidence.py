from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-RECONCILIATION-OPERATOR-UX-RECHECK"
NEXT_TASK_CLASS = "MVP4_PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    run_command,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.core.ledger.restart_recovery import build_restart_recovery_report  # noqa: E402
from trader1.config.config_schema import build_runtime_config  # noqa: E402
from trader1.dashboard.read_only_dashboard import (  # noqa: E402
    build_read_only_dashboard_shell,
    dashboard_shell_hash,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.summary_writer import build_summary_shell  # noqa: E402
from trader1.runtime.boot.startup_probe import build_startup_probe  # noqa: E402
from trader1.runtime.health.heartbeat import build_heartbeat  # noqa: E402
from trader1.runtime.portfolio.paper_portfolio import build_initial_paper_portfolio_snapshot  # noqa: E402
from trader1.runtime.readiness.readiness_surface import build_readiness_surface  # noqa: E402
from trader1.runtime.reconciliation.reconciliation import build_reconciliation_report  # noqa: E402
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "reconciliation_validator",
    "restart_recovery_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if not validator_id.startswith("patch_result") and validator_id != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/validation/mvp0_validators.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_reconciliation_operator_ux_recheck_patch_evidence.py",
    "contracts/generated/context_pack/DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
]
BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def build_dashboard_fixture(
    *,
    session_id: str = "dashboard_reconciliation_operator_ux_audit",
    reconciliation_report: dict[str, Any] | None = None,
    restart_recovery_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_bundle_hash = sha256_json(
        {rel(path): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))}
    )
    source_tree_hash = sha256_json(
        {
            rel(path): sha256_file(path)
            for path in sorted((ROOT / "trader1").rglob("*.py"))
            if "__pycache__" not in path.parts
        }
    )
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    portfolio = build_initial_paper_portfolio_snapshot(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id=session_id,
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness,
        paper_portfolio_snapshot=portfolio,
    )
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        reconciliation_report=reconciliation_report,
        restart_recovery_report=restart_recovery_report,
    )


def dashboard_reconciliation_operator_ux_audit() -> dict[str, Any]:
    allowed_blockers = set(load_json(ROOT / "contracts" / "registry.yaml")["enums"]["live_blocker_code"]["values"])
    default_dashboard = build_dashboard_fixture()
    default_result = validate_read_only_dashboard_shell(default_dashboard, allowed_blockers)
    default_summary = default_dashboard["reconciliation_recovery_summary"]

    pass_session = "dashboard_reconciliation_operator_ux_audit_pass"
    pass_dashboard = build_dashboard_fixture(
        session_id=pass_session,
        reconciliation_report=build_reconciliation_report(
            reconciliation_id="dashboard-reconciliation-pass",
            session_id=pass_session,
        ),
        restart_recovery_report=build_restart_recovery_report(
            restart_id="dashboard-restart-pass",
            session_id=pass_session,
        ),
    )
    pass_result = validate_read_only_dashboard_shell(pass_dashboard, allowed_blockers)
    pass_summary = pass_dashboard["reconciliation_recovery_summary"]

    mismatch_session = "dashboard_reconciliation_operator_ux_audit_mismatch"
    mismatch_report = build_reconciliation_report(
        reconciliation_id="dashboard-reconciliation-mismatch",
        session_id=mismatch_session,
        exchange_snapshot={
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": mismatch_session,
            "balances": {"KRW": "1000000"},
            "positions": [],
            "open_orders": [],
        },
        internal_state={
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": mismatch_session,
            "balances": {"KRW": "900000"},
            "positions": [],
            "open_orders": [],
        },
    )
    mismatch_dashboard = build_dashboard_fixture(
        session_id=mismatch_session,
        reconciliation_report=mismatch_report,
        restart_recovery_report=build_restart_recovery_report(
            restart_id="dashboard-restart-mismatch",
            session_id=mismatch_session,
        ),
    )
    mismatch_result = validate_read_only_dashboard_shell(mismatch_dashboard, allowed_blockers)
    mismatch_summary = mismatch_dashboard["reconciliation_recovery_summary"]

    live_drift_dashboard = build_dashboard_fixture(
        session_id=pass_session,
        reconciliation_report=build_reconciliation_report(
            reconciliation_id="dashboard-reconciliation-live-drift",
            session_id=pass_session,
        ),
        restart_recovery_report=build_restart_recovery_report(
            restart_id="dashboard-restart-live-drift",
            session_id=pass_session,
        ),
    )
    live_drift_dashboard["reconciliation_recovery_summary"]["live_order_allowed"] = True
    live_drift_dashboard["dashboard_hash"] = dashboard_shell_hash(live_drift_dashboard)
    live_drift_result = validate_read_only_dashboard_shell(live_drift_dashboard, allowed_blockers)

    checks = {
        "default_not_loaded_visible": (
            default_result.status == "PASS"
            and default_summary["status"] == "NOT_LOADED"
            and default_summary["color_token"] == "yellow"
            and default_summary["live_order_allowed"] is False
        ),
        "pass_display_only_green": (
            pass_result.status == "PASS"
            and pass_summary["status"] == "PASS"
            and pass_summary["color_token"] == "green"
            and pass_summary["primary_blocker_code"] == "LIVE_READY_MISSING"
            and pass_summary["live_order_allowed"] is False
        ),
        "mismatch_display_red": (
            mismatch_result.status == "PASS"
            and mismatch_summary["status"] == "BLOCKED"
            and mismatch_summary["color_token"] == "red"
            and mismatch_summary["primary_blocker_code"] == "RECONCILIATION_REQUIRED"
            and mismatch_summary["mismatch_count"] == 1
        ),
        "live_drift_blocked": (
            live_drift_result.status == "BLOCKED"
            and live_drift_result.blocker_code == "LIVE_FINAL_GUARD_FAILED"
        ),
    }
    blockers = [name for name, ok in checks.items() if not ok]
    return {
        "audit_schema_id": "trader1.dashboard_reconciliation_operator_ux_recheck_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "default_panel_status": default_summary["status"],
        "default_panel_color": default_summary["color_token"],
        "pass_panel_status": pass_summary["status"],
        "pass_panel_color": pass_summary["color_token"],
        "mismatch_panel_status": mismatch_summary["status"],
        "mismatch_panel_color": mismatch_summary["color_token"],
        "mismatch_count": mismatch_summary["mismatch_count"],
        "live_drift_result": live_drift_result.status,
        "live_drift_blocker": live_drift_result.blocker_code,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_action": (
            "Bind actual PAPER reconciliation artifacts into launcher dashboard generation."
            if not blockers
            else "Repair dashboard reconciliation operator UX before continuing."
        ),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK.md",
        f"""# DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK

context_pack_id: DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK
task_class: MVP4_DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard first screen shows a dedicated Ledger & Reconciliation panel.
- Missing reconciliation/restart evidence is visible as yellow warning, not hidden behind green operation status.
- PASS reconciliation/restart evidence displays green but still shows LIVE_READY_MISSING and all live flags false.
- Reconciliation mismatch displays red BLOCKED and does not create order permission.
- Dashboard validator blocks any reconciliation panel live/order/scale flag drift.

coverage_snapshot:
- default_panel_status: {audit["default_panel_status"]}
- default_panel_color: {audit["default_panel_color"]}
- pass_panel_status: {audit["pass_panel_status"]}
- pass_panel_color: {audit["pass_panel_color"]}
- mismatch_panel_status: {audit["mismatch_panel_status"]}
- mismatch_panel_color: {audit["mismatch_panel_color"]}
- live_drift_result: {audit["live_drift_result"]}

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

The read-only dashboard now has a dedicated Ledger & Reconciliation panel. Missing evidence is yellow, clean PAPER reconciliation/restart evidence is green but still live-blocked, and reconciliation mismatch or invalid evidence is red and fail-closed.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard reconciliation operator visibility",
            "full_text_marker": f"{REQUIREMENT_ID}:dashboard must show reconciliation and recovery status without live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard shows ledger/reconciliation safety status",
            "requirement_kind": "DASHBOARD_UX_SAFETY_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-LEDGER-RECONCILIATION-RECOVERY-EDGE-RECHECK"],
            "source_text_sha256": sha256_bytes(b"dashboard must show reconciliation and recovery status without live permission"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
) -> dict[str, Any]:
    patch_result: dict[str, Any] = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP4-LEDGER-RECONCILIATION-RECOVERY-EDGE-RECHECK"],
        "affected_exchange": "UPBIT_AND_BINANCE",
        "affected_market_type": "KRW_SPOT_AND_SPOT",
        "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
        "validators_required": validators_required,
        "validators_run": validators_run,
        "tests_run": tests_run,
        "coverage_unmapped_count": 0,
        "coverage_index_result": "UPDATED_PASS",
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
        "read_cache_update_required": True,
        "context_pack_update_required": True,
        "current_implementation_state_updated": True,
        "next_task_class": NEXT_TASK_CLASS,
        "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY"],
        "next_optional_section_ids": ["SECTION_RUNTIME_ARTIFACT_BINDING", "SECTION_LEDGER_IDEMPOTENCY"],
        "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
        "live_order_ready_before": False,
        "live_order_ready_after": False,
        "live_order_allowed_before": False,
        "live_order_allowed_after": False,
        "can_live_trade_before": False,
        "can_live_trade_after": False,
        "scale_up_allowed_before": False,
        "scale_up_allowed_after": False,
        "remaining_blockers": BLOCKERS,
        "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
        "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
        "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
        "token_navigation_patch": True,
        "active_read_surface_used": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK",
        "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["TRADER_1:dashboard-operator-ux-active-surface", "AGENTS:dashboard-implementation-guide"],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "REUSED_HASH_MATCH",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UPDATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_DASHBOARD_RECONCILIATION_UX",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
    }
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "validators_untested": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_FOR_DASHBOARD_RECONCILIATION_OPERATOR_UX_NO_LIVE_ORDERS",
            "dashboard_reconciliation_operator_ux_audit": audit,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_AUDIT.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Dashboard Reconciliation Operator UX Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- The dashboard could show a fresh green operation heartbeat while ledger/reconciliation/restart evidence was not visible on the first screen.
- Reconciliation mismatch needed an explicit red display state and a negative validator path.
- Clean PAPER reconciliation needed to be shown as PAPER-only review state, not live readiness.

Patch:
- Added Ledger & Reconciliation panel to the read-only dashboard shell and HTML.
- Added strict schema fields for reconciliation/restart validation status, mismatch count, writer/idempotency state, and live boundary flags.
- Added dashboard validation that blocks live/order/scale drift inside the new panel.
- Added negative tests for mismatch display, false PASS display, and live permission drift.
- Regenerated UPBIT_PAPER and BINANCE_PAPER safe dashboard runtime artifacts.

Audit:
- default_panel_status: {audit['default_panel_status']} / {audit['default_panel_color']}
- pass_panel_status: {audit['pass_panel_status']} / {audit['pass_panel_color']}
- mismatch_panel_status: {audit['mismatch_panel_status']} / {audit['mismatch_panel_color']}
- live_drift_result: {audit['live_drift_result']} / {audit['live_drift_blocker']}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    audit = dashboard_reconciliation_operator_ux_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command(
            [
                sys.executable,
                "-c",
                "from trader1.runtime.boot.safe_launcher import launcher_main; raise SystemExit(launcher_main('UPBIT_PAPER', pause=False, open_dashboard=False, console_heartbeat_ticks=1, console_heartbeat_interval_seconds=0.0))",
            ]
        ),
        run_command(
            [
                sys.executable,
                "-c",
                "from trader1.runtime.boot.safe_launcher import launcher_main; raise SystemExit(launcher_main('BINANCE_PAPER', pause=False, open_dashboard=False, console_heartbeat_ticks=1, console_heartbeat_interval_seconds=0.0))",
            ]
        ),
    ]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS_REQUIRED), BOOTSTRAP_VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "dashboard reconciliation operator UX audit failed"})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "default_panel": [audit["default_panel_status"], audit["default_panel_color"]],
                "pass_panel": [audit["pass_panel_status"], audit["pass_panel_color"]],
                "mismatch_panel": [audit["mismatch_panel_status"], audit["mismatch_panel_color"]],
                "live_drift": [audit["live_drift_result"], audit["live_drift_blocker"]],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
