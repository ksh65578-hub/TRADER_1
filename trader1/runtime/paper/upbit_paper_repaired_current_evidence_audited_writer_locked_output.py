from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_dry_run import (
    AUDITED_WRITER_DRY_RUN_STATUS,
    validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_SCHEMA_ID = (
    "trader1.upbit_paper_repaired_current_evidence_audited_writer_locked_output_report.v1"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_ROLE = (
    "PAPER_RUNTIME_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_SCAFFOLD"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_TRUTH_ROLE = (
    "paper_runtime_repaired_current_evidence_audited_writer_locked_output_truth"
)
AUDITED_WRITER_LOCKED_OUTPUT_STATUS = "BLOCKED_LOCKED_OUTPUT_WRITER_NOT_ENABLED"
SOURCE_DRY_RUN_INVALID_STATUS = "BLOCKED_SOURCE_DRY_RUN_INVALID"

REQUIRED_LOCKED_OUTPUT_CONTROL_IDS = [
    "SOURCE_AUDITED_WRITER_DRY_RUN_VALID",
    "TARGET_NAMESPACE_LOCKED",
    "CURRENT_EVIDENCE_TARGET_LOCKED",
    "IDEMPOTENCY_MANIFEST_TARGET_LOCKED",
    "PORTFOLIO_TRUTH_TARGET_LOCKED",
    "ATOMIC_TEMP_TARGETS_LOCKED",
    "SINGLE_WRITER_LOCK_PATH_LOCKED",
    "OUTPUT_PAYLOAD_HASHES_LOCKED",
    "DASHBOARD_PROJECTION_LOCKED",
    "NO_RUNTIME_MUTATION_CONFIRMED",
    "LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
    "WRITER_OUTPUT_APPROVAL_GRANTED",
]


@dataclass(frozen=True)
class UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("audited_writer_locked_output_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _control(
    *,
    control_id: str,
    control_status: str,
    blocker_code: str | None,
    detail: str,
) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "control_status": control_status,
        "blocker_code": blocker_code,
        "detail": detail,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "artifact_write_allowed": False,
        "artifact_written": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _locked_payload(
    *,
    payload_schema_id: str,
    payload_role: str,
    relative_final_path: str,
    relative_temp_path: str,
    source_preview: dict[str, Any],
    source_preview_hash: str,
) -> dict[str, Any]:
    payload = {
        "payload_schema_id": payload_schema_id,
        "payload_role": payload_role,
        "payload_status": "LOCKED_NOT_WRITTEN",
        "relative_final_path": relative_final_path,
        "relative_temp_path": relative_temp_path,
        "source_preview_hash": source_preview_hash,
        "source_preview": source_preview,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "artifact_write_allowed": False,
        "artifact_written": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }
    payload["payload_hash"] = _sha256_json({key: value for key, value in payload.items() if key != "payload_hash"})
    return payload


def build_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
    *,
    root: Path,
    source_audited_writer_dry_run_report: dict[str, Any],
    audited_writer_locked_output_id: str = "upbit-paper-repaired-current-evidence-audited-writer-locked-output",
) -> dict[str, Any]:
    source_result = validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
        source_audited_writer_dry_run_report
    )
    session_id = str(source_audited_writer_dry_run_report.get("session_id", "UNKNOWN"))
    planned_paths = list(source_audited_writer_dry_run_report.get("planned_artifact_paths") or [])
    expected_paths = [
        "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
        "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
        "paper_runtime/portfolio/paper_portfolio_snapshot.json",
    ]
    source_valid = (
        source_result.status == "PASS"
        and source_audited_writer_dry_run_report.get("dry_run_status") == AUDITED_WRITER_DRY_RUN_STATUS
        and source_audited_writer_dry_run_report.get("primary_blocker_code")
        == AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        and source_audited_writer_dry_run_report.get("current_evidence_artifact_written") is False
        and source_audited_writer_dry_run_report.get("portfolio_truth_artifact_written") is False
        and source_audited_writer_dry_run_report.get("current_evidence_write_allowed") is False
        and source_audited_writer_dry_run_report.get("portfolio_truth_write_allowed") is False
        and source_audited_writer_dry_run_report.get("live_order_allowed") is False
        and source_audited_writer_dry_run_report.get("scale_up_allowed") is False
        and planned_paths == expected_paths
    )
    source_blocker = None if source_valid else (source_result.blocker_code or "AUDITED_WRITER_DRY_RUN_INVALID")

    current_payload = _locked_payload(
        payload_schema_id="trader1.upbit_paper_audited_current_evidence_locked_payload.v1",
        payload_role="CURRENT_EVIDENCE_SNAPSHOT_LOCKED_PAYLOAD_NOT_WRITTEN",
        relative_final_path=expected_paths[0],
        relative_temp_path=f"{expected_paths[0]}.tmp",
        source_preview=dict(source_audited_writer_dry_run_report.get("current_evidence_snapshot_preview") or {}),
        source_preview_hash=str(source_audited_writer_dry_run_report.get("current_evidence_snapshot_preview_hash")),
    )
    portfolio_payload = _locked_payload(
        payload_schema_id="trader1.upbit_paper_audited_portfolio_truth_locked_payload.v1",
        payload_role="PORTFOLIO_TRUTH_LOCKED_PAYLOAD_NOT_WRITTEN",
        relative_final_path=expected_paths[2],
        relative_temp_path=f"{expected_paths[2]}.tmp",
        source_preview=dict(source_audited_writer_dry_run_report.get("portfolio_snapshot_preview") or {}),
        source_preview_hash=str(source_audited_writer_dry_run_report.get("portfolio_snapshot_preview_hash")),
    )
    idempotency_manifest_locked_payload = {
        "payload_schema_id": "trader1.upbit_paper_audited_writer_idempotency_locked_manifest.v1",
        "payload_status": "LOCKED_NOT_WRITTEN",
        "relative_final_path": expected_paths[1],
        "relative_temp_path": f"{expected_paths[1]}.tmp",
        "source_audited_writer_dry_run_hash": source_audited_writer_dry_run_report.get(
            "audited_writer_dry_run_hash"
        ),
        "current_evidence_locked_payload_hash": current_payload["payload_hash"],
        "portfolio_truth_locked_payload_hash": portfolio_payload["payload_hash"],
        "manifest_write_allowed": False,
        "artifact_write_allowed": False,
        "artifact_written": False,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }
    idempotency_manifest_locked_payload["payload_hash"] = _sha256_json(
        {key: value for key, value in idempotency_manifest_locked_payload.items() if key != "payload_hash"}
    )
    locked_write_plan = {
        "plan_schema_id": "trader1.upbit_paper_audited_writer_locked_write_plan.v1",
        "plan_status": "LOCKED_NOT_WRITTEN",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "lock_path": "paper_runtime/locks/audited_current_evidence_writer.lock",
        "planned_artifact_paths": expected_paths,
        "planned_temp_paths": [f"{path}.tmp" for path in expected_paths],
        "locked_outputs": [
            {
                "artifact_id": "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
                "relative_final_path": expected_paths[0],
                "relative_temp_path": f"{expected_paths[0]}.tmp",
                "payload_hash": current_payload["payload_hash"],
                "artifact_write_allowed": False,
                "artifact_written": False,
            },
            {
                "artifact_id": "AUDITED_CURRENT_EVIDENCE_IDEMPOTENCY_MANIFEST",
                "relative_final_path": expected_paths[1],
                "relative_temp_path": f"{expected_paths[1]}.tmp",
                "payload_hash": idempotency_manifest_locked_payload["payload_hash"],
                "artifact_write_allowed": False,
                "artifact_written": False,
            },
            {
                "artifact_id": "AUDITED_PORTFOLIO_TRUTH_SNAPSHOT",
                "relative_final_path": expected_paths[2],
                "relative_temp_path": f"{expected_paths[2]}.tmp",
                "payload_hash": portfolio_payload["payload_hash"],
                "artifact_write_allowed": False,
                "artifact_written": False,
            },
        ],
        "plan_write_allowed": False,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }
    locked_write_plan["plan_hash"] = _sha256_json(
        {key: value for key, value in locked_write_plan.items() if key != "plan_hash"}
    )
    controls = [
        _control(
            control_id="SOURCE_AUDITED_WRITER_DRY_RUN_VALID",
            control_status="PASS" if source_valid else "BLOCKED",
            blocker_code=source_blocker,
            detail="Locked output scaffold must be derived from the validated dry-run report only.",
        ),
        _control(
            control_id="TARGET_NAMESPACE_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="All future targets remain scoped to UPBIT/KRW_SPOT/PAPER and the same session id.",
        ),
        _control(
            control_id="CURRENT_EVIDENCE_TARGET_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="The current-evidence snapshot final and temporary paths are fixed but not written.",
        ),
        _control(
            control_id="IDEMPOTENCY_MANIFEST_TARGET_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="The idempotency manifest final and temporary paths are fixed but not written.",
        ),
        _control(
            control_id="PORTFOLIO_TRUTH_TARGET_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="The portfolio truth final and temporary paths are fixed but not written.",
        ),
        _control(
            control_id="ATOMIC_TEMP_TARGETS_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="Every locked output has an adjacent temp path for a later atomic replace writer.",
        ),
        _control(
            control_id="SINGLE_WRITER_LOCK_PATH_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="The future writer lock path is fixed without acquiring or creating the lock.",
        ),
        _control(
            control_id="OUTPUT_PAYLOAD_HASHES_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="Locked payload hashes are deterministic and source-preview backed.",
        ),
        _control(
            control_id="DASHBOARD_PROJECTION_LOCKED",
            control_status="PASS",
            blocker_code=None,
            detail="Dashboard projection must still treat locked payloads as unverified until a separate writer exists.",
        ),
        _control(
            control_id="NO_RUNTIME_MUTATION_CONFIRMED",
            control_status="PASS",
            blocker_code=None,
            detail="This scaffold writes only its own report and never writes current evidence or portfolio truth.",
        ),
        _control(
            control_id="LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
            control_status="PASS",
            blocker_code=None,
            detail="Locked output scaffold cannot create LIVE_READY, live order permission, live config mutation, or scale-up.",
        ),
        _control(
            control_id="WRITER_OUTPUT_APPROVAL_GRANTED",
            control_status="BLOCKED",
            blocker_code=AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
            detail="Locked output scaffold does not approve writing current-evidence or portfolio truth artifacts.",
        ),
    ]
    pass_count = sum(1 for control in controls if control["control_status"] == "PASS")
    blocked_count = sum(1 for control in controls if control["control_status"] == "BLOCKED")
    primary_blocker = (
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        if source_valid
        else (source_blocker or "AUDITED_WRITER_DRY_RUN_INVALID")
    )
    blocker_codes = {
        primary_blocker,
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
        "POST_RERUN_RECONCILIATION_REQUIRED",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    for control in controls:
        if control["blocker_code"]:
            blocker_codes.add(str(control["blocker_code"]))

    report = {
        "schema_id": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "audited_writer_locked_output_id": audited_writer_locked_output_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_TRUTH_ROLE,
        "audited_writer_locked_output_role": (
            UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_ROLE
        ),
        "source_audited_writer_dry_run_hash": source_audited_writer_dry_run_report.get(
            "audited_writer_dry_run_hash"
        ),
        "source_audited_writer_dry_run_status": source_audited_writer_dry_run_report.get("dry_run_status"),
        "source_audited_writer_dry_run_validator_status": source_result.status,
        "source_dry_run_check_pass_count": int(
            source_audited_writer_dry_run_report.get("dry_run_check_pass_count") or 0
        ),
        "source_dry_run_check_blocked_count": int(
            source_audited_writer_dry_run_report.get("dry_run_check_blocked_count") or 0
        ),
        "source_current_evidence_artifact_written": source_audited_writer_dry_run_report.get(
            "current_evidence_artifact_written"
        )
        is True,
        "source_portfolio_truth_artifact_written": source_audited_writer_dry_run_report.get(
            "portfolio_truth_artifact_written"
        )
        is True,
        "locked_output_status": AUDITED_WRITER_LOCKED_OUTPUT_STATUS if source_valid else SOURCE_DRY_RUN_INVALID_STATUS,
        "locked_output_passed": False,
        "locked_output_control_count": len(controls),
        "locked_output_control_pass_count": pass_count,
        "locked_output_control_blocked_count": blocked_count,
        "locked_output_controls": controls,
        "locked_write_plan": locked_write_plan,
        "current_evidence_locked_payload": current_payload,
        "portfolio_truth_locked_payload": portfolio_payload,
        "idempotency_manifest_locked_payload": idempotency_manifest_locked_payload,
        "planned_artifact_paths": expected_paths,
        "planned_temp_paths": [f"{path}.tmp" for path in expected_paths],
        "lock_path": "paper_runtime/locks/audited_current_evidence_writer.lock",
        "primary_blocker_code": primary_blocker,
        "blocker_codes": sorted(blocker_codes),
        "operator_next_action": "Keep locked outputs review-only; a separate audited writer implementation is still required before current-evidence or portfolio truth writes.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "locked_output_only": True,
        "separate_writer_patch_required": True,
        "writer_implementation_allowed": False,
        "writer_enabled": False,
        "lock_acquired": False,
        "lock_file_written": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_evidence_artifact_written": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "portfolio_snapshot_write_allowed": False,
        "portfolio_truth_artifact_written": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "audited_writer_locked_output_hash": "",
    }
    report["audited_writer_locked_output_hash"] = (
        upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(report)
    )
    return report


def write_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_locked_output_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def _validate_payload(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return "locked payload must be object"
    expected_hash = _sha256_json({key: value for key, value in payload.items() if key != "payload_hash"})
    if payload.get("payload_hash") != expected_hash:
        return "locked payload hash mismatch"
    for field in (
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "artifact_write_allowed",
        "artifact_written",
        "live_order_allowed",
        "scale_up_allowed",
    ):
        if payload.get(field) is not False:
            return "locked payload attempted write, live, or scale permission"
    if payload.get("payload_status") != "LOCKED_NOT_WRITTEN":
        return "locked payload status mismatch"
    if not str(payload.get("relative_temp_path", "")).endswith(".tmp"):
        return "locked payload temp path must end with .tmp"
    return None


def validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
    report: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audited_writer_locked_output_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "audited_writer_locked_output_role",
        "source_audited_writer_dry_run_hash",
        "source_audited_writer_dry_run_status",
        "source_audited_writer_dry_run_validator_status",
        "source_dry_run_check_pass_count",
        "source_dry_run_check_blocked_count",
        "source_current_evidence_artifact_written",
        "source_portfolio_truth_artifact_written",
        "locked_output_status",
        "locked_output_passed",
        "locked_output_control_count",
        "locked_output_control_pass_count",
        "locked_output_control_blocked_count",
        "locked_output_controls",
        "locked_write_plan",
        "current_evidence_locked_payload",
        "portfolio_truth_locked_payload",
        "idempotency_manifest_locked_payload",
        "planned_artifact_paths",
        "planned_temp_paths",
        "lock_path",
        "primary_blocker_code",
        "blocker_codes",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "locked_output_only",
        "separate_writer_patch_required",
        "writer_implementation_allowed",
        "writer_enabled",
        "lock_acquired",
        "lock_file_written",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_evidence_artifact_written",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
        "portfolio_snapshot_write_allowed",
        "portfolio_truth_artifact_written",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "audited_writer_locked_output_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", f"audited writer locked output missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audited_writer_locked_output_hash") != (
        upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(report)
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "BLOCKED", "audited writer locked output scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_TRUTH_ROLE
        or report.get("audited_writer_locked_output_role")
        != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT_ROLE
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "BLOCKED", "audited writer locked output cannot claim writer truth authority", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "locked_output_passed",
        "source_current_evidence_artifact_written",
        "source_portfolio_truth_artifact_written",
        "writer_implementation_allowed",
        "writer_enabled",
        "lock_acquired",
        "lock_file_written",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_evidence_artifact_written",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
        "portfolio_snapshot_write_allowed",
        "portfolio_truth_artifact_written",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "BLOCKED", "audited writer locked output attempted write, live, or scale permission", "LIVE_FINAL_GUARD_FAILED"
        )
    true_fields = (
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "locked_output_only",
        "separate_writer_patch_required",
    )
    if any(report.get(field) is not True for field in true_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "BLOCKED", "audited writer locked output missing safety boundary", "LIVE_FINAL_GUARD_FAILED"
        )
    controls = report.get("locked_output_controls")
    if not isinstance(controls, list) or report.get("locked_output_control_count") != len(controls):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output control count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_count = 0
    blocked_count = 0
    control_ids = []
    for control in controls:
        if not isinstance(control, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
                "FAIL", "audited writer locked output control must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        control_ids.append(control.get("control_id"))
        if control.get("control_status") == "PASS":
            pass_count += 1
        elif control.get("control_status") == "BLOCKED":
            blocked_count += 1
        else:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
                "FAIL", "audited writer locked output control status unknown", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "current_evidence_write_allowed",
            "portfolio_truth_write_allowed",
            "artifact_write_allowed",
            "artifact_written",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if control.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
                    "BLOCKED", "audited writer locked output control attempted permission", "LIVE_FINAL_GUARD_FAILED"
                )
    if control_ids != REQUIRED_LOCKED_OUTPUT_CONTROL_IDS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output control sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("locked_output_control_pass_count") != pass_count
        or report.get("locked_output_control_blocked_count") != blocked_count
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output aggregate counts mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("locked_output_status") == AUDITED_WRITER_LOCKED_OUTPUT_STATUS
        and (
            pass_count != len(REQUIRED_LOCKED_OUTPUT_CONTROL_IDS) - 1
            or blocked_count != 1
            or report.get("primary_blocker_code") != AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        )
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output blocker aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("locked_output_status") not in {
        AUDITED_WRITER_LOCKED_OUTPUT_STATUS,
        SOURCE_DRY_RUN_INVALID_STATUS,
    }:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected_paths = [
        "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
        "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
        "paper_runtime/portfolio/paper_portfolio_snapshot.json",
    ]
    if report.get("planned_artifact_paths") != expected_paths:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output planned paths mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("planned_temp_paths") != [f"{path}.tmp" for path in expected_paths]:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output temp paths mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for payload_name in (
        "current_evidence_locked_payload",
        "portfolio_truth_locked_payload",
        "idempotency_manifest_locked_payload",
    ):
        payload_error = _validate_payload(report.get(payload_name))
        if payload_error:
            blocker = "LIVE_FINAL_GUARD_FAILED" if "permission" in payload_error else "SCHEMA_IDENTITY_MISMATCH"
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
                "BLOCKED" if blocker == "LIVE_FINAL_GUARD_FAILED" else "FAIL",
                payload_error,
                blocker,
            )
    plan = report.get("locked_write_plan")
    if not isinstance(plan, dict):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output plan must be object", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected_plan_hash = _sha256_json({key: value for key, value in plan.items() if key != "plan_hash"})
    if plan.get("plan_hash") != expected_plan_hash:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output plan hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for field in ("plan_write_allowed", "current_evidence_write_allowed", "portfolio_truth_write_allowed", "live_order_allowed", "scale_up_allowed"):
        if plan.get(field) is not False:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
                "BLOCKED", "audited writer locked output plan attempted permission", "LIVE_FINAL_GUARD_FAILED"
            )
    outputs = plan.get("locked_outputs")
    if not isinstance(outputs, list) or len(outputs) != 3:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
            "FAIL", "audited writer locked output plan outputs mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for output in outputs:
        if output.get("artifact_write_allowed") is not False or output.get("artifact_written") is not False:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
                "BLOCKED", "audited writer locked output output attempted write", "LIVE_FINAL_GUARD_FAILED"
            )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterLockedOutputValidationResult(
        "PASS", "audited writer locked output scaffold fixes future output boundaries without writing them", None
    )
