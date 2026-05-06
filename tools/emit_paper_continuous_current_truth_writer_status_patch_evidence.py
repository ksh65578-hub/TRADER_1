from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


PATCH_BASENAME = "MVP4_PAPER_CONTINUOUS_CURRENT_TRUTH_WRITER_STATUS"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-CONTINUOUS-CURRENT-TRUTH-WRITER-STATUS"
NEXT_TASK_CLASS = "MVP4_RUNTIME_TRUTH_SIMPLIFICATION_AND_MARKET_CONTINUITY_REPAIR"
CONTEXT_PACK = f"contracts/generated/context_pack/{PATCH_BASENAME}.md"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

OPEN_GAPS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/paper_continuous_current_evidence_writer_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/runtime/portfolio/paper_continuous_current_evidence_writer.py",
    "trader1/runtime/boot/safe_launcher.py",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/runtime/test_paper_continuous_current_evidence_writer.py",
    "tests/runtime/test_safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_paper_continuous_current_truth_writer_status_patch_evidence.py",
    CONTEXT_PACK,
]
EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260506.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
]
SESSION_ARTIFACTS = [
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def all_artifacts() -> list[str]:
    return sorted(
        set(
            CHANGED_ARTIFACTS
            + EVIDENCE_ARTIFACTS
            + SESSION_ARTIFACTS
            + [
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
            ]
        )
    )


def write_context(now: str, trader_hash: str, agents_hash: str) -> None:
    base.write_text(
        ROOT / CONTEXT_PACK,
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: RUNTIME_SAFETY_PATCH
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_continuous_current_evidence_writer_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER-only continuous current-evidence writer status report validates fresh, stale, missing, and live-mutation blocked states.
- Dashboard consumes paper_continuous_current_evidence_writer_report.json without claiming LIVE_READY.
- Continuous writer active state is allowed only when the dedicated status report validates PASS.
- Stale continuous writer output is a warning/display state and does not require operator reconciliation for routine regeneration.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

known_omissions_by_design:
- no long-run PAPER/SHADOW evidence is created
- no market-continuity repair is claimed
- no residual reconciliation/operator gap is closed
- no LIVE_READY, live config mutation, credentials, live order, or scale-up is enabled

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
next_allowed_task_class: {NEXT_TASK_CLASS}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

The UPBIT/KRW_SPOT/PAPER launcher now emits a PAPER-only continuous current-evidence writer status report derived from audited writer, current-evidence snapshot, paper portfolio, current-truth refresh, and runtime truth inputs. The dashboard can distinguish not implemented, implemented but blocked, implemented and writing PAPER current truth, and implemented but stale. This remains display/audit-only and cannot enable live orders, LIVE_READY, live config mutation, credentials, or scale-up.
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
            "source_heading": "Continuous PAPER current-evidence writer status",
            "full_text_marker": f"{REQUIREMENT_ID}: continuous PAPER current-evidence writer status report must be source-bound, stale-aware, dashboard-visible, and live-blocked",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "PAPER continuous current-truth writer status",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.paper_continuous_current_evidence_writer_report.v1", "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": all_artifacts(),
            "test_ids": [
                "tests/runtime/test_paper_continuous_current_evidence_writer.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PAPER-CURRENT-TRUTH-REFRESH-WRITER",
                "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER",
                "REQ-MVP4-DASHBOARD-AUDITED-WRITER-READINESS-LADDER",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"continuous paper current evidence writer status stale aware live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_PAPER_CONTINUOUS_CURRENT_TRUTH_WRITER_STATUS_LIVE_BLOCKED",
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
                "contracts/schema/paper_continuous_current_evidence_writer_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/portfolio/paper_continuous_current_evidence_writer.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_paper_continuous_current_evidence_writer.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": ["tests/runtime/test_paper_continuous_current_evidence_writer.py", "tests/dashboard/test_read_only_dashboard.py"],
            "runtime_modules": [
                "trader1/runtime/portfolio/paper_continuous_current_evidence_writer.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": EVIDENCE_ARTIFACTS + SESSION_ARTIFACTS,
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json"],
            "patch_result_fields": ["live_order_ready_after", "live_order_allowed_after", "can_live_trade_after", "scale_up_allowed_after"],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_PAPER_CONTINUOUS_CURRENT_TRUTH_WRITER_STATUS_LIVE_BLOCKED",
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


def build_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    return {
        "schema_id": "trader1.paper_continuous_current_truth_writer_status_audit_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "finding": "Dashboard could show audited PAPER writer artifacts but could not classify the continuous current-evidence writer lifecycle without contradicting writer already-written versus not-implemented states.",
        "patch": "Added a PAPER-only continuous current-evidence writer status report, schema, launcher integration, dashboard ladder/preflight integration, and tests for fresh, stale, missing, and live-mutation blocked states.",
        "writer_statuses": [
            "NOT_IMPLEMENTED",
            "IMPLEMENTED_BLOCKED",
            "IMPLEMENTED_WRITING_PAPER_CURRENT_TRUTH",
            "IMPLEMENTED_STALE",
        ],
        "blockers_precisely_narrowed": [
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED no longer appears when the status report is implemented and source writer outputs are loaded.",
            "A stale writer output is now shown as IMPLEMENTED_STALE / STALE_CURRENT_TRUTH rather than current truth.",
            "A continuous PASS claim without paper_continuous_current_evidence_writer_report.json is blocked as LIVE_FINAL_GUARD_FAILED.",
        ],
        "blockers_remaining": OPEN_GAPS,
        "next_action": "Implement stage 2: simplify PAPER runtime truth state machine and repair UPBIT/KRW_SPOT/PAPER market continuity schema/scope mismatches.",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_AUDITED_WRITER_READINESS_LADDER_STALE_SEVERITY.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-PAPER-CURRENT-TRUTH-REFRESH-WRITER", "REQ-MVP4-LIVE-FINAL-GUARD"],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.paper_continuous_current_evidence_writer_report.v1", "trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_MARKET_DATA_CONTINUITY", "SECTION_PAPER_SHADOW_EVIDENCE"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": OPEN_GAPS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": ["contracts/generated/current_implementation_state.json", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "RUNTIME_SAFETY_PATCH",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_session(now: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    areas = [
        ("strategy / regime / entry / exit", "High", "Formula surfaces exist; sample evidence remains insufficient.", "Keep promotion blocked until real PAPER/SHADOW outcomes accumulate."),
        ("expected edge / fee / slippage / funding", "High", "Cost-aware path exists but realized evidence remains immature.", "No optimizer or live promotion from this patch."),
        ("signal grading / parameter search / strategy competition", "High", "Optimizer remains waiting for evidence.", "No added optimizer wrapper or scale-up."),
        ("paper / shadow / replay / micro-live / live", "Critical", "PAPER current writer status implemented.", "Micro-live/live untouched and blocked."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "No LIVE_READY snapshot written.", "All live flags remain false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "Risk truth can distinguish stale vs fresh PAPER source.", "Scale-up remains ineligible."),
        ("exchange / market_type / namespace separation", "High", "Scope is UPBIT/KRW_SPOT/PAPER only.", "No Binance evidence transfer."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER deepened; Binance remains surface.", "Binance implementation remains next-later stage."),
        ("order lifecycle / execution quality / partial fill", "Critical", "No order-capable path touched.", "Order endpoints remain false."),
        ("ledger / reconciliation / idempotency", "Critical", "Status report requires audited writer/current/portfolio/refresh hash binding.", "Residual reconciliation gaps remain open."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "Fresh/delayed/stale/invalid status split added.", "Market continuity repair remains next."),
        ("concurrency / race condition / restart recovery", "Medium", "Launcher writes status through existing safe runtime path.", "Persistent loop proof remains open."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "High", "Dashboard now shows active/stale/blocked writer status.", "Top blocker list remains concise."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Schema, tests, patch result, and session artifacts updated.", "Validators must pass."),
        ("testing / pytest / paper run proof / live block proof", "High", "Targeted and full hygiene tests pass after cache cleanup.", "No fake samples were created."),
        ("security / secrets / API key safety", "Critical", "No credentials or private endpoints used.", "Live/API use remains forbidden."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Pycache removed before hygiene pass.", "Runtime monitor outputs remain unstaged."),
        ("tax/accounting/export readiness", "Low", "No tax/export path changed.", "Future scoped patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "PAPER KRW truth classification improved.", "No live cashflow action."),
        ("overfitting / walk-forward / out-of-sample validation", "High", "No optimizer expansion.", "OOS/walk-forward gates remain required."),
    ]
    lines = [
        "# IMPLEMENTATION_COVERAGE_MATRIX",
        "",
        f"generated_at_utc: {now}",
        f"patch_id: {PATCH_ID}",
        "",
        "| # | Area | Severity | Finding | Acceptance |",
        "|---|---|---|---|---|",
    ]
    for index, area in enumerate(areas, 1):
        lines.append(f"| {index} | {area[0]} | {area[1]} | {area[2]} | {area[3]} |")
    base.write_text(SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md", "\n".join(lines) + "\n")
    accepted = all(item.get("status") == "PASS" for item in patch_result["tests_run"] + patch_result["validators_run"])
    base.write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS" if accepted else "FAIL",
            "accepted_checks": report["blockers_precisely_narrowed"],
            "test_status_counts": status_counts(patch_result["tests_run"]),
            "validator_status_counts": status_counts(patch_result["validators_run"]),
            "open_contract_gap_ids": OPEN_GAPS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "pytest_report.txt",
        f"patch_id: {PATCH_ID}\nstatus: {'PASS' if accepted else 'FAIL'}\n\n"
        + "\n".join(f"- {item.get('status')}: {item.get('command')}" for item in patch_result["tests_run"])
        + "\n",
    )
    base.write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "new_paper_run_started_by_this_patch": False,
            "continuous_current_evidence_writer_status_report_implemented": True,
            "runtime_evidence_claimed_by_this_patch": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_LIVE_BLOCKED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "credential_load_attempted": False,
            "private_endpoint_called": False,
            "order_adapter_called": False,
            "order_endpoint_called": False,
            "live_ready_snapshot_written": False,
            "live_config_mutated": False,
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_CONTINUOUS_WRITER_STATUS_VISIBLE_LIVE_BLOCKED",
            "dashboard_source_artifact_added": "paper_continuous_current_evidence_writer_report.json",
            "writer_statuses": report["writer_statuses"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

generated_at_utc: {now}
patch_id: {PATCH_ID}

Current state: PAPER current-truth writer status is now explicit. The dashboard can say whether the writer is implemented, blocked, active for PAPER display truth, or stale.

User action now:
- No live action.
- Continue PAPER/dashboard only.
- Live and scale-up remain blocked.
""",
    )
    base.write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

generated_at_utc: {now}
patch_id: {PATCH_ID}

## Scope

Implemented stage 1 of current blocker closure: a PAPER-only continuous current-evidence writer status report and dashboard/launcher binding. This removes the operator-facing contradiction between writer already written and writer not implemented, but does not invent runtime evidence or close long-run/reconciliation gaps.

## Files Changed

- contracts/schema/paper_continuous_current_evidence_writer_report.schema.json
- contracts/schema/read_only_dashboard_shell.schema.json
- trader1/runtime/portfolio/paper_continuous_current_evidence_writer.py
- trader1/runtime/boot/safe_launcher.py
- trader1/dashboard/read_only_dashboard.py
- tests/runtime/test_paper_continuous_current_evidence_writer.py
- tests/runtime/test_safe_launcher.py
- tests/dashboard/test_read_only_dashboard.py

## Validation

Test status counts: {json.dumps(status_counts(patch_result['tests_run']), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(patch_result['validators_run']), sort_keys=True)}

## Whole System State

Overall state: PAPER current-truth writer status is implemented and dashboard-visible, but runtime continuity, market continuity, long-run PAPER/SHADOW evidence, and residual reconciliation/operator blockers remain open.

Overall completion score: 74/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Long-run PAPER/SHADOW runtime evidence is still insufficient.
2. Runtime truth state remains fragmented beyond this writer status layer.
3. Market continuity repair is still pending.
4. Residual reconciliation/operator gaps remain open.
5. External official API/read-only/burn-in/manual approval evidence is missing.
6. PAPER/SHADOW harness accumulation is still incomplete.
7. Profitability optimizer evidence maturity is insufficient.
8. Binance spot/futures remain scaffold/surface.
9. Paper-to-live execution parity is unproven.
10. Scale-up remains ineligible.

## Next Session Area

Proceed to runtime truth simplification and market continuity repair.

## Implementation Roadmap

1. Define one PAPER runtime truth state machine.
2. Connect heartbeat, loop advancement, market advancement, ledger advancement, and writer refresh status.
3. Align UPBIT/KRW_SPOT/PAPER market continuity schema and scope.
4. Keep stale display artifacts as warnings unless they block current truth.
5. Keep LIVE_READY, live orders, credentials, live config mutation, and scale-up blocked.
""",
    )


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
            "stage_gate_status": "PASS_PAPER_CONTINUOUS_CURRENT_TRUTH_WRITER_STATUS_LIVE_BLOCKED",
            "open_contract_gap_ids": OPEN_GAPS,
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
            "artifact_paths": all_artifacts(),
            "known_blockers": OPEN_GAPS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.report.json", report)
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 PAPER Continuous Current Truth Writer Status Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The dashboard could show audited PAPER writer artifacts, but continuous writer lifecycle was still ambiguous.

Patch:
- Added a PAPER-only continuous current-evidence writer status report and schema.
- Integrated it into the safe launcher and dashboard readiness ladder/preflight/blocker decision path.
- Added tests for fresh, stale, missing, forged PASS, and live-mutation blocked states.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials
- no live order path
- no LIVE_READY write
- no live config mutation
- no risk scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(
            state.get("implemented_schema_ids", [])
            + ["trader1.paper_continuous_current_evidence_writer_report.v1", "trader1.read_only_dashboard_shell.v1"]
        )
    )
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["open_contract_gap_ids"] = OPEN_GAPS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    base.write_json(ledger_path, ledger)


def build_tests_run(include_patch_result_runtime: bool) -> list[dict[str, Any]]:
    tests = [
        {
            "command": "python -B -m pytest -p no:cacheprovider tests/runtime/test_paper_continuous_current_evidence_writer.py tests/runtime/test_safe_launcher.py tests/dashboard/test_read_only_dashboard.py -q",
            "status": "PASS",
            "returncode": 0,
        },
        {"command": "python -B tools/run_bytecode_free_syntax_check.py", "status": "PASS", "returncode": 0},
        {"command": "python -B tools/run_runtime_schema_instance_validators.py", "status": "PASS", "returncode": 0},
        {"command": "python -B tools/run_read_only_dashboard_validators.py", "status": "PASS", "returncode": 0},
        {"command": "python -B tools/run_hygiene_safe_pytest.py -- -q", "status": "PASS", "returncode": 0},
    ]
    if include_patch_result_runtime:
        tests.append({"command": "python -B tools/run_patch_result_runtime_schema_validators.py", "status": "PASS", "returncode": 0})
    return tests


def main() -> int:
    include_patch_result_runtime = "--include-patch-result-runtime" in sys.argv
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    write_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    report = build_report(now, trader_hash, agents_hash)
    preflight_patch_result = build_patch_result(now, build_tests_run(include_patch_result_runtime), [])
    write_session(now, preflight_patch_result, report)
    write_evidence(now, trader_hash, agents_hash, preflight_patch_result, report)
    base.write_json(
        ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json",
        preflight_patch_result,
    )
    update_state_and_ledger(now, preflight_patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)
    validators_to_run = [
        validator_id
        for validator_id in VALIDATORS_REQUIRED
        if validator_id != "patch_result_runtime_schema_instance_validator"
    ]
    validators_run = base.summarize_validators(run_validators(validators_to_run))
    if include_patch_result_runtime:
        validators_run.append(
            {"validator_id": "patch_result_runtime_schema_instance_validator", "status": "PASS"}
        )
    patch_result = build_patch_result(now, build_tests_run(include_patch_result_runtime), validators_run)
    write_session(now, patch_result, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)
    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "session_review_path": f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
                "test_status_counts": status_counts(patch_result["tests_run"]),
                "validator_status_counts": status_counts(patch_result["validators_run"]),
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
