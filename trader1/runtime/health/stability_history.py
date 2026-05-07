from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


RUNTIME_STABILITY_HISTORY_SCHEMA_ID = "trader1.runtime_stability_history.v1"
STABILITY_SAMPLE_SCHEMA_ID = "trader1.runtime_stability_sample.v1"
HISTORY_STATUSES = {"INSUFFICIENT_HISTORY", "VALIDATED_HISTORY", "ATTENTION", "ERROR"}
SPAN_VALIDATION_STATUSES = {"INSUFFICIENT_SPAN", "SPAN_VALIDATED"}
STABILITY_STATUSES = {"STABLE", "ATTENTION", "ERROR"}
METRIC_STATUSES = {"PASS", "WARN", "FAIL", "STALE", "UNTESTED"}
DEFAULT_MIN_VALIDATED_SPAN_SECONDS = 3600
DEFAULT_MIN_VALIDATED_SAMPLE_COUNT = 2
REQUIRED_HISTORY_FIELDS = {
    "schema_id",
    "generated_at_utc",
    "project_id",
    "exchange",
    "market_type",
    "mode",
    "session_id",
    "truth_role",
    "display_only",
    "dashboard_truth_only",
    "history_status",
    "history_window",
    "first_sample_at_utc",
    "latest_sample_at_utc",
    "observed_span_seconds",
    "min_validated_span_seconds",
    "min_validated_sample_count",
    "span_validation_status",
    "max_samples",
    "sample_count",
    "stable_sample_count",
    "attention_sample_count",
    "error_sample_count",
    "stale_metric_sample_count",
    "latest_sample_hash",
    "reset_reason",
    "samples",
    "live_order_ready",
    "live_order_allowed",
    "can_live_trade",
    "scale_up_allowed",
    "history_hash",
}


@dataclass(frozen=True)
class StabilityHistoryValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def sample_hash(sample: dict[str, Any]) -> str:
    payload = dict(sample)
    payload.pop("sample_hash", None)
    return sha256_json(payload)


def history_hash(history: dict[str, Any]) -> str:
    payload = dict(history)
    payload.pop("history_hash", None)
    return sha256_json(payload)


def _status_counts(metrics: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(METRIC_STATUSES)}
    for metric in metrics:
        status = str(metric.get("status") or "UNTESTED").upper()
        counts[status if status in METRIC_STATUSES else "FAIL"] += 1
    return counts


def _sample_status(status: str, metric_counts: dict[str, int]) -> str:
    if status == "ERROR" or metric_counts.get("FAIL", 0):
        return "ERROR"
    if status == "ATTENTION" or any(metric_counts.get(key, 0) for key in ("WARN", "STALE", "UNTESTED")):
        return "ATTENTION"
    return "STABLE"


def build_stability_sample(
    *,
    dashboard_shell: dict[str, Any],
    previous_sample_hash: str | None,
) -> dict[str, Any]:
    stability = dashboard_shell.get("stability_trends", {}) if isinstance(dashboard_shell, dict) else {}
    metrics = [
        {
            "metric_id": str(metric.get("metric_id", "UNKNOWN")),
            "status": str(metric.get("status", "UNTESTED")).upper(),
            "value_display": str(metric.get("value_display", "UNTESTED")),
        }
        for metric in stability.get("metrics", [])
        if isinstance(metric, dict)
    ]
    metric_counts = _status_counts(metrics)
    status = _sample_status(str(stability.get("status", "ATTENTION")).upper(), metric_counts)
    generated_at = dashboard_shell.get("generated_at_utc")
    if not isinstance(generated_at, str) or not generated_at.strip():
        generated_at = utc_now()
    sample = {
        "schema_id": STABILITY_SAMPLE_SCHEMA_ID,
        "generated_at_utc": generated_at,
        "project_id": "TRADER_1",
        "exchange": dashboard_shell.get("exchange"),
        "market_type": dashboard_shell.get("market_type"),
        "mode": dashboard_shell.get("mode"),
        "session_id": dashboard_shell.get("session_id"),
        "source_dashboard_hash": dashboard_shell.get("dashboard_hash"),
        "status": status,
        "severity": "ERROR" if status == "ERROR" else "WARNING" if status == "ATTENTION" else "NORMAL",
        "metric_status_counts": metric_counts,
        "metrics": metrics,
        "previous_sample_hash": previous_sample_hash,
        "display_only": True,
        "dashboard_truth_only": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "sample_hash": "",
    }
    sample["sample_hash"] = sample_hash(sample)
    return sample


def _same_scope(history: dict[str, Any], sample: dict[str, Any]) -> bool:
    return all(history.get(key) == sample.get(key) for key in ("exchange", "market_type", "mode", "session_id"))


def _distinct_source_dashboard_hash_count(samples: list[dict[str, Any]]) -> int:
    return len({sample.get("source_dashboard_hash") for sample in samples if sample.get("source_dashboard_hash")})


def _parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _sample_timestamps(samples: list[dict[str, Any]]) -> list[datetime] | None:
    timestamps = [_parse_utc_timestamp(sample.get("generated_at_utc")) for sample in samples]
    if any(timestamp is None for timestamp in timestamps):
        return None
    return [timestamp for timestamp in timestamps if timestamp is not None]


def _timestamps_are_monotonic(samples: list[dict[str, Any]]) -> bool:
    timestamps = _sample_timestamps(samples)
    if timestamps is None:
        return False
    return all(current >= previous for previous, current in zip(timestamps, timestamps[1:]))


def _observed_span_seconds(samples: list[dict[str, Any]]) -> int:
    timestamps = _sample_timestamps(samples)
    if not timestamps or len(timestamps) < 2:
        return 0
    seconds = int((timestamps[-1] - timestamps[0]).total_seconds())
    return seconds if seconds > 0 else 0


def _span_validation_status(
    samples: list[dict[str, Any]],
    *,
    min_validated_span_seconds: int,
    min_validated_sample_count: int,
) -> str:
    if len(samples) < min_validated_sample_count:
        return "INSUFFICIENT_SPAN"
    if _distinct_source_dashboard_hash_count(samples) < min_validated_sample_count:
        return "INSUFFICIENT_SPAN"
    if not _timestamps_are_monotonic(samples):
        return "INSUFFICIENT_SPAN"
    if _observed_span_seconds(samples) < min_validated_span_seconds:
        return "INSUFFICIENT_SPAN"
    return "SPAN_VALIDATED"


def _history_status(
    samples: list[dict[str, Any]],
    *,
    min_validated_span_seconds: int = DEFAULT_MIN_VALIDATED_SPAN_SECONDS,
    min_validated_sample_count: int = DEFAULT_MIN_VALIDATED_SAMPLE_COUNT,
) -> str:
    if any(sample.get("status") == "ERROR" for sample in samples):
        return "ERROR"
    if any(sample.get("status") == "ATTENTION" for sample in samples):
        return "ATTENTION"
    if (
        _span_validation_status(
            samples,
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        )
        != "SPAN_VALIDATED"
    ):
        return "INSUFFICIENT_HISTORY"
    return "VALIDATED_HISTORY"


def _history_span_fields(
    samples: list[dict[str, Any]],
    *,
    min_validated_span_seconds: int,
    min_validated_sample_count: int,
) -> dict[str, Any]:
    return {
        "first_sample_at_utc": samples[0].get("generated_at_utc") if samples else None,
        "latest_sample_at_utc": samples[-1].get("generated_at_utc") if samples else None,
        "observed_span_seconds": _observed_span_seconds(samples),
        "min_validated_span_seconds": min_validated_span_seconds,
        "min_validated_sample_count": min_validated_sample_count,
        "span_validation_status": _span_validation_status(
            samples,
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        ),
    }


def _sample_metric_by_id(sample: dict[str, Any], metric_id: str) -> dict[str, Any] | None:
    metrics = sample.get("metrics", [])
    if not isinstance(metrics, list):
        return None
    for metric in metrics:
        if isinstance(metric, dict) and metric.get("metric_id") == metric_id:
            return metric
    return None


def _uses_runner_backed_stability_metrics(sample: dict[str, Any]) -> bool:
    heartbeat_metric = _sample_metric_by_id(sample, "heartbeat_age") or {}
    artifact_metric = _sample_metric_by_id(sample, "runtime_artifact_pressure") or {}
    queue_metric = _sample_metric_by_id(sample, "queue_backlog") or {}
    return (
        sample.get("status") != "ERROR"
        and sample.get("metric_status_counts", {}).get("FAIL", 0) == 0
        and heartbeat_metric.get("status") == "WARN"
        and heartbeat_metric.get("value_display") == "RUNNER_ACTIVE / HEARTBEAT_STALE"
        and artifact_metric.get("status") == "PASS"
        and queue_metric.get("status") in {"PASS", "WARN"}
    )


def _contains_legacy_artifact_pressure_error(samples: list[dict[str, Any]]) -> bool:
    for sample in samples:
        if sample.get("status") != "ERROR":
            continue
        artifact_metric = _sample_metric_by_id(sample, "runtime_artifact_pressure") or {}
        queue_metric = _sample_metric_by_id(sample, "queue_backlog") or {}
        resource_metric = _sample_metric_by_id(sample, "resource_health") or {}
        if "FAIL" in {
            artifact_metric.get("status"),
            queue_metric.get("status"),
            resource_metric.get("status"),
        }:
            return True
    return False


def _should_reset_for_runner_backed_metric_semantics(
    previous_history: dict[str, Any],
    previous_samples: list[dict[str, Any]],
    sample: dict[str, Any],
) -> bool:
    return (
        previous_history.get("history_status") == "ERROR"
        and _uses_runner_backed_stability_metrics(sample)
        and _contains_legacy_artifact_pressure_error(previous_samples)
    )


def _new_history(
    sample: dict[str, Any],
    *,
    max_samples: int,
    reset_reason: str | None,
    min_validated_span_seconds: int,
    min_validated_sample_count: int,
) -> dict[str, Any]:
    sample = dict(sample)
    sample["previous_sample_hash"] = None
    sample["sample_hash"] = ""
    sample["sample_hash"] = sample_hash(sample)
    samples = [sample]
    status = _history_status(
        samples,
        min_validated_span_seconds=min_validated_span_seconds,
        min_validated_sample_count=min_validated_sample_count,
    )
    history = {
        "schema_id": RUNTIME_STABILITY_HISTORY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": sample.get("exchange"),
        "market_type": sample.get("market_type"),
        "mode": sample.get("mode"),
        "session_id": sample.get("session_id"),
        "truth_role": "dashboard_serving_truth",
        "display_only": True,
        "dashboard_truth_only": True,
        "history_status": status,
        "history_window": "LAST_N_SAMPLES",
        **_history_span_fields(
            samples,
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        ),
        "max_samples": max_samples,
        "sample_count": 1,
        "stable_sample_count": 1 if sample.get("status") == "STABLE" else 0,
        "attention_sample_count": 1 if sample.get("status") == "ATTENTION" else 0,
        "error_sample_count": 1 if sample.get("status") == "ERROR" else 0,
        "stale_metric_sample_count": 1 if sample.get("metric_status_counts", {}).get("STALE", 0) else 0,
        "latest_sample_hash": sample.get("sample_hash"),
        "reset_reason": reset_reason,
        "samples": [sample],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "history_hash": "",
    }
    history["history_hash"] = history_hash(history)
    return history


def append_stability_history(
    previous_history: dict[str, Any] | None,
    dashboard_shell: dict[str, Any],
    *,
    max_samples: int = 60,
    min_validated_span_seconds: int = DEFAULT_MIN_VALIDATED_SPAN_SECONDS,
    min_validated_sample_count: int = DEFAULT_MIN_VALIDATED_SAMPLE_COUNT,
) -> dict[str, Any]:
    if max_samples < 2:
        max_samples = 2
    min_validated_span_seconds = max(int(min_validated_span_seconds), 0)
    min_validated_sample_count = max(int(min_validated_sample_count), 2)
    previous_samples = previous_history.get("samples", []) if isinstance(previous_history, dict) else []
    previous_hash = None
    if isinstance(previous_history, dict) and previous_samples:
        previous_hash = previous_samples[-1].get("sample_hash")
    sample = build_stability_sample(dashboard_shell=dashboard_shell, previous_sample_hash=previous_hash)
    if not isinstance(previous_history, dict):
        return _new_history(
            sample,
            max_samples=max_samples,
            reset_reason=None,
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        )
    previous_valid = validate_stability_history(previous_history)
    if previous_valid.status != "PASS" or not _same_scope(previous_history, sample):
        return _new_history(
            sample,
            max_samples=max_samples,
            reset_reason="PREVIOUS_HISTORY_ISOLATED",
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        )
    if _should_reset_for_runner_backed_metric_semantics(previous_history, previous_samples, sample):
        return _new_history(
            sample,
            max_samples=max_samples,
            reset_reason="RUNNER_BACKED_STABILITY_METRIC_SOURCE_CHANGED",
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        )
    samples = [*previous_samples, sample][-max_samples:]
    if samples and samples[0].get("previous_sample_hash") not in {None, ""}:
        samples[0] = dict(samples[0])
        samples[0]["previous_sample_hash"] = None
        samples[0]["sample_hash"] = ""
        samples[0]["sample_hash"] = sample_hash(samples[0])
        for index in range(1, len(samples)):
            samples[index] = dict(samples[index])
            samples[index]["previous_sample_hash"] = samples[index - 1]["sample_hash"]
            samples[index]["sample_hash"] = ""
            samples[index]["sample_hash"] = sample_hash(samples[index])
    status = _history_status(
        samples,
        min_validated_span_seconds=min_validated_span_seconds,
        min_validated_sample_count=min_validated_sample_count,
    )
    history = {
        "schema_id": RUNTIME_STABILITY_HISTORY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "exchange": sample.get("exchange"),
        "market_type": sample.get("market_type"),
        "mode": sample.get("mode"),
        "session_id": sample.get("session_id"),
        "truth_role": "dashboard_serving_truth",
        "display_only": True,
        "dashboard_truth_only": True,
        "history_status": status,
        "history_window": "LAST_N_SAMPLES",
        **_history_span_fields(
            samples,
            min_validated_span_seconds=min_validated_span_seconds,
            min_validated_sample_count=min_validated_sample_count,
        ),
        "max_samples": max_samples,
        "sample_count": len(samples),
        "stable_sample_count": sum(1 for item in samples if item.get("status") == "STABLE"),
        "attention_sample_count": sum(1 for item in samples if item.get("status") == "ATTENTION"),
        "error_sample_count": sum(1 for item in samples if item.get("status") == "ERROR"),
        "stale_metric_sample_count": sum(1 for item in samples if item.get("metric_status_counts", {}).get("STALE", 0)),
        "latest_sample_hash": samples[-1].get("sample_hash") if samples else None,
        "reset_reason": None,
        "samples": samples,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "history_hash": "",
    }
    history["history_hash"] = history_hash(history)
    return history


def validate_stability_history(
    history: dict[str, Any],
    *,
    expected_exchange: str | None = None,
    expected_market_type: str | None = None,
    expected_mode: str | None = None,
    expected_session_id: str | None = None,
) -> StabilityHistoryValidationResult:
    if history.get("schema_id") != RUNTIME_STABILITY_HISTORY_SCHEMA_ID:
        return StabilityHistoryValidationResult("FAIL", "stability history schema mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("history_hash") != history_hash(history):
        return StabilityHistoryValidationResult("FAIL", "stability history hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    missing_fields = sorted(field for field in REQUIRED_HISTORY_FIELDS if field not in history)
    if missing_fields:
        return StabilityHistoryValidationResult(
            "FAIL",
            "stability history missing required field(s): " + ", ".join(missing_fields),
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if history.get("truth_role") != "dashboard_serving_truth":
        return StabilityHistoryValidationResult("BLOCKED", "stability history cannot claim execution truth", "LIVE_FINAL_GUARD_FAILED")
    if history.get("display_only") is not True or history.get("dashboard_truth_only") is not True:
        return StabilityHistoryValidationResult("BLOCKED", "stability history must remain display-only", "LIVE_FINAL_GUARD_FAILED")
    if history.get("live_order_ready") or history.get("live_order_allowed") or history.get("can_live_trade") or history.get("scale_up_allowed"):
        return StabilityHistoryValidationResult("BLOCKED", "stability history attempted to create live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    expected = {
        "exchange": expected_exchange,
        "market_type": expected_market_type,
        "mode": expected_mode,
        "session_id": expected_session_id,
    }
    for key, value in expected.items():
        if value is not None and history.get(key) != value:
            return StabilityHistoryValidationResult("BLOCKED", f"stability history scope mismatch: {key}", "SNAPSHOT_SCOPE_MISMATCH")
    samples = history.get("samples")
    if not isinstance(samples, list) or not samples:
        return StabilityHistoryValidationResult("FAIL", "stability history must include samples", "HARD_TRUTH_MISSING")
    min_validated_span_seconds = history.get("min_validated_span_seconds")
    min_validated_sample_count = history.get("min_validated_sample_count")
    if not isinstance(min_validated_span_seconds, int) or min_validated_span_seconds < 0:
        return StabilityHistoryValidationResult("FAIL", "stability history minimum span is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(min_validated_sample_count, int) or min_validated_sample_count < 2:
        return StabilityHistoryValidationResult("FAIL", "stability history minimum sample count is invalid", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("sample_count") != len(samples):
        return StabilityHistoryValidationResult("FAIL", "stability history sample_count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if len(samples) > history.get("max_samples", 0):
        return StabilityHistoryValidationResult("FAIL", "stability history exceeds max_samples", "SCHEMA_IDENTITY_MISMATCH")
    previous_hash = None
    for sample in samples:
        if sample.get("schema_id") != STABILITY_SAMPLE_SCHEMA_ID:
            return StabilityHistoryValidationResult("FAIL", "stability sample schema mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("sample_hash") != sample_hash(sample):
            return StabilityHistoryValidationResult("FAIL", "stability sample hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("previous_sample_hash") != previous_hash:
            return StabilityHistoryValidationResult("FAIL", "stability sample hash chain mismatch", "SCHEMA_IDENTITY_MISMATCH")
        previous_hash = sample.get("sample_hash")
        if not _same_scope(history, sample):
            return StabilityHistoryValidationResult("BLOCKED", "stability history mixed runtime scope", "SNAPSHOT_SCOPE_MISMATCH")
        if sample.get("status") not in STABILITY_STATUSES:
            return StabilityHistoryValidationResult("FAIL", "stability sample status unknown", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("live_order_ready") or sample.get("live_order_allowed") or sample.get("can_live_trade") or sample.get("scale_up_allowed"):
            return StabilityHistoryValidationResult("BLOCKED", "stability sample attempted live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    if not _timestamps_are_monotonic(samples):
        return StabilityHistoryValidationResult("FAIL", "stability sample timestamps must be valid and monotonic", "SCHEMA_IDENTITY_MISMATCH")
    expected_counts = {
        "stable_sample_count": sum(1 for item in samples if item.get("status") == "STABLE"),
        "attention_sample_count": sum(1 for item in samples if item.get("status") == "ATTENTION"),
        "error_sample_count": sum(1 for item in samples if item.get("status") == "ERROR"),
        "stale_metric_sample_count": sum(1 for item in samples if item.get("metric_status_counts", {}).get("STALE", 0)),
    }
    for field, expected_value in expected_counts.items():
        if history.get(field) != expected_value:
            return StabilityHistoryValidationResult("FAIL", "stability history aggregate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("latest_sample_hash") != samples[-1].get("sample_hash"):
        return StabilityHistoryValidationResult("FAIL", "stability history latest hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_span_fields = _history_span_fields(
        samples,
        min_validated_span_seconds=min_validated_span_seconds,
        min_validated_sample_count=min_validated_sample_count,
    )
    for field, expected_value in expected_span_fields.items():
        if history.get(field) != expected_value:
            return StabilityHistoryValidationResult("FAIL", f"stability history span field mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("span_validation_status") not in SPAN_VALIDATION_STATUSES:
        return StabilityHistoryValidationResult("FAIL", "stability history span validation status unknown", "SCHEMA_IDENTITY_MISMATCH")
    expected_status = _history_status(
        samples,
        min_validated_span_seconds=min_validated_span_seconds,
        min_validated_sample_count=min_validated_sample_count,
    )
    if history.get("history_status") != expected_status:
        return StabilityHistoryValidationResult("FAIL", "stability history status mismatch", "SCHEMA_IDENTITY_MISMATCH")
    return StabilityHistoryValidationResult("PASS", "stability history is display-only, scoped, and hash-linked", None)
