from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation_actual_runtime_harness import (
    shadow_observation_actual_runtime_harness_hash,
    validate_shadow_observation_actual_runtime_harness_report,
)
from trader1.research.shadow.shadow_runner import (
    AGENTS_SHA256,
    TRADER1_SHA256,
    paper_shadow_evidence_hash,
    utc_now,
    validate_paper_shadow_evidence_accumulation_report,
)


PAPER_SHADOW_HARNESS_BINDING_SCHEMA_ID = "trader1.paper_shadow_harness_binding_report.v1"
PAPER_SHADOW_HARNESS_BINDING_GRAPH_VERSION = "paper_shadow_harness_binding_evidence_graph.v1"

CRITICAL_SOURCE_BLOCKERS = {
    "LIVE_FINAL_GUARD_FAILED",
    "SNAPSHOT_SCOPE_MISMATCH",
    "SCHEMA_IDENTITY_MISMATCH",
    "API_UNVERIFIED",
    "SOURCE_IDENTITY_MISMATCH",
    "OPTIMIZER_DIRECT_LIVE_FORBIDDEN",
}
WARNING_SOURCE_BLOCKERS = {
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "DATA_QUALITY_INSUFFICIENT",
    "EXECUTION_FEEDBACK_MISSING",
    "HARD_TRUTH_MISSING",
    "MEASUREMENT_MISSING",
    "SAMPLE_INSUFFICIENT",
    "SCORECARD_MISSING",
}
SAFE_BINDING_STATUSES = {
    "HARNESS_ONLY_WAITING_EVIDENCE",
    "EVIDENCE_PRESENT_WAITING_COLLECTION",
    "BOUND_TO_SCORECARD_INPUT",
    "STALE_DISPLAY_ONLY",
}


@dataclass(frozen=True)
class PaperShadowHarnessBindingValidationResult:
    status: str
    message: str
    blocker_code: str | None


def paper_shadow_harness_binding_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("binding_report_hash", None)
    return _sha256_payload(payload)


def build_paper_shadow_harness_binding_report(
    *,
    binding_report_id: str,
    shadow_runtime_harness_report: dict[str, Any],
    paper_shadow_evidence_accumulation_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    harness = dict(shadow_runtime_harness_report)
    evidence = dict(paper_shadow_evidence_accumulation_report) if isinstance(paper_shadow_evidence_accumulation_report, dict) else None

    harness_result = validate_shadow_observation_actual_runtime_harness_report(harness)
    harness_hash = str(harness.get("harness_report_hash") or "")
    harness_hash_verified = harness_hash == shadow_observation_actual_runtime_harness_hash(harness)

    evidence_result = None
    evidence_hash = None
    evidence_hash_verified = None
    if evidence is not None:
        evidence_result = validate_paper_shadow_evidence_accumulation_report(evidence)
        evidence_hash = str(evidence.get("evidence_hash") or "")
        evidence_hash_verified = evidence_hash == paper_shadow_evidence_hash(evidence)

    critical_blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    informational: list[dict[str, str]] = []

    if harness_result.status != "PASS" or not harness_hash_verified:
        code = harness_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH"
        target = critical_blockers if code in CRITICAL_SOURCE_BLOCKERS or not harness_hash_verified else warnings
        target.append(
            _blocker(
                code if code in CRITICAL_SOURCE_BLOCKERS or code in WARNING_SOURCE_BLOCKERS else "DATA_QUALITY_INSUFFICIENT",
                harness_result.message if harness_hash_verified else "PAPER/SHADOW harness source hash does not verify.",
                "CRITICAL" if target is critical_blockers else "HIGH",
            )
        )

    if evidence is None:
        warnings.append(
            _blocker(
                "SCORECARD_MISSING",
                "No paper_shadow_evidence_accumulation_report is loaded; strategy evidence collection has not started for this binding.",
                "MEDIUM",
            )
        )
    else:
        if evidence_result is None:
            warnings.append(_blocker("MEASUREMENT_MISSING", "PAPER/SHADOW evidence validation did not run.", "MEDIUM"))
        elif evidence_result.status != "PASS":
            code = evidence_result.blocker_code or "MEASUREMENT_MISSING"
            target = critical_blockers if code in CRITICAL_SOURCE_BLOCKERS or evidence_hash_verified is False else warnings
            target.append(
                _blocker(
                    code if code in CRITICAL_SOURCE_BLOCKERS or code in WARNING_SOURCE_BLOCKERS else "MEASUREMENT_MISSING",
                    evidence_result.message,
                    "CRITICAL" if target is critical_blockers else "MEDIUM",
                )
            )
        if evidence_hash_verified is False:
            critical_blockers.append(
                _blocker(
                    "SCHEMA_IDENTITY_MISMATCH",
                    "PAPER/SHADOW evidence source hash does not verify.",
                    "CRITICAL",
                )
            )

    if evidence is None or evidence.get("long_run_evidence_eligible") is not True:
        warnings.append(
            _blocker(
                "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
                "This binding is non-live and does not contain validated long-run PAPER/SHADOW runtime evidence.",
                "MEDIUM",
            )
        )
    if _safe_int(evidence.get("cost_evidence_count") if evidence else 0) <= 0:
        warnings.append(_blocker("EXECUTION_FEEDBACK_MISSING", "Cost evidence is not yet bound to this harness.", "MEDIUM"))
    if _safe_int(evidence.get("entry_reason_count") if evidence else 0) <= 0 or _safe_int(
        evidence.get("no_trade_reason_count") if evidence else 0
    ) <= 0:
        warnings.append(_blocker("MEASUREMENT_MISSING", "Entry and no-trade reason coverage is not yet complete.", "MEDIUM"))

    informational.append(
        _blocker(
            "MEASUREMENT_MISSING",
            "Market regime tag count is currently tracked by this binding as zero until runtime evidence provides scoped regime labels.",
            "INFO",
        )
    )

    critical_blockers = _dedupe_blockers(critical_blockers)
    warnings = _dedupe_blockers(warnings)
    informational = _dedupe_blockers(informational)
    binding_status = _binding_status(critical_blockers, evidence, evidence_result)
    latency_status = _latency_status(critical_blockers, evidence, evidence_result)
    top_codes = [blocker["code"] for blocker in [*critical_blockers, *warnings]][:5]
    primary_code = top_codes[0] if top_codes else None
    blocks_source_collection = bool(critical_blockers)

    report = {
        "schema_id": PAPER_SHADOW_HARNESS_BINDING_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": TRADER1_SHA256, "agents_sha256": AGENTS_SHA256},
        "binding_report_id": binding_report_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "paper_mode": "PAPER",
        "shadow_mode": "SHADOW",
        "session_id": str(harness.get("session_id") or harness.get("harness_id") or binding_report_id),
        "harness_id": str(harness.get("harness_id") or binding_report_id),
        "harness_report_hash": harness_hash,
        "harness_hash_verified": harness_hash_verified,
        "harness_validation_status": harness_result.status,
        "evidence_report_id": evidence.get("evidence_report_id") if evidence else None,
        "evidence_report_hash": evidence_hash,
        "evidence_hash_verified": evidence_hash_verified,
        "evidence_validation_status": evidence_result.status if evidence_result is not None else "NOT_LOADED",
        "binding_status": binding_status,
        "evidence_graph_version": PAPER_SHADOW_HARNESS_BINDING_GRAPH_VERSION,
        "critical_blockers": critical_blockers,
        "warnings": warnings,
        "informational": informational,
        "critical_blocker_count": len(critical_blockers),
        "warning_count": len(warnings),
        "informational_count": len(informational),
        "primary_blocker_code": primary_code,
        "top_level_blocker_codes": top_codes,
        "paper_cycle_count": _safe_int(harness.get("completed_cycle_count")),
        "shadow_opportunity_count": _safe_int(harness.get("observation_count")),
        "paper_sample_count": _safe_int(evidence.get("paper_sample_count") if evidence else 0),
        "shadow_sample_count": _safe_int(evidence.get("shadow_sample_count") if evidence else 0),
        "entry_reason_count": _safe_int(evidence.get("entry_reason_count") if evidence else 0),
        "no_trade_reason_count": _safe_int(evidence.get("no_trade_reason_count") if evidence else 0),
        "cost_assumption_count": _safe_int(evidence.get("cost_evidence_count") if evidence else 0),
        "market_regime_tag_count": 0,
        "latency_freshness_status": latency_status,
        "source_binding_count": len(evidence.get("source_evidence_bindings", [])) if evidence else 1,
        "source_scope_status": "BLOCKED" if critical_blockers else "PASS",
        "blocks_paper_current_truth_write": bool(critical_blockers),
        "blocks_non_live_runtime_collection": blocks_source_collection,
        "blocks_live_ready": True,
        "blocks_optimizer_or_convergence": True,
        "optimizer_status": "BLOCKED_SOURCE_INVALID" if critical_blockers else "WAITING_FOR_LONG_RUN_EVIDENCE",
        "operator_action_required": _operator_action(binding_status),
        "codex_non_live_action": _codex_action(binding_status),
        "local_paper_shadow_runtime_action": _local_runtime_action(binding_status),
        "external_live_evidence_action": "No external/live action is accepted from this binding; LIVE_READY remains blocked.",
        "next_action": _next_action(binding_status),
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "credential_access_attempted": False,
        "exchange_account_call_attempted": False,
        "live_order_api_attempted": False,
        "order_adapter_called": False,
        "live_ready_snapshot_written": False,
        "binding_report_hash": "",
    }
    report["binding_report_hash"] = paper_shadow_harness_binding_hash(report)
    return report


def validate_paper_shadow_harness_binding_report(
    report: dict[str, Any],
) -> PaperShadowHarnessBindingValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "binding_report_id",
        "exchange",
        "market_type",
        "paper_mode",
        "shadow_mode",
        "session_id",
        "harness_id",
        "harness_report_hash",
        "harness_hash_verified",
        "harness_validation_status",
        "evidence_report_id",
        "evidence_report_hash",
        "evidence_hash_verified",
        "evidence_validation_status",
        "binding_status",
        "evidence_graph_version",
        "critical_blockers",
        "warnings",
        "informational",
        "critical_blocker_count",
        "warning_count",
        "informational_count",
        "primary_blocker_code",
        "top_level_blocker_codes",
        "paper_cycle_count",
        "shadow_opportunity_count",
        "paper_sample_count",
        "shadow_sample_count",
        "entry_reason_count",
        "no_trade_reason_count",
        "cost_assumption_count",
        "market_regime_tag_count",
        "latency_freshness_status",
        "source_binding_count",
        "source_scope_status",
        "blocks_paper_current_truth_write",
        "blocks_non_live_runtime_collection",
        "blocks_live_ready",
        "blocks_optimizer_or_convergence",
        "optimizer_status",
        "operator_action_required",
        "codex_non_live_action",
        "local_paper_shadow_runtime_action",
        "external_live_evidence_action",
        "next_action",
        "dashboard_display_truth_only",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "credential_access_attempted",
        "exchange_account_call_attempted",
        "live_order_api_attempted",
        "order_adapter_called",
        "live_ready_snapshot_written",
        "binding_report_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return PaperShadowHarnessBindingValidationResult("FAIL", f"paper/shadow harness binding report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != PAPER_SHADOW_HARNESS_BINDING_SCHEMA_ID:
        return PaperShadowHarnessBindingValidationResult("FAIL", "paper/shadow harness binding schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("binding_report_hash") != paper_shadow_harness_binding_hash(report):
        return PaperShadowHarnessBindingValidationResult("FAIL", "paper/shadow harness binding hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return PaperShadowHarnessBindingValidationResult("BLOCKED", "paper/shadow harness binding is UPBIT/KRW_SPOT scoped for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("paper_mode") != "PAPER" or report.get("shadow_mode") != "SHADOW":
        return PaperShadowHarnessBindingValidationResult("BLOCKED", "paper/shadow harness binding must remain PAPER source and SHADOW comparison scoped", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("evidence_graph_version") != PAPER_SHADOW_HARNESS_BINDING_GRAPH_VERSION:
        return PaperShadowHarnessBindingValidationResult("FAIL", "paper/shadow harness binding evidence graph version mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if not _hex_64(str(report.get("harness_report_hash") or "")):
        return PaperShadowHarnessBindingValidationResult("FAIL", "paper/shadow harness binding lacks a valid harness hash", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("evidence_validation_status") == "NOT_LOADED":
        if report.get("evidence_report_id") is not None or report.get("evidence_report_hash") is not None or report.get("evidence_hash_verified") is not None:
            return PaperShadowHarnessBindingValidationResult("FAIL", "not-loaded evidence cannot carry report id, hash, or verification state", "SCHEMA_IDENTITY_MISMATCH")
        not_loaded_statuses = {"HARNESS_ONLY_WAITING_EVIDENCE"}
        if int(report.get("critical_blocker_count", 0) or 0) > 0:
            not_loaded_statuses.add("BLOCKED_SOURCE_INVALID")
        if report.get("binding_status") not in not_loaded_statuses:
            return PaperShadowHarnessBindingValidationResult("FAIL", "not-loaded evidence must be harness-only waiting state", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if not _hex_64(str(report.get("evidence_report_hash") or "")):
            return PaperShadowHarnessBindingValidationResult("FAIL", "loaded evidence must carry a valid evidence hash", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("evidence_hash_verified") is not True:
            return PaperShadowHarnessBindingValidationResult("BLOCKED", "loaded evidence hash is not verified", "SCHEMA_IDENTITY_MISMATCH")
    for field in (
        "paper_cycle_count",
        "shadow_opportunity_count",
        "paper_sample_count",
        "shadow_sample_count",
        "entry_reason_count",
        "no_trade_reason_count",
        "cost_assumption_count",
        "market_regime_tag_count",
        "source_binding_count",
    ):
        if not isinstance(report.get(field), int) or report.get(field) < 0:
            return PaperShadowHarnessBindingValidationResult("FAIL", f"{field} must be a non-negative integer", "MEASUREMENT_MISSING")
    critical = report.get("critical_blockers")
    warnings = report.get("warnings")
    informational = report.get("informational")
    if not isinstance(critical, list) or not isinstance(warnings, list) or not isinstance(informational, list):
        return PaperShadowHarnessBindingValidationResult("FAIL", "paper/shadow harness binding blocker tiers must be arrays", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("critical_blocker_count") != len(critical) or report.get("warning_count") != len(warnings) or report.get("informational_count") != len(informational):
        return PaperShadowHarnessBindingValidationResult("FAIL", "paper/shadow harness binding blocker tier counts drifted", "SCHEMA_IDENTITY_MISMATCH")
    top_codes = [blocker.get("code") for blocker in [*critical, *warnings] if isinstance(blocker, dict)][:5]
    if report.get("top_level_blocker_codes") != top_codes:
        return PaperShadowHarnessBindingValidationResult("FAIL", "top-level PAPER/SHADOW blocker list is not tier ordered", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("primary_blocker_code") != (top_codes[0] if top_codes else None):
        return PaperShadowHarnessBindingValidationResult("FAIL", "primary blocker code must match first top-level blocker", "SCHEMA_IDENTITY_MISMATCH")
    if critical:
        if report.get("binding_status") != "BLOCKED_SOURCE_INVALID":
            return PaperShadowHarnessBindingValidationResult("BLOCKED", "critical source blockers must force BLOCKED_SOURCE_INVALID", critical[0].get("code", "UNKNOWN_BLOCKED"))
        if report.get("blocks_paper_current_truth_write") is not True or report.get("blocks_non_live_runtime_collection") is not True:
            return PaperShadowHarnessBindingValidationResult("BLOCKED", "critical source blockers must block current truth write and non-live collection until repaired", critical[0].get("code", "UNKNOWN_BLOCKED"))
        if report.get("source_scope_status") != "BLOCKED" or report.get("latency_freshness_status") != "INVALID":
            return PaperShadowHarnessBindingValidationResult("BLOCKED", "critical source blockers must mark source scope blocked and freshness invalid", critical[0].get("code", "UNKNOWN_BLOCKED"))
        return PaperShadowHarnessBindingValidationResult(
            "BLOCKED",
            "paper/shadow harness binding contains critical source blockers",
            critical[0].get("code", "UNKNOWN_BLOCKED"),
        )
    else:
        if report.get("harness_hash_verified") is not True or report.get("harness_validation_status") != "PASS":
            return PaperShadowHarnessBindingValidationResult("BLOCKED", "paper/shadow harness binding source harness is not verified PASS", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("binding_status") not in SAFE_BINDING_STATUSES:
            return PaperShadowHarnessBindingValidationResult("FAIL", "safe paper/shadow harness binding status is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("blocks_paper_current_truth_write") is not False or report.get("blocks_non_live_runtime_collection") is not False:
            return PaperShadowHarnessBindingValidationResult("BLOCKED", "non-critical stale/sample deficits cannot block PAPER current truth regeneration or non-live collection", "LIVE_FINAL_GUARD_FAILED")
        if report.get("source_scope_status") != "PASS":
            return PaperShadowHarnessBindingValidationResult("FAIL", "non-critical binding source scope should pass", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("binding_status") == "BOUND_TO_SCORECARD_INPUT":
        if report.get("evidence_validation_status") != "PASS" or int(report.get("paper_sample_count", 0)) <= 0 or int(report.get("shadow_sample_count", 0)) <= 0:
            return PaperShadowHarnessBindingValidationResult("FAIL", "scorecard binding requires PASS evidence and nonzero PAPER/SHADOW samples", "MEASUREMENT_MISSING")
    if report.get("binding_status") == "STALE_DISPLAY_ONLY" and report.get("latency_freshness_status") != "STALE_DISPLAY_ONLY":
        return PaperShadowHarnessBindingValidationResult("FAIL", "stale display binding must carry stale display-only freshness", "DATA_QUALITY_INSUFFICIENT")
    if report.get("blocks_live_ready") is not True or report.get("blocks_optimizer_or_convergence") is not True:
        return PaperShadowHarnessBindingValidationResult("BLOCKED", "paper/shadow harness binding cannot unblock live readiness or optimizer/convergence", "LIVE_FINAL_GUARD_FAILED")
    if report.get("dashboard_display_truth_only") is not True or report.get("promotion_eligible") is not False:
        return PaperShadowHarnessBindingValidationResult("BLOCKED", "paper/shadow harness binding must remain display-only and non-promotable", "LIVE_FINAL_GUARD_FAILED")
    forbidden_true = (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "credential_access_attempted",
        "exchange_account_call_attempted",
        "live_order_api_attempted",
        "order_adapter_called",
        "live_ready_snapshot_written",
    )
    if any(report.get(field) is not False for field in forbidden_true):
        return PaperShadowHarnessBindingValidationResult("BLOCKED", "paper/shadow harness binding attempted live, credential, order, LIVE_READY, or scale-up state", "LIVE_FINAL_GUARD_FAILED")
    joined_text = " ".join(
        str(report.get(field) or "")
        for field in (
            "codex_non_live_action",
            "local_paper_shadow_runtime_action",
            "external_live_evidence_action",
            "next_action",
        )
    ).lower()
    forbidden_phrases = ("profit guaranteed", "live_ready=true", "live orders allowed", "safe to scale automatically")
    if any(phrase in joined_text for phrase in forbidden_phrases):
        return PaperShadowHarnessBindingValidationResult("BLOCKED", "operator-facing paper/shadow binding text contains forbidden live/profit wording", "LIVE_FINAL_GUARD_FAILED")
    return PaperShadowHarnessBindingValidationResult(
        "PASS",
        "PAPER/SHADOW harness binding separates critical blockers from stale/sample warnings and keeps live/optimizer blocked",
        None,
    )


def _binding_status(
    critical_blockers: list[dict[str, str]],
    evidence: dict[str, Any] | None,
    evidence_result: Any,
) -> str:
    if critical_blockers:
        return "BLOCKED_SOURCE_INVALID"
    if evidence is None:
        return "HARNESS_ONLY_WAITING_EVIDENCE"
    if evidence_result is not None and evidence_result.status == "PASS" and evidence.get("scorecard_input_eligible") is True:
        return "BOUND_TO_SCORECARD_INPUT"
    if evidence_result is not None and evidence_result.blocker_code == "DATA_QUALITY_INSUFFICIENT":
        return "STALE_DISPLAY_ONLY"
    return "EVIDENCE_PRESENT_WAITING_COLLECTION"


def _latency_status(critical_blockers: list[dict[str, str]], evidence: dict[str, Any] | None, evidence_result: Any) -> str:
    if critical_blockers:
        return "INVALID"
    if evidence_result is not None and evidence_result.blocker_code == "DATA_QUALITY_INSUFFICIENT":
        return "STALE_DISPLAY_ONLY"
    if evidence is None:
        return "DELAYED"
    return "FRESH" if evidence_result is not None and evidence_result.status == "PASS" else "DELAYED"


def _operator_action(binding_status: str) -> str:
    if binding_status == "BLOCKED_SOURCE_INVALID":
        return "STOP_AND_INSPECT_SOURCE"
    if binding_status == "STALE_DISPLAY_ONLY":
        return "NONE_FOR_ROUTINE_REFRESH"
    return "LOCAL_PAPER_SHADOW_RUNTIME_COLLECTION"


def _codex_action(binding_status: str) -> str:
    if binding_status == "BLOCKED_SOURCE_INVALID":
        return "Repair source scope/hash/live-safety drift before rebinding PAPER/SHADOW evidence."
    if binding_status == "STALE_DISPLAY_ONLY":
        return "Regenerate the non-live binding after fresh PAPER/SHADOW artifacts are produced."
    return "Keep this as a non-live evidence graph; do not add optimizer wrappers until runtime/replay evidence thresholds are met."


def _local_runtime_action(binding_status: str) -> str:
    if binding_status == "BOUND_TO_SCORECARD_INPUT":
        return "Continue non-live PAPER/SHADOW runtime collection for paired windows, realized/expected edge, costs, and regime-labeled outcomes."
    if binding_status == "HARNESS_ONLY_WAITING_EVIDENCE":
        return "Run the local non-live PAPER/SHADOW collection harness so PAPER cycles and SHADOW opportunities produce a source-bound evidence report."
    if binding_status == "STALE_DISPLAY_ONLY":
        return "Refresh stale PAPER/SHADOW artifacts locally; this does not require operator reconciliation."
    return "Stop routine collection until source scope/hash/live-safety drift is repaired."


def _next_action(binding_status: str) -> str:
    if binding_status == "BOUND_TO_SCORECARD_INPUT":
        return "Use this binding as PAPER scorecard input only; keep optimizer/convergence waiting for long-run evidence."
    if binding_status == "EVIDENCE_PRESENT_WAITING_COLLECTION":
        return "Collect missing PAPER/SHADOW samples, reason codes, cost evidence, and paired windows in the same scope."
    if binding_status == "STALE_DISPLAY_ONLY":
        return "Refresh the stale non-live artifacts and rebuild this binding; do not treat stale values as current truth."
    if binding_status == "HARNESS_ONLY_WAITING_EVIDENCE":
        return "Generate paper_shadow_evidence_accumulation_report from actual non-live PAPER/SHADOW runtime or replay evidence."
    return "Inspect and repair critical source mismatch before continuing non-live evidence collection."


def _blocker(code: str, message: str, severity: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _dedupe_blockers(blockers: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, str]] = []
    for blocker in blockers:
        key = (blocker.get("code", ""), blocker.get("message", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(blocker)
    return deduped


def _safe_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed >= 0 else 0


def _hex_64(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()
