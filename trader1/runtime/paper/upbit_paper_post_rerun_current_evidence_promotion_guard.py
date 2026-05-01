from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE,
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
    upbit_paper_post_rerun_ledger_rollup_reconciliation_hash,
    validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1"
)
POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_REQUIRED_BLOCKER_CODE = (
    "POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_REQUIRED"
)
POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE = "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED"
RERUN_CANDIDATE_PROMOTION_HASH_MISMATCH_BLOCKER_CODE = (
    "RERUN_CANDIDATE_PROMOTION_HASH_MISMATCH_RECONCILIATION_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_rerun_current_evidence_promotion_guard_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("promotion_guard_hash", None)
    return _sha256_json(payload)


def _candidate_rollup_hash(candidate: dict[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("candidate_rollup_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/") and ".." not in parts and "/live/" not in normalized


def _candidate_rollup_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates_post_rollup/" in normalized


def _staging_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return _artifact_path_allowed(normalized, session_id) and "/paper_runtime/rerun_candidates/" in normalized


def _current_ledger_path(session_id: str, cycle_id: str) -> str:
    safe_cycle_id = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in str(cycle_id))
    return f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/{safe_cycle_id}.paper_ledger_events.jsonl"


def _current_ledger_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        _artifact_path_allowed(normalized, session_id)
        and normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/cycles/")
        and normalized.endswith(".paper_ledger_events.jsonl")
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


def _source_reconciliation_file_binding(
    *,
    root: Path,
    relative_path: str,
    expected_hash: Any,
) -> dict[str, Any]:
    source, source_error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            "source_post_rerun_reconciliation_file_load_status": str(source_error or "UNKNOWN"),
            "source_post_rerun_reconciliation_file_hash": None,
            "source_post_rerun_reconciliation_file_recomputed_hash": None,
            "source_post_rerun_reconciliation_file_hash_match": False,
        }
    file_hash = source.get("post_rerun_reconciliation_hash")
    recomputed_hash = upbit_paper_post_rerun_ledger_rollup_reconciliation_hash(source)
    hash_match = bool(file_hash == expected_hash == recomputed_hash)
    return {
        "source_post_rerun_reconciliation_file_load_status": "PASS" if hash_match else "HASH_MISMATCH",
        "source_post_rerun_reconciliation_file_hash": file_hash,
        "source_post_rerun_reconciliation_file_recomputed_hash": recomputed_hash,
        "source_post_rerun_reconciliation_file_hash_match": hash_match,
    }


def _build_item(*, root: Path, session_id: str, source_item: dict[str, Any]) -> dict[str, Any]:
    candidate_path = str(source_item.get("candidate_rollup_artifact_path") or "")
    candidate, candidate_error = _safe_load_json(_rooted(root, candidate_path))
    source_candidate_hash = source_item.get("candidate_rollup_hash")
    candidate_hash = candidate.get("candidate_rollup_hash") if isinstance(candidate, dict) else None
    candidate_recomputed_hash = _candidate_rollup_hash(candidate) if isinstance(candidate, dict) else None
    hash_self_check = "PASS" if candidate_hash == candidate_recomputed_hash else "FAIL"
    path_scope_status = "MATCH" if _candidate_rollup_path_allowed(candidate_path, session_id) else "MISMATCH"
    staged_runtime_path = source_item.get("staged_runtime_cycle_path") if isinstance(source_item.get("staged_runtime_cycle_path"), str) else ""
    staged_ledger_path = source_item.get("staged_ledger_jsonl_path") if isinstance(source_item.get("staged_ledger_jsonl_path"), str) else ""
    staged_writer_path = source_item.get("staged_writer_report_path") if isinstance(source_item.get("staged_writer_report_path"), str) else ""
    staged_scope_status = (
        "MATCH"
        if _staging_path_allowed(staged_runtime_path, session_id)
        and _staging_path_allowed(staged_ledger_path, session_id)
        and _staging_path_allowed(staged_writer_path, session_id)
        else "MISMATCH"
    )
    candidate_verified = (
        isinstance(candidate, dict)
        and candidate_error is None
        and path_scope_status == "MATCH"
        and staged_scope_status == "MATCH"
        and candidate.get("candidate_rollup_role") == POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
        and candidate.get("candidate_rollup_status") == "PASS"
        and candidate_hash == source_candidate_hash
        and hash_self_check == "PASS"
        and not candidate.get("candidate_current_evidence_usable")
        and not candidate.get("current_evidence_mutation_allowed")
        and not candidate.get("live_order_allowed")
        and not candidate.get("scale_up_allowed")
    )
    if candidate_verified:
        review_status = "REVIEW_READY_WRITE_BLOCKED"
        item_blocker = POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
    elif path_scope_status != "MATCH" or staged_scope_status != "MATCH":
        review_status = "BLOCKED_SCOPE_MISMATCH"
        item_blocker = "SNAPSHOT_SCOPE_MISMATCH"
    elif candidate_hash != source_candidate_hash or hash_self_check != "PASS":
        review_status = "BLOCKED_HASH_MISMATCH"
        item_blocker = RERUN_CANDIDATE_PROMOTION_HASH_MISMATCH_BLOCKER_CODE
    else:
        review_status = "BLOCKED_CANDIDATE_VALIDATION"
        item_blocker = candidate.get("primary_blocker_code") if isinstance(candidate, dict) else str(candidate_error or "MEASUREMENT_MISSING")
    cycle_id = str(source_item.get("cycle_id") or (candidate or {}).get("cycle_id") or "UNKNOWN")
    planned_current_ledger_path = _current_ledger_path(session_id, cycle_id)
    return {
        "replacement_loop_id": str(source_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": cycle_id,
        "source_candidate_classification": str(source_item.get("candidate_classification") or "UNKNOWN"),
        "source_item_blocker_code": source_item.get("item_blocker_code"),
        "candidate_rollup_artifact_path": candidate_path,
        "candidate_rollup_load_status": "PASS" if candidate is not None else str(candidate_error or "UNKNOWN"),
        "candidate_rollup_path_scope_status": path_scope_status,
        "candidate_rollup_role": candidate.get("candidate_rollup_role") if isinstance(candidate, dict) else None,
        "source_candidate_rollup_hash": source_candidate_hash,
        "candidate_rollup_hash": candidate_hash,
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": hash_self_check,
        "candidate_rollup_status": candidate.get("candidate_rollup_status") if isinstance(candidate, dict) else None,
        "candidate_ledger_jsonl_count": candidate.get("ledger_jsonl_count") if isinstance(candidate, dict) else None,
        "candidate_ledger_event_count": candidate.get("ledger_event_count") if isinstance(candidate, dict) else None,
        "candidate_filled_order_count": candidate.get("filled_order_count") if isinstance(candidate, dict) else None,
        "candidate_empty_no_trade_ledger": bool(candidate.get("empty_no_trade_ledger")) if isinstance(candidate, dict) else False,
        "staged_runtime_cycle_path": staged_runtime_path,
        "staged_ledger_jsonl_path": staged_ledger_path,
        "staged_writer_report_path": staged_writer_path,
        "staged_artifact_scope_status": staged_scope_status,
        "planned_current_ledger_jsonl_path": planned_current_ledger_path,
        "planned_current_ledger_path_scope_status": "MATCH"
        if _current_ledger_path_allowed(planned_current_ledger_path, session_id)
        else "MISMATCH",
        "candidate_rollup_verified": candidate_verified,
        "promotion_review_ready": candidate_verified,
        "promotion_review_status": review_status,
        "item_blocker_code": item_blocker,
        "recommended_operator_action": "Do not write current evidence in this guard. Use a separate reviewed writer patch only if policy explicitly permits PAPER current-evidence mutation.",
        "candidate_rollup": candidate if isinstance(candidate, dict) else {},
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "current_evidence_mutation_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "live_permission_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_upbit_paper_post_rerun_current_evidence_promotion_guard_report(
    *,
    root: Path,
    post_rerun_reconciliation_report: dict[str, Any],
    source_post_rerun_reconciliation_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json",
    guard_id: str = "upbit-paper-post-rerun-current-evidence-promotion-guard",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_post_rerun_ledger_rollup_reconciliation_report(post_rerun_reconciliation_report)
    session_id = str(post_rerun_reconciliation_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in post_rerun_reconciliation_report.get("items", [])
        if isinstance(item, dict) and item.get("candidate_rollup_status") == "PASS"
    ]
    items = [
        _build_item(root=root, session_id=session_id, source_item=item)
        for item in source_items
    ] if source_result.status == "PASS" else []
    verified_count = sum(1 for item in items if item.get("candidate_rollup_verified"))
    review_ready_count = sum(1 for item in items if item.get("promotion_review_ready"))
    hash_mismatch_count = sum(1 for item in items if item.get("promotion_review_status") == "BLOCKED_HASH_MISMATCH")
    scope_mismatch_count = sum(1 for item in items if item.get("promotion_review_status") == "BLOCKED_SCOPE_MISMATCH")
    blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_CODE,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if source_result.status != "PASS":
        blockers.add(source_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")
    for item in items:
        blockers.add(str(item.get("item_blocker_code") or "UNKNOWN_BLOCKED"))
    source_hash = post_rerun_reconciliation_report.get("post_rerun_reconciliation_hash")
    source_file_binding = _source_reconciliation_file_binding(
        root=root,
        relative_path=source_post_rerun_reconciliation_path,
        expected_hash=source_hash,
    )
    if source_file_binding["source_post_rerun_reconciliation_file_load_status"] != "PASS":
        blockers.add("POST_RERUN_SOURCE_RECONCILIATION_FILE_BINDING_REQUIRED")
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "promotion_guard_id": guard_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_TRUTH_ROLE,
        "source_post_rerun_reconciliation_path": source_post_rerun_reconciliation_path,
        "source_post_rerun_reconciliation_hash": source_hash,
        **source_file_binding,
        "source_post_rerun_ledger_rollup_status": post_rerun_reconciliation_report.get("post_rerun_ledger_rollup_status"),
        "source_post_rerun_reconciliation_status": post_rerun_reconciliation_report.get("post_rerun_reconciliation_status"),
        "source_primary_blocker_code": post_rerun_reconciliation_report.get("primary_blocker_code"),
        "source_candidate_item_count": int(post_rerun_reconciliation_report.get("candidate_item_count") or 0),
        "source_candidate_rollup_pass_count": int(post_rerun_reconciliation_report.get("candidate_rollup_pass_count") or 0),
        "candidate_item_count": len(items),
        "candidate_rollup_verified_count": verified_count,
        "candidate_rollup_hash_mismatch_count": hash_mismatch_count,
        "candidate_rollup_scope_mismatch_count": scope_mismatch_count,
        "promotion_review_ready_count": review_ready_count,
        "promotion_review_blocked_count": len(items),
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "candidate_current_evidence_blocked_count": len(items),
        "promotion_guard_status": "BLOCKED",
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocker_codes": sorted(blockers),
        "items": items,
        "operator_next_action": "Keep post-rerun rollups as candidate evidence only. This guard does not write current ledger or runtime pointers.",
        "current_evidence_mutation_allowed": False,
        "current_evidence_write_allowed": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "source_delete_allowed": False,
        "actual_rerun_executed": False,
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
        "promotion_guard_hash": "",
    }
    report["promotion_guard_hash"] = upbit_paper_post_rerun_current_evidence_promotion_guard_hash(report)
    return report


def write_upbit_paper_post_rerun_current_evidence_promotion_guard_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_current_evidence_promotion_guard_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "promotion_guard_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "source_post_rerun_reconciliation_path",
        "source_post_rerun_reconciliation_hash",
        "source_post_rerun_reconciliation_file_load_status",
        "source_post_rerun_reconciliation_file_hash",
        "source_post_rerun_reconciliation_file_recomputed_hash",
        "source_post_rerun_reconciliation_file_hash_match",
        "source_post_rerun_ledger_rollup_status",
        "source_post_rerun_reconciliation_status",
        "source_primary_blocker_code",
        "source_candidate_item_count",
        "source_candidate_rollup_pass_count",
        "candidate_item_count",
        "candidate_rollup_verified_count",
        "candidate_rollup_hash_mismatch_count",
        "candidate_rollup_scope_mismatch_count",
        "promotion_review_ready_count",
        "promotion_review_blocked_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "candidate_current_evidence_blocked_count",
        "promotion_guard_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "current_evidence_mutation_allowed",
        "current_evidence_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_rerun_executed",
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
        "promotion_guard_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", f"post-rerun promotion guard missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_SCHEMA_ID:
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("promotion_guard_hash") != upbit_paper_post_rerun_current_evidence_promotion_guard_hash(report):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion guard scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_TRUTH_ROLE:
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion guard cannot claim writer or live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
        "current_evidence_write_allowed",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
        "persistent_loop_mutation_allowed",
        "source_delete_allowed",
        "actual_rerun_executed",
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
    if any(report.get(field) for field in forbidden):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion guard created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if report.get("source_post_rerun_ledger_rollup_status") != "PASS":
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "source post-rerun ledger rollup must PASS before promotion review", "POST_RERUN_LEDGER_ROLLUP_REQUIRED")
    if (
        report.get("source_post_rerun_reconciliation_status") != "BLOCKED"
        or report.get("source_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
    ):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "source post-rerun reconciliation boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("promotion_guard_status") != "BLOCKED" or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion guard must remain blocked and review-only", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("current_evidence_write_allowed_count") != 0 or report.get("candidate_current_evidence_usable_count") != 0:
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion guard exposed current evidence write/use", "LIVE_FINAL_GUARD_FAILED")
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_post_rerun_reconciliation_path") or ""), session_id):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "source post-rerun reconciliation path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("source_post_rerun_reconciliation_file_load_status") != "PASS"
        or report.get("source_post_rerun_reconciliation_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult(
            "BLOCKED",
            "source post-rerun reconciliation file binding is missing or mismatched",
            POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if (
        report.get("source_post_rerun_reconciliation_file_hash") != report.get("source_post_rerun_reconciliation_hash")
        or report.get("source_post_rerun_reconciliation_file_recomputed_hash") != report.get("source_post_rerun_reconciliation_hash")
    ):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult(
            "FAIL",
            "source post-rerun reconciliation file hash does not match source report hash",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("candidate_item_count") != len(items):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion guard item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    expected = {
        "candidate_rollup_verified_count": sum(1 for item in items if isinstance(item, dict) and item.get("candidate_rollup_verified")),
        "candidate_rollup_hash_mismatch_count": sum(1 for item in items if isinstance(item, dict) and item.get("promotion_review_status") == "BLOCKED_HASH_MISMATCH"),
        "candidate_rollup_scope_mismatch_count": sum(1 for item in items if isinstance(item, dict) and item.get("promotion_review_status") == "BLOCKED_SCOPE_MISMATCH"),
        "promotion_review_ready_count": sum(1 for item in items if isinstance(item, dict) and item.get("promotion_review_ready")),
        "promotion_review_blocked_count": len(items),
        "candidate_current_evidence_blocked_count": len(items),
    }
    for field, value in expected.items():
        if report.get(field) != value:
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", f"post-rerun promotion guard count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_candidate_rollup_pass_count") != len(items) or report.get("source_candidate_item_count") != len(items):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion guard source count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(report.get("blocker_codes") or []):
        return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion guard missing reconciliation blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion guard item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "promotion guard candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        for path_field in ("staged_runtime_cycle_path", "staged_ledger_jsonl_path", "staged_writer_report_path"):
            if not _staging_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", f"promotion guard {path_field} escaped staging namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "promotion guard planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if item.get("planned_current_ledger_path_scope_status") != "MATCH":
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "promotion guard planned current ledger path scope status mismatch", "SNAPSHOT_SCOPE_MISMATCH")
        item_forbidden = (
            "candidate_current_evidence_usable",
            "current_evidence_write_allowed",
            "current_evidence_mutation_allowed",
            "current_ledger_jsonl_write_allowed",
            "latest_runtime_pointer_write_allowed",
            "persistent_loop_mutation_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "long_run_evidence_eligible",
            "promotion_eligible",
            "live_permission_created",
            "live_order_ready",
            "live_order_allowed",
            "can_live_trade",
            "scale_up_allowed",
        )
        if any(item.get(field) for field in item_forbidden):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH")
        if (
            item.get("candidate_rollup_role") != POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
            or candidate.get("candidate_rollup_role") != POST_RERUN_LEDGER_ROLLUP_CANDIDATE_ROLE
            or item.get("source_candidate_rollup_hash") != item.get("candidate_rollup_hash")
        ):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion candidate source hash/role mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            candidate.get("candidate_rollup_hash") != item.get("candidate_rollup_hash")
            or _candidate_rollup_hash(candidate) != item.get("candidate_rollup_recomputed_hash")
            or item.get("candidate_rollup_hash_self_check") != "PASS"
            or candidate.get("candidate_rollup_status") != "PASS"
        ):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "post-rerun promotion candidate hash/status mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if (
            candidate.get("candidate_current_evidence_usable")
            or candidate.get("current_evidence_mutation_allowed")
            or candidate.get("live_order_allowed")
            or candidate.get("scale_up_allowed")
        ):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("BLOCKED", "post-rerun promotion candidate attempted forbidden permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("candidate_rollup_verified") and (
            item.get("promotion_review_status") != "REVIEW_READY_WRITE_BLOCKED"
            or item.get("item_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        ):
            return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult("FAIL", "verified promotion candidate must remain write-blocked", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperPostRerunCurrentEvidencePromotionGuardValidationResult(
        "PASS",
        "Upbit PAPER post-rerun promotion guard verifies candidate rollups but keeps current evidence writes blocked",
        None,
    )
