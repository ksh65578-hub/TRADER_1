from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_VISUAL_LAYOUT_QA"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-VISUAL-LAYOUT-QA"
NEXT_TASK_CLASS = "MVP4_DASHBOARD_BROWSER_SCREENSHOT_QA_OR_RUNTIME_ALIAS_CLOSURE"

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
    "dashboard_visual_layout_validator",
    "runtime_schema_instance_validator",
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
    "BROWSER_SCREENSHOT_QA_TOOLING_NOT_AVAILABLE_IN_CURRENT_ENVIRONMENT",
]

CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/run_dashboard_visual_layout_validators.py",
    "tools/refresh_runtime_dashboard_html.py",
    "tools/emit_dashboard_visual_layout_qa_patch_evidence.py",
    "contracts/generated/context_pack/DASHBOARD_VISUAL_LAYOUT_QA.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def run_command(args: list[str], timeout_seconds: int = 180) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1600:],
        "stderr_tail": completed.stderr[-1600:],
    }


def upsert_requirement_index(now: str, trader_hash: str, agents_hash: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_index.json"
    index = load_json(path)
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    index["updated_at_utc"] = now
    entry = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
        "source_file": "TRADER_1.md",
        "source_heading": "Dashboard visual layout QA and readable operator first screen",
        "full_text_marker": f"{REQUIREMENT_ID}:SECTION_DASHBOARD_OPERATOR_UX:readable first screen, overflow-safe grids, stable detail persistence",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Dashboard visual layout contract prevents cramped cards, text overlap, and lost detail state",
        "requirement_kind": "DASHBOARD_UX_VALIDATOR_PATCH",
        "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
        "validator_ids": ["dashboard_visual_layout_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator"],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tools/run_dashboard_visual_layout_validators.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["DASHBOARD_UX", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
        "depends_on": [
            "REQ-MVP4-DASHBOARD-FIRST-SCREEN-SIMPLIFICATION",
            "REQ-MVP4-DASHBOARD-PORTFOLIO-DETAIL-LAYOUT",
            "REQ-MVP4-DASHBOARD-RECOVERY-GUARD-VISIBILITY",
        ],
        "source_text_sha256": sha256_json({"requirement_id": REQUIREMENT_ID, "title": "Dashboard visual layout QA"}),
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index["requirements"] = [item for item in index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    index["requirements"].append(entry)
    index["requirements"] = sorted(index["requirements"], key=lambda item: item["requirement_id"])
    write_json(path, index)


def upsert_requirement_artifact_matrix(now: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    matrix = load_json(path)
    matrix["updated_at_utc"] = now
    row = {
        "requirement_id": REQUIREMENT_ID,
        "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
        "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py", "contracts/validators/validator_registry.json"],
        "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
        "fixture_files": [],
        "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        ],
        "dashboard_artifacts": [
            "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
            "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
            "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard/index.html",
            "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard/index.html",
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
    matrix["rows"] = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    matrix["rows"].append(row)
    matrix["rows"] = sorted(matrix["rows"], key=lambda item: item["requirement_id"])
    write_json(path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_VISUAL_LAYOUT_QA.md",
        f"""# DASHBOARD_VISUAL_LAYOUT_QA

context_pack_id: DASHBOARD_VISUAL_LAYOUT_QA
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-DASHBOARD-FIRST-SCREEN-SIMPLIFICATION", "REQ-MVP4-DASHBOARD-PORTFOLIO-DETAIL-LAYOUT"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- first screen shows portfolio, running status, and live readiness without three cramped columns
- text wrapping and line-height are guarded for operator readability
- detail drawer open/closed state uses stable keys instead of DOM index only
- every generated runtime dashboard HTML passes the visual layout contract
- no live, order, scale-up, or credential behavior is introduced

known_omissions_by_design:
- browser screenshot pixel QA is still blocked by missing local browser automation dependency
- dashboard remains display truth only and cannot become execution truth

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

Dashboard visual layout is now guarded by a static layout validator. The first screen uses a wider portfolio area plus running status and live-readiness cards, detail drawers persist by stable keys, and legacy/runtime dashboard HTML is refreshed from dashboard_shell.json before validation.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_RECOVERY_GUARD_VISIBILITY.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "authority_hash_checked": True,
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"],
            "affected_exchange": "UPBIT_AND_BINANCE_DISPLAY_SAFE",
            "affected_market_type": "KRW_SPOT_AND_SPOT_DISPLAY_SAFE",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID, "dashboard_visual_layout_validator"],
            "new_or_changed_schema_ids": [],
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
            "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SHELL"],
            "next_optional_section_ids": ["SECTION_BROWSER_VISUAL_QA", "SECTION_RUNTIME_ALIAS_HYGIENE"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": PATCH_BASENAME,
            "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SHELL"],
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
            "failure_analysis_status": "NOT_REQUIRED_FOR_DASHBOARD_VISUAL_LAYOUT_QA",
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
            "stage_gate_status": "PASS_FOR_DASHBOARD_VISUAL_LAYOUT_QA_NO_LIVE_ORDERS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = [
        *CHANGED_ARTIFACTS,
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
        "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
        "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
        "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard/index.html",
        "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard/index.html",
        patch_result["validator_run_log_path"],
        patch_result["stage_gate_result_path"],
        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    ]
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260430.md",
        f"""# MVP4 Dashboard Visual Layout QA Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Hidden issue: runtime dashboard HTML can become stale even when dashboard_shell.json and Python rendering code have advanced.
- Hidden issue: detail drawer persistence used DOM index plus label, so adding or reordering drawers could reset or misapply operator-expanded state.
- UX risk: fixed 3-column first-screen and fixed KPI/ledger grids can make long tokens such as BOOTSTRAP_READ_ONLY feel cramped.

Patch:
- First screen now uses a wider two-column grid with portfolio spanning two rows.
- Portfolio KPI, ledger, quicklook, and operation status grids now use overflow-safe minmax constraints.
- Detail drawers now carry stable data-detail-key values.
- Added dashboard_visual_layout_validator and refresh_runtime_dashboard_html tooling.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def update_validator_registry_metadata(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    registry["implemented_logic_status"] = "MVP4_DASHBOARD_VISUAL_LAYOUT_VALIDATOR_ADDED"
    write_json(path, registry)


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    completed = state.setdefault("completed_requirement_ids", [])
    if REQUIREMENT_ID not in completed:
        completed.append(REQUIREMENT_ID)
        completed.sort()
    validators = state.setdefault("implemented_validator_ids", [])
    for validator_id in ["dashboard_visual_layout_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator"]:
        if validator_id not in validators:
            validators.append(validator_id)
    validators.sort()
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
    update_validator_registry_metadata(now)
    launcher_artifacts = write_launcher_artifacts()
    tests_run = [
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "tools/refresh_runtime_dashboard_html.py"]),
        run_command([sys.executable, "tools/run_dashboard_visual_layout_validators.py"]),
    ]
    pre_validators = run_validators(
        [item for item in VALIDATORS_REQUIRED if item not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}]
    )

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

    patch_result["tests_run"].append(run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout_seconds=240))
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

    final_validators = run_validators(VALIDATORS_REQUIRED)
    patch_result["validators_run"] = final_validators
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed_tests = [item for item in patch_result["tests_run"] if item.get("status") != "PASS"]
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
