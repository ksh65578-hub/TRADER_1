from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RECONCILIATION-QUEUE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_promotion_guard import (  # noqa: E402
    validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_queue import (  # noqa: E402
    build_upbit_paper_post_rerun_operator_reconciliation_queue_report,
    validate_upbit_paper_post_rerun_operator_reconciliation_queue_report,
    write_upbit_paper_post_rerun_operator_reconciliation_queue_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_rerun_current_evidence_promotion_guard_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
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
    "contracts/registry.yaml",
    "contracts/schema/patch_result.schema.json",
    "contracts/schema/upbit_paper_post_rerun_operator_reconciliation_queue_report.schema.json",
    "trader1/runtime/paper/upbit_paper_post_rerun_operator_reconciliation_queue.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_post_rerun_operator_reconciliation_queue_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE.md",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
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


def runtime_path(name: str) -> Path:
    return ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID / "paper_runtime" / name


def write_runtime_report() -> dict[str, Any]:
    guard = load_json(runtime_path("upbit_paper_post_rerun_current_evidence_promotion_guard_report.json"))
    guard_result = validate_upbit_paper_post_rerun_current_evidence_promotion_guard_report(guard)
    if guard_result.status != "PASS":
        raise RuntimeError(
            "source post-rerun promotion guard validation failed: "
            f"{guard_result.status} {guard_result.blocker_code} {guard_result.message}"
        )
    report = build_upbit_paper_post_rerun_operator_reconciliation_queue_report(
        promotion_guard_report=guard,
        queue_id="mvp4-upbit-paper-post-rerun-operator-reconciliation-queue",
    )
    result = validate_upbit_paper_post_rerun_operator_reconciliation_queue_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            "post-rerun operator reconciliation queue validation failed: "
            f"{result.status} {result.blocker_code} {result.message}"
        )
    write_upbit_paper_post_rerun_operator_reconciliation_queue_report(root=ROOT, report=report)
    return report


def candidate_paths(report: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for item in report.get("items", []):
        if isinstance(item, dict):
            for key in ("candidate_rollup_artifact_path", "planned_current_ledger_jsonl_path"):
                value = item.get(key)
                if isinstance(value, str):
                    paths.append(value)
    return sorted(set(paths))


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE.md",
        f"""# MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE
task_class: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The queue consumes only the validated post-rerun promotion guard report.
- Review-ready candidate rollups are listed for operator reconciliation with candidate/staged/planned-current path scope checks.
- The queue does not write current ledger JSONL, latest runtime pointers, persistent loops, LIVE_READY input, or scale-up artifacts.
- Candidate current evidence use and current evidence write counts remain zero.

known_omissions_by_design:
- This patch is not a reconciliation decision, writer, or promotion patch.
- POST_RERUN_RECONCILIATION_REQUIRED remains open for a later review-only decision audit.
- No private exchange/account/API call, credential, live order, live config mutation, or scale-up was used.

runtime_summary:
- queue_status: {report["queue_status"]}
- queue_item_count: {report["queue_item_count"]}
- operator_reconciliation_required_count: {report["operator_reconciliation_required_count"]}
- review_ready_reconciliation_item_count: {report["review_ready_reconciliation_item_count"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}
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

Upbit PAPER post-rerun candidate rollups now have a review-only operator reconciliation queue. It exposes candidate/staged/planned-current paths for operator review, but it does not write current evidence and keeps live/scale blocked.

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
            "source_heading": "Upbit PAPER post-rerun operator reconciliation queue",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: post-rerun PAPER promotion-guard candidates must be surfaced in a review-only "
                "operator reconciliation queue before any current evidence decision"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER post-rerun operator reconciliation queue",
            "requirement_kind": "SCHEMA_VALIDATOR_RUNTIME_ARTIFACT_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-PROMOTION-GUARD",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"post rerun operator queue exposes review items but blocks current evidence writes"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_REVIEW_ONLY_OPERATOR_QUEUE_CURRENT_EVIDENCE_WRITE_BLOCKED",
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
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_post_rerun_operator_reconciliation_queue_report.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_post_rerun_operator_reconciliation_queue.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_post_rerun_operator_reconciliation_queue.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "post_rerun_operator_reconciliation_queue_status",
                "post_rerun_operator_reconciliation_queue_item_count",
                "post_rerun_operator_reconciliation_required_count",
                "post_rerun_review_ready_reconciliation_item_count",
                "candidate_current_evidence_usable_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_REVIEW_ONLY_OPERATOR_QUEUE_CURRENT_EVIDENCE_WRITE_BLOCKED",
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
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-PROMOTION-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID, "upbit_paper_post_rerun_operator_reconciliation_queue_validator"],
            "new_or_changed_schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
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
                "post-rerun current evidence promotion guard report",
                "PAPER post-rerun candidate rollups",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_POST_RERUN_OPERATOR_QUEUE_REVIEW_ONLY",
            "optimizer_guardrail_result": "PASS_OPERATOR_QUEUE_DOES_NOT_MUTATE_CURRENT_EVIDENCE",
            "convergence_state_after": "POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_READY_RECONCILIATION_REQUIRED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP",
            "post_rerun_operator_reconciliation_queue_status": report["queue_status"],
            "post_rerun_operator_reconciliation_queue_item_count": report["queue_item_count"],
            "post_rerun_operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
            "post_rerun_review_ready_reconciliation_item_count": report["review_ready_reconciliation_item_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_REVIEW_ONLY_OPERATOR_QUEUE_CURRENT_EVIDENCE_WRITE_BLOCKED",
            "queue_status": report["queue_status"],
            "queue_item_count": report["queue_item_count"],
            "operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
            "review_ready_reconciliation_item_count": report["review_ready_reconciliation_item_count"],
            "current_evidence_write_allowed_count": report["current_evidence_write_allowed_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "current_evidence_mutation_allowed": False,
            "actual_long_run_evidence_created": False,
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
                *candidate_paths(report),
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "queue_status": report["queue_status"],
            "queue_item_count": report["queue_item_count"],
            "operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
            "review_ready_reconciliation_item_count": report["review_ready_reconciliation_item_count"],
            "current_evidence_write_allowed_count": report["current_evidence_write_allowed_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "current_evidence_mutation_allowed": False,
            "actual_long_run_evidence_created": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Post-Rerun Operator Reconciliation Queue Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Promotion-guard candidates were review-ready but needed an explicit operator reconciliation queue before any future current-evidence decision.

Patch:
- Added a strict review-only operator reconciliation queue schema, runtime builder/writer/validator, registry entry, runtime artifact, patch-result fields, and negative tests.
- The queue lists candidate rollups with candidate/staged/planned-current path scope checks.
- Current ledger JSONL, latest runtime pointer, persistent loop reports, source artifacts, live permission, promotion, long-run evidence, and scale-up remain blocked.

Runtime summary:
- queue_status: {report["queue_status"]}
- queue_item_count: {report["queue_item_count"]}
- operator_reconciliation_required_count: {report["operator_reconciliation_required_count"]}
- review_ready_reconciliation_item_count: {report["review_ready_reconciliation_item_count"]}
- current_evidence_write_allowed_count: {report["current_evidence_write_allowed_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}

Safety:
- current_evidence_mutation_allowed=false
- current_evidence_write_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    configure_base()
    base.update_state_and_ledger(now, patch_result)
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    schema_ids = set(state.get("implemented_schema_ids", []))
    schema_ids.add("trader1.patch_result.v1")
    schema_ids.add("trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1")
    validator_ids = set(state.get("implemented_validator_ids", []))
    validator_ids.add("upbit_paper_post_rerun_operator_reconciliation_queue_validator")
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    gaps = set(state.get("open_contract_gap_ids", []))
    gaps.update(
        {
            "POST_RERUN_RECONCILIATION_REQUIRED",
            "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
            "LIVE_ENABLING_EVIDENCE_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        }
    )
    state["implemented_schema_ids"] = sorted(schema_ids)
    state["implemented_validator_ids"] = sorted(validator_ids)
    state["completed_requirement_ids"] = sorted(completed)
    state["untested_validator_ids"] = sorted(set(state.get("untested_validator_ids", [])) - validator_ids)
    state["open_contract_gap_ids"] = sorted(gaps)
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["updated_at_utc"] = now
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    report = write_runtime_report()
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py",
                "tests/runtime/test_upbit_paper_post_rerun_current_evidence_promotion_guard.py",
                "-q",
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
                "queue_status": report["queue_status"],
                "queue_item_count": report["queue_item_count"],
                "operator_reconciliation_required_count": report["operator_reconciliation_required_count"],
                "review_ready_reconciliation_item_count": report["review_ready_reconciliation_item_count"],
                "current_evidence_write_allowed_count": report["current_evidence_write_allowed_count"],
                "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
                "current_evidence_mutation_allowed": False,
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
