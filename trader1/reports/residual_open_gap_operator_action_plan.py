from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import (
    CATEGORY_ORDER,
    NEXT_TASK_CLASS,
    validate_open_gap_current_blocker_classification_report,
)


SCHEMA_ID = "trader1.residual_open_gap_operator_action_plan_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

ACTION_CLASS_BY_CATEGORY = {
    "OPERATOR_RECONCILIATION": "OPERATOR_RECONCILIATION_ACTION",
    "LEDGER_RERUN_RECONCILIATION": "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION",
    "RUNTIME_LONG_RUN_EVIDENCE": "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
    "PAPER_SHADOW_RUNTIME_EVIDENCE": "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
    "PROFITABILITY_EVIDENCE_MATURITY": "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
    "EXTERNAL_LIVE_EVIDENCE": "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION",
    "SEALED_HISTORICAL_PATCH_RESULT_BASELINE": "SEALED_BASELINE_PRESERVATION_ACTION",
    "SCALE_UP_POLICY": "SCALE_UP_POLICY_EVIDENCE_ACTION",
    "UNCLASSIFIED_OPEN_GAP": "CLASSIFY_OPEN_GAP_ACTION",
}

ACTION_ORDER = (
    "OPERATOR_RECONCILIATION_ACTION",
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION",
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION",
    "SEALED_BASELINE_PRESERVATION_ACTION",
    "SCALE_UP_POLICY_EVIDENCE_ACTION",
    "CLASSIFY_OPEN_GAP_ACTION",
)

ACTION_MESSAGES = {
    "OPERATOR_RECONCILIATION_ACTION": {
        "title": "Complete operator reconciliation",
        "plain_next_action": "Review and reconcile repaired, regenerated, or hash-mismatched evidence before promotion.",
        "unlock_condition": "operator reconciliation artifacts explicitly resolve the affected gaps",
    },
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION": {
        "title": "Run bounded PAPER ledger/reconciliation reruns",
        "plain_next_action": "Rerun paper-only ledger and reconciliation jobs only when the required inputs exist.",
        "unlock_condition": "bounded paper-only rerun outputs and reconciliation reports validate cleanly",
    },
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION": {
        "title": "Collect longer PAPER/SHADOW evidence",
        "plain_next_action": "Collect fresh audited PAPER/SHADOW runtime and profitability maturity evidence.",
        "unlock_condition": "long-run PAPER/SHADOW evidence, shadow observation, and profitability maturity validators pass",
    },
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION": {
        "title": "Provide external live-readiness evidence",
        "plain_next_action": "Provide official API, read-only account, burn-in, manual test, and operator approval evidence outside this non-live patch path.",
        "unlock_condition": "independent live-readiness evidence exists and all live gates pass",
    },
    "SEALED_BASELINE_PRESERVATION_ACTION": {
        "title": "Preserve sealed historical baseline",
        "plain_next_action": "Do not rewrite sealed patch_result validator-run history by inference.",
        "unlock_condition": "sealed baseline reconciliation remains explicit and audit-preserved",
    },
    "SCALE_UP_POLICY_EVIDENCE_ACTION": {
        "title": "Keep scale-up disabled",
        "plain_next_action": "Keep scale-up disabled until burn-in, parity, survival, and operator policy evidence pass.",
        "unlock_condition": "scale-up eligibility validators and operator policy pass for the exact scope",
    },
    "CLASSIFY_OPEN_GAP_ACTION": {
        "title": "Classify unmapped open gap",
        "plain_next_action": "Classify the gap before selecting any implementation or evidence path.",
        "unlock_condition": "gap is mapped to a closed blocker category",
    },
}

FORBIDDEN_ACTIONS = (
    "do not place live orders",
    "do not use credentials or API keys",
    "do not mutate live config",
    "do not write LIVE_READY snapshot",
    "do not infer evidence across exchange, market_type, mode, or session scope",
    "do not enable risk scale-up",
)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _empty_action(action_class: str, index: int) -> dict[str, Any]:
    message = ACTION_MESSAGES[action_class]
    return {
        "action_class": action_class,
        "priority": index,
        "title": message["title"],
        "plain_next_action": message["plain_next_action"],
        "unlock_condition": message["unlock_condition"],
        "gap_count": 0,
        "gap_ids": [],
        "source_categories": [],
        "requires_operator_reconciliation": action_class == "OPERATOR_RECONCILIATION_ACTION",
        "requires_external_evidence": action_class == "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION",
        "requires_paper_shadow_evidence": action_class == "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
        "requires_ledger_rerun": action_class == "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION",
        "allows_live_order": False,
        "allows_live_config_mutation": False,
        "allows_scale_up": False,
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
    }


def build_residual_open_gap_operator_action_plan_report(
    classification_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    classification_errors = validate_open_gap_current_blocker_classification_report(classification_report, state)
    actions_by_class = {
        action_class: _empty_action(action_class, index + 1) for index, action_class in enumerate(ACTION_ORDER)
    }

    for item in classification_report.get("gap_classifications", []):
        if not isinstance(item, Mapping):
            continue
        category = str(item.get("blocker_category", "UNCLASSIFIED_OPEN_GAP"))
        gap_id = str(item.get("gap_id", ""))
        action_class = ACTION_CLASS_BY_CATEGORY.get(category, "CLASSIFY_OPEN_GAP_ACTION")
        action = actions_by_class[action_class]
        action["gap_ids"].append(gap_id)
        if category not in action["source_categories"]:
            action["source_categories"].append(category)

    action_items = []
    for action_class in ACTION_ORDER:
        action = actions_by_class[action_class]
        action["gap_ids"] = sorted(set(action["gap_ids"]))
        action["source_categories"] = [category for category in CATEGORY_ORDER if category in action["source_categories"]]
        action["gap_count"] = len(action["gap_ids"])
        if action["gap_count"] > 0:
            action_items.append(action)

    open_gap_count = int(classification_report.get("open_gap_count", 0))
    total_action_gap_count = sum(action["gap_count"] for action in action_items)
    implementation_recheck_action_count = len(classification_report.get("remaining_implementation_recheck_gap_ids", []))
    external_or_operator_action_required = open_gap_count > 0 and implementation_recheck_action_count == 0

    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_classification_report_id": str(classification_report.get("patch_id", "")),
        "source_classification_report_hash": str(classification_report.get("report_hash", "")),
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "open_gap_count": open_gap_count,
        "total_action_gap_count": total_action_gap_count,
        "implementation_recheck_action_count": implementation_recheck_action_count,
        "external_or_operator_action_required": external_or_operator_action_required,
        "action_items": action_items,
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "classification_validation_status": "PASS" if not classification_errors else "FAIL",
        "classification_validation_errors": classification_errors,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_open_gap_operator_action_plan_report(
    report: Mapping[str, Any],
    classification_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")

    classification_errors = validate_open_gap_current_blocker_classification_report(classification_report, state)
    if classification_errors:
        errors.extend(f"classification: {error}" for error in classification_errors)
    if report.get("classification_validation_status") != "PASS":
        errors.append("classification_validation_status must be PASS")
    if report.get("classification_validation_errors") != []:
        errors.append("classification_validation_errors must be empty")
    if report.get("source_classification_report_hash") != classification_report.get("report_hash"):
        errors.append("source_classification_report_hash mismatch")
    if report.get("open_gap_count") != classification_report.get("open_gap_count"):
        errors.append("open_gap_count mismatch")
    if report.get("total_action_gap_count") != classification_report.get("open_gap_count"):
        errors.append("total_action_gap_count must cover every open gap")
    if report.get("implementation_recheck_action_count") != len(
        classification_report.get("remaining_implementation_recheck_gap_ids", [])
    ):
        errors.append("implementation_recheck_action_count mismatch")
    if report.get("external_or_operator_action_required") is not True:
        errors.append("external_or_operator_action_required must be true for residual blockers")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")

    seen_gap_ids: list[str] = []
    for action in report.get("action_items", []):
        if not isinstance(action, Mapping):
            errors.append("action_items contains a non-object item")
            continue
        seen_gap_ids.extend(str(gap_id) for gap_id in action.get("gap_ids", []))
        if action.get("allows_live_order") is not False:
            errors.append(f"{action.get('action_class')} allows live order")
        if action.get("allows_live_config_mutation") is not False:
            errors.append(f"{action.get('action_class')} allows live config mutation")
        if action.get("allows_scale_up") is not False:
            errors.append(f"{action.get('action_class')} allows scale-up")
        forbidden = set(action.get("forbidden_actions", []))
        if not set(FORBIDDEN_ACTIONS).issubset(forbidden):
            errors.append(f"{action.get('action_class')} missing forbidden actions")

    if sorted(seen_gap_ids) != sorted(classification_report.get("residual_blocked_gap_ids", [])):
        errors.append("action_items must cover residual_blocked_gap_ids exactly once")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
