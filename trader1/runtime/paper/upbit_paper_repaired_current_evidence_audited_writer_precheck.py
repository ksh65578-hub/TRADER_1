from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_repaired_current_evidence_audited_writer_precheck_report.v1"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_ROLE = (
    "PAPER_RUNTIME_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_REVIEW_ONLY"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_TRUTH_ROLE = (
    "paper_runtime_repaired_current_evidence_audited_writer_precheck_truth"
)
AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE = (
    "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED"
)
AUDITED_CURRENT_EVIDENCE_WRITER_PRECHECK_STATUS = "BLOCKED_AUDITED_WRITER_DISABLED"
SOURCE_GUARD_INVALID_STATUS = "BLOCKED_SOURCE_GUARD_INVALID"


@dataclass(frozen=True)
class UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("audited_writer_precheck_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _gate(
    *,
    gate_id: str,
    gate_status: str,
    gate_blocker_code: str | None,
    detail: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "gate_status": gate_status,
        "gate_blocker_code": gate_blocker_code,
        "detail": detail,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _false_source_flags(source_guard_report: dict[str, Any]) -> bool:
    false_fields = (
        "candidate_current_evidence_usable",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "portfolio_truth_write_allowed",
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
    return all(source_guard_report.get(field) is False for field in false_fields)


def build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
    *,
    root: Path,
    source_current_evidence_guard_report: dict[str, Any],
    audited_writer_precheck_id: str = "upbit-paper-repaired-current-evidence-audited-writer-precheck",
) -> dict[str, Any]:
    source_result = validate_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report(
        source_current_evidence_guard_report
    )
    session_id = str(source_current_evidence_guard_report.get("session_id", "UNKNOWN"))
    source_candidate_count = int(source_current_evidence_guard_report.get("candidate_count") or 0)
    source_guard_review_ready_count = int(source_current_evidence_guard_report.get("guard_review_ready_count") or 0)
    source_clean_candidate_count = int(source_current_evidence_guard_report.get("clean_candidate_count") or 0)
    source_duplicate_total_count = int(source_current_evidence_guard_report.get("duplicate_total_count") or 0)
    source_ledger_jsonl_count = int(source_current_evidence_guard_report.get("ledger_jsonl_count") or 0)
    source_ledger_event_count = int(source_current_evidence_guard_report.get("ledger_event_count") or 0)
    source_filled_order_count = int(source_current_evidence_guard_report.get("filled_order_count") or 0)
    source_write_counts_zero = (
        int(source_current_evidence_guard_report.get("current_evidence_write_allowed_count") or 0) == 0
        and int(source_current_evidence_guard_report.get("candidate_current_evidence_usable_count") or 0) == 0
        and int(source_current_evidence_guard_report.get("portfolio_truth_write_allowed_count") or 0) == 0
        and int(source_current_evidence_guard_report.get("operator_guidance_current_evidence_write_allowed_count") or 0)
        == 0
    )
    clean_inputs = (
        source_result.status == "PASS"
        and source_current_evidence_guard_report.get("current_evidence_guard_status")
        == "BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED"
        and source_candidate_count > 0
        and source_guard_review_ready_count == source_candidate_count
        and source_clean_candidate_count == source_candidate_count
        and source_duplicate_total_count == 0
        and source_ledger_jsonl_count > 0
        and source_ledger_event_count > 0
        and source_filled_order_count > 0
        and source_write_counts_zero
        and _false_source_flags(source_current_evidence_guard_report)
    )
    gates = [
        _gate(
            gate_id="SOURCE_CURRENT_EVIDENCE_GUARD_VALID",
            gate_status="PASS" if source_result.status == "PASS" else "BLOCKED",
            gate_blocker_code=None if source_result.status == "PASS" else source_result.blocker_code,
            detail="Source repaired current-evidence guard validates before any writer precheck.",
        ),
        _gate(
            gate_id="CLEAN_REPAIRED_CANDIDATES_PRESENT",
            gate_status="PASS"
            if source_candidate_count > 0
            and source_guard_review_ready_count == source_candidate_count
            and source_clean_candidate_count == source_candidate_count
            else "BLOCKED",
            gate_blocker_code=None
            if source_candidate_count > 0
            and source_guard_review_ready_count == source_candidate_count
            and source_clean_candidate_count == source_candidate_count
            else POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
            detail="Every repaired candidate must be clean, review-ready, and still current-evidence blocked.",
        ),
        _gate(
            gate_id="DUPLICATE_TOTAL_ZERO",
            gate_status="PASS" if source_duplicate_total_count == 0 else "BLOCKED",
            gate_blocker_code=None
            if source_duplicate_total_count == 0
            else POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
            detail="Duplicate event, dedup, and filled-order counts must remain zero.",
        ),
        _gate(
            gate_id="LEDGER_COUNTS_PRESENT",
            gate_status="PASS"
            if source_ledger_jsonl_count > 0 and source_ledger_event_count > 0 and source_filled_order_count > 0
            else "BLOCKED",
            gate_blocker_code=None
            if source_ledger_jsonl_count > 0 and source_ledger_event_count > 0 and source_filled_order_count > 0
            else "MEASUREMENT_MISSING",
            detail="Repaired candidates must still point to measurable PAPER ledger JSONL, events, and fills.",
        ),
        _gate(
            gate_id="SOURCE_WRITE_COUNTS_ZERO",
            gate_status="PASS" if source_write_counts_zero else "BLOCKED",
            gate_blocker_code=None if source_write_counts_zero else "LIVE_FINAL_GUARD_FAILED",
            detail="Source guard must expose zero current-evidence, usable-candidate, and portfolio-truth writes.",
        ),
        _gate(
            gate_id="SOURCE_LIVE_AND_SCALE_FALSE",
            gate_status="PASS" if _false_source_flags(source_current_evidence_guard_report) else "BLOCKED",
            gate_blocker_code=None if _false_source_flags(source_current_evidence_guard_report) else "LIVE_FINAL_GUARD_FAILED",
            detail="Source guard must keep all live, credential, order, promotion, long-run, and scale flags false.",
        ),
        _gate(
            gate_id="AUDITED_WRITER_IMPLEMENTATION_PRESENT",
            gate_status="BLOCKED",
            gate_blocker_code=AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
            detail="A separate audited current-evidence writer, lock discipline, idempotency manifest, and post-write reconciliation are not implemented in this patch.",
        ),
    ]
    gate_pass_count = sum(1 for gate in gates if gate["gate_status"] == "PASS")
    gate_blocked_count = sum(1 for gate in gates if gate["gate_status"] == "BLOCKED")
    primary_blocker = (
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        if clean_inputs
        else (source_result.blocker_code or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    )
    blocker_codes = {
        primary_blocker,
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    for gate in gates:
        if gate["gate_blocker_code"]:
            blocker_codes.add(str(gate["gate_blocker_code"]))
    report = {
        "schema_id": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "audited_writer_precheck_id": audited_writer_precheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_TRUTH_ROLE,
        "audited_writer_precheck_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_ROLE,
        "source_current_evidence_guard_hash": source_current_evidence_guard_report.get(
            "event_id_scope_repaired_current_evidence_guard_hash"
        ),
        "source_current_evidence_guard_status": source_current_evidence_guard_report.get(
            "current_evidence_guard_status"
        ),
        "source_current_evidence_guard_validator_status": source_result.status,
        "source_candidate_count": source_candidate_count,
        "source_guard_review_ready_count": source_guard_review_ready_count,
        "source_clean_candidate_count": source_clean_candidate_count,
        "source_duplicate_total_count": source_duplicate_total_count,
        "source_ledger_jsonl_count": source_ledger_jsonl_count,
        "source_ledger_event_count": source_ledger_event_count,
        "source_filled_order_count": source_filled_order_count,
        "source_current_evidence_write_allowed_count": int(
            source_current_evidence_guard_report.get("current_evidence_write_allowed_count") or 0
        ),
        "source_candidate_current_evidence_usable_count": int(
            source_current_evidence_guard_report.get("candidate_current_evidence_usable_count") or 0
        ),
        "source_portfolio_truth_write_allowed_count": int(
            source_current_evidence_guard_report.get("portfolio_truth_write_allowed_count") or 0
        ),
        "source_operator_guidance_current_evidence_write_allowed_count": int(
            source_current_evidence_guard_report.get("operator_guidance_current_evidence_write_allowed_count") or 0
        ),
        "audit_gate_count": len(gates),
        "audit_gate_pass_count": gate_pass_count,
        "audit_gate_blocked_count": gate_blocked_count,
        "audit_inputs_clean": clean_inputs,
        "audited_writer_precheck_status": AUDITED_CURRENT_EVIDENCE_WRITER_PRECHECK_STATUS
        if clean_inputs
        else SOURCE_GUARD_INVALID_STATUS,
        "audited_writer_precheck_passed": False,
        "audited_writer_enabled": False,
        "audited_writer_candidate_ready_count": source_guard_review_ready_count if clean_inputs else 0,
        "audit_gates": gates,
        "primary_blocker_code": primary_blocker,
        "blocker_codes": sorted(blocker_codes),
        "operator_next_action": "Keep current evidence writes blocked; implement a separate audited writer with locks, idempotency, and post-write reconciliation before portfolio truth can be considered.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
        "writer_precheck_only": True,
        "separate_writer_patch_required": True,
        "write_lock_required": True,
        "atomic_write_required": True,
        "idempotency_manifest_required": True,
        "post_write_reconciliation_required": True,
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
        "audited_writer_precheck_hash": "",
    }
    report["audited_writer_precheck_hash"] = upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(
        report
    )
    return report


def write_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
    report: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audited_writer_precheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "audited_writer_precheck_role",
        "source_current_evidence_guard_hash",
        "source_current_evidence_guard_status",
        "source_current_evidence_guard_validator_status",
        "source_candidate_count",
        "source_guard_review_ready_count",
        "source_clean_candidate_count",
        "source_duplicate_total_count",
        "source_ledger_jsonl_count",
        "source_ledger_event_count",
        "source_filled_order_count",
        "source_current_evidence_write_allowed_count",
        "source_candidate_current_evidence_usable_count",
        "source_portfolio_truth_write_allowed_count",
        "source_operator_guidance_current_evidence_write_allowed_count",
        "audit_gate_count",
        "audit_gate_pass_count",
        "audit_gate_blocked_count",
        "audit_inputs_clean",
        "audited_writer_precheck_status",
        "audited_writer_precheck_passed",
        "audited_writer_enabled",
        "audited_writer_candidate_ready_count",
        "audit_gates",
        "primary_blocker_code",
        "blocker_codes",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_only",
        "writer_precheck_only",
        "separate_writer_patch_required",
        "write_lock_required",
        "atomic_write_required",
        "idempotency_manifest_required",
        "post_write_reconciliation_required",
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
        "audited_writer_precheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", f"audited writer precheck missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", "audited writer precheck schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audited_writer_precheck_hash") != upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(
        report
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", "audited writer precheck hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_TRUTH_ROLE
        or report.get("audited_writer_precheck_role")
        != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_ROLE
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck cannot claim writer truth authority", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "audited_writer_precheck_passed",
        "audited_writer_enabled",
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
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck attempted write, live, or scale permission", "LIVE_FINAL_GUARD_FAILED"
        )
    true_fields = (
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_only",
        "writer_precheck_only",
        "separate_writer_patch_required",
        "write_lock_required",
        "atomic_write_required",
        "idempotency_manifest_required",
        "post_write_reconciliation_required",
    )
    if any(report.get(field) is not True for field in true_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck missing required safety boundary", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("source_current_evidence_write_allowed_count") != 0
        or report.get("source_candidate_current_evidence_usable_count") != 0
        or report.get("source_portfolio_truth_write_allowed_count") != 0
        or report.get("source_operator_guidance_current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck source write counts must remain zero", "LIVE_FINAL_GUARD_FAILED"
        )
    gates = report.get("audit_gates")
    if not isinstance(gates, list) or report.get("audit_gate_count") != len(gates):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", "audited writer precheck gate count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_count = 0
    blocked_count = 0
    gate_ids = []
    for gate in gates:
        if not isinstance(gate, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
                "FAIL", "audited writer precheck gate must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        gate_ids.append(gate.get("gate_id"))
        if gate.get("gate_status") == "PASS":
            pass_count += 1
        elif gate.get("gate_status") == "BLOCKED":
            blocked_count += 1
        else:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
                "FAIL", "audited writer precheck gate status unknown", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "current_evidence_write_allowed",
            "portfolio_truth_write_allowed",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if gate.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
                    "BLOCKED", "audited writer precheck gate attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED"
                )
    if gate_ids != [
        "SOURCE_CURRENT_EVIDENCE_GUARD_VALID",
        "CLEAN_REPAIRED_CANDIDATES_PRESENT",
        "DUPLICATE_TOTAL_ZERO",
        "LEDGER_COUNTS_PRESENT",
        "SOURCE_WRITE_COUNTS_ZERO",
        "SOURCE_LIVE_AND_SCALE_FALSE",
        "AUDITED_WRITER_IMPLEMENTATION_PRESENT",
    ]:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", "audited writer precheck gate order mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audit_gate_pass_count") != pass_count or report.get("audit_gate_blocked_count") != blocked_count:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", "audited writer precheck aggregate gate count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    clean_expected = pass_count == 6 and blocked_count == 1 and report.get("source_current_evidence_guard_validator_status") == "PASS"
    if report.get("audit_inputs_clean") is not clean_expected:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "FAIL", "audited writer precheck clean-input flag mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if clean_expected:
        if (
            report.get("audited_writer_precheck_status") != AUDITED_CURRENT_EVIDENCE_WRITER_PRECHECK_STATUS
            or report.get("primary_blocker_code")
            != AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
            or report.get("audited_writer_candidate_ready_count") != report.get("source_candidate_count")
            or report.get("source_candidate_count") <= 0
            or report.get("source_guard_review_ready_count") != report.get("source_candidate_count")
            or report.get("source_clean_candidate_count") != report.get("source_candidate_count")
            or report.get("source_duplicate_total_count") != 0
            or report.get("source_ledger_jsonl_count") <= 0
            or report.get("source_ledger_event_count") <= 0
            or report.get("source_filled_order_count") <= 0
        ):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
                "BLOCKED", "audited writer precheck clean source inputs did not preserve blocked writer status", "LIVE_FINAL_GUARD_FAILED"
            )
    elif report.get("audited_writer_precheck_status") != SOURCE_GUARD_INVALID_STATUS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck invalid source did not stay blocked", "LIVE_FINAL_GUARD_FAILED"
        )
    if AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
            "BLOCKED", "audited writer precheck missing writer implementation blocker", AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterPrecheckValidationResult(
        "PASS", "audited writer precheck validates clean inputs while keeping current evidence writes blocked", None
    )
