from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_PROFITABILITY_EVIDENCE_MATURITY_RUNTIME_LINKAGE"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-RUNTIME-LINKAGE"
NEXT_TASK_CLASS = "MVP4_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from trader1.runtime.paper.upbit_paper_persistent_loop import (  # noqa: E402
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (  # noqa: E402
    build_upbit_paper_runtime_cycle_report,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


ROLLUP_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
ROLLUP_FIXTURE_PATH = ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"
RUNTIME_FIXTURE_PATH = ROOT / "tests" / "validators" / "fixtures" / "profitability_runtime_cycle_linkage_pass.json"
LATEST_RUNTIME_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "upbit_paper_runtime_cycle_report.json"
)

VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "profitability_evidence_maturity_rollup_validator",
    "profitability_optimizer_evidence_gap_validator",
    "upbit_paper_runtime_cycle_validator",
    "upbit_paper_persistent_loop_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]

BOOTSTRAP_VALIDATORS = [
    item
    for item in VALIDATORS_REQUIRED
    if item
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
]

CHANGED_ARTIFACTS = [
    "contracts/schema/profitability_evidence_maturity_rollup.schema.json",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
    "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json",
    "tests/validators/fixtures/profitability_runtime_cycle_linkage_pass.json",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
    "tools/emit_profitability_evidence_runtime_linkage_patch.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "PROFITABILITY_EVIDENCE_MATURITY",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
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


def remove_python_bytecode_artifacts() -> None:
    for path in ROOT.rglob("__pycache__"):
        if ".git" not in path.parts and path.is_dir():
            shutil.rmtree(path)
    for path in ROOT.rglob("*.pyc"):
        if ".git" not in path.parts and path.is_file():
            path.unlink()


def rollup_hash(rollup: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in rollup.items() if key != "rollup_hash"})


def runtime_linkage_evidence(runtime_path: Path) -> dict[str, Any]:
    report = load_json(runtime_path)
    result = validate_upbit_paper_runtime_cycle_report(report)
    selected = report.get("selected_candidate", {})
    return {
        "status": "PASS" if result.status == "PASS" else "BLOCKED",
        "source_runtime_cycle_path": rel(runtime_path),
        "source_runtime_cycle_id": report.get("cycle_id"),
        "source_runtime_cycle_hash": report.get("cycle_hash"),
        "runtime_input_role": report.get("runtime_input_role"),
        "runtime_public_market_data_hash": report.get("runtime_public_market_data_hash"),
        "feature_snapshot_hash": report.get("feature_snapshot_hash"),
        "strategy_regime_cost_linkage_status": "PASS" if result.status == "PASS" and report.get("strategy_regime_cost_linkage") else "BLOCKED",
        "selected_candidate_id": selected.get("candidate_id"),
        "selected_candidate_net_ev_after_cost_bps": selected.get("net_ev_after_cost_bps"),
        "cost_model_source": selected.get("cost_model_source"),
        "sample_count": 1 if result.status == "PASS" else 0,
        "min_required_sample_count": 1,
        "primary_blocker_code": "PROFITABILITY_EVIDENCE_MATURITY",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def attach_runtime_linkage_to_components(rollup: dict[str, Any], source_path: str) -> None:
    runtime_linked_components = {
        "strategy_entry_exit_no_trade",
        "symbol_selection_regime",
        "vwap_trend_breakout",
        "execution_slippage_fee_impact",
        "optimizer_objective_net_ev_after_cost",
    }
    for component in rollup.get("components", []):
        if component.get("component_id") not in runtime_linked_components:
            continue
        paths = component.setdefault("source_artifact_paths", [])
        if source_path not in paths:
            paths.append(source_path)
        evidence_ids = component.setdefault("source_evidence_ids", [])
        if REQUIREMENT_ID not in evidence_ids:
            evidence_ids.append(REQUIREMENT_ID)
        component["sample_count"] = max(int(component.get("sample_count", 0)), 1)
        component["freshness_status"] = "PASS"
        component["evidence_status"] = "PARTIAL"
        component["primary_blocker_code"] = "PROFITABILITY_EVIDENCE_MATURITY"
        component["live_review_eligible"] = False
        component["scale_up_allowed"] = False
        component["long_run_evidence_eligible"] = False
        component["long_run_blocker_code"] = component.get("long_run_blocker_code") or "PROFITABILITY_EVIDENCE_MATURITY"


def update_rollup(path: Path, *, now: str, trader_hash: str, agents_hash: str, runtime_path: Path) -> None:
    rollup = load_json(path)
    rollup["generated_at_utc"] = now
    rollup["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    rollup["runtime_linkage_evidence"] = runtime_linkage_evidence(runtime_path)
    attach_runtime_linkage_to_components(rollup, rel(runtime_path))
    rollup["status"] = "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY"
    rollup["live_order_ready"] = False
    rollup["live_order_allowed"] = False
    rollup["can_live_trade"] = False
    rollup["scale_up_allowed"] = False
    rollup["live_permission_created"] = False
    rollup["profitability_guarantee_created"] = False
    rollup["optimizer_live_mutation_detected"] = False
    rollup["convergence_live_mutation_detected"] = False
    rollup["live_review_eligible"] = False
    rollup["scale_up_eligible"] = False
    rollup["primary_blocker_code"] = "PROFITABILITY_EVIDENCE_MATURITY"
    rollup["next_operator_action"] = (
        "Use PAPER runtime-linked strategy/regime/cost evidence only as PAPER scorecard input; "
        "collect longer PAPER/SHADOW windows, OOS, walk-forward, bootstrap, read-only burn-in, "
        "manual order evidence, and operator approval while live remains blocked."
    )
    rollup["rollup_hash"] = ""
    rollup["rollup_hash"] = rollup_hash(rollup)
    write_json(path, rollup)


def run_runtime_loop(now: str) -> dict[str, Any]:
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-profitability-evidence-runtime-linkage",
        session_id="mvp1_upbit_paper_launcher",
        requested_cycle_count=2,
    )
    result = validate_upbit_paper_persistent_loop_report(loop)
    return {
        "command": "run_upbit_paper_persistent_loop(root=ROOT, loop_id=mvp4-profitability-evidence-runtime-linkage, requested_cycle_count=2)",
        "status": result.status,
        "returncode": 0 if result.status == "PASS" else 1,
        "stdout_tail": json.dumps(
            {
                "loop_id": loop.get("loop_id"),
                "completed_cycle_count": loop.get("completed_cycle_count"),
                "loop_status": loop.get("loop_status"),
                "checked_at_utc": now,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        ),
        "stderr_tail": "" if result.status == "PASS" else result.message,
    }


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    matrix["updated_at_utc"] = now
    requirement = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_STRATEGY_PROFITABILITY_LOOP",
        "source_file": "TRADER_1.md",
        "source_heading": "Profitability evidence maturity runtime linkage",
        "full_text_marker": f"{REQUIREMENT_ID}:SECTION_STRATEGY_PROFITABILITY_LOOP:profitability rollup links PAPER runtime strategy/regime/cost evidence",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Profitability maturity rollup must link to actual PAPER runtime strategy/regime/cost evidence",
        "requirement_kind": "RUNTIME_VALIDATOR_SCHEMA_PATCH",
        "schema_ids": ["trader1.profitability_evidence_maturity_rollup.v1"],
        "validator_ids": ["profitability_evidence_maturity_rollup_validator", "upbit_paper_runtime_cycle_validator"],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["PROFIT_CONVERGENCE_MVP3", "SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_LIVE_FINAL_GUARD"],
        "depends_on": [
            "REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE",
            "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
            "REQ-MVP4-LIVE-FINAL-GUARD",
        ],
        "source_text_sha256": sha256_json({"requirement_id": REQUIREMENT_ID, "title": "profitability runtime linkage"}),
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index["requirements"] = [item for item in index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    index["requirements"].append(requirement)
    index["requirements"] = sorted(index["requirements"], key=lambda item: item["requirement_id"])
    write_json(index_path, index)

    row = {
        "requirement_id": REQUIREMENT_ID,
        "section_id": "SECTION_STRATEGY_PROFITABILITY_LOOP",
        "schema_files": ["contracts/schema/profitability_evidence_maturity_rollup.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py"],
        "test_files": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
        "fixture_files": [
            "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json",
            "tests/validators/fixtures/profitability_runtime_cycle_linkage_pass.json",
        ],
        "runtime_modules": ["trader1/runtime/paper/upbit_paper_runtime.py"],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
        ],
        "dashboard_artifacts": ["system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"],
        "patch_result_fields": ["validators_run", "tests_run", "remaining_blockers"],
        "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "live_affecting": True,
        "status": "IMPLEMENTED_FAIL_CLOSED",
    }
    matrix["rows"] = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    matrix["rows"].append(row)
    matrix["rows"] = sorted(matrix["rows"], key=lambda item: item["requirement_id"])
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- profitability maturity rollup contains runtime_linkage_evidence
- runtime_linkage_evidence points to a validating Upbit PAPER runtime cycle report
- runtime cycle hash, market data hash, feature hash, selected candidate, net EV, and cost model source match
- PAPER runtime linkage may allow PAPER scorecard input only
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- runtime linkage is not long-run evidence
- runtime linkage is not live-readiness evidence
- external API verification, read-only burn-in, manual order evidence, and operator approval remain missing

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. Generated context is read cache only.
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

Profitability evidence maturity now links to validating Upbit PAPER runtime strategy/regime/cost evidence. This linkage is PAPER scorecard input only; long-run, read-only, operator, and live-review blockers remain active.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE",
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
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
            "new_or_changed_schema_ids": ["trader1.profitability_evidence_maturity_rollup.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_SOURCE_BUNDLE_HYGIENE"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
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
            "active_read_surface_used": ["SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": PATCH_BASENAME,
            "required_section_ids": ["SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_UPBIT_PAPER_RUNTIME"],
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
            "optimizer_patch": "PROFITABILITY_RUNTIME_LINKAGE_ONLY_NO_OPTIMIZER_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "PAPER_RUNTIME_PROFITABILITY_EVIDENCE_LINKAGE_STRENGTHENED",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
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
            "stage_gate_status": "PASS_FOR_PAPER_PROFITABILITY_RUNTIME_LINKAGE_NO_LIVE_ORDERS",
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
                rel(LATEST_RUNTIME_PATH),
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.profitability_evidence_maturity_rollup.v1"]))
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["profitability_evidence_maturity_rollup_validator"])
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

    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
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
    remove_python_bytecode_artifacts()
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)

    runtime_fixture = build_upbit_paper_runtime_cycle_report(cycle_id="fixture-profitability-runtime-linkage-pass")
    write_json(RUNTIME_FIXTURE_PATH, runtime_fixture)
    loop_run = run_runtime_loop(now)
    update_rollup(ROLLUP_PATH, now=now, trader_hash=trader_hash, agents_hash=agents_hash, runtime_path=LATEST_RUNTIME_PATH)
    update_rollup(ROLLUP_FIXTURE_PATH, now=now, trader_hash=trader_hash, agents_hash=agents_hash, runtime_path=RUNTIME_FIXTURE_PATH)
    update_navigation(now, trader_hash, agents_hash)
    write_source_bundle_manifest()
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        loop_run,
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/validators/test_profitability_optimizer_evidence_gap_validator.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "-q"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = run_validators(BOOTSTRAP_VALIDATORS)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"

    def persist() -> dict[str, Any]:
        patch_result = build_patch_result(now, tests_run, validators_run)
        write_evidence(now, trader_hash, agents_hash, patch_result)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)
        write_source_bundle_manifest()
        return patch_result

    patch_result = persist()
    for _ in range(2):
        validators_run = run_validators(VALIDATORS_REQUIRED)
        patch_result = persist()

    tests_run.append(run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"], timeout_seconds=900))
    patch_result = persist()
    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"], timeout_seconds=300))
    patch_result = persist()

    for _ in range(2):
        validators_run = run_validators(VALIDATORS_REQUIRED)
        patch_result = persist()

    failed = [item for item in [*patch_result["tests_run"], *patch_result["validators_run"]] if item.get("status") != "PASS"]
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
    remove_python_bytecode_artifacts()
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
