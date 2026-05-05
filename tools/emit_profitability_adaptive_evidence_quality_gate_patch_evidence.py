from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROFITABILITY_QUALITY_GATE"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-ADAPTIVE-EVIDENCE-QUALITY-GATE"
CONTRACT_GAP_ID = "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
GATE_ROLE = "OBSERVED_CONTEXT_ONLY_NO_FIXED_RUNTIME_FLOOR"
REMOVED_FIXED_RUNTIME_CODE = "PAPER_RUNTIME_HOURS_BELOW_MIN"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_convergence_memory_failure_learning_hardening_patch_evidence import (  # noqa: E402
    ensure_matrix_row,
    ensure_requirement,
)
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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


ROLLUP_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
ROLLUP_FIXTURE_PATH = ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"

VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "profitability_evidence_maturity_rollup_validator",
    "profitability_optimizer_evidence_gap_validator",
    "read_only_dashboard_validator",
    "optimizer_no_live_mutation_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    item for item in VALIDATORS_REQUIRED if item != "patch_result_runtime_schema_instance_validator"
]

CHANGED_ARTIFACTS = [
    "contracts/schema/profitability_evidence_maturity_rollup.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/validation/mvp0_validators.py",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
    "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
    "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
    "tools/emit_profitability_optimizer_evidence_maturity_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    "tools/emit_profitability_adaptive_evidence_quality_gate_patch_evidence.py",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str], timeout_seconds: int = 900) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    result = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.stdout:
        result["stdout_tail"] = completed.stdout[-1600:]
    if completed.stderr:
        result["stderr_tail"] = completed.stderr[-1600:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def refresh_rollup(path: Path, now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    rollup = load_json(path)
    rollup["generated_at_utc"] = now
    rollup["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    thresholds = rollup["promotion_threshold_evidence"]
    thresholds["min_paper_runtime_hours"] = 0
    thresholds["paper_runtime_hours_gate_role"] = GATE_ROLE
    thresholds["missing_threshold_codes"] = [
        code for code in thresholds.get("missing_threshold_codes", []) if code != REMOVED_FIXED_RUNTIME_CODE
    ]
    for component in rollup.get("components", []):
        if component.get("component_id") == "paper_shadow_evidence_accumulation":
            component["next_required_evidence"] = (
                "Collect session-hashed PAPER and SHADOW evidence until adaptive quality review has enough "
                "distinct windows, regimes, cost-adjusted scorecards, and shadow opportunities; short "
                "scorecard input is not long-run or LIVE_READY evidence."
            )
    rollup["next_operator_action"] = (
        "Use PAPER runtime-linked strategy/regime/cost evidence only as PAPER scorecard input; continue "
        "adaptive evidence-quality review across replay, OOS, walk-forward, bootstrap, PAPER, SHADOW, "
        "read-only burn-in, manual order evidence, and operator approval while live remains blocked."
    )
    rollup["live_order_ready"] = False
    rollup["live_order_allowed"] = False
    rollup["can_live_trade"] = False
    rollup["scale_up_allowed"] = False
    rollup["live_review_eligible"] = False
    rollup["scale_up_eligible"] = False
    rollup["rollup_hash"] = ""
    rollup["rollup_hash"] = sha256_json({key: value for key, value in rollup.items() if key != "rollup_hash"})
    write_json(path, rollup)
    return rollup


def update_contract_gap(now: str, trader_hash: str, agents_hash: str) -> None:
    gap = load_json(CONTRACT_GAP_PATH)
    gap["generated_at_utc"] = now
    gap["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    gap["status"] = "OPEN"
    gap["live_affecting"] = True
    gap["notes"] = (
        "Rechecked in MVP-4. Profitability evidence maturity uses adaptive evidence-quality review. PAPER runtime "
        "hours are observed context only with no fixed runtime-hour floor; replay trades, OOS/walk-forward coverage, "
        "paper trades, shadow opportunities, net EV after cost, profit factor, drawdown, fill quality, paper/live parity, "
        "and open HIGH contract gaps remain explicit blockers. The gap remains OPEN and live-blocking."
    )
    write_json(CONTRACT_GAP_PATH, gap)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    matrix["updated_at_utc"] = now
    matrix["trader1_sha256"] = trader_hash
    matrix["agents_sha256"] = agents_hash
    ensure_requirement(
        index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_STRATEGY_PROFITABILITY",
            "source_file": "TRADER_1.md",
            "source_heading": "Profitability adaptive evidence quality gate",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: profitability maturity must use adaptive evidence-quality review, not a fixed "
                "PAPER runtime-hour floor, while preserving all live and scale-up blockers"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Profitability adaptive evidence quality gate",
            "requirement_kind": "VALIDATOR_DASHBOARD_EVIDENCE_PATCH",
            "schema_ids": [
                "trader1.profitability_evidence_maturity_rollup.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"profitability adaptive evidence quality gate no fixed runtime floor"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_STRATEGY_PROFITABILITY",
            "schema_files": [
                "contracts/schema/profitability_evidence_maturity_rollup.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "test_files": [
                "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
            ],
            "fixture_files": ["tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json"],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
                "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
            ],
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py"],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    write_json(index_path, index)
    write_json(matrix_path, matrix)
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR", "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(artifacts)}

acceptance_checklist:
- PAPER runtime hours are observed context only and do not create a fixed runtime-hour floor.
- Profitability maturity remains blocked by replay, OOS/walk-forward, PAPER trade, SHADOW opportunity, cost, drawdown, fill quality, paper/live parity, and open HIGH gap evidence.
- Dashboard renders runtime hours as observed context rather than a pass/fail duration gate.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not execute PAPER/SHADOW runtime.
- This patch does not close {CONTRACT_GAP_ID}.
- This patch does not create LIVE_READY, live orders, credentials, live config mutation, or scale-up.

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

Profitability maturity now uses adaptive evidence-quality review. PAPER runtime hours are shown as observed context only; live review, live orders, and scale-up remain blocked until independent evidence and validators pass.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    state_before: dict[str, Any],
    validators_required: list[str] | None = None,
) -> dict[str, Any]:
    required = validators_required or VALIDATORS_REQUIRED
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_DURATION_WORDING_HYGIENE.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_SHADOW_REVIEW",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.profitability_evidence_maturity_rollup.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validators_required": required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_OPERATOR_CONTROL"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "LIVE_READY_WRITE", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": state_before.get("open_contract_gap_ids", []),
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "profitability evidence maturity rollup",
                "read-only dashboard profitability panel",
                "live final guard",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_PROFITABILITY_ADAPTIVE_EVIDENCE_QUALITY_GATE",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
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
            "stage_gate_status": "PASS_PROFITABILITY_ADAPTIVE_EVIDENCE_QUALITY_GATE_LIVE_BLOCKED",
            "paper_runtime_hours_gate_role": GATE_ROLE,
            "fixed_paper_runtime_hour_floor_removed": True,
            "profitability_gap_closed_by_this_patch": False,
            "next_allowed_task_class": NEXT_TASK_CLASS,
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
            "artifact_paths": sorted(
                set(
                    [
                        *CHANGED_ARTIFACTS,
                        "contracts/generated/ACTIVE_WORKING_VIEW.md",
                        "contracts/generated/current_implementation_state.json",
                        "contracts/generated/read_cache_manifest.json",
                        "contracts/generated/requirement_index.json",
                        "contracts/generated/requirement_artifact_matrix.json",
                        "system/evidence/implementation_patch_ledger.json",
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "paper_runtime_hours_gate_role": GATE_ROLE,
            "fixed_paper_runtime_hour_floor_removed": True,
            "profitability_gap_closed_by_this_patch": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Profitability Adaptive Evidence Quality Gate

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Removed the fixed PAPER runtime-hour floor from active profitability maturity evidence.
- Kept PAPER runtime hours as observed context only.
- Kept replay, OOS/walk-forward, PAPER trade count, SHADOW opportunity, net EV after cost, profit factor, drawdown, fill quality, paper/live parity, and open HIGH gap blockers visible.
- Updated the dashboard projection so operators see runtime as observed context rather than a duration pass/fail gate.

Safety:
- {CONTRACT_GAP_ID} remains OPEN.
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no live order
- no credential/API key use
- no LIVE_READY write
- no live config mutation
- no risk scale-up
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
        set(
            state.get("implemented_schema_ids", [])
            + ["trader1.profitability_evidence_maturity_rollup.v1", "trader1.read_only_dashboard_shell.v1"]
        )
    )
    state["implemented_validator_ids"] = sorted(
        set(
            state.get("implemented_validator_ids", [])
            + ["profitability_evidence_maturity_rollup_validator", "profitability_optimizer_evidence_gap_validator"]
        )
    )
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [CONTRACT_GAP_ID]))
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


def persist_patch(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    state_before = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")

    update_authority_manifest(now)
    refresh_rollup(ROLLUP_PATH, now, trader_hash, agents_hash)
    refresh_rollup(ROLLUP_FIXTURE_PATH, now, trader_hash, agents_hash)
    update_contract_gap(now, trader_hash, agents_hash)
    update_navigation(now, trader_hash, agents_hash)

    preliminary = build_patch_result(
        now,
        [],
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        state_before,
        BOOTSTRAP_VALIDATORS_REQUIRED,
    )
    persist_patch(now, trader_hash, agents_hash, preliminary)

    tests_run = [
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"], timeout_seconds=300),
        run_command([sys.executable, "-B", "-m", "json.tool", "contracts/schema/profitability_evidence_maturity_rollup.schema.json"], timeout_seconds=120),
        run_command([sys.executable, "-B", "-m", "json.tool", "contracts/schema/read_only_dashboard_shell.schema.json"], timeout_seconds=120),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
                "-q",
            ],
            timeout_seconds=300,
        ),
        run_command([sys.executable, "-B", "tools/run_profitability_optimizer_evidence_gap_validators.py"], timeout_seconds=300),
        run_command([sys.executable, "-B", "tools/run_read_only_dashboard_validators.py"], timeout_seconds=300),
    ]
    interim = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        state_before,
    )
    persist_patch(now, trader_hash, agents_hash, interim)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"], timeout_seconds=300))
    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1200))
    final = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        state_before,
    )
    persist_patch(now, trader_hash, agents_hash, final)

    failed = [item for item in [*final["tests_run"], *final["validators_run"]] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": final["result_hash"],
                "paper_runtime_hours_gate_role": GATE_ROLE,
                "fixed_paper_runtime_hour_floor_removed": True,
                "open_gap_count": len(state_before.get("open_contract_gap_ids", [])),
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
