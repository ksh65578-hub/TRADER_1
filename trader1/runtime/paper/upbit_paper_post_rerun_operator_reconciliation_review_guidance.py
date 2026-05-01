from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.paper.upbit_paper_post_rerun_ledger_rollup_reconciliation import (
    POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_blocker_rollup import (
    POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS,
    POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_OUTCOME,
    upbit_paper_post_rerun_reconciliation_blocker_rollup_hash,
    validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_SCHEMA_ID = (
    "trader1.upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.v1"
)
POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_TRUTH_ROLE = (
    "PAPER_RUNTIME_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_REVIEW_ONLY_NOT_WRITER"
)
POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_ROLE = (
    "PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_NOT_CURRENT_EVIDENCE"
)
POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_STATUS = (
    "BLOCKED_RECONCILIATION_REVIEW_REQUIRED"
)
POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_OUTCOME = (
    "OPERATOR_REVIEW_GUIDANCE_CREATED_CURRENT_EVIDENCE_BLOCKED"
)
POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS = (
    "PENDING_OPERATOR_REVIEW_CURRENT_EVIDENCE_BLOCKED"
)
POST_RERUN_REVIEW_GUIDANCE_SOURCE_BLOCKER_ROLLUP_BINDING_REQUIRED = (
    "POST_RERUN_REVIEW_GUIDANCE_SOURCE_BLOCKER_ROLLUP_BINDING_REQUIRED"
)


@dataclass(frozen=True)
class UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def upbit_paper_post_rerun_operator_reconciliation_review_guidance_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("guidance_hash", None)
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


def _source_blocker_rollup_file_binding(
    *,
    root: Path,
    relative_path: str,
    expected_hash: Any,
    session_id: str,
) -> dict[str, Any]:
    if not _artifact_path_allowed(relative_path, session_id):
        return {
            "source_blocker_rollup_file_load_status": "SCOPE_MISMATCH",
            "source_blocker_rollup_file_hash": None,
            "source_blocker_rollup_file_recomputed_hash": None,
            "source_blocker_rollup_file_hash_match": False,
        }
    source, source_error = _safe_load_json(_rooted(root, relative_path))
    if source is None:
        return {
            "source_blocker_rollup_file_load_status": str(source_error or "UNKNOWN"),
            "source_blocker_rollup_file_hash": None,
            "source_blocker_rollup_file_recomputed_hash": None,
            "source_blocker_rollup_file_hash_match": False,
        }
    file_hash = source.get("blocker_rollup_hash")
    recomputed_hash = upbit_paper_post_rerun_reconciliation_blocker_rollup_hash(source)
    hash_match = bool(file_hash == expected_hash == recomputed_hash)
    return {
        "source_blocker_rollup_file_load_status": "PASS" if hash_match else "HASH_MISMATCH",
        "source_blocker_rollup_file_hash": file_hash,
        "source_blocker_rollup_file_recomputed_hash": recomputed_hash,
        "source_blocker_rollup_file_hash_match": hash_match,
    }


def _build_review_steps(blocker_codes: list[str]) -> list[dict[str, Any]]:
    steps = [
        (
            "VERIFY_BLOCKER_ROLLUP_INTEGRITY",
            "Confirm the source blocker rollup is BLOCKED and hash-linked before any operator decision is considered.",
        ),
        (
            "REVIEW_CANDIDATE_ROLLUP_ARTIFACTS",
            "Inspect each candidate post-rerun rollup artifact as staged evidence only; do not promote it to current evidence.",
        ),
        (
            "VERIFY_PLANNED_CURRENT_LEDGER_PATHS",
            "Compare planned current ledger paths against the PAPER namespace and keep them unwritten while reconciliation is unresolved.",
        ),
        (
            "RECORD_REVIEW_OUTSIDE_CURRENT_EVIDENCE_WRITER",
            "Record any operator notes through a separate review/audit path; do not use this guidance as a writer input.",
        ),
    ]
    return [
        {
            "step_order": index,
            "review_step_id": step_id,
            "review_step_status": POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS,
            "instruction": instruction,
            "expected_source_status": "BLOCKED",
            "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
            "referenced_blocker_codes": blocker_codes,
            "blocks_current_evidence": True,
            "blocks_live_order": True,
            "blocks_scale_up": True,
        }
        for index, (step_id, instruction) in enumerate(steps, start=1)
    ]


def _build_forbidden_outputs() -> list[dict[str, Any]]:
    return [
        {
            "output_name": "current_evidence_snapshot",
            "allowed": False,
            "output_blocked": True,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        },
        {
            "output_name": "current_ledger_jsonl",
            "allowed": False,
            "output_blocked": True,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        },
        {
            "output_name": "latest_runtime_pointer",
            "allowed": False,
            "output_blocked": True,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        },
        {
            "output_name": "LIVE_READY_snapshot",
            "allowed": False,
            "output_blocked": True,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        },
        {
            "output_name": "live_config_mutation",
            "allowed": False,
            "output_blocked": True,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        },
        {
            "output_name": "risk_scale_up_decision",
            "allowed": False,
            "output_blocked": True,
            "blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        },
    ]


def _build_guidance_item(*, source_item: dict[str, Any]) -> dict[str, Any]:
    return {
        "priority_order": int(source_item.get("priority_order") or 0),
        "replacement_loop_id": str(source_item.get("replacement_loop_id") or "UNKNOWN"),
        "cycle_id": str(source_item.get("cycle_id") or "UNKNOWN"),
        "source_item_rollup_status": str(source_item.get("item_rollup_status") or "UNKNOWN"),
        "candidate_rollup_artifact_path": str(source_item.get("candidate_rollup_artifact_path") or ""),
        "planned_current_ledger_jsonl_path": str(source_item.get("planned_current_ledger_jsonl_path") or ""),
        "primary_item_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "blocking_codes": sorted({str(code) for code in source_item.get("blocking_codes", []) if code}),
        "item_blocker_count": int(source_item.get("item_blocker_count") or 0),
        "review_status": POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS,
        "recommended_operator_action": (
            "Review the staged candidate rollup and planned current ledger path, then keep current evidence blocked "
            "until a separate reconciliation process produces validated evidence."
        ),
        "path_scope_status": str(source_item.get("path_scope_status") or "UNKNOWN"),
        "operator_decision_required": True,
        "current_evidence_write_authorized": False,
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


def build_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(
    *,
    root: Path,
    blocker_rollup_report: dict[str, Any],
    source_blocker_rollup_path: str = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json",
    guidance_id: str = "upbit-paper-post-rerun-operator-reconciliation-review-guidance",
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(blocker_rollup_report)
    session_id = str(blocker_rollup_report.get("session_id") or "UNKNOWN")
    blocker_codes = sorted({str(code) for code in blocker_rollup_report.get("blocker_codes", []) if code})
    if POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in blocker_codes:
        blocker_codes = sorted({*blocker_codes, POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE})
    source_items = [item for item in blocker_rollup_report.get("items", []) if isinstance(item, dict)]
    guidance_items = [_build_guidance_item(source_item=item) for item in source_items] if source_result.status == "PASS" else []
    review_steps = _build_review_steps(blocker_codes)
    forbidden_outputs = _build_forbidden_outputs()
    source_hash = blocker_rollup_report.get("blocker_rollup_hash")
    source_file_binding = _source_blocker_rollup_file_binding(
        root=root,
        relative_path=source_blocker_rollup_path,
        expected_hash=source_hash,
        session_id=session_id,
    )
    if source_file_binding["source_blocker_rollup_file_load_status"] != "PASS":
        blocker_codes = sorted({*blocker_codes, POST_RERUN_REVIEW_GUIDANCE_SOURCE_BLOCKER_ROLLUP_BINDING_REQUIRED})
    report = {
        "schema_id": UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "guidance_id": guidance_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_TRUTH_ROLE,
        "guidance_role": POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_ROLE,
        "source_blocker_rollup_path": source_blocker_rollup_path,
        "source_blocker_rollup_hash": source_hash,
        **source_file_binding,
        "source_blocker_rollup_status": blocker_rollup_report.get("blocker_rollup_status"),
        "source_blocker_rollup_primary_blocker_code": blocker_rollup_report.get("primary_blocker_code"),
        "source_blocker_rollup_outcome": blocker_rollup_report.get("rollup_outcome"),
        "source_rollup_item_count": int(blocker_rollup_report.get("rollup_item_count") or 0),
        "source_unique_blocker_count": int(blocker_rollup_report.get("unique_blocker_count") or 0),
        "source_unresolved_blocker_count": int(blocker_rollup_report.get("unresolved_blocker_count") or 0),
        "source_primary_blocker_item_count": int(blocker_rollup_report.get("primary_blocker_item_count") or 0),
        "review_guidance_status": POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_STATUS,
        "primary_blocker_code": POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE,
        "guidance_outcome": POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_OUTCOME,
        "operator_action_required": True,
        "guidance_item_count": len(guidance_items),
        "review_step_count": len(review_steps),
        "forbidden_output_count": len(forbidden_outputs),
        "current_evidence_write_authorized_count": 0,
        "current_evidence_write_allowed_count": 0,
        "candidate_current_evidence_usable_count": 0,
        "blocker_codes": blocker_codes,
        "review_steps": review_steps,
        "guidance_items": guidance_items,
        "forbidden_outputs": forbidden_outputs,
        "guidance_next_action": "Use this guidance for operator review only; keep current evidence, live readiness, live orders, and scale-up blocked.",
        "current_evidence_mutation_allowed": False,
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
        "scale_up_allowed": False,
        "guidance_hash": "",
    }
    report["guidance_hash"] = upbit_paper_post_rerun_operator_reconciliation_review_guidance_hash(report)
    return report


def write_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(*, root: Path, report: dict[str, Any]) -> Path:
    path = _runtime_base(Path(root), str(report["session_id"])) / "paper_runtime" / "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json"
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_post_rerun_operator_reconciliation_review_guidance_report(
    report: dict[str, Any],
) -> UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "guidance_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "guidance_role",
        "source_blocker_rollup_path",
        "source_blocker_rollup_hash",
        "source_blocker_rollup_file_load_status",
        "source_blocker_rollup_file_hash",
        "source_blocker_rollup_file_recomputed_hash",
        "source_blocker_rollup_file_hash_match",
        "source_blocker_rollup_status",
        "source_blocker_rollup_primary_blocker_code",
        "source_blocker_rollup_outcome",
        "source_rollup_item_count",
        "source_unique_blocker_count",
        "source_unresolved_blocker_count",
        "source_primary_blocker_item_count",
        "review_guidance_status",
        "primary_blocker_code",
        "guidance_outcome",
        "operator_action_required",
        "guidance_item_count",
        "review_step_count",
        "forbidden_output_count",
        "current_evidence_write_authorized_count",
        "current_evidence_write_allowed_count",
        "candidate_current_evidence_usable_count",
        "blocker_codes",
        "review_steps",
        "guidance_items",
        "forbidden_outputs",
        "guidance_next_action",
        "current_evidence_mutation_allowed",
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
        "scale_up_allowed",
        "guidance_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", f"post-rerun review guidance missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_SCHEMA_ID:
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("guidance_hash") != upbit_paper_post_rerun_operator_reconciliation_review_guidance_hash(report):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("truth_role") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_TRUTH_ROLE or report.get("guidance_role") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_ROLE:
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance cannot claim writer or live truth", "LIVE_FINAL_GUARD_FAILED")
    forbidden = (
        "current_evidence_mutation_allowed",
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
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance created forbidden permission or mutation", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("current_evidence_write_authorized_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
        or report.get("candidate_current_evidence_usable_count") != 0
    ):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance exposed current evidence write/use", "LIVE_FINAL_GUARD_FAILED")
    if (
        report.get("source_blocker_rollup_status") != "BLOCKED"
        or report.get("source_blocker_rollup_primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("source_blocker_rollup_outcome") != POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_OUTCOME
    ):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "source blocker rollup boundary mismatch", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if (
        report.get("review_guidance_status") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_STATUS
        or report.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
        or report.get("guidance_outcome") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_OUTCOME
        or report.get("operator_action_required") is not True
    ):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance must remain blocked and operator-review-only", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    session_id = str(report.get("session_id"))
    if not _artifact_path_allowed(str(report.get("source_blocker_rollup_path") or ""), session_id):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "source blocker rollup path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
    if (
        report.get("source_blocker_rollup_file_load_status") != "PASS"
        or report.get("source_blocker_rollup_file_hash_match") is not True
    ):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult(
            "BLOCKED",
            "source blocker rollup file binding is missing or mismatched",
            POST_RERUN_REVIEW_GUIDANCE_SOURCE_BLOCKER_ROLLUP_BINDING_REQUIRED,
        )
    if (
        report.get("source_blocker_rollup_file_hash") != report.get("source_blocker_rollup_hash")
        or report.get("source_blocker_rollup_file_recomputed_hash") != report.get("source_blocker_rollup_hash")
    ):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult(
            "FAIL",
            "source blocker rollup file hash does not match source report hash",
            "SCHEMA_IDENTITY_MISMATCH",
        )
    blocker_codes = report.get("blocker_codes")
    if not isinstance(blocker_codes, list) or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(blocker_codes):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance missing reconciliation blocker", POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE)
    if report.get("source_unique_blocker_count") != len(set(blocker_codes)) or report.get("source_unresolved_blocker_count") != len(set(blocker_codes)):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance blocker count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    items = report.get("guidance_items")
    if not isinstance(items, list) or report.get("guidance_item_count") != len(items) or report.get("source_rollup_item_count") != len(items):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance item count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("source_primary_blocker_item_count") != len(items):
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance primary blocker count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    review_steps = report.get("review_steps")
    if not isinstance(review_steps, list) or report.get("review_step_count") != len(review_steps) or len(review_steps) < 4:
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance step count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for step in review_steps:
        if not isinstance(step, dict):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review step must be object", "SCHEMA_IDENTITY_MISMATCH")
        if (
            step.get("review_step_status") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS
            or step.get("expected_source_status") != "BLOCKED"
            or step.get("primary_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(step.get("referenced_blocker_codes") or [])
            or step.get("blocks_current_evidence") is not True
            or step.get("blocks_live_order") is not True
            or step.get("blocks_scale_up") is not True
        ):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review step lost blocking semantics", "LIVE_FINAL_GUARD_FAILED")
    forbidden_outputs = report.get("forbidden_outputs")
    if not isinstance(forbidden_outputs, list) or report.get("forbidden_output_count") != len(forbidden_outputs) or len(forbidden_outputs) < 5:
        return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun forbidden output count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    for output in forbidden_outputs:
        if not isinstance(output, dict):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun forbidden output must be object", "SCHEMA_IDENTITY_MISMATCH")
        if output.get("allowed") is not False or output.get("output_blocked") is not True or output.get("blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE:
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance allowed a forbidden output", "LIVE_FINAL_GUARD_FAILED")
    for item in items:
        if not isinstance(item, dict):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance item must be object", "SCHEMA_IDENTITY_MISMATCH")
        if not _candidate_rollup_path_allowed(str(item.get("candidate_rollup_artifact_path") or ""), session_id):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "review guidance candidate rollup path escaped post-rollup namespace", "SNAPSHOT_SCOPE_MISMATCH")
        if not _current_ledger_path_allowed(str(item.get("planned_current_ledger_jsonl_path") or ""), session_id):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "review guidance planned current ledger path escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH")
        item_forbidden = (
            "current_evidence_write_authorized",
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
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("BLOCKED", "post-rerun review guidance item attempted current evidence or live mutation", "LIVE_FINAL_GUARD_FAILED")
        if (
            item.get("source_item_rollup_status") != POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_ITEM_STATUS
            or item.get("primary_item_blocker_code") != POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE
            or item.get("review_status") != POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_ITEM_STATUS
            or item.get("path_scope_status") != "MATCH"
            or item.get("operator_decision_required") is not True
            or POST_RERUN_RECONCILIATION_REQUIRED_BLOCKER_CODE not in set(item.get("blocking_codes") or [])
            or item.get("item_blocker_count") != len(item.get("blocking_codes") or [])
        ):
            return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult("FAIL", "post-rerun review guidance item lost blocked state", "SCHEMA_IDENTITY_MISMATCH")
    return UpbitPaperPostRerunOperatorReconciliationReviewGuidanceValidationResult(
        "PASS",
        "Upbit PAPER post-rerun operator reconciliation guidance remains review-only and blocks current evidence/live/scale",
        None,
    )
