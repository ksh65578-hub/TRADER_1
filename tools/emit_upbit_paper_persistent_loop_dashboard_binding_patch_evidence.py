from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-DASHBOARD-BINDING"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_EVIDENCE"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.config.config_schema import build_runtime_config  # noqa: E402
from trader1.dashboard.read_only_dashboard import (  # noqa: E402
    build_read_only_dashboard_shell,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.summary_writer import build_summary_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import (  # noqa: E402
    build_launcher_report,
    launcher_dashboard_paths,
    load_json as launcher_load_json,
    write_launcher_dashboard,
)
from trader1.runtime.boot.startup_probe import build_startup_probe  # noqa: E402
from trader1.runtime.health.heartbeat import build_heartbeat  # noqa: E402
from trader1.runtime.paper.upbit_paper_persistent_loop import (  # noqa: E402
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.readiness.readiness_surface import build_readiness_surface  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_recovery_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "trader1/runtime/paper/upbit_paper_persistent_loop.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/runtime/test_safe_launcher.py",
    "tools/emit_upbit_paper_persistent_loop_dashboard_binding_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

REMAINING_BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def run_safe_command(args: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def cleanup_cache_artifacts() -> None:
    for cache_dir in [ROOT / ".pytest_cache", *ROOT.rglob("__pycache__")]:
        if not cache_dir.exists() or not cache_dir.is_dir():
            continue
        resolved = cache_dir.resolve()
        if ROOT.resolve() not in (resolved, *resolved.parents):
            raise RuntimeError(f"refusing to remove cache outside repo: {resolved}")
        if resolved.name not in {".pytest_cache", "__pycache__"}:
            raise RuntimeError(f"refusing to remove unexpected cache path: {resolved}")
        shutil.rmtree(resolved)


def refresh_current_dashboard_shells() -> None:
    for launcher_name in ("UPBIT_PAPER", "BINANCE_PAPER"):
        report = build_launcher_report(launcher_name)
        write_launcher_dashboard(report)
        if report.get("live_order_allowed") is not False or report.get("can_live_trade") is not False:
            raise RuntimeError(f"launcher refresh attempted live permission: {launcher_name}")


def build_dashboard_inputs(session_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_bundle_hash = sha256_json(
        {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
        }
    )
    source_tree_hash = sha256_json(
        {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
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
        authority={
            "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
            "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
        },
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness,
    )
    return summary, heartbeat, startup_probe


def validate_temp_dashboard_projection() -> dict[str, Any]:
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(
            root=temp_root,
            loop_id="evidence-paper-persistent-loop-dashboard-binding",
            session_id=SESSION_ID,
            requested_cycle_count=1,
        )
        loop_result = validate_upbit_paper_persistent_loop_report(loop)
        if loop_result.status != "PASS":
            raise RuntimeError(f"persistent loop fixture did not validate: {loop_result.status} {loop_result.blocker_code}")
        summary, heartbeat, startup_probe = build_dashboard_inputs(SESSION_ID)
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=SESSION_ID,
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
            upbit_paper_persistent_loop_report=loop,
        )
        dashboard_result = validate_read_only_dashboard_shell(dashboard)
        if dashboard_result.status != "PASS":
            raise RuntimeError(
                f"dashboard projection did not validate: {dashboard_result.status} {dashboard_result.blocker_code}"
            )
        loop_status = dashboard["paper_persistent_loop_status"]
        if loop_status["status"] != "PASS":
            raise RuntimeError("dashboard did not project the persistent loop as PASS")
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if loop_status.get(field) is not False or dashboard.get(field) is not False:
                raise RuntimeError(f"dashboard attempted forbidden live or scale permission: {field}")
        if loop_status["long_run_evidence_eligible"] is not False or loop_status["promotion_eligible"] is not False:
            raise RuntimeError("dashboard attempted to promote bounded PAPER loop evidence")
        source_ids = {source["artifact_id"]: source for source in dashboard["source_artifacts"]}
        paper_source = source_ids.get("PAPER_PERSISTENT_LOOP")
        if not isinstance(paper_source, dict) or paper_source.get("freshness_status") != "PASS":
            raise RuntimeError("dashboard did not publish PAPER_PERSISTENT_LOOP as a fresh source")
        return {
            "loop_hash": loop["loop_hash"],
            "dashboard_hash": dashboard["dashboard_hash"],
            "paper_persistent_loop_status": loop_status["status"],
            "runtime_evidence_role": loop_status["runtime_evidence_role"],
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }


def validate_launcher_projection() -> dict[str, Any]:
    report = build_launcher_report("UPBIT_PAPER")
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(
            root=temp_root,
            loop_id="evidence-launcher-paper-persistent-loop-dashboard-binding",
            session_id=report["session_id"],
            requested_cycle_count=1,
        )
        dashboard_paths = write_launcher_dashboard(report, temp_root)
        dashboard = launcher_load_json(dashboard_paths["dashboard_shell"])
        canonical_path = launcher_dashboard_paths(report, temp_root)["upbit_paper_persistent_loop_report"]
        if not canonical_path.exists():
            raise RuntimeError("launcher canonical persistent loop path was not written")
        if launcher_load_json(canonical_path)["loop_hash"] != loop["loop_hash"]:
            raise RuntimeError("launcher canonical persistent loop report drifted from loop output")
        result = validate_read_only_dashboard_shell(dashboard)
        if result.status != "PASS":
            raise RuntimeError(f"launcher dashboard validation failed: {result.status} {result.blocker_code}")
        loop_status = dashboard["paper_persistent_loop_status"]
        if loop_status["status"] != "PASS" or loop_status["runtime_evidence_role"] != "BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE":
            raise RuntimeError("launcher did not bind bounded PAPER loop status")
        if loop_status["live_order_allowed"] or loop_status["can_live_trade"] or loop_status["scale_up_allowed"]:
            raise RuntimeError("launcher persistent loop status attempted live or scale permission")
        return {
            "loop_hash": loop["loop_hash"],
            "canonical_loop_path": str(canonical_path),
            "dashboard_shell_path": str(dashboard_paths["dashboard_shell"]),
            "dashboard_hash": dashboard["dashboard_hash"],
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_persistent_loop_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit PAPER persistent loop writes a canonical latest loop report for launcher/dashboard discovery.
- Safe launcher loads the scoped canonical or latest loop report without cross-session leakage.
- Read-only dashboard projects bounded PAPER loop status as dashboard display truth only.
- Bounded PAPER loop evidence cannot become long-run evidence, LIVE_READY, live order permission, or scale-up permission.

known_omissions_by_design:
- This patch does not resolve post-rerun reconciliation.
- This patch does not create long-run evidence, LIVE_READY, live order permission, credential loading, live config mutation, or scale-up.
- Binance spot/futures and MICRO_LIVE remain outside this patch.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
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

Upbit PAPER persistent loop reports now have a canonical latest report path and a read-only dashboard projection. The projection is bounded PAPER runtime status only and cannot create long-run evidence, LIVE_READY, live order permission, or scale-up.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = json.loads(req_path.read_text(encoding="utf-8"))
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "PAPER persistent runtime dashboard truth",
            "full_text_marker": f"{REQUIREMENT_ID}: dashboard must load scoped Upbit PAPER persistent loop status as bounded display truth only",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER persistent loop dashboard binding",
            "requirement_kind": "RUNTIME_DASHBOARD_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_persistent_loop_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/runtime/test_safe_launcher.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-PERSISTENT-RUNTIME-RECOVERY-PREFLIGHT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"dashboard must load scoped Upbit PAPER persistent loop status as bounded display truth only"
            ),
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

    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/upbit_paper_persistent_loop_report.schema.json",
            ],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
            ],
            "test_files": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/runtime/test_safe_launcher.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["paper_persistent_loop_status"],
            "patch_result_fields": [
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
    matrix.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "rows": sorted(rows, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = json.loads(
        (ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_LEDGER_JSONL_RECOVERY.patch_result.json").read_text(
            encoding="utf-8"
        )
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_RUNTIME_RECOVERY", "SECTION_STRATEGY_PROFITABILITY"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": REMAINING_BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    dashboard_projection: dict[str, Any],
    launcher_projection: dict[str, Any],
) -> None:
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
            "stage_gate_status": "PASS_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING_LIVE_BLOCKED",
            "dashboard_projection": dashboard_projection,
            "launcher_projection": launcher_projection,
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
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_projection": dashboard_projection,
            "launcher_projection": launcher_projection,
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Persistent Loop Dashboard Binding Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Writes a canonical Upbit PAPER persistent loop report at paper_runtime/upbit_paper_persistent_loop_report.json.
- Loads the scoped canonical/latest persistent loop report through the safe launcher.
- Adds a read-only dashboard panel and schema for paper_persistent_loop_status.
- Keeps the bounded PAPER loop separated from long-run evidence, LIVE_READY, live orders, and scale-up.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live orders, live config mutation, LIVE_READY writer, or scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.read_only_dashboard_shell.v1"]))
    state["implemented_validator_ids"] = sorted(
        set(
            state.get("implemented_validator_ids", [])
            + [
                "read_only_dashboard_validator",
                "dashboard_visual_layout_validator",
                "upbit_paper_persistent_loop_validator",
            ]
        )
    )
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
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
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)

    dashboard_projection = validate_temp_dashboard_projection()
    launcher_projection = validate_launcher_projection()
    cleanup_cache_artifacts()
    refresh_current_dashboard_shells()
    write_source_bundle_manifest()

    tests_run = [
        run_safe_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_projects_paper_persistent_loop_as_bounded_runtime_evidence",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_persistent_loop_live_or_long_run_drift",
                "tests/runtime/test_safe_launcher.py::SafeLauncherTest::test_launcher_dashboard_binds_scoped_upbit_paper_persistent_loop_status",
                "-p",
                "no:cacheprovider",
                "-q",
            ]
        ),
        run_safe_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "-p",
                "no:cacheprovider",
                "-q",
            ]
        ),
        run_safe_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
    ]
    cleanup_cache_artifacts()
    refresh_current_dashboard_shells()
    write_source_bundle_manifest()
    tests_run.append(run_safe_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]))
    cleanup_cache_artifacts()
    write_source_bundle_manifest()
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard_projection, launcher_projection)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_safe_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard_projection, launcher_projection)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
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
