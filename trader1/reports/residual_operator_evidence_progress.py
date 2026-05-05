from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS


SCHEMA_ID = "trader1.residual_operator_evidence_progress_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

EXTERNAL_PREFIX = "system/evidence/external/"
RUNTIME_PREFIX = "system/runtime/"
PLACEHOLDER_TOKENS = ("<session_id>", "<shadow_session_id>")


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _path_status(path: str, root: Path) -> str:
    if any(token in path for token in PLACEHOLDER_TOKENS):
        return "PLACEHOLDER_PATTERN_PENDING"
    if path.startswith(EXTERNAL_PREFIX):
        return "EXTERNAL_EVIDENCE_REQUIRED"
    if path.startswith(RUNTIME_PREFIX):
        if (root / path).exists():
            return "LOCAL_RUNTIME_OUTPUT_PRESENT_NOT_CLOSURE_READY"
        return "LOCAL_RUNTIME_OUTPUT_MISSING"
    if (root / path).exists():
        return "PRESENT_BLOCKED"
    return "MISSING_OPERATOR_EVIDENCE"


def _evidence_item_status_blocks_closure(status: str) -> bool:
    return status in {
        "PRESENT_BLOCKED",
        "MISSING_OPERATOR_EVIDENCE",
        "PLACEHOLDER_PATTERN_PENDING",
        "EXTERNAL_EVIDENCE_REQUIRED",
        "LOCAL_RUNTIME_OUTPUT_PRESENT_NOT_CLOSURE_READY",
        "LOCAL_RUNTIME_OUTPUT_MISSING",
    }


def _build_evidence_items(execution_guide_report: Mapping[str, Any], root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for step in execution_guide_report.get("execution_steps", []):
        if not isinstance(step, Mapping):
            continue
        action_class = str(step.get("action_class", "UNKNOWN_ACTION"))
        step_id = str(step.get("step_id", "UNKNOWN_STEP"))
        evidence_paths = step.get("required_evidence_artifacts", [])
        if not isinstance(evidence_paths, list):
            continue
        for index, evidence_path in enumerate(evidence_paths, start=1):
            path = str(evidence_path)
            status = _path_status(path, root)
            items.append(
                {
                    "evidence_item_id": f"EVIDENCE:{action_class}:{index}",
                    "step_id": step_id,
                    "action_class": action_class,
                    "evidence_path": path,
                    "path_status": status,
                    "blocks_mvp5_entry": True,
                    "evidence_ready_for_closure": False,
                    "current_evidence_write_allowed": False,
                    "gap_closure_allowed_by_this_patch": False,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            )
    return items


def _build_runtime_command_items(execution_guide_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for step in execution_guide_report.get("execution_steps", []):
        if not isinstance(step, Mapping):
            continue
        action_class = str(step.get("action_class", "UNKNOWN_ACTION"))
        for command in step.get("allowed_local_commands", []):
            if not isinstance(command, Mapping):
                continue
            commands.append(
                {
                    "command_id": str(command.get("command_id", "")),
                    "action_class": action_class,
                    "scope": str(command.get("scope", "")),
                    "minimum_duration_hours": int(command.get("minimum_duration_hours", 0) or 0),
                    "command_status": "NOT_RUN_BY_THIS_PATCH",
                    "non_live_only": command.get("non_live_only") is True,
                    "credential_required": command.get("credential_required") is True,
                    "live_order_allowed": command.get("live_order_allowed") is True,
                    "evidence_ready_for_closure": False,
                    "current_evidence_write_allowed": False,
                    "gap_closure_allowed_by_this_patch": False,
                    "scale_up_allowed": False,
                }
            )
    return commands


def build_residual_operator_evidence_progress_report(
    execution_guide_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    root: Path,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    evidence_items = _build_evidence_items(execution_guide_report, root)
    runtime_commands = _build_runtime_command_items(execution_guide_report)
    status_counts: dict[str, int] = {}
    for item in evidence_items:
        status = item["path_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [_source_report_ref("residual_operator_execution_guide", execution_guide_report)],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "execution_step_count": int(execution_guide_report.get("execution_step_count", 0) or 0),
        "evidence_item_count": len(evidence_items),
        "present_blocked_evidence_item_count": status_counts.get("PRESENT_BLOCKED", 0),
        "missing_operator_evidence_item_count": status_counts.get("MISSING_OPERATOR_EVIDENCE", 0),
        "placeholder_pending_evidence_item_count": status_counts.get("PLACEHOLDER_PATTERN_PENDING", 0),
        "external_evidence_required_item_count": status_counts.get("EXTERNAL_EVIDENCE_REQUIRED", 0),
        "local_runtime_output_item_count": status_counts.get("LOCAL_RUNTIME_OUTPUT_PRESENT_NOT_CLOSURE_READY", 0)
        + status_counts.get("LOCAL_RUNTIME_OUTPUT_MISSING", 0),
        "local_runtime_command_count": len(runtime_commands),
        "local_runtime_completed_count": 0,
        "minimum_observation_hours_required": max(
            (command["minimum_duration_hours"] for command in runtime_commands),
            default=0,
        ),
        "adaptive_judgement_status": "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY",
        "fixed_duration_gate_status": "REMOVED_NO_FIXED_RUNTIME_FLOOR",
        "codex_stepwise_review_allowed": True,
        "codex_can_continue_non_live_patches": True,
        "user_runtime_required_for_next_non_live_patch": False,
        "user_runtime_required_for_gap_closure": True,
        "evidence_quality_status": "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES",
        "codex_judgement_summary": (
            "Codex may continue non-live implementation and evidence review from existing artifacts; "
            "gap closure still requires audited runtime, reconciliation, external, or operator evidence."
        ),
        "user_action_summary": (
            "No immediate user action is required for the next non-live patch; PAPER/SHADOW runtime is only "
            "required when Codex reaches an evidence-dependent closure review."
        ),
        "codex_review_next_actions": [
            "review existing residual evidence reports",
            "harden non-live evidence, validator, ledger, reconciliation, and dashboard bindings",
            "keep open gaps blocked until audited closure evidence exists",
        ],
        "operator_evidence_ready_for_mvp5": False,
        "any_evidence_item_ready_for_closure": False,
        "mvp5_entry_blocked_until_operator_evidence": True,
        "binance_runtime_status": "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS",
        "progress_status": "BLOCKED_EVIDENCE_MISSING",
        "evidence_items": evidence_items,
        "local_runtime_commands": runtime_commands,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "live_ready_write_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "validation_status": "PASS",
        "validation_errors": [],
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_operator_evidence_progress_report(
    report: Mapping[str, Any],
    execution_guide_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if execution_guide_report.get("guide_status") != "BLOCKED_GUIDE_ONLY":
        errors.append("source execution guide must remain blocked")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        if execution_guide_report.get(field) is not False:
            errors.append(f"execution guide {field} must remain false")
    for field in (
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids:
        errors.append("open_gap_ids must match current state")
    evidence_items = report.get("evidence_items", [])
    if not isinstance(evidence_items, list):
        return errors + ["evidence_items must be an array"]
    if report.get("evidence_item_count") != len(evidence_items):
        errors.append("evidence_item_count must match evidence_items")
    for item in evidence_items:
        if not isinstance(item, Mapping):
            errors.append("evidence item must be object")
            continue
        status = str(item.get("path_status", ""))
        if not _evidence_item_status_blocks_closure(status):
            errors.append(f"{status} is not a blocked evidence status")
        if item.get("evidence_ready_for_closure") is not False:
            errors.append("evidence item cannot be ready for closure")
        for field in (
            "current_evidence_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if item.get(field) is not False:
                errors.append(f"evidence item {field} must remain false")
    runtime_commands = report.get("local_runtime_commands", [])
    if not isinstance(runtime_commands, list):
        return errors + ["local_runtime_commands must be an array"]
    if report.get("local_runtime_command_count") != len(runtime_commands):
        errors.append("local_runtime_command_count must match local_runtime_commands")
    for command in runtime_commands:
        if not isinstance(command, Mapping):
            errors.append("local runtime command must be object")
            continue
        if command.get("non_live_only") is not True:
            errors.append("local runtime command must be non_live_only")
        if command.get("credential_required") is not False:
            errors.append("local runtime command must not require credentials")
        if command.get("live_order_allowed") is not False:
            errors.append("local runtime command must keep live_order_allowed false")
        if command.get("evidence_ready_for_closure") is not False:
            errors.append("local runtime command cannot mark evidence ready for closure")
    if report.get("local_runtime_command_count") != 1:
        errors.append("exactly one local runtime command must be tracked")
    if report.get("adaptive_judgement_status") != "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY":
        errors.append("adaptive_judgement_status must keep non-live review open without closure")
    if report.get("fixed_duration_gate_status") != "REMOVED_NO_FIXED_RUNTIME_FLOOR":
        errors.append("fixed_duration_gate_status must show the fixed runtime floor is removed")
    for field in ("codex_stepwise_review_allowed", "codex_can_continue_non_live_patches"):
        if report.get(field) is not True:
            errors.append(f"{field} must remain true")
    if report.get("user_runtime_required_for_next_non_live_patch") is not False:
        errors.append("user_runtime_required_for_next_non_live_patch must remain false")
    if report.get("user_runtime_required_for_gap_closure") is not True:
        errors.append("user_runtime_required_for_gap_closure must remain true")
    if report.get("evidence_quality_status") != "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES":
        errors.append("evidence_quality_status must remain insufficient for gap closure")
    if not isinstance(report.get("codex_judgement_summary"), str) or not report.get("codex_judgement_summary"):
        errors.append("codex_judgement_summary must be non-empty")
    if not isinstance(report.get("user_action_summary"), str) or not report.get("user_action_summary"):
        errors.append("user_action_summary must be non-empty")
    next_actions = report.get("codex_review_next_actions", [])
    if not isinstance(next_actions, list) or len(next_actions) < 3:
        errors.append("codex_review_next_actions must list stepwise non-live review actions")
    if report.get("operator_evidence_ready_for_mvp5") is not False:
        errors.append("operator_evidence_ready_for_mvp5 must remain false")
    if report.get("any_evidence_item_ready_for_closure") is not False:
        errors.append("any_evidence_item_ready_for_closure must remain false")
    if report.get("mvp5_entry_blocked_until_operator_evidence") is not True:
        errors.append("mvp5 entry must stay blocked until operator evidence")
    if report.get("binance_runtime_status") != "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS":
        errors.append("binance runtime status must remain scaffold-only")
    if report.get("progress_status") != "BLOCKED_EVIDENCE_MISSING":
        errors.append("progress_status must remain BLOCKED_EVIDENCE_MISSING")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
