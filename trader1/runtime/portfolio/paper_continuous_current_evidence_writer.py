from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.paper.paper_runtime_truth_state import (
    PAPER_RUNTIME_ACTIVE_STATUS,
    validate_paper_runtime_truth_state_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    AUDITED_WRITER_IDEMPOTENT_STATUS,
    AUDITED_WRITER_WRITTEN_STATUS,
    validate_upbit_paper_audited_current_evidence_snapshot,
    validate_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.runtime.portfolio.paper_current_truth_refresh import (
    PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS,
    validate_paper_current_truth_refresh_report,
)
from trader1.runtime.portfolio.paper_portfolio import validate_paper_portfolio_snapshot


PAPER_CONTINUOUS_CURRENT_EVIDENCE_WRITER_SCHEMA_ID = (
    "trader1.paper_continuous_current_evidence_writer_report.v1"
)
PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS = "NOT_IMPLEMENTED"
PAPER_CONTINUOUS_WRITER_IMPLEMENTED_BLOCKED_STATUS = "IMPLEMENTED_BLOCKED"
PAPER_CONTINUOUS_WRITER_WRITING_STATUS = "IMPLEMENTED_WRITING_PAPER_CURRENT_TRUTH"
PAPER_CONTINUOUS_WRITER_STALE_STATUS = "IMPLEMENTED_STALE"
PAPER_CONTINUOUS_WRITER_STATUSES = {
    PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS,
    PAPER_CONTINUOUS_WRITER_IMPLEMENTED_BLOCKED_STATUS,
    PAPER_CONTINUOUS_WRITER_WRITING_STATUS,
    PAPER_CONTINUOUS_WRITER_STALE_STATUS,
}
PAPER_CONTINUOUS_WRITER_TRUTH_ROLE = "PAPER_CONTINUOUS_CURRENT_EVIDENCE_WRITER_STATUS_NOT_LIVE_READY"
PAPER_CONTINUOUS_WRITER_FRESHNESS_STATUSES = {
    "FRESH",
    "DELAYED",
    "STALE_DISPLAY_ONLY",
    "INVALID",
}
DEFAULT_CONTINUOUS_WRITER_STALE_AFTER_SECONDS = 300
DEFAULT_CONTINUOUS_WRITER_DELAYED_AFTER_SECONDS = 60


@dataclass(frozen=True)
class PaperContinuousCurrentEvidenceWriterValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_seconds(*, generated_at_utc: Any, now_utc: str) -> int | None:
    generated = _parse_utc(generated_at_utc)
    now = _parse_utc(now_utc)
    if generated is None or now is None:
        return None
    return max(0, int((now - generated).total_seconds()))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def paper_continuous_current_evidence_writer_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("continuous_writer_report_hash", None)
    return _sha256_json(payload)


def _hash_from(report: dict[str, Any] | None, field: str) -> str | None:
    if not isinstance(report, dict):
        return None
    value = report.get(field)
    return value if isinstance(value, str) and len(value) == 64 else None


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _source_age_candidates(
    *reports: dict[str, Any] | None,
    now_utc: str,
) -> list[int]:
    ages: list[int] = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        age = _age_seconds(generated_at_utc=report.get("generated_at_utc"), now_utc=now_utc)
        if age is not None:
            ages.append(age)
    return ages


def _freshness_status(age_seconds: int | None, delayed_after_seconds: int, stale_after_seconds: int) -> str:
    if age_seconds is None:
        return "INVALID"
    if age_seconds > stale_after_seconds:
        return "STALE_DISPLAY_ONLY"
    if age_seconds > delayed_after_seconds:
        return "DELAYED"
    return "FRESH"


def build_paper_continuous_current_evidence_writer_report(
    *,
    exchange: str,
    market_type: str,
    mode: str,
    session_id: str,
    audited_writer_report: dict[str, Any] | None,
    audited_current_evidence_snapshot: dict[str, Any] | None,
    audited_paper_portfolio_snapshot: dict[str, Any] | None,
    paper_current_truth_refresh_report: dict[str, Any] | None,
    paper_runtime_truth_state_report: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
    delayed_after_seconds: int = DEFAULT_CONTINUOUS_WRITER_DELAYED_AFTER_SECONDS,
    stale_after_seconds: int = DEFAULT_CONTINUOUS_WRITER_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    now = generated_at_utc or utc_now()
    blockers: list[dict[str, str]] = []
    paper_scope = exchange == "UPBIT" and market_type == "KRW_SPOT" and mode == "PAPER"
    if not paper_scope:
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "continuous current-evidence writer is PAPER-only"))

    writer_result = (
        validate_upbit_paper_repaired_current_evidence_audited_writer_report(audited_writer_report)
        if isinstance(audited_writer_report, dict)
        else None
    )
    current_result = (
        validate_upbit_paper_audited_current_evidence_snapshot(audited_current_evidence_snapshot)
        if isinstance(audited_current_evidence_snapshot, dict)
        else None
    )
    portfolio_result = (
        validate_paper_portfolio_snapshot(audited_paper_portfolio_snapshot)
        if isinstance(audited_paper_portfolio_snapshot, dict)
        else None
    )
    refresh_result = (
        validate_paper_current_truth_refresh_report(paper_current_truth_refresh_report)
        if isinstance(paper_current_truth_refresh_report, dict)
        else None
    )
    runtime_result = (
        validate_paper_runtime_truth_state_report(paper_runtime_truth_state_report)
        if isinstance(paper_runtime_truth_state_report, dict)
        else None
    )

    writer_source_present = isinstance(audited_writer_report, dict)
    writer_source_valid = bool(
        paper_scope
        and writer_result is not None
        and writer_result.status == "PASS"
        and audited_writer_report.get("writer_status") in {AUDITED_WRITER_WRITTEN_STATUS, AUDITED_WRITER_IDEMPOTENT_STATUS}
        and audited_writer_report.get("writer_passed") is True
        and audited_writer_report.get("current_evidence_artifact_written") is True
        and audited_writer_report.get("idempotency_manifest_written") is True
        and audited_writer_report.get("portfolio_truth_artifact_written") is True
        and audited_writer_report.get("live_order_ready") is False
        and audited_writer_report.get("live_order_allowed") is False
        and audited_writer_report.get("can_live_trade") is False
        and audited_writer_report.get("scale_up_allowed") is False
    )
    current_snapshot_valid = bool(
        paper_scope
        and current_result is not None
        and current_result.status == "PASS"
        and audited_current_evidence_snapshot.get("current_evidence_status") == "PASS"
    )
    portfolio_valid = bool(
        paper_scope
        and portfolio_result is not None
        and portfolio_result.status == "PASS"
        and audited_paper_portfolio_snapshot.get("snapshot_status") == "PASS"
        and audited_paper_portfolio_snapshot.get("paper_only") is True
    )
    refresh_valid = bool(
        paper_scope
        and refresh_result is not None
        and refresh_result.status == "PASS"
        and paper_current_truth_refresh_report.get("refresh_status") == PAPER_CURRENT_TRUTH_REFRESH_PASS_STATUS
        and paper_current_truth_refresh_report.get("refresh_passed") is True
    )
    runtime_truth_active = bool(
        paper_scope
        and runtime_result is not None
        and runtime_result.status == "PASS"
        and paper_runtime_truth_state_report.get("runtime_truth_status") == PAPER_RUNTIME_ACTIVE_STATUS
    )

    hash_bound = False
    if writer_source_valid and current_snapshot_valid and portfolio_valid and refresh_valid:
        hash_bound = (
            audited_current_evidence_snapshot.get("source_ledger_rollup_hash")
            == audited_writer_report.get("source_ledger_rollup_hash")
            and audited_current_evidence_snapshot.get("source_paper_ledger_head_hash")
            == audited_writer_report.get("source_paper_ledger_head_hash")
            == audited_paper_portfolio_snapshot.get("source_paper_ledger_head_hash")
            == paper_current_truth_refresh_report.get("source_paper_ledger_head_hash")
            and audited_current_evidence_snapshot.get("source_runtime_cycle_id")
            == audited_writer_report.get("source_runtime_cycle_id")
            == audited_paper_portfolio_snapshot.get("source_runtime_cycle_id")
            == paper_current_truth_refresh_report.get("source_runtime_cycle_id")
            and audited_current_evidence_snapshot.get("source_portfolio_snapshot_hash")
            == audited_paper_portfolio_snapshot.get("snapshot_hash")
            and paper_current_truth_refresh_report.get("source_portfolio_snapshot_hash")
            in {audited_paper_portfolio_snapshot.get("snapshot_hash"), audited_writer_report.get("source_portfolio_snapshot_hash")}
        )
    if paper_scope and not writer_source_present:
        blockers.append(_blocker("AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED", "audited writer report is not loaded"))
    elif paper_scope and not writer_source_valid:
        blockers.append(
            _blocker(
                writer_result.blocker_code if writer_result is not None else "SCHEMA_IDENTITY_MISMATCH",
                "audited writer source is blocked or invalid",
            )
        )
    if paper_scope and not current_snapshot_valid:
        blockers.append(
            _blocker(
                current_result.blocker_code if current_result is not None else "MEASUREMENT_MISSING",
                "audited current-evidence snapshot is missing or invalid",
            )
        )
    if paper_scope and not portfolio_valid:
        blockers.append(
            _blocker(
                portfolio_result.blocker_code if portfolio_result is not None else "MEASUREMENT_MISSING",
                "audited PAPER portfolio snapshot is missing or invalid",
            )
        )
    if paper_scope and not refresh_valid:
        blockers.append(
            _blocker(
                refresh_result.blocker_code if refresh_result is not None else "HARD_TRUTH_MISSING",
                "PAPER current-truth refresh report is missing, blocked, or invalid",
            )
        )
    if paper_scope and writer_source_valid and current_snapshot_valid and portfolio_valid and refresh_valid and not hash_bound:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "continuous writer sources are not hash-bound"))

    ages = _source_age_candidates(
        audited_writer_report,
        audited_current_evidence_snapshot,
        paper_current_truth_refresh_report,
        now_utc=now,
    )
    max_source_age_seconds = max(ages) if ages else None
    truth_freshness_status = _freshness_status(max_source_age_seconds, delayed_after_seconds, stale_after_seconds)
    sources_clean = (
        paper_scope
        and writer_source_valid
        and current_snapshot_valid
        and portfolio_valid
        and refresh_valid
        and hash_bound
        and not any(blocker["code"] not in {"STALE_CURRENT_TRUTH"} for blocker in blockers)
    )
    if sources_clean and truth_freshness_status in {"FRESH", "DELAYED"}:
        continuous_writer_status = PAPER_CONTINUOUS_WRITER_WRITING_STATUS
        primary_blocker_code = "LIVE_READY_MISSING"
        writer_active = True
        blockers = []
        summary = "Continuous PAPER current-evidence writer is implemented and refreshing audited PAPER truth."
        next_action = "Keep collecting PAPER/SHADOW evidence; live orders and scale-up remain blocked."
    elif sources_clean and truth_freshness_status == "STALE_DISPLAY_ONLY":
        continuous_writer_status = PAPER_CONTINUOUS_WRITER_STALE_STATUS
        primary_blocker_code = "STALE_CURRENT_TRUTH"
        writer_active = False
        blockers = [_blocker("STALE_CURRENT_TRUTH", "audited PAPER current-evidence writer output is stale", "MEDIUM")]
        summary = "Continuous PAPER current-evidence writer is implemented, but the last verified truth is stale."
        next_action = "Regenerate PAPER current truth before treating the displayed portfolio as current."
    elif paper_scope and not writer_source_present:
        continuous_writer_status = PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS
        primary_blocker_code = "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED"
        writer_active = False
        summary = "Continuous PAPER current-evidence writer report is present, but no source writer output is loaded."
        next_action = "Run the scoped PAPER launcher so it can build the audited writer output from ledger-backed sources."
    else:
        continuous_writer_status = PAPER_CONTINUOUS_WRITER_IMPLEMENTED_BLOCKED_STATUS
        primary_blocker_code = blockers[0]["code"] if blockers else "HARD_TRUTH_MISSING"
        writer_active = False
        summary = "Continuous PAPER current-evidence writer is implemented but blocked by source validation."
        next_action = "Resolve the listed PAPER source blocker before using current evidence as fresh truth."

    configured_capital = (
        audited_paper_portfolio_snapshot.get("starting_cash") if portfolio_valid else None
    )
    last_verified_equity = (
        audited_paper_portfolio_snapshot.get("equity") if portfolio_valid else None
    )
    current_refreshed_equity = (
        paper_current_truth_refresh_report.get("verified_equity")
        if continuous_writer_status == PAPER_CONTINUOUS_WRITER_WRITING_STATUS
        else None
    )
    stale_display_equity = (
        last_verified_equity if continuous_writer_status == PAPER_CONTINUOUS_WRITER_STALE_STATUS else None
    )

    report = {
        "schema_id": PAPER_CONTINUOUS_CURRENT_EVIDENCE_WRITER_SCHEMA_ID,
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "exchange": exchange,
        "market_type": market_type,
        "mode": mode,
        "session_id": session_id,
        "continuous_writer_status": continuous_writer_status,
        "truth_freshness_status": truth_freshness_status,
        "writer_summary": summary,
        "next_action": next_action,
        "writer_implemented": True,
        "writer_active_for_paper_current_truth": writer_active,
        "writer_stale": continuous_writer_status == PAPER_CONTINUOUS_WRITER_STALE_STATUS,
        "writer_source_present": writer_source_present,
        "writer_source_valid": writer_source_valid,
        "current_snapshot_valid": current_snapshot_valid,
        "portfolio_snapshot_valid": portfolio_valid,
        "current_truth_refresh_valid": refresh_valid,
        "runtime_truth_active": runtime_truth_active,
        "source_hash_bound": hash_bound,
        "source_audited_writer_hash": _hash_from(audited_writer_report, "audited_writer_report_hash"),
        "source_audited_writer_status": audited_writer_report.get("writer_status") if isinstance(audited_writer_report, dict) else "MISSING",
        "source_audited_writer_validator_status": writer_result.status if writer_result is not None else "MISSING",
        "source_current_evidence_snapshot_hash": _hash_from(audited_current_evidence_snapshot, "snapshot_hash"),
        "source_current_evidence_status": audited_current_evidence_snapshot.get("current_evidence_status")
        if isinstance(audited_current_evidence_snapshot, dict)
        else "MISSING",
        "source_current_evidence_validator_status": current_result.status if current_result is not None else "MISSING",
        "source_portfolio_snapshot_hash": _hash_from(audited_paper_portfolio_snapshot, "snapshot_hash"),
        "source_portfolio_snapshot_status": audited_paper_portfolio_snapshot.get("snapshot_status")
        if isinstance(audited_paper_portfolio_snapshot, dict)
        else "MISSING",
        "source_portfolio_validator_status": portfolio_result.status if portfolio_result is not None else "MISSING",
        "source_current_truth_refresh_hash": _hash_from(paper_current_truth_refresh_report, "refresh_report_hash"),
        "source_current_truth_refresh_status": paper_current_truth_refresh_report.get("refresh_status")
        if isinstance(paper_current_truth_refresh_report, dict)
        else "MISSING",
        "source_current_truth_refresh_validator_status": refresh_result.status if refresh_result is not None else "MISSING",
        "source_runtime_truth_state_hash": _hash_from(paper_runtime_truth_state_report, "truth_state_hash"),
        "source_runtime_truth_status": paper_runtime_truth_state_report.get("runtime_truth_status")
        if isinstance(paper_runtime_truth_state_report, dict)
        else "NOT_LOADED",
        "source_runtime_truth_validator_status": runtime_result.status if runtime_result is not None else "NOT_LOADED",
        "source_paper_ledger_head_hash": audited_paper_portfolio_snapshot.get("source_paper_ledger_head_hash")
        if portfolio_valid
        else None,
        "source_runtime_cycle_id": audited_paper_portfolio_snapshot.get("source_runtime_cycle_id")
        if portfolio_valid
        else None,
        "configured_capital_krw": configured_capital,
        "last_verified_paper_ledger_equity_krw": last_verified_equity,
        "current_refreshed_paper_equity_krw": current_refreshed_equity,
        "stale_display_only_equity_krw": stale_display_equity,
        "max_source_age_seconds": max_source_age_seconds,
        "delayed_after_seconds": delayed_after_seconds,
        "stale_after_seconds": stale_after_seconds,
        "primary_blocker_code": primary_blocker_code,
        "blockers": blockers,
        "evidence_role": PAPER_CONTINUOUS_WRITER_TRUTH_ROLE,
        "paper_only": True,
        "display_only": True,
        "dashboard_truth_only": True,
        "current_trading_review_allowed": False,
        "current_evidence_write_allowed": False,
        "audited_current_evidence_write_allowed": False,
        "portfolio_truth_write_allowed": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "credential_load_attempted": False,
        "authorization_header_present": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "scale_up_allowed": False,
        "continuous_writer_report_hash": "",
    }
    report["continuous_writer_report_hash"] = paper_continuous_current_evidence_writer_report_hash(report)
    return report


def validate_paper_continuous_current_evidence_writer_report(
    report: dict[str, Any],
) -> PaperContinuousCurrentEvidenceWriterValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "continuous_writer_status",
        "truth_freshness_status",
        "writer_summary",
        "next_action",
        "writer_implemented",
        "writer_active_for_paper_current_truth",
        "writer_stale",
        "writer_source_present",
        "writer_source_valid",
        "current_snapshot_valid",
        "portfolio_snapshot_valid",
        "current_truth_refresh_valid",
        "runtime_truth_active",
        "source_hash_bound",
        "source_audited_writer_hash",
        "source_audited_writer_status",
        "source_audited_writer_validator_status",
        "source_current_evidence_snapshot_hash",
        "source_current_evidence_status",
        "source_current_evidence_validator_status",
        "source_portfolio_snapshot_hash",
        "source_portfolio_snapshot_status",
        "source_portfolio_validator_status",
        "source_current_truth_refresh_hash",
        "source_current_truth_refresh_status",
        "source_current_truth_refresh_validator_status",
        "source_runtime_truth_state_hash",
        "source_runtime_truth_status",
        "source_runtime_truth_validator_status",
        "source_paper_ledger_head_hash",
        "source_runtime_cycle_id",
        "configured_capital_krw",
        "last_verified_paper_ledger_equity_krw",
        "current_refreshed_paper_equity_krw",
        "stale_display_only_equity_krw",
        "max_source_age_seconds",
        "delayed_after_seconds",
        "stale_after_seconds",
        "primary_blocker_code",
        "blockers",
        "evidence_role",
        "paper_only",
        "display_only",
        "dashboard_truth_only",
        "current_trading_review_allowed",
        "current_evidence_write_allowed",
        "audited_current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "credential_load_attempted",
        "authorization_header_present",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "can_submit_order",
        "scale_up_allowed",
        "continuous_writer_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "FAIL",
            f"continuous current-evidence writer report missing fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("schema_id") != PAPER_CONTINUOUS_CURRENT_EVIDENCE_WRITER_SCHEMA_ID:
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "FAIL", "continuous writer schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("continuous_writer_report_hash") != paper_continuous_current_evidence_writer_report_hash(report):
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "FAIL", "continuous writer report hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED", "continuous writer scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    if report.get("continuous_writer_status") not in PAPER_CONTINUOUS_WRITER_STATUSES:
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "FAIL", "continuous writer status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("truth_freshness_status") not in PAPER_CONTINUOUS_WRITER_FRESHNESS_STATUSES:
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "FAIL", "continuous writer freshness status unknown", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("evidence_role") != PAPER_CONTINUOUS_WRITER_TRUTH_ROLE:
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED", "continuous writer role cannot imply live readiness", "LIVE_FINAL_GUARD_FAILED"
        )
    false_fields = (
        "current_trading_review_allowed",
        "current_evidence_write_allowed",
        "audited_current_evidence_write_allowed",
        "portfolio_truth_write_allowed",
        "live_ready_write_allowed",
        "live_config_mutation_allowed",
        "credential_load_attempted",
        "authorization_header_present",
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
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED",
            "continuous writer attempted trading review, live, order, credential, or scale permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if report.get("paper_only") is not True or report.get("display_only") is not True or report.get("dashboard_truth_only") is not True:
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED", "continuous writer must remain PAPER display truth only", "LIVE_FINAL_GUARD_FAILED"
        )
    for field in (
        "writer_implemented",
        "writer_active_for_paper_current_truth",
        "writer_stale",
        "writer_source_present",
        "writer_source_valid",
        "current_snapshot_valid",
        "portfolio_snapshot_valid",
        "current_truth_refresh_valid",
        "runtime_truth_active",
        "source_hash_bound",
    ):
        if not isinstance(report.get(field), bool):
            return PaperContinuousCurrentEvidenceWriterValidationResult(
                "FAIL", f"continuous writer boolean field malformed: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "FAIL", "continuous writer blockers must be an array", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("continuous_writer_status") == PAPER_CONTINUOUS_WRITER_WRITING_STATUS:
        if (
            report.get("writer_active_for_paper_current_truth") is not True
            or report.get("writer_stale") is not False
            or report.get("truth_freshness_status") not in {"FRESH", "DELAYED"}
            or report.get("writer_source_valid") is not True
            or report.get("current_snapshot_valid") is not True
            or report.get("portfolio_snapshot_valid") is not True
            or report.get("current_truth_refresh_valid") is not True
            or report.get("source_hash_bound") is not True
            or blockers
            or report.get("primary_blocker_code") != "LIVE_READY_MISSING"
            or not report.get("current_refreshed_paper_equity_krw")
            or report.get("stale_display_only_equity_krw") is not None
        ):
            return PaperContinuousCurrentEvidenceWriterValidationResult(
                "FAIL", "continuous writer active status invariant mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "PASS", "continuous PAPER current-evidence writer is implemented, fresh, and live-blocked", None
        )
    if report.get("continuous_writer_status") == PAPER_CONTINUOUS_WRITER_STALE_STATUS:
        if (
            report.get("writer_active_for_paper_current_truth") is not False
            or report.get("writer_stale") is not True
            or report.get("truth_freshness_status") != "STALE_DISPLAY_ONLY"
            or report.get("primary_blocker_code") != "STALE_CURRENT_TRUTH"
            or not blockers
            or report.get("current_refreshed_paper_equity_krw") is not None
            or not report.get("stale_display_only_equity_krw")
        ):
            return PaperContinuousCurrentEvidenceWriterValidationResult(
                "FAIL", "continuous writer stale status invariant mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED", "continuous PAPER current-evidence writer is stale display-only", "STALE_CURRENT_TRUTH"
        )
    if report.get("continuous_writer_status") == PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS:
        if report.get("writer_source_present") is not False or report.get("primary_blocker_code") != "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED":
            return PaperContinuousCurrentEvidenceWriterValidationResult(
                "FAIL", "continuous writer not-implemented status invariant mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED", "continuous writer source report is not loaded", "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED"
        )
    if not blockers or not isinstance(report.get("primary_blocker_code"), str) or not report.get("primary_blocker_code"):
        return PaperContinuousCurrentEvidenceWriterValidationResult(
            "BLOCKED", "blocked continuous writer status must expose a primary blocker", "HARD_TRUTH_MISSING"
        )
    return PaperContinuousCurrentEvidenceWriterValidationResult(
        "BLOCKED", "continuous PAPER current-evidence writer is implemented but blocked", report.get("primary_blocker_code")
    )
