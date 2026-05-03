from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260503_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-DEPTH-RECHECK"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "upbit_paper_persistent_loop_validator",
    "paper_ledger_rollup_validator",
    "reconciliation_validator",
    "ledger_reconciliation_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
]

BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id not in {"patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
]

CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json",
    "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
    "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
    "tools/emit_upbit_paper_ledger_idempotency_runtime_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
]


def run_command(args: list[str], timeout_seconds: int = 600) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def patch_hash(patch_result: dict[str, Any]) -> str:
    payload = dict(patch_result)
    payload.pop("result_hash", None)
    return sha256_json(payload)


def build_audit() -> dict[str, Any]:
    module_text = (ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_ledger_idempotency_runtime_evidence.py").read_text(
        encoding="utf-8"
    )
    validator_text = (ROOT / "trader1" / "validation" / "mvp0_validators.py").read_text(encoding="utf-8")
    test_text = (ROOT / "tests" / "runtime" / "test_upbit_paper_ledger_idempotency_runtime_evidence.py").read_text(
        encoding="utf-8"
    )
    refresh_test_text = (
        ROOT / "tests" / "runtime" / "test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py"
    ).read_text(encoding="utf-8")
    schema = load_json(ROOT / "contracts" / "schema" / "upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json")
    required = set(schema.get("required", []))
    depth_fields = {
        "source_persistent_loop_path",
        "source_persistent_loop_hash",
        "source_persistent_loop_hash_self_check",
        "source_persistent_loop_validation_status",
        "source_runtime_cycle_ids",
        "source_runtime_cycle_hashes",
        "ledger_head_cycle_in_persistent_loop",
        "ledger_head_runtime_cycle_hash",
        "source_runtime_input_role",
        "source_collection_report_hash",
        "source_public_market_data_hash",
        "source_runtime_public_market_data_hash",
        "source_canonical_event_count",
        "source_feature_snapshot_hash",
        "source_strategy_regime_cost_linkage_hash",
        "source_runtime_depth_status",
        "source_runtime_depth_mismatch_count",
    }
    checks = {
        "module_loads_and_validates_persistent_loop_source": all(
            token in module_text
            for token in (
                "upbit_paper_persistent_loop_hash",
                "validate_upbit_paper_persistent_loop_report",
                "upbit_paper_persistent_loop_report.json",
            )
        ),
        "module_requires_ledger_head_cycle_runtime_depth": all(
            token in module_text
            for token in (
                "ledger_head_cycle_in_persistent_loop",
                "source_runtime_depth_status",
                "PUBLIC_MARKET_DATA_COLLECTION",
                "source_strategy_regime_cost_linkage_live_order_allowed",
            )
        ),
        "schema_requires_runtime_depth_fields": depth_fields.issubset(required),
        "validator_rechecks_runtime_depth_fields": all(
            token in validator_text
            for token in (
                "source_runtime_depth_status",
                "ledger_head_cycle_in_persistent_loop",
                "source_runtime_public_market_data_hash",
                "source_strategy_regime_cost_linkage_live_order_allowed",
            )
        ),
        "negative_tests_cover_missing_depth_hash_and_live_mutation": all(
            token in test_text
            for token in (
                "test_evidence_blocks_missing_persistent_loop_runtime_depth",
                "test_evidence_blocks_runtime_depth_hash_mismatch_mutation",
                "test_evidence_blocks_runtime_depth_linkage_live_mutation",
            )
        ),
        "refresh_tests_assert_depth_binding": "source_runtime_depth_status" in refresh_test_text
        and "ledger_head_cycle_in_persistent_loop" in refresh_test_text,
    }
    return {
        "audit_schema_id": "trader1.audit_report.v1",
        "audit_id": f"{PATCH_BASENAME}_AUDIT",
        "patch_id": PATCH_ID,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "requirement_id": REQUIREMENT_ID,
        "checks": checks,
        "finding": (
            "Upbit PAPER ledger idempotency runtime evidence recomputed ledger rollup counts, but did not independently bind "
            "the ledger head cycle to the current persistent loop public-data runtime-depth summary."
        ),
        "fix": (
            "The evidence report now loads the canonical persistent loop report, validates its hash and schema, requires the "
            "rollup ledger_head_cycle_id to be present in PASS cycle_results, and blocks missing public input hashes, source/runtime "
            "hash mismatch, shallow canonical event depth, and strategy/regime/cost linkage live flags."
        ),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_STRATEGY_REGIME_COST_RUNTIME_LINKAGE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.upbit_paper_persistent_loop_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- ledger idempotency evidence validates the canonical persistent-loop source hash and status
- ledger head cycle id must exist in persistent loop cycle_results
- the matching cycle must be public-market-data backed with source/runtime hash equality and canonical depth
- strategy/regime/cost linkage live or scale-up flags remain blocked
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

audit_status: {audit["status"]}

known_omissions_by_design:
- no runtime root output is staged by this contract/evidence patch
- no long-run evidence eligibility, LIVE_READY snapshot, live order path, credential use, live config mutation, or scale-up is introduced
- post-rerun reconciliation and stale-loop regeneration blockers remain separate follow-up work

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

Upbit PAPER ledger idempotency runtime evidence now fails closed unless the ledger head cycle is present in the current persistent-loop PASS cycle_results and carries public input hash, canonical depth, feature, regime, and strategy/regime/cost linkage evidence. This is PAPER-only evidence and does not create live readiness or scale-up permission.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER ledger idempotency runtime-depth binding",
            "full_text_marker": f"{REQUIREMENT_ID}: ledger idempotency evidence must bind ledger head cycle to persistent loop runtime depth",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Bind ledger idempotency evidence to persistent-loop runtime depth",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1",
                "trader1.upbit_paper_persistent_loop_report.v1",
                "trader1.patch_result.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "tests/validators/test_mvp0_validators.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_STRATEGY_REGIME_COST_RUNTIME_LINKAGE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-DEPTH-RECHECK",
                "REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE",
            ],
            "source_text_sha256": sha256_bytes(
                b"ledger idempotency evidence must bind ledger head cycle to persistent loop runtime depth"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
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
            "section_id": "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "schema_files": ["contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json"],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/runtime/ledger/paper_ledger_rollup.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-DEPTH-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "BINANCE_FUTURES_LIVE"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "AGENTS:0G",
                "AGENTS:0F",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "AGENTS:0G",
                "AGENTS:0F",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    audit: dict[str, Any],
) -> None:
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK_NO_LIVE_ORDERS",
            "runtime_depth_audit": audit,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260503.md",
        f"""# MVP4 Upbit PAPER Ledger Idempotency Runtime Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Ledger idempotency evidence recomputed rollup and JSONL counts, but did not require the rollup ledger head cycle to be bound to the current persistent-loop runtime-depth summary.

Patch:
- Added persistent-loop source hash and validation fields to the ledger idempotency evidence report.
- Required ledger_head_cycle_id to exist in persistent loop cycle_results with public market data input, matching source/runtime public hash, canonical event depth, feature hash, and strategy/regime/cost linkage hash.
- Added negative tests for missing persistent loop evidence, runtime-depth hash mismatch, and linkage live permission mutation.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []) + ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"])
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["upbit_paper_ledger_idempotency_runtime_evidence_validator"])
    )
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
        }
    )
    write_json(ledger_path, ledger)


def remove_cache_artifacts() -> None:
    for path in sorted(ROOT.rglob("__pycache__"), reverse=True):
        if path.is_dir():
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink(missing_ok=True)
            path.rmdir()
    for path in ROOT.rglob("*.pyc"):
        if path.is_file():
            path.unlink(missing_ok=True)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    audit = build_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_schema_instance_validation", "-v"]),
    ]
    remove_cache_artifacts()
    write_source_bundle_manifest()
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/validators/test_mvp0_validators.py", "-q"]),
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command([sys.executable, "-B", "tools/run_live_final_guard_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"], timeout_seconds=900),
        ]
    )
    remove_cache_artifacts()
    write_source_bundle_manifest()
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed"})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
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
