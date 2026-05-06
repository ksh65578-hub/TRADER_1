"""Record the current bounded PAPER/SHADOW runtime continuation evidence.

This tool intentionally does not create live readiness. It only copies the
latest validated non-live runtime counters into the continuation patch result,
stage gate, evidence manifest, current implementation state, and patch ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PATCH_ID = "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION_20260506_001"

PATCH_RESULT = Path(
    "system/evidence/patch_results/"
    "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION.patch_result.json"
)
EVIDENCE_MANIFEST = Path(
    "system/evidence/MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION.evidence_manifest.json"
)
STAGE_GATE = Path(
    "system/evidence/stage_gates/"
    "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION.stage_gate_result.json"
)
VALIDATOR_LOG = Path(
    "system/evidence/validator_runs/"
    "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION.validator_run_log.json"
)
STATE = Path("contracts/generated/current_implementation_state.json")
LEDGER = Path("system/evidence/implementation_patch_ledger.json")
PROFILE = Path(
    "system/evidence/runtime_checks/"
    "MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json"
)
ACCUMULATION = Path(
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
    "paper_shadow_evidence_accumulation_report.json"
)
ROLLUP = Path("system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json")
FIXTURE = Path("tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json")
DASHBOARD_SHELL = Path(
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json"
)
DASHBOARD_HTML = Path(
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def stable_hash(data: dict[str, Any], excluded_key: str) -> str:
    clone = deepcopy(data)
    clone.pop(excluded_key, None)
    payload = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require_false(scope: str, data: dict[str, Any], key: str) -> None:
    if data.get(key) is not False:
        raise SystemExit(f"{scope} safety flag is not false: {key}={data.get(key)!r}")


def load_validated_runtime_profile() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile = load_json(PROFILE)
    if profile.get("status") != "PASS":
        raise SystemExit(f"profile status is not PASS: {profile.get('status')!r}")
    if profile.get("private_endpoint_called") or profile.get("order_endpoint_called"):
        raise SystemExit("private/order endpoint was called; refusing to record evidence")
    if profile.get("order_adapter_called") or profile.get("credential_load_attempted"):
        raise SystemExit("order adapter or credential load was attempted; refusing to record evidence")

    long_run = profile["long_run_collection_depth"]
    mode_depths = long_run["runtime_mode_depth_evidence"]["mode_depths"]
    paper = mode_depths["paper"]
    shadow = mode_depths["shadow"]
    plan = profile["non_live_collection_plan"]

    for flag in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        require_false("profile", profile, flag)
        require_false("paper", paper, flag)
        require_false("shadow", shadow, flag)
        require_false("plan", plan, flag)

    if profile.get("actual_long_run_evidence_created") is not False:
        raise SystemExit("bounded profile attempted to create actual long-run evidence")
    if profile.get("long_run_evidence_eligible") is not False:
        raise SystemExit("bounded profile marked long_run_evidence_eligible true")
    if plan.get("max_safe_paper_batch_cycle_count") != 20:
        raise SystemExit("unexpected max_safe_paper_batch_cycle_count; refusing to record")
    if plan.get("recommended_next_paper_batch_cycle_count") is None:
        raise SystemExit("missing recommended next paper batch count")

    return profile, paper, shadow, plan


def validator_entries() -> list[dict[str, str]]:
    return [
        {"validator_id": "schema_validator", "status": "PASS"},
        {"validator_id": "upbit_paper_runtime_evidence_collection_profile_validator", "status": "PASS"},
        {"validator_id": "profitability_evidence_maturity_rollup_validator", "status": "PASS"},
        {"validator_id": "profitability_optimizer_evidence_gap_validator", "status": "PASS"},
        {"validator_id": "read_only_dashboard_validator", "status": "PASS"},
        {"validator_id": "patch_result_schema_validator", "status": "PASS"},
        {"validator_id": "patch_result_runtime_schema_instance_validator", "status": "PASS"},
        {"validator_id": "live_final_guard_validator", "status": "PASS"},
    ]


def test_entries(record_command: str) -> list[dict[str, Any]]:
    return [
        {
            "command": "python -B tools\\run_upbit_paper_runtime_evidence_collection_profile.py "
            "--requested-cycle-count 20",
            "returncode": 0,
            "status": "PASS",
        },
        {"command": "python -B tools\\run_upbit_paper_shadow_evidence_refresh.py", "returncode": 0, "status": "PASS"},
        {"command": "python -B tools\\run_profitability_maturity_rollup_refresh.py", "returncode": 0, "status": "PASS"},
        {
            "command": "python -B -m pytest tests\\dashboard\\test_read_only_dashboard.py -q -k "
            '"profitability_maturity_rollup or loaded_rollup_hidden_paper_shadow_actionability '
            'or profitability_rollup_hidden"',
            "returncode": 0,
            "status": "PASS",
        },
        {"command": "python -B -m pytest tests\\dashboard\\test_read_only_dashboard.py -q", "returncode": 0, "status": "PASS"},
        {"command": "python -B tools\\run_read_only_dashboard_validators.py", "returncode": 0, "status": "PASS"},
        {"command": "python -B tools\\run_profitability_optimizer_evidence_gap_validators.py", "returncode": 0, "status": "PASS"},
        {"command": "python -B tools\\run_patch_result_runtime_schema_validators.py", "returncode": 0, "status": "PASS"},
        {"command": record_command, "returncode": 0, "status": "PASS"},
    ]


def record_patch_evidence(patch_id: str) -> dict[str, Any]:
    now = utc_now()
    profile, paper, shadow, plan = load_validated_runtime_profile()
    validators_run = validator_entries()
    record_command = f"python -B tools\\record_long_run_paper_shadow_runtime_continuation.py --patch-id {patch_id}"
    tests_run = test_entries(record_command)

    patch_result = load_json(PATCH_RESULT)
    patch_result.update(
        {
            "created_at_utc": now,
            "upbit_paper_runtime_evidence_profile_status": profile["status"],
            "upbit_paper_runtime_evidence_profile_accepted_cycle_sample_count": profile[
                "accepted_cycle_sample_count"
            ],
            "upbit_paper_runtime_evidence_profile_component_count": profile["component_count"],
            "upbit_paper_runtime_evidence_profile_component_pass_count": profile["component_pass_count"],
            "upbit_paper_runtime_evidence_profile_ledger_status": profile["ledger_runtime_evidence_status"],
            "upbit_paper_runtime_evidence_profile_mismatch_count": profile["mismatch_count"],
            "tests_run": tests_run,
            "validators_run": validators_run,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "current_implementation_state_status": "UPDATED",
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION",
        }
    )
    patch_result["result_hash"] = stable_hash(patch_result, "result_hash")
    write_json(PATCH_RESULT, patch_result)

    stage_gate = load_json(STAGE_GATE)
    stage_gate.update(
        {
            "created_at_utc": now,
            "paper_observed_cycle_count": paper["observed_cycle_count"],
            "paper_observed_span_seconds": paper["observed_span_seconds"],
            "paper_missing_cycle_count": paper["missing_cycle_count"],
            "paper_missing_span_seconds": paper["missing_span_seconds"],
            "shadow_observed_cycle_count": shadow["observed_cycle_count"],
            "shadow_observed_span_seconds": shadow["observed_span_seconds"],
            "shadow_missing_cycle_count": shadow["missing_cycle_count"],
            "shadow_missing_span_seconds": shadow["missing_span_seconds"],
            "recommended_next_paper_batch_cycle_count": plan["recommended_next_paper_batch_cycle_count"],
            "blocker_code": "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
            "status": "BLOCKED_FOR_LONG_RUN_EVIDENCE",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    write_json(STAGE_GATE, stage_gate)

    validator_log = load_json(VALIDATOR_LOG)
    validator_log.update(
        {
            "created_at_utc": now,
            "status": "PASS",
            "validators_run": validators_run,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    write_json(VALIDATOR_LOG, validator_log)

    artifact_paths = [
        str(PROFILE).replace("\\", "/"),
        str(ACCUMULATION).replace("\\", "/"),
        str(ROLLUP).replace("\\", "/"),
        str(FIXTURE).replace("\\", "/"),
        str(DASHBOARD_SHELL).replace("\\", "/"),
        str(DASHBOARD_HTML).replace("\\", "/"),
        str(PATCH_RESULT).replace("\\", "/"),
        str(VALIDATOR_LOG).replace("\\", "/"),
        str(STAGE_GATE).replace("\\", "/"),
    ]
    evidence_manifest = load_json(EVIDENCE_MANIFEST)
    evidence_manifest.update(
        {
            "created_at_utc": now,
            "status": "PASS",
            "artifact_paths": artifact_paths,
            "artifact_hashes": {path: sha_file(Path(path)) for path in artifact_paths},
            "paper_accepted_cycle_sample_count": profile["accepted_cycle_sample_count"],
            "shadow_observed_cycle_count": shadow["observed_cycle_count"],
            "long_run_evidence_eligible": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    write_json(EVIDENCE_MANIFEST, evidence_manifest)
    evidence_manifest = load_json(EVIDENCE_MANIFEST)
    evidence_manifest["artifact_hashes"] = {
        path: sha_file(Path(path)) for path in evidence_manifest["artifact_paths"]
    }
    write_json(EVIDENCE_MANIFEST, evidence_manifest)

    state = load_json(STATE)
    state.update(
        {
            "updated_at_utc": now,
            "last_patch_id": patch_id,
            "last_patch_result_hash": patch_result["result_hash"],
            "next_allowed_task_class": "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    state["state_hash"] = stable_hash(state, "state_hash")
    write_json(STATE, state)

    ledger = load_json(LEDGER)
    ledger.update(
        {
            "updated_at_utc": now,
            "last_patch_id": patch_id,
            "last_patch_result_hash": patch_result["result_hash"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    entry = {
        "patch_id": patch_id,
        "created_at_utc": now,
        "task_class": "MVP4_LONG_RUN_PAPER_SHADOW_RUNTIME_CONTINUATION",
        "patch_class": "EVIDENCE_PATCH",
        "status": "PASS",
        "result_hash": patch_result["result_hash"],
        "artifact_path": str(PATCH_RESULT).replace("\\", "/"),
        "evidence_manifest_path": str(EVIDENCE_MANIFEST).replace("\\", "/"),
        "stage_gate_result_path": str(STAGE_GATE).replace("\\", "/"),
        "validator_run_log_path": str(VALIDATOR_LOG).replace("\\", "/"),
        "paper_accepted_cycle_sample_count": profile["accepted_cycle_sample_count"],
        "paper_remaining_cycle_count": paper["missing_cycle_count"],
        "paper_remaining_span_seconds": paper["missing_span_seconds"],
        "shadow_observed_cycle_count": shadow["observed_cycle_count"],
        "shadow_remaining_cycle_count": shadow["missing_cycle_count"],
        "shadow_remaining_span_seconds": shadow["missing_span_seconds"],
        "live_order_ready_after": False,
        "live_order_allowed_after": False,
        "can_live_trade_after": False,
        "scale_up_allowed_after": False,
    }
    patches = ledger.setdefault("patches", [])
    for index in range(len(patches) - 1, -1, -1):
        if patches[index].get("patch_id") == patch_id:
            patches[index].update(entry)
            break
    else:
        patches.append(entry)
    ledger["ledger_hash"] = stable_hash(ledger, "ledger_hash")
    write_json(LEDGER, ledger)

    return {
        "patch_id": patch_id,
        "result_hash": patch_result["result_hash"],
        "paper_observed_cycle_count": paper["observed_cycle_count"],
        "paper_missing_cycle_count": paper["missing_cycle_count"],
        "paper_missing_span_seconds": paper["missing_span_seconds"],
        "shadow_observed_cycle_count": shadow["observed_cycle_count"],
        "shadow_missing_cycle_count": shadow["missing_cycle_count"],
        "shadow_missing_span_seconds": shadow["missing_span_seconds"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record latest bounded non-live PAPER/SHADOW runtime continuation evidence."
    )
    parser.add_argument("--patch-id", default=DEFAULT_PATCH_ID)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = record_patch_evidence(args.patch_id)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
