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
from trader1.runtime.ledger.paper_ledger_input_manifest import (
    PAPER_LEDGER_INPUT_MANIFEST_SCOPE,
    load_paper_ledger_input_manifest,
    paper_ledger_input_manifest_hash,
    paper_ledger_input_manifest_path,
    validate_paper_ledger_input_manifest,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    upbit_paper_persistent_loop_hash,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
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


def _manifest_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return (
        normalized == f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/paper_ledger_input_manifest.json"
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


def _runtime_cycle_summary_from_artifact(
    *,
    root: Path,
    session_id: str,
    cycle_id: str,
    blockers: list[dict[str, str]],
) -> tuple[dict[str, Any] | None, str | None]:
    cycle_path = _runtime_base(root, session_id) / "paper_runtime" / "cycles" / f"{cycle_id}.runtime_cycle.json"
    cycle_path_text = _relative_posix(cycle_path, root)
    if not _paper_runtime_path_allowed(cycle_path_text, session_id):
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "PAPER runtime cycle artifact path escaped PAPER namespace"))
        return None, cycle_path_text
    cycle, cycle_error = _safe_load_json(cycle_path)
    if cycle_error:
        blockers.append(_blocker("MEASUREMENT_MISSING", f"PAPER runtime cycle artifact could not be loaded: {cycle_error}"))
        return None, cycle_path_text
    if cycle.get("cycle_id") != cycle_id:
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "PAPER runtime cycle artifact identity does not match rollup head cycle"))
        return None, cycle_path_text
    if cycle.get("cycle_hash") != upbit_paper_runtime_cycle_hash(cycle):
        blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "PAPER runtime cycle artifact hash self-check failed"))
        return None, cycle_path_text
    runtime_cycle_contract_mode = "CURRENT"
    cycle_result = validate_upbit_paper_runtime_cycle_report(cycle)
    if cycle_result.status != "PASS":
        legacy_cycle_result = validate_upbit_paper_runtime_cycle_report(cycle, require_current_sizing_caps=False)
        if (
            legacy_cycle_result.status == "PASS"
            and cycle_result.blocker_code == "SCHEMA_IDENTITY_MISMATCH"
            and "exposure_cap" in cycle_result.message
        ):
            runtime_cycle_contract_mode = "LEGACY_RECHECK_WITHOUT_CURRENT_SIZING_EXPOSURE_CAP"
            cycle_result = legacy_cycle_result
    if cycle_result.status != "PASS":
        blockers.append(
            _blocker(
                cycle_result.blocker_code or "RECONCILIATION_REQUIRED",
                f"PAPER runtime cycle artifact did not validate PASS: {cycle_result.message}",
            )
        )
        return None, cycle_path_text

    writer_path = _runtime_base(root, session_id) / "paper_runtime" / "cycles" / f"{cycle_id}.writer_report.json"
    writer_path_text = _relative_posix(writer_path, root)
    if not _paper_runtime_path_allowed(writer_path_text, session_id):
        blockers.append(_blocker("SNAPSHOT_SCOPE_MISMATCH", "PAPER runtime cycle writer path escaped PAPER namespace"))
        return None, cycle_path_text
    writer, writer_error = _safe_load_json(writer_path)
    if writer_error:
        blockers.append(_blocker("MEASUREMENT_MISSING", f"PAPER runtime cycle writer report could not be loaded: {writer_error}"))
        return None, cycle_path_text
    if (
        writer.get("writer_status") != "PASS"
        or writer.get("cycle_id") != cycle_id
        or writer.get("live_order_ready")
        or writer.get("live_order_allowed")
        or writer.get("can_live_trade")
        or writer.get("scale_up_allowed")
    ):
        blockers.append(_blocker("RECONCILIATION_REQUIRED", "PAPER runtime cycle writer report is not a PASS live-blocked writer"))
        return None, cycle_path_text

    selected = cycle.get("selected_candidate") if isinstance(cycle.get("selected_candidate"), dict) else {}
    return (
        {
            "cycle_id": cycle.get("cycle_id"),
            "runtime_status": "PASS",
            "runtime_writer_status": "PASS",
            "runtime_input_role": cycle.get("runtime_input_role"),
            "runtime_cycle_hash": cycle.get("cycle_hash"),
            "runtime_cycle_contract_mode": runtime_cycle_contract_mode,
            "source_collection_report_hash": cycle.get("source_collection_report_hash"),
            "source_public_market_data_hash": cycle.get("source_public_market_data_hash"),
            "runtime_public_market_data_hash": cycle.get("runtime_public_market_data_hash"),
            "feature_snapshot_hash": cycle.get("feature_snapshot_hash"),
            "canonical_event_count": cycle.get("canonical_event_count"),
            "strategy_regime_cost_linkage": cycle.get("strategy_regime_cost_linkage"),
            "regime": cycle.get("regime"),
            "selected_candidate_id": selected.get("candidate_id"),
            "selected_candidate_net_ev_after_cost_bps": selected.get("net_ev_after_cost_bps"),
        },
        cycle_path_text,
    )


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

    source_rollup_ledger_input_scope = rollup.get("ledger_input_scope") if isinstance(rollup, dict) else None
    source_rollup_ledger_head_match_status = rollup.get("ledger_head_match_status") if isinstance(rollup, dict) else None
    try:
        source_rollup_ledger_head_mismatch_count = int(rollup.get("ledger_head_mismatch_count") or 0)
    except (TypeError, ValueError):
        source_rollup_ledger_head_mismatch_count = 1

    source_manifest_path = None
    source_manifest_hash = None
    source_manifest_validation_status = "NOT_APPLICABLE"
    source_manifest_blocker_code = None
    source_manifest_binding_status = "NOT_APPLICABLE"
    source_manifest_accepted_ledger_path_count = 0
    source_manifest_excluded_ledger_path_count = 0
    manifest_excluded_paths: set[str] = set()
    if source_rollup_ledger_input_scope == PAPER_LEDGER_INPUT_MANIFEST_SCOPE:
        manifest_path = paper_ledger_input_manifest_path(root, session_id)
        source_manifest_path = _relative_posix(manifest_path, root)
        manifest, manifest_load_error = load_paper_ledger_input_manifest(root=root, session_id=session_id)
        if manifest_load_error:
            source_manifest_validation_status = "BLOCKED"
            source_manifest_binding_status = "MISMATCH"
            source_manifest_blocker_code = "RECONCILIATION_REQUIRED"
            blockers.append(
                _blocker(
                    "RECONCILIATION_REQUIRED",
                    f"PAPER ledger input manifest could not be loaded for idempotency binding: {manifest_load_error}",
                )
            )
        else:
            source_manifest_hash = manifest.get("manifest_hash") if isinstance(manifest, dict) else None
            manifest_result = validate_paper_ledger_input_manifest(manifest if isinstance(manifest, dict) else {})
            source_manifest_validation_status = manifest_result.status
            source_manifest_blocker_code = manifest_result.blocker_code
            accepted = manifest.get("accepted_ledger_paths") if isinstance(manifest.get("accepted_ledger_paths"), list) else []
            excluded = manifest.get("excluded_ledger_paths") if isinstance(manifest.get("excluded_ledger_paths"), list) else []
            source_manifest_accepted_ledger_path_count = len(accepted)
            source_manifest_excluded_ledger_path_count = len(excluded)
            manifest_excluded_paths = {
                str(item.get("path"))
                for item in excluded
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            }
            if manifest_result.status != "PASS":
                source_manifest_binding_status = "MISMATCH"
                blockers.append(
                    _blocker(
                        manifest_result.blocker_code or "RECONCILIATION_REQUIRED",
                        f"PAPER ledger input manifest did not validate PASS: {manifest_result.message}",
                    )
                )
            elif source_manifest_hash != paper_ledger_input_manifest_hash(manifest):
                source_manifest_validation_status = "FAIL"
                source_manifest_binding_status = "MISMATCH"
                source_manifest_blocker_code = "SCHEMA_IDENTITY_MISMATCH"
                blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "PAPER ledger input manifest hash self-check failed"))
            elif source_manifest_path not in rollup.get("artifact_paths", []):
                source_manifest_binding_status = "MISMATCH"
                blockers.append(_blocker("SCHEMA_IDENTITY_MISMATCH", "manifest-scoped rollup is missing the input manifest artifact path"))
            else:
                source_manifest_binding_status = "PASS"

    cycle_results = persistent_loop.get("cycle_results") if isinstance(persistent_loop.get("cycle_results"), list) else []
    source_runtime_cycle_ids = sorted(
        str(item.get("cycle_id")) for item in cycle_results if isinstance(item, dict) and isinstance(item.get("cycle_id"), str)
    )
    source_runtime_cycle_hashes = sorted(
        str(item.get("runtime_cycle_hash")) for item in cycle_results if isinstance(item, dict) and _is_sha256(item.get("runtime_cycle_hash"))
    )
    portfolio = rollup.get("portfolio_snapshot") if isinstance(rollup.get("portfolio_snapshot"), dict) else {}
    source_ledger_head_cycle_id = rollup.get("ledger_head_cycle_id")
    if (
        not source_ledger_head_cycle_id
        and source_rollup_ledger_input_scope == PAPER_LEDGER_INPUT_MANIFEST_SCOPE
        and source_rollup_ledger_head_match_status == "NOT_APPLICABLE"
    ):
        source_ledger_head_cycle_id = portfolio.get("source_runtime_cycle_id")
    ledger_head_cycle = next(
        (item for item in cycle_results if isinstance(item, dict) and item.get("cycle_id") == source_ledger_head_cycle_id),
        None,
    )
    source_runtime_cycle_binding_source = "PERSISTENT_LOOP_REPORT" if ledger_head_cycle is not None else "NOT_FOUND"
    source_runtime_cycle_path = None
    source_runtime_cycle_contract_mode = "PERSISTENT_LOOP_SUMMARY" if ledger_head_cycle is not None else "NOT_BOUND"
    if (
        ledger_head_cycle is None
        and isinstance(source_ledger_head_cycle_id, str)
        and source_ledger_head_cycle_id
        and source_persistent_loop_validation.status == "PASS"
        and source_persistent_loop_hash_self_check == "PASS"
    ):
        artifact_cycle, artifact_path = _runtime_cycle_summary_from_artifact(
            root=root,
            session_id=session_id,
            cycle_id=source_ledger_head_cycle_id,
            blockers=blockers,
        )
        if artifact_cycle is not None:
            ledger_head_cycle = artifact_cycle
            source_runtime_cycle_binding_source = "SCOPED_RUNTIME_CYCLE_ARTIFACT"
            source_runtime_cycle_path = artifact_path
            source_runtime_cycle_contract_mode = str(
                artifact_cycle.get("runtime_cycle_contract_mode") or "CURRENT"
            )
    ledger_head_cycle_in_persistent_loop = (
        ledger_head_cycle is not None and source_runtime_cycle_binding_source == "PERSISTENT_LOOP_REPORT"
    )
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

    portfolio_provenance_match = (
        portfolio.get("snapshot_status") == "PASS"
        and portfolio.get("source") == "PAPER_LEDGER_ROLLUP"
        and portfolio.get("source_paper_ledger_head_hash") == rollup.get("latest_ledger_head_hash")
        and portfolio.get("source_runtime_cycle_id") == rollup.get("ledger_head_cycle_id")
    )
    if (
        source_rollup_ledger_input_scope == PAPER_LEDGER_INPUT_MANIFEST_SCOPE
        and source_rollup_ledger_head_match_status == "NOT_APPLICABLE"
    ):
        portfolio_provenance_match = (
            portfolio.get("snapshot_status") == "PASS"
            and portfolio.get("source") == "PAPER_LEDGER_ROLLUP"
            and portfolio.get("source_paper_ledger_head_hash") == rollup.get("latest_ledger_head_hash")
            and portfolio.get("source_runtime_cycle_id") == source_ledger_head_cycle_id
        )
    if not portfolio_provenance_match:
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER portfolio snapshot provenance does not match the rollup ledger head"))

    manifest_scoped_head_binding = (
        source_rollup_ledger_input_scope == PAPER_LEDGER_INPUT_MANIFEST_SCOPE
        and source_rollup_ledger_head_match_status == "NOT_APPLICABLE"
        and source_rollup_ledger_head_mismatch_count == 0
        and source_manifest_validation_status == "PASS"
        and source_manifest_binding_status == "PASS"
        and isinstance(source_ledger_head_cycle_id, str)
        and _is_sha256(rollup.get("latest_ledger_head_hash"))
        and portfolio_provenance_match
    )
    direct_head_binding = rollup.get("ledger_head_match_status") == "PASS" and rollup.get("ledger_head_mismatch_count") == 0
    ledger_head_binding_status = "PASS" if direct_head_binding or manifest_scoped_head_binding else "MISMATCH"
    if ledger_head_binding_status != "PASS":
        blockers.append(_blocker("LEDGER_INTEGRITY_FAIL", "PAPER ledger head binding is not PASS"))
    if source_manifest_binding_status == "PASS" and manifest_excluded_paths:
        included_excluded_paths = sorted(set(relative_path for relative_path, _ in source_ledger_paths) & manifest_excluded_paths)
        if included_excluded_paths:
            source_manifest_binding_status = "MISMATCH"
            ledger_head_binding_status = "MISMATCH"
            blockers.append(_blocker("RECONCILIATION_REQUIRED", "manifest-scoped rollup included excluded PAPER ledger paths"))

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
        "source_rollup_ledger_input_scope": source_rollup_ledger_input_scope,
        "source_rollup_ledger_head_match_status": source_rollup_ledger_head_match_status,
        "source_rollup_ledger_head_mismatch_count": source_rollup_ledger_head_mismatch_count,
        "source_manifest_path": source_manifest_path,
        "source_manifest_hash": source_manifest_hash,
        "source_manifest_validation_status": source_manifest_validation_status,
        "source_manifest_blocker_code": source_manifest_blocker_code,
        "source_manifest_binding_status": source_manifest_binding_status,
        "source_manifest_accepted_ledger_path_count": source_manifest_accepted_ledger_path_count,
        "source_manifest_excluded_ledger_path_count": source_manifest_excluded_ledger_path_count,
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
        "source_runtime_cycle_binding_source": source_runtime_cycle_binding_source,
        "source_runtime_cycle_path": source_runtime_cycle_path,
        "source_runtime_cycle_contract_mode": source_runtime_cycle_contract_mode,
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
        "source_rollup_ledger_input_scope",
        "source_rollup_ledger_head_match_status",
        "source_rollup_ledger_head_mismatch_count",
        "source_manifest_path",
        "source_manifest_hash",
        "source_manifest_validation_status",
        "source_manifest_blocker_code",
        "source_manifest_binding_status",
        "source_manifest_accepted_ledger_path_count",
        "source_manifest_excluded_ledger_path_count",
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
        "source_runtime_cycle_binding_source",
        "source_runtime_cycle_path",
        "source_runtime_cycle_contract_mode",
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
        "source_rollup_ledger_head_mismatch_count",
        "source_manifest_accepted_ledger_path_count",
        "source_manifest_excluded_ledger_path_count",
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
    if report.get("source_runtime_cycle_binding_source") not in {
        "PERSISTENT_LOOP_REPORT",
        "SCOPED_RUNTIME_CYCLE_ARTIFACT",
        "NOT_FOUND",
    }:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "runtime cycle binding source is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_runtime_cycle_contract_mode") not in {
        "PERSISTENT_LOOP_SUMMARY",
        "CURRENT",
        "LEGACY_RECHECK_WITHOUT_CURRENT_SIZING_EXPOSURE_CAP",
        "NOT_BOUND",
    }:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "runtime cycle contract mode is unknown", "SCHEMA_IDENTITY_MISMATCH")
    source_runtime_cycle_path = report.get("source_runtime_cycle_path")
    if source_runtime_cycle_path is not None:
        if not isinstance(source_runtime_cycle_path, str) or not _paper_runtime_path_allowed(source_runtime_cycle_path, session_id):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "runtime cycle artifact path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("source_runtime_cycle_binding_source") == "SCOPED_RUNTIME_CYCLE_ARTIFACT" and not source_runtime_cycle_path:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "runtime cycle artifact binding requires a source path", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_runtime_cycle_binding_source") == "PERSISTENT_LOOP_REPORT":
        if report.get("source_runtime_cycle_contract_mode") != "PERSISTENT_LOOP_SUMMARY":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "persistent-loop binding must use persistent-loop summary contract mode", "SCHEMA_IDENTITY_MISMATCH")
    elif report.get("source_runtime_cycle_binding_source") == "SCOPED_RUNTIME_CYCLE_ARTIFACT":
        if report.get("source_runtime_cycle_contract_mode") not in {
            "CURRENT",
            "LEGACY_RECHECK_WITHOUT_CURRENT_SIZING_EXPOSURE_CAP",
        }:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "artifact binding must expose current or legacy runtime cycle contract mode", "SCHEMA_IDENTITY_MISMATCH")
    elif report.get("source_runtime_cycle_contract_mode") != "NOT_BOUND":
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "unbound runtime cycle must mark contract mode NOT_BOUND", "SCHEMA_IDENTITY_MISMATCH")

    rollup_input_scope = report.get("source_rollup_ledger_input_scope")
    if rollup_input_scope not in {"SESSION_CYCLE_GLOB", "EXPLICIT_SCOPED_PATHS", PAPER_LEDGER_INPUT_MANIFEST_SCOPE, None}:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source rollup input scope is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_rollup_ledger_head_match_status") not in {"PASS", "MISSING", "MISMATCH", "NOT_APPLICABLE", None}:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "source rollup head match status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_manifest_validation_status") not in {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "manifest validation status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_manifest_binding_status") not in {"PASS", "MISMATCH", "NOT_APPLICABLE"}:
        return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "manifest binding status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    source_manifest_path = report.get("source_manifest_path")
    if rollup_input_scope == PAPER_LEDGER_INPUT_MANIFEST_SCOPE:
        if not isinstance(source_manifest_path, str) or not _manifest_path_allowed(source_manifest_path, session_id):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "manifest path escaped PAPER ledger namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _is_sha256(report.get("source_manifest_hash")):
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "manifest-scoped evidence requires manifest hash", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("source_manifest_validation_status") != "PASS" or report.get("source_manifest_binding_status") != "PASS":
            if report.get("runtime_evidence_status") == "PASS":
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "PASS manifest-scoped evidence requires manifest binding PASS", "LEDGER_INTEGRITY_FAIL")
    else:
        if source_manifest_path is not None or report.get("source_manifest_hash") is not None:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "non-manifest evidence cannot expose manifest source fields", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("source_manifest_validation_status") != "NOT_APPLICABLE" or report.get("source_manifest_binding_status") != "NOT_APPLICABLE":
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "non-manifest evidence must mark manifest binding not applicable", "SCHEMA_IDENTITY_MISMATCH")

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
        binding_source = report.get("source_runtime_cycle_binding_source")
        if binding_source == "PERSISTENT_LOOP_REPORT":
            if report.get("ledger_head_cycle_in_persistent_loop") is not True:
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "PASS idempotency evidence requires ledger head cycle in persistent loop", "RECONCILIATION_REQUIRED")
            if report.get("source_ledger_head_cycle_id") not in source_runtime_cycle_ids:
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "ledger head cycle id missing from persistent loop cycle ids", "RECONCILIATION_REQUIRED")
            if not _is_sha256(report.get("ledger_head_runtime_cycle_hash")) or report.get("ledger_head_runtime_cycle_hash") not in source_runtime_cycle_hashes:
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "ledger head runtime cycle hash missing from persistent loop hashes", "RECONCILIATION_REQUIRED")
        elif binding_source == "SCOPED_RUNTIME_CYCLE_ARTIFACT":
            if not _is_sha256(report.get("ledger_head_runtime_cycle_hash")):
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "runtime cycle artifact binding requires a runtime cycle hash", "SCHEMA_IDENTITY_MISMATCH")
            if report.get("ledger_head_cycle_in_persistent_loop") is not False:
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "artifact-bound cycle cannot also claim persistent-loop membership", "SCHEMA_IDENTITY_MISMATCH")
        else:
            return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("BLOCKED", "PASS idempotency evidence requires a runtime cycle binding", "MEASUREMENT_MISSING")
        if rollup_input_scope == PAPER_LEDGER_INPUT_MANIFEST_SCOPE:
            if (
                report.get("source_rollup_ledger_head_match_status") != "NOT_APPLICABLE"
                and report.get("source_rollup_ledger_head_match_status") != "PASS"
            ):
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "manifest-scoped evidence cannot pass with mismatched rollup head status", "LEDGER_INTEGRITY_FAIL")
            if report.get("source_manifest_validation_status") != "PASS" or report.get("source_manifest_binding_status") != "PASS":
                return UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult("FAIL", "manifest-scoped PASS evidence requires manifest validation and binding PASS", "LEDGER_INTEGRITY_FAIL")
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
