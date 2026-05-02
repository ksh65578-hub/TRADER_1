from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_ledger_rollup_regeneration_plan import (
    validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_SCHEMA_ID = (
    "trader1.upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report.v1"
)
STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_TRUTH_ROLE = (
    "paper_runtime_stale_loop_ledger_rollup_regeneration_executor_truth"
)
STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_ROLE = (
    "PAPER_RUNTIME_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_CANDIDATE_ONLY"
)
LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE = "LEDGER_ROLLUP_REGENERATION_EXECUTOR_CURRENT_EVIDENCE_BLOCKED"
LEDGER_ROLLUP_REGENERATION_EXECUTOR_INPUT_SCOPE_BLOCKER_CODE = (
    "LEDGER_ROLLUP_REGENERATION_EXECUTOR_INPUT_SCOPE_BLOCKED"
)


@dataclass(frozen=True)
class UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def upbit_paper_stale_loop_ledger_rollup_regeneration_executor_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("ledger_rollup_regeneration_executor_hash", None)
    return _sha256_json(payload)


def _runtime_base(root: Path, session_id: str) -> Path:
    return Path(root).resolve() / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _rooted(root: Path, relative_path: str) -> Path:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return Path(root).resolve().joinpath(*parts)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_path_allowed(path: str, session_id: str) -> bool:
    normalized = path.replace("\\", "/")
    return (
        normalized.startswith(f"system/runtime/upbit/krw_spot/paper/{session_id}/")
        and ".." not in normalized.split("/")
        and "/live/" not in normalized
    )


def _candidate_path(session_id: str, replacement_loop_id: str) -> str:
    safe_loop_id = "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in replacement_loop_id)
    return (
        f"system/runtime/upbit/krw_spot/paper/{session_id}/paper_runtime/"
        f"ledger_rollup_regeneration_candidates/{safe_loop_id}.paper_ledger_rollup_report.json"
    )


def _existing_candidate_matches(path: Path, candidate: dict[str, Any]) -> bool:
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(existing, dict):
        return False
    if validate_paper_ledger_rollup_report(existing).status != "PASS":
        return False
    if validate_paper_ledger_rollup_report(candidate).status != "PASS":
        return False
    stable_fields = (
        "schema_id",
        "project_id",
        "rollup_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "ledger_source_dir",
        "ledger_input_scope",
        "ledger_jsonl_count",
        "ledger_event_count",
        "filled_order_count",
        "duplicate_ledger_path_count",
        "duplicate_event_count",
        "duplicate_order_count",
        "lifecycle_incomplete_order_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "invalid_ledger_jsonl_count",
        "latest_ledger_head_hash",
        "ledger_head_cycle_id",
        "ledger_head_event_count",
        "ledger_head_match_status",
        "ledger_head_mismatch_count",
        "rollup_status",
        "primary_blocker_code",
        "blockers",
        "artifact_paths",
        "display_only",
        "dashboard_truth_only",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    return {field: existing.get(field) for field in stable_fields} == {
        field: candidate.get(field) for field in stable_fields
    }


def _write_candidate(path: Path, candidate: dict[str, Any], enabled: bool) -> tuple[str, bool, bool]:
    if not enabled:
        return "WRITE_DISABLED", False, False
    if path.exists():
        if _existing_candidate_matches(path, candidate):
            return "REUSED_EXISTING_MATCH", False, True
        return "BLOCKED_EXISTING_MISMATCH", False, False
    durable_atomic_write_json(path, candidate)
    return "WRITTEN", True, False


def _candidate_rollup_from_item(*, root: Path, session_id: str, item: dict[str, Any]) -> dict[str, Any]:
    ledger_paths = [
        _rooted(root, str(cycle.get("selected_ledger_path", "")))
        for cycle in item.get("cycles", [])
        if isinstance(cycle, dict) and isinstance(cycle.get("selected_ledger_path"), str)
    ]
    return build_paper_ledger_rollup_report(
        root=root,
        session_id=session_id,
        rollup_id=f"{item.get('replacement_loop_id')}-ledger-rollup-regeneration-candidate",
        ledger_paths=ledger_paths,
    )


def _build_item(
    *,
    root: Path,
    session_id: str,
    plan_item: dict[str, Any],
    priority_order: int,
    candidate_write_enabled: bool,
) -> dict[str, Any]:
    replacement_loop_id = str(plan_item.get("replacement_loop_id") or "UNKNOWN")
    candidate_path = _candidate_path(session_id, replacement_loop_id)
    candidate = _candidate_rollup_from_item(root=root, session_id=session_id, item=plan_item)
    result = validate_paper_ledger_rollup_report(candidate)
    candidate_recomputed_hash = paper_ledger_rollup_hash(candidate)
    candidate_hash_self_check = "PASS" if candidate.get("rollup_hash") == candidate_recomputed_hash else "FAIL"
    write_status = "NOT_WRITTEN"
    candidate_written = False
    candidate_reused = False
    if result.status == "PASS" and candidate_hash_self_check == "PASS":
        write_status, candidate_written, candidate_reused = _write_candidate(
            _rooted(root, candidate_path),
            candidate,
            candidate_write_enabled,
        )
    if write_status == "BLOCKED_EXISTING_MISMATCH":
        executor_item_status = "BLOCKED_EXISTING_CANDIDATE_MISMATCH"
        primary_blocker_code = "LEDGER_ROLLUP_REGENERATION_CANDIDATE_MISMATCH"
    elif result.status == "PASS" and candidate_hash_self_check == "PASS":
        executor_item_status = "CANDIDATE_ROLLUP_READY_CURRENT_EVIDENCE_BLOCKED"
        primary_blocker_code = LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE
    else:
        executor_item_status = "BLOCKED_ROLLUP_VALIDATION"
        primary_blocker_code = result.blocker_code or LEDGER_ROLLUP_REGENERATION_EXECUTOR_INPUT_SCOPE_BLOCKER_CODE
    blocker_codes = {LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE, primary_blocker_code}
    if result.status != "PASS":
        blocker_codes.add(result.blocker_code or LEDGER_ROLLUP_REGENERATION_EXECUTOR_INPUT_SCOPE_BLOCKER_CODE)
    return {
        "priority_order": priority_order,
        "replacement_loop_id": replacement_loop_id,
        "source_plan_item_status": plan_item.get("plan_item_status"),
        "target_ledger_rollup_path": plan_item.get("target_ledger_rollup_path"),
        "target_ledger_rollup_hash": plan_item.get("target_ledger_rollup_hash"),
        "candidate_rollup_artifact_path": candidate_path,
        "candidate_rollup_write_status": write_status,
        "candidate_rollup_written": candidate_written,
        "candidate_rollup_reused_existing": candidate_reused,
        "candidate_rollup_artifact_ready": write_status in {"WRITTEN", "REUSED_EXISTING_MATCH"},
        "candidate_rollup_status": candidate.get("rollup_status"),
        "candidate_rollup_validator_status": result.status,
        "candidate_rollup_validator_blocker_code": result.blocker_code,
        "candidate_rollup_validator_message": result.message,
        "candidate_rollup_hash": candidate.get("rollup_hash"),
        "candidate_rollup_recomputed_hash": candidate_recomputed_hash,
        "candidate_rollup_hash_self_check": candidate_hash_self_check,
        "candidate_ledger_jsonl_count": candidate.get("ledger_jsonl_count"),
        "candidate_ledger_event_count": candidate.get("ledger_event_count"),
        "candidate_filled_order_count": candidate.get("filled_order_count"),
        "candidate_duplicate_event_count": candidate.get("duplicate_event_count"),
        "candidate_primary_blocker_code": candidate.get("primary_blocker_code"),
        "candidate_strict_input_scope_blocked": candidate.get("primary_blocker_code") == "SNAPSHOT_SCOPE_MISMATCH",
        "candidate_rollup": candidate,
        "executor_item_status": executor_item_status,
        "primary_blocker_code": primary_blocker_code,
        "blocker_codes": sorted(blocker_codes),
        "operator_action": "Keep candidate rollup out of current evidence; run reconciliation and promotion guard first.",
        "candidate_artifact_is_current_evidence": False,
        "candidate_current_evidence_usable": False,
        "current_evidence_write_allowed": False,
        "target_rollup_write_allowed": False,
        "persistent_loop_mutation_allowed": False,
        "replacement_write_allowed": False,
        "source_delete_allowed": False,
        "actual_long_run_evidence_created": False,
        "live_permission_created": False,
    }


def build_upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report(
    *,
    root: Path,
    ledger_rollup_regeneration_plan_report: dict[str, Any],
    ledger_rollup_regeneration_executor_id: str = "upbit-paper-stale-loop-ledger-rollup-regeneration-executor",
    candidate_write_enabled: bool = False,
) -> dict[str, Any]:
    root = Path(root).resolve()
    source_result = validate_upbit_paper_stale_loop_ledger_rollup_regeneration_plan_report(
        ledger_rollup_regeneration_plan_report
    )
    session_id = str(ledger_rollup_regeneration_plan_report.get("session_id", "UNKNOWN"))
    source_items = [
        item
        for item in ledger_rollup_regeneration_plan_report.get("items", [])
        if isinstance(item, dict) and item.get("plan_item_status") == "READY_PLAN_ONLY"
    ]
    items = [
        _build_item(
            root=root,
            session_id=session_id,
            plan_item=item,
            priority_order=index,
            candidate_write_enabled=candidate_write_enabled,
        )
        for index, item in enumerate(source_items, start=1)
    ]
    pass_count = sum(1 for item in items if item["candidate_rollup_validator_status"] == "PASS")
    blocked_count = len(items) - pass_count
    artifact_ready_count = sum(1 for item in items if item["candidate_rollup_artifact_ready"])
    written_count = sum(1 for item in items if item["candidate_rollup_written"])
    reused_count = sum(1 for item in items if item["candidate_rollup_reused_existing"])
    strict_input_scope_blocked_count = sum(1 for item in items if item["candidate_strict_input_scope_blocked"])
    blocker_codes = {LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE}
    if source_result.status != "PASS":
        blocker_codes.add(source_result.blocker_code or "LEDGER_ROLLUP_REGENERATION_PLAN_INVALID")
    for item in items:
        blocker_codes.update(str(code) for code in item["blocker_codes"])
    if blocked_count:
        blocker_codes.add(LEDGER_ROLLUP_REGENERATION_EXECUTOR_INPUT_SCOPE_BLOCKER_CODE)
    report = {
        "schema_id": UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "ledger_rollup_regeneration_executor_id": ledger_rollup_regeneration_executor_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "truth_role": STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_TRUTH_ROLE,
        "ledger_rollup_regeneration_executor_role": STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_ROLE,
        "source_ledger_rollup_regeneration_plan_hash": ledger_rollup_regeneration_plan_report.get(
            "ledger_rollup_regeneration_plan_hash"
        ),
        "source_ledger_rollup_regeneration_plan_status": ledger_rollup_regeneration_plan_report.get("plan_status"),
        "source_ledger_rollup_regeneration_plan_validator_status": source_result.status,
        "source_plan_candidate_count": ledger_rollup_regeneration_plan_report.get("plan_candidate_count"),
        "item_count": len(items),
        "candidate_rollup_attempt_count": len(items),
        "candidate_rollup_pass_count": pass_count,
        "candidate_rollup_blocked_count": blocked_count,
        "candidate_rollup_artifact_ready_count": artifact_ready_count,
        "candidate_rollup_written_count": written_count,
        "candidate_rollup_reused_existing_count": reused_count,
        "strict_input_scope_blocked_count": strict_input_scope_blocked_count,
        "candidate_ledger_jsonl_count": sum(int(item.get("candidate_ledger_jsonl_count") or 0) for item in items),
        "candidate_ledger_event_count": sum(int(item.get("candidate_ledger_event_count") or 0) for item in items),
        "candidate_filled_order_count": sum(int(item.get("candidate_filled_order_count") or 0) for item in items),
        "candidate_current_evidence_usable_count": 0,
        "target_rollup_write_allowed_count": 0,
        "current_evidence_write_allowed_count": 0,
        "executor_status": "BLOCKED",
        "primary_blocker_code": LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE,
        "blocker_codes": sorted(blocker_codes),
        "items": items,
        "operator_next_action": "Reconcile candidate rollups and resolve blocked input scopes before current-evidence closure.",
        "display_only": True,
        "dashboard_truth_only": True,
        "paper_only": True,
        "candidate_only": True,
        "candidate_write_enabled": bool(candidate_write_enabled),
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
        "ledger_rollup_regeneration_executor_hash": "",
    }
    report["ledger_rollup_regeneration_executor_hash"] = upbit_paper_stale_loop_ledger_rollup_regeneration_executor_hash(report)
    return report


def write_upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report(
    *, root: Path, report: dict[str, Any]
) -> Path:
    path = (
        _runtime_base(Path(root), str(report["session_id"]))
        / "paper_runtime"
        / "upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report.json"
    )
    durable_atomic_write_json(path, report)
    return path


def validate_upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report(
    report: dict[str, Any],
) -> UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "ledger_rollup_regeneration_executor_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "truth_role",
        "ledger_rollup_regeneration_executor_role",
        "source_ledger_rollup_regeneration_plan_hash",
        "source_ledger_rollup_regeneration_plan_status",
        "source_ledger_rollup_regeneration_plan_validator_status",
        "source_plan_candidate_count",
        "item_count",
        "candidate_rollup_attempt_count",
        "candidate_rollup_pass_count",
        "candidate_rollup_blocked_count",
        "candidate_rollup_artifact_ready_count",
        "candidate_rollup_written_count",
        "candidate_rollup_reused_existing_count",
        "strict_input_scope_blocked_count",
        "candidate_ledger_jsonl_count",
        "candidate_ledger_event_count",
        "candidate_filled_order_count",
        "candidate_current_evidence_usable_count",
        "target_rollup_write_allowed_count",
        "current_evidence_write_allowed_count",
        "executor_status",
        "primary_blocker_code",
        "blocker_codes",
        "items",
        "operator_next_action",
        "display_only",
        "dashboard_truth_only",
        "paper_only",
        "candidate_only",
        "candidate_write_enabled",
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
        "ledger_rollup_regeneration_executor_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "FAIL", f"ledger-rollup regeneration executor missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("schema_id") != UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR_SCHEMA_ID:
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "FAIL", "ledger-rollup regeneration executor schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("ledger_rollup_regeneration_executor_hash") != upbit_paper_stale_loop_ledger_rollup_regeneration_executor_hash(report):
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "FAIL", "ledger-rollup regeneration executor hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "BLOCKED", "ledger-rollup regeneration executor scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH"
        )
    false_fields = (
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
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "BLOCKED", "ledger-rollup regeneration executor attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("display_only") is not True
        or report.get("dashboard_truth_only") is not True
        or report.get("paper_only") is not True
        or report.get("candidate_only") is not True
    ):
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "BLOCKED", "ledger-rollup regeneration executor must stay candidate-only", "LIVE_FINAL_GUARD_FAILED"
        )
    if (
        report.get("candidate_current_evidence_usable_count") != 0
        or report.get("target_rollup_write_allowed_count") != 0
        or report.get("current_evidence_write_allowed_count") != 0
    ):
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "BLOCKED", "ledger-rollup regeneration executor exposed current evidence usability", "LIVE_FINAL_GUARD_FAILED"
        )
    items = report.get("items")
    if not isinstance(items, list) or report.get("item_count") != len(items) or report.get("candidate_rollup_attempt_count") != len(items):
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "FAIL", "ledger-rollup regeneration executor item count mismatch", "SCHEMA_IDENTITY_MISMATCH"
        )
    pass_count = 0
    artifact_ready_count = 0
    written_count = 0
    reused_count = 0
    strict_input_scope_blocked_count = 0
    ledger_jsonl_count = 0
    ledger_event_count = 0
    filled_count = 0
    session_id = str(report.get("session_id"))
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", "ledger-rollup regeneration executor item must be an object", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("priority_order") != index:
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", "ledger-rollup regeneration executor priority sequence mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        for path_field in ("target_ledger_rollup_path", "candidate_rollup_artifact_path"):
            if not _artifact_path_allowed(str(item.get(path_field) or ""), session_id):
                return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                    "BLOCKED", f"ledger-rollup regeneration executor {path_field} escaped PAPER namespace", "SNAPSHOT_SCOPE_MISMATCH"
                )
        item_false = (
            "candidate_artifact_is_current_evidence",
            "candidate_current_evidence_usable",
            "current_evidence_write_allowed",
            "target_rollup_write_allowed",
            "persistent_loop_mutation_allowed",
            "replacement_write_allowed",
            "source_delete_allowed",
            "actual_long_run_evidence_created",
            "live_permission_created",
        )
        if any(item.get(field) for field in item_false):
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "BLOCKED", "ledger-rollup regeneration executor item attempted current evidence or live permission", "LIVE_FINAL_GUARD_FAILED"
            )
        candidate = item.get("candidate_rollup")
        if not isinstance(candidate, dict):
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", "ledger-rollup regeneration executor candidate rollup missing", "SCHEMA_IDENTITY_MISMATCH"
            )
        result = validate_paper_ledger_rollup_report(candidate)
        if item.get("candidate_rollup_validator_status") != result.status:
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", "ledger-rollup regeneration executor candidate validator status mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        recomputed_hash = paper_ledger_rollup_hash(candidate)
        if item.get("candidate_rollup_recomputed_hash") != recomputed_hash or item.get("candidate_rollup_hash_self_check") != (
            "PASS" if candidate.get("rollup_hash") == recomputed_hash else "FAIL"
        ):
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", "ledger-rollup regeneration executor candidate hash mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if result.status == "PASS":
            pass_count += 1
            if item.get("executor_item_status") != "CANDIDATE_ROLLUP_READY_CURRENT_EVIDENCE_BLOCKED":
                return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                    "FAIL", "PASS candidate must remain current-evidence blocked", "SCHEMA_IDENTITY_MISMATCH"
                )
        elif item.get("executor_item_status") != "BLOCKED_ROLLUP_VALIDATION":
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", "blocked candidate status mismatch", "SCHEMA_IDENTITY_MISMATCH"
            )
        if item.get("candidate_rollup_artifact_ready"):
            artifact_ready_count += 1
            if item.get("candidate_rollup_write_status") not in {"WRITTEN", "REUSED_EXISTING_MATCH"}:
                return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                    "FAIL", "ready candidate artifact write status mismatch", "SCHEMA_IDENTITY_MISMATCH"
                )
        if item.get("candidate_rollup_written"):
            written_count += 1
        if item.get("candidate_rollup_reused_existing"):
            reused_count += 1
        if item.get("candidate_strict_input_scope_blocked"):
            strict_input_scope_blocked_count += 1
        ledger_jsonl_count += int(item.get("candidate_ledger_jsonl_count") or 0)
        ledger_event_count += int(item.get("candidate_ledger_event_count") or 0)
        filled_count += int(item.get("candidate_filled_order_count") or 0)
    expected_counts = {
        "candidate_rollup_pass_count": pass_count,
        "candidate_rollup_blocked_count": len(items) - pass_count,
        "candidate_rollup_artifact_ready_count": artifact_ready_count,
        "candidate_rollup_written_count": written_count,
        "candidate_rollup_reused_existing_count": reused_count,
        "strict_input_scope_blocked_count": strict_input_scope_blocked_count,
        "candidate_ledger_jsonl_count": ledger_jsonl_count,
        "candidate_ledger_event_count": ledger_event_count,
        "candidate_filled_order_count": filled_count,
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
                "FAIL", f"ledger-rollup regeneration executor count mismatch: {field}", "SCHEMA_IDENTITY_MISMATCH"
            )
    if report.get("executor_status") != "BLOCKED" or report.get("primary_blocker_code") != LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE:
        return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
            "BLOCKED", "ledger-rollup regeneration executor must remain blocked before current-evidence promotion", LEDGER_ROLLUP_REGENERATION_EXECUTOR_BLOCKER_CODE
        )
    return UpbitPaperStaleLoopLedgerRollupRegenerationExecutorValidationResult(
        "PASS",
        "Upbit PAPER stale-loop ledger-rollup regeneration executor writes candidate-only artifacts and keeps current evidence blocked",
        None,
    )
