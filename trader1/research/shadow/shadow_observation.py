from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.runtime.paper.operational_cycle import operation_gate_hash, validate_paper_operation_gate_report
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now


SHADOW_OBSERVATION_SCHEMA_ID = "trader1.shadow_observation_report.v1"


@dataclass(frozen=True)
class ShadowObservationValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("observation_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_report(
    *,
    observation_id: str,
    paper_operation_gate_report: dict[str, Any],
    shadow_session_id: str | None = None,
    shadow_sample_count: int | None = None,
    shadow_artifact_age_seconds: int = 0,
    max_artifact_age_seconds: int = 900,
) -> dict[str, Any]:
    evidence = paper_operation_gate_report.get("paper_shadow_evidence_accumulation_report") or {}
    strategy = paper_operation_gate_report.get("strategy_unit") or {}
    paper = paper_operation_gate_report.get("paper_dry_run_report") or {}

    exchange = str(paper_operation_gate_report.get("exchange") or evidence.get("exchange") or "UPBIT")
    market_type = str(paper_operation_gate_report.get("market_type") or evidence.get("market_type") or "KRW_SPOT")
    paper_session_id = str(paper_operation_gate_report.get("session_id") or evidence.get("paper_session_id") or "paper-session-missing")
    shadow_session = str(shadow_session_id or evidence.get("shadow_session_id") or f"{paper_session_id}_shadow_observation")
    candidate_id = str(evidence.get("candidate_id") or strategy.get("strategy_unit_id") or "candidate-missing")
    strategy_id = str(evidence.get("strategy_id") or strategy.get("strategy_id") or "strategy-missing")
    strategy_build_id = str(evidence.get("strategy_build_id") or strategy.get("strategy_build_id") or "strategy-build-missing")
    parameter_hash = str(evidence.get("parameter_hash") or strategy.get("parameter_hash") or "0" * 64)
    paper_hash = str(paper_operation_gate_report.get("operation_gate_hash") or _sha256_payload(paper_operation_gate_report))
    sample_count = int(shadow_sample_count if shadow_sample_count is not None else max(1, int(evidence.get("paper_sample_count", 0))))

    paper_path = _paper_gate_path(exchange, market_type, paper_session_id)
    shadow_path = _shadow_observation_path(exchange, market_type, shadow_session)
    shadow_artifact_hash = _sha256_payload(
        {
            "observation_id": observation_id,
            "paper_operation_gate_hash": paper_hash,
            "shadow_session_id": shadow_session,
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "parameter_hash": parameter_hash,
        }
    )

    source_validation = validate_paper_operation_gate_report(paper_operation_gate_report)
    source_hash_valid = paper_operation_gate_report.get("operation_gate_hash") == operation_gate_hash(paper_operation_gate_report)
    blockers: list[dict[str, str]] = []
    if source_validation.status != "PASS":
        blockers.append(_blocker(source_validation.blocker_code or "MEASUREMENT_MISSING", f"source PAPER gate is not valid: {source_validation.message}"))
    if not source_hash_valid:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "source PAPER gate hash does not match its content"))
    if exchange != "UPBIT" or market_type != "KRW_SPOT" or paper_operation_gate_report.get("mode") != "PAPER":
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "SHADOW observation scaffold is currently scoped to UPBIT/KRW_SPOT/PAPER source"))
    if paper_session_id == shadow_session:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "PAPER source session and SHADOW observation session must be distinct"))
    if sample_count <= 0:
        blockers.append(_blocker("SAMPLE_INSUFFICIENT", "SHADOW observation sample count must be positive"))
    if shadow_artifact_age_seconds > max_artifact_age_seconds:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "SHADOW observation artifact is stale"))
    if _live_flag_drift(paper_operation_gate_report, evidence, paper):
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "source PAPER gate or nested evidence attempted live/order state"))

    report = {
        "schema_id": SHADOW_OBSERVATION_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "observation_id": observation_id,
        "exchange": exchange,
        "market_type": market_type,
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "paper_session_id": paper_session_id,
        "shadow_session_id": shadow_session,
        "paper_artifact_path": paper_path,
        "shadow_artifact_path": shadow_path,
        "paper_operation_gate_id": str(paper_operation_gate_report.get("operation_gate_id") or "paper-operation-gate-missing"),
        "paper_operation_gate_hash": paper_hash,
        "source_paper_validation_status": source_validation.status,
        "source_paper_hash_valid": source_hash_valid,
        "candidate_id": candidate_id,
        "strategy_id": strategy_id,
        "strategy_build_id": strategy_build_id,
        "parameter_hash": parameter_hash,
        "shadow_artifact_hash": shadow_artifact_hash,
        "shadow_sample_count": sample_count,
        "shadow_artifact_age_seconds": shadow_artifact_age_seconds,
        "max_artifact_age_seconds": max_artifact_age_seconds,
        "entry_reason_count": int(evidence.get("entry_reason_count", len(paper.get("entry_reasons") or []))),
        "exit_reason_count": int(evidence.get("exit_reason_count", len(paper.get("exit_reasons") or []))),
        "no_trade_reason_count": int(evidence.get("no_trade_reason_count", len(paper.get("no_trade_reasons") or []))),
        "cost_evidence_count": int(evidence.get("cost_evidence_count", 0)),
        "source_evidence_binding": {
            "source_role": "PAPER_OPERATION",
            "exchange": exchange,
            "market_type": market_type,
            "mode": "PAPER",
            "session_id": paper_session_id,
            "artifact_path": paper_path,
            "artifact_hash": paper_hash,
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "strategy_build_id": strategy_build_id,
            "parameter_hash": parameter_hash,
            "identity_match_status": "PASS" if not blockers else "BLOCKED",
        },
        "shadow_observation_status": "PASS" if not blockers else "BLOCKED",
        "optimizer_input_role": "SHADOW_OBSERVATION_ONLY",
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "observation_hash": "",
    }
    report["observation_hash"] = shadow_observation_hash(report)
    return report


def validate_shadow_observation_report(report: dict[str, Any]) -> ShadowObservationValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "observation_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "paper_session_id",
        "shadow_session_id",
        "paper_artifact_path",
        "shadow_artifact_path",
        "paper_operation_gate_id",
        "paper_operation_gate_hash",
        "source_paper_validation_status",
        "source_paper_hash_valid",
        "candidate_id",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "shadow_artifact_hash",
        "shadow_sample_count",
        "shadow_artifact_age_seconds",
        "max_artifact_age_seconds",
        "source_evidence_binding",
        "shadow_observation_status",
        "optimizer_input_role",
        "dashboard_display_truth_only",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "order_adapter_called",
        "primary_blocker_code",
        "blockers",
        "observation_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationValidationResult("FAIL", f"SHADOW observation missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_SCHEMA_ID:
        return ShadowObservationValidationResult("FAIL", "SHADOW observation schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("observation_hash") != shadow_observation_hash(report):
        return ShadowObservationValidationResult("FAIL", "SHADOW observation hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation scope must remain UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("paper_session_id") == report.get("shadow_session_id"):
        return ShadowObservationValidationResult("BLOCKED", "PAPER source session and SHADOW session must be distinct", "SNAPSHOT_SCOPE_MISMATCH")
    if "/paper/" not in report.get("paper_artifact_path", "") or "/shadow/" not in report.get("shadow_artifact_path", ""):
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation paths lack paper/shadow namespace separation", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_paper_validation_status") != "PASS" or report.get("source_paper_hash_valid") is not True:
        return ShadowObservationValidationResult("BLOCKED", "source PAPER gate is not validated and hash-bound", "SCHEMA_IDENTITY_MISMATCH")
    if int(report.get("shadow_sample_count", 0)) <= 0:
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation sample count is insufficient", "SAMPLE_INSUFFICIENT")
    if int(report.get("shadow_artifact_age_seconds", 0)) > int(report.get("max_artifact_age_seconds", 1)):
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation artifact is stale", "DATA_QUALITY_INSUFFICIENT")
    if report.get("optimizer_input_role") != "SHADOW_OBSERVATION_ONLY":
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation cannot be treated as promotion or live input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    if report.get("dashboard_display_truth_only") is not True:
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation must remain dashboard display truth only", "MEASUREMENT_MISSING")
    if any(report.get(field) for field in ("promotion_eligible", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation attempted live/order or scale-up state", "LIVE_FINAL_GUARD_FAILED")
    binding = report.get("source_evidence_binding")
    if not isinstance(binding, dict):
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation source binding is missing", "MEASUREMENT_MISSING")
    for field in ("exchange", "market_type", "candidate_id", "strategy_id", "strategy_build_id", "parameter_hash"):
        if binding.get(field) != report.get(field):
            return ShadowObservationValidationResult("BLOCKED", f"SHADOW observation source binding mismatch: {field}", "SNAPSHOT_SCOPE_MISMATCH")
    if binding.get("mode") != "PAPER" or binding.get("source_role") != "PAPER_OPERATION":
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation source binding must be PAPER_OPERATION", "SNAPSHOT_SCOPE_MISMATCH")
    if binding.get("artifact_hash") != report.get("paper_operation_gate_hash"):
        return ShadowObservationValidationResult("BLOCKED", "SHADOW observation source binding hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    blockers = report.get("blockers") or []
    if report.get("shadow_observation_status") == "PASS":
        if blockers:
            return ShadowObservationValidationResult("BLOCKED", "PASS SHADOW observation cannot carry blockers", blockers[0].get("code", "UNKNOWN_BLOCKED"))
        return ShadowObservationValidationResult("PASS", "SHADOW observation is paper-bound, namespace-separated, and live-blocked", None)
    if not blockers:
        return ShadowObservationValidationResult("BLOCKED", "blocked SHADOW observation must carry explicit blockers", "MEASUREMENT_MISSING")
    return ShadowObservationValidationResult("BLOCKED", "SHADOW observation is blocked", blockers[0].get("code", "UNKNOWN_BLOCKED"))


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "HIGH", "message": message}


def _live_flag_drift(*sources: dict[str, Any]) -> bool:
    return any(
        bool(source.get(field))
        for source in sources
        if isinstance(source, dict)
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "can_submit_order", "order_adapter_called")
    )


def _paper_gate_path(exchange: str, market_type: str, session_id: str) -> str:
    return f"system/runtime/{exchange.lower()}/{market_type.lower()}/paper/{session_id}/paper_operation_gate_report.json"


def _shadow_observation_path(exchange: str, market_type: str, session_id: str) -> str:
    return f"system/runtime/{exchange.lower()}/{market_type.lower()}/shadow/{session_id}/shadow_observation_report.json"


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()
