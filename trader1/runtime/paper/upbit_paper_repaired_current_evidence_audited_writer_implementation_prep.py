from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_locked_output import (
    AUDITED_WRITER_LOCKED_OUTPUT_STATUS,
    validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_SCHEMA_ID = (
    "trader1.upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.v1"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_ROLE = (
    "PAPER_RUNTIME_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_REVIEW_ONLY"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_TRUTH_ROLE = (
    "paper_runtime_repaired_current_evidence_audited_writer_implementation_prep_truth"
)
AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS = "BLOCKED_IMPLEMENTATION_PREP_WRITER_NOT_ENABLED"
SOURCE_LOCKED_OUTPUT_INVALID_STATUS = "BLOCKED_SOURCE_LOCKED_OUTPUT_INVALID"
TARGET_STATE_DIRTY_STATUS = "BLOCKED_IMPLEMENTATION_PREP_TARGET_DIRTY"

REQUIRED_IMPLEMENTATION_PREP_CHECK_IDS = [
    "SOURCE_LOCKED_OUTPUT_VALID",
    "TARGET_PATHS_WITHIN_SESSION",
    "TEMP_PATHS_WITHIN_SESSION",
    "TARGET_OUTPUTS_ABSENT",
    "SINGLE_WRITER_LOCK_PRECHECKED",
    "PAYLOAD_HASHES_MATCH",
    "IDEMPOTENCY_MANIFEST_PREPARED",
    "POST_WRITE_RECONCILIATION_REQUIRED",
    "NO_RUNTIME_MUTATION_CONFIRMED",
    "LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
    "WRITER_ENABLEMENT_APPROVAL_GRANTED",
]


@dataclass(frozen=True)
class UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("audited_writer_implementation_prep_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _is_safe_relative_path(path: str) -> bool:
    candidate = Path(path)
    return (
        bool(path)
        and not candidate.is_absolute()
        and ".." not in candidate.parts
        and "\\" not in path
    )


def _is_under(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def _target_state(*, runtime_base: Path, relative_final_path: str, relative_temp_path: str) -> dict[str, Any]:
    final_path = runtime_base / relative_final_path
    temp_path = runtime_base / relative_temp_path
    final_safe = _is_safe_relative_path(relative_final_path) and _is_under(runtime_base, final_path)
    temp_safe = _is_safe_relative_path(relative_temp_path) and _is_under(runtime_base, temp_path)
    return {
        "relative_final_path": relative_final_path,
        "relative_temp_path": relative_temp_path,
        "final_path_resolves_under_session": final_safe,
        "temp_path_resolves_under_session": temp_safe,
        "final_exists": final_path.exists(),
        "temp_exists": temp_path.exists(),
        "parent_exists": final_path.parent.exists(),
        "artifact_write_allowed": False,
        "artifact_written": False,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }


def _prep_check(
    *,
    check_id: str,
    check_status: str,
    blocker_code: str | None,
    detail: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "check_status": check_status,
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


def _payload_hash_ok(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    expected = _sha256_json({key: value for key, value in payload.items() if key != "payload_hash"})
    return payload.get("payload_hash") == expected


def build_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
    *,
    root: Path,
    source_audited_writer_locked_output_report: dict[str, Any],
    audited_writer_implementation_prep_id: str = (
        "upbit-paper-repaired-current-evidence-audited-writer-implementation-prep"
    ),
) -> dict[str, Any]:
    source_result = validate_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
        source_audited_writer_locked_output_report
    )
    session_id = str(source_audited_writer_locked_output_report.get("session_id", "UNKNOWN"))
    runtime_base = _runtime_base(Path(root), session_id)
    planned_paths = list(source_audited_writer_locked_output_report.get("planned_artifact_paths") or [])
    planned_temp_paths = list(source_audited_writer_locked_output_report.get("planned_temp_paths") or [])
    expected_paths = [
        "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
        "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
        "paper_runtime/portfolio/paper_portfolio_snapshot.json",
    ]
    expected_temp_paths = [f"{path}.tmp" for path in expected_paths]
    source_valid = (
        source_result.status == "PASS"
        and source_audited_writer_locked_output_report.get("locked_output_status")
        == AUDITED_WRITER_LOCKED_OUTPUT_STATUS
        and source_audited_writer_locked_output_report.get("primary_blocker_code")
        == AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        and source_audited_writer_locked_output_report.get("writer_enabled") is False
        and source_audited_writer_locked_output_report.get("lock_acquired") is False
        and source_audited_writer_locked_output_report.get("lock_file_written") is False
        and source_audited_writer_locked_output_report.get("current_evidence_write_allowed") is False
        and source_audited_writer_locked_output_report.get("portfolio_truth_write_allowed") is False
        and source_audited_writer_locked_output_report.get("current_evidence_artifact_written") is False
        and source_audited_writer_locked_output_report.get("portfolio_truth_artifact_written") is False
        and source_audited_writer_locked_output_report.get("live_order_allowed") is False
        and source_audited_writer_locked_output_report.get("scale_up_allowed") is False
        and planned_paths == expected_paths
        and planned_temp_paths == expected_temp_paths
    )
    target_states = [
        _target_state(runtime_base=runtime_base, relative_final_path=final, relative_temp_path=temp)
        for final, temp in zip(planned_paths, planned_temp_paths, strict=False)
    ]
    target_paths_safe = len(target_states) == len(expected_paths) and all(
        state["final_path_resolves_under_session"] for state in target_states
    )
    temp_paths_safe = len(target_states) == len(expected_temp_paths) and all(
        state["temp_path_resolves_under_session"] for state in target_states
    )
    target_outputs_absent = all(
        not state["final_exists"] and not state["temp_exists"] for state in target_states
    )
    lock_path = str(source_audited_writer_locked_output_report.get("lock_path") or "")
    lock_path_safe = _is_safe_relative_path(lock_path) and _is_under(runtime_base, runtime_base / lock_path)
    current_payload = source_audited_writer_locked_output_report.get("current_evidence_locked_payload")
    portfolio_payload = source_audited_writer_locked_output_report.get("portfolio_truth_locked_payload")
    locked_manifest_payload = source_audited_writer_locked_output_report.get("idempotency_manifest_locked_payload")
    payload_hashes_match = (
        _payload_hash_ok(current_payload)
        and _payload_hash_ok(portfolio_payload)
        and _payload_hash_ok(locked_manifest_payload)
    )
    target_state_hash = _sha256_json(target_states)
    pre_write_manifest = {
        "manifest_schema_id": "trader1.upbit_paper_audited_writer_pre_write_idempotency_manifest.v1",
        "manifest_status": "PREPARED_NOT_WRITTEN",
        "source_audited_writer_locked_output_hash": source_audited_writer_locked_output_report.get(
            "audited_writer_locked_output_hash"
        ),
        "target_state_hash": target_state_hash,
        "current_evidence_locked_payload_hash": (current_payload or {}).get("payload_hash")
        if isinstance(current_payload, dict)
        else None,
        "portfolio_truth_locked_payload_hash": (portfolio_payload or {}).get("payload_hash")
        if isinstance(portfolio_payload, dict)
        else None,
        "locked_idempotency_manifest_payload_hash": (locked_manifest_payload or {}).get("payload_hash")
        if isinstance(locked_manifest_payload, dict)
        else None,
        "manifest_write_allowed": False,
        "artifact_written": False,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }
    pre_write_manifest["manifest_hash"] = _sha256_json(
        {key: value for key, value in pre_write_manifest.items() if key != "manifest_hash"}
    )
    manifest_prepared = (
        payload_hashes_match
        and pre_write_manifest["source_audited_writer_locked_output_hash"]
        == source_audited_writer_locked_output_report.get("audited_writer_locked_output_hash")
        and pre_write_manifest["manifest_write_allowed"] is False
    )
    prep_inputs_clean = (
        source_valid
        and target_paths_safe
        and temp_paths_safe
        and target_outputs_absent
        and lock_path_safe
        and payload_hashes_match
        and manifest_prepared
    )
    if not source_valid:
        prep_status = SOURCE_LOCKED_OUTPUT_INVALID_STATUS
        primary_blocker = source_result.blocker_code or "AUDITED_WRITER_LOCKED_OUTPUT_INVALID"
    elif not target_outputs_absent or not target_paths_safe or not temp_paths_safe or not lock_path_safe:
        prep_status = TARGET_STATE_DIRTY_STATUS
        primary_blocker = "POST_RERUN_RECONCILIATION_REQUIRED"
    else:
        prep_status = AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS
        primary_blocker = AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE

    checks = [
        _prep_check(
            check_id="SOURCE_LOCKED_OUTPUT_VALID",
            check_status="PASS" if source_valid else "BLOCKED",
            blocker_code=None if source_valid else primary_blocker,
            detail="Implementation prep must derive from a validated locked-output report only.",
        ),
        _prep_check(
            check_id="TARGET_PATHS_WITHIN_SESSION",
            check_status="PASS" if target_paths_safe else "BLOCKED",
            blocker_code=None if target_paths_safe else "SNAPSHOT_SCOPE_MISMATCH",
            detail="Every future final artifact path must resolve under the scoped UPBIT/KRW_SPOT/PAPER session.",
        ),
        _prep_check(
            check_id="TEMP_PATHS_WITHIN_SESSION",
            check_status="PASS" if temp_paths_safe else "BLOCKED",
            blocker_code=None if temp_paths_safe else "SNAPSHOT_SCOPE_MISMATCH",
            detail="Every future temporary artifact path must resolve under the scoped session and end in .tmp.",
        ),
        _prep_check(
            check_id="TARGET_OUTPUTS_ABSENT",
            check_status="PASS" if target_outputs_absent else "BLOCKED",
            blocker_code=None if target_outputs_absent else "POST_RERUN_RECONCILIATION_REQUIRED",
            detail="Implementation prep cannot overwrite existing current-evidence, idempotency, or portfolio truth outputs.",
        ),
        _prep_check(
            check_id="SINGLE_WRITER_LOCK_PRECHECKED",
            check_status="PASS" if lock_path_safe else "BLOCKED",
            blocker_code=None if lock_path_safe else "SNAPSHOT_SCOPE_MISMATCH",
            detail="The future writer lock path is scoped and checked without acquiring or writing the lock.",
        ),
        _prep_check(
            check_id="PAYLOAD_HASHES_MATCH",
            check_status="PASS" if payload_hashes_match else "BLOCKED",
            blocker_code=None if payload_hashes_match else "SCHEMA_IDENTITY_MISMATCH",
            detail="Locked current-evidence, idempotency, and portfolio payload hashes must still match.",
        ),
        _prep_check(
            check_id="IDEMPOTENCY_MANIFEST_PREPARED",
            check_status="PASS" if manifest_prepared else "BLOCKED",
            blocker_code=None if manifest_prepared else "SCHEMA_IDENTITY_MISMATCH",
            detail="A pre-write idempotency manifest preview is prepared but not written.",
        ),
        _prep_check(
            check_id="POST_WRITE_RECONCILIATION_REQUIRED",
            check_status="PASS",
            blocker_code=None,
            detail="A later writer must still run post-write reconciliation before dashboard portfolio trust.",
        ),
        _prep_check(
            check_id="NO_RUNTIME_MUTATION_CONFIRMED",
            check_status="PASS",
            blocker_code=None,
            detail="Implementation prep writes only its own report and never writes target artifacts or lock files.",
        ),
        _prep_check(
            check_id="LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
            check_status="PASS",
            blocker_code=None,
            detail="Implementation prep cannot create LIVE_READY, live order permission, live config mutation, or scale-up.",
        ),
        _prep_check(
            check_id="WRITER_ENABLEMENT_APPROVAL_GRANTED",
            check_status="BLOCKED",
            blocker_code=AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
            detail="The actual audited writer remains disabled until a separate implementation patch.",
        ),
    ]
    pass_count = sum(1 for check in checks if check["check_status"] == "PASS")
    blocked_count = sum(1 for check in checks if check["check_status"] == "BLOCKED")
    blocker_codes = {
        primary_blocker,
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
        "POST_RERUN_RECONCILIATION_REQUIRED",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    for check in checks:
        if check["blocker_code"]:
            blocker_codes.add(str(check["blocker_code"]))

    report = {
        "schema_id": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "audited_writer_implementation_prep_id": audited_writer_implementation_prep_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_TRUTH_ROLE,
        "audited_writer_implementation_prep_role": (
            UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_ROLE
        ),
        "source_audited_writer_locked_output_hash": source_audited_writer_locked_output_report.get(
            "audited_writer_locked_output_hash"
        ),
        "source_audited_writer_locked_output_status": source_audited_writer_locked_output_report.get(
            "locked_output_status"
        ),
        "source_audited_writer_locked_output_validator_status": source_result.status,
        "source_locked_output_control_pass_count": int(
            source_audited_writer_locked_output_report.get("locked_output_control_pass_count") or 0
        ),
        "source_locked_output_control_blocked_count": int(
            source_audited_writer_locked_output_report.get("locked_output_control_blocked_count") or 0
        ),
        "source_current_evidence_artifact_written": source_audited_writer_locked_output_report.get(
            "current_evidence_artifact_written"
        )
        is True,
        "source_portfolio_truth_artifact_written": source_audited_writer_locked_output_report.get(
            "portfolio_truth_artifact_written"
        )
        is True,
        "implementation_prep_status": prep_status,
        "implementation_prep_passed": False,
        "implementation_prep_check_count": len(checks),
        "implementation_prep_check_pass_count": pass_count,
        "implementation_prep_check_blocked_count": blocked_count,
        "implementation_prep_checks": checks,
        "implementation_prep_inputs_clean": prep_inputs_clean,
        "planned_artifact_paths": expected_paths,
        "planned_temp_paths": expected_temp_paths,
        "lock_path": lock_path,
        "target_states": target_states,
        "target_state_hash": target_state_hash,
        "pre_write_idempotency_manifest": pre_write_manifest,
        "primary_blocker_code": primary_blocker,
        "blocker_codes": sorted(blocker_codes),
        "operator_next_action": "Keep audited writer implementation prep review-only; a separate writer patch must still acquire the lock, write atomically, and reconcile before portfolio truth can be verified.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "implementation_prep_only": True,
        "separate_writer_patch_required": True,
        "writer_implementation_allowed": False,
        "writer_enabled": False,
        "lock_acquire_attempted": False,
        "lock_acquired": False,
        "lock_file_written": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_evidence_artifact_written": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "idempotency_manifest_write_allowed": False,
        "idempotency_manifest_written": False,
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
        "audited_writer_implementation_prep_hash": "",
    }
    report["audited_writer_implementation_prep_hash"] = (
        upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(report)
    )
    return report


def write_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def _validate_manifest(manifest: Any) -> str | None:
    if not isinstance(manifest, dict):
        return "implementation prep idempotency manifest must be object"
    expected_hash = _sha256_json({key: value for key, value in manifest.items() if key != "manifest_hash"})
    if manifest.get("manifest_hash") != expected_hash:
        return "implementation prep idempotency manifest hash mismatch"
    for field in (
        "manifest_write_allowed",
        "artifact_written",
        "current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "live_order_allowed",
        "scale_up_allowed",
    ):
        if manifest.get(field) is not False:
            return "implementation prep idempotency manifest attempted write, live, or scale permission"
    if manifest.get("manifest_status") != "PREPARED_NOT_WRITTEN":
        return "implementation prep idempotency manifest status mismatch"
    return None


def validate_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
    report: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audited_writer_implementation_prep_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "audited_writer_implementation_prep_role",
        "source_audited_writer_locked_output_hash",
        "source_audited_writer_locked_output_status",
        "source_audited_writer_locked_output_validator_status",
        "source_locked_output_control_pass_count",
        "source_locked_output_control_blocked_count",
        "source_current_evidence_artifact_written",
        "source_portfolio_truth_artifact_written",
        "implementation_prep_status",
        "implementation_prep_passed",
        "implementation_prep_check_count",
        "implementation_prep_check_pass_count",
        "implementation_prep_check_blocked_count",
        "implementation_prep_checks",
        "implementation_prep_inputs_clean",
        "planned_artifact_paths",
        "planned_temp_paths",
        "lock_path",
        "target_states",
        "target_state_hash",
        "pre_write_idempotency_manifest",
        "primary_blocker_code",
        "blocker_codes",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "implementation_prep_only",
        "separate_writer_patch_required",
        "writer_implementation_allowed",
        "writer_enabled",
        "lock_acquire_attempted",
        "lock_acquired",
        "lock_file_written",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_evidence_artifact_written",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "idempotency_manifest_write_allowed",
        "idempotency_manifest_written",
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
        "audited_writer_implementation_prep_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", f"audited writer implementation prep missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("schema_id")
        != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_SCHEMA_ID
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audited_writer_implementation_prep_hash") != (
        upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(report)
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "BLOCKED", "audited writer implementation prep scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role")
        != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_TRUTH_ROLE
        or report.get("audited_writer_implementation_prep_role")
        != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP_ROLE
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "BLOCKED",
            "audited writer implementation prep cannot claim writer truth authority",
            "LIVE_FINAL_GUARD_FAILED",
        )
    false_fields = (
        "implementation_prep_passed",
        "source_current_evidence_artifact_written",
        "source_portfolio_truth_artifact_written",
        "writer_implementation_allowed",
        "writer_enabled",
        "lock_acquire_attempted",
        "lock_acquired",
        "lock_file_written",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_evidence_artifact_written",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "idempotency_manifest_write_allowed",
        "idempotency_manifest_written",
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
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "BLOCKED",
            "audited writer implementation prep attempted write, live, or scale permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    true_fields = (
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "implementation_prep_only",
        "separate_writer_patch_required",
    )
    if any(report.get(field) is not True for field in true_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "BLOCKED", "audited writer implementation prep missing safety boundary", "LIVE_FINAL_GUARD_FAILED"
        )
    checks = report.get("implementation_prep_checks")
    if not isinstance(checks, list) or report.get("implementation_prep_check_count") != len(checks):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep check count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_count = 0
    blocked_count = 0
    check_ids = []
    for check in checks:
        if not isinstance(check, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
                "FAIL", "audited writer implementation prep check must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        check_ids.append(check.get("check_id"))
        if check.get("check_status") == "PASS":
            pass_count += 1
        elif check.get("check_status") == "BLOCKED":
            blocked_count += 1
        else:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
                "FAIL", "audited writer implementation prep check status unknown", "SCHEMA_IDENTITY_MISMATCH"
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
            if check.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
                    "BLOCKED",
                    "audited writer implementation prep check attempted permission",
                    "LIVE_FINAL_GUARD_FAILED",
                )
    if check_ids != REQUIRED_IMPLEMENTATION_PREP_CHECK_IDS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep check sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("implementation_prep_check_pass_count") != pass_count
        or report.get("implementation_prep_check_blocked_count") != blocked_count
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep aggregate counts mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("implementation_prep_status") == AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS
        and (
            pass_count != len(REQUIRED_IMPLEMENTATION_PREP_CHECK_IDS) - 1
            or blocked_count != 1
            or report.get("primary_blocker_code") != AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        )
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep blocker aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("implementation_prep_status") not in {
        AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS,
        SOURCE_LOCKED_OUTPUT_INVALID_STATUS,
        TARGET_STATE_DIRTY_STATUS,
    }:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("implementation_prep_status") != AUDITED_WRITER_IMPLEMENTATION_PREP_STATUS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "BLOCKED",
            "audited writer implementation prep source or target state is not clean",
            report.get("primary_blocker_code") or "LIVE_FINAL_GUARD_FAILED",
        )
    expected_paths = [
        "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
        "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
        "paper_runtime/portfolio/paper_portfolio_snapshot.json",
    ]
    if report.get("planned_artifact_paths") != expected_paths or report.get("planned_temp_paths") != [
        f"{path}.tmp" for path in expected_paths
    ]:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep target paths drifted", "SCHEMA_IDENTITY_MISMATCH"
        )
    states = report.get("target_states")
    if not isinstance(states, list) or len(states) != len(expected_paths):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep target states mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("target_state_hash") != _sha256_json(states):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "FAIL", "audited writer implementation prep target state hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for state in states:
        if not isinstance(state, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
                "FAIL", "audited writer implementation prep target state must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "final_path_resolves_under_session",
            "temp_path_resolves_under_session",
        ):
            if state.get(field) is not True:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
                    "BLOCKED", "audited writer implementation prep target escaped session", "SNAPSHOT_SCOPE_MISMATCH"
                )
        for field in (
            "final_exists",
            "temp_exists",
            "artifact_write_allowed",
            "artifact_written",
            "current_evidence_write_allowed",
            "portfolio_truth_write_allowed",
            "live_order_allowed",
            "scale_up_allowed",
        ):
            if state.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
                    "BLOCKED",
                    "audited writer implementation prep target attempted or detected output write",
                    "LIVE_FINAL_GUARD_FAILED",
                )
    manifest_error = _validate_manifest(report.get("pre_write_idempotency_manifest"))
    if manifest_error:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
            "BLOCKED", manifest_error, "LIVE_FINAL_GUARD_FAILED"
        )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterImplementationPrepValidationResult(
        "PASS",
        "audited writer implementation prep is review-only, target-safe, idempotency-prepared, and live-blocked",
        None,
    )
