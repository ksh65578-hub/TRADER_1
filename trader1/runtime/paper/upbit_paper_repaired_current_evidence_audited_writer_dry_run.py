from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_design import (
    AUDITED_WRITER_DESIGN_STATUS,
    validate_upbit_paper_repaired_current_evidence_audited_writer_design_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_SCHEMA_ID = (
    "trader1.upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.v1"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_ROLE = (
    "PAPER_RUNTIME_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_REVIEW_ONLY"
)
UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_TRUTH_ROLE = (
    "paper_runtime_repaired_current_evidence_audited_writer_dry_run_truth"
)
AUDITED_WRITER_DRY_RUN_STATUS = "BLOCKED_DRY_RUN_ONLY_WRITER_NOT_ENABLED"
SOURCE_DESIGN_INVALID_STATUS = "BLOCKED_SOURCE_DESIGN_INVALID"

REQUIRED_DRY_RUN_CHECK_IDS = [
    "SOURCE_AUDITED_WRITER_DESIGN_VALID",
    "PLANNED_WRITE_TARGETS_PRESENT",
    "PRE_WRITE_CHECKS_PRESENT",
    "POST_WRITE_CHECKS_PRESENT",
    "IDEMPOTENCY_DRY_RUN_DIGEST_CREATED",
    "CURRENT_EVIDENCE_SNAPSHOT_PREVIEW_CREATED",
    "PORTFOLIO_TRUTH_PREVIEW_CREATED",
    "ATOMIC_WRITE_PLAN_PREVIEW_CREATED",
    "LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
    "CURRENT_EVIDENCE_WRITE_APPROVAL_GRANTED",
]


@dataclass(frozen=True)
class UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("audited_writer_dry_run_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _check(
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
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _preview_hash(value: dict[str, Any]) -> str:
    return _sha256_json(value)


def build_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
    *,
    root: Path,
    source_audited_writer_design_report: dict[str, Any],
    audited_writer_dry_run_id: str = "upbit-paper-repaired-current-evidence-audited-writer-dry-run",
) -> dict[str, Any]:
    source_result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(
        source_audited_writer_design_report
    )
    session_id = str(source_audited_writer_design_report.get("session_id", "UNKNOWN"))
    planned_write_targets = list(source_audited_writer_design_report.get("planned_write_targets") or [])
    required_pre_write_checks = list(source_audited_writer_design_report.get("required_pre_write_checks") or [])
    required_post_write_checks = list(source_audited_writer_design_report.get("required_post_write_checks") or [])
    source_valid = (
        source_result.status == "PASS"
        and source_audited_writer_design_report.get("design_status") == AUDITED_WRITER_DESIGN_STATUS
        and source_audited_writer_design_report.get("primary_blocker_code")
        == AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        and source_audited_writer_design_report.get("writer_enabled") is False
        and source_audited_writer_design_report.get("current_evidence_write_allowed") is False
        and source_audited_writer_design_report.get("portfolio_truth_write_allowed") is False
        and source_audited_writer_design_report.get("live_order_allowed") is False
        and source_audited_writer_design_report.get("scale_up_allowed") is False
    )
    source_blocker = None if source_valid else (source_result.blocker_code or "AUDITED_WRITER_DESIGN_INVALID")
    snapshot_preview = {
        "preview_schema_id": "trader1.upbit_paper_current_evidence_snapshot_preview.v1",
        "preview_status": "DRY_RUN_ONLY_NOT_WRITTEN",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "configured_initial_cash_krw": 1000000,
        "configured_initial_cash_source": "PAPER_CONFIG_ONLY_UNVERIFIED",
        "cash_status": "UNVERIFIED",
        "equity_status": "UNVERIFIED",
        "portfolio_truth_status": "DRY_RUN_ONLY_UNVERIFIED",
        "ledger_head_status": "NOT_WRITTEN_BY_DRY_RUN",
        "runtime_cycle_status": "NOT_WRITTEN_BY_DRY_RUN",
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }
    portfolio_preview = {
        "preview_schema_id": "trader1.upbit_paper_portfolio_truth_preview.v1",
        "preview_status": "DRY_RUN_ONLY_NOT_WRITTEN",
        "portfolio_source_status": "UNVERIFIED_UNTIL_AUDITED_WRITER",
        "configured_initial_cash_krw": 1000000,
        "verified_cash_krw": None,
        "verified_equity_krw": None,
        "verified_total_pnl_krw": None,
        "verified_return_pct": None,
        "positions_verified": False,
        "candidates_verified": False,
        "current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_order_allowed": False,
        "scale_up_allowed": False,
    }
    snapshot_hash = _preview_hash(snapshot_preview)
    portfolio_hash = _preview_hash(portfolio_preview)
    dry_run_manifest = {
        "manifest_schema_id": "trader1.upbit_paper_audited_writer_dry_run_manifest.v1",
        "source_design_hash": source_audited_writer_design_report.get("audited_writer_design_hash"),
        "planned_write_targets": planned_write_targets,
        "required_pre_write_checks": required_pre_write_checks,
        "required_post_write_checks": required_post_write_checks,
        "current_evidence_snapshot_preview_hash": snapshot_hash,
        "portfolio_snapshot_preview_hash": portfolio_hash,
        "manifest_write_allowed": False,
    }
    dry_run_manifest["manifest_hash"] = _sha256_json(dry_run_manifest)
    checks = [
        _check(
            check_id="SOURCE_AUDITED_WRITER_DESIGN_VALID",
            check_status="PASS" if source_valid else "BLOCKED",
            blocker_code=source_blocker,
            detail="Dry-run input must be a validated review-only audited writer design report.",
        ),
        _check(
            check_id="PLANNED_WRITE_TARGETS_PRESENT",
            check_status="PASS" if planned_write_targets else "BLOCKED",
            blocker_code=None if planned_write_targets else "AUDITED_WRITER_DESIGN_INVALID",
            detail="Dry-run must preview the exact current-evidence and portfolio truth targets before any writer exists.",
        ),
        _check(
            check_id="PRE_WRITE_CHECKS_PRESENT",
            check_status="PASS" if required_pre_write_checks else "BLOCKED",
            blocker_code=None if required_pre_write_checks else "AUDITED_WRITER_DESIGN_INVALID",
            detail="Dry-run must carry pre-write checks for source hash, ledger head, writer lock, idempotency, and temp paths.",
        ),
        _check(
            check_id="POST_WRITE_CHECKS_PRESENT",
            check_status="PASS" if required_post_write_checks else "BLOCKED",
            blocker_code=None if required_post_write_checks else "AUDITED_WRITER_DESIGN_INVALID",
            detail="Dry-run must carry post-write validation, idempotency, reconciliation, and dashboard projection checks.",
        ),
        _check(
            check_id="IDEMPOTENCY_DRY_RUN_DIGEST_CREATED",
            check_status="PASS",
            blocker_code=None,
            detail="Dry-run creates a deterministic idempotency manifest preview without writing it as current evidence.",
        ),
        _check(
            check_id="CURRENT_EVIDENCE_SNAPSHOT_PREVIEW_CREATED",
            check_status="PASS",
            blocker_code=None,
            detail="Dry-run previews current-evidence fields and explicitly leaves configured PAPER cash unverified.",
        ),
        _check(
            check_id="PORTFOLIO_TRUTH_PREVIEW_CREATED",
            check_status="PASS",
            blocker_code=None,
            detail="Dry-run previews portfolio truth fields but does not verify or write cash, equity, PnL, positions, or candidates.",
        ),
        _check(
            check_id="ATOMIC_WRITE_PLAN_PREVIEW_CREATED",
            check_status="PASS",
            blocker_code=None,
            detail="Dry-run confirms the later writer must use temporary paths and atomic replace after validation.",
        ),
        _check(
            check_id="LIVE_AND_SCALE_BOUNDARY_CONFIRMED",
            check_status="PASS",
            blocker_code=None,
            detail="Dry-run output cannot create LIVE_READY, live order permission, live config mutation, or risk scale-up.",
        ),
        _check(
            check_id="CURRENT_EVIDENCE_WRITE_APPROVAL_GRANTED",
            check_status="BLOCKED",
            blocker_code=AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
            detail="Dry-run does not approve current-evidence or portfolio truth writes.",
        ),
    ]
    pass_count = sum(1 for check in checks if check["check_status"] == "PASS")
    blocked_count = sum(1 for check in checks if check["check_status"] == "BLOCKED")
    primary_blocker = (
        AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        if source_valid
        else (source_blocker or "AUDITED_WRITER_DESIGN_INVALID")
    )
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
        "schema_id": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "audited_writer_dry_run_id": audited_writer_dry_run_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_TRUTH_ROLE,
        "audited_writer_dry_run_role": UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_ROLE,
        "source_audited_writer_design_hash": source_audited_writer_design_report.get("audited_writer_design_hash"),
        "source_audited_writer_design_status": source_audited_writer_design_report.get("design_status"),
        "source_audited_writer_design_validator_status": source_result.status,
        "source_design_control_pass_count": int(source_audited_writer_design_report.get("design_control_pass_count") or 0),
        "source_design_control_blocked_count": int(
            source_audited_writer_design_report.get("design_control_blocked_count") or 0
        ),
        "source_design_current_evidence_write_allowed": source_audited_writer_design_report.get(
            "current_evidence_write_allowed"
        )
        is True,
        "source_design_portfolio_truth_write_allowed": source_audited_writer_design_report.get(
            "portfolio_truth_write_allowed"
        )
        is True,
        "dry_run_status": AUDITED_WRITER_DRY_RUN_STATUS if source_valid else SOURCE_DESIGN_INVALID_STATUS,
        "dry_run_passed": False,
        "dry_run_check_count": len(checks),
        "dry_run_check_pass_count": pass_count,
        "dry_run_check_blocked_count": blocked_count,
        "dry_run_checks": checks,
        "dry_run_manifest": dry_run_manifest,
        "current_evidence_snapshot_preview": snapshot_preview,
        "portfolio_snapshot_preview": portfolio_preview,
        "current_evidence_snapshot_preview_hash": snapshot_hash,
        "portfolio_snapshot_preview_hash": portfolio_hash,
        "planned_artifact_paths": planned_write_targets,
        "primary_blocker_code": primary_blocker,
        "blocker_codes": sorted(blocker_codes),
        "operator_next_action": "Review the dry-run manifest only; a separate audited writer patch is still required before any current-evidence or portfolio truth artifact can be written.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "dry_run_only": True,
        "separate_writer_patch_required": True,
        "writer_implementation_allowed": False,
        "writer_enabled": False,
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
        "audited_writer_dry_run_hash": "",
    }
    report["audited_writer_dry_run_hash"] = upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(report)
    return report


def write_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
    report: dict[str, Any],
) -> UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "audited_writer_dry_run_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "audited_writer_dry_run_role",
        "source_audited_writer_design_hash",
        "source_audited_writer_design_status",
        "source_audited_writer_design_validator_status",
        "source_design_control_pass_count",
        "source_design_control_blocked_count",
        "source_design_current_evidence_write_allowed",
        "source_design_portfolio_truth_write_allowed",
        "dry_run_status",
        "dry_run_passed",
        "dry_run_check_count",
        "dry_run_check_pass_count",
        "dry_run_check_blocked_count",
        "dry_run_checks",
        "dry_run_manifest",
        "current_evidence_snapshot_preview",
        "portfolio_snapshot_preview",
        "current_evidence_snapshot_preview_hash",
        "portfolio_snapshot_preview_hash",
        "planned_artifact_paths",
        "primary_blocker_code",
        "blocker_codes",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "dry_run_only",
        "separate_writer_patch_required",
        "writer_implementation_allowed",
        "writer_enabled",
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
        "audited_writer_dry_run_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", f"audited writer dry-run missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_SCHEMA_ID:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("audited_writer_dry_run_hash") != upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(
        report
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "BLOCKED", "audited writer dry-run scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if (
        report.get("truth_role") != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_TRUTH_ROLE
        or report.get("audited_writer_dry_run_role")
        != UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_ROLE
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "BLOCKED", "audited writer dry-run cannot claim writer truth authority", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "dry_run_passed",
        "source_design_current_evidence_write_allowed",
        "source_design_portfolio_truth_write_allowed",
        "writer_implementation_allowed",
        "writer_enabled",
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
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "BLOCKED", "audited writer dry-run attempted write, live, or scale permission", "LIVE_FINAL_GUARD_FAILED"
        )
    true_fields = ("display_only", "dashboard_truth_only", "paper_only", "dry_run_only", "separate_writer_patch_required")
    if any(report.get(field) is not True for field in true_fields):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "BLOCKED", "audited writer dry-run missing required safety boundary", "LIVE_FINAL_GUARD_FAILED"
        )
    checks = report.get("dry_run_checks")
    if not isinstance(checks, list) or report.get("dry_run_check_count") != len(checks):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run check count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_count = 0
    blocked_count = 0
    check_ids = []
    for check in checks:
        if not isinstance(check, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
                "FAIL", "audited writer dry-run check must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        check_ids.append(check.get("check_id"))
        if check.get("check_status") == "PASS":
            pass_count += 1
        elif check.get("check_status") == "BLOCKED":
            blocked_count += 1
        else:
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
                "FAIL", "audited writer dry-run check status unknown", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in (
            "current_evidence_write_allowed",
            "portfolio_truth_write_allowed",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        ):
            if check.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
                    "BLOCKED", "audited writer dry-run check attempted permission", "LIVE_FINAL_GUARD_FAILED"
                )
    if check_ids != REQUIRED_DRY_RUN_CHECK_IDS:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run check sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("dry_run_check_pass_count") != pass_count or report.get("dry_run_check_blocked_count") != blocked_count:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run aggregate counts mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if (
        report.get("dry_run_status") == AUDITED_WRITER_DRY_RUN_STATUS
        and (
            pass_count != len(REQUIRED_DRY_RUN_CHECK_IDS) - 1
            or blocked_count != 1
            or report.get("primary_blocker_code") != AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        )
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run blocker aggregate mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("dry_run_status") not in {AUDITED_WRITER_DRY_RUN_STATUS, SOURCE_DESIGN_INVALID_STATUS}:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("current_evidence_snapshot_preview_hash") != _preview_hash(
        report.get("current_evidence_snapshot_preview")
    ):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run current-evidence preview hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("portfolio_snapshot_preview_hash") != _preview_hash(report.get("portfolio_snapshot_preview")):
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run portfolio preview hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    manifest = report.get("dry_run_manifest")
    if not isinstance(manifest, dict) or manifest.get("manifest_write_allowed") is not False:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "BLOCKED", "audited writer dry-run manifest attempted write permission", "LIVE_FINAL_GUARD_FAILED"
        )
    expected_manifest_hash = _sha256_json({key: value for key, value in manifest.items() if key != "manifest_hash"})
    if manifest.get("manifest_hash") != expected_manifest_hash:
        return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
            "FAIL", "audited writer dry-run manifest hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    for preview in (report.get("current_evidence_snapshot_preview"), report.get("portfolio_snapshot_preview")):
        if not isinstance(preview, dict):
            return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
                "FAIL", "audited writer dry-run preview must be object", "SCHEMA_IDENTITY_MISMATCH"
            )
        for field in ("current_evidence_write_allowed", "portfolio_truth_write_allowed", "live_order_allowed", "scale_up_allowed"):
            if preview.get(field) is not False:
                return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
                    "BLOCKED", "audited writer dry-run preview attempted permission", "LIVE_FINAL_GUARD_FAILED"
                )
    return UpbitPaperRepairedCurrentEvidenceAuditedWriterDryRunValidationResult(
        "PASS", "audited writer dry-run preview is generated but no writer output is permitted", None
    )
