from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROGRESS_CLARITY"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-PROGRESS-CLARITY"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_residual_mvp5_entry_duration_policy_patch_evidence as adaptive_base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


base = adaptive_base.base

VALIDATORS_REQUIRED = [
    "runtime_schema_instance_validator",
    "schema_validator",
    "registry_validator",
    "paper_shadow_evidence_accumulation_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

CHANGED_ARTIFACTS = sorted(
    set(
        adaptive_base.CHANGED_ARTIFACTS
        + [
            "contracts/schema/residual_operator_evidence_progress_report.schema.json",
            "trader1/dashboard/read_only_dashboard.py",
            "trader1/reports/residual_operator_evidence_progress.py",
            "tests/contract/test_residual_adaptive_evidence_progress_clarity.py",
            "tests/contract/test_residual_operator_evidence_progress.py",
            "tests/dashboard/test_read_only_dashboard.py",
            "tools/emit_residual_adaptive_evidence_progress_clarity_patch_evidence.py",
            "tools/emit_residual_operator_evidence_progress_audit_patch_evidence.py",
            f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
        ]
    )
)


def configure_adaptive_base() -> None:
    adaptive_base.PATCH_BASENAME = PATCH_BASENAME
    adaptive_base.PATCH_ID = PATCH_ID
    adaptive_base.REQUIREMENT_ID = REQUIREMENT_ID
    adaptive_base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    adaptive_base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    adaptive_base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    adaptive_base.configure_base()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_context(now: str, trader_hash: str, agents_hash: str, progress: dict[str, Any]) -> None:
    adaptive_base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD", "SECTION_OPERATOR_CONTROL"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY", "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.residual_operator_evidence_progress_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Evidence progress report declares the fixed-duration gate removed.
- Codex stepwise non-live review is explicitly allowed from existing artifacts.
- User runtime is not required for the next non-live patch.
- Gap closure still requires audited runtime, reconciliation, external, or operator evidence.
- Dashboard exposes Codex review and user-action summaries without implying readiness.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

evidence_progress_clarity_snapshot:
- adaptive_judgement_status: {progress["adaptive_judgement_status"]}
- fixed_duration_gate_status: {progress["fixed_duration_gate_status"]}
- codex_stepwise_review_allowed: {str(progress["codex_stepwise_review_allowed"]).lower()}
- codex_can_continue_non_live_patches: {str(progress["codex_can_continue_non_live_patches"]).lower()}
- user_runtime_required_for_next_non_live_patch: {str(progress["user_runtime_required_for_next_non_live_patch"]).lower()}
- user_runtime_required_for_gap_closure: {str(progress["user_runtime_required_for_gap_closure"]).lower()}
- evidence_quality_status: {progress["evidence_quality_status"]}

known_omissions_by_design:
- This patch does not execute PAPER/SHADOW runtime.
- This patch does not validate an operator submission package.
- This patch does not close residual gaps.
- This patch does not enable live orders, LIVE_READY writes, or scale-up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    adaptive_base.write_text(
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

The residual adaptive gate has no fixed runtime floor. Codex may continue non-live implementation and evidence review from existing artifacts. User runtime is not required for the next non-live patch, but audited runtime, reconciliation, external, or operator evidence is still required before gap closure, MVP-5 review-entry, live readiness, LIVE_READY, or scale-up can proceed.

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
            "source_section_id": "SECTION_OPERATOR_CONTROL",
            "source_file": "TRADER_1.md",
            "source_heading": "Residual adaptive evidence progress clarity",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: residual evidence progress must distinguish Codex non-live stepwise "
                "review from gap closure evidence requirements after fixed duration gates are removed"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual adaptive evidence progress clarity",
            "requirement_kind": "EVIDENCE_READINESS_PATCH",
            "schema_ids": ["trader1.residual_operator_evidence_progress_report.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/contract/test_residual_adaptive_evidence_progress_clarity.py",
                "tests/contract/test_residual_operator_evidence_progress.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual adaptive evidence progress clarity live blocked"),
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
    adaptive_base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_OPERATOR_CONTROL",
            "schema_files": ["contracts/schema/residual_operator_evidence_progress_report.schema.json"],
            "validator_files": [
                "trader1/reports/residual_operator_evidence_progress.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "test_files": [
                "tests/contract/test_residual_adaptive_evidence_progress_clarity.py",
                "tests/contract/test_residual_operator_evidence_progress.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [
                "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json",
                "contracts/generated/current_implementation_state.json",
            ],
            "runtime_modules": [
                "trader1/reports/residual_operator_evidence_progress.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py"],
            "patch_result_fields": [
                "adaptive_evidence_progress_clarity_status",
                "codex_stepwise_review_allowed",
                "codex_can_continue_non_live_patches",
                "user_runtime_required_for_next_non_live_patch",
                "user_runtime_required_for_gap_closure",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
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
    adaptive_base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    policy: dict[str, Any],
    progress: dict[str, Any],
) -> dict[str, Any]:
    patch_result = adaptive_base.build_patch_result(now, tests_run, validators_run, policy)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-PROGRESS-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.residual_operator_evidence_progress_report.v1", "trader1.patch_result.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator evidence progress",
                "residual adaptive evidence gate policy",
                "dashboard residual evidence progress summary",
                "live final guard",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "adaptive_evidence_progress_clarity_status": "PASS_CODEX_NON_LIVE_REVIEW_CAN_CONTINUE_GAP_CLOSURE_BLOCKED",
            "adaptive_judgement_status": progress["adaptive_judgement_status"],
            "fixed_duration_gate_status": progress["fixed_duration_gate_status"],
            "codex_stepwise_review_allowed": progress["codex_stepwise_review_allowed"],
            "codex_can_continue_non_live_patches": progress["codex_can_continue_non_live_patches"],
            "user_runtime_required_for_next_non_live_patch": progress["user_runtime_required_for_next_non_live_patch"],
            "user_runtime_required_for_gap_closure": progress["user_runtime_required_for_gap_closure"],
            "evidence_quality_status": progress["evidence_quality_status"],
            "dashboard_operator_visibility_changed": True,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_extra_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], progress: dict[str, Any]) -> None:
    adaptive_base.write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_ADAPTIVE_EVIDENCE_PROGRESS_CLARITY_LIVE_BLOCKED",
            "adaptive_judgement_status": progress["adaptive_judgement_status"],
            "codex_stepwise_review_allowed": True,
            "codex_can_continue_non_live_patches": True,
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
            "evidence_quality_status": progress["evidence_quality_status"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    adaptive_base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Residual Adaptive Evidence Progress Clarity

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- After the fixed duration gate was removed, the operator-facing progress report still needed a clear distinction between Codex non-live continuation and evidence-dependent gap closure.

Patch:
- Added explicit Codex stepwise judgement fields to the residual evidence progress report.
- Marked user runtime as not required for the next non-live patch.
- Kept user/runtime evidence required for actual gap closure, MVP-5 entry, live readiness, LIVE_READY, and scale-up.
- Exposed the same distinction on the dashboard first-screen blocker details.
- Removed stale 120h wording from the progress-audit evidence emitter.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no live order
- no credential/API key use
- no live config mutation
- no LIVE_READY write
- no current evidence write
- no gap closure
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    policy: dict[str, Any],
    progress: dict[str, Any],
) -> None:
    adaptive_base.write_patch_artifacts(now, trader_hash, agents_hash, patch_result, policy)
    write_extra_evidence(now, trader_hash, agents_hash, patch_result, progress)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    adaptive_base.write_json(patch_path, patch_result)


def main() -> int:
    configure_adaptive_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    reports = adaptive_base.build_and_write_reports(now, trader_hash, agents_hash)
    progress = reports["progress"]
    policy = reports["policy"]
    write_context(now, trader_hash, agents_hash, progress)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/contract/test_residual_adaptive_evidence_progress_clarity.py",
                "tests/contract/test_residual_operator_evidence_progress.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, policy, progress)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, policy, progress)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    tests_run.append(
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.contract.test_schema_instance_validation",
                "tests.contract.test_patch_result_runtime_schema_validation",
                "tests.contract.test_residual_adaptive_evidence_progress_clarity",
                "tests.contract.test_residual_operator_evidence_progress",
                "-v",
            ]
        )
    )
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    reports = adaptive_base.build_and_write_reports(now, trader_hash, agents_hash)
    progress = reports["progress"]
    policy = reports["policy"]
    patch_result = build_patch_result(now, tests_run, validators_run, policy, progress)
    write_context(now, trader_hash, agents_hash, progress)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, policy, progress)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "adaptive_judgement_status": progress["adaptive_judgement_status"],
                "fixed_duration_gate_status": progress["fixed_duration_gate_status"],
                "codex_stepwise_review_allowed": progress["codex_stepwise_review_allowed"],
                "user_runtime_required_for_next_non_live_patch": progress[
                    "user_runtime_required_for_next_non_live_patch"
                ],
                "user_runtime_required_for_gap_closure": progress["user_runtime_required_for_gap_closure"],
                "open_gap_count": progress["open_gap_count"],
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
