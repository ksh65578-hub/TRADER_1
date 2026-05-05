from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Mapping


SCHEMA_ID = "trader1.open_contract_gap_current_blocker_classification_report.v1"
NEXT_TASK_CLASS = (
    "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
)
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

OPEN_GAP_RECHECK_REQUIREMENTS = {
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY": (
        "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION": (
        "REQ-MVP4-BLOCKED-REPAIR-PLAN-REQUIRES-OPERATOR-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "LIVE_ENABLING_EVIDENCE_MISSING": "REQ-MVP4-LIVE-ENABLING-EVIDENCE-MISSING-RECHECK",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED": (
        "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP": (
        "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "PATCH_RESULT_VALIDATOR_RUN_GAP": (
        "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "POST_REPAIR_RECONCILIATION_REQUIRED": (
        "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED": (
        "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "POST_RERUN_RECONCILIATION_REQUIRED": (
        "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY": (
        "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION": (
        "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-RECONCILIATION-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED": (
        "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK"
    ),
    "SCALE_UP_NOT_ELIGIBLE": "REQ-MVP4-SCALE-UP-NOT-ELIGIBLE-RECHECK",
}

GAP_BLOCKER_CATEGORIES = {
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY": "RUNTIME_LONG_RUN_EVIDENCE",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION": "OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING": "EXTERNAL_LIVE_EVIDENCE",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED": "LEDGER_RERUN_RECONCILIATION",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP": "PAPER_SHADOW_RUNTIME_EVIDENCE",
    "PATCH_RESULT_VALIDATOR_RUN_GAP": "SEALED_HISTORICAL_PATCH_RESULT_BASELINE",
    "POST_REPAIR_RECONCILIATION_REQUIRED": "OPERATOR_RECONCILIATION",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED": "LEDGER_RERUN_RECONCILIATION",
    "POST_RERUN_RECONCILIATION_REQUIRED": "LEDGER_RERUN_RECONCILIATION",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY": "PROFITABILITY_EVIDENCE_MATURITY",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION": (
        "OPERATOR_RECONCILIATION"
    ),
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED": "OPERATOR_RECONCILIATION",
    "SCALE_UP_NOT_ELIGIBLE": "SCALE_UP_POLICY",
}

GAP_REASONS = {
    "RUNTIME_LONG_RUN_EVIDENCE": (
        "accepted long-run PAPER/SHADOW runtime evidence is still insufficient for a current claim"
    ),
    "OPERATOR_RECONCILIATION": (
        "operator reconciliation is required before any repaired or regenerated evidence can be promoted"
    ),
    "EXTERNAL_LIVE_EVIDENCE": (
        "official API, read-only account, burn-in, manual test, and operator approval evidence is absent"
    ),
    "LEDGER_RERUN_RECONCILIATION": (
        "bounded paper-only rerun and reconciliation outputs remain incomplete or not promotion-usable"
    ),
    "PAPER_SHADOW_RUNTIME_EVIDENCE": (
        "PAPER/SHADOW observation evidence remains open even after implementation-depth scaffolding"
    ),
    "SEALED_HISTORICAL_PATCH_RESULT_BASELINE": (
        "sealed patch_result validator-run baseline remains live-blocking and cannot be rewritten by inference"
    ),
    "PROFITABILITY_EVIDENCE_MATURITY": (
        "profitability optimizer evidence has not reached the required paper/shadow maturity"
    ),
    "SCALE_UP_POLICY": "scale-up is not eligible without live burn-in, parity, survival, and operator evidence",
    "UNCLASSIFIED_OPEN_GAP": "gap is not mapped to a safe blocker category",
}

GAP_ACTIONS = {
    "RUNTIME_LONG_RUN_EVIDENCE": "collect fresh audited long-run PAPER/SHADOW runtime evidence",
    "OPERATOR_RECONCILIATION": "complete operator reconciliation; keep current-evidence writes blocked",
    "EXTERNAL_LIVE_EVIDENCE": "supply external live-readiness evidence outside this non-live patch path",
    "LEDGER_RERUN_RECONCILIATION": "rerun paper-only ledger/reconciliation jobs when required inputs exist",
    "PAPER_SHADOW_RUNTIME_EVIDENCE": "continue paper/shadow evidence collection without live credentials",
    "SEALED_HISTORICAL_PATCH_RESULT_BASELINE": "preserve sealed baseline and keep the gap live-blocking",
    "PROFITABILITY_EVIDENCE_MATURITY": "collect more paper/shadow maturity evidence before promotion",
    "SCALE_UP_POLICY": "keep scale-up disabled until all scale-up validators and operator policy pass",
    "UNCLASSIFIED_OPEN_GAP": "classify the gap before selecting implementation work",
}

CATEGORY_ORDER = (
    "RUNTIME_LONG_RUN_EVIDENCE",
    "OPERATOR_RECONCILIATION",
    "EXTERNAL_LIVE_EVIDENCE",
    "LEDGER_RERUN_RECONCILIATION",
    "PAPER_SHADOW_RUNTIME_EVIDENCE",
    "SEALED_HISTORICAL_PATCH_RESULT_BASELINE",
    "PROFITABILITY_EVIDENCE_MATURITY",
    "SCALE_UP_POLICY",
    "UNCLASSIFIED_OPEN_GAP",
)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def build_open_gap_current_blocker_classification_report(
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    completed = set(state.get("completed_requirement_ids", []))
    open_gaps = sorted(state.get("open_contract_gap_ids", []))
    classifications: list[dict[str, Any]] = []
    category_counter: Counter[str] = Counter()
    remaining_implementation_recheck_gap_ids: list[str] = []
    residual_blocked_gap_ids: list[str] = []

    for gap_id in open_gaps:
        requirement_id = OPEN_GAP_RECHECK_REQUIREMENTS.get(gap_id)
        completed_recheck_recorded = bool(requirement_id and requirement_id in completed)
        category = GAP_BLOCKER_CATEGORIES.get(gap_id, "UNCLASSIFIED_OPEN_GAP")
        category_counter[category] += 1

        if completed_recheck_recorded:
            residual_blocked_gap_ids.append(gap_id)
        else:
            remaining_implementation_recheck_gap_ids.append(gap_id)

        classifications.append(
            {
                "gap_id": gap_id,
                "blocker_category": category,
                "completed_recheck_requirement_id": requirement_id or "",
                "completed_recheck_recorded": completed_recheck_recorded,
                "residual_blocker_reason": GAP_REASONS[category],
                "next_operator_or_evidence_action": GAP_ACTIONS[category],
            }
        )

    all_rechecks_complete = bool(open_gaps) and not remaining_implementation_recheck_gap_ids
    category_counts = {category: category_counter.get(category, 0) for category in CATEGORY_ORDER}
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "open_gap_count": len(open_gaps),
        "completed_recheck_gap_count": len(residual_blocked_gap_ids),
        "all_open_gaps_have_completed_recheck": all_rechecks_complete,
        "repeat_completed_recheck_selected": False,
        "remaining_implementation_recheck_gap_ids": remaining_implementation_recheck_gap_ids,
        "residual_blocked_gap_ids": sorted(residual_blocked_gap_ids),
        "blocker_category_counts": category_counts,
        "gap_classifications": classifications,
        "selected_next_task_class": NEXT_TASK_CLASS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_open_gap_current_blocker_classification_report(
    report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    open_gaps = sorted(state.get("open_contract_gap_ids", []))
    completed = set(state.get("completed_requirement_ids", []))

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")

    if report.get("open_gap_count") != len(open_gaps):
        errors.append("open_gap_count does not match current state")
    if sorted(report.get("residual_blocked_gap_ids", [])) != open_gaps:
        errors.append("residual_blocked_gap_ids must preserve every current open gap")
    if report.get("remaining_implementation_recheck_gap_ids") != []:
        errors.append("remaining_implementation_recheck_gap_ids must be empty after completed rechecks")
    if report.get("all_open_gaps_have_completed_recheck") is not True:
        errors.append("all_open_gaps_have_completed_recheck must be true")
    if report.get("repeat_completed_recheck_selected") is not False:
        errors.append("repeat_completed_recheck_selected must be false")

    classifications = report.get("gap_classifications", [])
    classified_gap_ids = sorted(item.get("gap_id") for item in classifications if isinstance(item, dict))
    if classified_gap_ids != open_gaps:
        errors.append("gap_classifications must cover every current open gap exactly once")
    for item in classifications:
        if not isinstance(item, dict):
            errors.append("gap_classifications contains a non-object item")
            continue
        gap_id = item.get("gap_id")
        requirement_id = item.get("completed_recheck_requirement_id")
        if gap_id not in OPEN_GAP_RECHECK_REQUIREMENTS:
            errors.append(f"unmapped open gap: {gap_id}")
            continue
        if requirement_id != OPEN_GAP_RECHECK_REQUIREMENTS[gap_id]:
            errors.append(f"wrong completed recheck requirement for {gap_id}")
        if requirement_id not in completed:
            errors.append(f"completed recheck missing from current state for {gap_id}")
        if item.get("completed_recheck_recorded") is not True:
            errors.append(f"completed_recheck_recorded must be true for {gap_id}")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
