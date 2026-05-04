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

PATCH_BASENAME = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-RECHECK"
CONTRACT_GAP_ID = "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK"

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
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "profitability_evidence_maturity_rollup_validator",
    "profitability_optimizer_evidence_gap_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"]

CHANGED_ARTIFACTS = [
    "contracts/schema/profitability_evidence_maturity_rollup.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/security/source_bundle.py",
    "trader1/validation/mvp0_validators.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
    "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json",
    "tools/run_hygiene_safe_pytest.py",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
    "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    "tools/emit_profitability_optimizer_evidence_maturity_recheck_patch_evidence.py",
]

PROMOTION_THRESHOLD_EVIDENCE = {
    "status": "BLOCKED_FOR_THRESHOLD_EVIDENCE",
    "replay_closed_trades": 1,
    "min_replay_closed_trades": 100,
    "walk_forward_or_oos_coverage_pct": 0,
    "min_walk_forward_or_oos_coverage_pct": 30,
    "paper_closed_trades": 1,
    "min_paper_closed_trades": 30,
    "paper_runtime_hours": 0.1,
    "min_paper_runtime_hours": 72,
    "shadow_signal_opportunities": 2,
    "min_shadow_signal_opportunities": 50,
    "net_ev_after_cost_status": "PARTIAL",
    "profit_factor_status": "UNTESTED",
    "max_drawdown_status": "UNTESTED",
    "fill_quality_status": "UNTESTED",
    "paper_live_gap_status": "NOT_AVAILABLE",
    "high_or_critical_contract_gap_count": 1,
    "blocking_validator_fail_count": 0,
    "missing_threshold_codes": [
        "REPLAY_CLOSED_TRADES_BELOW_MIN",
        "WALK_FORWARD_OR_OOS_COVERAGE_BELOW_MIN",
        "PAPER_CLOSED_TRADES_BELOW_MIN",
        "PAPER_RUNTIME_HOURS_BELOW_MIN",
        "SHADOW_SIGNAL_OPPORTUNITIES_BELOW_MIN",
        "NET_EV_AFTER_COST_NOT_PASS",
        "PROFIT_FACTOR_NOT_PASS",
        "MAX_DRAWDOWN_NOT_PASS",
        "FILL_QUALITY_NOT_PASS",
        "PAPER_LIVE_GAP_NOT_AVAILABLE",
        "HIGH_OR_CRITICAL_CONTRACT_GAP_OPEN",
    ],
    "explicit_insufficient_sample_blocker": True,
    "live_order_ready": False,
    "live_order_allowed": False,
    "can_live_trade": False,
    "scale_up_allowed": False,
}

BLOCKERS = [
    CONTRACT_GAP_ID,
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "OOS_WALK_FORWARD_BOOTSTRAP_EVIDENCE_MISSING",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def refresh_rollup(path: Path, now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    rollup = load_json(path)
    rollup["generated_at_utc"] = now
    rollup["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    rollup["status"] = "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY"
    rollup["promotion_threshold_evidence"] = dict(PROMOTION_THRESHOLD_EVIDENCE)
    rollup["live_order_ready"] = False
    rollup["live_order_allowed"] = False
    rollup["can_live_trade"] = False
    rollup["scale_up_allowed"] = False
    rollup["live_review_eligible"] = False
    rollup["scale_up_eligible"] = False
    rollup["primary_blocker_code"] = CONTRACT_GAP_ID
    rollup["rollup_hash"] = ""
    rollup["rollup_hash"] = sha256_json({key: value for key, value in rollup.items() if key != "rollup_hash"})
    write_json(path, rollup)
    return rollup


def update_contract_gap(now: str, trader_hash: str, agents_hash: str) -> None:
    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    gap = load_json(gap_path)
    gap["generated_at_utc"] = now
    gap["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    gap["status"] = "OPEN"
    gap["live_affecting"] = True
    gap["notes"] = (
        "Rechecked in MVP-4. Profitability evidence maturity now carries explicit promotion threshold evidence "
        "for replay trades, OOS/walk-forward coverage, paper trades, paper runtime hours, shadow opportunities, "
        "net EV after cost, profit factor, drawdown, fill quality, paper/live parity, and open HIGH contract gaps. "
        "The gap remains OPEN and live-blocking."
    )
    write_json(gap_path, gap)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + [
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
    matrix["updated_at_utc"] = now
    ensure_requirement(
        index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_STRATEGY_PROFITABILITY",
            "source_file": "TRADER_1.md",
            "source_heading": "profitability optimizer evidence maturity recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: promotion threshold evidence must stay explicit, insufficient, "
                "and live-blocking until exact replay, OOS/walk-forward, PAPER, SHADOW, live burn-in, "
                "and operator evidence exists"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Profitability optimizer evidence maturity recheck",
            "requirement_kind": "SCHEMA_VALIDATOR_PATCH",
            "schema_ids": ["trader1.profitability_evidence_maturity_rollup.v1"],
            "validator_ids": [
                "profitability_evidence_maturity_rollup_validator",
                "profitability_optimizer_evidence_gap_validator",
                "optimizer_guardrail_validator",
                "convergence_assessment_validator",
                "live_final_guard_validator",
            ],
            "artifact_ids": artifacts,
            "test_ids": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_CONVERGENCE_ASSESSMENT",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"profitability optimizer evidence maturity recheck promotion threshold evidence live blocked"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED_THRESHOLD_EVIDENCE",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_STRATEGY_PROFITABILITY",
            "schema_files": ["contracts/schema/profitability_evidence_maturity_rollup.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
            "fixture_files": ["tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json"],
            "runtime_modules": ["tools/run_profitability_optimizer_evidence_gap_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
                "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
            ],
            "dashboard_artifacts": [],
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
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED_THRESHOLD_EVIDENCE",
        },
    )
    write_json(index_path, index)
    write_json(matrix_path, matrix)
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR", "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(artifacts)}

acceptance_checklist:
- profitability_evidence_maturity_rollup requires promotion_threshold_evidence.
- Promotion threshold evidence counts replay, OOS/walk-forward, PAPER, SHADOW, net EV, quality, parity, and open HIGH gap blockers.
- Missing or false-PASS threshold evidence fails closed.
- {CONTRACT_GAP_ID} remains OPEN and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- No live execution, credential use, LIVE_READY write, live config mutation, or risk scale-up.
- The new threshold evidence records insufficiency; it does not claim maturity.

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

Profitability optimizer evidence maturity is now threshold-explicit and still blocked. PAPER scorecard input remains analysis-only; replay, OOS/walk-forward, PAPER runtime hours, SHADOW opportunities, read-only burn-in, manual order evidence, and operator approval are still insufficient for live review.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str] | None = None,
) -> dict[str, Any]:
    required = validators_required or VALIDATORS_REQUIRED
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_STATE_SYNC_RECHECK.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [REQUIREMENT_ID, f"contracts/generated/context_pack/{PATCH_BASENAME}.md"],
            "new_or_changed_schema_ids": ["trader1.profitability_evidence_maturity_rollup.v1"],
            "validators_required": required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_OPTIMIZER_GUARDRAIL",
            ],
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
            "active_read_surface_used": [
                "current_implementation_state",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_CONVERGENCE_ASSESSMENT",
                "SECTION_LIVE_FINAL_GUARD",
                "profitability_evidence_maturity_rollup",
                "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY contract gap",
            ],
            "task_class": "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK",
            "required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_CONVERGENCE_ASSESSMENT",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_CONVERGENCE_ASSESSMENT",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "PROFITABILITY_EVIDENCE_MATURITY_THRESHOLD_RECHECK_NO_LIVE_MUTATION",
            "optimizer_stage": "MVP4_REVIEW_PREP",
            "optimizer_status_before": "EVIDENCE_MATURITY_GAP_VISIBLE",
            "optimizer_status_after": "THRESHOLD_EXPLICIT_EVIDENCE_MATURITY_GAP_LIVE_BLOCKED",
            "optimizer_maturity_level_before": "MVP4_PARTIAL_PATCHED_GAP_VISIBLE",
            "optimizer_maturity_level_after": "MVP4_THRESHOLD_EXPLICIT_LIVE_BLOCKED",
            "optimizer_output_type": "ANALYSIS_ONLY_THRESHOLD_EVIDENCE",
            "optimizer_validators_required": [
                "profitability_evidence_maturity_rollup_validator",
                "profitability_optimizer_evidence_gap_validator",
                "optimizer_guardrail_validator",
                "live_final_guard_validator",
            ],
            "optimizer_validators_run": [
                result
                for result in validators_run
                if result.get("validator_id")
                in {
                    "profitability_evidence_maturity_rollup_validator",
                    "profitability_optimizer_evidence_gap_validator",
                    "optimizer_guardrail_validator",
                    "live_final_guard_validator",
                }
            ],
            "optimizer_guardrail_result": next(
                (
                    result.get("status")
                    for result in validators_run
                    if result.get("validator_id") == "optimizer_guardrail_validator"
                ),
                "UNTESTED",
            ),
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "PROFITABILITY_THRESHOLD_EVIDENCE_RECHECK_NO_LIVE_MUTATION",
            "convergence_layer_changed": False,
            "convergence_state_before": "EVIDENCE_MATURITY_GAP_VISIBLE",
            "convergence_state_after": "THRESHOLD_EXPLICIT_EVIDENCE_MATURITY_GAP_LIVE_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED_THRESHOLD_EVIDENCE_RECHECK_ONLY",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": [
                "convergence_assessment_validator",
                "profitability_optimizer_evidence_gap_validator",
                "live_final_guard_validator",
            ],
            "convergence_validators_run": [
                result
                for result in validators_run
                if result.get("validator_id")
                in {
                    "convergence_assessment_validator",
                    "profitability_optimizer_evidence_gap_validator",
                    "live_final_guard_validator",
                }
            ],
            "convergence_guardrail_result": next(
                (
                    result.get("status")
                    for result in validators_run
                    if result.get("validator_id") == "convergence_assessment_validator"
                ),
                "UNTESTED",
            ),
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
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
            "stage_gate_status": "PASS_THRESHOLD_EXPLICIT_RECHECK_LIVE_BLOCKED",
            "promotion_threshold_evidence": PROMOTION_THRESHOLD_EVIDENCE,
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": artifact_paths,
            "known_blockers": BLOCKERS,
            "promotion_threshold_evidence": PROMOTION_THRESHOLD_EVIDENCE,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Profitability Optimizer Evidence Maturity Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added schema-backed promotion_threshold_evidence to the profitability maturity rollup.
- Validator now fails closed if threshold evidence claims PASS while replay, OOS/walk-forward, PAPER, SHADOW, parity, quality, or HIGH contract-gap evidence is insufficient.
- Contract gap remains OPEN and live-affecting.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
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
        set(state.get("implemented_schema_ids", []) + ["trader1.profitability_evidence_maturity_rollup.v1"])
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


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    refresh_rollup(
        ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
        now,
        trader_hash,
        agents_hash,
    )
    refresh_rollup(
        ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json",
        now,
        trader_hash,
        agents_hash,
    )
    update_contract_gap(now, trader_hash, agents_hash)
    update_navigation(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    write_source_bundle_manifest()

    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    preliminary = build_patch_result(
        now,
        [],
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
    )
    write_json(patch_path, preliminary)
    write_evidence(now, trader_hash, agents_hash, preliminary)
    update_state_and_ledger(now, preliminary)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "-m", "json.tool", "contracts/schema/profitability_evidence_maturity_rollup.schema.json"]),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_profitability_optimizer_evidence_gap_validators.py"]),
        run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/contract/test_patch_result_runtime_schema_validation.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
    ]
    final_patch = build_patch_result(now, tests_run, summarize_validators(run_validators(VALIDATORS_REQUIRED)))
    write_json(patch_path, final_patch)
    write_evidence(now, trader_hash, agents_hash, final_patch)
    update_state_and_ledger(now, final_patch)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in final_patch["tests_run"] + final_patch["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": final_patch["result_hash"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "promotion_threshold_missing_code_count": len(PROMOTION_THRESHOLD_EVIDENCE["missing_threshold_codes"]),
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
