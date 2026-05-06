from __future__ import annotations

from dataclasses import dataclass
from typing import Any


LIVE_FALSE_FIELDS = (
    "live_order_ready",
    "live_order_allowed",
    "can_live_trade",
    "scale_up_allowed",
    "order_adapter_called",
)
SCOPE_FIELDS = (
    "exchange",
    "market_type",
    "paper_mode",
    "shadow_mode",
    "paper_session_id",
    "shadow_session_id",
    "candidate_id",
    "strategy_id",
    "strategy_build_id",
    "parameter_hash",
)
CRITICAL_LATEST_BLOCKERS = {
    "LIVE_FINAL_GUARD_FAILED",
    "SNAPSHOT_SCOPE_MISMATCH",
    "SCHEMA_IDENTITY_MISMATCH",
    "SOURCE_IDENTITY_MISMATCH",
    "API_UNVERIFIED",
    "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
}


@dataclass(frozen=True)
class PaperShadowEvidenceRefreshDecision:
    selected_report: dict[str, Any]
    selected_source: str
    evidence_refresh_action: str
    evidence_refresh_reason_code: str
    latest_validation_status: str
    latest_blocker_code: str | None
    selected_validation_status: str
    selected_blocker_code: str | None


def choose_paper_shadow_evidence_refresh_report(
    *,
    existing_report: dict[str, Any] | None,
    existing_validation_result: Any,
    existing_binding_report: dict[str, Any] | None,
    existing_binding_validation_result: Any,
    latest_report: dict[str, Any],
    latest_validation_result: Any,
) -> PaperShadowEvidenceRefreshDecision:
    """Select the report to persist after a non-live PAPER/SHADOW refresh.

    A short latest SHADOW harness can safely prove liveness while carrying fewer
    observations than the already validated scorecard evidence. Preserve the
    prior source-bound scorecard report only for that narrow regression case.
    Critical live/scope/hash failures always force the latest result to surface.
    """

    latest_status = _result_status(latest_validation_result)
    latest_blocker = _result_blocker_code(latest_validation_result)
    latest_decision = _decision(
        selected_report=latest_report,
        selected_source="latest",
        action="WRITE_LATEST_RUNTIME_EVIDENCE",
        reason="LATEST_NOT_PRESERVABLE",
        latest_status=latest_status,
        latest_blocker=latest_blocker,
        selected_status=latest_status,
        selected_blocker=latest_blocker,
    )

    if latest_status == "PASS":
        return _replace_reason(latest_decision, "LATEST_SCORECARD_READY")
    if latest_blocker in CRITICAL_LATEST_BLOCKERS:
        return _replace_reason(latest_decision, "LATEST_CRITICAL_BLOCKER_SURFACED")
    if latest_blocker != "SAMPLE_INSUFFICIENT":
        return _replace_reason(latest_decision, "LATEST_BLOCKER_NOT_SAMPLE_REGRESSION")
    if not isinstance(existing_report, dict):
        return _replace_reason(latest_decision, "NO_EXISTING_EVIDENCE")

    existing_status = _result_status(existing_validation_result)
    existing_blocker = _result_blocker_code(existing_validation_result)
    if existing_status != "PASS":
        return _replace_reason(latest_decision, "EXISTING_EVIDENCE_NOT_PASS")
    if not _same_scope(existing_report, latest_report):
        return _replace_reason(latest_decision, "EXISTING_SCOPE_MISMATCH")
    if not _scorecard_ready(existing_report):
        return _replace_reason(latest_decision, "EXISTING_NOT_SCORECARD_READY")
    if not _all_live_flags_false(existing_report):
        return _replace_reason(latest_decision, "EXISTING_LIVE_FLAG_DRIFT")
    if not _binding_confirms_existing_evidence(
        existing_binding_report,
        existing_binding_validation_result,
        existing_report,
    ):
        return _replace_reason(latest_decision, "EXISTING_BINDING_NOT_VERIFIED")
    if not _latest_is_shadow_sample_regression(existing_report, latest_report):
        return _replace_reason(latest_decision, "LATEST_NOT_SHADOW_SAMPLE_REGRESSION")

    return _decision(
        selected_report=existing_report,
        selected_source="existing",
        action="PRESERVE_EXISTING_SOURCE_BOUND_SCORECARD_EVIDENCE",
        reason="LATEST_SHORT_WINDOW_SHADOW_SAMPLE_REGRESSION",
        latest_status=latest_status,
        latest_blocker=latest_blocker,
        selected_status=existing_status,
        selected_blocker=existing_blocker,
    )


def _decision(
    *,
    selected_report: dict[str, Any],
    selected_source: str,
    action: str,
    reason: str,
    latest_status: str,
    latest_blocker: str | None,
    selected_status: str,
    selected_blocker: str | None,
) -> PaperShadowEvidenceRefreshDecision:
    return PaperShadowEvidenceRefreshDecision(
        selected_report=selected_report,
        selected_source=selected_source,
        evidence_refresh_action=action,
        evidence_refresh_reason_code=reason,
        latest_validation_status=latest_status,
        latest_blocker_code=latest_blocker,
        selected_validation_status=selected_status,
        selected_blocker_code=selected_blocker,
    )


def _replace_reason(
    decision: PaperShadowEvidenceRefreshDecision,
    reason: str,
) -> PaperShadowEvidenceRefreshDecision:
    return PaperShadowEvidenceRefreshDecision(
        selected_report=decision.selected_report,
        selected_source=decision.selected_source,
        evidence_refresh_action=decision.evidence_refresh_action,
        evidence_refresh_reason_code=reason,
        latest_validation_status=decision.latest_validation_status,
        latest_blocker_code=decision.latest_blocker_code,
        selected_validation_status=decision.selected_validation_status,
        selected_blocker_code=decision.selected_blocker_code,
    )


def _same_scope(existing_report: dict[str, Any], latest_report: dict[str, Any]) -> bool:
    return all(str(existing_report.get(field)) == str(latest_report.get(field)) for field in SCOPE_FIELDS)


def _scorecard_ready(report: dict[str, Any]) -> bool:
    return (
        report.get("scorecard_input_eligible") is True
        and report.get("optimizer_ranking_action") == "ALLOW_RANKING"
        and report.get("evidence_chain_complete") is True
    )


def _all_live_flags_false(report: dict[str, Any]) -> bool:
    return all(report.get(field) is False for field in LIVE_FALSE_FIELDS)


def _binding_confirms_existing_evidence(
    binding_report: dict[str, Any] | None,
    binding_validation_result: Any,
    existing_report: dict[str, Any],
) -> bool:
    if not isinstance(binding_report, dict):
        return False
    if _result_status(binding_validation_result) != "PASS":
        return False
    return (
        binding_report.get("binding_status") == "BOUND_TO_SCORECARD_INPUT"
        and binding_report.get("evidence_validation_status") == "PASS"
        and binding_report.get("evidence_hash_verified") is True
        and binding_report.get("evidence_report_hash") == existing_report.get("evidence_hash")
        and _all_live_flags_false(binding_report)
    )


def _latest_is_shadow_sample_regression(existing_report: dict[str, Any], latest_report: dict[str, Any]) -> bool:
    min_required = max(
        1,
        _safe_int(latest_report.get("min_required_sample_count"), 1),
        _safe_int(existing_report.get("min_required_sample_count"), 1),
    )
    latest_paper = _safe_int(latest_report.get("paper_sample_count"), 0)
    latest_shadow = _safe_int(latest_report.get("shadow_sample_count"), 0)
    existing_paper = _safe_int(existing_report.get("paper_sample_count"), 0)
    existing_shadow = _safe_int(existing_report.get("shadow_sample_count"), 0)
    return (
        latest_paper >= min_required
        and latest_shadow < min_required
        and existing_paper >= min_required
        and existing_shadow >= min_required
        and existing_shadow > latest_shadow
    )


def _result_status(result: Any) -> str:
    return str(getattr(result, "status", "NOT_RUN") or "NOT_RUN")


def _result_blocker_code(result: Any) -> str | None:
    blocker = getattr(result, "blocker_code", None)
    return str(blocker) if blocker else None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default
