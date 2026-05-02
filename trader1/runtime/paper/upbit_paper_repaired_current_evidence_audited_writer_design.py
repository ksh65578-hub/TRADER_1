from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
    validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_SCHEMA_ID = (
    "trader1.upbit_paper_repaired_current_evidence_audited_writer_design_report.v1"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_ROLE = (
    "PAPER_RUNTIME_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_REVIEW_ONLY"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_TRUTH_ROLE = (
    "paper_runtime_repaired_current_evidence_audited_writer_design_truth"
)
AUDITED_WRITER_DESIGN_STATUS = "BLOCKED_DESIGN_ONLY_WRITER_NOT_IMPLEMENTED"
SOURCE_PRECHECK_INVALID_STATUS = "BLOCKED_SOURCE_PRECHECK_INVALID"

REQUIRED_CONTROL_IDS = [
    "SOURCE_AUDITED_WRITER_PRECHECK_VALID",
    "SINGLE_WRITER_LOCK_DISCIPLINE_SPECIFIED",
    "IDEMPOTENCY_MANIFEST_SPECIFIED",
    "ATOMIC_WRITE_RENAME_SPECIFIED",
    "POST_WRITE_RECONCILIATION_SPECIFIED",
    "PORTFOLIO_TRUTH_PROVENANCE_SPECIFIED",
    "LIVE_AND_SCALE_BOUNDARY_SPECIFIED",
    "WRITER_IMPLEMENTATION_APPROVED",
]


@dataclass(frozen=True)
class UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_repaired_current_evidence_audited_writer_design_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("audited_writer_design_hash", None)
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
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_repaired_current_evidence_audited_writer_design_report(
    *,
    root: Path,
    source_audited_writer_precheck_report: dict[str, Any],
    audited_writer_design_id: str = "upbit-paper-repaired-current-evidence-audited-writer-design",
) -> dict[str, Any]:
    source_result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
        source_audited_writer_precheck_report
    )
    session_id = str(source_audited_writer_precheck_report.get("session_id", "UNKNOWN"))
    source_valid = (
        source_result.status == "PASS"
        and source_audited_writer_precheck_report.get("audited_writer_precheck_status")
        == "BLOCKED_AUDITED_WRITER_DISABLED"
        and source_audited_writer_precheck_report.get("primary_blocker_code")
        == AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        and source_audited_writer_precheck_report.get("current_evidence_write_allowed") is False
        and source_audited_writer_precheck_report.get("portfolio_truth_write_allowed") is False
        and source_audited_writer_precheck_report.get("live_order_allowed") is False
        and source_audited_writer_precheck_report.get("scale_up_allowed") is False
    )
    controls = [
        _control(
            control_id="SOURCE_AUDITED_WRITER_PRECHECK_VALID",
            control_status="PASS" if source_valid else "BLOCKED",
            blocker_code=None if source_valid else (source_result.blocker_code or "AUDITED_WRITER_PRECHECK_INVALID"),
            detail="The audited writer design may only use a validated review-only writer precheck source.",
        ),
        _control(
            control_id="SINGLE_WRITER_LOCK_DISCIPLINE_SPECIFIED",
            control_status="PASS",
            blocker_code=None,
            detail="Future writer must acquire a scoped single-writer lock before creating any current-evidence artifact.",
        ),
        _control(
            control_id="IDEMPOTENCY_MANIFEST_SPECIFIED",
            control_status="PASS",
            blocker_code=None,
            detail="Future writer must hash source precheck, source guard, ledger head, and target paths into an idempotency manifest.",
        ),
        _control(
            control_id="ATOMIC_WRITE_RENAME_SPECIFIED",
            control_status="PASS",
            blocker_code=None,
            detail="Future writer must write to a temporary file, fsync where available, and publish with atomic replace only after validation.",
        ),
        _control(
            control_id="POST_WRITE_RECONCILIATION_SPECIFIED",
            control_status="PASS",
            blocker_code=None,
            detail="Future writer output must be reconciled against the source ledger and rejected on mismatch before dashboard trust.",
        ),
        _control(
            control_id="PORTFOLIO_TRUTH_PROVENANCE_SPECIFIED",
            control_status="PASS",
            blocker_code=None,
            detail="Future portfolio truth must carry source hashes, ledger head, runtime cycle id, and reconciliation report id.",
        ),
        _control(
            control_id="LIVE_AND_SCALE_BOUNDARY_SPECIFIED",
            control_status="PASS",
            blocker_code=None,
            detail="Design output cannot create LIVE_READY, live order permission, live config mutation, or risk scale-up.",
        ),
        _control(
            control_id="WRITER_IMPLEMENTATION_APPROVED",
            control_status="BLOCKED",
            blocker_code=AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
            detail="This patch specifies the writer design only; it does not implement or approve current-evidence writes.",
        ),
    ]
    pass_count = sum(1 for control in controls if control["control_status"] == "PASS")
    blocked_count = sum(1 for control in controls if control["control_status"] == "BLOCKED")
    primary_blocker = (
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        if source_valid
        else (source_result.blocker_code or "AUDITED_WRITER_PRECHECK_INVALID")
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
        "schema_id": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "audited_writer_design_id": audited_writer_design_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_TRUTH_ROLE,
        "audited_writer_design_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_ROLE,
        "source_audited_writer_precheck_hash": source_audited_writer_precheck_report.get(
            "audited_writer_precheck_hash"
        ),
        "source_audited_writer_precheck_status": source_audited_writer_precheck_report.get(
            "audited_writer_precheck_status"
        ),
        "source_audited_writer_precheck_validator_status": source_result.status,
        "source_audited_writer_candidate_ready_count": int(
            source_audited_writer_precheck_report.get("audited_writer_candidate_ready_count") or 0
        ),
        "source_audit_gate_pass_count": int(source_audited_writer_precheck_report.get("audit_gate_pass_count") or 0),
        "source_audit_gate_blocked_count": int(
            source_audited_writer_precheck_report.get("audit_gate_blocked_count") or 0
        ),
        "source_current_evidence_write_allowed": source_audited_writer_precheck_report.get(
            "current_evidence_write_allowed"
        )
        is True,
        "source_portfolio_truth_write_allowed": source_audited_writer_precheck_report.get(
            "portfolio_truth_write_allowed"
        )
        is True,
        "design_status": AUDITED_WRITER_DESIGN_STATUS if source_valid else SOURCE_PRECHECK_INVALID_STATUS,
        "design_passed": False,
        "design_control_count": len(controls),
        "design_control_pass_count": pass_count,
        "design_control_blocked_count": blocked_count,
        "design_controls": controls,
        "planned_write_targets": [
            "paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
            "paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
            "paper_runtime/portfolio/paper_portfolio_snapshot.json",
        ],
        "required_pre_write_checks": [
            "source_precheck_hash_match",
            "ledger_head_hash_match",
            "single_writer_lock_acquired",
            "idempotency_manifest_absent_or_equal",
            "target_temp_paths_clear",
        ],
        "required_post_write_checks": [
            "schema_validation_pass",
            "idempotency_manifest_hash_match",
            "post_write_reconciliation_pass",
            "dashboard_source_projection_pass",
        ],
        "primary_blocker_code": primary_blocker,
        "blocker_codes": sorted(blocker_codes),
        "operator_next_action": "Keep current-evidence and portfolio truth writes blocked; implement the audited writer in a separate patch that satisfies this design.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "design_only": True,
        "separate_writer_patch_required": True,
        "writer_implementation_allowed": False,
        "writer_enabled": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "portfolio_snapshot_write_allowed": False,
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
        "audited_writer_design_hash": "",
    }
    report["audited_writer_design_hash"] = upbit_paper_repaired_current_evidence_audited_writer_design_hash(report)
    return report


def write_upbit_paper_repaired_current_evidence_audited_writer_design_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_design_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(
    report: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audited_writer_design_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "audited_writer_design_role",
        "source_audited_writer_precheck_hash",
        "source_audited_writer_precheck_status",
        "source_audited_writer_precheck_validator_status",
        "source_audited_writer_candidate_ready_count",
        "source_audit_gate_pass_count",
        "source_audit_gate_blocked_count",
        "source_current_evidence_write_allowed",
        "source_portfolio_truth_write_allowed",
        "design_status",
        "design_passed",
        "design_control_count",
        "design_control_pass_count",
        "design_control_blocked_count",
        "design_controls",
        "planned_write_targets",
        "required_pre_write_checks",
        "required_post_write_checks",
        "primary_blocker_code",
        "blocker_codes",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "design_only",
        "separate_writer_patch_required",
        "writer_implementation_allowed",
        "writer_enabled",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
        "portfolio_snapshot_write_allowed",
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
        "audited_writer_design_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", f"audited writer design missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audited_writer_design_hash") != upbit_paper_repaired_current_evidence_audited_writer_design_hash(
        report
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "BLOCKED", "audited writer design scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_TRUTH_ROLE
        or report.get("audited_writer_design_role") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_ROLE
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "BLOCKED", "audited writer design cannot claim writer truth authority", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "design_passed",
        "source_current_evidence_write_allowed",
        "source_portfolio_truth_write_allowed",
        "writer_implementation_allowed",
        "writer_enabled",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
        "portfolio_snapshot_write_allowed",
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
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "BLOCKED", "audited writer design attempted write, live, or scale permission", "LIVE_FINAL_GUARD_FAILED"
        )
    true_fields = ("display_only", "dashboard_truth_only", "paper_only", "design_only", "separate_writer_patch_required")
    if any(report.get(field) is not True for field in true_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "BLOCKED", "audited writer design missing required safety boundary", "LIVE_FINAL_GUARD_FAILED"
        )
    controls = report.get("design_controls")
    if not isinstance(controls, list) or report.get("design_control_count") != len(controls):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design control count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_count = 0
    blocked_count = 0
    control_ids = []
    for control in controls:
        if not isinstance(control, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
                "FAIL", "audited writer design control must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        control_ids.append(control.get("control_id"))
        if control.get("control_status") == "PASS":
            pass_count += 1
        elif control.get("control_status") == "BLOCKED":
            blocked_count += 1
        else:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
                "FAIL", "audited writer design control status unknown", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "current_evidence_write_allowed",
            "portfolio_truth_write_allowed",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if control.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
                    "BLOCKED", "audited writer design control attempted permission", "LIVE_FINAL_GUARD_FAILED"
                )
    if control_ids != REQUIRED_CONTROL_IDS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design control sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("design_control_pass_count") != pass_count or report.get("design_control_blocked_count") != blocked_count:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design aggregate counts mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("design_status") == AUDITED_WRITER_DESIGN_STATUS
        and (
            pass_count != len(REQUIRED_CONTROL_IDS) - 1
            or blocked_count != 1
            or report.get("primary_blocker_code") != AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        )
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design blocker aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("design_status") not in {AUDITED_WRITER_DESIGN_STATUS, SOURCE_PRECHECK_INVALID_STATUS}:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    if not report.get("planned_write_targets") or not report.get("required_pre_write_checks") or not report.get(
        "required_post_write_checks"
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
            "FAIL", "audited writer design missing write plan controls", "SCHEMA_IDENTITY_MISMATCH"
        )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterDesignValidationResult(
        "PASS", "audited writer design is specified but writer remains disabled", None
    )
