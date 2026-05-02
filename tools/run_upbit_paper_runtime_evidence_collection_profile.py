from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.ledger.paper_ledger_rollup import build_paper_ledger_rollup_report, write_paper_ledger_rollup_report
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    LONG_RUN_EVIDENCE_BLOCKER_CODE,
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
    validate_upbit_paper_runtime_recovery_guard_report,
)
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


REPORT_SCHEMA_ID = "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1"
PROFILE_ID = "UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_V1"
PROFILE_SCOPE = "UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_ONLY_NO_LIVE"
DEFAULT_REPORT_PATH = Path(
    "system/evidence/runtime_checks/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json"
)
DEFAULT_SESSION_ID = "mvp1_upbit_paper_launcher"


@dataclass(frozen=True)
class ProfileValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest().upper()


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_text(path: Path, value: str) -> None:
    _atomic_write_text(path, value)


def upbit_paper_runtime_evidence_collection_profile_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("profile_hash", None)
    return _sha256_json(payload)


def _component(
    *,
    component_id: str,
    status: str,
    blocker_code: str | None,
    message: str,
    evidence_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "status": status,
        "blocker_code": blocker_code,
        "message": message,
        "evidence_hash": evidence_hash,
    }


def _duplicate_first_ledger_jsonl(root: Path, loop: dict[str, Any]) -> None:
    for cycle_result in loop.get("cycle_results", []):
        for artifact_path in cycle_result.get("artifact_paths", []):
            artifact_text = str(artifact_path)
            if artifact_text.endswith(".paper_ledger_events.jsonl"):
                source = root / artifact_text
                duplicate = source.with_name("duplicate-runtime-evidence-profile.paper_ledger_events.jsonl")
                write_text(duplicate, source.read_text(encoding="utf-8"))
                rollup = build_paper_ledger_rollup_report(
                    root=root,
                    session_id=str(loop.get("session_id") or DEFAULT_SESSION_ID),
                    rollup_id=f"{loop.get('loop_id')}-duplicate-ledger-rollup",
                )
                write_paper_ledger_rollup_report(root=root, report=rollup)
                return
    raise RuntimeError("bounded PAPER loop did not write a ledger JSONL artifact")


def build_upbit_paper_runtime_evidence_collection_profile_report(
    *,
    root: Path,
    loop_id: str = "upbit-paper-runtime-evidence-profile",
    session_id: str = DEFAULT_SESSION_ID,
    requested_cycle_count: int = 2,
    duplicate_ledger_events: bool = False,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    loop = run_upbit_paper_persistent_loop(
        root=root,
        loop_id=loop_id,
        session_id=session_id,
        requested_cycle_count=requested_cycle_count,
    )
    if duplicate_ledger_events:
        _duplicate_first_ledger_jsonl(root, loop)

    loop_result = validate_upbit_paper_persistent_loop_report(loop)
    recovery_guard = build_recovery_guard_from_loop(root=root, loop=loop)
    recovery_result = validate_upbit_paper_runtime_recovery_guard_report(recovery_guard)
    sample_history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
    sample_history_result = validate_upbit_paper_runtime_sample_history(sample_history)
    idempotency_evidence = build_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, session_id=session_id)
    idempotency_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(idempotency_evidence)

    component_results = [
        _component(
            component_id="persistent_loop",
            status=loop_result.status,
            blocker_code=loop_result.blocker_code,
            message=loop_result.message,
            evidence_hash=loop.get("loop_hash"),
        ),
        _component(
            component_id="runtime_recovery_guard",
            status=recovery_result.status,
            blocker_code=recovery_result.blocker_code,
            message=recovery_result.message,
            evidence_hash=recovery_guard.get("guard_hash"),
        ),
        _component(
            component_id="runtime_sample_history",
            status=sample_history_result.status,
            blocker_code=sample_history_result.blocker_code,
            message=sample_history_result.message,
            evidence_hash=sample_history.get("history_hash"),
        ),
        _component(
            component_id="ledger_idempotency_runtime_evidence",
            status=idempotency_result.status,
            blocker_code=idempotency_result.blocker_code,
            message=idempotency_result.message,
            evidence_hash=idempotency_evidence.get("evidence_hash"),
        ),
    ]
    blockers = [
        str(item["blocker_code"] or f"{item['component_id'].upper()}_NOT_PASS")
        for item in component_results
        if item.get("status") != "PASS"
    ]
    if sample_history.get("long_run_evidence_eligible") or idempotency_evidence.get("long_run_evidence_eligible"):
        blockers.append("LONG_RUN_EVIDENCE_FALSE_POSITIVE")
    forbidden_flags = (
        loop.get("live_order_ready"),
        loop.get("live_order_allowed"),
        loop.get("can_live_trade"),
        loop.get("scale_up_allowed"),
        recovery_guard.get("live_order_ready"),
        recovery_guard.get("live_order_allowed"),
        recovery_guard.get("can_live_trade"),
        recovery_guard.get("scale_up_allowed"),
        sample_history.get("live_order_ready"),
        sample_history.get("live_order_allowed"),
        sample_history.get("can_live_trade"),
        sample_history.get("scale_up_allowed"),
        idempotency_evidence.get("live_order_ready"),
        idempotency_evidence.get("live_order_allowed"),
        idempotency_evidence.get("can_live_trade"),
        idempotency_evidence.get("can_submit_order"),
        idempotency_evidence.get("scale_up_allowed"),
    )
    if any(forbidden_flags):
        blockers.append("LIVE_FINAL_GUARD_FAILED")

    blocker_codes = sorted(set(blockers))
    profile_status = "PASS" if not blocker_codes else "BLOCKED"
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "created_at_utc": created_at_utc or utc_now(),
        "profile_id": PROFILE_ID,
        "profile_scope": PROFILE_SCOPE,
        "status": profile_status,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "loop_id": loop_id,
        "requested_cycle_count": requested_cycle_count,
        "completed_cycle_count": int(loop.get("completed_cycle_count") or 0),
        "component_count": len(component_results),
        "component_pass_count": sum(1 for item in component_results if item["status"] == "PASS"),
        "component_blocked_count": sum(1 for item in component_results if item["status"] != "PASS"),
        "component_results": component_results,
        "loop_status": loop.get("loop_status"),
        "loop_hash": loop.get("loop_hash"),
        "recovery_guard_status": recovery_guard.get("recovery_guard_status"),
        "recovery_guard_hash": recovery_guard.get("guard_hash"),
        "runtime_sample_history_validation_status": sample_history_result.status,
        "runtime_sample_status": sample_history.get("runtime_sample_status"),
        "runtime_sample_history_hash": sample_history.get("history_hash"),
        "accepted_cycle_sample_count": int(sample_history.get("accepted_cycle_sample_count") or 0),
        "unique_runtime_cycle_hash_count": int(sample_history.get("unique_runtime_cycle_hash_count") or 0),
        "duplicate_cycle_hash_count": int(sample_history.get("duplicate_cycle_hash_count") or 0),
        "invalid_source_count": int(sample_history.get("invalid_source_count") or 0),
        "observed_span_seconds": int(sample_history.get("observed_span_seconds") or 0),
        "min_actual_long_run_span_seconds": int(sample_history.get("min_actual_long_run_span_seconds") or 0),
        "min_actual_long_run_cycle_count": int(sample_history.get("min_actual_long_run_cycle_count") or 0),
        "span_floor_met": bool(sample_history.get("span_floor_met")),
        "cycle_floor_met": bool(sample_history.get("cycle_floor_met")),
        "ledger_runtime_evidence_status": idempotency_evidence.get("runtime_evidence_status"),
        "ledger_idempotency_evidence_hash": idempotency_evidence.get("evidence_hash"),
        "idempotency_status": idempotency_evidence.get("idempotency_status"),
        "reconciliation_status": idempotency_evidence.get("reconciliation_status"),
        "mismatch_count": int(idempotency_evidence.get("mismatch_count") or 0),
        "source_ledger_jsonl_count": int(idempotency_evidence.get("source_ledger_jsonl_count") or 0),
        "recomputed_ledger_event_count": int(idempotency_evidence.get("recomputed_ledger_event_count") or 0),
        "recomputed_filled_order_count": int(idempotency_evidence.get("recomputed_filled_order_count") or 0),
        "duplicate_event_id_count": int(idempotency_evidence.get("duplicate_event_id_count") or 0),
        "duplicate_dedup_key_count": int(idempotency_evidence.get("duplicate_dedup_key_count") or 0),
        "duplicate_semantic_event_count": int(idempotency_evidence.get("duplicate_semantic_event_count") or 0),
        "duplicate_filled_order_key_count": int(idempotency_evidence.get("duplicate_filled_order_key_count") or 0),
        "primary_blocker_code": blocker_codes[0] if blocker_codes else None,
        "blockers": blocker_codes,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "promotion_eligible": False,
        "current_evidence_write_allowed": False,
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
        "profile_hash": "",
    }
    report["profile_hash"] = upbit_paper_runtime_evidence_collection_profile_hash(report)
    return report


def build_recovery_guard_from_loop(*, root: Path, loop: dict[str, Any]) -> dict[str, Any]:
    guard_path_text = loop.get("runtime_recovery_guard_path")
    if isinstance(guard_path_text, str) and guard_path_text:
        guard_path = Path(root).resolve() / guard_path_text
        try:
            value = json.loads(guard_path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                return value
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            pass
    from trader1.runtime.paper.upbit_paper_persistent_loop import build_upbit_paper_runtime_recovery_guard_report

    return build_upbit_paper_runtime_recovery_guard_report(
        root=Path(root).resolve(),
        session_id=str(loop.get("session_id") or DEFAULT_SESSION_ID),
        loop_id=str(loop.get("loop_id") or "upbit-paper-runtime-evidence-profile"),
    )


def validate_upbit_paper_runtime_evidence_collection_profile_report(
    report: dict[str, Any],
) -> ProfileValidationResult:
    required = {
        "schema_id",
        "created_at_utc",
        "profile_id",
        "profile_scope",
        "status",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "loop_id",
        "requested_cycle_count",
        "completed_cycle_count",
        "component_count",
        "component_pass_count",
        "component_blocked_count",
        "component_results",
        "loop_status",
        "loop_hash",
        "recovery_guard_status",
        "recovery_guard_hash",
        "runtime_sample_history_validation_status",
        "runtime_sample_status",
        "runtime_sample_history_hash",
        "accepted_cycle_sample_count",
        "unique_runtime_cycle_hash_count",
        "duplicate_cycle_hash_count",
        "invalid_source_count",
        "observed_span_seconds",
        "min_actual_long_run_span_seconds",
        "min_actual_long_run_cycle_count",
        "span_floor_met",
        "cycle_floor_met",
        "ledger_runtime_evidence_status",
        "ledger_idempotency_evidence_hash",
        "idempotency_status",
        "reconciliation_status",
        "mismatch_count",
        "source_ledger_jsonl_count",
        "recomputed_ledger_event_count",
        "recomputed_filled_order_count",
        "duplicate_event_id_count",
        "duplicate_dedup_key_count",
        "duplicate_semantic_event_count",
        "duplicate_filled_order_key_count",
        "primary_blocker_code",
        "blockers",
        "long_run_blocker_code",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "current_evidence_write_allowed",
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
        "profile_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return ProfileValidationResult("FAIL", f"runtime evidence profile missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != REPORT_SCHEMA_ID or report.get("profile_id") != PROFILE_ID:
        return ProfileValidationResult("FAIL", "runtime evidence profile identity mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("profile_hash") != upbit_paper_runtime_evidence_collection_profile_hash(report):
        return ProfileValidationResult("FAIL", "runtime evidence profile hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return ProfileValidationResult("BLOCKED", "runtime evidence profile scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    forbidden = (
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "current_evidence_write_allowed",
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
        return ProfileValidationResult("BLOCKED", "runtime evidence profile attempted forbidden live or promotion permission", "LIVE_FINAL_GUARD_FAILED")
    if report.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE:
        return ProfileValidationResult("BLOCKED", "runtime evidence profile must preserve long-run evidence blocker", LONG_RUN_EVIDENCE_BLOCKER_CODE)
    component_results = report.get("component_results")
    if not isinstance(component_results, list) or report.get("component_count") != len(component_results):
        return ProfileValidationResult("FAIL", "runtime evidence profile component count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    component_pass_count = sum(1 for item in component_results if isinstance(item, dict) and item.get("status") == "PASS")
    if report.get("component_pass_count") != component_pass_count:
        return ProfileValidationResult("FAIL", "runtime evidence profile component pass count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("component_blocked_count") != len(component_results) - component_pass_count:
        return ProfileValidationResult("FAIL", "runtime evidence profile component blocked count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if component_pass_count != len(component_results) and report.get("status") == "PASS":
        return ProfileValidationResult(
            "BLOCKED",
            "runtime evidence profile cannot PASS when a component is not PASS",
            "RUNTIME_EVIDENCE_PROFILE_COMPONENT_NOT_PASS",
        )
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return ProfileValidationResult("FAIL", "runtime evidence profile blockers must be a list", "SCHEMA_IDENTITY_MISMATCH")
    if blockers and report.get("status") != "BLOCKED":
        return ProfileValidationResult("FAIL", "runtime evidence profile with blockers must be BLOCKED", "SCHEMA_IDENTITY_MISMATCH")
    if not blockers and report.get("status") != "PASS":
        return ProfileValidationResult("FAIL", "runtime evidence profile without blockers must PASS", "SCHEMA_IDENTITY_MISMATCH")
    if blockers and report.get("primary_blocker_code") not in blockers:
        return ProfileValidationResult("FAIL", "runtime evidence profile primary blocker mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if not blockers and report.get("primary_blocker_code") is not None:
        return ProfileValidationResult("FAIL", "runtime evidence profile primary blocker set without blockers", "SCHEMA_IDENTITY_MISMATCH")
    expected_duplicate_total = (
        int(report.get("duplicate_event_id_count") or 0)
        + int(report.get("duplicate_dedup_key_count") or 0)
        + int(report.get("duplicate_semantic_event_count") or 0)
        + int(report.get("duplicate_filled_order_key_count") or 0)
    )
    if expected_duplicate_total > 0 and "RECONCILIATION_REQUIRED" not in blockers:
        return ProfileValidationResult("BLOCKED", "duplicate runtime ledger evidence must require reconciliation", "RECONCILIATION_REQUIRED")
    if report.get("status") == "PASS":
        pass_required = {
            "loop_status": "PASS",
            "recovery_guard_status": "PASS",
            "runtime_sample_history_validation_status": "PASS",
            "runtime_sample_status": "COLLECTING",
            "ledger_runtime_evidence_status": "PASS",
            "idempotency_status": "PASS",
            "reconciliation_status": "PASS",
        }
        for field, expected in pass_required.items():
            if report.get(field) != expected:
                return ProfileValidationResult("FAIL", f"PASS profile requires {field}={expected}", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("accepted_cycle_sample_count") != report.get("completed_cycle_count"):
            return ProfileValidationResult("FAIL", "accepted runtime sample count must match completed bounded cycles", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("accepted_cycle_sample_count", 0) < 1 or report.get("source_ledger_jsonl_count", 0) < 1:
            return ProfileValidationResult("BLOCKED", "PASS profile requires actual bounded PAPER runtime and ledger artifacts", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    return ProfileValidationResult(report["status"], "Upbit PAPER runtime evidence collection profile is fail-closed", report.get("primary_blocker_code"))


def run_upbit_paper_runtime_evidence_collection_profile(
    *,
    requested_cycle_count: int = 2,
    duplicate_ledger_events: bool = False,
) -> dict[str, Any]:
    with TemporaryDirectory() as tmp:
        return build_upbit_paper_runtime_evidence_collection_profile_report(
            root=Path(tmp),
            requested_cycle_count=requested_cycle_count,
            duplicate_ledger_events=duplicate_ledger_events,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded Upbit PAPER runtime evidence collection profile.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH, help="JSON report path.")
    parser.add_argument("--requested-cycle-count", type=int, default=2, help="Bounded PAPER cycle count.")
    parser.add_argument(
        "--duplicate-ledger-events",
        action="store_true",
        help="Inject duplicate PAPER ledger events to prove reconciliation blocking.",
    )
    args = parser.parse_args()

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    report = run_upbit_paper_runtime_evidence_collection_profile(
        requested_cycle_count=args.requested_cycle_count,
        duplicate_ledger_events=args.duplicate_ledger_events,
    )
    result = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
    output = ROOT / args.output
    durable_atomic_write_json(output, report)
    print(json.dumps(report, indent=2))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
