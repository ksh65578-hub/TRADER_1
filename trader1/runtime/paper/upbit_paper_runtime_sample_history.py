from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_persistent_loop import (
    LONG_RUN_EVIDENCE_BLOCKER_CODE,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID = "trader1.upbit_paper_runtime_sample_history.v1"
UPBIT_PAPER_RUNTIME_SAMPLE_SCHEMA_ID = "trader1.upbit_paper_runtime_sample.v1"
RUNTIME_SAMPLE_HISTORY_ROLE = "PAPER_RUNTIME_SAMPLE_HISTORY_NOT_LONG_RUN_EVIDENCE"
RUNTIME_SAMPLE_TRUTH_ROLE = "paper_runtime_analysis_truth"
DEFAULT_MIN_ACTUAL_LONG_RUN_SPAN_SECONDS = 86400
DEFAULT_MIN_ACTUAL_LONG_RUN_CYCLE_COUNT = 2880
DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT = 30
PAPER_SCOPE_COLLECTING_STATUS = "COLLECT_PAPER_SCOPE_SAMPLES"
PAPER_SCOPE_FLOOR_MET_STATUS = "PAPER_SCOPE_SAMPLE_FLOOR_MET"
PAPER_SCOPE_MISSING_STATUS = "NO_CANDIDATE_SCOPE"


@dataclass(frozen=True)
class UpbitPaperRuntimeSampleHistoryValidationResult:
    status: str
    message: str
    blocker_code: str | None


@dataclass(frozen=True)
class _ArtifactJsonSource:
    display_path: str
    path: Path
    zip_member: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_runtime_sample_hash(sample: dict[str, Any]) -> str:
    payload = dict(sample)
    payload.pop("sample_hash", None)
    return _sha256_json(payload)


def upbit_paper_runtime_sample_history_hash(history: dict[str, Any]) -> str:
    payload = dict(history)
    payload.pop("history_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    return value, None


def _zip_member_allowed(member: str) -> bool:
    normalized = member.replace("\\", "/")
    parts = normalized.split("/")
    return bool(normalized and not normalized.startswith("/") and ".." not in parts and "live" not in parts)


def _safe_read_artifact_json(
    *,
    root: Path,
    source_path: str,
    session_id: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if not _artifact_path_allowed(source_path, session_id):
        return None, "path_not_allowed"
    if "#" not in source_path:
        return _safe_read_json(root / source_path)

    archive_path_text, member = source_path.split("#", 1)
    if not _artifact_path_allowed(archive_path_text, session_id) or not _zip_member_allowed(member):
        return None, "zip_member_not_allowed"
    archive_path = root / archive_path_text
    try:
        with zipfile.ZipFile(archive_path) as archive:
            raw = archive.read(member)
    except FileNotFoundError:
        return None, "missing"
    except KeyError:
        return None, "missing_zip_member"
    except (OSError, zipfile.BadZipFile):
        return None, "invalid_zip"
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    return value, None


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _span_seconds(samples: list[dict[str, Any]]) -> int:
    timestamps = [_parse_utc(sample.get("generated_at_utc")) for sample in samples]
    valid = sorted(timestamp for timestamp in timestamps if timestamp is not None)
    if len(valid) < 2:
        return 0
    return int((valid[-1] - valid[0]).total_seconds())


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _natural_text_key(value: Any) -> tuple[tuple[int, int | str], ...]:
    parts = re.split(r"(\d+)", str(value))
    key: list[tuple[int, int | str]] = []
    for part in parts:
        if not part:
            continue
        key.append((0, int(part)) if part.isdigit() else (1, part))
    return tuple(key)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    prefix = f"system/runtime/upbit/krw_spot/paper/{session_id}/"
    parts = path.replace("\\", "/").split("/")
    return path.startswith(prefix) and ".." not in parts and "live" not in parts


def _candidate_scope_key(sample: dict[str, Any]) -> tuple[str, str, str, str, str, str] | None:
    if sample.get("scorecard_candidate_identity_binding_status") != "BOUND":
        return None
    if any(sample.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        return None
    exchange = str(sample.get("exchange") or "")
    market_type = str(sample.get("market_type") or "")
    candidate_id = str(sample.get("scorecard_candidate_id") or "")
    strategy_id = str(sample.get("scorecard_strategy_id") or "")
    parameter_hash = str(sample.get("scorecard_parameter_hash") or "").upper()
    symbol = str(sample.get("scorecard_symbol") or "")
    if not all((exchange, market_type, candidate_id, strategy_id, parameter_hash, symbol)):
        return None
    if re.fullmatch(r"[0-9A-F]{64}", parameter_hash) is None:
        return None
    return exchange, market_type, candidate_id, strategy_id, parameter_hash, symbol


def _candidate_scope_id(key: tuple[str, str, str, str, str, str]) -> str:
    exchange, market_type, candidate_id, strategy_id, parameter_hash, _symbol = key
    return f"{exchange}:{market_type}:PAPER:{candidate_id}:{strategy_id}:{parameter_hash}"


def _candidate_scope_next_action(summary: dict[str, Any]) -> str:
    deficit = _safe_int(summary.get("sample_deficit"))
    if deficit <= 0:
        return (
            "PAPER samples meet the per-candidate scope floor; keep collecting paired SHADOW/window/span "
            "evidence before any live review."
        )
    return (
        f"Collect {deficit} more PAPER samples for candidate {summary.get('candidate_id')} with strategy "
        f"{summary.get('strategy_id')} and parameter hash {summary.get('parameter_hash')}."
    )


def _candidate_scope_sample_summaries(
    samples: list[dict[str, Any]],
    *,
    min_required_sample_count: int,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for sample in samples:
        key = _candidate_scope_key(sample)
        if key is None:
            continue
        exchange, market_type, candidate_id, strategy_id, parameter_hash, symbol = key
        summary = buckets.setdefault(
            key,
            {
                "candidate_scope_id": _candidate_scope_id(key),
                "exchange": exchange,
                "market_type": market_type,
                "mode": "PAPER",
                "symbol": symbol,
                "candidate_id": candidate_id,
                "strategy_id": strategy_id,
                "parameter_hash": parameter_hash,
                "sample_count": 0,
                "entry_reason_count": 0,
                "exit_reason_count": 0,
                "no_trade_reason_count": 0,
                "candidate_count_total": 0,
                "first_sample_at_utc": sample.get("generated_at_utc"),
                "latest_sample_at_utc": sample.get("generated_at_utc"),
                "latest_loop_id": sample.get("loop_id"),
                "latest_cycle_id": sample.get("cycle_id"),
                "latest_final_decision": sample.get("final_decision"),
                "latest_candidate_decision": sample.get("scorecard_candidate_decision"),
                "latest_sample_hash": sample.get("sample_hash"),
                "latest_runtime_cycle_hash": sample.get("source_runtime_cycle_hash"),
                "min_required_sample_count": int(min_required_sample_count),
                "sample_deficit": int(min_required_sample_count),
                "scope_progress_status": PAPER_SCOPE_COLLECTING_STATUS,
                "next_collection_action": "RUN_MORE_PAPER_SAMPLE_WINDOWS",
                "next_operator_action": "",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
        )
        summary["sample_count"] += 1
        summary["entry_reason_count"] += _safe_int(sample.get("entry_reason_count"))
        summary["exit_reason_count"] += _safe_int(sample.get("exit_reason_count"))
        summary["no_trade_reason_count"] += _safe_int(sample.get("no_trade_reason_count"))
        summary["candidate_count_total"] += _safe_int(sample.get("candidate_count"))
        summary["latest_sample_at_utc"] = sample.get("generated_at_utc")
        summary["latest_loop_id"] = sample.get("loop_id")
        summary["latest_cycle_id"] = sample.get("cycle_id")
        summary["latest_final_decision"] = sample.get("final_decision")
        summary["latest_candidate_decision"] = sample.get("scorecard_candidate_decision")
        summary["latest_sample_hash"] = sample.get("sample_hash")
        summary["latest_runtime_cycle_hash"] = sample.get("source_runtime_cycle_hash")

    summaries = list(buckets.values())
    for summary in summaries:
        sample_count = _safe_int(summary.get("sample_count"))
        deficit = max(0, int(min_required_sample_count) - sample_count)
        summary["sample_deficit"] = deficit
        summary["scope_progress_status"] = PAPER_SCOPE_FLOOR_MET_STATUS if deficit == 0 else PAPER_SCOPE_COLLECTING_STATUS
        summary["next_collection_action"] = (
            "KEEP_PAPER_RUNNING_FOR_PAIRED_WINDOWS" if deficit == 0 else "RUN_MORE_PAPER_SAMPLE_WINDOWS"
        )
        summary["next_operator_action"] = _candidate_scope_next_action(summary)

    return sorted(
        summaries,
        key=lambda item: (
            item.get("sample_count", 0),
            item.get("entry_reason_count", 0) > 0,
            item.get("latest_candidate_decision") == "PAPER_ENTRY_REVIEW",
            item.get("entry_reason_count", 0),
            -item.get("no_trade_reason_count", 0),
            str(item.get("latest_sample_at_utc") or ""),
            str(item.get("candidate_id") or ""),
            str(item.get("strategy_id") or ""),
            str(item.get("parameter_hash") or ""),
        ),
        reverse=True,
    )


def _active_candidate_scope_fields(
    summaries: list[dict[str, Any]],
    *,
    min_required_sample_count: int,
) -> dict[str, Any]:
    if not summaries:
        return {
            "candidate_scope_sample_summary_count": 0,
            "candidate_scope_sample_summaries": [],
            "active_candidate_scope": None,
            "active_candidate_scope_status": PAPER_SCOPE_MISSING_STATUS,
            "active_candidate_scope_sample_count": 0,
            "active_candidate_scope_sample_deficit": int(min_required_sample_count),
            "active_candidate_scope_next_action": (
                "Keep PAPER running until a source-bound candidate, strategy, and parameter scope appears."
            ),
        }
    active = summaries[0]
    return {
        "candidate_scope_sample_summary_count": len(summaries),
        "candidate_scope_sample_summaries": summaries,
        "active_candidate_scope": active,
        "active_candidate_scope_status": str(active["scope_progress_status"]),
        "active_candidate_scope_sample_count": int(active["sample_count"]),
        "active_candidate_scope_sample_deficit": int(active["sample_deficit"]),
        "active_candidate_scope_next_action": str(active["next_operator_action"]),
    }


def _archive_batches_root(root: Path, session_id: str) -> Path:
    return _runtime_base(root, session_id) / "paper_runtime" / "runner" / "archive"


def _source_path_from_archive_member(member: str, session_id: str) -> str | None:
    safe_name = member.replace("\\", "/").split("/")[-1]
    source_path = safe_name.replace("__", "/")
    if _artifact_path_allowed(source_path, session_id):
        return source_path
    return None


def _archived_artifact_source_map(
    *,
    root: Path,
    session_id: str,
    groups: set[str],
) -> dict[str, _ArtifactJsonSource]:
    archive_root = _archive_batches_root(root, session_id)
    sources: dict[str, _ArtifactJsonSource] = {}
    if not archive_root.exists():
        return sources

    for batch_dir in sorted(path for path in archive_root.iterdir() if path.is_dir() and path.name.startswith("runner-retention-")):
        for group in sorted(groups):
            group_dir = batch_dir / group
            if not group_dir.exists():
                continue
            for artifact_path in sorted(path for path in group_dir.rglob("*") if path.is_file()):
                member = artifact_path.relative_to(batch_dir).as_posix()
                source_path = _source_path_from_archive_member(member, session_id)
                if source_path is None:
                    continue
                sources.setdefault(
                    source_path,
                    _ArtifactJsonSource(display_path=_relative_posix(artifact_path, root), path=artifact_path),
                )

    for archive_path in sorted(archive_root.glob("runner-retention-*.zip")):
        try:
            with zipfile.ZipFile(archive_path) as archive:
                members = sorted(archive.namelist())
        except (OSError, zipfile.BadZipFile):
            continue
        for member in members:
            normalized_member = member.replace("\\", "/")
            group = normalized_member.split("/", 1)[0]
            if group not in groups or not _zip_member_allowed(normalized_member):
                continue
            source_path = _source_path_from_archive_member(normalized_member, session_id)
            if source_path is None:
                continue
            display_path = f"{_relative_posix(archive_path, root)}#{normalized_member}"
            sources.setdefault(
                source_path,
                _ArtifactJsonSource(display_path=display_path, path=archive_path, zip_member=normalized_member),
            )
    return sources


def _loop_report_sources(root: Path, session_id: str) -> list[_ArtifactJsonSource]:
    base = _runtime_base(root, session_id)
    sources_by_display_path: dict[str, _ArtifactJsonSource] = {}
    if base.exists():
        for path in sorted((base / "paper_runtime").glob("*.persistent_loop_report.json")):
            source = _ArtifactJsonSource(display_path=_relative_posix(path, root), path=path)
            sources_by_display_path[source.display_path] = source
    for source_path, source in _archived_artifact_source_map(
        root=root,
        session_id=session_id,
        groups={"persistent_loop_reports"},
    ).items():
        if source_path.endswith(".persistent_loop_report.json"):
            sources_by_display_path.setdefault(source.display_path, source)
    return sorted(sources_by_display_path.values(), key=lambda source: _natural_text_key(source.display_path))


def _runtime_cycle_source(
    cycle_result: dict[str, Any],
    root: Path,
    session_id: str,
    archived_cycle_sources: dict[str, _ArtifactJsonSource],
) -> _ArtifactJsonSource | None:
    for artifact_path in cycle_result.get("artifact_paths") or []:
        if isinstance(artifact_path, str) and artifact_path.endswith(".runtime_cycle.json"):
            normalized_path = artifact_path.replace("\\", "/")
            active_path = root / normalized_path
            if active_path.is_file():
                return _ArtifactJsonSource(display_path=normalized_path, path=active_path)
            archived_source = archived_cycle_sources.get(normalized_path)
            if archived_source is not None:
                return archived_source
            if _artifact_path_allowed(normalized_path, session_id):
                return _ArtifactJsonSource(display_path=normalized_path, path=active_path)
    return None


def _entry_reason_evidence_count(runtime_cycle: dict[str, Any]) -> int:
    explicit_entry_reasons = len(runtime_cycle.get("entry_reasons") or [])
    selected = runtime_cycle.get("selected_candidate")
    entry_review_candidates = sum(
        1
        for candidate in runtime_cycle.get("strategy_candidates") or []
        if isinstance(candidate, dict) and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
    )
    if isinstance(selected, dict) and selected.get("decision") == "PAPER_ENTRY_REVIEW":
        return max(explicit_entry_reasons, entry_review_candidates, 1)
    return max(explicit_entry_reasons, entry_review_candidates)


def _exit_reason_evidence_count(runtime_cycle: dict[str, Any]) -> int:
    final_decision = str(runtime_cycle.get("final_decision") or "")
    if final_decision not in {"EXIT_POSITION", "REDUCE_POSITION", "HOLD_POSITION"}:
        return 0
    reason_count = len(runtime_cycle.get("no_trade_reasons") or [])
    position_decision = runtime_cycle.get("position_management_decision")
    if isinstance(position_decision, dict):
        for field in (
            "final_decision",
            "requested_position_decision",
            "reason_code",
            "execution_adjusted_position_decision_reason",
        ):
            if position_decision.get(field):
                reason_count += 1
    return max(reason_count, 1)


def _decimal_value(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _candidate_is_non_live(candidate: dict[str, Any]) -> bool:
    return not any(
        candidate.get(field) is True
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
    )


def _candidate_rank_key(candidate: dict[str, Any]) -> tuple[Decimal, Decimal, int, str]:
    return (
        _decimal_value(candidate.get("candidate_selection_score")),
        _decimal_value(candidate.get("net_ev_after_cost_bps")),
        -int(candidate.get("selection_priority", 999) or 999),
        str(candidate.get("candidate_id") or ""),
    )


def _paper_entry_review_candidates(runtime_cycle: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in runtime_cycle.get("strategy_candidates") or []
        if isinstance(candidate, dict)
        and candidate.get("decision") == "PAPER_ENTRY_REVIEW"
        and isinstance(candidate.get("candidate_id"), str)
        and _candidate_is_non_live(candidate)
    ]


def _strategy_id_for_family(strategy_family: str) -> str:
    mapping = {
        "PULLBACK_TREND_LONG": "trend_pullback",
        "BREAKOUT_RETEST_LONG": "breakout_retest",
        "VWAP_MEAN_REVERSION": "vwap_mean_reversion",
    }
    return mapping.get(strategy_family, strategy_family.lower())


def _candidate_parameter_hash(candidate: dict[str, Any]) -> str | None:
    explicit_hash = str(candidate.get("parameter_hash") or "").upper()
    if (
        candidate.get("mutation_status") == "APPLIED_TO_PAPER_CANDIDATE"
        and candidate.get("mutation_id")
        and re.fullmatch(r"[0-9A-F]{64}", explicit_hash)
    ):
        return explicit_hash
    candidate_id = str(candidate.get("candidate_id") or "")
    strategy_family = str(candidate.get("strategy_family") or "")
    symbol = str(candidate.get("symbol") or "")
    if not candidate_id or not strategy_family or not symbol:
        return None
    return hashlib.sha256(f"{candidate_id}:{strategy_family}:{symbol}".encode("utf-8")).hexdigest().upper()


_PAPER_SCOPE_FOCUS_SAMPLE_HISTORY_STATUSES = frozenset(
    {
        "SELECTED",
        "MANAGED_POSITION_OVERRIDES_SCOPE_FOCUS",
        "FOCUS_CANDIDATE_NOT_ENTRY_REVIEW",
        "SCORE_GAP_TOO_WIDE",
        "NET_EV_GAP_TOO_WIDE",
    }
)


def _paper_scope_focus_candidate_from_runtime_cycle(runtime_cycle: dict[str, Any]) -> dict[str, Any] | None:
    continuity = runtime_cycle.get("paper_scope_continuity_decision")
    if not isinstance(continuity, dict):
        return None
    if continuity.get("requested") is not True:
        return None
    if str(continuity.get("selection_status") or "") not in _PAPER_SCOPE_FOCUS_SAMPLE_HISTORY_STATUSES:
        return None

    requested_candidate_id = str(continuity.get("requested_candidate_id") or "")
    requested_symbol = str(continuity.get("requested_symbol") or "")
    requested_strategy_id = str(continuity.get("requested_strategy_id") or "")
    requested_parameter_hash = str(continuity.get("requested_parameter_hash") or "").upper()
    if not requested_candidate_id:
        return None

    for candidate in runtime_cycle.get("strategy_candidates") or []:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("candidate_id") != requested_candidate_id:
            continue
        if not _candidate_is_non_live(candidate):
            return None
        candidate_symbol = str(candidate.get("symbol") or "")
        strategy_family = str(candidate.get("strategy_family") or "")
        candidate_strategy_id = _strategy_id_for_family(strategy_family) if strategy_family else ""
        candidate_parameter_hash = _candidate_parameter_hash(candidate)
        if requested_symbol and candidate_symbol != requested_symbol:
            return None
        if requested_strategy_id and candidate_strategy_id != requested_strategy_id:
            return None
        if requested_parameter_hash and candidate_parameter_hash != requested_parameter_hash:
            return None
        return candidate
    return None


def _scorecard_candidate_from_runtime_cycle(runtime_cycle: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    focused = _paper_scope_focus_candidate_from_runtime_cycle(runtime_cycle)
    if focused is not None:
        return "PAPER_SCOPE_FOCUS_CANDIDATE", focused
    selected = runtime_cycle.get("selected_candidate")
    if isinstance(selected, dict) and selected.get("decision") == "PAPER_ENTRY_REVIEW" and _candidate_is_non_live(selected):
        return "SELECTED_CANDIDATE", selected
    entry_candidates = _paper_entry_review_candidates(runtime_cycle)
    if entry_candidates:
        return "PAPER_ENTRY_REVIEW_CANDIDATE", max(entry_candidates, key=_candidate_rank_key)
    if isinstance(selected, dict):
        return "SELECTED_CANDIDATE", selected
    return "MISSING", {}


def _candidate_identity_fields(runtime_cycle: dict[str, Any]) -> dict[str, Any]:
    identity_source, candidate = _scorecard_candidate_from_runtime_cycle(runtime_cycle)
    entry_candidates = sorted(_paper_entry_review_candidates(runtime_cycle), key=_candidate_rank_key, reverse=True)
    entry_candidate_ids = [str(candidate["candidate_id"]) for candidate in entry_candidates]
    entry_symbols = sorted({str(candidate.get("symbol")) for candidate in entry_candidates if candidate.get("symbol")})
    strategy_family = str(candidate.get("strategy_family") or "")
    symbol = str(candidate.get("symbol") or runtime_cycle.get("selected_symbol") or runtime_cycle.get("symbol") or "")
    candidate_id = str(candidate.get("candidate_id") or "")
    parameter_hash = _candidate_parameter_hash(candidate)
    identity_bound = bool(candidate_id and strategy_family and symbol and parameter_hash and _candidate_is_non_live(candidate))
    return {
        "scorecard_candidate_identity_source": identity_source,
        "scorecard_candidate_identity_binding_status": "BOUND" if identity_bound else "MISSING",
        "scorecard_candidate_live_flags_clear": _candidate_is_non_live(candidate),
        "scorecard_symbol": symbol or None,
        "scorecard_candidate_id": candidate_id or None,
        "scorecard_strategy_family": strategy_family or None,
        "scorecard_strategy_id": _strategy_id_for_family(strategy_family) if strategy_family else None,
        "scorecard_parameter_hash": parameter_hash,
        "scorecard_candidate_decision": candidate.get("decision"),
        "scorecard_candidate_net_ev_after_cost_bps": candidate.get("net_ev_after_cost_bps"),
        "scorecard_candidate_selection_score": candidate.get("candidate_selection_score"),
        "scorecard_expected_edge_bps": candidate.get("expected_edge_bps"),
        "scorecard_expected_cost_bps": candidate.get("expected_cost_bps"),
        "paper_entry_review_candidate_count": len(entry_candidates),
        "paper_entry_review_candidate_ids": entry_candidate_ids,
        "paper_entry_review_symbols": entry_symbols,
        "paper_entry_review_symbol_count": len(entry_symbols),
        "symbol_evidence_scorecard_count": int(
            runtime_cycle.get("symbol_evidence_scorecard_count")
            or len(runtime_cycle.get("symbol_evidence_scorecards") or [])
        ),
    }


def _build_sample(
    *,
    loop_report_path: str,
    loop_report: dict[str, Any],
    cycle_result: dict[str, Any],
    runtime_cycle_path: str,
    runtime_cycle: dict[str, Any],
    previous_sample_hash: str | None,
) -> dict[str, Any]:
    identity_fields = _candidate_identity_fields(runtime_cycle)
    sample = {
        "schema_id": UPBIT_PAPER_RUNTIME_SAMPLE_SCHEMA_ID,
        "generated_at_utc": runtime_cycle["generated_at_utc"],
        "project_id": "TRADER_1",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": loop_report["session_id"],
        "loop_id": loop_report["loop_id"],
        "cycle_id": cycle_result["cycle_id"],
        "source_loop_report_path": loop_report_path,
        "source_loop_report_hash": loop_report["loop_hash"],
        "source_runtime_cycle_path": runtime_cycle_path,
        "source_runtime_cycle_hash": runtime_cycle["cycle_hash"],
        "runtime_input_role": runtime_cycle["runtime_input_role"],
        "final_decision": runtime_cycle["final_decision"],
        "paper_ledger_head_hash": runtime_cycle.get("paper_ledger_head_hash"),
        "paper_portfolio_snapshot_hash": runtime_cycle.get("paper_portfolio_snapshot", {}).get("snapshot_hash"),
        "candidate_count": len(runtime_cycle.get("strategy_candidates") or []),
        "entry_reason_count": _entry_reason_evidence_count(runtime_cycle),
        "exit_reason_count": _exit_reason_evidence_count(runtime_cycle),
        "no_trade_reason_count": len(runtime_cycle.get("no_trade_reasons") or []),
        **identity_fields,
        "previous_sample_hash": previous_sample_hash,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "sample_hash": "",
    }
    sample["sample_hash"] = upbit_paper_runtime_sample_hash(sample)
    return sample


def build_upbit_paper_runtime_sample_history(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    history_id: str = "upbit-paper-runtime-sample-history",
    min_actual_long_run_span_seconds: int = DEFAULT_MIN_ACTUAL_LONG_RUN_SPAN_SECONDS,
    min_actual_long_run_cycle_count: int = DEFAULT_MIN_ACTUAL_LONG_RUN_CYCLE_COUNT,
    max_samples: int = 3000,
) -> dict[str, Any]:
    root = Path(root).resolve()
    loop_report_sources = _loop_report_sources(root, session_id)
    archived_cycle_sources = _archived_artifact_source_map(
        root=root,
        session_id=session_id,
        groups={"paper_runtime_cycles"},
    )
    samples: list[dict[str, Any]] = []
    accepted_loop_report_count = 0
    invalid_source_count = 0
    invalid_sources: list[dict[str, str]] = []
    seen_runtime_hashes: set[str] = set()
    duplicate_cycle_hash_count = 0
    source_loop_hashes: list[str] = []
    source_runtime_cycle_hashes: list[str] = []

    for loop_report_source in loop_report_sources:
        loop_report, load_error = _safe_read_artifact_json(
            root=root,
            source_path=loop_report_source.display_path,
            session_id=session_id,
        )
        if load_error or loop_report is None:
            invalid_source_count += 1
            invalid_sources.append({"path": loop_report_source.display_path, "reason": load_error or "unknown"})
            continue
        loop_result = validate_upbit_paper_persistent_loop_report(loop_report)
        if loop_result.status != "PASS":
            invalid_source_count += 1
            invalid_sources.append({"path": loop_report_source.display_path, "reason": loop_result.blocker_code or loop_result.message})
            continue
        accepted_loop_report_count += 1
        source_loop_hashes.append(loop_report["loop_hash"])
        for cycle_result in loop_report.get("cycle_results") or []:
            runtime_hash = cycle_result.get("runtime_cycle_hash")
            if runtime_hash in seen_runtime_hashes:
                duplicate_cycle_hash_count += 1
                continue
            runtime_source = _runtime_cycle_source(cycle_result, root, session_id, archived_cycle_sources)
            if runtime_source is None:
                invalid_source_count += 1
                invalid_sources.append({"path": loop_report_source.display_path, "reason": "runtime_cycle_path_missing"})
                continue
            runtime_cycle, runtime_error = _safe_read_artifact_json(
                root=root,
                source_path=runtime_source.display_path,
                session_id=session_id,
            )
            if runtime_error or runtime_cycle is None:
                invalid_source_count += 1
                invalid_sources.append({"path": runtime_source.display_path, "reason": runtime_error or "unknown"})
                continue
            runtime_result = validate_upbit_paper_runtime_cycle_report(runtime_cycle)
            if runtime_result.status != "PASS":
                invalid_source_count += 1
                invalid_sources.append({"path": runtime_source.display_path, "reason": runtime_result.blocker_code or runtime_result.message})
                continue
            if runtime_cycle.get("cycle_hash") != runtime_hash:
                invalid_source_count += 1
                invalid_sources.append({"path": runtime_source.display_path, "reason": "runtime_cycle_hash_mismatch"})
                continue
            seen_runtime_hashes.add(str(runtime_hash))
            previous_hash = samples[-1]["sample_hash"] if samples else None
            sample = _build_sample(
                loop_report_path=loop_report_source.display_path,
                loop_report=loop_report,
                cycle_result=cycle_result,
                runtime_cycle_path=runtime_source.display_path,
                runtime_cycle=runtime_cycle,
                previous_sample_hash=previous_hash,
            )
            samples.append(sample)
            source_runtime_cycle_hashes.append(runtime_cycle["cycle_hash"])
            if len(samples) >= max_samples:
                break
        if len(samples) >= max_samples:
            break

    samples.sort(
        key=lambda item: (
            item["generated_at_utc"],
            _natural_text_key(item.get("loop_id")),
            _natural_text_key(item.get("cycle_id")),
            _natural_text_key(item.get("source_runtime_cycle_path")),
        )
    )
    previous_hash: str | None = None
    for sample in samples:
        sample["previous_sample_hash"] = previous_hash
        sample["sample_hash"] = upbit_paper_runtime_sample_hash(sample)
        previous_hash = sample["sample_hash"]
    source_runtime_cycle_hashes = [sample["source_runtime_cycle_hash"] for sample in samples]

    observed_span_seconds = _span_seconds(samples)
    span_floor_met = observed_span_seconds >= min_actual_long_run_span_seconds
    cycle_floor_met = len(samples) >= min_actual_long_run_cycle_count
    candidate_scope_summaries = _candidate_scope_sample_summaries(
        samples,
        min_required_sample_count=DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
    )
    candidate_scope_fields = _active_candidate_scope_fields(
        candidate_scope_summaries,
        min_required_sample_count=DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
    )
    if duplicate_cycle_hash_count > 0:
        status = "BLOCKED"
        primary_blocker_code = "RECONCILIATION_REQUIRED"
    elif not samples and invalid_source_count > 0:
        status = "BLOCKED"
        primary_blocker_code = "RECONCILIATION_REQUIRED"
    elif not samples:
        status = "INSUFFICIENT_HISTORY"
        primary_blocker_code = "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING"
    else:
        status = "COLLECTING"
        primary_blocker_code = LONG_RUN_EVIDENCE_BLOCKER_CODE

    history = {
        "schema_id": UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "history_id": history_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": RUNTIME_SAMPLE_TRUTH_ROLE,
        "runtime_analysis_only": True,
        "execution_truth": False,
        "dashboard_truth_only": False,
        "history_evidence_role": RUNTIME_SAMPLE_HISTORY_ROLE,
        "runtime_sample_status": status,
        "primary_blocker_code": primary_blocker_code,
        "source_loop_report_count": len(loop_report_sources),
        "accepted_loop_report_count": accepted_loop_report_count,
        "accepted_cycle_sample_count": len(samples),
        "unique_runtime_cycle_hash_count": len({sample["source_runtime_cycle_hash"] for sample in samples}),
        "duplicate_cycle_hash_count": duplicate_cycle_hash_count,
        "invalid_source_count": invalid_source_count,
        "invalid_sources": invalid_sources,
        "first_sample_at_utc": samples[0]["generated_at_utc"] if samples else None,
        "latest_sample_at_utc": samples[-1]["generated_at_utc"] if samples else None,
        "observed_span_seconds": observed_span_seconds,
        "min_actual_long_run_span_seconds": min_actual_long_run_span_seconds,
        "min_actual_long_run_cycle_count": min_actual_long_run_cycle_count,
        "span_floor_met": span_floor_met,
        "cycle_floor_met": cycle_floor_met,
        "min_profitability_scope_sample_count": DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
        **candidate_scope_fields,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "long_run_next_action": "Collect validated, non-duplicated PAPER and SHADOW runtime history over the required wall-clock span before live review.",
        "promotion_eligible": False,
        "source_loop_report_hashes": source_loop_hashes,
        "source_runtime_cycle_hashes": source_runtime_cycle_hashes,
        "samples": samples,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "history_hash": "",
    }
    history["history_hash"] = upbit_paper_runtime_sample_history_hash(history)
    return history


def write_upbit_paper_runtime_sample_history(*, root: Path, history: dict[str, Any]) -> Path:
    path = _runtime_base(root, str(history["session_id"])) / "paper_runtime" / "upbit_paper_runtime_sample_history.json"
    durable_atomic_write_json(path, history)
    return path


def validate_upbit_paper_runtime_sample_history(history: dict[str, Any]) -> UpbitPaperRuntimeSampleHistoryValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "history_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "runtime_analysis_only",
        "execution_truth",
        "dashboard_truth_only",
        "history_evidence_role",
        "runtime_sample_status",
        "primary_blocker_code",
        "source_loop_report_count",
        "accepted_loop_report_count",
        "accepted_cycle_sample_count",
        "unique_runtime_cycle_hash_count",
        "duplicate_cycle_hash_count",
        "invalid_source_count",
        "invalid_sources",
        "first_sample_at_utc",
        "latest_sample_at_utc",
        "observed_span_seconds",
        "min_actual_long_run_span_seconds",
        "min_actual_long_run_cycle_count",
        "span_floor_met",
        "cycle_floor_met",
        "min_profitability_scope_sample_count",
        "candidate_scope_sample_summary_count",
        "candidate_scope_sample_summaries",
        "active_candidate_scope",
        "active_candidate_scope_status",
        "active_candidate_scope_sample_count",
        "active_candidate_scope_sample_deficit",
        "active_candidate_scope_next_action",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "source_loop_report_hashes",
        "source_runtime_cycle_hashes",
        "samples",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "history_hash",
    }
    missing = sorted(required - set(history))
    if missing:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", f"runtime sample history missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("schema_id") != UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY_SCHEMA_ID:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("history_hash") != upbit_paper_runtime_sample_history_hash(history):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("exchange") != "UPBIT" or history.get("market_type") != "KRW_SPOT" or history.get("mode") != "PAPER":
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if history.get("truth_role") != RUNTIME_SAMPLE_TRUTH_ROLE or history.get("history_evidence_role") != RUNTIME_SAMPLE_HISTORY_ROLE:
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history evidence role cannot claim live, dashboard, or execution truth", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    if history.get("runtime_analysis_only") is not True or history.get("execution_truth") or history.get("dashboard_truth_only"):
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history must remain analysis-only", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
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
        "scale_up_allowed",
    )
    if any(history.get(field) for field in forbidden_fields):
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history attempted live, order, promotion, long-run, or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    if history.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE or not history.get("long_run_next_action"):
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample history must expose the long-run evidence blocker", LONG_RUN_EVIDENCE_BLOCKER_CODE)

    invalid_sources = history.get("invalid_sources")
    invalid_source_count = int(history.get("invalid_source_count", -1))
    if not isinstance(invalid_sources, list) or invalid_source_count != len(invalid_sources):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample invalid source count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    session_id = str(history.get("session_id"))
    for invalid_source in invalid_sources:
        if not isinstance(invalid_source, dict):
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample invalid source must be an object", "SCHEMA_IDENTITY_MISMATCH")
        invalid_path = invalid_source.get("path")
        invalid_reason = invalid_source.get("reason")
        if not isinstance(invalid_path, str) or not _artifact_path_allowed(invalid_path, session_id):
            return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample invalid source path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not isinstance(invalid_reason, str) or not invalid_reason:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample invalid source reason missing", "SCHEMA_IDENTITY_MISMATCH")

    samples = history.get("samples")
    if not isinstance(samples, list):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history samples must be a list", "SCHEMA_IDENTITY_MISMATCH")
    if history.get("accepted_cycle_sample_count") != len(samples):
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "accepted cycle sample count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    runtime_hashes: list[str] = []
    previous_hash: str | None = None
    previous_timestamp: datetime | None = None
    for sample in samples:
        if not isinstance(sample, dict):
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("schema_id") != UPBIT_PAPER_RUNTIME_SAMPLE_SCHEMA_ID:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("sample_hash") != upbit_paper_runtime_sample_hash(sample):
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("previous_sample_hash") != previous_hash:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample hash chain mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if sample.get("exchange") != "UPBIT" or sample.get("market_type") != "KRW_SPOT" or sample.get("mode") != "PAPER" or sample.get("session_id") != session_id:
            return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
        for path_field in ("source_loop_report_path", "source_runtime_cycle_path"):
            path_value = sample.get(path_field)
            if not isinstance(path_value, str) or not _artifact_path_allowed(path_value, session_id):
                return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample source path escaped UPBIT PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if sample.get("live_order_ready") or sample.get("live_order_allowed") or sample.get("can_live_trade") or sample.get("scale_up_allowed"):
            return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample created live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        binding_status = sample.get("scorecard_candidate_identity_binding_status")
        if binding_status is not None:
            if binding_status not in {"BOUND", "MISSING"}:
                return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample candidate identity status is invalid", "SCHEMA_IDENTITY_MISMATCH")
            entry_candidate_ids = sample.get("paper_entry_review_candidate_ids")
            entry_symbols = sample.get("paper_entry_review_symbols")
            if not isinstance(entry_candidate_ids, list) or not isinstance(entry_symbols, list):
                return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample candidate identity lists are invalid", "SCHEMA_IDENTITY_MISMATCH")
            if sample.get("paper_entry_review_candidate_count") != len(entry_candidate_ids):
                return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample entry-review candidate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
            if sample.get("paper_entry_review_symbol_count") != len(set(entry_symbols)):
                return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample entry-review symbol count mismatch", "SCHEMA_IDENTITY_MISMATCH")
            if binding_status == "BOUND":
                for field in (
                    "scorecard_symbol",
                    "scorecard_candidate_id",
                    "scorecard_strategy_family",
                    "scorecard_strategy_id",
                    "scorecard_parameter_hash",
                    "scorecard_candidate_identity_source",
                ):
                    if not isinstance(sample.get(field), str) or not sample.get(field):
                        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", f"runtime sample candidate identity missing field: {field}", "SCHEMA_IDENTITY_MISMATCH")
                parameter_hash = str(sample.get("scorecard_parameter_hash") or "")
                if re.fullmatch(r"[0-9A-F]{64}", parameter_hash) is None:
                    return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample parameter hash is invalid", "SCHEMA_IDENTITY_MISMATCH")
                if sample.get("scorecard_candidate_live_flags_clear") is not True:
                    return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "runtime sample candidate identity attempted live or scale-up state", "LIVE_FINAL_GUARD_FAILED")
        timestamp = _parse_utc(sample.get("generated_at_utc"))
        if timestamp is None:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample timestamp is invalid", "SCHEMA_IDENTITY_MISMATCH")
        if previous_timestamp is not None and timestamp < previous_timestamp:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample timestamps are not monotonic", "SCHEMA_IDENTITY_MISMATCH")
        runtime_hashes.append(str(sample.get("source_runtime_cycle_hash")))
        previous_hash = sample["sample_hash"]
        previous_timestamp = timestamp

    unique_count = len(set(runtime_hashes))
    duplicate_count = len(runtime_hashes) - unique_count
    reported_duplicate_count = int(history.get("duplicate_cycle_hash_count", -1))
    if history.get("unique_runtime_cycle_hash_count") != unique_count or reported_duplicate_count < duplicate_count:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample duplicate count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if reported_duplicate_count:
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "duplicate runtime cycle samples require reconciliation", "RECONCILIATION_REQUIRED")
    if history.get("source_runtime_cycle_hashes") != runtime_hashes:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime cycle hash list is not bound to samples", "SCHEMA_IDENTITY_MISMATCH")
    observed_span_seconds = _span_seconds(samples)
    if history.get("observed_span_seconds") != observed_span_seconds:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample observed span mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected_span_floor_met = observed_span_seconds >= int(history.get("min_actual_long_run_span_seconds", -1))
    expected_cycle_floor_met = len(samples) >= int(history.get("min_actual_long_run_cycle_count", -1))
    if history.get("span_floor_met") is not expected_span_floor_met or history.get("cycle_floor_met") is not expected_cycle_floor_met:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample floor flag mismatch", "SCHEMA_IDENTITY_MISMATCH")
    min_scope_samples = int(history.get("min_profitability_scope_sample_count", -1))
    if min_scope_samples < 1:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample scope floor is invalid", "SCHEMA_IDENTITY_MISMATCH")
    expected_scope_summaries = _candidate_scope_sample_summaries(
        samples,
        min_required_sample_count=min_scope_samples,
    )
    expected_scope_fields = _active_candidate_scope_fields(
        expected_scope_summaries,
        min_required_sample_count=min_scope_samples,
    )
    for field in (
        "candidate_scope_sample_summary_count",
        "candidate_scope_sample_summaries",
        "active_candidate_scope",
        "active_candidate_scope_status",
        "active_candidate_scope_sample_count",
        "active_candidate_scope_sample_deficit",
        "active_candidate_scope_next_action",
    ):
        if history.get(field) != expected_scope_fields[field]:
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "FAIL",
                f"runtime sample candidate scope progress mismatch: {field}",
                "SCHEMA_IDENTITY_MISMATCH",
            )
    for summary in expected_scope_summaries:
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
            if summary.get(field) is not False:
                return UpbitPaperRuntimeSampleHistoryValidationResult(
                    "BLOCKED",
                    "runtime sample candidate scope summary attempted live or scale-up state",
                    "LIVE_FINAL_GUARD_FAILED",
                )
    if samples:
        if history.get("first_sample_at_utc") != samples[0]["generated_at_utc"] or history.get("latest_sample_at_utc") != samples[-1]["generated_at_utc"]:
            return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample first/latest timestamp mismatch", "SCHEMA_IDENTITY_MISMATCH")
    elif history.get("first_sample_at_utc") is not None or history.get("latest_sample_at_utc") is not None:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "empty runtime sample history cannot carry first/latest timestamps", "SCHEMA_IDENTITY_MISMATCH")
    if invalid_source_count > 0 and not samples:
        if history.get("runtime_sample_status") != "BLOCKED":
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                "invalid runtime source with no accepted samples must block sample history",
                "RECONCILIATION_REQUIRED",
            )
        return UpbitPaperRuntimeSampleHistoryValidationResult(
            "BLOCKED",
            "invalid runtime sources left no accepted source-bound PAPER samples",
            "RECONCILIATION_REQUIRED",
        )
    if invalid_source_count > 0 and samples and history.get("runtime_sample_status") not in {"COLLECTING", "BLOCKED"}:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample invalid source status is inconsistent", "SCHEMA_IDENTITY_MISMATCH")
    if not samples and history.get("runtime_sample_status") != "INSUFFICIENT_HISTORY":
        return UpbitPaperRuntimeSampleHistoryValidationResult("BLOCKED", "empty runtime sample history must be insufficient", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if samples and history.get("runtime_sample_status") not in {"COLLECTING", "BLOCKED"}:
        return UpbitPaperRuntimeSampleHistoryValidationResult("FAIL", "runtime sample history status is inconsistent", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperRuntimeSampleHistoryValidationResult("PASS", "Upbit PAPER runtime sample history is hash-linked, scoped, and live-blocked", None)


def validate_upbit_paper_runtime_sample_history_sources(
    *,
    root: Path,
    history: dict[str, Any],
) -> UpbitPaperRuntimeSampleHistoryValidationResult:
    """Validate the current source files behind a sample history artifact.

    The schema validator proves the history was internally consistent when it was
    written.  This root-bound check prevents a later cleanup or retention action
    from leaving a stale PASS history whose source cycle files are gone.
    """
    base_result = validate_upbit_paper_runtime_sample_history(history)
    if base_result.status != "PASS":
        return base_result

    root = Path(root).resolve()
    session_id = str(history.get("session_id"))
    for sample in history.get("samples") or []:
        if not isinstance(sample, dict):
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "FAIL",
                "runtime sample must be an object",
                "SCHEMA_IDENTITY_MISMATCH",
            )

        loop_path_text = str(sample.get("source_loop_report_path") or "")
        runtime_path_text = str(sample.get("source_runtime_cycle_path") or "")
        for source_path_text in (loop_path_text, runtime_path_text):
            if not _artifact_path_allowed(source_path_text, session_id):
                return UpbitPaperRuntimeSampleHistoryValidationResult(
                    "BLOCKED",
                    "runtime sample source path escaped UPBIT PAPER namespace",
                    "SNAPSHOT_SCOPE_MISMATCH",
                )

        loop_report, loop_error = _safe_read_artifact_json(
            root=root,
            source_path=loop_path_text,
            session_id=session_id,
        )
        if loop_error is not None or not isinstance(loop_report, dict):
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                f"runtime sample source loop report is missing or unreadable: {loop_path_text}",
                "RECONCILIATION_REQUIRED",
            )
        loop_result = validate_upbit_paper_persistent_loop_report(loop_report)
        if loop_result.status != "PASS":
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                f"runtime sample source loop report failed validation: {loop_result.message}",
                loop_result.blocker_code or "RECONCILIATION_REQUIRED",
            )
        if loop_report.get("loop_hash") != sample.get("source_loop_report_hash"):
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                "runtime sample source loop report hash mismatch",
                "RECONCILIATION_REQUIRED",
            )

        runtime_cycle, runtime_error = _safe_read_artifact_json(
            root=root,
            source_path=runtime_path_text,
            session_id=session_id,
        )
        if runtime_error is not None or not isinstance(runtime_cycle, dict):
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                f"runtime sample source cycle is missing or unreadable: {runtime_path_text}",
                "RECONCILIATION_REQUIRED",
            )
        runtime_result = validate_upbit_paper_runtime_cycle_report(runtime_cycle)
        if runtime_result.status != "PASS":
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                f"runtime sample source cycle failed validation: {runtime_result.message}",
                runtime_result.blocker_code or "RECONCILIATION_REQUIRED",
            )
        if runtime_cycle.get("cycle_hash") != sample.get("source_runtime_cycle_hash"):
            return UpbitPaperRuntimeSampleHistoryValidationResult(
                "BLOCKED",
                "runtime sample source cycle hash mismatch",
                "RECONCILIATION_REQUIRED",
            )

    return UpbitPaperRuntimeSampleHistoryValidationResult(
        "PASS",
        "Upbit PAPER runtime sample history sources exist, validate, and match sample hashes",
        None,
    )
