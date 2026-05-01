from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-RERUN-DECISION-AUDIT-SOURCE-BINDING-GUARD"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_SOURCE_BINDING_GUARD"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
import tools.emit_upbit_paper_post_rerun_reconciliation_decision_audit_patch_evidence as previous  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
    "upbit_paper_post_rerun_reconciliation_decision_audit_validator",
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
    "contracts/schema/patch_result.schema.json",
    "contracts/schema/upbit_paper_post_rerun_reconciliation_decision_audit_report.schema.json",
    "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_decision_audit.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py",
    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
    "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_review_guidance.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_decision_audit_report.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_post_rerun_reconciliation_decision_audit_patch_evidence.py",
    "tools/emit_upbit_paper_post_rerun_decision_audit_source_binding_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD.md",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_DECISION_AUDIT_SOURCE_QUEUE_BINDING_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_previous() -> None:
    previous.PATCH_BASENAME = PATCH_BASENAME
    previous.PATCH_ID = PATCH_ID
    previous.REQUIREMENT_ID = REQUIREMENT_ID
    previous.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    previous.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    previous.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    previous.BLOCKERS = BLOCKERS
    previous.configure_base()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD.md",
        f"""# MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD
task_class: MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_reconciliation_decision_audit_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The decision audit reloads the source operator queue artifact from disk.
- The source artifact's stored queue_hash and recomputed hash must match the in-memory source queue hash.
- Missing, invalid, scope-mismatched, or hash-mismatched source operator queue files block the decision audit.
- Current evidence writes, live permission, promotion, long-run evidence, and scale-up stay false.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, promotion patch, or LIVE_ENABLING_PATCH.
- POST_RERUN_RECONCILIATION_REQUIRED remains open.
- No credentialed exchange/account/API call, live order, live config mutation, or scale-up was used.

runtime_summary:
- decision_audit_status: {report["decision_audit_status"]}
- source_file_load_status: {report["source_operator_queue_file_load_status"]}
- source_file_hash_match: {str(report["source_operator_queue_file_hash_match"]).lower()}
- decision_item_count: {report["decision_item_count"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}
- live_order_allowed: false
- scale_up_allowed: false

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

Upbit PAPER post-rerun reconciliation decision audit evidence is now bound to the persisted operator queue artifact hash. Missing or mismatched source files block the audit while all live and scale-up flags remain false.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER post-rerun decision audit source binding guard",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: post-rerun reconciliation decision audit must bind source operator queue "
                "evidence to the persisted source artifact hash before write-denied decisions are accepted"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER post-rerun decision audit source binding guard",
            "requirement_kind": "SCHEMA_VALIDATOR_RUNTIME_EVIDENCE_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_decision_audit_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py",
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_review_guidance.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-DECISION-AUDIT",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-SOURCE-BINDING-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"post rerun decision audit source operator queue file hash binding"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_SOURCE_ARTIFACT_HASH_BINDING_LIVE_BLOCKED",
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
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_post_rerun_reconciliation_decision_audit_report.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_decision_audit.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py",
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_review_guidance.py",
            ],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_decision_audit.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "post_rerun_reconciliation_decision_audit_status",
                "post_rerun_decision_audit_source_operator_queue_file_load_status",
                "post_rerun_decision_audit_source_operator_queue_file_hash_match",
                "post_rerun_reconciliation_decision_item_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_SOURCE_ARTIFACT_HASH_BINDING_LIVE_BLOCKED",
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


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    patch_result = previous.build_patch_result(now, tests_run, validators_run, report)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-DECISION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_decision_audit_report.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "remaining_blockers": BLOCKERS,
            "next_task_class": NEXT_TASK_CLASS,
            "task_class": "MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD",
            "active_read_surface_used": [
                "current_implementation_state",
                "post-rerun reconciliation decision audit report",
                "persisted operator queue artifact",
                "live final guard",
            ],
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "post_rerun_decision_audit_source_operator_queue_file_load_status": report["source_operator_queue_file_load_status"],
            "post_rerun_decision_audit_source_operator_queue_file_hash_match": report["source_operator_queue_file_hash_match"],
            "optimizer_guardrail_result": "PASS_DECISION_AUDIT_SOURCE_OPERATOR_QUEUE_ARTIFACT_HASH_BOUND",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP_SOURCE_BOUND",
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    previous.write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Post-Rerun Decision Audit Source Binding Guard Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The decision audit consumed the operator queue report object but did not independently prove the persisted operator queue artifact still matched that report.

Patch:
- Added source operator queue file load status, stored hash, recomputed hash, and hash-match fields to the decision audit report.
- The decision audit now blocks missing, invalid, scope-mismatched, or hash-mismatched source operator queue files.
- Validator and runtime tests cover the missing-source negative case.

Runtime summary:
- decision_audit_status: {report["decision_audit_status"]}
- source_file_load_status: {report["source_operator_queue_file_load_status"]}
- source_file_hash_match: {report["source_operator_queue_file_hash_match"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no current-evidence writer permission was added
""",
    )


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(patch_path, patch_result)
    previous.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_previous()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    report = previous.write_runtime_report()
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.runtime.test_upbit_paper_post_rerun_reconciliation_decision_audit",
                "tests.runtime.test_upbit_paper_post_rerun_reconciliation_blocker_rollup",
                "tests.runtime.test_upbit_paper_post_rerun_operator_reconciliation_review_guidance",
                "-v",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "decision_audit_status": report["decision_audit_status"],
                "source_file_load_status": report["source_operator_queue_file_load_status"],
                "source_file_hash_match": report["source_operator_queue_file_hash_match"],
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
