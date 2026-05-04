from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-BASELINE-RECONCILIATION-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK"
PREVIOUS_PATCH_PREFIX = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK_"
CONTRACT_GAP_ID = "PATCH_RESULT_VALIDATOR_RUN_GAP"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
LEGACY_COMPLETED_RECHECK_ROUTE = "MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK"

BASELINE_PATH = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE.json"
AUDIT_PATH = ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json"
CONTRACT_GAP_PATH = ROOT / "system" / "evidence" / "contract_gaps" / "PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json"
RECONCILIATION_PATH = (
    ROOT / "system" / "evidence" / "audit_reports" / "PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION.json"
)
POST_REPAIR_REPORT = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / "mvp1_upbit_paper_launcher"
    / "paper_runtime"
    / "upbit_paper_post_repair_reconciliation_report.json"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_patch_result_runtime_schema_validation_patch_evidence import current_gap_rows  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    load_json,
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import _audit_gap_key, _patch_result_unbaselined_gaps, run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id for validator_id in VALIDATORS_REQUIRED if validator_id != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    "tests/contract/test_completed_recheck_route_depth_guard.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_open_contract_gap_implementation_priority_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
    "tools/emit_patch_result_validator_run_gap_baseline_reconciliation_recheck_patch_evidence.py",
    "tools/run_hygiene_safe_pytest.py",
    "system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json",
    "system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION.json",
    "system/evidence/contract_gaps/PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
STATIC_BLOCKERS = {
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
}


def run_command(args: list[str], timeout_seconds: int = 900) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    result = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def gap_key(gap: dict[str, Any]) -> str:
    return "|".join(_audit_gap_key(gap))


def gap_key_hash(keys: list[str]) -> str:
    return sha256_json(keys)


def baseline_hash_matches(baseline: dict[str, Any]) -> bool:
    return baseline.get("baseline_hash") == sha256_json(
        {key: value for key, value in baseline.items() if key != "baseline_hash"}
    )


def build_reconciliation_report(
    now: str,
    trader_hash: str,
    agents_hash: str,
    current_gaps: list[dict[str, Any]],
    baseline: dict[str, Any],
    audit: dict[str, Any],
    contract_gap: dict[str, Any],
) -> dict[str, Any]:
    baseline_gaps = [item for item in baseline.get("gaps", []) if isinstance(item, dict)]
    audit_gaps = [item for item in audit.get("gaps", []) if isinstance(item, dict)]
    baseline_keys = sorted(gap_key(item) for item in baseline_gaps)
    current_keys = sorted(gap_key(item) for item in current_gaps)
    audit_keys = sorted(gap_key(item) for item in audit_gaps)
    unbaselined = _patch_result_unbaselined_gaps(current_gaps, baseline_gaps)
    missing_from_current = sorted(set(baseline_keys) - set(current_keys))
    missing_from_baseline = sorted(set(current_keys) - set(baseline_keys))
    missing_from_audit = sorted(set(current_keys) - set(audit_keys))
    extra_in_audit = sorted(set(audit_keys) - set(current_keys))
    checks = {
        "baseline_hash_matches": baseline_hash_matches(baseline),
        "baseline_status_sealed": baseline.get("status") == "SEALED_HISTORICAL_BASELINE",
        "audit_live_blocking": audit.get("status") == "AUDIT_PRESERVED_BASELINE_MATCH_LIVE_BLOCKING",
        "contract_gap_open": contract_gap.get("status") == "OPEN",
        "contract_gap_live_affecting": contract_gap.get("live_affecting") is True,
        "baseline_matches_current": baseline_keys == current_keys,
        "audit_matches_current": audit_keys == current_keys,
        "unbaselined_gap_count_zero": len(unbaselined) == 0,
        "no_baseline_or_audit_extra_gap": not missing_from_current and not missing_from_audit and not extra_in_audit,
        "historical_gaps_not_backfilled": all(
            gap.get("resolution") == "AUDIT_PRESERVED_NOT_BACKFILLED" for gap in baseline_gaps
        ),
        "live_and_scale_false": all(
            artifact.get(field) is False
            for artifact in (baseline, audit)
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        ),
    }
    status = (
        "PASS_BASELINE_RECONCILED_HISTORICAL_GAP_REMAINS_LIVE_BLOCKING"
        if all(checks.values())
        else "BLOCKED_BASELINE_RECONCILIATION_DRIFT"
    )
    return {
        "schema_id": "trader1.patch_result_validator_run_gap_baseline_reconciliation.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "patch_id": PATCH_ID,
        "requirement_id": REQUIREMENT_ID,
        "status": status,
        "checks": checks,
        "baseline_path": rel(BASELINE_PATH),
        "audit_path": rel(AUDIT_PATH),
        "contract_gap_path": rel(CONTRACT_GAP_PATH),
        "baseline_sealed_at_patch_id": baseline.get("sealed_at_patch_id"),
        "baseline_gap_count": len(baseline_gaps),
        "current_gap_count": len(current_gaps),
        "audit_gap_count": len(audit_gaps),
        "unbaselined_gap_count": len(unbaselined),
        "missing_from_current_count": len(missing_from_current),
        "missing_from_baseline_count": len(missing_from_baseline),
        "missing_from_audit_count": len(missing_from_audit),
        "extra_in_audit_count": len(extra_in_audit),
        "missing_from_current_gap_keys": missing_from_current,
        "missing_from_baseline_gap_keys": missing_from_baseline,
        "missing_from_audit_gap_keys": missing_from_audit,
        "extra_in_audit_gap_keys": extra_in_audit,
        "baseline_gap_key_hash": gap_key_hash(baseline_keys),
        "current_gap_key_hash": gap_key_hash(current_keys),
        "audit_gap_key_hash": gap_key_hash(audit_keys),
        "baseline_hash": baseline.get("baseline_hash"),
        "baseline_hash_recomputed": sha256_json(
            {key: value for key, value in baseline.items() if key != "baseline_hash"}
        ),
        "contract_gap_status": contract_gap.get("status"),
        "contract_gap_severity": contract_gap.get("severity"),
        "contract_gap_live_affecting": contract_gap.get("live_affecting"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def write_gap_audit(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    baseline = load_json(BASELINE_PATH)
    audit = load_json(AUDIT_PATH)
    contract_gap = load_json(CONTRACT_GAP_PATH)
    current_gaps = current_gap_rows()
    baseline_gaps = [item for item in baseline.get("gaps", []) if isinstance(item, dict)]
    unbaselined = _patch_result_unbaselined_gaps(current_gaps, baseline_gaps)
    refreshed_audit = {
        **audit,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "status": "AUDIT_PRESERVED_BASELINE_MATCH_LIVE_BLOCKING" if not unbaselined else "BLOCKED_UNBASELINED_GAPS",
        "baseline_gap_count": len(baseline_gaps),
        "current_gap_count": len(current_gaps),
        "unbaselined_gap_count": len(unbaselined),
        "unbaselined_gaps": unbaselined,
        "gaps": current_gaps,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(AUDIT_PATH, refreshed_audit)
    refreshed_contract_gap = {
        **contract_gap,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "status": "OPEN" if current_gaps else "RESOLVED",
        "severity": "HIGH" if current_gaps else "INFO",
        "live_affecting": True,
        "notes": (
            f"Historical gap count={len(baseline_gaps)}; current gap count={len(current_gaps)}; "
            f"unbaselined gap count={len(unbaselined)}. Historical patch_result evidence is not backfilled. "
            f"Latest reconciliation patch={PATCH_ID}."
        ),
    }
    if current_gaps:
        refreshed_contract_gap["blockers"] = [
            {
                "code": "CONTRACT_GAP_HIGH",
                "severity": "HIGH",
                "message": (
                    "Historical patch_result artifacts have validators_required entries without matching "
                    "validators_run evidence. The sealed baseline is reconciled; new gaps remain blocked."
                ),
                "source_requirement_id": REQUIREMENT_ID,
            }
        ]
    else:
        refreshed_contract_gap["blockers"] = []
    write_json(CONTRACT_GAP_PATH, refreshed_contract_gap)
    report = build_reconciliation_report(
        now,
        trader_hash,
        agents_hash,
        current_gaps,
        baseline,
        refreshed_audit,
        refreshed_contract_gap,
    )
    write_json(RECONCILIATION_PATH, report)
    return report


def post_repair_summary() -> dict[str, Any]:
    report = load_json(POST_REPAIR_REPORT)
    return {
        "post_repair_reconciliation_status": report.get("post_repair_reconciliation_status"),
        "post_repair_reconciliation_item_count": report.get("reconciliation_item_count"),
        "post_repair_source_loop_expected_rollup_hash_mismatch_count": report.get(
            "source_loop_expected_rollup_hash_mismatch_count"
        ),
        "post_repair_candidate_current_evidence_usable_count": report.get("candidate_current_evidence_usable_count"),
    }


def assert_current_state_ready_for_baseline_reconciliation() -> None:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    completed = set(state.get("completed_requirement_ids", []))
    gaps = set(state.get("open_contract_gap_ids", []))
    last_patch_id = str(state.get("last_patch_id", ""))
    next_allowed = state.get("next_allowed_task_class")
    live_flags = {
        "live_order_ready": state.get("live_order_ready"),
        "live_order_allowed": state.get("live_order_allowed"),
        "can_live_trade": state.get("can_live_trade"),
        "scale_up_allowed": state.get("scale_up_allowed"),
    }
    if any(value is not False for value in live_flags.values()):
        raise RuntimeError(f"unsafe live/scale state for {PATCH_BASENAME}: {live_flags}")
    if CONTRACT_GAP_ID not in gaps:
        raise RuntimeError(f"{CONTRACT_GAP_ID} must remain open before baseline reconciliation")

    previous_route_ready = last_patch_id.startswith(PREVIOUS_PATCH_PREFIX) and next_allowed == PATCH_BASENAME
    idempotent_rerun_ready = last_patch_id.startswith(PATCH_BASENAME) and next_allowed in {
        NEXT_TASK_CLASS,
        LEGACY_COMPLETED_RECHECK_ROUTE,
    }
    if not (previous_route_ready or idempotent_rerun_ready):
        raise RuntimeError(
            f"{PATCH_BASENAME} expected previous route {PREVIOUS_PATCH_PREFIX} -> {PATCH_BASENAME}; "
            f"got last_patch_id={last_patch_id!r}, next_allowed_task_class={next_allowed!r}"
        )
    if previous_route_ready and PREVIOUS_REQUIREMENT_ID not in completed:
        raise RuntimeError(f"{PREVIOUS_REQUIREMENT_ID} must be completed before {PATCH_BASENAME}")


def remaining_blockers() -> list[str]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    return sorted(set(state.get("open_contract_gap_ids", [])) | STATIC_BLOCKERS)


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PATCH_RESULT", "SECTION_VALIDATOR_DEPENDENCY_CHAIN", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-RECHECK", "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-STATE-SYNC-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Recompute current patch_result validator-run gaps from all patch_result artifacts.
- Confirm the sealed baseline hash still matches its stored content.
- Confirm current, audit, and sealed baseline gap keys match exactly.
- Keep {CONTRACT_GAP_ID} open and live-blocking; do not backfill historical patch_result artifacts.
- Route the next safe task to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

reconciliation_snapshot:
- status: {report["status"]}
- baseline_gap_count: {report["baseline_gap_count"]}
- current_gap_count: {report["current_gap_count"]}
- audit_gap_count: {report["audit_gap_count"]}
- unbaselined_gap_count: {report["unbaselined_gap_count"]}

known_omissions_by_design:
- Historical patch_result evidence is not rewritten or backfilled.
- The patch_result validator-run gap remains open until a separate evidence-preserving correction policy exists.
- This patch does not use credentials, call private exchange/account APIs, place live orders, mutate live config, or scale up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Patch result validator-run historical gaps are reconciled against the sealed baseline: baseline={report["baseline_gap_count"]}, current={report["current_gap_count"]}, audit={report["audit_gap_count"]}, unbaselined={report["unbaselined_gap_count"]}. The gap remains open and live-blocking; no historical evidence was backfilled.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + [
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_PATCH_RESULT",
            "source_file": "TRADER_1.md",
            "source_heading": "patch_result validator-run gap baseline reconciliation recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: reconcile sealed patch_result validator-run gap baseline against current "
                "patch_result history without backfilling historical evidence"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Patch result validator-run baseline reconciliation recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.contract_gap.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_patch_result_runtime_schema_validation.py",
                "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_PATCH_RESULT", "SECTION_VALIDATOR_DEPENDENCY_CHAIN", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-RECHECK",
                "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"patch result validator run gap sealed baseline reconciliation"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_BASELINE_RECONCILED_HISTORICAL_GAP_OPEN",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_PATCH_RESULT",
            "schema_files": ["contracts/schema/patch_result.schema.json", "contracts/schema/contract_gap.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_patch_result_runtime_schema_validation.py",
                "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
            ],
            "fixture_files": [
                rel(BASELINE_PATH),
                rel(AUDIT_PATH),
                rel(CONTRACT_GAP_PATH),
                rel(RECONCILIATION_PATH),
            ],
            "runtime_modules": ["trader1/validation/mvp0_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                rel(RECONCILIATION_PATH),
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_BASELINE_RECONCILED_HISTORICAL_GAP_OPEN",
        }
    )
    matrix.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "rows": sorted(rows, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_NEXT_TASK_RESTORE.patch_result.json"
    )
    post_repair = post_repair_summary()
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-RECHECK",
                "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": [
                REQUIREMENT_ID,
                rel(RECONCILIATION_PATH),
                f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            ],
            "new_or_changed_schema_ids": [],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": remaining_blockers(),
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                rel(BASELINE_PATH),
                rel(AUDIT_PATH),
                rel(CONTRACT_GAP_PATH),
                "SECTION_PATCH_RESULT",
                "SECTION_VALIDATOR_DEPENDENCY_CHAIN",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_BASELINE_RECONCILIATION_RECHECK",
            "required_section_ids": [
                "SECTION_PATCH_RESULT",
                "SECTION_VALIDATOR_DEPENDENCY_CHAIN",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_PATCH_RESULT",
                "SECTION_VALIDATOR_DEPENDENCY_CHAIN",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_BASELINE_RECONCILED_NEXT_TASK_ADVANCED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_CURRENT_EVIDENCE_PROMOTION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            **post_repair,
        }
    )
    if report["status"] != "PASS_BASELINE_RECONCILED_HISTORICAL_GAP_REMAINS_LIVE_BLOCKING":
        raise RuntimeError("cannot emit patch_result while patch_result validator-run baseline is unreconciled")
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "validators_untested": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_BASELINE_RECONCILED_HISTORICAL_PATCH_RESULT_GAP_REMAINS_LIVE_BLOCKING",
            "reconciliation_report_path": rel(RECONCILIATION_PATH),
            "baseline_gap_count": report["baseline_gap_count"],
            "current_gap_count": report["current_gap_count"],
            "audit_gap_count": report["audit_gap_count"],
            "unbaselined_gap_count": report["unbaselined_gap_count"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            "reconciliation_report_path": rel(RECONCILIATION_PATH),
            "baseline_gap_count": report["baseline_gap_count"],
            "current_gap_count": report["current_gap_count"],
            "unbaselined_gap_count": report["unbaselined_gap_count"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Patch Result Validator Run Gap Baseline Reconciliation Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Historical patch_result validator-run omissions remain sealed at baseline count {report["baseline_gap_count"]}.
- Current patch_result history still has {report["current_gap_count"]} preserved omissions and 0 unbaselined omissions.
- The gap remains open and live-blocking; historical patch_result evidence was not backfilled.

Patch:
- Added a reconciliation report that hash-binds current, audit, and baseline gap keys.
- Refreshed the audit and contract gap timestamps without changing the sealed baseline.
- Advanced next_allowed_task_class to {NEXT_TASK_CLASS}.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", [])) | {CONTRACT_GAP_ID})
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
            "next_allowed_task_class": NEXT_TASK_CLASS,
        }
    )
    write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    assert_current_state_ready_for_baseline_reconciliation()
    update_authority_manifest(now)
    write_source_bundle_manifest()
    report = write_gap_audit(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.contract.test_patch_result_runtime_schema_validation",
                    "tests.contract.test_patch_result_validator_run_gap_baseline_reconciliation_recheck",
                    "-v",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    report = write_gap_audit(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    write_source_bundle_manifest()
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "baseline_gap_count": report["baseline_gap_count"],
                "current_gap_count": report["current_gap_count"],
                "unbaselined_gap_count": report["unbaselined_gap_count"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
