from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS
from trader1.reports.residual_operator_execution_guide import (
    MVP5_REVIEW_ENTRY_DURATION_HOURS,
    MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS,
    MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT,
    MVP5_REVIEW_ENTRY_PROFILE_ID,
)


SCHEMA_ID = "trader1.residual_operator_evidence_run_preflight_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
PAPER_SHADOW_ACTION_CLASS = "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION"


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _paper_shadow_step(execution_guide_report: Mapping[str, Any]) -> Mapping[str, Any]:
    for step in execution_guide_report.get("execution_steps", []):
        if isinstance(step, Mapping) and step.get("action_class") == PAPER_SHADOW_ACTION_CLASS:
            return step
    return {}


def _paper_shadow_command(step: Mapping[str, Any]) -> Mapping[str, Any]:
    for command in step.get("allowed_local_commands", []):
        if isinstance(command, Mapping) and command.get("command_id") == MVP5_REVIEW_ENTRY_PROFILE_ID:
            return command
    return {}


def _extract_env_override(command_text: str, name: str) -> str:
    match = re.search(rf"\$env:{re.escape(name)}='([^']*)'", command_text)
    return match.group(1) if match else ""


def _runtime_path_status(path: str, root: Path) -> str:
    if "<session_id>" in path or "<shadow_session_id>" in path:
        return "PLACEHOLDER_PATTERN_PENDING"
    if (root / path).exists():
        return "PRESENT_LOCAL_RUNTIME_OUTPUT_NOT_CLOSURE_READY"
    return "MISSING_EXPECTED_RUNTIME_OUTPUT"


def _check(check_id: str, passed: bool, message: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "status": "PASS" if passed else "BLOCKED",
        "message": message,
    }


def _completion_acceptance_item(
    *,
    acceptance_id: str,
    acceptance_kind: str,
    evidence_path: str,
    responsible_validator_id: str,
    current_preflight_status: str,
    required_after_operator_run: str,
    operator_message: str,
) -> dict[str, Any]:
    return {
        "acceptance_id": acceptance_id,
        "acceptance_kind": acceptance_kind,
        "evidence_path": evidence_path,
        "responsible_validator_id": responsible_validator_id,
        "current_preflight_status": current_preflight_status,
        "required_after_operator_run": required_after_operator_run,
        "operator_message": operator_message,
        "blocks_mvp5_entry_until_pass": True,
        "blocks_live_until_pass": True,
        "blocks_gap_closure_until_pass": True,
        "evidence_ready_for_closure": False,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_ready_write_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _completion_acceptance_matrix(
    expected_artifacts: list[dict[str, Any]],
    required_validators: list[str],
) -> list[dict[str, Any]]:
    validator_by_path = {
        "heartbeat.json": "runtime_schema_instance_validator",
        "summary.json": "runtime_schema_instance_validator",
        "upbit_paper_persistent_loop_report.json": "upbit_paper_persistent_loop_validator",
        "shadow_observation_persistent_runtime_report.json": "shadow_observation_persistent_runtime_validator",
        "paper_shadow_evidence_accumulation_report.json": "paper_shadow_evidence_accumulation_validator",
    }
    items: list[dict[str, Any]] = []
    for index, artifact in enumerate(expected_artifacts, 1):
        path = str(artifact.get("path", ""))
        validator_id = next(
            (
                validator
                for marker, validator in validator_by_path.items()
                if marker in path and validator in required_validators
            ),
            "runtime_schema_instance_validator",
        )
        items.append(
            _completion_acceptance_item(
                acceptance_id=f"RUNTIME_ARTIFACT_{index:02d}",
                acceptance_kind="RUNTIME_ARTIFACT",
                evidence_path=path,
                responsible_validator_id=validator_id,
                current_preflight_status=str(artifact.get("current_path_status") or "MISSING_EXPECTED_RUNTIME_OUTPUT"),
                required_after_operator_run="ARTIFACT_PRESENT_AND_VALIDATOR_PASS",
                operator_message=(
                    "After the operator PAPER/SHADOW run, this artifact must exist for the exact scope and its "
                    f"responsible validator must PASS: {validator_id}."
                ),
            )
        )
    for validator_id in required_validators:
        items.append(
            _completion_acceptance_item(
                acceptance_id=f"VALIDATOR_{validator_id.upper()}",
                acceptance_kind="VALIDATOR",
                evidence_path="VALIDATOR_RUN_LOG",
                responsible_validator_id=validator_id,
                current_preflight_status="PENDING_OPERATOR_RUN",
                required_after_operator_run="VALIDATOR_PASS_WITH_FRESH_SCOPE_EVIDENCE",
                operator_message=(
                    "After the operator PAPER/SHADOW run, this validator must PASS with fresh evidence from the "
                    f"same exchange/market_type/mode scope: {validator_id}."
                ),
            )
        )
    items.append(
        _completion_acceptance_item(
            acceptance_id="LIVE_FLAGS_REMAIN_FALSE",
            acceptance_kind="SAFETY_INVARIANT",
            evidence_path="contracts/generated/current_implementation_state.json",
            responsible_validator_id="live_final_guard_validator",
            current_preflight_status="PASS_FALSE_FLAGS",
            required_after_operator_run="LIVE_AND_SCALE_FLAGS_FALSE",
            operator_message=(
                "After the operator run, live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed "
                "must still be false unless a separate authorized LIVE_READY path exists."
            ),
        )
    )
    return items


def build_residual_operator_evidence_run_preflight_report(
    execution_guide_report: Mapping[str, Any],
    progress_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    root: Path,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    step = _paper_shadow_step(execution_guide_report)
    command = _paper_shadow_command(step)
    command_text = str(command.get("command", ""))
    ticks_text = _extract_env_override(command_text, "TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS")
    interval_text = _extract_env_override(command_text, "TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS")
    try:
        expected_ticks = int(ticks_text)
    except ValueError:
        expected_ticks = 0
    try:
        heartbeat_interval_seconds = int(interval_text)
    except ValueError:
        heartbeat_interval_seconds = 0

    expected_artifacts = []
    for artifact_path in step.get("required_evidence_artifacts", []):
        path = str(artifact_path)
        expected_artifacts.append(
            {
                "path": path,
                "artifact_role": "PAPER_SHADOW_OPERATOR_EVIDENCE_INPUT",
                "required_before_next_review": True,
                "current_path_status": _runtime_path_status(path, root),
                "evidence_ready_for_closure": False,
                "current_evidence_write_allowed": False,
                "gap_closure_allowed_by_this_patch": False,
            }
        )

    required_validators = [str(item) for item in step.get("validators_required_for_next_review", [])]
    live_flags_false = all(state.get(field) is False for field in LIVE_FALSE_FIELDS) and all(
        progress_report.get(field) is False for field in LIVE_FALSE_FIELDS
    ) and all(execution_guide_report.get(field) is False for field in LIVE_FALSE_FIELDS)
    command_non_live = command.get("non_live_only") is True and command.get("live_order_allowed") is False
    command_credential_free = command.get("credential_required") is False
    entrypoint_exists = (root / "UPBIT_PAPER.py").exists() and "UPBIT_PAPER.py" in command_text
    duration_floor_met = (
        int(command.get("minimum_duration_hours", 0) or 0) >= MVP5_REVIEW_ENTRY_DURATION_HOURS
        and expected_ticks >= MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS
    )
    window_floor_met = (
        int(step.get("minimum_paper_shadow_window_count", 0) or 0)
        >= MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT
    )
    checks = [
        _check("STATE_ROUTE_RESIDUAL_OPERATOR_EVIDENCE", state.get("next_allowed_task_class") == NEXT_TASK_CLASS, "state remains on residual external-evidence/operator-reconciliation route"),
        _check("LIVE_AND_SCALE_FLAGS_FALSE", live_flags_false, "state, progress, and execution guide keep live/scale flags false"),
        _check("PROGRESS_REPORT_BLOCKED", progress_report.get("progress_status") == "BLOCKED_EVIDENCE_MISSING", "progress report remains blocked and does not close evidence"),
        _check("COMMAND_NON_LIVE_ONLY", command_non_live, "operator command is declared non-live and cannot allow live orders"),
        _check("COMMAND_CREDENTIAL_FREE", command_credential_free, "operator command is declared credential-free"),
        _check("COMMAND_NOT_EXECUTED_BY_PATCH", True, "this patch records preflight only and does not start the runtime command"),
        _check("ENTRYPOINT_EXISTS", entrypoint_exists, "UPBIT_PAPER.py entrypoint exists for the operator-run PAPER command"),
        _check(
            "ADAPTIVE_EVIDENCE_GATE_DECLARED",
            duration_floor_met,
            "operator command declares an adaptive evidence gate with no fixed duration floor",
        ),
        _check(
            "PAPER_SHADOW_WINDOW_FLOOR_DECLARED",
            window_floor_met,
            "operator command leaves PAPER/SHADOW window sufficiency to evidence validators",
        ),
        _check("EXPECTED_ARTIFACTS_DECLARED", len(expected_artifacts) >= 5, "required PAPER/SHADOW evidence artifacts are listed"),
        _check("NEXT_REVIEW_VALIDATORS_DECLARED", len(required_validators) >= 6, "next-review validators are listed"),
    ]
    completion_items = _completion_acceptance_matrix(expected_artifacts, required_validators)
    completion_pending_count = sum(1 for item in completion_items if item["evidence_ready_for_closure"] is False)
    completion_artifact_count = sum(1 for item in completion_items if item["acceptance_kind"] == "RUNTIME_ARTIFACT")
    completion_validator_count = sum(1 for item in completion_items if item["acceptance_kind"] == "VALIDATOR")
    blocked_count = sum(1 for item in checks if item["status"] != "PASS")
    status = "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS" if blocked_count == 0 else "BLOCKED_PREFLIGHT"
    env_overrides = [
        {"name": "TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS", "value": ticks_text},
        {"name": "TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS", "value": interval_text},
    ]
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": [
            _source_report_ref("residual_operator_execution_guide", execution_guide_report),
            _source_report_ref("residual_operator_evidence_progress", progress_report),
        ],
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "preflight_status": status,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "command_id": str(command.get("command_id", "")),
        "command_shell": str(command.get("shell", "")),
        "command_text": command_text,
        "command_scope": str(command.get("scope", "")),
        "command_entrypoint": "UPBIT_PAPER.py" if "UPBIT_PAPER.py" in command_text else "",
        "command_environment_overrides": env_overrides,
        "minimum_duration_hours": int(command.get("minimum_duration_hours", 0) or 0),
        "minimum_paper_shadow_window_count": int(step.get("minimum_paper_shadow_window_count", 0) or 0),
        "expected_heartbeat_ticks": expected_ticks,
        "heartbeat_interval_seconds": heartbeat_interval_seconds,
        "expected_runtime_artifacts": expected_artifacts,
        "required_validator_ids": required_validators,
        "operator_completion_acceptance_status": "PENDING_OPERATOR_RUNTIME_EVIDENCE",
        "operator_completion_acceptance_summary": (
            "PAPER/SHADOW run completion is not accepted by this preflight. The operator run must produce the listed "
            "runtime artifacts and every listed validator must PASS before any next review can consider evidence closure."
        ),
        "operator_completion_acceptance_items": completion_items,
        "operator_completion_acceptance_count": len(completion_items),
        "operator_completion_acceptance_pending_count": completion_pending_count,
        "operator_completion_acceptance_artifact_count": completion_artifact_count,
        "operator_completion_acceptance_validator_count": completion_validator_count,
        "preflight_checks": checks,
        "preflight_check_count": len(checks),
        "preflight_pass_count": len(checks) - blocked_count,
        "preflight_blocked_count": blocked_count,
        "non_live_operator_command_preflight_passed": blocked_count == 0,
        "credential_values_read": False,
        "credential_environment_inspection_performed": False,
        "command_executed_by_this_patch": False,
        "operator_run_started_by_this_patch": False,
        "operator_run_completed_by_this_patch": False,
        "operator_run_evidence_ready_for_mvp5": False,
        "mvp5_entry_blocked_until_operator_evidence": True,
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


def validate_residual_operator_evidence_run_preflight_report(
    report: Mapping[str, Any],
    execution_guide_report: Mapping[str, Any],
    progress_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    if report.get("schema_id") != SCHEMA_ID:
        errors.append("schema_id mismatch")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")
    if report.get("preflight_status") not in {"NON_LIVE_OPERATOR_RUN_PRECHECK_PASS", "BLOCKED_PREFLIGHT"}:
        errors.append("preflight_status is unknown")
    if execution_guide_report.get("guide_status") != "BLOCKED_GUIDE_ONLY":
        errors.append("source execution guide must remain blocked")
    if progress_report.get("progress_status") != "BLOCKED_EVIDENCE_MISSING":
        errors.append("source evidence progress must remain blocked")
    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
    for field in (
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
        "credential_values_read",
        "credential_environment_inspection_performed",
        "command_executed_by_this_patch",
        "operator_run_started_by_this_patch",
        "operator_run_completed_by_this_patch",
        "operator_run_evidence_ready_for_mvp5",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
    if report.get("mvp5_entry_blocked_until_operator_evidence") is not True:
        errors.append("mvp5 entry must stay blocked until operator evidence")
    if report.get("command_id") != MVP5_REVIEW_ENTRY_PROFILE_ID:
        errors.append("unexpected command_id")
    if report.get("command_shell") != "powershell":
        errors.append("operator command must be powershell")
    if report.get("command_entrypoint") != "UPBIT_PAPER.py":
        errors.append("operator command entrypoint mismatch")
    if "TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS=''" not in str(report.get("command_text", "")):
        errors.append("operator command must leave heartbeat ticks empty for adaptive evidence review")
    if report.get("minimum_duration_hours", 0) < MVP5_REVIEW_ENTRY_DURATION_HOURS:
        errors.append("minimum duration must not be negative")
    if report.get("minimum_paper_shadow_window_count", 0) < MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT:
        errors.append(
            f"minimum PAPER/SHADOW window count must be at least {MVP5_REVIEW_ENTRY_MINIMUM_PAPER_SHADOW_WINDOW_COUNT}"
        )
    if report.get("expected_heartbeat_ticks", 0) < MVP5_REVIEW_ENTRY_HEARTBEAT_TICKS:
        errors.append("expected heartbeat ticks must not be negative")
    if report.get("heartbeat_interval_seconds") != 10:
        errors.append("heartbeat interval must be 10 seconds")
    expected_artifacts = report.get("expected_runtime_artifacts", [])
    if not isinstance(expected_artifacts, list) or len(expected_artifacts) < 5:
        errors.append("expected runtime artifacts must list PAPER/SHADOW evidence outputs")
    else:
        for artifact in expected_artifacts:
            if not isinstance(artifact, Mapping):
                errors.append("expected artifact must be object")
                continue
            if artifact.get("evidence_ready_for_closure") is not False:
                errors.append("expected artifact cannot be ready for closure")
            if artifact.get("current_evidence_write_allowed") is not False:
                errors.append("expected artifact cannot allow current evidence write")
            if artifact.get("gap_closure_allowed_by_this_patch") is not False:
                errors.append("expected artifact cannot allow gap closure")
    completion_items = report.get("operator_completion_acceptance_items", [])
    if report.get("operator_completion_acceptance_status") != "PENDING_OPERATOR_RUNTIME_EVIDENCE":
        errors.append("operator completion acceptance status must remain pending")
    if not isinstance(report.get("operator_completion_acceptance_summary"), str) or not report.get(
        "operator_completion_acceptance_summary", ""
    ):
        errors.append("operator completion acceptance summary is required")
    if not isinstance(completion_items, list) or len(completion_items) < 12:
        errors.append("operator completion acceptance matrix must include artifacts, validators, and safety invariant")
    else:
        artifact_count = validator_count = pending_count = 0
        acceptance_ids: set[str] = set()
        for item in completion_items:
            if not isinstance(item, Mapping):
                errors.append("operator completion acceptance item must be object")
                continue
            acceptance_id = str(item.get("acceptance_id", ""))
            if not acceptance_id:
                errors.append("operator completion acceptance item missing acceptance_id")
            if acceptance_id in acceptance_ids:
                errors.append(f"duplicate operator completion acceptance_id {acceptance_id}")
            acceptance_ids.add(acceptance_id)
            if item.get("acceptance_kind") == "RUNTIME_ARTIFACT":
                artifact_count += 1
            elif item.get("acceptance_kind") == "VALIDATOR":
                validator_count += 1
            elif item.get("acceptance_kind") != "SAFETY_INVARIANT":
                errors.append("operator completion acceptance kind is unknown")
            for field in (
                "evidence_path",
                "responsible_validator_id",
                "current_preflight_status",
                "required_after_operator_run",
                "operator_message",
            ):
                if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                    errors.append(f"operator completion acceptance item missing {field}")
            for field in (
                "blocks_mvp5_entry_until_pass",
                "blocks_live_until_pass",
                "blocks_gap_closure_until_pass",
            ):
                if item.get(field) is not True:
                    errors.append(f"operator completion acceptance item must keep {field}=true")
            for field in (
                "evidence_ready_for_closure",
                "current_evidence_write_allowed",
                "gap_closure_allowed_by_this_patch",
                "live_ready_write_allowed",
                "live_order_ready",
                "live_order_allowed",
                "can_live_trade",
                "scale_up_allowed",
            ):
                if item.get(field) is not False:
                    errors.append(f"operator completion acceptance item must keep {field}=false")
            if item.get("evidence_ready_for_closure") is False:
                pending_count += 1
        if report.get("operator_completion_acceptance_count") != len(completion_items):
            errors.append("operator completion acceptance count mismatch")
        if report.get("operator_completion_acceptance_pending_count") != pending_count:
            errors.append("operator completion acceptance pending count mismatch")
        if report.get("operator_completion_acceptance_artifact_count") != artifact_count:
            errors.append("operator completion acceptance artifact count mismatch")
        if report.get("operator_completion_acceptance_validator_count") != validator_count:
            errors.append("operator completion acceptance validator count mismatch")
    validators = report.get("required_validator_ids", [])
    for validator_id in (
        "upbit_paper_persistent_loop_validator",
        "shadow_observation_persistent_runtime_validator",
        "paper_shadow_evidence_accumulation_validator",
        "profitability_evidence_maturity_rollup_validator",
        "runtime_schema_instance_validator",
        "live_final_guard_validator",
    ):
        if validator_id not in validators:
            errors.append(f"missing required validator {validator_id}")
    checks = report.get("preflight_checks", [])
    if not isinstance(checks, list) or report.get("preflight_check_count") != len(checks):
        errors.append("preflight check count mismatch")
    elif report.get("preflight_pass_count", 0) + report.get("preflight_blocked_count", 0) != len(checks):
        errors.append("preflight pass/blocked counts do not add up")
    if report.get("preflight_status") == "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS" and report.get("preflight_blocked_count") != 0:
        errors.append("passing preflight cannot contain blocked checks")
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids:
        errors.append("open_gap_ids must match current state")
    if report.get("validation_status") != "PASS" or report.get("validation_errors") != []:
        errors.append("validation status/errors mismatch")
    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
