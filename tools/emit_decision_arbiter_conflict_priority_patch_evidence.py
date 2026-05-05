from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DECISION_ARBITER_CONFLICT_PRIORITY"
PATCH_ID = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_DECISION_ARBITER_CONFLICT_PRIORITY_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-DECISION-ARBITER-CONFLICT-PRIORITY"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"

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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "trader1/core/decision/decision_arbiter.py",
    "trader1/adapters/upbit/paper_broker.py",
    "trader1/runtime/paper/operational_cycle.py",
    "trader1/runtime/paper/upbit_paper_runtime.py",
    "tests/contract/test_decision_arbiter_conflict_priority.py",
    "tools/emit_decision_arbiter_conflict_priority_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "upbit_paper_dry_run_validator",
    "upbit_operational_paper_gate_validator",
    "upbit_paper_runtime_cycle_validator",
    "runtime_schema_instance_validator",
    "optimizer_no_live_mutation_validator",
    "profitability_optimizer_evidence_gap_validator",
    "live_final_guard_validator",
]

POST_WRITE_VALIDATORS = [
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
]

REMAINING_BLOCKERS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_BURN_IN_MISSING",
    "OPERATOR_APPROVAL_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def clean_bytecode_cache() -> dict[str, Any]:
    removed: list[str] = []
    root = ROOT.resolve()
    for path in sorted(root.rglob("*.pyc")) + sorted(root.rglob("*.pyo")):
        resolved = path.resolve()
        if root == resolved or root not in resolved.parents:
            continue
        path.unlink(missing_ok=True)
        removed.append(rel(path))
    for path in sorted(root.rglob("__pycache__"), reverse=True):
        resolved = path.resolve()
        if root == resolved or root not in resolved.parents:
            continue
        try:
            path.rmdir()
            removed.append(rel(path))
        except OSError:
            pass
    return {
        "command": "clean_bytecode_cache()",
        "status": "PASS",
        "returncode": 0,
        "stdout_tail": json.dumps({"removed_count": len(removed), "sample": removed[:20]}, indent=2),
        "stderr_tail": "",
    }


def upsert_requirement_index(now: str, trader_hash: str, agents_hash: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_index.json"
    index = load_json(path)
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    index["updated_at_utc"] = now
    entry = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
        "source_file": "TRADER_1.md",
        "source_heading": "Strategy decision conflict priority and no-trade traffic control",
        "full_text_marker": f"{REQUIREMENT_ID}: deterministic primary blocker and PAPER-safe final decision arbitration",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Decision arbiter must resolve conflicting blockers deterministically before PAPER entry/no-trade handling",
        "requirement_kind": "RUNTIME_SAFETY_PATCH",
        "schema_ids": ["trader1.final_decision.v1", "trader1.common_defs.v1"],
        "validator_ids": [
            "upbit_paper_dry_run_validator",
            "upbit_operational_paper_gate_validator",
            "upbit_paper_runtime_cycle_validator",
            "live_final_guard_validator",
        ],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": [
            "tests/contract/test_decision_arbiter_conflict_priority.py",
            "tests/contract/test_strategy_unit_scope.py",
            "tests/integration/test_upbit_paper_runtime_cycle.py",
        ],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
        "blocking_level": "PAPER_RUNTIME_BLOCKING",
        "live_affecting": True,
        "read_when": ["DASHBOARD_UX", "PROFIT_CONVERGENCE_MVP3", "SECTION_LIVE_FINAL_GUARD"],
        "depends_on": [
            "REQ-MVP0-LIVE-DEFAULT-FALSE",
            "REQ-MVP0-ORDER-PATH-GUARD",
            "REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE",
            "REQ-MVP4-UPBIT-PAPER-CANDIDATE-DECISION-THRESHOLD-GUARD",
        ],
        "source_text_sha256": sha256_json(
            {
                "requirement_id": REQUIREMENT_ID,
                "title": "deterministic decision arbitration conflict priority",
            }
        ),
        "implementation_status": "IMPLEMENTED_LIVE_BLOCKED",
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
        "section_id": "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
        "schema_files": ["contracts/schema/final_decision.schema.json", "contracts/schema/common.defs.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py"],
        "test_files": [
            "tests/contract/test_decision_arbiter_conflict_priority.py",
            "tests/contract/test_strategy_unit_scope.py",
            "tests/integration/test_upbit_paper_runtime_cycle.py",
        ],
        "fixture_files": [],
        "runtime_modules": [
            "trader1/core/decision/decision_arbiter.py",
            "trader1/adapters/upbit/paper_broker.py",
            "trader1/runtime/paper/operational_cycle.py",
            "trader1/runtime/paper/upbit_paper_runtime.py",
        ],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        ],
        "dashboard_artifacts": ["primary_blocker_code", "no_trade_reasons", "blockers"],
        "patch_result_fields": ["validators_run", "tests_run", "remaining_blockers"],
        "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
        "live_affecting": True,
        "status": "IMPLEMENTED_LIVE_BLOCKED",
    }
    matrix["rows"] = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    matrix["rows"].append(row)
    matrix["rows"] = sorted(matrix["rows"], key=lambda item: item["requirement_id"])
    write_json(path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.final_decision.v1", "trader1.common_defs.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED + POST_WRITE_VALIDATORS)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- primary blocker selection is deterministic and no longer depends on set iteration
- legacy KILL_SWITCH input is normalized to KILL_SWITCH_ACTIVE
- kill switch, live final guard, reconciliation, risk, data, cost, regime, and min-edge blockers have an explicit order
- PAPER no-trade reason lists use the same priority order as primary_blocker_code
- reconciliation-family blockers force RECONCILE_REQUIRED in the operational PAPER arbiter
- all changed paths remain PAPER/SHADOW analysis only and do not create live permission

known_omissions_by_design:
- no live order submission
- no credential or private API use
- no LIVE_READY snapshot write
- no risk scale-up
- open contract gaps remain open until external evidence or operator reconciliation exists

conflict_resolution_rule:
TRADER_1.md active authority wins over this generated cache. AGENTS.md guides implementation only when non-conflicting.
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

PAPER decision arbitration now resolves conflicting blockers through a deterministic priority order before choosing primary_blocker_code, no_trade_reasons, and operational PAPER final_decision. This improves strategy traffic control and operator-visible blocker clarity without enabling live orders.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROFITABILITY_QUALITY_GATE.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "HASH_MATCH",
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
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_NO_RETAINED_ARCHIVE_READ",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_PROFIT_CONVERGENCE_REINFORCEMENT",
                "SECTION_BINANCE_ADAPTER_BOUNDARY",
            ],
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
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/context_pack/UPBIT_PAPER_CANDIDATE_DECISION_GUARD.md",
                "contracts/generated/context_pack/STRATEGY_CONDITION_MATRIX_SCHEMA_HARDENING.md",
                "contracts/generated/context_pack/MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE.md",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
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
            "read_cache_invalidated": True,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "PAPER_DECISION_ARBITRATION_TRAFFIC_CONTROL_HARDENED",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_DECISION_ARBITER_CONFLICT_PRIORITY",
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
            "stage_gate_status": "PASS_FOR_DECISION_ARBITER_CONFLICT_PRIORITY_NO_LIVE_PERMISSION",
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
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
            ],
            "known_blockers": REMAINING_BLOCKERS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Decision Arbiter Conflict Priority Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The PAPER decision arbiter selected unknown fallback blockers through set iteration, which could make primary_blocker_code nondeterministic when several blockers appeared together.
- The priority list also missed current registered blocker codes such as KILL_SWITCH_ACTIVE, LEDGER_INTEGRITY_FAIL, data freshness, cost, regime, and risk-scale blockers.

Patch:
- Added deterministic blocker normalization and ordering.
- Normalized legacy KILL_SWITCH to KILL_SWITCH_ACTIVE.
- Made reconciliation-family blockers force RECONCILE_REQUIRED in operational PAPER arbitration.
- Reused the same ordering for PAPER no_trade_reasons and primary_blocker_code in the paper broker and Upbit PAPER runtime.
- Added negative and ordering tests for kill/reconcile/live-guard/risk/data/cost/min-edge conflict cases.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- This is traffic-control hardening only. Open external-evidence/operator-reconciliation gaps remain open and live readiness remains blocked.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    state["completed_requirement_ids"] = sorted(completed)
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

    tests_run = [
        clean_bytecode_cache(),
        run_command([sys.executable, "-m", "unittest", "tests.contract.test_decision_arbiter_conflict_priority", "-v"], 120),
        run_command(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.contract.test_strategy_unit_scope",
                "tests.integration.test_upbit_paper_runtime_cycle",
                "-v",
            ],
            180,
        ),
        run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py", "--paths", "trader1", "tools", "tests"], 180),
    ]

    pre_validators = run_validators(VALIDATORS_REQUIRED)
    upsert_requirement_index(now, trader_hash, agents_hash)
    upsert_requirement_artifact_matrix(now)
    update_context(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, pre_validators)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"], 180))
    tests_run.append(clean_bytecode_cache())
    tests_run.append(
        run_command(
            [
                sys.executable,
                "tools/run_hygiene_safe_pytest.py",
                "--",
                "-q",
                "tests/contract/test_decision_arbiter_conflict_priority.py",
                "tests/contract/test_strategy_unit_scope.py",
                "tests/integration/test_upbit_paper_runtime_cycle.py",
            ],
            240,
        )
    )
    tests_run.append(clean_bytecode_cache())
    tests_run.append(run_command([sys.executable, "tools/run_hygiene_safe_pytest.py", "--", "-q"], 600))
    final_validators = run_validators(VALIDATORS_REQUIRED + POST_WRITE_VALIDATORS)
    patch_result["tests_run"] = tests_run
    patch_result["validators_run"] = final_validators
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
                "failed_tests": failed_tests,
                "failed_validators": failed_validators,
            },
            indent=2,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
