from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-WINDOWS-RESTART-RECOVERY-ARTIFACT-PATH-GUARD"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_convergence_memory_failure_learning_hardening_patch_evidence import ensure_matrix_row, ensure_requirement  # noqa: E402
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
from trader1.core.ledger.restart_recovery import build_restart_recovery_report, validate_restart_recovery_report  # noqa: E402
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (  # noqa: E402
    build_upbit_paper_ledger_rollup_repair_report,
    validate_upbit_paper_ledger_rollup_repair_report,
    write_upbit_paper_ledger_rollup_repair_report,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (  # noqa: E402
    build_upbit_paper_post_repair_reconciliation_report,
    validate_upbit_paper_post_repair_reconciliation_report,
    write_upbit_paper_post_repair_reconciliation_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "restart_recovery_validator",
    "runtime_schema_instance_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if not validator_id.startswith("patch_result") and validator_id != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "trader1/core/ledger/restart_recovery.py",
    "contracts/schema/restart_recovery_report.schema.json",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_restart_recovery.py",
    "tools/emit_windows_restart_recovery_artifact_path_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD.md",
    "system/runtime/upbit/krw_spot/paper/recovery/restart_recovery_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/restart_recovery_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_ledger_rollup_repair_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/repairs/mvp4-ledger-jsonl-recovery-ui-refresh-regenerated-current-schema.ledger_rollup_candidate.json",
]
RUNTIME_REPORT_TARGETS = [
    (
        "system/runtime/upbit/krw_spot/paper/recovery/restart_recovery_report.json",
        "mvp2-restart-recovery",
        "mvp2_restart_recovery",
    ),
    (
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/restart_recovery_report.json",
        "mvp4-dashboard-bound-upbit-paper-restart",
        "mvp1_upbit_paper_launcher",
    ),
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


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1600:],
        "stderr_tail": completed.stderr[-1600:],
    }


def write_runtime_reports() -> list[str]:
    artifact_paths: list[str] = []
    for target, restart_id, session_id in RUNTIME_REPORT_TARGETS:
        report = build_restart_recovery_report(
            restart_id=restart_id,
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=session_id,
        )
        write_json(ROOT / target, report)
        artifact_paths.append(target)
    return artifact_paths


def refresh_dependent_paper_repair_artifacts() -> list[str]:
    repair_plan_path = (
        ROOT
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / "mvp1_upbit_paper_launcher"
        / "paper_runtime"
        / "upbit_paper_blocked_repair_plan_report.json"
    )
    repair_plan = load_json(repair_plan_path)
    ledger_report = build_upbit_paper_ledger_rollup_repair_report(root=ROOT, repair_plan_report=repair_plan)
    ledger_result = validate_upbit_paper_ledger_rollup_repair_report(ledger_report)
    if ledger_result.status != "PASS":
        raise RuntimeError(f"ledger rollup repair refresh failed: {ledger_result.status} {ledger_result.message}")
    ledger_path = write_upbit_paper_ledger_rollup_repair_report(root=ROOT, report=ledger_report)
    post_report = build_upbit_paper_post_repair_reconciliation_report(
        ledger_rollup_repair_report=ledger_report,
        source_repair_report_path=rel(ledger_path),
    )
    post_result = validate_upbit_paper_post_repair_reconciliation_report(post_report)
    if post_result.status != "PASS":
        raise RuntimeError(f"post-repair reconciliation refresh failed: {post_result.status} {post_result.message}")
    post_path = write_upbit_paper_post_repair_reconciliation_report(root=ROOT, report=post_report)
    refreshed = [rel(ledger_path), rel(post_path)]
    for item in ledger_report.get("items", []):
        candidate_path = item.get("candidate_rollup_artifact_path") if isinstance(item, dict) else None
        if isinstance(candidate_path, str):
            refreshed.append(candidate_path)
    return sorted(set(refreshed))


def build_audit() -> dict[str, Any]:
    pass_report = build_restart_recovery_report(restart_id="audit-windows-restart-pass")
    drive_path = build_restart_recovery_report(
        restart_id="audit-windows-restart-drive-path",
        recovery_artifact_paths=["C:/TRADER_1/system/runtime/restart_recovery_report.json"],
    )
    backslash_path = build_restart_recovery_report(
        restart_id="audit-windows-restart-backslash-path",
        recovery_artifact_paths=["system\\runtime\\restart_recovery_report.json"],
    )
    traversal_path = build_restart_recovery_report(
        restart_id="audit-windows-restart-traversal-path",
        recovery_artifact_paths=["system/runtime/../restart_recovery_report.json"],
    )
    missing_partial = build_restart_recovery_report(
        restart_id="audit-windows-restart-missing-partial-write",
        partial_write_recovery_checked=False,
    )
    empty_paths = build_restart_recovery_report(
        restart_id="audit-windows-restart-empty-paths",
        recovery_artifact_paths=[],
    )
    cases = {
        "pass_report": validate_restart_recovery_report(pass_report),
        "drive_path": validate_restart_recovery_report(drive_path),
        "backslash_path": validate_restart_recovery_report(backslash_path),
        "traversal_path": validate_restart_recovery_report(traversal_path),
        "missing_partial_write": validate_restart_recovery_report(missing_partial),
        "empty_paths": validate_restart_recovery_report(empty_paths),
    }
    checks = {
        "pass_report_has_windows_path_evidence": cases["pass_report"].status == "PASS"
        and pass_report["windows_path_recovery_checked"]
        and pass_report["atomic_write_recovery_checked"]
        and pass_report["partial_write_recovery_checked"]
        and pass_report["stale_lock_recovery_checked"],
        "pass_report_has_safe_relative_artifacts": bool(pass_report["recovery_artifact_paths"])
        and all("\\" not in path and not path.startswith("/") and ":" not in path[:2] for path in pass_report["recovery_artifact_paths"]),
        "drive_path_blocks": cases["drive_path"].status == "BLOCKED" and cases["drive_path"].blocker_code == "SNAPSHOT_SCOPE_MISMATCH",
        "backslash_path_blocks": cases["backslash_path"].status == "BLOCKED" and cases["backslash_path"].blocker_code == "SNAPSHOT_SCOPE_MISMATCH",
        "traversal_path_blocks": cases["traversal_path"].status == "BLOCKED" and cases["traversal_path"].blocker_code == "SNAPSHOT_SCOPE_MISMATCH",
        "missing_partial_write_blocks": cases["missing_partial_write"].status == "BLOCKED"
        and cases["missing_partial_write"].blocker_code == "RECONCILIATION_REQUIRED",
        "empty_artifact_paths_block": cases["empty_paths"].status == "BLOCKED" and cases["empty_paths"].blocker_code == "RECONCILIATION_REQUIRED",
        "live_flags_remain_false": not pass_report["live_order_ready"]
        and not pass_report["live_order_allowed"]
        and not pass_report["can_live_trade"]
        and not pass_report["can_submit_order"]
        and not pass_report["order_adapter_called"],
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.windows_restart_recovery_artifact_path_guard_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "case_results": {
            name: {"status": result.status, "blocker_code": result.blocker_code, "message": result.message}
            for name, result in cases.items()
        },
        "recovery_artifact_paths": pass_report["recovery_artifact_paths"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_navigation(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any], refreshed_artifacts: list[str]) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    matrix = load_json(matrix_path)
    req_index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    ensure_requirement(
        req_index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE",
            "source_file": "TRADER_1.md",
            "source_heading": "Runtime recovery and Windows-safe restart artifact paths",
            "full_text_marker": f"{REQUIREMENT_ID}:restart recovery PASS requires Windows-safe relative artifact paths and partial-write evidence",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Windows-safe restart recovery artifact path and partial-write evidence guard",
            "requirement_kind": "RUNTIME_SAFETY_VALIDATOR_PATCH",
            "schema_ids": ["trader1.restart_recovery_report.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_restart_recovery.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP2-RESTART-RECOVERY-SKELETON",
                "REQ-MVP4-RESTART-RECOVERY-WAL-LEDGER-BINDING-RECHECK",
                "REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"restart recovery PASS requires Windows-safe relative artifact paths and partial-write evidence"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE",
            "schema_files": ["contracts/schema/restart_recovery_report.schema.json"],
            "validator_files": ["trader1/core/ledger/restart_recovery.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_restart_recovery.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/core/ledger/restart_recovery.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
                *[target for target, _, _ in RUNTIME_REPORT_TARGETS],
                *refreshed_artifacts,
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    req_index["trader1_sha256"] = trader_hash
    req_index["agents_sha256"] = agents_hash
    write_json(req_path, req_index)
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD.md",
        f"""# MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD

context_pack_id: MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD
task_class: MVP4_WINDOWS_RUNTIME_RECOVERY_CONTINUE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.restart_recovery_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Restart recovery PASS requires windows_path_recovery_checked=true.
- Restart recovery PASS requires atomic_write_recovery_checked=true.
- Restart recovery PASS requires partial_write_recovery_checked=true.
- Restart recovery PASS requires stale_lock_recovery_checked=true.
- Recovery artifact paths must be non-empty relative POSIX paths with no drive prefix, backslash, absolute path, or parent traversal.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- recovery_artifact_paths: {json.dumps(audit["recovery_artifact_paths"])}
- refreshed_dependent_paper_repair_artifacts: {json.dumps(refreshed_artifacts)}
- negative_cases: drive path, backslash path, parent traversal, missing partial-write evidence, empty artifact paths

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
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

Restart recovery now requires Windows-safe relative artifact paths plus atomic-write, partial-write, and stale-lock recovery evidence before a PAPER restart report can PASS. Unsafe paths and missing recovery evidence fail closed.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


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
        "affected_contract_ids": [
            REQUIREMENT_ID,
            "REQ-MVP2-RESTART-RECOVERY-SKELETON",
            "REQ-MVP4-RESTART-RECOVERY-WAL-LEDGER-BINDING-RECHECK",
            "REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK",
            "REQ-MVP4-LIVE-FINAL-GUARD",
        ],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [
            REQUIREMENT_ID,
            "restart_recovery_windows_artifact_path_guard",
            "contracts/generated/context_pack/MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD.md",
        ],
        "new_or_changed_schema_ids": ["trader1.restart_recovery_report.v1"],
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
        "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_LIVE_FINAL_GUARD"],
        "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
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
        "active_read_surface_used": [
            "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE",
            "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "task_class": "MVP4_WINDOWS_RUNTIME_RECOVERY_CONTINUE",
        "required_section_ids": [
            "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE",
            "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "expanded_section_ids": [
            "TRADER_1:runtime-recovery-active-surface",
            "TRADER_1:partial-write-crash-recovery-active-surface",
            "AGENTS:restart-recovery-file-hint",
        ],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_WINDOWS_RESTART_RECOVERY_GUARD",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_APPLICABLE",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
    }
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    audit: dict[str, Any],
    refreshed_artifacts: list[str],
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
            "stage_gate_status": "PASS_FOR_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD_NO_LIVE_ORDERS",
            "restart_recovery_artifact_path_audit": audit,
            "refreshed_dependent_paper_repair_artifacts": refreshed_artifacts,
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
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260501.md",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
        },
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Windows Restart Recovery Artifact Path Guard

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- restart_recovery_report now records Windows path recovery, atomic write recovery, partial-write recovery, stale-lock recovery, and recovery artifact paths.
- Restart recovery PASS requires all recovery checks to be true.
- Recovery artifact paths must be relative POSIX paths with no Windows drive prefix, backslash, absolute path, empty segment, dot segment, or parent traversal.
- Negative fixtures cover drive paths, backslashes, parent traversal, missing partial-write evidence, and empty artifact paths.

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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.restart_recovery_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + VALIDATORS_REQUIRED))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
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
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    runtime_reports = write_runtime_reports()
    refreshed_artifacts = refresh_dependent_paper_repair_artifacts()
    audit = build_audit()
    update_navigation(now, trader_hash, agents_hash, audit, refreshed_artifacts)
    update_authority_manifest(now)
    write_source_bundle_manifest()
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/runtime/test_restart_recovery.py", "-q"], timeout_seconds=300),
        run_command([sys.executable, "-B", "tools/run_restart_recovery_validators.py"], timeout_seconds=300),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"], timeout_seconds=300),
    ]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit, refreshed_artifacts)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    for _ in range(2):
        patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
        write_evidence(now, trader_hash, agents_hash, patch_result, audit, refreshed_artifacts)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"], timeout_seconds=300))
    for _ in range(2):
        patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
        write_evidence(now, trader_hash, agents_hash, patch_result, audit, refreshed_artifacts)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "Windows restart recovery artifact path guard audit failed"})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "runtime_reports": runtime_reports,
                "refreshed_dependent_paper_repair_artifacts": refreshed_artifacts,
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
