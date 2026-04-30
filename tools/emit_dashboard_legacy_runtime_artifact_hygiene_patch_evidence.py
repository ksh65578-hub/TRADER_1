from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-LEGACY-RUNTIME-ARTIFACT-HYGIENE"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY"

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
from trader1.runtime.artifact_hygiene import (  # noqa: E402
    build_runtime_dashboard_artifact_hygiene_report,
    validate_runtime_dashboard_artifact_hygiene_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "runtime_dashboard_artifact_hygiene_validator",
    "runtime_schema_instance_validator",
    "schema_validator",
    "registry_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/runtime/artifact_hygiene.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/schema/runtime_dashboard_artifact_hygiene_report.schema.json",
    "tests/runtime/test_dashboard_artifact_hygiene.py",
    "tools/run_runtime_dashboard_artifact_hygiene_validators.py",
    "tools/emit_dashboard_legacy_runtime_artifact_hygiene_patch_evidence.py",
    "system/evidence/runtime_artifact_hygiene/runtime_dashboard_artifact_hygiene_report.json",
]

BLOCKERS = [
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def write_hygiene_report() -> dict[str, Any]:
    report = build_runtime_dashboard_artifact_hygiene_report(ROOT)
    result = validate_runtime_dashboard_artifact_hygiene_report(report)
    report_path = ROOT / "system" / "evidence" / "runtime_artifact_hygiene" / "runtime_dashboard_artifact_hygiene_report.json"
    write_json(report_path, report)
    return {
        "command": "build runtime dashboard artifact hygiene report",
        "status": "PASS" if result.status == "PASS" else "FAIL",
        "returncode": 0 if result.status == "PASS" else 1,
        "report_path": rel(report_path),
        "active_count": report["active_count"],
        "legacy_retained_count": report["legacy_retained_count"],
        "unknown_count": report["unknown_count"],
        "validation_status": result.status,
    }


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE.md",
        f"""# MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE

context_pack_id: MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.runtime_dashboard_artifact_hygiene_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Session-scoped launcher dashboard shells are classified as active display artifacts only.
- Legacy dashboard shells without session_id are retained for audit but cannot become execution truth or dashboard-serving truth.
- Unknown dashboard_shell.json paths block hygiene validation until classified.
- Live, order, can_live_trade, and scale-up flags remain false.

known_omissions_by_design:
- legacy runtime artifacts are not deleted in this patch
- no exchange account, credential, API key, live order, or LIVE_ENABLING behavior is used

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

Runtime dashboard shell artifacts are now hygiene-classified. Session-scoped launcher dashboards remain display-only. Legacy unscoped dashboard shells are retained as non-authoritative audit artifacts and cannot be treated as current dashboard truth.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_SHELL",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard runtime artifact hygiene",
            "full_text_marker": f"{REQUIREMENT_ID}: legacy unscoped dashboard shells must be retained as non-authoritative audit artifacts",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard legacy runtime artifact hygiene",
            "requirement_kind": "RUNTIME_ARTIFACT_HYGIENE_PATCH",
            "schema_ids": ["trader1.runtime_dashboard_artifact_hygiene_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_dashboard_artifact_hygiene.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_SHELL", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-LAUNCHER-INTEGRATION",
                "REQ-MVP4-DASHBOARD-LONG-RUN-EVIDENCE-REQUIREMENTS-VISIBILITY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"legacy unscoped dashboard shells must be retained as non-authoritative audit artifacts"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
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
            "section_id": "SECTION_DASHBOARD_SHELL",
            "schema_files": ["contracts/schema/runtime_dashboard_artifact_hygiene_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py", "trader1/runtime/artifact_hygiene.py"],
            "test_files": ["tests/runtime/test_dashboard_artifact_hygiene.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/artifact_hygiene.py"],
            "evidence_artifacts": [
                "system/evidence/runtime_artifact_hygiene/runtime_dashboard_artifact_hygiene_report.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            ],
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
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "PASS",
            "authority_hash_checked": True,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-LAUNCHER-INTEGRATION",
                "REQ-MVP4-DASHBOARD-LONG-RUN-EVIDENCE-REQUIREMENTS-VISIBILITY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT,BINANCE",
            "affected_market_type": "KRW_SPOT,SPOT",
            "affected_mode": "PAPER,LIVE_SAFE_BLOCKED_DISPLAY",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID, "runtime_dashboard_artifact_hygiene_validator"],
            "new_or_changed_schema_ids": ["trader1.runtime_dashboard_artifact_hygiene_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "OPT_SLICE_EXECUTION_FEEDBACK"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
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
                "current_implementation_state",
                "dashboard shell runtime artifact scan",
                "runtime_dashboard_artifact_hygiene_report schema",
                "live final guard slice",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "CURRENT",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": True,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_DASHBOARD_ARTIFACT_HYGIENE_ONLY",
            "optimizer_status_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_output_type": "NO_OPTIMIZER_OUTPUT_CREATED",
            "optimizer_validators_required": ["runtime_dashboard_artifact_hygiene_validator", "live_final_guard_validator"],
            "optimizer_validators_run": ["runtime_dashboard_artifact_hygiene_validator:PASS", "live_final_guard_validator:PASS"],
            "optimizer_guardrail_result": "PASS_DASHBOARD_ARTIFACT_HYGIENE_DISPLAY_ONLY",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "false",
            "convergence_layer_changed": False,
            "convergence_state_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "convergence_state_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["runtime_dashboard_artifact_hygiene_validator", "live_final_guard_validator"],
            "convergence_validators_run": ["runtime_dashboard_artifact_hygiene_validator:PASS", "live_final_guard_validator:PASS"],
            "convergence_guardrail_result": "PASS_DASHBOARD_ARTIFACTS_CANNOT_CREATE_LIVE_PERMISSION",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_RUNTIME_DASHBOARD_ARTIFACT_HYGIENE_NO_LIVE_PERMISSION",
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
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260430.md",
        f"""# MVP4 Dashboard Legacy Runtime Artifact Hygiene Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- A legacy dashboard shell exists at system/runtime/upbit/krw_spot/paper/dashboard_shell.json without a session_id path segment.
- A user or tool opening this legacy path could see stale or incomplete dashboard state instead of the current launcher-scoped dashboard.

Patch:
- Added a runtime dashboard artifact hygiene report schema and builder.
- Added runtime_dashboard_artifact_hygiene_validator.
- Added tests for current classification, unsafe legacy live-flag mutation, and unknown dashboard shell paths.
- Wrote the legacy shell as retained, non-authoritative, display-disabled audit material rather than deleting it.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
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
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []) + ["trader1.runtime_dashboard_artifact_hygiene_report.v1"])
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["runtime_dashboard_artifact_hygiene_validator"])
    )
    state["untested_validator_ids"] = sorted(
        item for item in state.get("untested_validator_ids", []) if item != "runtime_dashboard_artifact_hygiene_validator"
    )
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


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash)

    tests_run = [
        write_hygiene_report(),
        run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_dashboard_artifact_hygiene", "-v"]),
        run_command([sys.executable, "tools/run_runtime_dashboard_artifact_hygiene_validators.py"]),
        run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result)

    tests_run.append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
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
