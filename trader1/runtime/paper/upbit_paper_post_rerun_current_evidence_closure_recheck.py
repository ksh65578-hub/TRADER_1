from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    upbit_paper_ledger_idempotency_runtime_evidence_hash,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
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


UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1"
)
POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_TRUTH_ROLE = (
    "PAPER_POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS = (
    "BLOCKED_POST_RERUN_CLOSURE_CONFIRMED"
)
POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_LEDGER_BLOCKED_STATUS = (
    "BLOCKED_CURRENT_LEDGER_IDEMPOTENCY_RECHECK_REQUIRED"
)
POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_OUTCOME = (
    "LEDGER_IDEMPOTENCY_PASS_BUT_POST_RERUN_CLOSURE_BLOCKS_CURRENT_EVIDENCE"
)
POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED = (
    "POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_post_rerun_current_evidence_closure_recheck_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("recheck_hash", None)
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


def _ledger_idempotency_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        _runtime_path_allowed(normalized, session_id)
        and normalized.endswith("/ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json")
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


def build_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    closure_report_path: str | None = None,
    ledger_idempotency_report_path: str | None = None,
    recheck_id: str = "upbit-paper-post-rerun-current-evidence-closure-recheck",
) -> dict[str, Any]:
    root = Path(root).resolve()
    closure_path = closure_report_path or (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
    )
    ledger_path = ledger_idempotency_report_path or (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/ledger/"
        "upbit_paper_ledger_idempotency_runtime_evidence_report.json"
    )

    closure_binding = _load_source(
        root=root,
        relative_path=closure_path,
        session_id=session_id,
        path_checker=_closure_path_allowed,
        hash_field="closure_hash",
        hash_func=upbit_paper_post_rerun_resolution_current_evidence_closure_hash,
    )
    ledger_binding = _load_source(
        root=root,
        relative_path=ledger_path,
        session_id=session_id,
        path_checker=_ledger_idempotency_path_allowed,
        hash_field="evidence_hash",
        hash_func=upbit_paper_ledger_idempotency_runtime_evidence_hash,
    )
    closure = closure_binding["source"]
    ledger = ledger_binding["source"]
    closure_result = validate_upbit_paper_post_rerun_resolution_current_evidence_closure_report(closure)
    ledger_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(ledger)

    blocker_codes = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if closure_binding["file_load_status"] != "PASS" or not closure_binding["hash_match"]:
        blocker_codes.add(POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED)
    if ledger_binding["file_load_status"] != "PASS" or not ledger_binding["hash_match"]:
        blocker_codes.add(POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED)
    if closure_result.status != "PASS":
        blocker_codes.add(closure_result.blocker_code or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if ledger_result.status != "PASS":
        blocker_codes.add(ledger_result.blocker_code or "RECONCILIATION_REQUIRED")

    ledger_duplicate_total = (
        int(ledger.get("duplicate_event_id_count") or 0)
        + int(ledger.get("duplicate_dedup_key_count") or 0)
        + int(ledger.get("duplicate_semantic_event_count") or 0)
        + int(ledger.get("duplicate_filled_order_key_count") or 0)
    )
    ledger_pass = (
        ledger_result.status == "PASS"
        and ledger.get("runtime_evidence_status") == "PASS"
        and ledger.get("reconciliation_status") == "PASS"
        and ledger.get("idempotency_status") == "PASS"
        and ledger.get("portfolio_provenance_status") == "PASS"
    )
    closure_confirmed = (
        closure_result.status == "PASS"
        and closure.get("closure_status") == POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS
        and closure.get("primary_blocker_code") == POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        and int(closure.get("current_evidence_write_allowed_count") or 0) == 0
        and closure.get("current_evidence_write_allowed") is False
    )
    recheck_status = (
        POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS
        if ledger_pass and closure_confirmed
        else POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_LEDGER_BLOCKED_STATUS
    )

    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "recheck_id": recheck_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_TRUTH_ROLE,
        "source_closure_path": closure_path,
        "source_closure_hash": closure_binding["source_hash"],
        "source_closure_recomputed_hash": closure_binding["source_recomputed_hash"],
        "source_closure_file_load_status": closure_binding["file_load_status"],
        "source_closure_file_hash_match": bool(closure_binding["hash_match"]),
        "source_closure_validation_status": closure_result.status,
        "source_closure_blocker_code": closure_result.blocker_code,
        "source_ledger_idempotency_path": ledger_path,
        "source_ledger_idempotency_hash": ledger_binding["source_hash"],
        "source_ledger_idempotency_recomputed_hash": ledger_binding["source_recomputed_hash"],
        "source_ledger_idempotency_file_load_status": ledger_binding["file_load_status"],
        "source_ledger_idempotency_file_hash_match": bool(ledger_binding["hash_match"]),
        "source_ledger_idempotency_validation_status": ledger_result.status,
        "source_ledger_idempotency_blocker_code": ledger_result.blocker_code,
        "closure_status": str(closure.get("closure_status") or "NOT_LOADED"),
        "closure_primary_blocker_code": str(closure.get("primary_blocker_code") or "NOT_LOADED"),
        "closure_closed_item_count": int(closure.get("closed_item_count") or 0),
        "closure_current_evidence_closed_count": int(closure.get("current_evidence_closed_count") or 0),
        "closure_current_evidence_write_allowed_count": int(closure.get("current_evidence_write_allowed_count") or 0),
        "closure_candidate_current_evidence_usable_count": int(closure.get("candidate_current_evidence_usable_count") or 0),
        "ledger_runtime_evidence_status": str(ledger.get("runtime_evidence_status") or "NOT_LOADED"),
        "ledger_reconciliation_status": str(ledger.get("reconciliation_status") or "NOT_LOADED"),
        "ledger_idempotency_status": str(ledger.get("idempotency_status") or "NOT_LOADED"),
        "ledger_portfolio_provenance_status": str(ledger.get("portfolio_provenance_status") or "NOT_LOADED"),
        "ledger_source_ledger_jsonl_count": int(ledger.get("source_ledger_jsonl_count") or 0),
        "ledger_recomputed_ledger_event_count": int(ledger.get("recomputed_ledger_event_count") or 0),
        "ledger_duplicate_total_count": ledger_duplicate_total,
        "ledger_mismatch_count": int(ledger.get("mismatch_count") or 0),
        "recheck_status": recheck_status,
        "recheck_outcome": POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_OUTCOME,
        "current_evidence_bridge_status": "BLOCKED_BY_POST_RERUN_CLOSURE",
        "portfolio_truth_recheck_status": (
            "LEDGER_PROVENANCE_PASS_BUT_OPERATOR_CURRENT_EVIDENCE_BLOCKED"
            if ledger_pass
            else "LEDGER_PROVENANCE_NOT_VERIFIED_FOR_OPERATOR_CURRENT_EVIDENCE"
        ),
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "recheck_next_action": (
            "Keep ledger idempotency evidence as display-only support and rebuild a separate validated "
            "current ledger/reconciliation path before treating portfolio truth as operator-current evidence."
        ),
        "post_rerun_override_attempted": False,
        "post_rerun_override_allowed": False,
        "current_evidence_write_authorized": False,
        "current_evidence_write_allowed": False,
        "candidate_current_evidence_usable": False,
        "current_ledger_jsonl_write_allowed": False,
        "latest_runtime_pointer_write_allowed": False,
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
        "recheck_hash": "",
    }
    report["recheck_hash"] = upbit_paper_post_rerun_current_evidence_closure_recheck_hash(report)
    return report


def write_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_current_evidence_closure_recheck_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "recheck_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "source_closure_path",
        "source_closure_hash",
        "source_closure_recomputed_hash",
        "source_closure_file_load_status",
        "source_closure_file_hash_match",
        "source_closure_validation_status",
        "source_closure_blocker_code",
        "source_ledger_idempotency_path",
        "source_ledger_idempotency_hash",
        "source_ledger_idempotency_recomputed_hash",
        "source_ledger_idempotency_file_load_status",
        "source_ledger_idempotency_file_hash_match",
        "source_ledger_idempotency_validation_status",
        "source_ledger_idempotency_blocker_code",
        "closure_status",
        "closure_primary_blocker_code",
        "closure_closed_item_count",
        "closure_current_evidence_closed_count",
        "closure_current_evidence_write_allowed_count",
        "closure_candidate_current_evidence_usable_count",
        "ledger_runtime_evidence_status",
        "ledger_reconciliation_status",
        "ledger_idempotency_status",
        "ledger_portfolio_provenance_status",
        "ledger_source_ledger_jsonl_count",
        "ledger_recomputed_ledger_event_count",
        "ledger_duplicate_total_count",
        "ledger_mismatch_count",
        "recheck_status",
        "recheck_outcome",
        "current_evidence_bridge_status",
        "portfolio_truth_recheck_status",
        "primary_blocker_code",
        "blocker_codes",
        "recheck_next_action",
        "post_rerun_override_attempted",
        "post_rerun_override_allowed",
        "current_evidence_write_authorized",
        "current_evidence_write_allowed",
        "candidate_current_evidence_usable",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
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
        "recheck_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "FAIL",
            f"post-rerun current-evidence closure recheck missing fields: {missing}",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SCHEMA_ID:
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "FAIL",
            "post-rerun current-evidence closure recheck schema_id mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("recheck_hash") != upbit_paper_post_rerun_current_evidence_closure_recheck_hash(report):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "FAIL",
            "post-rerun current-evidence closure recheck hash mismatch",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun current-evidence closure recheck scope must remain UPBIT/KRW_SPOT/PAPER",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if report.get("truth_role") != POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_TRUTH_ROLE:
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun current-evidence closure recheck cannot claim writer or live truth",
            "LIVE_FINAL_GUARD_FAILED",
        )

    forbidden = (
        "post_rerun_override_attempted",
        "post_rerun_override_allowed",
        "current_evidence_write_authorized",
        "current_evidence_write_allowed",
        "candidate_current_evidence_usable",
        "current_ledger_jsonl_write_allowed",
        "latest_runtime_pointer_write_allowed",
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
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun current-evidence closure recheck created forbidden permission or mutation",
            "LIVE_FINAL_GUARD_FAILED",
        )

    session_id = str(report.get("session_id"))
    if not _closure_path_allowed(str(report.get("source_closure_path") or ""), session_id):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun closure source path escaped PAPER namespace",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if not _ledger_idempotency_path_allowed(str(report.get("source_ledger_idempotency_path") or ""), session_id):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "ledger idempotency source path escaped PAPER namespace",
            "SNAPSHOT_SCOPE_MISMATCH",
        )
    if (
        report.get("source_closure_file_load_status") != "PASS"
        or report.get("source_closure_file_hash_match") is not True
        or report.get("source_ledger_idempotency_file_load_status") != "PASS"
        or report.get("source_ledger_idempotency_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun closure recheck source binding is missing or mismatched",
            POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_SOURCE_BINDING_REQUIRED,
        )
    if (
        report.get("source_closure_hash") != report.get("source_closure_recomputed_hash")
        or report.get("source_ledger_idempotency_hash") != report.get("source_ledger_idempotency_recomputed_hash")
    ):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "FAIL",
            "post-rerun closure recheck source hash fields do not match",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    if report.get("source_closure_validation_status") != "PASS":
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "source closure report did not validate PASS",
            report.get("source_closure_blocker_code") or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if report.get("source_ledger_idempotency_validation_status") != "PASS":
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "source ledger idempotency evidence did not validate PASS",
            report.get("source_ledger_idempotency_blocker_code") or "RECONCILIATION_REQUIRED",
        )
    if (
        report.get("closure_status") != POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_STATUS
        or report.get("closure_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("closure_closed_item_count", 0) <= 0
        or report.get("closure_current_evidence_closed_count") != report.get("closure_closed_item_count")
        or report.get("closure_current_evidence_write_allowed_count") != 0
        or report.get("closure_candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun closure source no longer confirms current-evidence block",
            POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        )
    if (
        report.get("ledger_runtime_evidence_status") != "PASS"
        or report.get("ledger_reconciliation_status") != "PASS"
        or report.get("ledger_idempotency_status") != "PASS"
        or report.get("ledger_portfolio_provenance_status") != "PASS"
        or report.get("ledger_duplicate_total_count") != 0
        or report.get("ledger_mismatch_count") != 0
        or report.get("ledger_source_ledger_jsonl_count") < 1
        or report.get("ledger_recomputed_ledger_event_count") < 1
    ):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "ledger idempotency source is not clean enough for closure recheck",
            "RECONCILIATION_REQUIRED",
        )
    if (
        report.get("recheck_status") != POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_STATUS
        or report.get("recheck_outcome") != POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK_OUTCOME
        or report.get("current_evidence_bridge_status") != "BLOCKED_BY_POST_RERUN_CLOSURE"
        or report.get("portfolio_truth_recheck_status") != "LEDGER_PROVENANCE_PASS_BUT_OPERATOR_CURRENT_EVIDENCE_BLOCKED"
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
    ):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun closure recheck must preserve blocked bridge status",
            "LIVE_FINAL_GUARD_FAILED",
        )
    blockers = report.get("blocker_codes")
    if not isinstance(blockers, list):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "FAIL",
            "post-rerun closure recheck blocker_codes must be an array",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    required_blockers = {
        POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED,
        "LIVE_READY_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    }
    if not required_blockers.issubset(set(blockers)):
        return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
            "BLOCKED",
            "post-rerun closure recheck omitted required live-blocking blockers",
            "LIVE_FINAL_GUARD_FAILED",
        )
    return UpbitPaperPostRerunCurrentEvidenceClosureRecheckValidationResult(
        "PASS",
        "Upbit PAPER post-rerun current-evidence closure recheck confirms ledger evidence cannot override closure",
        None,
    )
