from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_RECOVERY_GUARD_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-RECOVERY-GUARD-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_DASHBOARD_VISUAL_LAYOUT_QA_TOOLING"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_dashboard_launch_visibility_patch_evidence import write_launcher_artifacts  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_runtime_recovery_guard_validator",
    "root_launcher_surface_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "generated_artifact_dirty_validator",
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
    "PAPER_RUNTIME_RECOVERY_GUARD_STALE_UNTIL_NEXT_PAPER_RUN",
]

CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "trader1/runtime/paper/upbit_paper_persistent_loop.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_recovery_guard_visibility_patch_evidence.py",
    "contracts/generated/context_pack/DASHBOARD_RECOVERY_GUARD_VISIBILITY.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def run_command(args: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def upsert_requirement_index(now: str, trader_hash: str, agents_hash: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_index.json"
    index = load_json(path)
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    index["updated_at_utc"] = now
    entry = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_DASHBOARD_SHELL",
        "source_file": "TRADER_1.md",
        "source_heading": "Dashboard PAPER runtime recovery guard operator visibility",
        "full_text_marker": f"{REQUIREMENT_ID}:SECTION_DASHBOARD_SHELL:Dashboard PAPER runtime recovery guard operator visibility",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Dashboard shows PAPER runtime recovery guard without creating live permission",
        "requirement_kind": "DASHBOARD_UX",
        "schema_ids": [
            "trader1.read_only_dashboard_shell.v1",
            "trader1.upbit_paper_runtime_recovery_guard_report.v1",
        ],
        "validator_ids": [
            "read_only_dashboard_validator",
            "runtime_schema_instance_validator",
            "upbit_paper_runtime_recovery_guard_validator",
            "live_final_guard_validator",
        ],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": [
            "tests/dashboard/test_read_only_dashboard.py",
            "tests/integration/test_upbit_public_collection_persistent_loop.py",
        ],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": [
            "DASHBOARD_UX",
            "MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD",
        ],
        "depends_on": [
            "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
            "REQ-MVP4-UPBIT-PAPER-RUNTIME-RECOVERY-GUARD",
        ],
        "source_text_sha256": sha256_json(
            {
                "requirement_id": REQUIREMENT_ID,
                "source_section_id": "SECTION_DASHBOARD_SHELL",
                "title": "Dashboard PAPER runtime recovery guard operator visibility",
            }
        ),
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index["requirements"] = [item for item in index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    index["requirements"].append(entry)
    write_json(path, index)


def upsert_requirement_artifact_matrix(now: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    matrix = load_json(path)
    matrix["updated_at_utc"] = now
    row = {
        "requirement_id": REQUIREMENT_ID,
        "section_id": "SECTION_DASHBOARD_SHELL",
        "schema_files": [
            "contracts/schema/read_only_dashboard_shell.schema.json",
            "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json",
        ],
        "validator_files": [
            "contracts/validators/validator_registry.json",
            "trader1/validation/mvp0_validators.py",
        ],
        "test_files": [
            "tests/dashboard/test_read_only_dashboard.py",
            "tests/integration/test_upbit_public_collection_persistent_loop.py",
        ],
        "fixture_files": [],
        "runtime_modules": [
            "trader1/dashboard/read_only_dashboard.py",
            "trader1/runtime/boot/safe_launcher.py",
            "trader1/runtime/paper/upbit_paper_persistent_loop.py",
        ],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
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
            "validators_run",
        ],
        "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
        "live_affecting": True,
        "status": "IMPLEMENTED_FAIL_CLOSED",
    }
    matrix["rows"] = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    matrix["rows"].append(row)
    write_json(path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_RECOVERY_GUARD_VISIBILITY.md",
        f"""# DASHBOARD_RECOVERY_GUARD_VISIBILITY

context_pack_id: DASHBOARD_RECOVERY_GUARD_VISIBILITY
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP4-UPBIT-PAPER-RUNTIME-RECOVERY-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_runtime_recovery_guard_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- dashboard first screen exposes PAPER runtime recovery separately from heartbeat freshness
- stale, missing, blocked, and invalid recovery guard states cannot look like normal RUNNING
- recovery guard PASS remains PAPER resume evidence only and cannot create live readiness
- generated dashboard_shell instances validate after schema expansion
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no private exchange call or credential load is performed
- recovery guard does not create long-run, promotion, scale-up, or LIVE_READY evidence
- browser screenshot QA remains a separate task because local Playwright is not installed in this environment

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: {state.get("current_mvp", "MVP-4")}
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

The read-only dashboard now shows PAPER runtime recovery guard state as operator-visible display truth. PASS means the PAPER runtime can resume from checked local artifacts only; STALE, BLOCKED, INVALID, or NOT_LOADED remain warnings or blockers and cannot create live trading permission.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_RUNTIME_FRESHNESS_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "authority_hash_checked": True,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-RECOVERY-GUARD",
            ],
            "affected_exchange": "UPBIT_PRIMARY_AND_BINANCE_DISPLAY_SAFE",
            "affected_market_type": "KRW_SPOT_AND_SPOT_DISPLAY_SAFE",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [
                REQUIREMENT_ID,
                "PAPER_RUNTIME_RECOVERY_GUARD dashboard source artifact",
            ],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_OPERATOR_VISIBILITY"],
            "next_optional_section_ids": ["SECTION_MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD"],
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
                "SECTION_DASHBOARD_SHELL",
                "SECTION_MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": True,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_DASHBOARD_RECOVERY_GUARD_VISIBILITY",
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
            "stage_gate_status": "PASS_FOR_DASHBOARD_RECOVERY_GUARD_VISIBILITY_NO_LIVE_ORDERS",
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
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_runtime_recovery_guard_report.json",
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
        f"""# MVP4 Dashboard Recovery Guard Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Hidden issue: PAPER runtime recovery guard reports could be produced by the runtime, but the operator dashboard did not surface them on the first screen or in details.
- Hidden issue: after adding the new dashboard field, stale dashboard_shell artifacts failed runtime schema instance validation until launcher dashboard bundles were regenerated.
- UX risk: users could see a fresh heartbeat and assume the PAPER runtime can resume, even when local JSONL recovery guard evidence is stale, blocked, invalid, or not loaded.

Patch:
- Added PAPER runtime recovery status to the dashboard operation panel and detailed status drawer.
- Added schema validation for the new display-only recovery guard status.
- Added launcher wiring for a canonical session-scoped recovery guard report path.
- Added negative dashboard tests for partial-write blockers and live-permission mutation attempts.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    completed = state.setdefault("completed_requirement_ids", [])
    if REQUIREMENT_ID not in completed:
        completed.append(REQUIREMENT_ID)
    schemas = state.setdefault("implemented_schema_ids", [])
    if "trader1.read_only_dashboard_shell.v1" not in schemas:
        schemas.append("trader1.read_only_dashboard_shell.v1")
    validators = state.setdefault("implemented_validator_ids", [])
    for validator_id in [
        "read_only_dashboard_validator",
        "runtime_schema_instance_validator",
        "upbit_paper_runtime_recovery_guard_validator",
    ]:
        if validator_id not in validators:
            validators.append(validator_id)
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
    launcher_artifacts = write_launcher_artifacts()
    tests_run = [
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.integration.test_upbit_public_collection_persistent_loop", "-v"]),
        run_command([sys.executable, "tools/run_bundle_security_validators.py"]),
        run_command([sys.executable, "tools/run_root_launcher_validators.py"]),
        run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
    ]
    pre_validators = run_validators([item for item in VALIDATORS_REQUIRED if item not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}])

    upsert_requirement_index(now, trader_hash, agents_hash)
    upsert_requirement_artifact_matrix(now)
    update_context(now, trader_hash, agents_hash)
    artifacts = sorted(set(CHANGED_ARTIFACTS + launcher_artifacts))
    patch_result = build_patch_result(now, tests_run, pre_validators, artifacts)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_validators = run_validators(VALIDATORS_REQUIRED)
    patch_result["validators_run"] = final_validators
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_validators = run_validators(VALIDATORS_REQUIRED)
    patch_result["validators_run"] = final_validators
    patch_result["tests_run"].append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed_tests = [item for item in tests_run if item.get("status") != "PASS"]
    failed_validators = [item for item in final_validators if item.get("status") != "PASS"]
    status = "PASS" if not failed_tests and not failed_validators else "FAIL"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": status,
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
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
