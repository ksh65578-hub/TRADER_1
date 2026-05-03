from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.ledger.paper_ledger_rollup import (
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    upbit_paper_persistent_loop_hash,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_SCHEMA_ID = (
    "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"
)
UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_ROLE = (
    "PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_CURRENT_ROLLUP_ONLY"
)


@dataclass(frozen=True)
class UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64


def upbit_paper_ledger_idempotency_runtime_evidence_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("evidence_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/")
        and ".." not in parts
        and "/live/" not in normalized
    )


def _paper_runtime_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/")
        and normalized.endswith(".json")
        and ".." not in parts
        and "/live/" not in normalized
    )


def _blocker(code: str, message: str, severity: str = "HIGH") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


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


def _ledger_paths_from_rollup(root: Path, session_id: str, rollup: dict[str, Any], blockers: list[dict[str, str]]) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for artifact_path in rollup.get("artifact_paths", []):
        if not isinstance(artifact_path, str) or not artifact_path.endswith(".paper_ledger_events.jsonl"):
            continue
        if not _artifact_path_allowed(artifact_path, session_id):
            blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "PAPER ledger idempotency evidence found an escaped ledger path"))
            continue
        paths.append((artifact_path, _rooted(root, artifact_path)))
    if not paths:
        blockers.append(_blocker("LEDGER_UNAVAILABLE", "PAPER ledger idempotency evidence found no source ledger JSONL paths"))
    return sorted(paths, key=lambda item: item[0])


def _runtime_depth_blocker(cycle: dict[str, Any] | None, cycle_id: Any) -> str | None:
    if not isinstance(cycle, dict):
        return "MEASUREMENT_MISSING"
    if cycle.get("cycle_id") != cycle_id:
        return "RECONCILIATION_REQUIRED"
    if cycle.get("runtime_status") != "PASS" or cycle.get("runtime_writer_status") != "PASS":
        return "RECONCILIATION_REQUIRED"
    if cycle.get("runtime_input_role") != "PUBLIC_MARKET_DATA_COLLECTION":
        return "MEASUREMENT_MISSING"
    for hash_field in (
        "runtime_cycle_hash",
        "source_collection_report_hash",
        "source_public_market_data_hash",
        "runtime_public_market_data_hash",
        "feature_snapshot_hash",
    ):
        if not _is_sha256(cycle.get(hash_field)):
            return "SCHEMA_IDENTITY_MISMATCH"
    if cycle.get("source_public_market_data_hash") != cycle.get("runtime_public_market_data_hash"):
        return "SCHEMA_IDENTITY_MISMATCH"
    if not isinstance(cycle.get("canonical_event_count"), int) or cycle["canonical_event_count"] < 5:
        return "MEASUREMENT_MISSING"
    linkage = cycle.get("strategy_regime_cost_linkage")
    if not isinstance(linkage, dict):
        return "SCHEMA_IDENTITY_MISMATCH"
    if linkage.get("live_order_ready") or linkage.get("live_order_allowed") or linkage.get("can_live_trade") or linkage.get("scale_up_allowed"):
        return "LIVE_FINAL_GUARD_FAILED"
    expected_linkage = {
        "source_runtime_cycle_id": cycle.get("cycle_id"),
        "runtime_input_role": cycle.get("runtime_input_role"),
        "runtime_public_market_data_hash": cycle.get("runtime_public_market_data_hash"),
        "feature_snapshot_hash": cycle.get("feature_snapshot_hash"),
        "report_regime": cycle.get("regime"),
        "selected_candidate_id": cycle.get("selected_candidate_id"),
        "selected_candidate_net_ev_after_cost_bps": cycle.get("selected_candidate_net_ev_after_cost_bps"),
    }
    for field, expected_value in expected_linkage.items():
        if linkage.get(field) != expected_value:
            return "SCHEMA_IDENTITY_MISMATCH"
    return None


def build_upbit_paper_ledger_idempotency_runtime_evidence_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    evidence_id: str = "upbit-paper-ledger-idempotency-runtime-evidence",
    source_rollup_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_path = source_rollup_path or (_runtime_base(root, session_id) / "ledger" / "paper_ledger_rollup_report.json")
    source_path = Path(source_path).resolve()
    source_rollup_path_text = _relative_posix(source_path, root)
    source_persistent_loop_path = _runtime_base(root, session_id) / "paper_runtime" / "upbit_paper_persistent_loop_report.json"
    source_persistent_loop_path_text = _relative_posix(source_persistent_loop_path, root)
    blockers: list[dict[str, str]] = []

    rollup, load_error = _safe_load_json(source_path)
    if load_error:
        blockers.append(_blocker("LEDGER_UNAVAILABLE", f"PAPER ledger rollup source could not be loaded: {load_error}"))
        rollup = {}

    source_rollup_hash = rollup.get("rollup_hash") if isinstance(rollup, dict) else None
    source_rollup_recomputed_hash = paper_ledger_rollup_hash(rollup) if isinstance(rollup, dict) else None
    source_hash_self_check = "PASS" if source_rollup_hash == source_rollup_recomputed_hash else "FAIL"
    source_validation = validate_paper_ledger_rollup_report(rollup if isinstance(rollup, dict) else {})
    if source_validation.status != "PASS":
        blockers.append(
            _blocker(
                source_validation.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
                f"PAPER ledger rollup source did not validate PASS: {source_validation.message}",
            )
        )
    if source_hash_self_check != "PASS":
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER ledger rollup source hash self-check failed"))

    persistent_loop, persistent_load_error = _safe_load_json(source_persistent_loop_path)
    if persistent_load_error:
        blockers.append(
            _blocker(
                "MEASUREMENT_MISSING",
                f"PAPER persistent loop source could not be loaded for ledger runtime-depth binding: {persistent_load_error}",
            )
        )
        persistent_loop = {}
    source_persistent_loop_hash = persistent_loop.get("loop_hash") if isinstance(persistent_loop, dict) else None
    source_persistent_loop_recomputed_hash = upbit_paper_persistent_loop_hash(persistent_loop if isinstance(persistent_loop, dict) else {})
    source_persistent_loop_hash_self_check = "PASS" if source_persistent_loop_hash == source_persistent_loop_recomputed_hash else "FAIL"
    source_persistent_loop_validation = validate_upbit_paper_persistent_loop_report(persistent_loop if isinstance(persistent_loop, dict) else {})
    if source_persistent_loop_validation.status != "PASS":
        blockers.append(
            _blocker(
                source_persistent_loop_validation.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
                f"PAPER persistent loop source did not validate PASS: {source_persistent_loop_validation.message}",
            )
        )
    if source_persistent_loop_hash_self_check != "PASS":
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER persistent loop source hash self-check failed"))

    cycle_results = persistent_loop.get("cycle_results") if isinstance(persistent_loop.get("cycle_results"), list) else []
    source_runtime_cycle_ids = sorted(
        str(item.get("cycle_id")) for item in cycle_results if isinstance(item, dict) and isinstance(item.get("cycle_id"), str)
    )
    source_runtime_cycle_hashes = sorted(
        str(item.get("runtime_cycle_hash")) for item in cycle_results if isinstance(item, dict) and _is_sha256(item.get("runtime_cycle_hash"))
    )
    source_ledger_head_cycle_id = rollup.get("ledger_head_cycle_id")
    ledger_head_cycle = next(
        (item for item in cycle_results if isinstance(item, dict) and item.get("cycle_id") == source_ledger_head_cycle_id),
        None,
    )
    ledger_head_cycle_in_persistent_loop = ledger_head_cycle is not None
    runtime_depth_blocker = _runtime_depth_blocker(ledger_head_cycle, source_ledger_head_cycle_id)
    source_runtime_depth_status = "PASS" if runtime_depth_blocker is None else "BLOCKED"
    source_runtime_depth_mismatch_count = 0 if source_runtime_depth_status == "PASS" else 1
    if runtime_depth_blocker is not None:
        blockers.append(
            _blocker(
                runtime_depth_blocker,
                "PAPER ledger head cycle is not bound to a PASS persistent loop public runtime-depth cycle",
            )
        )
    source_linkage = ledger_head_cycle.get("strategy_regime_cost_linkage") if isinstance(ledger_head_cycle, dict) else None
    if not isinstance(source_linkage, dict):
        source_linkage = {}

    source_ledger_paths = _ledger_paths_from_rollup(root, session_id, rollup, blockers)
    all_events: list[dict[str, Any]] = []
    fill_events: list[dict[str, Any]] = []
    duplicate_event_id_count = 0
    duplicate_dedup_key_count = 0
    duplicate_semantic_event_count = 0
    duplicate_filled_order_key_count = 0
    ledger_validation_fail_count = 0
    missing_or_invalid_ledger_jsonl_count = 0
    cross_scope_event_count = 0
    seen_event_ids: set[str] = set()
    seen_dedup_keys: set[str] = set()
    seen_semantic_events: set[tuple[str, Any, Any, Any]] = set()
    seen_filled_order_keys: set[tuple[Any, Any]] = set()

    for relative_path, absolute_path in source_ledger_paths:
        records, error = _safe_read_jsonl(absolute_path)
        if error or records is None:
            missing_or_invalid_ledger_jsonl_count += 1
            blockers.append(_blocker("LEDGER_UNAVAILABLE", f"PAPER ledger JSONL could not be loaded: {relative_path}"))
            continue
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
        if ledger_status != "PASS":
            ledger_validation_fail_count += 1
            blockers.append(_blocker(ledger_blocker or "LEDGER_INTEGRITY_FAIL", ledger_message))
        for event in records:
            if (
                event.get("exchange") != "UPBIT"
                or event.get("market_type") != "KRW_SPOT"
                or event.get("mode") != "PAPER"
                or event.get("session_id") != session_id
            ):
                cross_scope_event_count += 1
                blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "PAPER ledger idempotency evidence detected cross-scope ledger data"))
                continue
            event_id = str(event.get("event_id"))
            if event_id in seen_event_ids:
                duplicate_event_id_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", f"duplicate ledger event_id requires reconciliation: {event_id}"))
            seen_event_ids.add(event_id)
            dedup_key = str(event.get("dedup_key"))
            if dedup_key in seen_dedup_keys:
                duplicate_dedup_key_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", f"duplicate ledger dedup_key requires reconciliation: {dedup_key}"))
            seen_dedup_keys.add(dedup_key)
            semantic_key = (str(event.get("event_type")), event.get("intent_id"), event.get("client_order_id"), event.get("order_id"))
            if (event.get("intent_id") or event.get("client_order_id") or event.get("order_id")) and semantic_key in seen_semantic_events:
                duplicate_semantic_event_count += 1
                blockers.append(_blocker("RECONCILIATION_REQUIRED", "duplicate semantic ledger event requires reconciliation"))
            seen_semantic_events.add(semantic_key)
            if event.get("event_type") == "ORDER_FILLED":
                filled_order_key = (event.get("client_order_id"), event.get("order_id"))
                if filled_order_key in seen_filled_order_keys:
                    duplicate_filled_order_key_count += 1
                    blockers.append(_blocker("RECONCILIATION_REQUIRED", "duplicate filled PAPER order requires reconciliation"))
                seen_filled_order_keys.add(filled_order_key)
                fill_events.append(event)
            all_events.append(event)

    source_count_mismatch_count = 0
    count_pairs = {
        "ledger_jsonl_count": len(source_ledger_paths),
        "ledger_event_count": len(all_events),
        "filled_order_count": len(fill_events),
        "duplicate_event_count": duplicate_event_id_count + duplicate_dedup_key_count + duplicate_semantic_event_count,
        "duplicate_order_count": duplicate_filled_order_key_count,
    }
    for field, recomputed in count_pairs.items():
        if rollup.get(field) != recomputed:
            source_count_mismatch_count += 1
            blockers.append(_blocker("RECONCILIATION_REQUIRED", f"PAPER ledger rollup count mismatch: {field}"))

    portfolio = rollup.get("portfolio_snapshot") if isinstance(rollup.get("portfolio_snapshot"), dict) else {}
    portfolio_provenance_match = (
        portfolio.get("snapshot_status") == "PASS"
        and portfolio.get("source") == "PAPER_LEDGER_ROLLUP"
        and portfolio.get("source_paper_ledger_head_hash") == rollup.get("latest_ledger_head_hash")
        and portfolio.get("source_runtime_cycle_id") == rollup.get("ledger_head_cycle_id")
    )
    if not portfolio_provenance_match:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER portfolio snapshot provenance does not match the rollup ledger head"))

    ledger_head_binding_status = (
        "PASS"
        if rollup.get("ledger_head_match_status") == "PASS" and rollup.get("ledger_head_mismatch_count") == 0
        else "MISMATCH"
    )
    if ledger_head_binding_status != "PASS":
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER ledger head binding is not PASS"))

    forbidden_rollup_flags = (
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(rollup.get(field) for field in forbidden_rollup_flags):
        blockers.append(_blocker("LIVE_FINAL_GUARD_FAILED", "source PAPER ledger rollup attempted forbidden live or promotion permission"))

    duplicate_total = duplicate_event_id_count + duplicate_dedup_key_count + duplicate_semantic_event_count + duplicate_filled_order_key_count
    idempotency_status = "PASS" if duplicate_total == 0 else "BLOCKED"
    source_count_match_status = "PASS" if source_count_mismatch_count == 0 else "MISMATCH"
    portfolio_provenance_status = "PASS" if portfolio_provenance_match else "MISMATCH"
    reconciliation_status = (
        "PASS"
        if (
            source_validation.status == "PASS"
            and source_hash_self_check == "PASS"
            and source_count_match_status == "PASS"
            and idempotency_status == "PASS"
            and portfolio_provenance_status == "PASS"
            and ledger_head_binding_status == "PASS"
            and source_persistent_loop_validation.status == "PASS"
            and source_persistent_loop_hash_self_check == "PASS"
            and source_runtime_depth_status == "PASS"
            and ledger_validation_fail_count == 0
            and missing_or_invalid_ledger_jsonl_count == 0
            and cross_scope_event_count == 0
        )
        else "BLOCKED"
    )
    runtime_evidence_status = "PASS" if reconciliation_status == "PASS" and not blockers else "BLOCKED"

    report = {
        "schema_id": UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "evidence_id": evidence_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "evidence_role": UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_ROLE,
        "source_rollup_path": source_rollup_path_text,
        "source_rollup_hash": source_rollup_hash,
        "source_rollup_recomputed_hash": source_rollup_recomputed_hash,
        "source_rollup_hash_self_check": source_hash_self_check,
        "source_rollup_status": rollup.get("rollup_status"),
        "source_rollup_validation_status": source_validation.status,
        "source_rollup_blocker_code": source_validation.blocker_code,
        "source_ledger_head_hash": rollup.get("latest_ledger_head_hash"),
        "source_ledger_head_cycle_id": source_ledger_head_cycle_id,
        "ledger_head_binding_status": ledger_head_binding_status,
        "source_persistent_loop_path": source_persistent_loop_path_text,
        "source_persistent_loop_hash": source_persistent_loop_hash,
        "source_persistent_loop_recomputed_hash": source_persistent_loop_recomputed_hash,
        "source_persistent_loop_hash_self_check": source_persistent_loop_hash_self_check,
        "source_persistent_loop_validation_status": source_persistent_loop_validation.status,
        "source_persistent_loop_blocker_code": source_persistent_loop_validation.blocker_code,
        "source_persistent_loop_cycle_count": len(cycle_results),
        "source_runtime_cycle_ids": source_runtime_cycle_ids,
        "source_runtime_cycle_hashes": source_runtime_cycle_hashes,
        "ledger_head_cycle_in_persistent_loop": ledger_head_cycle_in_persistent_loop,
        "ledger_head_runtime_cycle_hash": ledger_head_cycle.get("runtime_cycle_hash") if isinstance(ledger_head_cycle, dict) else None,
        "source_runtime_input_role": ledger_head_cycle.get("runtime_input_role") if isinstance(ledger_head_cycle, dict) else None,
        "source_collection_report_hash": ledger_head_cycle.get("source_collection_report_hash") if isinstance(ledger_head_cycle, dict) else None,
        "source_public_market_data_hash": ledger_head_cycle.get("source_public_market_data_hash") if isinstance(ledger_head_cycle, dict) else None,
        "source_runtime_public_market_data_hash": ledger_head_cycle.get("runtime_public_market_data_hash") if isinstance(ledger_head_cycle, dict) else None,
        "source_canonical_event_count": (
            ledger_head_cycle.get("canonical_event_count")
            if isinstance(ledger_head_cycle, dict) and isinstance(ledger_head_cycle.get("canonical_event_count"), int)
            else 0
        ),
        "source_feature_snapshot_hash": ledger_head_cycle.get("feature_snapshot_hash") if isinstance(ledger_head_cycle, dict) else None,
        "source_regime": ledger_head_cycle.get("regime") if isinstance(ledger_head_cycle, dict) else None,
        "source_selected_candidate_id": ledger_head_cycle.get("selected_candidate_id") if isinstance(ledger_head_cycle, dict) else None,
        "source_selected_candidate_net_ev_after_cost_bps": (
            ledger_head_cycle.get("selected_candidate_net_ev_after_cost_bps") if isinstance(ledger_head_cycle, dict) else None
        ),
        "source_strategy_regime_cost_linkage_hash": _sha256_json(source_linkage) if source_linkage else None,
        "source_strategy_regime_cost_linkage_live_order_ready": bool(source_linkage.get("live_order_ready")),
        "source_strategy_regime_cost_linkage_live_order_allowed": bool(source_linkage.get("live_order_allowed")),
        "source_strategy_regime_cost_linkage_can_live_trade": bool(source_linkage.get("can_live_trade")),
        "source_strategy_regime_cost_linkage_scale_up_allowed": bool(source_linkage.get("scale_up_allowed")),
        "source_runtime_depth_status": source_runtime_depth_status,
        "source_runtime_depth_blocker_code": runtime_depth_blocker,
        "source_runtime_depth_mismatch_count": source_runtime_depth_mismatch_count,
        "source_ledger_paths": [relative_path for relative_path, _ in source_ledger_paths],
        "source_ledger_jsonl_count": int(rollup.get("ledger_jsonl_count") or 0),
        "source_ledger_event_count": int(rollup.get("ledger_event_count") or 0),
        "source_filled_order_count": int(rollup.get("filled_order_count") or 0),
        "source_duplicate_event_count": int(rollup.get("duplicate_event_count") or 0),
        "source_duplicate_order_count": int(rollup.get("duplicate_order_count") or 0),
        "recomputed_ledger_jsonl_count": len(source_ledger_paths),
        "recomputed_ledger_event_count": len(all_events),
        "recomputed_filled_order_count": len(fill_events),
        "recomputed_event_id_count": len(seen_event_ids),
        "recomputed_dedup_key_count": len(seen_dedup_keys),
        "recomputed_semantic_event_count": len(seen_semantic_events),
        "recomputed_filled_order_key_count": len(seen_filled_order_keys),
        "duplicate_event_id_count": duplicate_event_id_count,
        "duplicate_dedup_key_count": duplicate_dedup_key_count,
        "duplicate_semantic_event_count": duplicate_semantic_event_count,
        "duplicate_filled_order_key_count": duplicate_filled_order_key_count,
        "ledger_validation_fail_count": ledger_validation_fail_count,
        "missing_or_invalid_ledger_jsonl_count": missing_or_invalid_ledger_jsonl_count,
        "cross_scope_event_count": cross_scope_event_count,
        "source_count_match_status": source_count_match_status,
        "source_count_mismatch_count": source_count_mismatch_count,
        "idempotency_status": idempotency_status,
        "reconciliation_status": reconciliation_status,
        "portfolio_provenance_status": portfolio_provenance_status,
        "portfolio_snapshot_status": portfolio.get("snapshot_status"),
        "portfolio_source_runtime_cycle_id": portfolio.get("source_runtime_cycle_id"),
        "portfolio_source_paper_ledger_head_hash": portfolio.get("source_paper_ledger_head_hash"),
        "runtime_evidence_status": runtime_evidence_status,
        "mismatch_count": (
            source_count_mismatch_count
            + duplicate_total
            + ledger_validation_fail_count
            + missing_or_invalid_ledger_jsonl_count
            + cross_scope_event_count
            + source_runtime_depth_mismatch_count
        ),
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "current_evidence_write_allowed": False,
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
        "evidence_hash": "",
    }
    report["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(report)
    return report


def write_upbit_paper_ledger_idempotency_runtime_evidence_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "ledger"
        / "upbit_paper_ledger_idempotency_runtime_evidence_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_ledger_idempotency_runtime_evidence_report(
    report: dict[str, Any],
) -> UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "evidence_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "evidence_role",
        "source_rollup_path",
        "source_rollup_hash",
        "source_rollup_recomputed_hash",
        "source_rollup_hash_self_check",
        "source_rollup_status",
        "source_rollup_validation_status",
        "source_rollup_blocker_code",
        "source_ledger_head_hash",
        "source_ledger_head_cycle_id",
        "ledger_head_binding_status",
        "source_persistent_loop_path",
        "source_persistent_loop_hash",
        "source_persistent_loop_recomputed_hash",
        "source_persistent_loop_hash_self_check",
        "source_persistent_loop_validation_status",
        "source_persistent_loop_blocker_code",
        "source_persistent_loop_cycle_count",
        "source_runtime_cycle_ids",
        "source_runtime_cycle_hashes",
        "ledger_head_cycle_in_persistent_loop",
        "ledger_head_runtime_cycle_hash",
        "source_runtime_input_role",
        "source_collection_report_hash",
        "source_public_market_data_hash",
        "source_runtime_public_market_data_hash",
        "source_canonical_event_count",
        "source_feature_snapshot_hash",
        "source_regime",
        "source_selected_candidate_id",
        "source_selected_candidate_net_ev_after_cost_bps",
        "source_strategy_regime_cost_linkage_hash",
        "source_strategy_regime_cost_linkage_live_order_ready",
        "source_strategy_regime_cost_linkage_live_order_allowed",
        "source_strategy_regime_cost_linkage_can_live_trade",
        "source_strategy_regime_cost_linkage_scale_up_allowed",
        "source_runtime_depth_status",
        "source_runtime_depth_blocker_code",
        "source_runtime_depth_mismatch_count",
        "source_ledger_paths",
        "source_ledger_jsonl_count",
        "source_ledger_event_count",
        "source_filled_order_count",
        "source_duplicate_event_count",
        "source_duplicate_order_count",
        "recomputed_ledger_jsonl_count",
        "recomputed_ledger_event_count",
        "recomputed_filled_order_count",
        "recomputed_event_id_count",
        "recomputed_dedup_key_count",
        "recomputed_semantic_event_count",
        "recomputed_filled_order_key_count",
        "duplicate_event_id_count",
        "duplicate_dedup_key_count",
        "duplicate_semantic_event_count",
        "duplicate_filled_order_key_count",
        "ledger_validation_fail_count",
        "missing_or_invalid_ledger_jsonl_count",
        "cross_scope_event_count",
        "source_count_match_status",
        "source_count_mismatch_count",
        "idempotency_status",
        "reconciliation_status",
        "portfolio_provenance_status",
        "portfolio_snapshot_status",
        "portfolio_source_runtime_cycle_id",
        "portfolio_source_paper_ledger_head_hash",
        "runtime_evidence_status",
        "mismatch_count",
        "primary_blocker_code",
        "blockers",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "current_evidence_write_allowed",
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
        "evidence_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", f"idempotency runtime evidence missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_SCHEMA_ID or report.get("project_id") != "TRADER_1":
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence identity mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("evidence_hash") != upbit_paper_ledger_idempotency_runtime_evidence_hash(report):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "idempotency runtime evidence scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("evidence_role") != UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_ROLE:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "idempotency runtime evidence role cannot claim live or exchange truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_write_allowed",
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
    if any(report.get(field) for field in forbidden):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "idempotency runtime evidence created forbidden permission or live interaction", "LIVE_FINAL_GUARD_FAILED")
    if not report.get("display_only") or not report.get("dashboard_truth_only") or not report.get("paper_only"):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "idempotency runtime evidence must remain display-only PAPER evidence", "LIVE_FINAL_GUARD_FAILED")

    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_rollup_path") or ""), session_id):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "source rollup path escaped PAPER ledger namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if not _paper_runtime_path_allowed(str(report.get("source_persistent_loop_path") or ""), session_id):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "source persistent loop path escaped PAPER runtime namespace", "SNAPSHOT_SCOPE_MISMATCH")
    source_ledger_paths = report.get("source_ledger_paths")
    if not isinstance(source_ledger_paths, list):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source_ledger_paths must be an array", "SCHEMA_IDENTITY_MISMATCH")
    for source_path in source_ledger_paths:
        if not isinstance(source_path, str) or not source_path.endswith(".paper_ledger_events.jsonl") or not _artifact_path_allowed(source_path, session_id):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "source ledger path escaped PAPER ledger namespace", "SNAPSHOT_SCOPE_MISMATCH")

    count_fields = (
        "source_ledger_jsonl_count",
        "source_ledger_event_count",
        "source_filled_order_count",
        "source_duplicate_event_count",
        "source_duplicate_order_count",
        "recomputed_ledger_jsonl_count",
        "recomputed_ledger_event_count",
        "recomputed_filled_order_count",
        "recomputed_event_id_count",
        "recomputed_dedup_key_count",
        "recomputed_semantic_event_count",
        "recomputed_filled_order_key_count",
        "duplicate_event_id_count",
        "duplicate_dedup_key_count",
        "duplicate_semantic_event_count",
        "duplicate_filled_order_key_count",
        "ledger_validation_fail_count",
        "missing_or_invalid_ledger_jsonl_count",
        "cross_scope_event_count",
        "source_count_mismatch_count",
        "source_persistent_loop_cycle_count",
        "source_canonical_event_count",
        "source_runtime_depth_mismatch_count",
        "mismatch_count",
    )
    for field in count_fields:
        if not isinstance(report.get(field), int) or report.get(field) < 0:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", f"idempotency runtime evidence count invalid: {field}", "SCHEMA_IDENTITY_MISMATCH")

    duplicate_total = (
        report["duplicate_event_id_count"]
        + report["duplicate_dedup_key_count"]
        + report["duplicate_semantic_event_count"]
        + report["duplicate_filled_order_key_count"]
    )
    expected_mismatch_count = (
        report["source_count_mismatch_count"]
        + duplicate_total
        + report["ledger_validation_fail_count"]
        + report["missing_or_invalid_ledger_jsonl_count"]
        + report["cross_scope_event_count"]
        + report["source_runtime_depth_mismatch_count"]
    )
    if report.get("mismatch_count") != expected_mismatch_count:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence mismatch_count is inconsistent", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("recomputed_ledger_jsonl_count") != len(source_ledger_paths):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence ledger path count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_ledger_jsonl_count") != report.get("recomputed_ledger_jsonl_count"):
        if report.get("source_count_match_status") == "PASS":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source count status cannot PASS with JSONL mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_ledger_event_count") != report.get("recomputed_ledger_event_count"):
        if report.get("source_count_match_status") == "PASS":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source count status cannot PASS with event mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_filled_order_count") != report.get("recomputed_filled_order_count"):
        if report.get("source_count_match_status") == "PASS":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source count status cannot PASS with fill mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_duplicate_event_count") != (
        report.get("duplicate_event_id_count") + report.get("duplicate_dedup_key_count") + report.get("duplicate_semantic_event_count")
    ):
        if report.get("source_count_match_status") == "PASS":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source duplicate event count mismatch cannot PASS", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_duplicate_order_count") != report.get("duplicate_filled_order_key_count"):
        if report.get("source_count_match_status") == "PASS":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source duplicate order count mismatch cannot PASS", "SCHEMA_IDENTITY_MISMATCH")

    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    if blockers and report.get("primary_blocker_code") not in blocker_codes:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "idempotency runtime evidence primary blocker mismatch", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
    if not blockers and report.get("primary_blocker_code") is not None:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence primary blocker set without blockers", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("source_strategy_regime_cost_linkage_live_order_ready")
        or report.get("source_strategy_regime_cost_linkage_live_order_allowed")
        or report.get("source_strategy_regime_cost_linkage_can_live_trade")
        or report.get("source_strategy_regime_cost_linkage_scale_up_allowed")
    ):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult(
            "BLOCKED",
            "source strategy/regime/cost linkage attempted live or scale-up permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    source_runtime_cycle_ids = report.get("source_runtime_cycle_ids")
    source_runtime_cycle_hashes = report.get("source_runtime_cycle_hashes")
    if not isinstance(source_runtime_cycle_ids, list) or not all(isinstance(item, str) and item for item in source_runtime_cycle_ids):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source runtime cycle ids must be a string array", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(source_runtime_cycle_hashes, list) or not all(_is_sha256(item) for item in source_runtime_cycle_hashes):
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source runtime cycle hashes must be sha256 array", "SCHEMA_IDENTITY_MISMATCH")

    status_fields = {
        "source_rollup_hash_self_check": {"PASS", "FAIL"},
        "source_rollup_status": {"PASS", "BLOCKED"},
        "source_rollup_validation_status": {"PASS", "FAIL", "BLOCKED"},
        "source_persistent_loop_hash_self_check": {"PASS", "FAIL"},
        "source_persistent_loop_validation_status": {"PASS", "FAIL", "BLOCKED"},
        "ledger_head_binding_status": {"PASS", "MISMATCH"},
        "source_runtime_input_role": {"PUBLIC_MARKET_DATA_COLLECTION", "STATIC_FIXTURE", None},
        "source_runtime_depth_status": {"PASS", "BLOCKED"},
        "source_count_match_status": {"PASS", "MISMATCH"},
        "idempotency_status": {"PASS", "BLOCKED"},
        "reconciliation_status": {"PASS", "BLOCKED"},
        "portfolio_provenance_status": {"PASS", "MISMATCH"},
        "portfolio_snapshot_status": {"PASS", "BLOCKED", None},
        "runtime_evidence_status": {"PASS", "BLOCKED"},
    }
    for field, allowed in status_fields.items():
        if report.get(field) not in allowed:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", f"idempotency runtime evidence status invalid: {field}", "SCHEMA_IDENTITY_MISMATCH")

    if report.get("runtime_evidence_status") == "PASS":
        pass_required = (
            "source_rollup_hash_self_check",
            "source_rollup_status",
            "source_rollup_validation_status",
            "source_persistent_loop_hash_self_check",
            "source_persistent_loop_validation_status",
            "source_runtime_depth_status",
            "ledger_head_binding_status",
            "source_count_match_status",
            "idempotency_status",
            "reconciliation_status",
            "portfolio_provenance_status",
            "portfolio_snapshot_status",
        )
        for field in pass_required:
            if report.get(field) != "PASS":
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", f"PASS idempotency evidence requires {field}=PASS", "LEDGER_INTEGRITY_FAIL")
        if blockers:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "PASS idempotency evidence cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if (
            duplicate_total
            or report.get("source_count_mismatch_count")
            or report.get("ledger_validation_fail_count")
            or report.get("missing_or_invalid_ledger_jsonl_count")
            or report.get("cross_scope_event_count")
            or report.get("source_runtime_depth_mismatch_count")
        ):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "PASS idempotency evidence cannot carry mismatches", "RECONCILIATION_REQUIRED")
        if report.get("recomputed_ledger_jsonl_count") < 1 or report.get("recomputed_ledger_event_count") < 1:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "PASS idempotency evidence requires source PAPER ledger events", "LEDGER_UNAVAILABLE")
        if report.get("ledger_head_cycle_in_persistent_loop") is not True:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "PASS idempotency evidence requires ledger head cycle in persistent loop", "RECONCILIATION_REQUIRED")
        if report.get("source_ledger_head_cycle_id") not in source_runtime_cycle_ids:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "ledger head cycle id missing from persistent loop cycle ids", "RECONCILIATION_REQUIRED")
        if not _is_sha256(report.get("ledger_head_runtime_cycle_hash")) or report.get("ledger_head_runtime_cycle_hash") not in source_runtime_cycle_hashes:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "ledger head runtime cycle hash missing from persistent loop hashes", "RECONCILIATION_REQUIRED")
        for hash_field in (
            "source_persistent_loop_hash",
            "source_persistent_loop_recomputed_hash",
            "source_collection_report_hash",
            "source_public_market_data_hash",
            "source_runtime_public_market_data_hash",
            "source_feature_snapshot_hash",
            "source_strategy_regime_cost_linkage_hash",
        ):
            if not _is_sha256(report.get(hash_field)):
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", f"PASS idempotency evidence missing runtime-depth hash: {hash_field}", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("source_public_market_data_hash") != report.get("source_runtime_public_market_data_hash"):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source/runtime public market data hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("source_runtime_input_role") != "PUBLIC_MARKET_DATA_COLLECTION" or report.get("source_canonical_event_count", 0) < 5:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "PASS idempotency evidence requires public runtime-depth collection evidence", "MEASUREMENT_MISSING")
        if report.get("source_runtime_depth_blocker_code") is not None:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "PASS idempotency evidence cannot carry runtime-depth blocker", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("portfolio_source_paper_ledger_head_hash") != report.get("source_ledger_head_hash"):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "portfolio ledger head hash mismatch", "LEDGER_INTEGRITY_FAIL")
        if report.get("portfolio_source_runtime_cycle_id") != report.get("source_ledger_head_cycle_id"):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "portfolio source cycle mismatch", "LEDGER_INTEGRITY_FAIL")
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult(
            "PASS",
            "Upbit PAPER ledger idempotency runtime evidence is scoped, recomputed, and live-blocked",
            None,
        )

    if report.get("runtime_evidence_status") != "BLOCKED":
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "idempotency runtime evidence status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult(
        "BLOCKED",
        "Upbit PAPER ledger idempotency runtime evidence is blocked",
        report.get("primary_blocker_code") or "UNKNOWN_BLOCKED",
    )
