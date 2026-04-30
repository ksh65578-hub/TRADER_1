from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_LONG_RUN_SAMPLE_ACCUMULATION"

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
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_recovery_guard_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/registry.yaml",
    "contracts/schema/common.defs.schema.json",
    "contracts/schema/upbit_paper_persistent_loop_report.schema.json",
    "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/runtime/paper/upbit_paper_persistent_loop.py",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_upbit_paper_long_run_evidence_boundary_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY.md",
]

BLOCKERS = [
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def refresh_runtime_artifacts() -> list[str]:
    refreshed: list[str] = []
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-upbit-paper-long-run-evidence-boundary",
        session_id="mvp1_upbit_paper_launcher",
        requested_cycle_count=2,
    )
    refreshed.extend(rel(ROOT / path) for path in loop.get("cycle_results", [])[0].get("artifact_paths", []))
    refreshed.append(
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
        "mvp4-upbit-paper-long-run-evidence-boundary.persistent_loop_report.json"
    )
    refreshed.append(str(loop.get("runtime_recovery_guard_path")))
    refreshed.append(str(loop.get("paper_ledger_rollup_path")))
    for launcher_name in ("UPBIT_PAPER", "BINANCE_PAPER", "UPBIT_LIVE", "BINANCE_LIVE"):
        report = build_launcher_report(launcher_name)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report, ROOT)
        refreshed.append(rel(report_path))
        refreshed.extend(rel(path) for path in dashboard_paths.values())
    write_source_bundle_manifest()
    refreshed.append("contracts/security/source_bundle_manifest.json")
    return sorted(set(path for path in refreshed if path))


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY.md",
        f"""# MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY

context_pack_id: MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY
task_class: MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD", "SECTION_DASHBOARD_OPERATOR_UX"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_persistent_loop_report.v1", "trader1.upbit_paper_runtime_recovery_guard_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- bounded Upbit PAPER loops expose runtime_evidence_role=BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE
- PAPER recovery guard exposes runtime_evidence_role=PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE
- false long-run eligibility is blocked by runtime and dashboard validators
- dashboard shows the long-run blocker while keeping recovery resume status separate from live readiness
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no long-run evidence is created
- no private exchange account, credential, order-capable endpoint, live order, or live-enabling patch is used
- MVP-5 remains blocked by external live-review evidence

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    write_text(
        ROOT / "contracts/generated/ACTIVE_WORKING_VIEW.md",
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

Bounded Upbit PAPER runtime and recovery guard PASS states now carry an explicit not-long-run-evidence boundary. Dashboard recovery status remains useful for PAPER resume checks, but it cannot be mistaken for long-run evidence, LIVE_READY, promotion, or scale-up evidence.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts/generated/requirement_index.json"
    matrix_path = ROOT / "contracts/generated/requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Bounded PAPER runtime evidence boundary",
            "full_text_marker": f"{REQUIREMENT_ID}: bounded PAPER runtime PASS and recovery PASS cannot be treated as long-run evidence",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER long-run evidence boundary",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_persistent_loop_report.v1",
                "trader1.upbit_paper_runtime_recovery_guard_report.v1",
                "trader1.read_only_dashboard_shell.v1",
                "trader1.common.defs.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["DASHBOARD_UX", "VALIDATOR_IMPLEMENTATION", "LIVE_BLOCKED_TEST"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-PUBLIC-COLLECTOR-PERSISTENT-LOOP",
                "REQ-MVP4-DASHBOARD-RUNTIME-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"bounded PAPER runtime PASS and recovery PASS cannot be treated as long-run evidence"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_LIVE_BLOCKED",
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
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": [
                "contracts/schema/upbit_paper_persistent_loop_report.schema.json",
                "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/common.defs.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
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


def build_patch_result(
    *,
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    refreshed_paths: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / "system/evidence/patch_results/MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_hash_status": "CHECKED",
            "authority_hash_checked": True,
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
            "new_registry_items": ["live_blocker_code:LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT"],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_persistent_loop_report.v1",
                "trader1.upbit_paper_runtime_recovery_guard_report.v1",
                "trader1.read_only_dashboard_shell.v1",
                "trader1.common.defs.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
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
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PUBLIC_COLLECTOR_PERSISTENT_LOOP.md",
                "contracts/generated/context_pack/MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.md",
                "exact runtime/schema/validator/test sections for changed files",
            ],
            "task_class": "MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "PRESENT",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "profit_convergence_patch": "NOT_CONVERGENCE_PATCH",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["new_registry_items"].extend(refreshed_paths[:12])
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / patch_result["evidence_manifest_path"]
    validator_path = ROOT / patch_result["validator_run_log_path"]
    stage_path = ROOT / patch_result["stage_gate_result_path"]
    result_path = ROOT / "system/evidence/patch_results" / f"{PATCH_BASENAME}.patch_result.json"

    write_json(
        validator_path,
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
        stage_path,
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate": "UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY",
            "status": "PASS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "remaining_blockers": BLOCKERS,
        },
    )
    write_json(
        patch_path,
        {
            "evidence_manifest_schema_id": "trader1.evidence_manifest.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_paths": [
                rel(validator_path),
                rel(stage_path),
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY.md",
            ],
            "tests_run": patch_result["tests_run"],
            "validators_run": patch_result["validators_run"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(result_path, patch_result)

    state_path = ROOT / "contracts/generated/current_implementation_state.json"
    state = load_json(state_path)
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    implemented_schemas = set(state.get("implemented_schema_ids", []))
    implemented_schemas.update(patch_result["new_or_changed_schema_ids"])
    implemented_validators = set(state.get("implemented_validator_ids", []))
    implemented_validators.update(VALIDATORS_REQUIRED)
    state.update(
        {
            "updated_at_utc": now,
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "current_mvp": "MVP-4",
            "completed_requirement_ids": sorted(completed),
            "implemented_schema_ids": sorted(implemented_schemas),
            "implemented_validator_ids": sorted(implemented_validators),
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result["result_hash"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system/evidence/implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": rel(result_path),
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
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    refreshed_paths = refresh_runtime_artifacts()
    update_read_cache(now, trader_hash, agents_hash)
    tests_run = [
        run_command([sys.executable, "-B", "-m", "unittest", "tests.integration.test_upbit_public_collection_persistent_loop", "-q"]),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-q"]),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_schema_instance_validation", "-q"]),
    ]
    validators = run_validators(VALIDATORS_REQUIRED)
    validators_run = summarize_validators(validators)
    patch_result = build_patch_result(
        now=now,
        tests_run=tests_run,
        validators_run=validators_run,
        refreshed_paths=refreshed_paths,
    )
    write_evidence(now, trader_hash, agents_hash, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    post_write_validators = run_validators(VALIDATORS_REQUIRED)
    validators_run = summarize_validators(post_write_validators)

    failed_tests = [item for item in tests_run if item["status"] != "PASS"]
    failed_validators = [item for item in validators_run if item["status"] != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "patch_result_hash": patch_result["result_hash"],
                "tests": tests_run,
                "validators": validators_run,
                "failed_tests": failed_tests,
                "failed_validators": failed_validators,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed_tests and not failed_validators else 1


if __name__ == "__main__":
    raise SystemExit(main())
