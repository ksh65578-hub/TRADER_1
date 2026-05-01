from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.dashboard.summary_writer import build_summary_shell
from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash
from trader1.runtime.paper.upbit_paper_missing_cycle_rerun_guard import (
    MISSING_CYCLE_LEDGER_RERUN_REQUIRED_BLOCKER_CODE,
    RECOVERY_GUARD_RERUN_REQUIRED_BLOCKER_CODE,
    validate_upbit_paper_missing_cycle_rerun_guard_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    _build_strategy_regime_cost_linkage,
    _feature_snapshot,
    _hash_payload,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json, durable_atomic_write_jsonl, public_market_data_hash


UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR_SCHEMA_ID = (
    "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1"
)
BOUNDED_RERUN_STAGING_EXECUTOR_ROLE = (
    "PAPER_RUNTIME_BOUNDED_RERUN_STAGING_EXECUTOR_STAGING_ONLY_NOT_CURRENT_EVIDENCE"
)
RERUN_STAGING_WRITER_ROLE = "PAPER_RUNTIME_RERUN_STAGING_WRITER_NOT_CURRENT_EVIDENCE"
POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE = "POST_RERUN_LEDGER_ROLLUP_REQUIRED"
POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE = "POST_RERUN_RECONCILIATION_REQUIRED"
RERUN_STAGING_ARTIFACT_MISMATCH_BLOCKER_CODE = "RERUN_STAGING_ARTIFACT_MISMATCH_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class UpbitPaperBoundedRerunStagingExecutorValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))


def upbit_paper_bounded_rerun_staging_executor_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("executor_hash", None)
    return _sha256_json(payload)


def _writer_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("writer_report_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return path.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "live" not in parts


def _staging_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates/" in normalized


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "MISSING"
    except UnicodeDecodeError:
        return None, "INVALID_UTF8"
    except json.JSONDecodeError:
        return None, "INVALID_JSON"
    if not isinstance(value, dict):
        return None, "NOT_OBJECT"
    return value, None


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None, "MISSING"
    except UnicodeDecodeError:
        return None, "INVALID_UTF8"
    records: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            return None, "INVALID_JSON"
        if not isinstance(value, dict):
            return None, "NOT_OBJECT"
        records.append(value)
    return records, None


def _cycle_source_path_from_replacement(replacement: dict[str, Any], cycle_id: str) -> str:
    for cycle_result in replacement.get("cycle_results", []):
        if not isinstance(cycle_result, dict) or cycle_result.get("cycle_id") != cycle_id:
            continue
        for path in cycle_result.get("artifact_paths") or []:
            path_text = str(path)
            if path_text.endswith(f"/{cycle_id}.runtime_cycle.json") or path_text.endswith(f"\\{cycle_id}.runtime_cycle.json"):
                return path_text.replace("\\", "/")
    return ""


def _planned_paths_by_cycle(guard_item: dict[str, Any], cycle_id: str) -> dict[str, str]:
    paths = [str(path).replace("\\", "/") for path in guard_item.get("planned_staging_artifact_paths") or []]
    return {
        "runtime_cycle": next((path for path in paths if path.endswith(f"/{cycle_id}.runtime_cycle.json")), ""),
        "ledger_jsonl": next((path for path in paths if path.endswith(f"/{cycle_id}.paper_ledger_events.jsonl")), ""),
        "writer_report": next((path for path in paths if path.endswith(f"/{cycle_id}.writer_report.json")), ""),
    }


def _build_writer_report(
    *,
    cycle: dict[str, Any],
    source_runtime_cycle_path: str,
    source_runtime_cycle_hash: str | None,
    staged_runtime_cycle_hash: str | None,
    staged_runtime_cycle_path: str,
    staged_ledger_jsonl_path: str,
    staged_writer_report_path: str,
    ledger_event_count: int,
) -> dict[str, Any]:
    writer = {
        "writer_report_role": RERUN_STAGING_WRITER_ROLE,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "writer_status": "PASS",
        "cycle_id": cycle.get("cycle_id"),
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": cycle.get("session_id"),
        "source_runtime_cycle_path": source_runtime_cycle_path,
        "source_runtime_cycle_hash": source_runtime_cycle_hash,
        "staged_runtime_cycle_hash": staged_runtime_cycle_hash,
        "staged_runtime_cycle_path": staged_runtime_cycle_path,
        "staged_ledger_jsonl_path": staged_ledger_jsonl_path,
        "staged_writer_report_path": staged_writer_report_path,
        "staged_ledger_event_count": ledger_event_count,
        "staged_artifact_is_current_evidence": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_rerun_executed": False,
        "actual_long_run_evidence_created": False,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "writer_report_hash": "",
    }
    writer["writer_report_hash"] = _writer_hash(writer)
    return writer


def _normalize_runtime_cycle_for_staging(cycle: dict[str, Any]) -> tuple[dict[str, Any], str, UpbitPaperRuntimeCycleValidationResult]:
    source_result = validate_upbit_paper_runtime_cycle_report(cycle)
    if source_result.status == "PASS":
        return cycle, "NOT_REQUIRED", source_result
    if source_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return cycle, "BLOCKED", source_result
    market_data = cycle.get("public_market_data")
    portfolio = cycle.get("paper_portfolio_snapshot")
    selected = cycle.get("selected_candidate")
    if not isinstance(market_data, dict) or not isinstance(portfolio, dict) or not isinstance(selected, dict):
        return cycle, "BLOCKED", source_result
    try:
        expected_features = _feature_snapshot(market_data)
        if cycle.get("feature_snapshot") != expected_features:
            return cycle, "BLOCKED", source_result
        runtime_market_hash = public_market_data_hash(market_data)
        feature_hash = _hash_payload(expected_features)
        normalized = json.loads(json.dumps(cycle))
        normalized["runtime_public_market_data_hash"] = runtime_market_hash
        normalized["source_public_market_data_hash"] = (
            runtime_market_hash if normalized.get("runtime_input_role") == "PUBLIC_MARKET_DATA_COLLECTION" else None
        )
        normalized["feature_snapshot_hash"] = feature_hash
        for candidate in normalized.get("strategy_candidates") or []:
            if isinstance(candidate, dict) and (
                "cost_breakdown_bps" not in candidate or "cost_model_source" not in candidate
            ):
                candidate["cost_breakdown_bps"] = {
                    "fee_bps": "5",
                    "slippage_bps": "5",
                    "spread_bps": str(expected_features.get("spread_bps", "1")),
                    "market_impact_bps": "0",
                    "latency_bps": "0",
                }
                candidate["cost_model_source"] = "PAPER_RUNTIME_STATIC_COST_MODEL"
        selected_id = normalized.get("selected_candidate", {}).get("candidate_id")
        normalized["selected_candidate"] = next(
            (
                dict(candidate)
                for candidate in normalized.get("strategy_candidates") or []
                if isinstance(candidate, dict) and candidate.get("candidate_id") == selected_id
            ),
            normalized["selected_candidate"],
        )
        normalized["strategy_regime_cost_linkage"] = _build_strategy_regime_cost_linkage(
            cycle_id=str(normalized.get("cycle_id")),
            runtime_input_role=str(normalized.get("runtime_input_role")),
            runtime_public_market_data_hash=runtime_market_hash,
            feature_snapshot_hash=feature_hash,
            selected_candidate=normalized["selected_candidate"],
            regime=str(normalized.get("regime")),
        )
        normalized_portfolio = normalized["paper_portfolio_snapshot"]
        normalized_portfolio["source_runtime_cycle_id"] = normalized.get("cycle_id")
        normalized_portfolio["source_paper_ledger_head_hash"] = normalized.get("paper_ledger_head_hash")
        normalized_portfolio["snapshot_hash"] = paper_portfolio_hash(normalized_portfolio)
        normalized["summary"] = build_summary_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=str(normalized.get("session_id")),
            startup_probe={
                "startup_probe_passed": True,
                "primary_blocker_code": None,
                "next_action": "continue PAPER runtime evidence collection",
            },
            heartbeat={
                "heartbeat_status": "PASS",
                "primary_blocker_code": None,
                "next_action": "PAPER runtime cycle completed safely",
            },
            readiness_surface={
                "primary_blocker_code": "LIVE_READY_MISSING",
                "primary_blocker_message": "LIVE remains blocked; PAPER runtime evidence is not live readiness.",
            },
            paper_portfolio_snapshot=normalized_portfolio,
            entry_candidates=normalized.get("strategy_candidates") or [],
            recent_entry_context=normalized.get("entry_reasons") or [],
            recent_no_trade_context=[
                {"reason_code": str(reason), "message": "PAPER runtime did not enter"}
                for reason in (normalized.get("no_trade_reasons") or [])
            ],
            market_context={
                "source": "MARKET_DATA",
                "freshness_status": "PASS",
                "regime": expected_features.get("regime"),
                "liquidity_status": expected_features.get("liquidity_status"),
                "volatility_status": expected_features.get("volatility_status"),
            },
        )
        normalized["summary"]["generated_at_utc"] = str(
            cycle.get("summary", {}).get("generated_at_utc")
            if isinstance(cycle.get("summary"), dict)
            else normalized.get("generated_at_utc")
        )
        if normalized["summary"].get("portfolio", {}).get("source") in {"LEDGER", "RECONCILIATION"}:
            normalized["summary"]["portfolio"]["source_snapshot_age_seconds"] = 0
        normalized["cycle_hash"] = upbit_paper_runtime_cycle_hash(normalized)
    except Exception:
        return cycle, "BLOCKED", source_result
    normalized_result = validate_upbit_paper_runtime_cycle_report(normalized)
    if normalized_result.status != "PASS":
        return cycle, "BLOCKED", normalized_result
    return normalized, "APPLIED_STAGING_ONLY", normalized_result


def _existing_runtime_cycle_matches(path: Path, expected_cycle_hash: str | None) -> bool:
    existing, error = _safe_load_json(path)
    if error or existing is None:
        return False
    return existing.get("cycle_hash") == expected_cycle_hash and upbit_paper_runtime_cycle_hash(existing) == expected_cycle_hash


def _existing_ledger_matches(path: Path, expected_events: list[dict[str, Any]]) -> bool:
    records, error = _safe_read_jsonl(path)
    return error is None and records == expected_events


def _existing_writer_matches(path: Path, *, cycle_id: str, source_cycle_hash: str | None, staged_cycle_hash: str | None) -> bool:
    writer, error = _safe_load_json(path)
    if error or writer is None:
        return False
    return (
        writer.get("writer_report_role") == RERUN_STAGING_WRITER_ROLE
        and writer.get("writer_status") == "PASS"
        and writer.get("cycle_id") == cycle_id
        and writer.get("source_runtime_cycle_hash") == source_cycle_hash
        and writer.get("staged_runtime_cycle_hash") == staged_cycle_hash
        and not writer.get("staged_artifact_is_current_evidence")
        and not writer.get("live_order_allowed")
        and not writer.get("scale_up_allowed")
    )


def _write_or_reuse_json(path: Path, payload: dict[str, Any], *, expected_hash: str | None) -> tuple[str, bool, bool]:
    existed = path.exists()
    if existed:
        if _existing_runtime_cycle_matches(path, expected_hash):
            return "REUSED_EXISTING_MATCH", False, True
        return "BLOCKED_EXISTING_MISMATCH", False, False
    durable_atomic_write_json(path, payload)
    return "WRITTEN", True, False


def _write_or_reuse_jsonl(path: Path, records: list[dict[str, Any]]) -> tuple[str, bool, bool]:
    existed = path.exists()
    if existed:
        if _existing_ledger_matches(path, records):
            return "REUSED_EXISTING_MATCH", False, True
        return "BLOCKED_EXISTING_MISMATCH", False, False
    durable_atomic_write_jsonl(path, records)
    return "WRITTEN", True, False


def _write_or_reuse_writer(
    path: Path,
    writer: dict[str, Any],
    *,
    cycle_id: str,
    source_cycle_hash: str | None,
    staged_cycle_hash: str | None,
) -> tuple[str, bool, bool]:
    existed = path.exists()
    if existed:
        if not _existing_writer_matches(
            path,
            cycle_id=cycle_id,
            source_cycle_hash=source_cycle_hash,
            staged_cycle_hash=staged_cycle_hash,
        ):
            return "BLOCKED_EXISTING_MISMATCH", False, False
        return (
            "REUSED_EXISTING_MATCH",
            False,
            True,
        )
    durable_atomic_write_json(path, writer)
    return "WRITTEN", True, False


def _build_staging_item(*, root: Path, session_id: str, guard_item: dict[str, Any], cycle_id: str) -> dict[str, Any]:
    replacement_path = str(guard_item.get("replacement_path") or "")
    replacement, replacement_error = _safe_load_json(_rooted(root, replacement_path))
    source_cycle_path = _cycle_source_path_from_replacement(replacement or {}, cycle_id)
    planned = _planned_paths_by_cycle(guard_item, cycle_id)
    cycle, cycle_error = _safe_load_json(_rooted(root, source_cycle_path))
    source_runtime_result = validate_upbit_paper_runtime_cycle_report(cycle or {})
    staged_cycle, runtime_cycle_normalization_status, runtime_result = (
        _normalize_runtime_cycle_for_staging(cycle) if isinstance(cycle, dict) else ({}, "BLOCKED", source_runtime_result)
    )
    cycle_hash_expected = next(
        (
            str(item.get("runtime_cycle_hash"))
            for item in (replacement or {}).get("cycle_results", [])
            if isinstance(item, dict) and item.get("cycle_id") == cycle_id and item.get("runtime_cycle_hash")
        ),
        None,
    )
    cycle_hash_actual = cycle.get("cycle_hash") if isinstance(cycle, dict) else None
    staged_cycle_hash_actual = staged_cycle.get("cycle_hash") if isinstance(staged_cycle, dict) else None
    ledger_events = staged_cycle.get("paper_ledger_events") if isinstance(staged_cycle, dict) else None
    ledger_events_valid = isinstance(ledger_events, list) and all(isinstance(event, dict) for event in ledger_events)
    if ledger_events_valid and ledger_events:
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(ledger_events)
    elif ledger_events_valid and staged_cycle.get("final_decision") != "ENTER_LONG":
        ledger_status, ledger_blocker, ledger_message = (
            "PASS",
            None,
            "no-trade PAPER cycle has no ledger events; empty staging JSONL preserves cycle completeness",
        )
    else:
        ledger_status, ledger_blocker, ledger_message = ("BLOCKED", "MEASUREMENT_MISSING", "missing PAPER ledger events")
    path_scope_match = all(_staging_path_allowed(path, session_id) for path in planned.values()) and _artifact_path_allowed(source_cycle_path, session_id)
    blocker_code = None
    if replacement_error:
        blocker_code = str(replacement_error)
    elif not source_cycle_path or cycle_error:
        blocker_code = str(cycle_error or "SOURCE_RUNTIME_CYCLE_PATH_MISSING")
    elif runtime_result.status != "PASS":
        blocker_code = runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH"
    elif cycle_hash_expected and cycle_hash_actual != cycle_hash_expected:
        blocker_code = "SOURCE_RUNTIME_CYCLE_HASH_MISMATCH"
    elif ledger_status != "PASS":
        blocker_code = ledger_blocker or "LEDGER_INTEGRITY_FAIL"
    elif not path_scope_match:
        blocker_code = "SNAPSHOT_SCOPE_MISMATCH"

    runtime_status = "NOT_WRITTEN"
    ledger_write_status = "NOT_WRITTEN"
    writer_status = "NOT_WRITTEN"
    runtime_written = ledger_written = writer_written = False
    runtime_reused = ledger_reused = writer_reused = False
    if blocker_code is None and isinstance(staged_cycle, dict) and isinstance(ledger_events, list):
        runtime_path = _rooted(root, planned["runtime_cycle"])
        ledger_path = _rooted(root, planned["ledger_jsonl"])
        writer_path = _rooted(root, planned["writer_report"])
        writer = _build_writer_report(
            cycle=staged_cycle,
            source_runtime_cycle_path=source_cycle_path,
            source_runtime_cycle_hash=cycle_hash_actual,
            staged_runtime_cycle_hash=staged_cycle_hash_actual,
            staged_runtime_cycle_path=planned["runtime_cycle"],
            staged_ledger_jsonl_path=planned["ledger_jsonl"],
            staged_writer_report_path=planned["writer_report"],
            ledger_event_count=len(ledger_events),
        )
        runtime_status, runtime_written, runtime_reused = _write_or_reuse_json(runtime_path, staged_cycle, expected_hash=staged_cycle_hash_actual)
        ledger_write_status, ledger_written, ledger_reused = _write_or_reuse_jsonl(ledger_path, ledger_events)
        writer_status, writer_written, writer_reused = _write_or_reuse_writer(
            writer_path,
            writer,
            cycle_id=cycle_id,
            source_cycle_hash=cycle_hash_actual,
            staged_cycle_hash=staged_cycle_hash_actual,
        )
        if any(status == "BLOCKED_EXISTING_MISMATCH" for status in (runtime_status, ledger_write_status, writer_status)):
            blocker_code = RERUN_STAGING_ARTIFACT_MISMATCH_BLOCKER_CODE

    staging_written_count = sum(1 for value in (runtime_written, ledger_written, writer_written) if value)
    staging_reused_count = sum(1 for value in (runtime_reused, ledger_reused, writer_reused) if value)
    staging_status = "STAGED" if blocker_code is None and staging_written_count else "REUSED_EXISTING" if blocker_code is None else "BLOCKED"
    return {
        "source_guard_priority_order": int(guard_item.get("source_queue_priority_order") or 0),
        "replacement_loop_id": str(guard_item.get("replacement_loop_id") or ""),
        "replacement_path": replacement_path,
        "replacement_load_status": "PASS" if replacement is not None else str(replacement_error or "UNKNOWN"),
        "cycle_id": cycle_id,
        "source_runtime_cycle_path": source_cycle_path,
        "source_runtime_cycle_load_status": "PASS" if cycle is not None else str(cycle_error or "UNKNOWN"),
        "source_runtime_cycle_hash_expected": cycle_hash_expected,
        "source_runtime_cycle_hash_actual": cycle_hash_actual,
        "source_runtime_cycle_hash_match": bool(cycle_hash_expected and cycle_hash_expected == cycle_hash_actual),
        "source_runtime_cycle_validator_status": source_runtime_result.status,
        "source_runtime_cycle_validator_blocker_code": source_runtime_result.blocker_code,
        "runtime_cycle_normalization_status": runtime_cycle_normalization_status,
        "staged_runtime_cycle_hash_actual": staged_cycle_hash_actual,
        "runtime_cycle_validator_status": runtime_result.status,
        "runtime_cycle_validator_blocker_code": runtime_result.blocker_code,
        "ledger_validator_status": ledger_status,
        "ledger_validator_blocker_code": ledger_blocker,
        "ledger_validator_message": ledger_message,
        "source_ledger_event_count": len(ledger_events) if isinstance(ledger_events, list) else 0,
        "planned_runtime_cycle_path": planned["runtime_cycle"],
        "planned_ledger_jsonl_path": planned["ledger_jsonl"],
        "planned_writer_report_path": planned["writer_report"],
        "staging_path_scope_status": "MATCH" if path_scope_match else "MISMATCH",
        "staging_write_mode": "CREATE_NEW_OR_REUSE_MATCH_ONLY",
        "staging_artifact_paths": [planned["runtime_cycle"], planned["ledger_jsonl"], planned["writer_report"]],
        "staging_artifact_count": 3,
        "staging_written_count": staging_written_count,
        "staging_reused_existing_count": staging_reused_count,
        "runtime_cycle_staging_status": runtime_status,
        "ledger_jsonl_staging_status": ledger_write_status,
        "writer_report_staging_status": writer_status,
        "staging_item_status": staging_status,
        "blocker_code": blocker_code,
        "staged_artifact_is_current_evidence": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_rerun_executed": False,
        "requires_post_staging_ledger_rollup": True,
        "requires_post_staging_reconciliation": True,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_bounded_rerun_staging_executor_report(
    *,
    root: Path,
    missing_cycle_rerun_guard_report: dict[str, Any],
    executor_id: str = "upbit-paper-bounded-rerun-staging-executor",
) -> dict[str, Any]:
    root = Path(root).resolve()
    guard_result = validate_upbit_paper_missing_cycle_rerun_guard_report(missing_cycle_rerun_guard_report)
    session_id = str(missing_cycle_rerun_guard_report.get("session_id", "UNKNOWN"))
    ready_guard_items = [
        item
        for item in missing_cycle_rerun_guard_report.get("items", [])
        if isinstance(item, dict) and item.get("next_patch_staging_rerun_candidate_eligible")
    ]
    recovery_blocked_items = [
        item
        for item in missing_cycle_rerun_guard_report.get("items", [])
        if isinstance(item, dict) and item.get("rerun_guard_status") == "BLOCKED_RECOVERY_GUARD_REQUIRED"
    ]
    blockers = {
        MISSING_CYCLE_LEDGER_RERUN_REQUIRED_BLOCKER_CODE,
        POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE,
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    }
    if guard_result.status != "PASS":
        blockers.add(guard_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    items: list[dict[str, Any]] = []
    if guard_result.status == "PASS":
        for guard_item in ready_guard_items:
            for cycle_id in guard_item.get("missing_cycle_ids") or []:
                items.append(_build_staging_item(root=root, session_id=session_id, guard_item=guard_item, cycle_id=str(cycle_id)))
        if recovery_blocked_items:
            blockers.add(RECOVERY_GUARD_RERUN_REQUIRED_BLOCKER_CODE)
    blockers.update(str(item["blocker_code"]) for item in items if item.get("blocker_code"))
    staged_cycle_count = sum(1 for item in items if item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"})
    staged_artifact_count = sum(int(item.get("staging_artifact_count") or 0) for item in items if item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"})
    staging_written_count = sum(
        int(item.get("staging_written_count") or 0)
        for item in items
        if item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"}
    )
    staging_reused_count = sum(
        int(item.get("staging_reused_existing_count") or 0)
        for item in items
        if item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"}
    )
    eligible_missing_cycle_count = sum(len(item.get("missing_cycle_ids") or []) for item in ready_guard_items)
    staged_paths = sorted({path for item in items for path in item.get("staging_artifact_paths", []) if item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"}})
    staging_status = "PASS" if staged_cycle_count == eligible_missing_cycle_count and not any(item.get("blocker_code") for item in items) else "BLOCKED"
    primary_blocker_code = (
        POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE
        if staging_status == "PASS"
        else sorted(blockers)[0] if blockers else POST_RERUN_LEDGER_ROLLUP_REQUIRED_BLOCKER_CODE
    )
    report = {
        "schema_id": UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "executor_id": executor_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "executor_role": BOUNDED_RERUN_STAGING_EXECUTOR_ROLE,
        "source_missing_cycle_rerun_guard_hash": missing_cycle_rerun_guard_report.get("guard_hash"),
        "source_missing_cycle_rerun_guard_status": missing_cycle_rerun_guard_report.get("guard_status"),
        "source_guard_item_count": int(missing_cycle_rerun_guard_report.get("guard_item_count") or 0),
        "ready_guard_item_count": len(ready_guard_items),
        "recovery_guard_blocked_item_count": len(recovery_blocked_items),
        "eligible_missing_cycle_count": eligible_missing_cycle_count,
        "staged_cycle_count": staged_cycle_count,
        "skipped_cycle_count": max(0, int(missing_cycle_rerun_guard_report.get("missing_cycle_ledger_jsonl_total_count") or 0) - staged_cycle_count),
        "staged_artifact_count": staged_artifact_count,
        "staging_written_artifact_count": staging_written_count,
        "staging_reused_existing_artifact_count": staging_reused_count,
        "staging_artifact_mismatch_count": sum(1 for item in items if item.get("blocker_code") == RERUN_STAGING_ARTIFACT_MISMATCH_BLOCKER_CODE),
        "staged_current_evidence_usable_count": 0,
        "staging_status": staging_status,
        "executor_status": "BLOCKED",
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blockers),
        "staging_write_mode": "CREATE_NEW_OR_REUSE_MATCH_ONLY",
        "staged_artifact_paths": staged_paths,
        "items": items,
        "operator_next_action": (
            "Build a post-rerun PAPER ledger rollup from staged candidates and run reconciliation before any current evidence pointer can change."
        ),
        "post_staging_ledger_rollup_required": True,
        "post_staging_reconciliation_required": True,
        "staging_executor_created": True,
        "actual_staging_performed": bool(staged_cycle_count),
        "actual_rerun_executed": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
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
        "scale_up_allowed": False,
        "executor_hash": "",
    }
    report["executor_hash"] = upbit_paper_bounded_rerun_staging_executor_hash(report)
    return report


def write_upbit_paper_bounded_rerun_staging_executor_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_bounded_rerun_staging_executor_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_bounded_rerun_staging_executor_report(
    report: dict[str, Any],
) -> UpbitPaperBoundedRerunStagingExecutorValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "executor_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "executor_role",
        "source_missing_cycle_rerun_guard_hash",
        "source_missing_cycle_rerun_guard_status",
        "source_guard_item_count",
        "ready_guard_item_count",
        "recovery_guard_blocked_item_count",
        "eligible_missing_cycle_count",
        "staged_cycle_count",
        "skipped_cycle_count",
        "staged_artifact_count",
        "staging_written_artifact_count",
        "staging_reused_existing_artifact_count",
        "staging_artifact_mismatch_count",
        "staged_current_evidence_usable_count",
        "staging_status",
        "executor_status",
        "primary_blocker_code",
        "blocker_codes",
        "staging_write_mode",
        "staged_artifact_paths",
        "items",
        "operator_next_action",
        "post_staging_ledger_rollup_required",
        "post_staging_reconciliation_required",
        "staging_executor_created",
        "actual_staging_performed",
        "actual_rerun_executed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
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
        "scale_up_allowed",
        "executor_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", f"bounded rerun staging executor missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR_SCHEMA_ID:
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "bounded rerun staging executor schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("executor_hash") != upbit_paper_bounded_rerun_staging_executor_hash(report):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "bounded rerun staging executor hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging executor scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("executor_role") != BOUNDED_RERUN_STAGING_EXECUTOR_ROLE:
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging executor role cannot claim current evidence", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
        "actual_rerun_executed",
        "current_evidence_mutation_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
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
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden_fields):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging executor created forbidden mutation/live/order/scale behavior", "LIVE_FINAL_GUARD_FAILED")
    if report.get("executor_status") != "BLOCKED" or report.get("primary_blocker_code") is None:
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging executor must remain blocked pending rollup and reconciliation", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if not report.get("post_staging_ledger_rollup_required") or not report.get("post_staging_reconciliation_required"):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging executor must require post-staging rollup and reconciliation", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("staged_current_evidence_usable_count") != 0:
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging executor exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED")
    session_id = str(report.get("session_id"))
    for path in report.get("staged_artifact_paths") or []:
        if not isinstance(path, str) or not _staging_path_allowed(path, session_id):
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging artifact escaped staging namespace", "SNAPSHOT_SCOPE_MISMATCH")
    items = report.get("items")
    if not isinstance(items, list):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "bounded rerun staging executor items must be an array", "SCHEMA_IDENTITY_MISMATCH")
    expected = {
        "staged_cycle_count": 0,
        "staged_artifact_count": 0,
        "staging_written_artifact_count": 0,
        "staging_reused_existing_artifact_count": 0,
        "staging_artifact_mismatch_count": 0,
    }
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "bounded rerun staging item must be object", "SCHEMA_IDENTITY_MISMATCH")
        item_required = {
            "source_guard_priority_order",
            "replacement_loop_id",
            "replacement_path",
            "replacement_load_status",
            "cycle_id",
            "source_runtime_cycle_path",
            "source_runtime_cycle_load_status",
            "source_runtime_cycle_hash_expected",
            "source_runtime_cycle_hash_actual",
            "source_runtime_cycle_hash_match",
            "source_runtime_cycle_validator_status",
            "source_runtime_cycle_validator_blocker_code",
            "runtime_cycle_normalization_status",
            "staged_runtime_cycle_hash_actual",
            "runtime_cycle_validator_status",
            "runtime_cycle_validator_blocker_code",
            "ledger_validator_status",
            "ledger_validator_blocker_code",
            "ledger_validator_message",
            "source_ledger_event_count",
            "planned_runtime_cycle_path",
            "planned_ledger_jsonl_path",
            "planned_writer_report_path",
            "staging_path_scope_status",
            "staging_write_mode",
            "staging_artifact_paths",
            "staging_artifact_count",
            "staging_written_count",
            "staging_reused_existing_count",
            "runtime_cycle_staging_status",
            "ledger_jsonl_staging_status",
            "writer_report_staging_status",
            "staging_item_status",
            "blocker_code",
            "staged_artifact_is_current_evidence",
            "current_ledger_jsonl_write_allowed",
            "latest_runtime_pointer_write_allowed",
            "persistent_loop_mutation_allowed",
            "source_delete_allowed",
            "actual_rerun_executed",
            "requires_post_staging_ledger_rollup",
            "requires_post_staging_reconciliation",
            "actual_long_run_evidence_created",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", f"bounded rerun staging item missing fields: {missing_item}", "SCHEMA_IDENTITY_MISMATCH")
        if not _artifact_path_allowed(str(item.get("source_runtime_cycle_path") or ""), session_id):
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging source cycle path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        for path in item.get("staging_artifact_paths") or []:
            if not isinstance(path, str) or not _staging_path_allowed(path, session_id):
                return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging item path escaped staging namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if (
            item.get("staged_artifact_is_current_evidence")
            or item.get("current_ledger_jsonl_write_allowed")
            or item.get("latest_runtime_pointer_write_allowed")
            or item.get("persistent_loop_mutation_allowed")
            or item.get("source_delete_allowed")
            or item.get("actual_rerun_executed")
            or item.get("actual_long_run_evidence_created")
            or item.get("live_order_allowed")
            or item.get("scale_up_allowed")
        ):
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "bounded rerun staging item created forbidden mutation/live/order/scale behavior", "LIVE_FINAL_GUARD_FAILED")
        if item.get("staging_item_status") in {"STAGED", "REUSED_EXISTING"}:
            if item.get("runtime_cycle_validator_status") != "PASS" or item.get("ledger_validator_status") != "PASS":
                return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "staged rerun item must validate source cycle and ledger", "SCHEMA_IDENTITY_MISMATCH")
            if not item.get("source_runtime_cycle_hash_match"):
                return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "staged rerun item source hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
            if item.get("runtime_cycle_normalization_status") not in {"NOT_REQUIRED", "APPLIED_STAGING_ONLY"}:
                return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "staged rerun item has invalid normalization status", "SCHEMA_IDENTITY_MISMATCH")
            if not isinstance(item.get("staged_runtime_cycle_hash_actual"), str) or len(item["staged_runtime_cycle_hash_actual"]) != 64:
                return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "staged rerun item missing staged runtime hash", "SCHEMA_IDENTITY_MISMATCH")
            if not item.get("requires_post_staging_ledger_rollup") or not item.get("requires_post_staging_reconciliation"):
                return UpbitPaperBoundedRerunStagingExecutorValidationResult("BLOCKED", "staged rerun item must require rollup and reconciliation", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
            expected["staged_cycle_count"] += 1
            expected["staged_artifact_count"] += int(item.get("staging_artifact_count") or 0)
            expected["staging_written_artifact_count"] += int(item.get("staging_written_count") or 0)
            expected["staging_reused_existing_artifact_count"] += int(item.get("staging_reused_existing_count") or 0)
        elif item.get("staging_item_status") != "BLOCKED" or not item.get("blocker_code"):
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "blocked rerun staging item must expose blocker", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("blocker_code") == RERUN_STAGING_ARTIFACT_MISMATCH_BLOCKER_CODE:
            expected["staging_artifact_mismatch_count"] += 1
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", f"bounded rerun staging count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("eligible_missing_cycle_count") != len(items):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "bounded rerun staging eligible cycle count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("staging_status") == "PASS" and report.get("staged_cycle_count") != report.get("eligible_missing_cycle_count"):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "PASS staging status requires every eligible cycle to be staged", "SCHEMA_IDENTITY_MISMATCH")
    if MISSING_CYCLE_LEDGER_RERUN_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperBoundedRerunStagingExecutorValidationResult("FAIL", "bounded rerun staging executor missing source missing-cycle blocker", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperBoundedRerunStagingExecutorValidationResult(
        "PASS",
        "Upbit PAPER bounded rerun staging executor writes isolated rerun candidates without mutating current evidence",
        None,
    )
