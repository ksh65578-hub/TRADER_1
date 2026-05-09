from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from trader1.research.profitability.candidate_scorecard import (
    candidate_generation_report_hash,
    safe_candidate_scorecard_filename,
    validate_candidate_generation_report,
)
from trader1.research.profitability.strategy_mutation_compiler import (
    load_validated_mutation_spec_for_candidate,
)
from trader1.research.replay.replay_runner import (
    load_public_replay_robustness_report,
    public_replay_robustness_report_hash,
    public_replay_source_evidence_id,
    validate_public_replay_robustness_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT,
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history_sources,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


PAPER_CANDIDATE_REHYDRATION_SCHEMA_ID = "trader1.paper_candidate_rehydration_report.v1"
DEFAULT_UPBIT_PAPER_SESSION_ID = "mvp1_upbit_paper_launcher"
DEFAULT_RUNTIME_LINKAGE_MAX_AGE_SECONDS = 6 * 60 * 60
VALIDATED_GENERATION_STATUS = "ALTERNATIVE_PUBLIC_REPLAY_VALIDATED"

LIVE_AND_PRIVATE_FLAGS = (
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
LIVE_FALSE_FLAGS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


@dataclass(frozen=True)
class PaperTradeIntentInputs:
    paper_scope_focus: dict[str, Any]
    paper_candidate_rehydration_report: dict[str, Any]
    candidate_item: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _paper_base(root: Path, session_id: str) -> Path:
    return Path(root) / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def candidate_generation_report_path(root: Path, session_id: str = DEFAULT_UPBIT_PAPER_SESSION_ID) -> Path:
    return _paper_base(root, session_id) / "profitability" / "candidate_generation_report.json"


def paper_candidate_rehydration_report_path(root: Path, session_id: str = DEFAULT_UPBIT_PAPER_SESSION_ID) -> Path:
    return _paper_base(root, session_id) / "profitability" / "paper_candidate_rehydration_report.json"


def _candidate_discovery_runtime_path(root: Path, session_id: str) -> Path:
    return _paper_base(root, session_id) / "profitability" / "candidate_generation_discovery_runtime_cycle.json"


def _source_runtime_cycle_paths(root: Path, session_id: str, cycle_id: str) -> list[Path]:
    base = _paper_base(root, session_id)
    return [
        base / "paper_runtime" / "cycles" / f"{cycle_id}.runtime_cycle.json",
        base / "upbit_paper_runtime_cycle_report.json",
        _candidate_discovery_runtime_path(root, session_id),
    ]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _hash_is_64_hex(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "0123456789abcdefABCDEF" for character in text)


def _has_live_or_private_drift(*reports: dict[str, Any] | None) -> bool:
    for report in reports:
        if not isinstance(report, dict):
            continue
        if any(report.get(flag) is True for flag in LIVE_AND_PRIVATE_FLAGS):
            return True
    return False


def _runtime_source_evidence_id(cycle_id: str, cycle_hash: str) -> str:
    return f"upbit_paper_runtime_cycle:{cycle_id}:{cycle_hash}"


def _replay_source_evidence_id(replay_id: str, replay_hash: str) -> str:
    return public_replay_source_evidence_id(replay_id, replay_hash)


def _candidate_item(report: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    for item in report.get("candidate_items") or []:
        if isinstance(item, dict) and str(item.get("candidate_id") or "") == candidate_id:
            return item
    return None


def _current_open_position_count(snapshot: dict[str, Any] | None) -> int:
    if not isinstance(snapshot, dict):
        return 0
    count = snapshot.get("open_position_count")
    try:
        if int(count or 0) > 0:
            return int(count or 0)
    except (TypeError, ValueError):
        pass
    positions = snapshot.get("positions")
    if isinstance(positions, list):
        return sum(1 for item in positions if isinstance(item, dict) and _safe_decimal(item.get("quantity")) > 0)
    return 0


def _pending_confirm_detected(*reports: dict[str, Any] | None) -> bool:
    pending_values = {"PENDING", "PENDING_CONFIRM", "PARTIAL_FILL_PENDING", "OPEN", "AWAITING_CONFIRMATION"}
    for report in reports:
        if not isinstance(report, dict):
            continue
        for field in ("pending_confirm_count", "pending_confirmation_count", "open_order_count"):
            try:
                if int(report.get(field) or 0) > 0:
                    return True
            except (TypeError, ValueError):
                continue
        for field in ("order_lifecycle_state", "paper_order_state", "confirm_state"):
            if str(report.get(field) or "").upper() in pending_values:
                return True
        execution = report.get("paper_broker_execution")
        if isinstance(execution, dict):
            for field in ("order_lifecycle_state", "paper_order_state", "confirm_state"):
                if str(execution.get(field) or "").upper() in pending_values:
                    return True
    return False


def _duplicate_replay_candle_detected(replay_report: dict[str, Any] | None) -> bool:
    if not isinstance(replay_report, dict):
        return False
    seen: set[tuple[str, str]] = set()
    for row in replay_report.get("sample_rows") or []:
        if not isinstance(row, dict):
            continue
        timestamp = str(row.get("event_time_utc") or row.get("event_time") or "")
        runtime_cycle_id = str(row.get("runtime_cycle_id") or "")
        if not timestamp:
            continue
        key = (runtime_cycle_id, timestamp)
        if key in seen:
            return True
        seen.add(key)
    return False


def _load_bound_runtime_cycle(
    *,
    root: Path,
    session_id: str,
    source_runtime_cycle_id: str,
    source_runtime_cycle_hash: str,
) -> tuple[dict[str, Any] | None, Path | None, str]:
    for path in _source_runtime_cycle_paths(root, session_id, source_runtime_cycle_id):
        runtime = _read_json(path)
        if not isinstance(runtime, dict):
            continue
        if str(runtime.get("cycle_id") or "") != source_runtime_cycle_id:
            continue
        if str(runtime.get("cycle_hash") or "").upper() != source_runtime_cycle_hash.upper():
            return runtime, path, "HASH_MISMATCH"
        if upbit_paper_runtime_cycle_hash(runtime).upper() != source_runtime_cycle_hash.upper():
            return runtime, path, "HASH_MISMATCH"
        runtime_result = validate_upbit_paper_runtime_cycle_report(runtime)
        if runtime_result.status != "PASS":
            return runtime, path, str(runtime_result.blocker_code or "RUNTIME_CONTRACT_FAILED")
        return runtime, path, "PASS"
    return None, None, "MISSING"


def _candidate_scope_progress(
    *,
    root: Path,
    session_id: str,
    candidate_id: str,
    strategy_id: str,
    parameter_hash: str,
) -> tuple[int, int, str]:
    sample_count = 0
    sample_deficit = DEFAULT_MIN_PROFITABILITY_SCOPE_SAMPLE_COUNT
    status = "COLLECT_PAPER_SCOPE_SAMPLES"
    try:
        history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
        history_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=history)
    except Exception:
        return sample_count, sample_deficit, status
    if getattr(history_result, "status", None) != "PASS":
        return sample_count, sample_deficit, status
    for summary in history.get("candidate_scope_sample_summaries") or []:
        if not isinstance(summary, dict):
            continue
        if (
            str(summary.get("candidate_id") or "") == candidate_id
            and str(summary.get("strategy_id") or "") == strategy_id
            and str(summary.get("parameter_hash") or "").upper() == parameter_hash.upper()
        ):
            sample_count = max(0, int(summary.get("sample_count") or 0))
            sample_deficit = max(0, int(summary.get("sample_deficit") or 0))
            status = str(summary.get("scope_progress_status") or status)
            break
    if sample_deficit <= 0:
        status = "PAPER_SCOPE_SAMPLE_FLOOR_MET"
    return sample_count, sample_deficit, status


def _rehydration_hash(report: dict[str, Any]) -> str:
    from trader1.research.profitability.candidate_scorecard import stable_json_hash

    return stable_json_hash({key: value for key, value in report.items() if key != "rehydration_hash"})


def validate_paper_candidate_rehydration_report(report: dict[str, Any]) -> tuple[str, str, str | None]:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "generation_status",
        "replay_status",
        "runtime_linkage_status",
        "candidate_id",
        "source_runtime_cycle_id",
        "source_runtime_cycle_hash",
        "generation_hash_checked",
        "replay_hash_checked",
        "runtime_hash_checked",
        "blocker_code",
        "rehydration_status",
        "paper_scope_focus",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "rehydration_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return "FAIL", f"paper candidate rehydration report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("schema_id") != PAPER_CANDIDATE_REHYDRATION_SCHEMA_ID:
        return "FAIL", "paper candidate rehydration schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return "BLOCKED", "paper candidate rehydration is scoped to UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
    if any(report.get(flag) is True for flag in LIVE_AND_PRIVATE_FLAGS):
        return "BLOCKED", "paper candidate rehydration attempted private, order, live, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED"
    if report.get("rehydration_hash") != _rehydration_hash(report):
        return "FAIL", "paper candidate rehydration hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
    if report.get("rehydration_status") == "PASS":
        if report.get("generation_status") != VALIDATED_GENERATION_STATUS:
            return "FAIL", "PASS rehydration requires validated generation status", "SCHEMA_IDENTITY_MISMATCH"
        if report.get("replay_status") != "PASS" or report.get("runtime_linkage_status") != "PASS":
            return "FAIL", "PASS rehydration requires replay and runtime linkage PASS", "SCHEMA_IDENTITY_MISMATCH"
        if not all(report.get(field) is True for field in ("generation_hash_checked", "replay_hash_checked", "runtime_hash_checked")):
            return "FAIL", "PASS rehydration requires all hash checks", "SCHEMA_IDENTITY_MISMATCH"
        focus = report.get("paper_scope_focus")
        if not isinstance(focus, dict) or not focus.get("candidate_id") or int(focus.get("sample_deficit") or 0) <= 0:
            return "FAIL", "PASS rehydration requires actionable PAPER scope focus", "SCHEMA_IDENTITY_MISMATCH"
        if any(focus.get(flag) is True for flag in LIVE_FALSE_FLAGS):
            return "BLOCKED", "paper scope focus attempted live or scale-up behavior", "LIVE_FINAL_GUARD_FAILED"
    elif report.get("rehydration_status") != "BLOCKED":
        return "FAIL", "paper candidate rehydration status must be PASS or BLOCKED", "SCHEMA_IDENTITY_MISMATCH"
    return "PASS", "paper candidate rehydration report is scoped, hash-bound, and fail-closed", None


class CandidateGenerationPaperIntentProvider:
    def __init__(
        self,
        *,
        max_runtime_linkage_age_seconds: int = DEFAULT_RUNTIME_LINKAGE_MAX_AGE_SECONDS,
    ) -> None:
        self.max_runtime_linkage_age_seconds = int(max_runtime_linkage_age_seconds)

    def provide(
        self,
        *,
        root: Path,
        session_id: str = DEFAULT_UPBIT_PAPER_SESSION_ID,
        current_paper_portfolio_snapshot: dict[str, Any] | None = None,
        current_runtime_cycle_report: dict[str, Any] | None = None,
    ) -> PaperTradeIntentInputs | None:
        root = Path(root).resolve()
        generation_path = candidate_generation_report_path(root, session_id)
        generation_report = _read_json(generation_path)
        current_runtime = current_runtime_cycle_report or _read_json(
            _paper_base(root, session_id) / "upbit_paper_runtime_cycle_report.json"
        )
        current_portfolio = (
            current_paper_portfolio_snapshot
            if isinstance(current_paper_portfolio_snapshot, dict)
            else current_runtime.get("paper_portfolio_snapshot")
            if isinstance(current_runtime, dict)
            else None
        )

        report = self._build_blocked_report(
            root=root,
            session_id=session_id,
            generation_report=generation_report,
            generation_path=generation_path,
            replay_report=None,
            runtime_cycle=None,
            runtime_cycle_path=None,
            candidate_item=None,
            blocker_code="CANDIDATE_GENERATION_REPORT_MISSING",
            blocker_message="latest candidate_generation_report.json is missing or unreadable",
        )
        if not isinstance(generation_report, dict):
            self._write_report(root=root, session_id=session_id, report=report)
            return None

        generation_status = str(generation_report.get("generation_status") or "")
        if generation_status != VALIDATED_GENERATION_STATUS:
            report = self._build_blocked_report(
                root=root,
                session_id=session_id,
                generation_report=generation_report,
                generation_path=generation_path,
                replay_report=None,
                runtime_cycle=None,
                runtime_cycle_path=None,
                candidate_item=None,
                blocker_code="CANDIDATE_GENERATION_NOT_PUBLIC_REPLAY_VALIDATED",
                blocker_message="candidate generation must be ALTERNATIVE_PUBLIC_REPLAY_VALIDATED before PAPER intent rehydration",
            )
            self._write_report(root=root, session_id=session_id, report=report)
            return None

        validation_status, validation_message, validation_blocker = validate_candidate_generation_report(generation_report)
        if validation_status != "PASS":
            report = self._build_blocked_report(
                root=root,
                session_id=session_id,
                generation_report=generation_report,
                generation_path=generation_path,
                replay_report=None,
                runtime_cycle=None,
                runtime_cycle_path=None,
                candidate_item=None,
                blocker_code=validation_blocker or "CANDIDATE_GENERATION_CONTRACT_FAILED",
                blocker_message=validation_message,
            )
            self._write_report(root=root, session_id=session_id, report=report)
            return None

        generation_hash = str(generation_report.get("generation_hash") or "").upper()
        generation_hash_checked = generation_hash == candidate_generation_report_hash(generation_report).upper()
        candidate_id = str(generation_report.get("best_alternative_candidate_id") or "")
        candidate_item = _candidate_item(generation_report, candidate_id)
        replay_report = load_public_replay_robustness_report(root=root, session_id=session_id, candidate_id=candidate_id)
        source_runtime_cycle_id = str(candidate_item.get("source_runtime_cycle_id") or "") if isinstance(candidate_item, dict) else ""
        source_runtime_cycle_hash = (
            str(candidate_item.get("source_runtime_cycle_hash") or "").upper()
            if isinstance(candidate_item, dict)
            else ""
        )
        runtime_cycle, runtime_path, runtime_load_status = _load_bound_runtime_cycle(
            root=root,
            session_id=session_id,
            source_runtime_cycle_id=source_runtime_cycle_id,
            source_runtime_cycle_hash=source_runtime_cycle_hash,
        )

        blocker_code = None
        blocker_message = ""
        if _has_live_or_private_drift(generation_report, replay_report, runtime_cycle, current_runtime):
            blocker_code = "LIVE_FINAL_GUARD_FAILED"
            blocker_message = "candidate rehydration refused live/private/order flag drift"
        elif not generation_hash_checked:
            blocker_code = "CANDIDATE_GENERATION_HASH_MISMATCH"
            blocker_message = "candidate generation hash does not match canonical payload"
        elif not isinstance(candidate_item, dict) or candidate_item.get("candidate_status") != "REVIEW_READY":
            blocker_code = "BEST_ALTERNATIVE_CANDIDATE_MISSING"
            blocker_message = "validated generation report does not contain a review-ready best alternative candidate row"
        elif not _hash_is_64_hex(source_runtime_cycle_hash) or not source_runtime_cycle_id:
            blocker_code = "SOURCE_RUNTIME_LINKAGE_MISSING"
            blocker_message = "best alternative candidate row is missing source runtime cycle id/hash"
        elif _runtime_source_evidence_id(source_runtime_cycle_id, source_runtime_cycle_hash) not in set(
            str(item) for item in generation_report.get("source_evidence_ids") or []
        ):
            blocker_code = "SOURCE_RUNTIME_LINKAGE_MISSING"
            blocker_message = "generation report does not bind the best alternative source runtime cycle"
        elif runtime_load_status == "MISSING":
            blocker_code = "SOURCE_RUNTIME_CYCLE_MISSING"
            blocker_message = "source runtime cycle artifact is missing"
        elif runtime_load_status != "PASS":
            blocker_code = "SOURCE_RUNTIME_HASH_MISMATCH" if runtime_load_status == "HASH_MISMATCH" else runtime_load_status
            blocker_message = "source runtime cycle artifact failed hash or contract validation"
        elif not isinstance(replay_report, dict):
            blocker_code = "PUBLIC_REPLAY_REPORT_MISSING"
            blocker_message = "best alternative public replay robustness report is missing"
        else:
            replay_result = validate_public_replay_robustness_report(replay_report)
            replay_hash = str(replay_report.get("report_hash") or "").upper()
            replay_hash_checked = replay_hash == public_replay_robustness_report_hash(replay_report).upper()
            replay_evidence_bound = _replay_source_evidence_id(str(replay_report.get("replay_id") or ""), replay_hash) in set(
                str(item) for item in generation_report.get("source_evidence_ids") or []
            )
            if replay_result.status != "PASS":
                blocker_code = replay_result.blocker_code or "PUBLIC_REPLAY_CONTRACT_NOT_PASS"
                blocker_message = replay_result.message
            elif not replay_hash_checked:
                blocker_code = "PUBLIC_REPLAY_HASH_MISMATCH"
                blocker_message = "public replay report hash does not match canonical payload"
            elif replay_hash != str(generation_report.get("best_alternative_public_replay_report_hash") or "").upper():
                blocker_code = "PUBLIC_REPLAY_HASH_MISMATCH"
                blocker_message = "generation report best alternative replay hash does not match replay artifact"
            elif not replay_evidence_bound:
                blocker_code = "PUBLIC_REPLAY_SOURCE_BINDING_MISSING"
                blocker_message = "generation report does not bind the public replay robustness evidence id"
            elif replay_report.get("replay_status") != "PASS":
                blocker_code = str(replay_report.get("primary_blocker_code") or "PUBLIC_REPLAY_ROBUSTNESS_FAILED")
                blocker_message = "public replay robustness has not passed"
            elif str(replay_report.get("candidate_id") or "") != candidate_id:
                blocker_code = "SNAPSHOT_SCOPE_MISMATCH"
                blocker_message = "public replay candidate id does not match best alternative candidate"
            elif _current_open_position_count(current_portfolio) > 0:
                blocker_code = "OPEN_POSITION_BLOCKS_REHYDRATION"
                blocker_message = "PAPER candidate switch is blocked while an open simulated position exists"
            elif _pending_confirm_detected(current_runtime, current_portfolio):
                blocker_code = "PENDING_CONFIRM_BLOCKS_REHYDRATION"
                blocker_message = "PAPER candidate switch is blocked while pending confirmation/open-order state exists"
            elif _duplicate_replay_candle_detected(replay_report):
                blocker_code = "DUPLICATE_CANDLE_BLOCKS_REHYDRATION"
                blocker_message = "public replay sample rows contain duplicate runtime candle timestamps"
            elif self._runtime_linkage_is_stale(generation_report):
                blocker_code = "SOURCE_RUNTIME_LINKAGE_STALE"
                blocker_message = "candidate generation runtime linkage is stale for PAPER intent rehydration"
            else:
                sample_count, sample_deficit, scope_status = _candidate_scope_progress(
                    root=root,
                    session_id=session_id,
                    candidate_id=candidate_id,
                    strategy_id=str(replay_report.get("strategy_id") or candidate_item.get("strategy_id") or ""),
                    parameter_hash=str(replay_report.get("parameter_hash") or "").upper(),
                )
                if sample_deficit <= 0:
                    blocker_code = "PAPER_SCOPE_SAMPLE_FLOOR_MET"
                    blocker_message = "candidate already meets PAPER scope sample floor; keep long-run evidence gated separately"
                else:
                    mutation_spec = load_validated_mutation_spec_for_candidate(
                        root=root,
                        session_id=session_id,
                        candidate_id=candidate_id,
                    )
                    focus = {
                        "source": (
                            "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION_WITH_MUTATION"
                            if mutation_spec
                            else "CANDIDATE_GENERATION_PUBLIC_REPLAY_REHYDRATION"
                        ),
                        "candidate_id": candidate_id,
                        "symbol": str(replay_report.get("symbol") or candidate_item.get("symbol") or ""),
                        "strategy_id": str(replay_report.get("strategy_id") or candidate_item.get("strategy_id") or ""),
                        "strategy_build_id": str(replay_report.get("strategy_build_id") or ""),
                        "parameter_hash": str(
                            (mutation_spec or {}).get("parameter_hash") or replay_report.get("parameter_hash") or ""
                        ).upper(),
                        "sample_count": sample_count,
                        "sample_deficit": sample_deficit,
                        "scope_progress_status": scope_status,
                        "generation_report_id": generation_report.get("generation_report_id"),
                        "generation_hash": generation_hash,
                        "replay_id": replay_report.get("replay_id"),
                        "replay_hash": replay_hash,
                        "source_runtime_cycle_id": source_runtime_cycle_id,
                        "source_runtime_cycle_hash": source_runtime_cycle_hash,
                        "candidate_source_role": candidate_item.get("candidate_source_role"),
                        "live_order_ready": False,
                        "live_order_allowed": False,
                        "can_live_trade": False,
                        "scale_up_allowed": False,
                    }
                    if mutation_spec:
                        focus["mutated_paper_candidate_spec"] = mutation_spec
                        focus["mutation_id"] = mutation_spec.get("mutation_id")
                        focus["parent_parameter_hash"] = mutation_spec.get("parent_parameter_hash")
                    report = self._build_pass_report(
                        root=root,
                        session_id=session_id,
                        generation_report=generation_report,
                        generation_path=generation_path,
                        replay_report=replay_report,
                        runtime_cycle=runtime_cycle,
                        runtime_cycle_path=runtime_path,
                        candidate_item=candidate_item,
                        paper_scope_focus=focus,
                        generation_hash_checked=True,
                        replay_hash_checked=True,
                        runtime_hash_checked=True,
                    )
                    self._write_report(root=root, session_id=session_id, report=report)
                    return PaperTradeIntentInputs(
                        paper_scope_focus=focus,
                        paper_candidate_rehydration_report=report,
                        candidate_item=dict(candidate_item),
                    )

        report = self._build_blocked_report(
            root=root,
            session_id=session_id,
            generation_report=generation_report,
            generation_path=generation_path,
            replay_report=replay_report,
            runtime_cycle=runtime_cycle,
            runtime_cycle_path=runtime_path,
            candidate_item=candidate_item,
            blocker_code=blocker_code or "REHYDRATION_BLOCKED",
            blocker_message=blocker_message,
        )
        self._write_report(root=root, session_id=session_id, report=report)
        return None

    def _runtime_linkage_is_stale(self, generation_report: dict[str, Any]) -> bool:
        generated_at = _parse_utc(generation_report.get("generated_at_utc"))
        if generated_at is None:
            return True
        age_seconds = (datetime.now(timezone.utc) - generated_at).total_seconds()
        return age_seconds > self.max_runtime_linkage_age_seconds

    def _base_report(
        self,
        *,
        root: Path,
        session_id: str,
        generation_report: dict[str, Any] | None,
        generation_path: Path,
        replay_report: dict[str, Any] | None,
        runtime_cycle: dict[str, Any] | None,
        runtime_cycle_path: Path | None,
        candidate_item: dict[str, Any] | None,
    ) -> dict[str, Any]:
        candidate_id = str(
            (generation_report or {}).get("best_alternative_candidate_id")
            or (candidate_item or {}).get("candidate_id")
            or ""
        )
        source_runtime_cycle_id = str((candidate_item or {}).get("source_runtime_cycle_id") or "")
        source_runtime_cycle_hash = str((candidate_item or {}).get("source_runtime_cycle_hash") or "").upper()
        generation_hash = str((generation_report or {}).get("generation_hash") or "").upper()
        replay_hash = str((replay_report or {}).get("report_hash") or "").upper()
        runtime_hash = str((runtime_cycle or {}).get("cycle_hash") or "").upper()
        generation_hash_checked = (
            isinstance(generation_report, dict)
            and generation_hash
            and generation_hash == candidate_generation_report_hash(generation_report).upper()
        )
        replay_hash_checked = (
            isinstance(replay_report, dict)
            and replay_hash
            and replay_hash == public_replay_robustness_report_hash(replay_report).upper()
        )
        runtime_hash_checked = (
            isinstance(runtime_cycle, dict)
            and runtime_hash
            and runtime_hash == source_runtime_cycle_hash
            and upbit_paper_runtime_cycle_hash(runtime_cycle).upper() == source_runtime_cycle_hash
        )
        return {
            "schema_id": PAPER_CANDIDATE_REHYDRATION_SCHEMA_ID,
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": session_id,
            "generation_report_path": _relative_posix(generation_path, root),
            "replay_report_path": (
                _relative_posix(
                    _paper_base(root, session_id)
                    / "profitability"
                    / "replay_robustness"
                    / f"{safe_candidate_scorecard_filename(candidate_id)}.public_replay_robustness_report.json",
                    root,
                )
                if candidate_id
                else None
            ),
            "runtime_cycle_path": _relative_posix(runtime_cycle_path, root) if runtime_cycle_path else None,
            "generation_status": str((generation_report or {}).get("generation_status") or "MISSING"),
            "replay_status": str((replay_report or {}).get("replay_status") or "MISSING"),
            "runtime_linkage_status": "PASS" if runtime_hash_checked else "BLOCKED",
            "candidate_id": candidate_id or None,
            "source_runtime_cycle_id": source_runtime_cycle_id or None,
            "source_runtime_cycle_hash": source_runtime_cycle_hash or None,
            "generation_hash": generation_hash or None,
            "replay_hash": replay_hash or None,
            "runtime_hash": runtime_hash or None,
            "generation_hash_checked": bool(generation_hash_checked),
            "replay_hash_checked": bool(replay_hash_checked),
            "runtime_hash_checked": bool(runtime_hash_checked),
            "paper_scope_focus": None,
            "credential_load_attempted": False,
            "private_endpoint_called": False,
            "order_endpoint_called": False,
            "order_adapter_called": False,
            "live_key_loaded": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }

    def _build_blocked_report(
        self,
        *,
        root: Path,
        session_id: str,
        generation_report: dict[str, Any] | None,
        generation_path: Path,
        replay_report: dict[str, Any] | None,
        runtime_cycle: dict[str, Any] | None,
        runtime_cycle_path: Path | None,
        candidate_item: dict[str, Any] | None,
        blocker_code: str,
        blocker_message: str,
    ) -> dict[str, Any]:
        report = self._base_report(
            root=root,
            session_id=session_id,
            generation_report=generation_report,
            generation_path=generation_path,
            replay_report=replay_report,
            runtime_cycle=runtime_cycle,
            runtime_cycle_path=runtime_cycle_path,
            candidate_item=candidate_item,
        )
        report.update(
            {
                "blocker_code": blocker_code,
                "blocker_message": blocker_message,
                "rehydration_status": "BLOCKED",
                "next_action": "Keep PAPER live-blocked; do not inject a candidate until generation, replay, and runtime linkage all pass.",
            }
        )
        report["rehydration_hash"] = _rehydration_hash(report)
        return report

    def _build_pass_report(
        self,
        *,
        root: Path,
        session_id: str,
        generation_report: dict[str, Any],
        generation_path: Path,
        replay_report: dict[str, Any],
        runtime_cycle: dict[str, Any],
        runtime_cycle_path: Path | None,
        candidate_item: dict[str, Any],
        paper_scope_focus: dict[str, Any],
        generation_hash_checked: bool,
        replay_hash_checked: bool,
        runtime_hash_checked: bool,
    ) -> dict[str, Any]:
        report = self._base_report(
            root=root,
            session_id=session_id,
            generation_report=generation_report,
            generation_path=generation_path,
            replay_report=replay_report,
            runtime_cycle=runtime_cycle,
            runtime_cycle_path=runtime_cycle_path,
            candidate_item=candidate_item,
        )
        report.update(
            {
                "runtime_linkage_status": "PASS",
                "generation_hash_checked": generation_hash_checked,
                "replay_hash_checked": replay_hash_checked,
                "runtime_hash_checked": runtime_hash_checked,
                "blocker_code": None,
                "blocker_message": None,
                "rehydration_status": "PASS",
                "paper_scope_focus": paper_scope_focus,
                "next_action": "Inject this validated non-live PAPER candidate into the next bounded PAPER cycle as paper_scope_focus.",
            }
        )
        report["rehydration_hash"] = _rehydration_hash(report)
        return report

    def _write_report(self, *, root: Path, session_id: str, report: dict[str, Any]) -> Path:
        status, message, blocker_code = validate_paper_candidate_rehydration_report(report)
        if status != "PASS":
            raise ValueError(f"paper candidate rehydration report failed validation: {blocker_code or status}: {message}")
        path = paper_candidate_rehydration_report_path(root, session_id)
        durable_atomic_write_json(path, report)
        return path


def default_candidate_generation_paper_intent_provider(
    *,
    root: Path,
    session_id: str = DEFAULT_UPBIT_PAPER_SESSION_ID,
    current_paper_portfolio_snapshot: dict[str, Any] | None = None,
    current_runtime_cycle_report: dict[str, Any] | None = None,
) -> PaperTradeIntentInputs | None:
    provider = CandidateGenerationPaperIntentProvider()
    return provider.provide(
        root=root,
        session_id=session_id,
        current_paper_portfolio_snapshot=current_paper_portfolio_snapshot,
        current_runtime_cycle_report=current_runtime_cycle_report,
    )
