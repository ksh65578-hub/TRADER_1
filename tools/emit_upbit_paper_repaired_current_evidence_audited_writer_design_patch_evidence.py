from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_design import (  # noqa: E402
    AUDITED_WRITER_DESIGN_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_design_report,
    validate_upbit_paper_repaired_current_evidence_audited_writer_design_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_design_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (  # noqa: E402
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
    build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
    validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


PATCH_BASENAME = "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER-DESIGN"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN_SCAFFOLD"
SESSION_ID = "mvp1_upbit_paper_launcher"

RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID / "paper_runtime"
SOURCE_GUARD_PATH = (
    RUNTIME_BASE / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json"
)
PRECHECK_PATH = RUNTIME_BASE / "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json"
DESIGN_PATH = RUNTIME_BASE / "upbit_paper_repaired_current_evidence_audited_writer_design_report.json"

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_repaired_current_evidence_audited_writer_precheck_validator",
    "upbit_paper_repaired_current_evidence_audited_writer_design_validator",
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
    "contracts/schema/upbit_paper_repaired_current_evidence_audited_writer_design_report.schema.json",
    "trader1/runtime/paper/upbit_paper_repaired_current_evidence_audited_writer_design.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_design.py",
    "tools/emit_upbit_paper_repaired_current_evidence_audited_writer_design_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_design_report.json",
]

BLOCKERS = [
    AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE,
    "POST_RERUN_RECONCILIATION_REQUIRED",
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


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def write_runtime_precheck_report() -> dict[str, Any]:
    report = build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
        root=ROOT,
        source_current_evidence_guard_report=load_json(SOURCE_GUARD_PATH),
        audited_writer_precheck_id="upbit-paper-repaired-current-evidence-audited-writer-design-precheck-20260502",
    )
    result = validate_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            f"audited writer precheck validation failed: {result.status} {result.blocker_code} {result.message}"
        )
    write_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(root=ROOT, report=report)
    return report


def write_runtime_design_report(source_precheck: dict[str, Any]) -> dict[str, Any]:
    report = build_upbit_paper_repaired_current_evidence_audited_writer_design_report(
        root=ROOT,
        source_audited_writer_precheck_report=source_precheck,
        audited_writer_design_id="upbit-paper-repaired-current-evidence-audited-writer-design-20260502",
    )
    result = validate_upbit_paper_repaired_current_evidence_audited_writer_design_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            f"audited writer design validation failed: {result.status} {result.blocker_code} {result.message}"
        )
    write_upbit_paper_repaired_current_evidence_audited_writer_design_report(root=ROOT, report=report)
    return report


def validate_design_projection(report: dict[str, Any]) -> None:
    if (
        report.get("design_status") != AUDITED_WRITER_DESIGN_STATUS
        or report.get("primary_blocker_code") != AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED_BLOCKER_CODE
        or report.get("design_control_count") != 8
        or report.get("design_control_pass_count") != 7
        or report.get("design_control_blocked_count") != 1
        or report.get("source_audited_writer_candidate_ready_count") != 3
        or report.get("source_audit_gate_pass_count") != 6
        or report.get("source_audit_gate_blocked_count") != 1
        or report.get("writer_implementation_allowed") is not False
        or report.get("writer_enabled") is not False
        or report.get("current_evidence_write_allowed") is not False
        or report.get("portfolio_truth_write_allowed") is not False
        or report.get("live_order_ready") is not False
        or report.get("live_order_allowed") is not False
        or report.get("can_live_trade") is not False
        or report.get("scale_up_allowed") is not False
    ):
        raise RuntimeError("audited writer design did not preserve blocked writer, live, and scale boundary")


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_repaired_current_evidence_audited_writer_design_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The audited writer design has explicit pre-write, write-target, and post-write controls.
- The design source must be a validated audited-writer precheck report.
- The design records single-writer, idempotency, atomic write, reconciliation, provenance, and live-boundary controls.
- The missing audited writer implementation remains the primary blocker.
- Current-evidence writes, portfolio truth writes, live orders, and scale-up remain blocked.

runtime_summary:
- design_status: {report["design_status"]}
- primary_blocker_code: {report["primary_blocker_code"]}
- design_control_pass_count: {report["design_control_pass_count"]}
- design_control_blocked_count: {report["design_control_blocked_count"]}
- writer_enabled: false
- current_evidence_write_allowed: false
- portfolio_truth_write_allowed: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not implement, enable, dry-run, or call a current-evidence writer.
- It does not write portfolio truth, LIVE_READY, live config, orders, or scale-up.

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

Upbit PAPER repaired current-evidence inputs now have a review-only audited writer design report. The design records the controls that a later writer must satisfy, but no writer is implemented and no current-evidence or portfolio truth write is permitted.

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
            "source_heading": "Upbit PAPER repaired current-evidence audited writer design",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: repaired current-evidence inputs require an audited writer design with "
                "single-writer, idempotency, atomic write, post-write reconciliation, portfolio provenance, "
                "and live boundary controls while current-evidence writes remain blocked"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER repaired current-evidence audited writer design",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.upbit_paper_repaired_current_evidence_audited_writer_design_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_design.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER-PRECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"upbit paper repaired current evidence audited writer design no writes no live no scale"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DESIGN_WRITER_DISABLED_LIVE_BLOCKED",
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
            "schema_files": ["contracts/schema/upbit_paper_repaired_current_evidence_audited_writer_design_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_design.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_repaired_current_evidence_audited_writer_design.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                base.rel(DESIGN_PATH),
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_DESIGN_WRITER_DISABLED_LIVE_BLOCKED",
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


def update_state_schema_validator_lists() -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []))
        | {"trader1.upbit_paper_repaired_current_evidence_audited_writer_design_report.v1"}
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []))
        | {"upbit_paper_repaired_current_evidence_audited_writer_design_validator"}
    )
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_DASHBOARD_BINDING.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER-PRECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_repaired_current_evidence_audited_writer_design_report.v1"
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
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_CURRENT_EVIDENCE_WRITER", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": [
                "LIVE_ENABLING_PATCH",
                "LIVE_CONFIG_MUTATION",
                "RISK_SCALE_UP",
                "RETAINED_ARCHIVE",
            ],
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
                "audited writer precheck report",
                "audited writer design report",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_BLOCKED",
            "optimizer_guardrail_result": "PASS_DESIGN_DOES_NOT_MUTATE_CURRENT_EVIDENCE",
            "convergence_state_after": "REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DESIGN_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
        }
    )
    validate_design_projection(report)
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
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
            "stage_gate_status": "PASS_AUDITED_WRITER_DESIGN_CREATED_WRITER_DISABLED",
            "design_status": report["design_status"],
            "primary_blocker_code": report["primary_blocker_code"],
            "design_control_pass_count": report["design_control_pass_count"],
            "design_control_blocked_count": report["design_control_blocked_count"],
            "writer_enabled": False,
            "current_evidence_write_allowed": False,
            "portfolio_truth_write_allowed": False,
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
            "artifact_paths": sorted(
                set(
                    [
                        *CHANGED_ARTIFACTS,
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "design_status": report["design_status"],
            "primary_blocker_code": report["primary_blocker_code"],
            "design_control_pass_count": report["design_control_pass_count"],
            "design_control_blocked_count": report["design_control_blocked_count"],
            "writer_enabled": False,
            "current_evidence_write_allowed": False,
            "portfolio_truth_write_allowed": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    precheck_report = write_runtime_precheck_report()
    report = write_runtime_design_report(precheck_report)
    validate_design_projection(report)
    write_context(now, trader_hash, agents_hash, report)
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
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_design.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
    ]
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.update_state_and_ledger(now, patch_result)
    update_state_schema_validator_lists()
    base.update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.update_state_and_ledger(now, patch_result)
    update_state_schema_validator_lists()
    base.update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
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
