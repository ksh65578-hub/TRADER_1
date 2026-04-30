from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from trader1.research.shadow.shadow_observation import (
    shadow_observation_hash,
    validate_shadow_observation_report,
)
from trader1.research.shadow.shadow_runner import AGENTS_SHA256, TRADER1_SHA256, utc_now


SHADOW_OBSERVATION_STREAM_SCHEMA_ID = "trader1.shadow_observation_stream_report.v1"


@dataclass(frozen=True)
class ShadowObservationStreamValidationResult:
    status: str
    message: str
    blocker_code: str | None


def shadow_observation_stream_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("stream_hash", None)
    return _sha256_payload(payload)


def build_shadow_observation_stream_report(
    *,
    stream_id: str,
    observations: list[dict[str, Any]],
    min_required_observation_count: int = 20,
    min_required_evidence_span_hours: int = 120,
    evidence_span_hours: int = 0,
    max_artifact_age_seconds: int = 900,
) -> dict[str, Any]:
    if not observations:
        raise ValueError("observations are required for SHADOW observation stream report")

    first = observations[0]
    exchange = str(first.get("exchange") or "UPBIT")
    market_type = str(first.get("market_type") or "KRW_SPOT")
    candidate_id = str(first.get("candidate_id") or "candidate-missing")
    strategy_id = str(first.get("strategy_id") or "strategy-missing")
    strategy_build_id = str(first.get("strategy_build_id") or "strategy-build-missing")
    parameter_hash = str(first.get("parameter_hash") or "0" * 64)
    stream_path = f"system/runtime/{exchange.lower()}/{market_type.lower()}/shadow/{stream_id}/shadow_observation_stream_report.json"

    blockers: list[dict[str, str]] = []
    observation_hashes: list[str] = []
    paper_operation_gate_hashes: list[str] = []
    paper_session_ids: list[str] = []
    shadow_session_ids: list[str] = []
    source_binding_hashes: list[str] = []
    observation_bindings: list[dict[str, Any]] = []
    sequence_numbers: list[int] = []

    for index, observation in enumerate(observations, start=1):
        result = validate_shadow_observation_report(observation)
        observation_hash = str(observation.get("observation_hash") or "")
        paper_hash = str(observation.get("paper_operation_gate_hash") or "")
        paper_session = str(observation.get("paper_session_id") or "")
        shadow_session = str(observation.get("shadow_session_id") or "")
        binding = observation.get("source_evidence_binding") if isinstance(observation.get("source_evidence_binding"), dict) else {}

        observation_hashes.append(observation_hash)
        paper_operation_gate_hashes.append(paper_hash)
        paper_session_ids.append(paper_session)
        shadow_session_ids.append(shadow_session)
        source_binding_hashes.append(str(binding.get("artifact_hash") or ""))
        sequence_numbers.append(int(observation.get("stream_sequence_number", index)))
        observation_bindings.append(
            {
                "observation_id": str(observation.get("observation_id") or f"missing-{index}"),
                "sequence_number": int(observation.get("stream_sequence_number", index)),
                "observation_hash": observation_hash,
                "paper_operation_gate_hash": paper_hash,
                "paper_session_id": paper_session,
                "shadow_session_id": shadow_session,
                "shadow_artifact_age_seconds": int(observation.get("shadow_artifact_age_seconds", 0)),
                "validation_status": result.status,
            }
        )

        if result.status != "PASS":
            blockers.append(_blocker(result.blocker_code or "MEASUREMENT_MISSING", f"observation {index} is not valid: {result.message}"))
        if observation_hash != shadow_observation_hash(observation):
            blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", f"observation {index} hash does not match content"))
        if observation.get("exchange") != exchange or observation.get("market_type") != market_type:
            blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", f"observation {index} exchange/market_type scope mismatch"))
        if observation.get("source_mode") != "PAPER" or observation.get("mode") != "SHADOW":
            blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", f"observation {index} mode/source_mode mismatch"))
        if observation.get("candidate_id") != candidate_id or observation.get("strategy_id") != strategy_id:
            blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", f"observation {index} candidate or strategy mismatch"))
        if observation.get("strategy_build_id") != strategy_build_id or observation.get("parameter_hash") != parameter_hash:
            blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", f"observation {index} strategy build or parameter mismatch"))
        if any(observation.get(field) for field in ("promotion_eligible", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
            blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", f"observation {index} attempted live/order or scale-up state"))
        if int(observation.get("shadow_artifact_age_seconds", 0)) > max_artifact_age_seconds:
            blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", f"observation {index} is stale for stream guard"))

    duplicate_observation_count = len(observation_hashes) - len(set(observation_hashes))
    duplicate_paper_source_count = len(paper_operation_gate_hashes) - len(set(paper_operation_gate_hashes))
    duplicate_shadow_session_count = len(shadow_session_ids) - len(set(shadow_session_ids))
    paper_shadow_session_overlap = bool(set(paper_session_ids) & set(shadow_session_ids))
    sequence_monotonic = sequence_numbers == sorted(sequence_numbers) and len(sequence_numbers) == len(set(sequence_numbers))
    source_binding_hash_match = paper_operation_gate_hashes == source_binding_hashes
    observation_count = len(observations)
    evidence_window_count = len(set(shadow_session_ids))

    if duplicate_observation_count:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "SHADOW observation stream contains duplicate observation hashes"))
    if duplicate_paper_source_count:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "SHADOW observation stream reused a PAPER source hash"))
    if duplicate_shadow_session_count:
        blockers.append(_blocker("DUPLICATE_WRITER_RISK", "SHADOW observation stream reused a SHADOW session"))
    if paper_shadow_session_overlap:
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "SHADOW stream has overlapping PAPER and SHADOW sessions"))
    if not sequence_monotonic:
        blockers.append(_blocker("PARTIAL_WRITE_RECOVERY_REQUIRED", "SHADOW observation stream sequence is not strictly increasing"))
    if not source_binding_hash_match:
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "SHADOW observation source binding hash drift detected"))
    if observation_count < min_required_observation_count:
        blockers.append(_blocker("SAMPLE_INSUFFICIENT", "SHADOW observation stream has insufficient observation count"))
    if evidence_span_hours < min_required_evidence_span_hours:
        blockers.append(_blocker("DATA_QUALITY_INSUFFICIENT", "SHADOW observation stream has insufficient evidence span"))

    report = {
        "schema_id": SHADOW_OBSERVATION_STREAM_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": TRADER1_SHA256,
            "agents_sha256": AGENTS_SHA256,
        },
        "stream_id": stream_id,
        "exchange": exchange,
        "market_type": market_type,
        "source_mode": "PAPER",
        "mode": "SHADOW",
        "stream_artifact_path": stream_path,
        "candidate_id": candidate_id,
        "strategy_id": strategy_id,
        "strategy_build_id": strategy_build_id,
        "parameter_hash": parameter_hash,
        "observation_count": observation_count,
        "min_required_observation_count": min_required_observation_count,
        "evidence_window_count": evidence_window_count,
        "evidence_span_hours": evidence_span_hours,
        "min_required_evidence_span_hours": min_required_evidence_span_hours,
        "max_artifact_age_seconds": max_artifact_age_seconds,
        "observation_hashes": observation_hashes,
        "paper_operation_gate_hashes": paper_operation_gate_hashes,
        "source_binding_hashes": source_binding_hashes,
        "paper_session_ids": paper_session_ids,
        "shadow_session_ids": shadow_session_ids,
        "observation_bindings": observation_bindings,
        "duplicate_observation_count": duplicate_observation_count,
        "duplicate_paper_source_count": duplicate_paper_source_count,
        "duplicate_shadow_session_count": duplicate_shadow_session_count,
        "paper_shadow_session_overlap": paper_shadow_session_overlap,
        "sequence_monotonic": sequence_monotonic,
        "source_binding_hash_match": source_binding_hash_match,
        "stream_status": "PASS" if not blockers else "BLOCKED",
        "long_run_evidence_eligible": False,
        "optimizer_input_role": "SHADOW_STREAM_OBSERVATION_ONLY",
        "dashboard_display_truth_only": True,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "order_adapter_called": False,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": _dedupe_blockers(blockers),
        "stream_hash": "",
    }
    report["stream_hash"] = shadow_observation_stream_hash(report)
    return report


def validate_shadow_observation_stream_report(report: dict[str, Any]) -> ShadowObservationStreamValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "authority",
        "stream_id",
        "exchange",
        "market_type",
        "source_mode",
        "mode",
        "stream_artifact_path",
        "candidate_id",
        "strategy_id",
        "strategy_build_id",
        "parameter_hash",
        "observation_count",
        "min_required_observation_count",
        "evidence_window_count",
        "evidence_span_hours",
        "min_required_evidence_span_hours",
        "max_artifact_age_seconds",
        "observation_hashes",
        "paper_operation_gate_hashes",
        "source_binding_hashes",
        "paper_session_ids",
        "shadow_session_ids",
        "observation_bindings",
        "duplicate_observation_count",
        "duplicate_paper_source_count",
        "duplicate_shadow_session_count",
        "paper_shadow_session_overlap",
        "sequence_monotonic",
        "source_binding_hash_match",
        "stream_status",
        "long_run_evidence_eligible",
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
        "stream_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ShadowObservationStreamValidationResult("FAIL", f"SHADOW stream missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != SHADOW_OBSERVATION_STREAM_SCHEMA_ID:
        return ShadowObservationStreamValidationResult("FAIL", "SHADOW stream schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("stream_hash") != shadow_observation_stream_hash(report):
        return ShadowObservationStreamValidationResult("FAIL", "SHADOW stream hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT":
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream must remain UPBIT/KRW_SPOT for MVP-4", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_mode") != "PAPER" or report.get("mode") != "SHADOW":
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream must bind PAPER source to SHADOW output", "SNAPSHOT_SCOPE_MISMATCH")
    if "/shadow/" not in report.get("stream_artifact_path", ""):
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream path lacks shadow namespace", "SNAPSHOT_SCOPE_MISMATCH")
    for field in (
        "observation_hashes",
        "paper_operation_gate_hashes",
        "source_binding_hashes",
        "paper_session_ids",
        "shadow_session_ids",
        "observation_bindings",
    ):
        if len(report.get(field) or []) != int(report.get("observation_count", -1)):
            return ShadowObservationStreamValidationResult("BLOCKED", f"SHADOW stream count mismatch: {field}", "PARTIAL_WRITE_RECOVERY_REQUIRED")

    observation_hashes = [str(item) for item in report.get("observation_hashes", [])]
    paper_hashes = [str(item) for item in report.get("paper_operation_gate_hashes", [])]
    source_binding_hashes = [str(item) for item in report.get("source_binding_hashes", [])]
    paper_sessions = [str(item) for item in report.get("paper_session_ids", [])]
    shadow_sessions = [str(item) for item in report.get("shadow_session_ids", [])]
    bindings = [item for item in report.get("observation_bindings", []) if isinstance(item, dict)]
    if len(bindings) != int(report.get("observation_count", -1)):
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream binding count mismatch", "PARTIAL_WRITE_RECOVERY_REQUIRED")

    if observation_hashes != [str(item.get("observation_hash") or "") for item in bindings]:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream observation hash summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if paper_hashes != [str(item.get("paper_operation_gate_hash") or "") for item in bindings]:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream PAPER hash summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if paper_sessions != [str(item.get("paper_session_id") or "") for item in bindings]:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream PAPER session summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if shadow_sessions != [str(item.get("shadow_session_id") or "") for item in bindings]:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream SHADOW session summary drift", "SCHEMA_IDENTITY_MISMATCH")

    duplicate_observation_count = _duplicate_count(observation_hashes)
    duplicate_paper_source_count = _duplicate_count(paper_hashes)
    duplicate_shadow_session_count = _duplicate_count(shadow_sessions)
    paper_shadow_session_overlap = bool(set(paper_sessions) & set(shadow_sessions))
    sequence_numbers = [int(item.get("sequence_number", 0)) for item in bindings]
    sequence_monotonic = sequence_numbers == sorted(sequence_numbers) and len(sequence_numbers) == len(set(sequence_numbers))
    source_binding_hash_match = paper_hashes == source_binding_hashes
    evidence_window_count = len(set(shadow_sessions))

    if int(report.get("duplicate_observation_count", -1)) != duplicate_observation_count:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream duplicate observation summary drift", "DUPLICATE_WRITER_RISK")
    if int(report.get("duplicate_paper_source_count", -1)) != duplicate_paper_source_count:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream duplicate PAPER source summary drift", "DUPLICATE_WRITER_RISK")
    if int(report.get("duplicate_shadow_session_count", -1)) != duplicate_shadow_session_count:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream duplicate SHADOW session summary drift", "DUPLICATE_WRITER_RISK")
    if bool(report.get("paper_shadow_session_overlap")) != paper_shadow_session_overlap:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream session-overlap summary drift", "SNAPSHOT_SCOPE_MISMATCH")
    if bool(report.get("sequence_monotonic")) != sequence_monotonic:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream sequence summary drift", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if bool(report.get("source_binding_hash_match")) != source_binding_hash_match:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream source binding summary drift", "SCHEMA_IDENTITY_MISMATCH")
    if int(report.get("evidence_window_count", -1)) != evidence_window_count:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream evidence window summary drift", "DATA_QUALITY_INSUFFICIENT")

    if duplicate_observation_count or duplicate_paper_source_count or duplicate_shadow_session_count:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream duplicate writer risk detected", "DUPLICATE_WRITER_RISK")
    if paper_shadow_session_overlap:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream mixed PAPER and SHADOW sessions", "SNAPSHOT_SCOPE_MISMATCH")
    if not sequence_monotonic:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream sequence is not strictly increasing", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if not source_binding_hash_match:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream source binding hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if int(report.get("observation_count", 0)) < int(report.get("min_required_observation_count", 1)):
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream has insufficient observation count", "SAMPLE_INSUFFICIENT")
    if int(report.get("evidence_span_hours", 0)) < int(report.get("min_required_evidence_span_hours", 1)):
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream has insufficient evidence span", "DATA_QUALITY_INSUFFICIENT")
    if report.get("optimizer_input_role") != "SHADOW_STREAM_OBSERVATION_ONLY":
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream cannot become promotion or live input", "OPTIMIZER_DIRECT_LIVE_FORBIDDEN")
    if report.get("long_run_evidence_eligible") is not False:
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream guard cannot claim long-run eligibility in this MVP-4 patch", "LIVE_FINAL_GUARD_FAILED")
    if any(report.get(field) for field in ("promotion_eligible", "live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed", "order_adapter_called")):
        return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream attempted live/order or scale-up state", "LIVE_FINAL_GUARD_FAILED")

    blockers = report.get("blockers") or []
    if report.get("stream_status") == "PASS":
        if blockers:
            return ShadowObservationStreamValidationResult("BLOCKED", "PASS SHADOW stream cannot carry blockers", blockers[0].get("code", "UNKNOWN_BLOCKED"))
        return ShadowObservationStreamValidationResult("PASS", "SHADOW stream is ordered, unique, scoped, hash-bound, and live-blocked", None)
    if not blockers:
        return ShadowObservationStreamValidationResult("BLOCKED", "blocked SHADOW stream must carry explicit blockers", "MEASUREMENT_MISSING")
    return ShadowObservationStreamValidationResult("BLOCKED", "SHADOW stream is blocked", blockers[0].get("code", "UNKNOWN_BLOCKED"))


def _blocker(code: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": "HIGH", "message": message}


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


def _duplicate_count(values: list[str]) -> int:
    return len(values) - len(set(values))


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()
