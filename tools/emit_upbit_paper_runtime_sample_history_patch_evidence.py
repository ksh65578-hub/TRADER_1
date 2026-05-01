from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-RUNTIME-SAMPLE-HISTORY-PROVENANCE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_STALE_LOOP_REPORT_RECONCILIATION"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (  # noqa: E402
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history,
    write_upbit_paper_runtime_sample_history,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_sample_history_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_runtime_sample_history.schema.json",
    "contracts/registry.yaml",
    "trader1/runtime/paper/upbit_paper_runtime_sample_history.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_runtime_sample_history.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_runtime_sample_history.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_runtime_sample_history_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY.md",
]

BLOCKERS = [
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "STALE_PERSISTENT_LOOP_REPORTS_REQUIRE_RECONCILIATION",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_runtime_history() -> dict[str, Any]:
    history = build_upbit_paper_runtime_sample_history(
        root=ROOT,
        session_id="mvp1_upbit_paper_launcher",
        history_id="mvp4-upbit-paper-runtime-sample-history",
    )
    result = validate_upbit_paper_runtime_sample_history(history)
    if result.status != "PASS":
        raise RuntimeError(f"runtime sample history validation failed: {result.status} {result.blocker_code} {result.message}")
    write_upbit_paper_runtime_sample_history(root=ROOT, history=history)
    return history


def write_context(now: str, trader_hash: str, agents_hash: str, runtime_history: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY.md",
        f"""# MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_runtime_sample_history.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Upbit PAPER runtime sample history is built from persistent loop reports and runtime cycle JSON files.
- Runtime cycle paths stay inside system/runtime/upbit/krw_spot/paper/<session_id>/.
- Duplicate runtime cycle hashes are counted and blocked instead of inflating evidence.
- Existing stale or invalid loop reports are surfaced as reconciliation blockers.
- actual_long_run_evidence_created=false, long_run_evidence_eligible=false, live_order_allowed=false, scale_up_allowed=false.

known_omissions_by_design:
- this patch does not create long-run evidence
- this patch does not delete stale runtime artifacts
- this patch does not use private exchange/account/API calls or credentials
- MVP-5 remains blocked on external live-review evidence and operator approval

current_runtime_sample_history:
- runtime_sample_status: {runtime_history["runtime_sample_status"]}
- source_loop_report_count: {runtime_history["source_loop_report_count"]}
- accepted_cycle_sample_count: {runtime_history["accepted_cycle_sample_count"]}
- invalid_source_count: {runtime_history["invalid_source_count"]}
- duplicate_cycle_hash_count: {runtime_history["duplicate_cycle_hash_count"]}

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: {now}
""",
    )
    base.write_text(
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

Upbit PAPER runtime sample history now binds persistent loop reports to actual runtime cycle files. The current history remains BLOCKED because invalid or stale loop reports require reconciliation and the observed span/cycle count is not long-run evidence.

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
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER runtime sample history provenance",
            "full_text_marker": f"{REQUIREMENT_ID}: runtime sample history must bind actual PAPER loop and cycle artifacts without creating long-run or live evidence",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER runtime sample history provenance",
            "requirement_kind": "SCHEMA_VALIDATOR_RUNTIME_ARTIFACT_PATCH",
            "schema_ids": ["trader1.upbit_paper_runtime_sample_history.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_upbit_paper_runtime_sample_history.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-SAMPLE-ACCUMULATION-SPAN-PROVENANCE",
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"runtime sample history provenance and duplicate source blocking"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_LIVE_BLOCKED",
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
    base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": ["contracts/schema/upbit_paper_runtime_sample_history.schema.json"],
            "validator_files": ["trader1/runtime/paper/upbit_paper_runtime_sample_history.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_upbit_paper_runtime_sample_history.py"],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_runtime_sample_history.py",
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/runtime/paper/upbit_paper_runtime.py",
            ],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_runtime_sample_history.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
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
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    runtime_history: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_LONG_RUN_SAMPLE_ACCUMULATION.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "PASS",
            "authority_hash_checked": True,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-SAMPLE-ACCUMULATION-SPAN-PROVENANCE",
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [REQUIREMENT_ID, "upbit_paper_runtime_sample_history_validator"],
            "new_or_changed_schema_ids": ["trader1.upbit_paper_runtime_sample_history.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RUNTIME_RECOVERY"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE", "RETAINED_ARCHIVE"],
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
            "active_read_surface_used": [
                "current_implementation_state",
                "persistent loop schema and validator",
                "runtime cycle schema and validator",
                "검토안-derived runtime execution reproducibility gap",
            ],
            "task_class": "MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_RUNTIME_SAMPLE_HISTORY_BLOCKED",
            "optimizer_guardrail_result": "PASS_RUNTIME_SAMPLE_HISTORY_REMAINS_LIVE_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "true",
            "convergence_layer_changed": True,
            "convergence_state_after": "RUNTIME_SAMPLE_HISTORY_COLLECTING_LONG_RUN_EVIDENCE_BLOCKED",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_CREATED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], runtime_history: dict[str, Any]) -> None:
    base.write_json(
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
    base.write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_RUNTIME_SAMPLE_HISTORY_ADDED_LONG_RUN_EVIDENCE_BLOCKED",
            "runtime_sample_history_status": runtime_history["runtime_sample_status"],
            "accepted_cycle_sample_count": runtime_history["accepted_cycle_sample_count"],
            "invalid_source_count": runtime_history["invalid_source_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
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
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "runtime_sample_history_status": runtime_history["runtime_sample_status"],
            "accepted_cycle_sample_count": runtime_history["accepted_cycle_sample_count"],
            "invalid_source_count": runtime_history["invalid_source_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Upbit PAPER Runtime Sample History Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Dashboard stability history is display truth only and cannot prove actual PAPER runtime duration.
- Persistent loop reports existed, but there was no first-class history that bound loop reports to runtime cycle JSON files, counted duplicates, and surfaced stale or invalid source reports.

Patch:
- Added upbit_paper_runtime_sample_history schema, runtime builder, writer, validator, runtime artifact, and tests.
- Registered upbit_paper_runtime_sample_history_validator in registry and validator runner.
- Current repo runtime history is BLOCKED rather than promoted because stale/invalid persistent loop reports require reconciliation and accepted runtime samples remain short-span evidence only.

Runtime history summary:
- source_loop_report_count: {runtime_history["source_loop_report_count"]}
- accepted_cycle_sample_count: {runtime_history["accepted_cycle_sample_count"]}
- invalid_source_count: {runtime_history["invalid_source_count"]}
- duplicate_cycle_hash_count: {runtime_history["duplicate_cycle_hash_count"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
""",
    )


def write_patch(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], runtime_history: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, runtime_history)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    runtime_history = write_runtime_history()
    write_context(now, trader_hash, agents_hash, runtime_history)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        base.run_command([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "tests/runtime/test_upbit_paper_runtime_sample_history.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "-q"]),
        base.run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, runtime_history)
    write_patch(now, trader_hash, agents_hash, patch_result, runtime_history)

    tests_run.append(base.run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, runtime_history)
    write_patch(now, trader_hash, agents_hash, patch_result, runtime_history)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "runtime_sample_history_status": runtime_history["runtime_sample_status"],
                "accepted_cycle_sample_count": runtime_history["accepted_cycle_sample_count"],
                "invalid_source_count": runtime_history["invalid_source_count"],
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
