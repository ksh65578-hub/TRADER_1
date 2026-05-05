from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from trader1.reports.open_gap_current_blocker_classification import NEXT_TASK_CLASS


SCHEMA_ID = "trader1.residual_operator_handoff_packet_report.v1"
LIVE_FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

SOURCE_REPORT_ROLES = (
    "residual_open_gap_operator_action_plan",
    "residual_operator_evidence_audit_binding",
    "residual_paper_ledger_rerun_readiness",
    "external_live_evidence_intake_preflight",
)

ACTION_HANDOFF_TYPES = {
    "OPERATOR_RECONCILIATION_ACTION": "OPERATOR_RECONCILIATION",
    "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION": "PAPER_RERUN_RECONCILIATION",
    "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION": "PAPER_SHADOW_COLLECTION",
    "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION": "EXTERNAL_LIVE_EVIDENCE",
    "SEALED_BASELINE_PRESERVATION_ACTION": "SEALED_BASELINE_PRESERVATION",
    "SCALE_UP_POLICY_EVIDENCE_ACTION": "SCALE_UP_POLICY",
}


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _source_report_ref(role: str, report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": role,
        "patch_id": str(report.get("patch_id", "")),
        "report_hash": str(report.get("report_hash", "")),
    }


def _source_report_refs(
    action_plan_report: Mapping[str, Any],
    audit_binding_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
    external_preflight_report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _source_report_ref("residual_open_gap_operator_action_plan", action_plan_report),
        _source_report_ref("residual_operator_evidence_audit_binding", audit_binding_report),
        _source_report_ref("residual_paper_ledger_rerun_readiness", paper_rerun_readiness_report),
        _source_report_ref("external_live_evidence_intake_preflight", external_preflight_report),
    ]


def _linked_source_roles(action_class: str) -> list[str]:
    roles = [
        "residual_open_gap_operator_action_plan",
        "residual_operator_evidence_audit_binding",
    ]
    if action_class == "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION":
        roles.append("residual_paper_ledger_rerun_readiness")
    if action_class == "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION":
        roles.append("external_live_evidence_intake_preflight")
    return roles


def _external_packet_status(external_preflight_report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "external_blocked_requirement_count": int(external_preflight_report.get("blocked_requirement_count", 0)),
        "external_intake_ready_count": int(external_preflight_report.get("intake_ready_count", 0)),
        "external_missing_or_unusable_count": int(external_preflight_report.get("missing_or_unusable_count", 0)),
        "external_preflight_status": str(external_preflight_report.get("preflight_status", "UNKNOWN")),
    }


def _paper_packet_status(paper_rerun_readiness_report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "paper_ledger_rerun_readiness_status": str(
            paper_rerun_readiness_report.get("readiness_status", "UNKNOWN")
        ),
        "paper_post_rerun_reconciliation_status": str(
            paper_rerun_readiness_report.get("post_rerun_reconciliation_status", "UNKNOWN")
        ),
        "paper_current_evidence_bridge_status": str(
            paper_rerun_readiness_report.get("current_evidence_bridge_status", "UNKNOWN")
        ),
        "paper_current_evidence_write_allowed": paper_rerun_readiness_report.get("current_evidence_write_allowed")
        is True,
    }


def _build_handoff_packet(
    binding: Mapping[str, Any],
    external_preflight_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
) -> dict[str, Any]:
    action_class = str(binding.get("action_class", ""))
    handoff_type = ACTION_HANDOFF_TYPES.get(action_class, "UNKNOWN_HANDOFF")
    extra_status: dict[str, Any] = {}
    if action_class == "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION":
        extra_status.update(_external_packet_status(external_preflight_report))
    if action_class == "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION":
        extra_status.update(_paper_packet_status(paper_rerun_readiness_report))

    return {
        "packet_id": f"HANDOFF:{action_class}",
        "action_class": action_class,
        "handoff_type": handoff_type,
        "priority": int(binding.get("priority", 999) or 999),
        "gap_ids": sorted(str(gap_id) for gap_id in binding.get("gap_ids", [])),
        "gap_count": int(binding.get("gap_count", 0) or 0),
        "source_categories": [str(category) for category in binding.get("source_categories", [])],
        "required_evidence_kinds": [str(kind) for kind in binding.get("required_evidence_kinds", [])],
        "required_operator_action": str(binding.get("required_operator_action", "")),
        "closure_preconditions": [str(item) for item in binding.get("closure_preconditions", [])],
        "linked_source_report_roles": _linked_source_roles(action_class),
        "source_audit_binding_status": str(binding.get("audit_binding_status", "")),
        "handoff_status": "BLOCKED_HANDOFF_REQUIRED",
        "evidence_ready_for_closure": False,
        "operator_submission_required": action_class
        in {
            "OPERATOR_RECONCILIATION_ACTION",
            "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION",
            "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION",
        },
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_order_allowed": False,
        "live_config_mutation_allowed": False,
        "scale_up_allowed": False,
        "extra_status": extra_status,
    }


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def build_residual_operator_handoff_packet_report(
    action_plan_report: Mapping[str, Any],
    audit_binding_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
    external_preflight_report: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    patch_id: str,
    generated_at_utc: str,
    trader1_sha256: str,
    agents_sha256: str,
) -> dict[str, Any]:
    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    blocked_requirement_ids = sorted(str(item) for item in state.get("blocked_requirement_ids", []))
    handoff_packets = [
        _build_handoff_packet(binding, external_preflight_report, paper_rerun_readiness_report)
        for binding in audit_binding_report.get("audit_bindings", [])
        if isinstance(binding, Mapping)
    ]
    covered_gap_ids = sorted(gap_id for packet in handoff_packets for gap_id in packet["gap_ids"])
    duplicate_gap_ids = _duplicates(covered_gap_ids)
    unassigned_gap_ids = sorted(set(open_gap_ids) - set(covered_gap_ids))
    extra_gap_ids = sorted(set(covered_gap_ids) - set(open_gap_ids))
    blocked_packets = [packet for packet in handoff_packets if packet["handoff_status"] == "BLOCKED_HANDOFF_REQUIRED"]

    source_reports = _source_report_refs(
        action_plan_report,
        audit_binding_report,
        paper_rerun_readiness_report,
        external_preflight_report,
    )
    status_inputs_pass = (
        covered_gap_ids == open_gap_ids
        and not duplicate_gap_ids
        and not unassigned_gap_ids
        and not extra_gap_ids
        and len(handoff_packets) == int(audit_binding_report.get("action_binding_count", -1))
        and len(blocked_packets) == len(handoff_packets)
        and external_preflight_report.get("preflight_status") == "BLOCKED_EXTERNAL_EVIDENCE_MISSING"
        and external_preflight_report.get("intake_ready_count") == 0
        and paper_rerun_readiness_report.get("readiness_status") == "BLOCKED_RECONCILIATION_REQUIRED"
        and paper_rerun_readiness_report.get("current_evidence_write_allowed") is False
        and audit_binding_report.get("gap_closure_allowed_by_this_patch") is False
        and action_plan_report.get("implementation_recheck_action_count") == 0
    )

    report = {
        "schema_id": SCHEMA_ID,
        "patch_id": patch_id,
        "generated_at_utc": generated_at_utc,
        "authority": {
            "trader1_sha256": trader1_sha256,
            "agents_sha256": agents_sha256,
        },
        "source_reports": source_reports,
        "state_last_patch_id_before": str(state.get("last_patch_id", "")),
        "state_next_task_before": str(state.get("next_allowed_task_class", "")),
        "selected_next_task_class": NEXT_TASK_CLASS,
        "open_gap_ids": open_gap_ids,
        "open_gap_count": len(open_gap_ids),
        "covered_gap_ids": covered_gap_ids,
        "covered_gap_count": len(covered_gap_ids),
        "unassigned_gap_ids": unassigned_gap_ids,
        "extra_gap_ids": extra_gap_ids,
        "duplicate_gap_ids": duplicate_gap_ids,
        "blocked_requirement_ids": blocked_requirement_ids,
        "blocked_requirement_count": len(blocked_requirement_ids),
        "handoff_packet_count": len(handoff_packets),
        "blocked_handoff_packet_count": len(blocked_packets),
        "handoff_ready_count": 0,
        "implementation_recheck_action_count": int(action_plan_report.get("implementation_recheck_action_count", -1)),
        "external_intake_ready_count": int(external_preflight_report.get("intake_ready_count", -1)),
        "external_missing_or_unusable_count": int(external_preflight_report.get("missing_or_unusable_count", -1)),
        "paper_ledger_rerun_readiness_status": str(
            paper_rerun_readiness_report.get("readiness_status", "UNKNOWN")
        ),
        "paper_current_evidence_write_allowed": False,
        "operator_or_external_action_required": True,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "handoff_packets": handoff_packets,
        "handoff_status": "BLOCKED_HANDOFF_REQUIRED" if status_inputs_pass else "FAIL",
        "validation_status": "PASS" if status_inputs_pass else "FAIL",
        "validation_errors": [],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_residual_operator_handoff_packet_report(
    report: Mapping[str, Any],
    action_plan_report: Mapping[str, Any],
    audit_binding_report: Mapping[str, Any],
    paper_rerun_readiness_report: Mapping[str, Any],
    external_preflight_report: Mapping[str, Any],
    state: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    for field in LIVE_FALSE_FIELDS:
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")
        if state.get(field) is not False:
            errors.append(f"state {field} must remain false")
        for source_name, source in (
            ("action_plan", action_plan_report),
            ("audit_binding", audit_binding_report),
            ("paper_rerun_readiness", paper_rerun_readiness_report),
            ("external_preflight", external_preflight_report),
        ):
            if source.get(field) is not False:
                errors.append(f"{source_name} {field} must remain false")

    for field in (
        "paper_current_evidence_write_allowed",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "latest_runtime_pointer_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must remain false")

    expected_refs = _source_report_refs(
        action_plan_report,
        audit_binding_report,
        paper_rerun_readiness_report,
        external_preflight_report,
    )
    if report.get("source_reports") != expected_refs:
        errors.append("source_reports must bind exact source reports and hashes")
    if report.get("selected_next_task_class") != NEXT_TASK_CLASS:
        errors.append("selected_next_task_class mismatch")

    open_gap_ids = sorted(str(gap_id) for gap_id in state.get("open_contract_gap_ids", []))
    if report.get("open_gap_ids") != open_gap_ids:
        errors.append("open_gap_ids must match current implementation state")
    if report.get("open_gap_count") != len(open_gap_ids):
        errors.append("open_gap_count mismatch")
    if report.get("covered_gap_ids") != open_gap_ids:
        errors.append("covered_gap_ids must cover every current open gap exactly once")
    if report.get("covered_gap_count") != len(open_gap_ids):
        errors.append("covered_gap_count mismatch")
    if report.get("unassigned_gap_ids") != []:
        errors.append("unassigned_gap_ids must be empty")
    if report.get("extra_gap_ids") != []:
        errors.append("extra_gap_ids must be empty")
    if report.get("duplicate_gap_ids") != []:
        errors.append("duplicate_gap_ids must be empty")
    if report.get("implementation_recheck_action_count") != 0:
        errors.append("implementation_recheck_action_count must remain 0")
    if report.get("external_intake_ready_count") != 0:
        errors.append("external_intake_ready_count must remain 0")
    if report.get("paper_ledger_rerun_readiness_status") != "BLOCKED_RECONCILIATION_REQUIRED":
        errors.append("paper_ledger_rerun_readiness_status must remain BLOCKED_RECONCILIATION_REQUIRED")

    packets = report.get("handoff_packets", [])
    if not isinstance(packets, list):
        return errors + ["handoff_packets must be an array"]
    if report.get("handoff_packet_count") != len(packets):
        errors.append("handoff_packet_count mismatch")
    if report.get("blocked_handoff_packet_count") != len(packets):
        errors.append("blocked_handoff_packet_count must include every packet")
    if report.get("handoff_ready_count") != 0:
        errors.append("handoff_ready_count must remain 0")

    seen_gap_ids: list[str] = []
    for packet in packets:
        if not isinstance(packet, Mapping):
            errors.append("handoff_packets contains a non-object item")
            continue
        action_class = str(packet.get("action_class", ""))
        seen_gap_ids.extend(str(gap_id) for gap_id in packet.get("gap_ids", []))
        if packet.get("handoff_type") != ACTION_HANDOFF_TYPES.get(action_class):
            errors.append(f"{action_class} handoff_type mismatch")
        if packet.get("linked_source_report_roles") != _linked_source_roles(action_class):
            errors.append(f"{action_class} linked_source_report_roles mismatch")
        if packet.get("source_audit_binding_status") != "BOUND_BLOCKED":
            errors.append(f"{action_class} source_audit_binding_status must be BOUND_BLOCKED")
        if packet.get("handoff_status") != "BLOCKED_HANDOFF_REQUIRED":
            errors.append(f"{action_class} handoff_status must be BLOCKED_HANDOFF_REQUIRED")
        if packet.get("evidence_ready_for_closure") is not False:
            errors.append(f"{action_class} evidence_ready_for_closure must remain false")
        for field in (
            "current_evidence_write_allowed",
            "current_evidence_mutation_allowed",
            "latest_runtime_pointer_write_allowed",
            "gap_closure_allowed_by_this_patch",
            "live_order_allowed",
            "live_config_mutation_allowed",
            "scale_up_allowed",
        ):
            if packet.get(field) is not False:
                errors.append(f"{action_class} {field} must remain false")
        if action_class == "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION":
            extra = packet.get("extra_status", {})
            if extra.get("external_intake_ready_count") != 0:
                errors.append("external packet intake ready count must remain 0")
            if extra.get("external_preflight_status") != "BLOCKED_EXTERNAL_EVIDENCE_MISSING":
                errors.append("external packet preflight status mismatch")
        if action_class == "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION":
            extra = packet.get("extra_status", {})
            if extra.get("paper_current_evidence_write_allowed") is not False:
                errors.append("paper packet current evidence write must remain false")
            if extra.get("paper_ledger_rerun_readiness_status") != "BLOCKED_RECONCILIATION_REQUIRED":
                errors.append("paper packet readiness status mismatch")

    if sorted(seen_gap_ids) != open_gap_ids:
        errors.append("handoff_packets must cover current open gaps exactly once")
    if report.get("handoff_status") != "BLOCKED_HANDOFF_REQUIRED":
        errors.append("handoff_status must be BLOCKED_HANDOFF_REQUIRED")
    if report.get("validation_status") != "PASS":
        errors.append("validation_status must be PASS")
    if report.get("validation_errors") != []:
        errors.append("validation_errors must be empty")

    expected_hash = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    if report.get("report_hash") != expected_hash:
        errors.append("report_hash mismatch")
    return errors
