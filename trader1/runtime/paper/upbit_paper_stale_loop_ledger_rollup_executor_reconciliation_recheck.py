from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.paper_ledger_rollup import (
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_regeneration_executor import (
    validate_upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report.v1"
)
STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_TRUTH_ROLE = (
    "paper_runtime_stale_loop_ledger_rollup_executor_reconciliation_recheck_truth"
)
STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_NO_CURRENT_EVIDENCE"
)
LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE = (
    "LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_CURRENT_EVIDENCE_BLOCKED"
)
LEDGER_ROLLUP_EXECUTOR_RECHECK_INPUT_SCOPE_BLOCKER_CODE = (
    "LEDGER_ROLLUP_EXECUTOR_RECHECK_INPUT_SCOPE_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash(
    report: dict[str, Any],
) -> str:
    payload = dict(report)
    payload.pop("ledger_rollup_executor_reconciliation_recheck_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _candidate_artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(
            f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
            "ledger_rollup_regeneration_candidates/"
        )
        and normalized.endswith(".paper_ledger_rollup_report.json")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _safe_load_json(path: Path) -> tuple[dict[str, Any] | None, str]:
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
    return value, "PASS"


def _item_reasons(
    *,
    source_item: dict[str, Any],
    artifact_load_status: str,
    artifact_validator_status: str,
    hash_match: bool,
    target_rollup_path_exists: bool,
) -> list[str]:
    reasons = {"CURRENT_EVIDENCE_WRITE_BLOCKED"}
    if source_item.get("candidate_strict_input_scope_blocked"):
        reasons.add("STRICT_LEDGER_INPUT_SCOPE_BLOCKED")
    if source_item.get("candidate_rollup_validator_status") != "PASS":
        reasons.add("SOURCE_CANDIDATE_ROLLUP_NOT_PASS")
    if source_item.get("candidate_rollup_artifact_ready") is not True:
        reasons.add("SOURCE_CANDIDATE_ARTIFACT_NOT_READY")
    if artifact_load_status == "MISSING":
        reasons.add("CANDIDATE_ARTIFACT_MISSING")
    elif artifact_load_status != "PASS":
        reasons.add("CANDIDATE_ARTIFACT_UNREADABLE")
    if artifact_validator_status != "PASS":
        reasons.add("CANDIDATE_ARTIFACT_VALIDATOR_NOT_PASS")
    if not hash_match:
        reasons.add("CANDIDATE_ARTIFACT_HASH_NOT_RECONCILED")
    if not target_rollup_path_exists:
        reasons.add("TARGET_LEDGER_ROLLUP_ARTIFACT_MISSING")
    return sorted(reasons)


def _build_item(*, root: Path, session_id: str, source_item: dict[str, Any], priority_order: int) -> dict[str, Any]:
    candidate_artifact_path = str(source_item.get("candidate_rollup_artifact_path") or "")
    target_rollup_path = str(source_item.get("target_ledger_rollup_path") or "")
    candidate, load_status = _safe_load_json(_rooted(root, candidate_artifact_path))
    artifact_hash = candidate.get("rollup_hash") if isinstance(candidate, dict) else None
    artifact_recomputed_hash = paper_ledger_rollup_hash(candidate) if isinstance(candidate, dict) else None
    hash_self_check = (
        "PASS"
        if isinstance(artifact_hash, str) and artifact_hash == artifact_recomputed_hash
        else "FAIL"
        if isinstance(candidate, dict)
        else "NOT_AVAILABLE"
    )
    if isinstance(candidate, dict):
        artifact_result = validate_paper_ledger_rollup_report(candidate)
        artifact_validator_status = artifact_result.status
        artifact_validator_blocker_code = artifact_result.blocker_code
        artifact_validator_message = artifact_result.message
    else:
        artifact_validator_status = load_status
        artifact_validator_blocker_code = "CANDIDATE_ARTIFACT_MISSING" if load_status == "MISSING" else load_status
        artifact_validator_message = f"candidate artifact load status: {load_status}"
    source_candidate_hash = source_item.get("candidate_rollup_hash")
    artifact_hash_match = (
        isinstance(source_candidate_hash, str)
        and isinstance(artifact_hash, str)
        and source_candidate_hash == artifact_hash
        and artifact_hash == artifact_recomputed_hash
    )
    target_rollup_path_exists = _rooted(root, target_rollup_path).exists()
    source_ready = (
        source_item.get("candidate_rollup_artifact_ready") is True
        and source_item.get("candidate_rollup_validator_status") == "PASS"
        and source_item.get("candidate_strict_input_scope_blocked") is False
    )
    recheck_pass = source_ready and load_status == "PASS" and artifact_validator_status == "PASS" and artifact_hash_match
    if recheck_pass:
        recheck_status = "CANDIDATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED"
        primary_blocker_code = LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE
    elif source_item.get("candidate_strict_input_scope_blocked") is True:
        recheck_status = "BLOCKED_STRICT_LEDGER_INPUT_SCOPE"
        primary_blocker_code = LEDGER_ROLLUP_EXECUTOR_RECHECK_INPUT_SCOPE_BLOCKER_CODE
    elif load_status != "PASS":
        recheck_status = "BLOCKED_CANDIDATE_ARTIFACT_MISSING_OR_UNREADABLE"
        primary_blocker_code = "CANDIDATE_LEDGER_ROLLUP_ARTIFACT_MISSING"
    elif artifact_validator_status != "PASS":
        recheck_status = "BLOCKED_CANDIDATE_ARTIFACT_VALIDATION"
        primary_blocker_code = artifact_validator_blocker_code or "CANDIDATE_LEDGER_ROLLUP_VALIDATOR_NOT_PASS"
    elif not artifact_hash_match:
        recheck_status = "BLOCKED_CANDIDATE_ARTIFACT_HASH_MISMATCH"
        primary_blocker_code = "CANDIDATE_LEDGER_ROLLUP_HASH_NOT_RECONCILED"
    else:
        recheck_status = "BLOCKED_CANDIDATE_SOURCE_NOT_READY"
        primary_blocker_code = source_item.get("primary_blocker_code") or "CANDIDATE_LEDGER_ROLLUP_SOURCE_NOT_READY"
    reason_codes = _item_reasons(
        source_item=source_item,
        artifact_load_status=load_status,
        artifact_validator_status=artifact_validator_status,
        hash_match=artifact_hash_match,
        target_rollup_path_exists=target_rollup_path_exists,
    )
    blocker_codes = sorted(
        {
            LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE,
            primary_blocker_code,
            *reason_codes,
            *(str(code) for code in source_item.get("blocker_codes") or []),
        }
    )
    return {
        "priority_order": priority_order,
        "replacement_loop_id": str(source_item.get("replacement_loop_id") or "UNKNOWN"),
        "source_executor_item_status": source_item.get("executor_item_status"),
        "source_candidate_rollup_validator_status": source_item.get("candidate_rollup_validator_status"),
        "source_candidate_rollup_artifact_ready": source_item.get("candidate_rollup_artifact_ready"),
        "source_candidate_strict_input_scope_blocked": source_item.get("candidate_strict_input_scope_blocked"),
        "source_candidate_rollup_hash": source_candidate_hash,
        "candidate_rollup_artifact_path": candidate_artifact_path,
        "candidate_rollup_artifact_path_allowed": _candidate_artifact_path_allowed(candidate_artifact_path, session_id),
        "candidate_rollup_artifact_exists": isinstance(candidate, dict),
        "candidate_rollup_artifact_load_status": load_status,
        "artifact_rollup_hash": artifact_hash,
        "artifact_recomputed_rollup_hash": artifact_recomputed_hash,
        "artifact_rollup_hash_self_check": hash_self_check,
        "candidate_rollup_hash_match": artifact_hash_match,
        "candidate_rollup_validator_status": artifact_validator_status,
        "candidate_rollup_validator_blocker_code": artifact_validator_blocker_code,
        "candidate_rollup_validator_message": artifact_validator_message,
        "target_ledger_rollup_path": target_rollup_path,
        "target_ledger_rollup_path_exists": target_rollup_path_exists,
        "target_ledger_rollup_hash": source_item.get("target_ledger_rollup_hash"),
        "recheck_status": recheck_status,
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": blocker_codes,
        "recheck_reason_codes": reason_codes,
        "operator_action": "Keep candidate rollup out of current evidence until an explicit promotion guard and reconciliation pass.",
        "candidate_recheck_only": True,
        "candidate_artifact_is_current_evidence": False,
        "candidate_current_evidence_usable": False,
        "target_rollup_write_allowed": False,
        "current_evidence_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
    *,
    root: Path,
    ledger_rollup_regeneration_executor_report: dict[str, Any],
    ledger_rollup_executor_reconciliation_recheck_id: str = (
        "upbit-paper-stale-loop-ledger-rollup-executor-reconciliation-recheck"
    ),
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report(
        ledger_rollup_regeneration_executor_report
    )
    session_id = str(ledger_rollup_regeneration_executor_report.get("session_id", "UNKNOWN"))
    source_items = [
        item for item in ledger_rollup_regeneration_executor_report.get("items", []) if isinstance(item, dict)
    ]
    items = [
        _build_item(root=root, session_id=session_id, source_item=item, priority_order=index)
        for index, item in enumerate(source_items, start=1)
    ]
    pass_count = sum(1 for item in items if item["recheck_status"] == "CANDIDATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED")
    blocked_count = len(items) - pass_count
    artifact_exists_count = sum(1 for item in items if item["candidate_rollup_artifact_exists"])
    artifact_validator_pass_count = sum(1 for item in items if item["candidate_rollup_validator_status"] == "PASS")
    hash_match_count = sum(1 for item in items if item["candidate_rollup_hash_match"])
    strict_input_scope_blocked_count = sum(1 for item in items if item["source_candidate_strict_input_scope_blocked"])
    source_ready_count = sum(1 for item in items if item["source_candidate_rollup_artifact_ready"])
    target_rollup_exists_count = sum(1 for item in items if item["target_ledger_rollup_path_exists"])
    blocker_codes = {LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "LEDGER_ROLLUP_REGENERATION_EXECUTOR_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if strict_input_scope_blocked_count:
        blocker_codes.add(LEDGER_ROLLUP_EXECUTOR_RECHECK_INPUT_SCOPE_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "ledger_rollup_executor_reconciliation_recheck_id": ledger_rollup_executor_reconciliation_recheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_TRUTH_ROLE,
        "ledger_rollup_executor_reconciliation_recheck_role": (
            STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_ROLE
        ),
        "source_ledger_rollup_regeneration_executor_hash": ledger_rollup_regeneration_executor_report.get(
            "ledger_rollup_regeneration_executor_hash"
        ),
        "source_ledger_rollup_regeneration_executor_status": ledger_rollup_regeneration_executor_report.get(
            "executor_status"
        ),
        "source_ledger_rollup_regeneration_executor_validator_status": source_result.status,
        "source_candidate_rollup_attempt_count": ledger_rollup_regeneration_executor_report.get(
            "candidate_rollup_attempt_count"
        ),
        "item_count": len(items),
        "candidate_recheck_attempt_count": len(items),
        "candidate_recheck_pass_count": pass_count,
        "candidate_recheck_blocked_count": blocked_count,
        "source_candidate_rollup_artifact_ready_count": source_ready_count,
        "candidate_rollup_artifact_exists_count": artifact_exists_count,
        "candidate_rollup_artifact_validator_pass_count": artifact_validator_pass_count,
        "candidate_rollup_hash_match_count": hash_match_count,
        "strict_input_scope_blocked_count": strict_input_scope_blocked_count,
        "target_rollup_artifact_exists_count": target_rollup_exists_count,
        "candidate_current_evidence_usable_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "recheck_status": "BLOCKED",
        "primary_blocker_code": LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Resolve strict scoped ledger inputs and run an explicit promotion guard before any current evidence closure.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_recheck_only": True,
        "candidate_artifact_is_current_evidence": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
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
        "ledger_rollup_executor_reconciliation_recheck_hash": "",
    }
    report["ledger_rollup_executor_reconciliation_recheck_hash"] = (
        upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash(report)
    )
    return report


def write_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "ledger_rollup_executor_reconciliation_recheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "ledger_rollup_executor_reconciliation_recheck_role",
        "source_ledger_rollup_regeneration_executor_hash",
        "source_ledger_rollup_regeneration_executor_status",
        "source_ledger_rollup_regeneration_executor_validator_status",
        "source_candidate_rollup_attempt_count",
        "item_count",
        "candidate_recheck_attempt_count",
        "candidate_recheck_pass_count",
        "candidate_recheck_blocked_count",
        "source_candidate_rollup_artifact_ready_count",
        "candidate_rollup_artifact_exists_count",
        "candidate_rollup_artifact_validator_pass_count",
        "candidate_rollup_hash_match_count",
        "strict_input_scope_blocked_count",
        "target_rollup_artifact_exists_count",
        "candidate_current_evidence_usable_count",
        "target_rollup_write_allowed_count",
        "current_evidence_write_allowed_count",
        "recheck_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_recheck_only",
        "candidate_artifact_is_current_evidence",
        "current_evidence_write_allowed",
        "target_rollup_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
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
        "ledger_rollup_executor_reconciliation_recheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "FAIL", f"ledger-rollup executor recheck missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup executor recheck schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_rollup_executor_reconciliation_recheck_hash") != (
        upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_hash(report)
    ):
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup executor recheck hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup executor recheck scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
        "candidate_artifact_is_current_evidence",
        "current_evidence_write_allowed",
        "target_rollup_write_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
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
    if any(report.get(field) is not False for field in false_fields):
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup executor recheck attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if report.get("display_only") is not True or report.get("dashboard_truth_only") is not True or report.get("paper_only") is not True or report.get("candidate_recheck_only") is not True:
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup executor recheck must stay candidate-recheck-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("candidate_current_evidence_usable_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "BLOCKED", "ledger-rollup executor recheck exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("candidate_recheck_attempt_count") != len(items):
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "FAIL", "ledger-rollup executor recheck item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    expected = {
        "candidate_recheck_pass_count": 0,
        "candidate_recheck_blocked_count": 0,
        "source_candidate_rollup_artifact_ready_count": 0,
        "candidate_rollup_artifact_exists_count": 0,
        "candidate_rollup_artifact_validator_pass_count": 0,
        "candidate_rollup_hash_match_count": 0,
        "strict_input_scope_blocked_count": 0,
        "target_rollup_artifact_exists_count": 0,
    }
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                "FAIL", "ledger-rollup executor recheck item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                "FAIL", "ledger-rollup executor recheck priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("candidate_rollup_artifact_path", "target_ledger_rollup_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                    "BLOCKED", f"ledger-rollup executor recheck {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        if item.get("candidate_rollup_artifact_path_allowed") is not _candidate_artifact_path_allowed(
            str(item.get("candidate_rollup_artifact_path") or ""), session_id
        ):
            return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                "FAIL", "ledger-rollup executor recheck candidate path allowance mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        item_false_fields = (
            "candidate_artifact_is_current_evidence",
            "candidate_current_evidence_usable",
            "target_rollup_write_allowed",
            "current_evidence_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        )
        if any(item.get(field) for field in item_false_fields):
            return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                "BLOCKED", "ledger-rollup executor recheck item attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        if item.get("source_candidate_rollup_artifact_ready"):
            expected["source_candidate_rollup_artifact_ready_count"] += 1
        if item.get("candidate_rollup_artifact_exists"):
            expected["candidate_rollup_artifact_exists_count"] += 1
        if item.get("candidate_rollup_validator_status") == "PASS":
            expected["candidate_rollup_artifact_validator_pass_count"] += 1
        if item.get("candidate_rollup_hash_match"):
            expected["candidate_rollup_hash_match_count"] += 1
        if item.get("source_candidate_strict_input_scope_blocked"):
            expected["strict_input_scope_blocked_count"] += 1
        if item.get("target_ledger_rollup_path_exists"):
            expected["target_rollup_artifact_exists_count"] += 1
        if item.get("recheck_status") == "CANDIDATE_RECHECK_PASS_CURRENT_EVIDENCE_BLOCKED":
            expected["candidate_recheck_pass_count"] += 1
            if item.get("primary_blocker_code") != LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE:
                return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                    "FAIL", "PASS candidate recheck must remain current-evidence blocked", "SCHEMA_IDENTITY_MISMATCH"
                )
        else:
            expected["candidate_recheck_blocked_count"] += 1
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
                "FAIL", f"ledger-rollup executor recheck count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("recheck_status") != "BLOCKED" or report.get("primary_blocker_code") != LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE:
        return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
            "BLOCKED",
            "ledger-rollup executor recheck must remain blocked before current-evidence promotion",
            LEDGER_ROLLUP_EXECUTOR_RECONCILIATION_RECHECK_BLOCKER_CODE,
        )
    return UpbitPaperStaleLoopLedgerRollupExecutorReconciliationRecheckValidationResult(
        "PASS",
        "Upbit PAPER stale-loop ledger-rollup executor recheck validates candidate artifacts without current evidence writes",
        None,
    )
