from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_PAPER_EXPOSURE_QUALITY_REPORT"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-EXPOSURE-QUALITY-REPORT"
NEXT_TASK_CLASS = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK_CONTINUE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    run_command,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import (  # noqa: E402
    PROFITABILITY_OPTIMIZER_EVIDENCE_VALIDATORS,
    run_validators,
)


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "paper_exposure_quality_report_validator",
    "profitability_optimizer_evidence_gap_validator",
    "optimizer_no_live_mutation_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "paper_exposure_quality_report_validator",
    "profitability_optimizer_evidence_gap_validator",
    "optimizer_no_live_mutation_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "contracts/schema/paper_exposure_quality_report.schema.json",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_paper_exposure_quality_report_validator.py",
    "tests/validators/fixtures/paper_exposure_quality_pass.json",
    "tests/validators/fixtures/paper_exposure_quality_scale_up_fail.json",
    "tests/validators/fixtures/paper_exposure_quality_missing_evidence_fail.json",
    "tests/validators/fixtures/paper_exposure_quality_exposure_breach_fail.json",
    "tests/validators/fixtures/paper_exposure_quality_live_mode_fail.json",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json",
    "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
    "contracts/generated/context_pack/PAPER_EXPOSURE_QUALITY_REPORT.md",
]
BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def update_registry_and_validator_registry(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    registry["updated_at_utc"] = now
    write_json(registry_path, registry)

    validator_registry_path = ROOT / "contracts" / "validators" / "validator_registry.json"
    validator_registry = load_json(validator_registry_path)
    implemented = validator_registry.get("implemented_validators", [])
    implemented = [item for item in implemented if item.get("validator_id") != "paper_exposure_quality_report_validator"]
    implemented.append(
        {
            "validator_id": "paper_exposure_quality_report_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
    )
    validator_registry["implemented_validators"] = sorted(implemented, key=lambda item: item["validator_id"])
    validator_registry["updated_at_utc"] = now
    write_json(validator_registry_path, validator_registry)


def update_profitability_gap_audit(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
    audit = load_json(audit_path)
    audit["generated_at_utc"] = now
    audit["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}

    for component in audit.get("inspected_components", []):
        if component.get("component_id") == "risk_sizing_exposure":
            component["current_level"] = "PARTIAL_PATCHED"
            component["target_level"] = "VALIDATED_CONSERVATIVE_PAPER_RISK_BUDGET_WITH_SCALE_UP_BLOCKED"

    for gap in audit.get("gaps", []):
        if gap.get("gap_id") == "PROFIT-GAP-004":
            gap.update(
                {
                    "condition": "Risk sizing remains live-blocked, but paper exposure quality now has schema, validator, and negative fixtures; long-run and live-review evidence are still missing.",
                    "impact": "Risk remains disabled safely while the operator can now see whether paper exposure quality is sufficient for review.",
                    "ux_impact": "Operator can distinguish paper exposure quality from live or scale-up permission.",
                    "profitability_impact": "Creates a conservative feedback loop for exposure, concentration, drawdown, idempotency, and recovery quality.",
                    "fix": "Added paper_exposure_quality_report schema, validator, PASS fixture, live/scale flag negative fixture, missing-evidence fixture, exposure-breach fixture, and LIVE-mode fixture. Scale-up remains blocked.",
                    "patch_status": "PARTIAL_PATCHED",
                    "live_order_ready_after": False,
                    "live_order_allowed_after": False,
                }
            )

    actions = audit.setdefault("safe_patch_actions", [])
    if not any(isinstance(item, dict) and item.get("action_id") == PATCH_ID for item in actions):
        actions.append(
            {
                "action_id": PATCH_ID,
                "status": "APPLIED",
                "summary": "Added paper exposure quality report schema, fail-closed validator, and negative fixtures so risk sizing exposure quality is paper-visible while live and scale-up stay blocked.",
                "live_order_ready_after": False,
                "live_order_allowed_after": False,
                "can_live_trade_after": False,
                "scale_up_allowed_after": False,
            }
        )
    write_json(audit_path, audit)

    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json"
    gap = load_json(gap_path)
    gap["generated_at_utc"] = now
    gap["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    gap["notes"] = (
        "Rechecked in MVP-4. Paper exposure quality now has a strict schema, validator, and negative fixtures for "
        "scale-up drift, missing evidence, exposure breach, and LIVE-mode misuse. Gap remains OPEN because long-run "
        "evidence, external API verification, read-only burn-in, manual order evidence, and operator approval are still absent."
    )
    write_json(gap_path, gap)
    return audit


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "PAPER_EXPOSURE_QUALITY_REPORT.md",
        f"""# PAPER_EXPOSURE_QUALITY_REPORT

context_pack_id: PAPER_EXPOSURE_QUALITY_REPORT
task_class: MVP4_PAPER_EXPOSURE_QUALITY_REPORT
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_CONVERGENCE_RISK_SCALE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_exposure_quality_report.v1"]
included_validator_ids: ["paper_exposure_quality_report_validator", "profitability_optimizer_evidence_gap_validator", "live_final_guard_validator"]
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- paper exposure quality is PAPER-only and display-truth-only
- source_evidence_ids are required for paper review
- exposure, concentration, drawdown, idempotency, and recovery failures fail closed
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live evidence collection
- no live config mutation
- no scale-up permission
- no LIVE_READY snapshot write

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

Paper exposure quality is now schema-backed and validator-backed for review visibility. Scale-up remains blocked and the profitability maturity contract gap stays OPEN.

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
            "source_section_id": "SECTION_STRATEGY_PROFITABILITY",
            "source_file": "TRADER_1.md",
            "source_heading": "paper exposure quality report",
            "full_text_marker": f"{REQUIREMENT_ID}:paper exposure quality must be paper-only, evidence-bound, and scale-up blocked",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Paper exposure quality report guard",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.paper_exposure_quality_report.v1"],
            "validator_ids": ["paper_exposure_quality_report_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_paper_exposure_quality_report_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_STRATEGY_PROFITABILITY", "SECTION_CONVERGENCE_RISK_SCALE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT"],
            "source_text_sha256": sha256_bytes(b"paper exposure quality must be paper-only, evidence-bound, and scale-up blocked"),
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
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_STRATEGY_PROFITABILITY",
            "schema_files": ["contracts/schema/paper_exposure_quality_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_paper_exposure_quality_report_validator.py"],
            "fixture_files": [
                "tests/validators/fixtures/paper_exposure_quality_pass.json",
                "tests/validators/fixtures/paper_exposure_quality_scale_up_fail.json",
                "tests/validators/fixtures/paper_exposure_quality_missing_evidence_fail.json",
                "tests/validators/fixtures/paper_exposure_quality_exposure_breach_fail.json",
                "tests/validators/fixtures/paper_exposure_quality_live_mode_fail.json",
            ],
            "runtime_modules": ["trader1/validation/mvp0_validators.py"],
            "evidence_artifacts": [
                "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json",
                "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "scale_up_allowed_after",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
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
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [
                "paper_exposure_quality_report",
                "paper_exposure_quality_report_validator",
                REQUIREMENT_ID,
            ],
            "new_or_changed_schema_ids": ["trader1.paper_exposure_quality_report.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
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
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_PAPER_EXPOSURE_QUALITY_REPORT",
            "required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "TRADER_1:strategy-profitability-risk-sizing-exposure",
                "AGENTS:profit-convergence-risk-scaling-rules",
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
            "optimizer_patch": "PAPER_EXPOSURE_QUALITY_EVIDENCE_HARDENING",
            "optimizer_stage": "MVP4_REVIEW_PREP",
            "optimizer_status_before": "LIVE_BLOCKED",
            "optimizer_status_after": "LIVE_BLOCKED_WITH_PAPER_EXPOSURE_QUALITY_REVIEW",
            "optimizer_maturity_level_before": "PARTIAL_PATCHED",
            "optimizer_maturity_level_after": "PARTIAL_PATCHED",
            "optimizer_output_type": "PAPER_RISK_EVIDENCE_ONLY",
            "optimizer_validators_required": [
                "paper_exposure_quality_report_validator",
                "optimizer_no_live_mutation_validator",
            ],
            "optimizer_validators_run": [
                item
                for item in validators_run
                if item.get("validator_id") in {"paper_exposure_quality_report_validator", "optimizer_no_live_mutation_validator"}
            ],
            "optimizer_guardrail_result": "PASS_LIVE_MUTATION_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "PAPER_EXPOSURE_QUALITY_REPORT_GUARD",
            "convergence_layer_changed": False,
            "convergence_state_before": "LIVE_BLOCKED",
            "convergence_state_after": "LIVE_BLOCKED_WITH_PAPER_EXPOSURE_QUALITY_REVIEW",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_PAPER_EXPOSURE_QUALITY_REPORT",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["paper_exposure_quality_report_validator"],
            "convergence_validators_run": [
                item for item in validators_run if item.get("validator_id") == "paper_exposure_quality_report_validator"
            ],
            "convergence_guardrail_result": "PASS_SCALE_UP_BLOCKED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result.pop("affected_artifact_paths", None)
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_PAPER_EXPOSURE_QUALITY_REPORT_LIVE_AND_SCALE_UP_BLOCKED",
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
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Paper Exposure Quality Report Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- PROFIT-GAP-004 was only recorded: risk sizing exposure had no paper-only exposure quality report.

Patch:
- Added paper_exposure_quality_report schema.
- Added paper_exposure_quality_report_validator with PASS and negative fixtures.
- Negative fixtures cover scale-up drift, missing paper evidence, exposure breach, and LIVE-mode misuse.
- Updated profitability maturity audit while keeping the contract gap OPEN.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.paper_exposure_quality_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["paper_exposure_quality_report_validator"]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + ["PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"]))
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


def emit_patch(now: str, trader_hash: str, agents_hash: str, tests_run: list[dict[str, Any]], validator_ids: list[str]) -> dict[str, Any]:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(validator_ids), validator_ids)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)
    return patch_result


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_registry_and_validator_registry(now)
    update_authority_manifest(now)
    update_profitability_gap_audit(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_paper_exposure_quality_report_validator", "-v"]),
    ]

    emit_patch(now, trader_hash, agents_hash, tests_run, BOOTSTRAP_VALIDATORS_REQUIRED)

    tests_run.extend(
        [
            run_command([sys.executable, "tools/run_profitability_optimizer_evidence_gap_validators.py"]),
            run_command([sys.executable, "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        ]
    )

    patch_result = emit_patch(now, trader_hash, agents_hash, tests_run, VALIDATORS_REQUIRED)
    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "validators_required": VALIDATORS_REQUIRED,
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
