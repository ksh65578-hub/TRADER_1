from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_closure_recheck import (
    POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS,
    upbit_paper_post_rerun_current_evidence_closure_recheck_hash,
    validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_resolution_current_evidence_closure import (
    POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
    POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS,
    upbit_paper_post_rerun_resolution_current_evidence_closure_hash,
    validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1"
)
POST_RERUN_RECONCILIATION_REPAIR_PATH_TRUTH_ROLE = (
    "PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_ANALYSIS_ONLY_NOT_WRITER"
)
POST_RERUN_RECONCILIATION_REPAIR_PATH_STATUS = "BLOCKED_REPAIR_PATH_DECLARED"
POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED = (
    "POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED"
)

REPAIR_GATE_IDS = (
    "VALIDATED_OPERATOR_RESOLUTION_ACCEPTANCE",
    "VALIDATED_CURRENT_LEDGER_REBUILD",
    "VALIDATED_SOURCE_HASH_RECONCILIATION",
    "VALIDATED_NO_LIVE_OR_SCALE_MUTATION",
)
RECHECK_RUNTIME_DEPTH_HASH_FIELDS = (
    "source_recheck_ledger_source_persistent_loop_hash",
    "source_recheck_ledger_head_runtime_cycle_hash",
    "source_recheck_ledger_source_public_market_data_hash",
    "source_recheck_ledger_source_runtime_public_market_data_hash",
    "source_recheck_ledger_source_feature_snapshot_hash",
    "source_recheck_ledger_source_strategy_regime_cost_linkage_hash",
)
RECHECK_STRATEGY_REGIME_COST_LINKAGE_FALSE_FIELDS = (
    "source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_ready",
    "source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_allowed",
    "source_recheck_ledger_source_strategy_regime_cost_linkage_can_live_trade",
    "source_recheck_ledger_source_strategy_regime_cost_linkage_scale_up_allowed",
)


@dataclass(frozen=True)
class UpbitPaperPostRerunReconciliationRepairPathValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_post_rerun_reconciliation_repair_path_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("repair_path_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _runtime_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "/live/" not in normalized


def _closure_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        _runtime_path_allowed(normalized, session_id)
        and normalized.endswith("/paper_runtime/upbit_paper_post_rerun_resolution_current_evidence_closure_report.json")
    )


def _recheck_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        _runtime_path_allowed(normalized, session_id)
        and normalized.endswith("/paper_runtime/upbit_paper_post_rerun_current_evidence_closure_recheck_report.json")
    )


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


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_hash64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64


def _load_source(
    *,
    root: Path,
    relative_path: str,
    session_id: str,
    path_checker: Any,
    hash_field: str,
    hash_func: Any,
) -> dict[str, Any]:
    if not path_checker(relative_path, session_id):
        return {
            "source": {},
            "file_load_status": "SCOPE_MISMATCH",
            "source_hash": None,
            "source_recomputed_hash": None,
            "hash_match": False,
        }
    source, error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            "source": {},
            "file_load_status": str(error or "UNKNOWN"),
            "source_hash": None,
            "source_recomputed_hash": None,
            "hash_match": False,
        }
    source_hash = source.get(hash_field)
    recomputed_hash = hash_func(source)
    return {
        "source": source,
        "file_load_status": "PASS" if source_hash == recomputed_hash else "HASH_MISMATCH",
        "source_hash": source_hash,
        "source_recomputed_hash": recomputed_hash,
        "hash_match": source_hash == recomputed_hash,
    }


def _build_repair_gates() -> list[dict[str, Any]]:
    next_actions = {
        "VALIDATED_OPERATOR_RESOLUTION_ACCEPTANCE": (
            "Record a separately validated operator resolution acceptance before any current-evidence rebuild."
        ),
        "VALIDATED_CURRENT_LEDGER_REBUILD": (
            "Rebuild current PAPER ledger evidence through a validated writer, not through post-rerun review artifacts."
        ),
        "VALIDATED_SOURCE_HASH_RECONCILIATION": (
            "Bind rebuilt current evidence to source hashes and reject drift before publishing operator-current truth."
        ),
        "VALIDATED_NO_LIVE_OR_SCALE_MUTATION": (
            "Confirm no live permission, order adapter, credential, current pointer, or scale-up mutation occurred."
        ),
    }
    gates: list[dict[str, Any]] = []
    for order, gate_id in enumerate(REPAIR_GATE_IDS, start=1):
        gates.append(
            {
                "repair_order": order,
                "gate_id": gate_id,
                "gate_status": "BLOCKED",
                "required": True,
                "satisfied": False,
                "source_evidence_status": "MISSING",
                "blocking_reason_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
                "next_action": next_actions[gate_id],
                "blocks_current_evidence": True,
                "blocks_live": True,
                "blocks_scale_up": True,
                "current_evidence_write_allowed": False,
                "current_ledger_jsonl_write_allowed": False,
                "latest_runtime_pointer_write_allowed": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return gates


def build_upbit_paper_post_rerun_reconciliation_repair_path_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    closure_report_path: str | None = None,
    closure_recheck_report_path: str | None = None,
    repair_path_id: str = "upbit-paper-post-rerun-reconciliation-repair-path",
) -> dict[str, Any]:
    root = Path(root).resolve()
    closure_path = closure_report_path or (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
    )
    recheck_path = closure_recheck_report_path or (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json"
    )

    closure_binding = _load_source(
        root=root,
        relative_path=closure_path,
        session_id=session_id,
        path_checker=_closure_path_allowed,
        hash_field="closure_hash",
        hash_func=upbit_paper_post_rerun_resolution_current_evidence_closure_hash,
    )
    recheck_binding = _load_source(
        root=root,
        relative_path=recheck_path,
        session_id=session_id,
        path_checker=_recheck_path_allowed,
        hash_field="recheck_hash",
        hash_func=upbit_paper_post_rerun_current_evidence_closure_recheck_hash,
    )
    closure = closure_binding["source"]
    recheck = recheck_binding["source"]
    closure_result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(closure)
    recheck_result = validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(recheck)

    gates = _build_repair_gates()
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if closure_binding["file_load_status"] != "PASS" or not closure_binding["hash_match"]:
        blockers.add(POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED)
    if recheck_binding["file_load_status"] != "PASS" or not recheck_binding["hash_match"]:
        blockers.add(POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED)
    if closure_result.status != "PASS":
        blockers.add(closure_result.blocker_code or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if recheck_result.status != "PASS":
        blockers.add(recheck_result.blocker_code or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)

    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "repair_path_id": repair_path_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_RECONCILIATION_REPAIR_PATH_TRUTH_ROLE,
        "repair_path_role": "ANALYSIS_ONLY_REPAIR_GATE_DECLARATION_NOT_CURRENT_EVIDENCE",
        "repair_path_status": POST_RERUN_RECONCILIATION_REPAIR_PATH_STATUS,
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "source_closure_path": closure_path,
        "source_closure_hash": closure_binding["source_hash"],
        "source_closure_recomputed_hash": closure_binding["source_recomputed_hash"],
        "source_closure_file_load_status": closure_binding["file_load_status"],
        "source_closure_file_hash_match": bool(closure_binding["hash_match"]),
        "source_closure_validation_status": closure_result.status,
        "source_closure_blocker_code": closure_result.blocker_code,
        "source_recheck_path": recheck_path,
        "source_recheck_hash": recheck_binding["source_hash"],
        "source_recheck_recomputed_hash": recheck_binding["source_recomputed_hash"],
        "source_recheck_file_load_status": recheck_binding["file_load_status"],
        "source_recheck_file_hash_match": bool(recheck_binding["hash_match"]),
        "source_recheck_validation_status": recheck_result.status,
        "source_recheck_blocker_code": recheck_result.blocker_code,
        "source_closure_status": str(closure.get("closure_status") or "NOT_LOADED"),
        "source_closure_primary_blocker_code": str(closure.get("primary_blocker_code") or "NOT_LOADED"),
        "source_closure_closed_item_count": int(closure.get("closed_item_count") or 0),
        "source_closure_current_evidence_write_allowed_count": int(
            closure.get("current_evidence_write_allowed_count") or 0
        ),
        "source_closure_candidate_current_evidence_usable_count": int(
            closure.get("candidate_current_evidence_usable_count") or 0
        ),
        "source_recheck_status": str(recheck.get("recheck_status") or "NOT_LOADED"),
        "source_recheck_bridge_status": str(recheck.get("current_evidence_bridge_status") or "NOT_LOADED"),
        "source_recheck_portfolio_truth_status": str(recheck.get("portfolio_truth_recheck_status") or "NOT_LOADED"),
        "source_recheck_ledger_runtime_evidence_status": str(
            recheck.get("ledger_runtime_evidence_status") or "NOT_LOADED"
        ),
        "source_recheck_ledger_reconciliation_status": str(
            recheck.get("ledger_reconciliation_status") or "NOT_LOADED"
        ),
        "source_recheck_ledger_idempotency_status": str(recheck.get("ledger_idempotency_status") or "NOT_LOADED"),
        "source_recheck_ledger_portfolio_provenance_status": str(
            recheck.get("ledger_portfolio_provenance_status") or "NOT_LOADED"
        ),
        "source_recheck_ledger_source_persistent_loop_path": str(
            recheck.get("ledger_source_persistent_loop_path") or "NOT_LOADED"
        ),
        "source_recheck_ledger_source_persistent_loop_hash": recheck.get("ledger_source_persistent_loop_hash"),
        "source_recheck_ledger_source_persistent_loop_validation_status": str(
            recheck.get("ledger_source_persistent_loop_validation_status") or "NOT_LOADED"
        ),
        "source_recheck_ledger_source_persistent_loop_hash_self_check": str(
            recheck.get("ledger_source_persistent_loop_hash_self_check") or "NOT_LOADED"
        ),
        "source_recheck_ledger_head_cycle_in_persistent_loop": bool(
            recheck.get("ledger_head_cycle_in_persistent_loop") is True
        ),
        "source_recheck_ledger_head_runtime_cycle_hash": recheck.get("ledger_head_runtime_cycle_hash"),
        "source_recheck_ledger_source_runtime_input_role": str(
            recheck.get("ledger_source_runtime_input_role") or "NOT_LOADED"
        ),
        "source_recheck_ledger_source_public_market_data_hash": recheck.get("ledger_source_public_market_data_hash"),
        "source_recheck_ledger_source_runtime_public_market_data_hash": recheck.get(
            "ledger_source_runtime_public_market_data_hash"
        ),
        "source_recheck_ledger_source_feature_snapshot_hash": recheck.get("ledger_source_feature_snapshot_hash"),
        "source_recheck_ledger_source_canonical_event_count": _safe_int(
            recheck.get("ledger_source_canonical_event_count")
        ),
        "source_recheck_ledger_source_strategy_regime_cost_linkage_hash": recheck.get(
            "ledger_source_strategy_regime_cost_linkage_hash"
        ),
        "source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_ready": bool(
            recheck.get("ledger_source_strategy_regime_cost_linkage_live_order_ready") is True
        ),
        "source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_allowed": bool(
            recheck.get("ledger_source_strategy_regime_cost_linkage_live_order_allowed") is True
        ),
        "source_recheck_ledger_source_strategy_regime_cost_linkage_can_live_trade": bool(
            recheck.get("ledger_source_strategy_regime_cost_linkage_can_live_trade") is True
        ),
        "source_recheck_ledger_source_strategy_regime_cost_linkage_scale_up_allowed": bool(
            recheck.get("ledger_source_strategy_regime_cost_linkage_scale_up_allowed") is True
        ),
        "source_recheck_ledger_source_runtime_depth_status": str(
            recheck.get("ledger_source_runtime_depth_status") or "NOT_LOADED"
        ),
        "source_recheck_ledger_source_runtime_depth_blocker_code": recheck.get(
            "ledger_source_runtime_depth_blocker_code"
        ),
        "source_recheck_ledger_source_runtime_depth_mismatch_count": _safe_int(
            recheck.get("ledger_source_runtime_depth_mismatch_count")
        ),
        "repair_gate_count": len(gates),
        "satisfied_repair_gate_count": 0,
        "blocked_repair_gate_count": len(gates),
        "current_evidence_write_authorized_count": 0,
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "repair_gates": gates,
        "blocker_codes": sorted(blockers),
        "repair_next_action": (
            "Do not publish current portfolio or ledger truth from post-rerun artifacts. "
            "Collect the four repair-gate evidence items through a separate validated repair writer first."
        ),
        "current_evidence_mutation_allowed": False,
        "current_evidence_write_authorized": False,
        "current_evidence_write_allowed": False,
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
        "can_submit_order": False,
        "scale_up_allowed": False,
        "repair_path_hash": "",
    }
    report["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(report)
    return report


def write_upbit_paper_post_rerun_reconciliation_repair_path_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_post_rerun_reconciliation_repair_path_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_reconciliation_repair_path_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunReconciliationRepairPathValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "repair_path_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "repair_path_role",
        "repair_path_status",
        "primary_blocker_code",
        "source_closure_path",
        "source_closure_hash",
        "source_closure_recomputed_hash",
        "source_closure_file_load_status",
        "source_closure_file_hash_match",
        "source_closure_validation_status",
        "source_closure_blocker_code",
        "source_recheck_path",
        "source_recheck_hash",
        "source_recheck_recomputed_hash",
        "source_recheck_file_load_status",
        "source_recheck_file_hash_match",
        "source_recheck_validation_status",
        "source_recheck_blocker_code",
        "source_closure_status",
        "source_closure_primary_blocker_code",
        "source_closure_closed_item_count",
        "source_closure_current_evidence_write_allowed_count",
        "source_closure_candidate_current_evidence_usable_count",
        "source_recheck_status",
        "source_recheck_bridge_status",
        "source_recheck_portfolio_truth_status",
        "source_recheck_ledger_runtime_evidence_status",
        "source_recheck_ledger_reconciliation_status",
        "source_recheck_ledger_idempotency_status",
        "source_recheck_ledger_portfolio_provenance_status",
        "source_recheck_ledger_source_persistent_loop_path",
        "source_recheck_ledger_source_persistent_loop_hash",
        "source_recheck_ledger_source_persistent_loop_validation_status",
        "source_recheck_ledger_source_persistent_loop_hash_self_check",
        "source_recheck_ledger_head_cycle_in_persistent_loop",
        "source_recheck_ledger_head_runtime_cycle_hash",
        "source_recheck_ledger_source_runtime_input_role",
        "source_recheck_ledger_source_public_market_data_hash",
        "source_recheck_ledger_source_runtime_public_market_data_hash",
        "source_recheck_ledger_source_feature_snapshot_hash",
        "source_recheck_ledger_source_canonical_event_count",
        "source_recheck_ledger_source_strategy_regime_cost_linkage_hash",
        "source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_ready",
        "source_recheck_ledger_source_strategy_regime_cost_linkage_live_order_allowed",
        "source_recheck_ledger_source_strategy_regime_cost_linkage_can_live_trade",
        "source_recheck_ledger_source_strategy_regime_cost_linkage_scale_up_allowed",
        "source_recheck_ledger_source_runtime_depth_status",
        "source_recheck_ledger_source_runtime_depth_blocker_code",
        "source_recheck_ledger_source_runtime_depth_mismatch_count",
        "repair_gate_count",
        "satisfied_repair_gate_count",
        "blocked_repair_gate_count",
        "current_evidence_write_authorized_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "repair_gates",
        "blocker_codes",
        "repair_next_action",
        "current_evidence_mutation_allowed",
        "current_evidence_write_authorized",
        "current_evidence_write_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
        "repair_path_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            f"post-rerun reconciliation repair path missing fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_SCHEMA_ID:
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            "post-rerun reconciliation repair path schema_id mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("repair_path_hash") != upbit_paper_post_rerun_reconciliation_repair_path_hash(report):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            "post-rerun reconciliation repair path hash mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun reconciliation repair path scope must remain UPBIT/KRW_SPOT/PAPER",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if (
        report.get("truth_role") != POST_RERUN_RECONCILIATION_REPAIR_PATH_TRUTH_ROLE
        or report.get("repair_path_role") != "ANALYSIS_ONLY_REPAIR_GATE_DECLARATION_NOT_CURRENT_EVIDENCE"
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun reconciliation repair path cannot claim writer/current/live truth",
            "LIVE_FINAL_GUARD_FAILED",
        )

    forbidden = (
        "current_evidence_mutation_allowed",
        "current_evidence_write_authorized",
        "current_evidence_write_allowed",
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
        "can_submit_order",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun reconciliation repair path created forbidden permission or mutation",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if (
        report.get("current_evidence_write_authorized_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun reconciliation repair path exposed current evidence counts",
            "LIVE_FINAL_GUARD_FAILED",
        )

    session_id = str(report.get("session_id"))
    if not _closure_path_allowed(str(report.get("source_closure_path") or ""), session_id):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path closure source escaped PAPER namespace",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if not _recheck_path_allowed(str(report.get("source_recheck_path") or ""), session_id):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path recheck source escaped PAPER namespace",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if (
        report.get("source_closure_file_load_status") != "PASS"
        or report.get("source_closure_file_hash_match") is not True
        or report.get("source_recheck_file_load_status") != "PASS"
        or report.get("source_recheck_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun reconciliation repair path source binding is missing or mismatched",
            POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED,
        )
    if (
        report.get("source_closure_hash") != report.get("source_closure_recomputed_hash")
        or report.get("source_recheck_hash") != report.get("source_recheck_recomputed_hash")
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            "post-rerun repair path source hash fields do not match",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("source_closure_validation_status") != "PASS":
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "source post-rerun closure did not validate PASS",
            report.get("source_closure_blocker_code") or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if report.get("source_recheck_validation_status") != "PASS":
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "source post-rerun closure recheck did not validate PASS",
            report.get("source_recheck_blocker_code") or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if (
        report.get("source_closure_status") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS
        or report.get("source_closure_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("source_closure_closed_item_count", 0) <= 0
        or report.get("source_closure_current_evidence_write_allowed_count") != 0
        or report.get("source_closure_candidate_current_evidence_usable_count") != 0
        or report.get("source_recheck_status") != POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS
        or report.get("source_recheck_bridge_status") != "BLOCKED_BY_POST_RERUN_CLOSURE"
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path source reports no longer confirm unresolved blocked closure",
            POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if (
        report.get("source_recheck_ledger_runtime_evidence_status") != "PASS"
        or report.get("source_recheck_ledger_reconciliation_status") != "PASS"
        or report.get("source_recheck_ledger_idempotency_status") != "PASS"
        or report.get("source_recheck_ledger_portfolio_provenance_status") != "PASS"
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path recheck ledger support is not clean",
            "RECONCILIATION_REQUIRED",
        )
    if any(not _is_hash64(report.get(field)) for field in RECHECK_RUNTIME_DEPTH_HASH_FIELDS):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path recheck runtime-depth hashes are missing",
            POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED,
        )
    if any(report.get(field) for field in RECHECK_STRATEGY_REGIME_COST_LINKAGE_FALSE_FIELDS):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path recheck source linkage attempted live or scale permission",
            "LIVE_FINAL_GUARD_FAILED",
        )
    if (
        report.get("source_recheck_ledger_source_persistent_loop_validation_status") != "PASS"
        or report.get("source_recheck_ledger_source_persistent_loop_hash_self_check") != "PASS"
        or report.get("source_recheck_ledger_head_cycle_in_persistent_loop") is not True
        or report.get("source_recheck_ledger_source_runtime_input_role") != "PUBLIC_MARKET_DATA_COLLECTION"
        or report.get("source_recheck_ledger_source_public_market_data_hash")
        != report.get("source_recheck_ledger_source_runtime_public_market_data_hash")
        or report.get("source_recheck_ledger_source_canonical_event_count", 0) < 5
        or report.get("source_recheck_ledger_source_runtime_depth_status") != "PASS"
        or report.get("source_recheck_ledger_source_runtime_depth_blocker_code") is not None
        or report.get("source_recheck_ledger_source_runtime_depth_mismatch_count") != 0
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path recheck runtime-depth binding is not clean",
            POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED,
        )
    if (
        report.get("repair_path_status") != POST_RERUN_RECONCILIATION_REPAIR_PATH_STATUS
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("repair_gate_count") != len(REPAIR_GATE_IDS)
        or report.get("satisfied_repair_gate_count") != 0
        or report.get("blocked_repair_gate_count") != len(REPAIR_GATE_IDS)
    ):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path must remain blocked with all repair gates unsatisfied",
            POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )

    gates = report.get("repair_gates")
    if not isinstance(gates, list) or len(gates) != len(REPAIR_GATE_IDS):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            "post-rerun repair path gate count mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    gate_ids = [str(gate.get("gate_id") or "") for gate in gates if isinstance(gate, dict)]
    if tuple(gate_ids) != REPAIR_GATE_IDS:
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            "post-rerun repair path gate ordering mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    for gate in gates:
        if not isinstance(gate, dict):
            return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
                "FAIL",
                "post-rerun repair path gate must be object",
                "SCHEMA_IDENTITY_MISMATCH",
            )
        gate_forbidden = (
            "satisfied",
            "current_evidence_write_allowed",
            "current_ledger_jsonl_write_allowed",
            "latest_runtime_pointer_write_allowed",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        )
        if any(gate.get(field) for field in gate_forbidden):
            return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
                "BLOCKED",
                "post-rerun repair path gate attempted current evidence, live, or scale permission",
                "LIVE_FINAL_GUARD_FAILED",
            )
        if (
            gate.get("gate_status") != "BLOCKED"
            or gate.get("required") is not True
            or gate.get("source_evidence_status") != "MISSING"
            or gate.get("blocking_reason_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or gate.get("blocks_current_evidence") is not True
            or gate.get("blocks_live") is not True
            or gate.get("blocks_scale_up") is not True
        ):
            return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
                "BLOCKED",
                "post-rerun repair path gate lost required blocked state",
                POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
            )
    blockers = report.get("blocker_codes")
    if not isinstance(blockers, list):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "FAIL",
            "post-rerun repair path blocker_codes must be array",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    required_blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if not required_blockers.issubset(set(blockers)):
        return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
            "BLOCKED",
            "post-rerun repair path omitted required live-blocking blockers",
            "LIVE_FINAL_GUARD_FAILED",
        )
    return UpbitPaperPostRerunReconciliationRepairPathValidationResult(
        "PASS",
        "Upbit PAPER post-rerun reconciliation repair path declares blocked repair gates without current evidence/live/scale mutation",
        None,
    )
