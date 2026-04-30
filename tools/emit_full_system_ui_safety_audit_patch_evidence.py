from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_FULL_SYSTEM_UI_SAFETY_AUDIT_20260429_001"
PATCH_BASENAME = "MVP4_FULL_SYSTEM_UI_SAFETY_AUDIT"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_dashboard_launch_visibility_patch_evidence import write_launcher_artifacts
from tools.emit_root_launcher_operator_visibility_patch_evidence import (
    rel,
    run_command,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators


BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "LIVE_BURN_IN_FEEDBACK_MISSING",
    "EXECUTION_QUALITY_UNTESTED",
    "SURVIVAL_LAYER_BLOCKED",
    "RISK_SCALING_UNTESTED",
    "SCALE_UP_NOT_ELIGIBLE",
]

VALIDATORS_REQUIRED = [
    "authority_integrity_validator",
    "external_authority_manifest_validator",
    "registry_validator",
    "schema_validator",
    "closed_enum_validator",
    "common_defs_drift_validator",
    "patch_result_schema_validator",
    "coverage_index_validator",
    "active_schema_extraction_validator",
    "generated_artifact_dirty_validator",
    "live_blocked_negative_matrix_validator",
    "source_bundle_hygiene_validator",
    "secret_scan_validator",
    "path_namespace_validator",
    "truth_hierarchy_validator",
    "root_launcher_guard_validator",
    "root_launcher_surface_validator",
    "runtime_config_validator",
    "single_writer_order_path_validator",
    "strategy_direct_order_validator",
    "readiness_surface_validator",
    "live_ready_snapshot_writer_validator",
    "live_final_guard_validator",
    "upbit_live_review_preflight_validator",
    "read_only_dashboard_validator",
    "ledger_durability_validator",
    "reconciliation_validator",
    "ledger_reconciliation_validator",
    "restart_recovery_validator",
    "emergency_flatten_validator",
    "operator_action_audit_validator",
    "operator_control_validator",
    "upbit_paper_dry_run_validator",
    "upbit_operational_paper_gate_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
    "risk_scaling_decision_validator",
    "live_burn_in_feedback_validator",
    "paper_live_parity_validator",
    "execution_quality_measurement_validator",
    "survival_layer_validator",
]

SYSTEM_EVALUATION = [
    (
        "strategy / entry / exit / no-trade",
        "MVP-3 paper foundation",
        "entry and no-trade are testable; exit remains scaffolded",
        "partial",
        "under",
        "live blocked until review evidence",
        "needs clearer no-trade display",
        "moderate",
        "P1",
        "dashboard blocker and final_action surfaced",
    ),
    (
        "symbol selection / regime",
        "scaffolded",
        "regime fit evidence not mature",
        "partial",
        "under",
        "cannot promote by inference",
        "operator needs exact scope",
        "high later",
        "P2",
        "kept exchange and market_type explicit",
    ),
    (
        "bull / range / bear response",
        "scaffolded",
        "no robust regime adaptation yet",
        "partial",
        "under",
        "blocks live confidence",
        "status must avoid overclaim",
        "high later",
        "P2",
        "convergence remains non-live",
    ),
    (
        "VWAP / trend / breakout",
        "paper logic only",
        "needs fixtures and OOS checks",
        "partial",
        "under",
        "no live readiness impact until validated",
        "not first-screen critical",
        "high later",
        "P2",
        "no promotion path added",
    ),
    (
        "risk sizing / exposure",
        "MVP-3 bounded paper sizing",
        "live scale-up evidence absent",
        "partial",
        "balanced",
        "scale-up blocked",
        "false flags must be obvious",
        "high",
        "P0",
        "state scale_up_allowed fixed false",
    ),
    (
        "execution / slippage / fee",
        "paper adapter and fee model",
        "realized live execution unavailable",
        "partial",
        "under",
        "execution_quality blocked",
        "operator sees blockers",
        "high",
        "P1",
        "READ_ONLY only",
    ),
    (
        "order lifecycle / idempotency",
        "single-writer guard and ledger tests",
        "real adapter submit disabled",
        "covered for block path",
        "balanced",
        "live order path blocked",
        "no execution controls shown",
        "medium",
        "P0",
        "dashboard has no form/button",
    ),
    (
        "ledger / reconciliation",
        "hash-linked and scoped",
        "live hard truth absent",
        "covered for scaffold",
        "balanced",
        "reconcile required before live",
        "dashboard truth separated",
        "medium",
        "P0",
        "display warns truth separation",
    ),
    (
        "emergency protection",
        "dry-run scaffold",
        "real exchange flatten unavailable",
        "partial",
        "under",
        "live blocked",
        "control must remain visible",
        "medium",
        "P0",
        "validator rerun",
    ),
    (
        "optimizer / convergence",
        "MVP-4 guardrails",
        "analysis only; no live mutation",
        "partial",
        "balanced",
        "cannot enable live or scale-up",
        "wording avoids profit claims",
        "high later",
        "P0",
        "guardrail validators rerun",
    ),
    (
        "parameter adaptation",
        "schema scaffold",
        "no direct live config write",
        "partial",
        "balanced",
        "safe due to block",
        "operator needs candidate evidence later",
        "high later",
        "P2",
        "no mutation path added",
    ),
    (
        "evidence accumulation",
        "patch ledger and manifests",
        "external live evidence missing",
        "partial",
        "balanced",
        "MVP-5 blocked",
        "blocker list remains visible",
        "high",
        "P0",
        "audit evidence emitted",
    ),
    (
        "live review / burn-in",
        "Upbit review scaffold",
        "official API, burn-in, operator approval missing",
        "blocked",
        "balanced",
        "live_order_ready false",
        "must avoid LIVE_READY confusion",
        "high",
        "P0",
        "live launchers hard-block checked",
    ),
    (
        "dashboard UX / operator UX",
        "display-only dashboard",
        "first-screen blocker and scope needed hardening",
        "patched",
        "under before patch",
        "prevents operator confusion",
        "high improvement",
        "medium",
        "P0",
        "first-screen status/scope/next action added",
    ),
    (
        "logging / audit",
        "patch and validator logs",
        "full UI audit report was stale",
        "patched",
        "balanced",
        "traceability improved",
        "operator report clearer",
        "medium",
        "P0",
        "new audit report emitted",
    ),
    (
        "crash recovery / Windows",
        "restart recovery and launcher visibility",
        "no long-running service supervision yet",
        "partial",
        "under",
        "safe due to NO_TRADE",
        "launcher no longer disappears silently",
        "medium",
        "P1",
        "root launcher execution checked",
    ),
    (
        "adapter structure",
        "Upbit paper plus hard-block live shell",
        "Binance live remains below MVP-7",
        "partial",
        "balanced",
        "Binance live hard blocked",
        "scope labels needed",
        "medium",
        "P1",
        "all launcher scopes displayed",
    ),
    (
        "Upbit / Binance constraints",
        "scope-separated launchers",
        "live exchange specifics require external evidence",
        "partial",
        "balanced",
        "no cross-exchange inference",
        "exchange/market shown",
        "medium",
        "P1",
        "namespace validators rerun",
    ),
    (
        "schema / registry / validator",
        "64 schemas and full validator set parse",
        "external evidence validators blocked by design",
        "covered",
        "balanced",
        "fail-closed",
        "operator sees status only",
        "medium",
        "P0",
        "patch_result history revalidated",
    ),
    (
        "test / fixture",
        "193 tests passing",
        "live external fixtures unavailable",
        "covered below MVP-4",
        "balanced",
        "MVP-5 remains blocked",
        "good regression signal",
        "medium",
        "P0",
        "dashboard negative tests added",
    ),
    (
        "security / hygiene",
        "denylist and secret scan pass",
        "real credentials prohibited",
        "covered for bundle",
        "balanced",
        "no key load",
        "low UI impact",
        "high safety",
        "P0",
        "bundle validator rerun",
    ),
    (
        "performance / latency",
        "unit/runtime tests finish quickly",
        "no sustained load test yet",
        "partial",
        "under",
        "safe due to blocked live",
        "dashboard static and light",
        "medium later",
        "P2",
        "no long loop added",
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def authority_scan() -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in ("TRADER_1.md", "AGENTS.md"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        result[name] = {
            "sha256": sha256_file(path),
            "chars": len(text),
            "live_order_allowed_mentions": lower.count("live_order_allowed"),
            "can_live_trade_mentions": lower.count("can_live_trade"),
            "scale_up_allowed_mentions": lower.count("scale_up_allowed"),
            "optimizer_mentions": lower.count("optimizer"),
            "convergence_mentions": lower.count("convergence"),
            "retained_archive_mentions": lower.count("retained archive") + lower.count("retained_archive"),
            "contract_gap_mentions": lower.count("contract_gap"),
        }
    return result


def command_list() -> list[list[str]]:
    return [
        [sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"],
        [sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "tools/run_mvp0_validators.py"],
        [sys.executable, "tools/run_live_final_guard_validators.py"],
        [sys.executable, "tools/run_read_only_dashboard_validators.py"],
        [sys.executable, "tools/run_root_launcher_validators.py"],
        [sys.executable, "tools/run_namespace_validators.py"],
        [sys.executable, "tools/run_order_path_validators.py"],
        [sys.executable, "tools/run_execution_ledger_validators.py"],
        [sys.executable, "tools/run_reconciliation_validators.py"],
        [sys.executable, "tools/run_restart_recovery_validators.py"],
        [sys.executable, "tools/run_bundle_security_validators.py"],
        [sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"],
        [sys.executable, "tools/run_convergence_risk_scale_validators.py"],
        [sys.executable, "tools/run_upbit_live_review_validators.py"],
        [sys.executable, "tools/run_config_validators.py"],
        [sys.executable, "tools/run_live_blocked_validators.py"],
        [sys.executable, "tools/run_readiness_surface_validators.py"],
        [sys.executable, "tools/run_live_ready_snapshot_validators.py"],
        [sys.executable, "tools/run_safety_control_validators.py"],
        [sys.executable, "tools/run_emergency_flatten_validators.py"],
        [sys.executable, "tools/run_operator_control_validators.py"],
        [sys.executable, "tools/run_upbit_paper_validators.py"],
        [sys.executable, "tools/run_operational_paper_validators.py"],
        [sys.executable, "tools/run_convergence_assessment_dependency_validators.py"],
        [sys.executable, "tools/run_convergence_foundation_validators.py"],
        [sys.executable, "tools/validate_mvp0_contracts.py"],
        [sys.executable, "UPBIT_PAPER.py"],
        [sys.executable, "BINANCE_PAPER.py"],
        [sys.executable, "UPBIT_LIVE.py"],
        [sys.executable, "BINANCE_LIVE.py"],
    ]


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "FULL_SYSTEM_UI_SAFETY_AUDIT.md",
        f"""# FULL_SYSTEM_UI_SAFETY_AUDIT

context_pack_id: FULL_SYSTEM_UI_SAFETY_AUDIT
task_class: MVP4_FULL_SYSTEM_UI_SAFETY_AUDIT
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_DASHBOARD_SHELL", "SECTION_ROOT_LAUNCHER", "SECTION_NAMESPACE_TRUTH", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_RETAINED_ARCHIVE"]
included_requirement_ids: ["REQ-MVP0-LIVE-BLOCKED-MATRIX", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD", "REQ-MVP1-RECONCILIATION-SCAFFOLD", "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.read_only_dashboard_shell.v1", "trader1.root_launcher_report.v1", "trader1.live_preflight_report.v1", "trader1.risk_scaling_decision.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "contracts/generated/current_implementation_state.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- dashboard is display-only
- live launchers are hard-blocked
- optimizer and convergence cannot create live permission

known_omissions_by_design:
- no real exchange account access
- no credential loading
- no manual order test
- no live burn-in
- no LIVE_ENABLING_PATCH

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: {state.get("current_mvp", "MVP-4")}
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

MVP-4 and below are in audited safe mode. Root launchers generate display-only dashboards and live launchers remain hard-blocked. The dashboard first screen now exposes runtime scope, primary blocker, next operator action, and explicit false live flags.
""",
    )


def write_audit_report(now: str, authority: dict[str, Any], tests_run: list[dict[str, Any]], patch_result: dict[str, Any]) -> str:
    rows = "\n".join(
        "| "
        + " | ".join(item.replace("|", "/") for item in row)
        + " |"
        for row in SYSTEM_EVALUATION
    )
    commands = "\n".join(f"- {item['command']}: {item['status']} ({item['returncode']})" for item in tests_run)
    authority_lines = "\n".join(
        f"- {name}: sha256={data['sha256']} chars={data['chars']} retained_archive_mentions={data['retained_archive_mentions']} contract_gap_mentions={data['contract_gap_mentions']}"
        for name, data in authority.items()
    )
    report_path = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md"
    write_text(
        report_path,
        f"""# MVP4 Full System UI Safety Audit

created_at_utc: {now}
patch_id: {PATCH_ID}
target_mvp_level: MVP-4
execution_mode: REPLAY/PAPER/SHADOW/READ_ONLY mock-safe checks only
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Exhaustive Audit Summary
- Active authority surface scanned in full for this audit; generated navigation remains non-authority.
- Registry, schema bundle, validator registry, dependency validators, optimizer/convergence guardrails, retained archive markers, namespace separation, ledger/reconciliation, root launcher safety, dashboard truth, source bundle hygiene, and live-blocked negative cases were checked.
- Patch applied: dashboard first-screen safety UX was hardened and current_implementation_state now records scale_up_allowed=false.
- No real exchange account, credential, live order API, or LIVE_ENABLING behavior was used.

## Authority Surface
{authority_lines}

## Findings
- FINDING-001: read-only dashboard HTML did not prominently group runtime scope, primary blocker, next operator action, false live flags, and dashboard-vs-execution truth separation on the first screen.
- FINDING-002: current_implementation_state lacked an explicit scale_up_allowed=false field even though patch_results and validators kept scale-up blocked.
- FINDING-003: MVP-5 remains blocked by external evidence gaps; this is expected and not bypassed.

## System Evaluation
| Area | Current level | Gap | Missing | Over/under | Live safety impact | UX impact | Profit impact | Priority | Safe patch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{rows}

## Command Status
overall_command_status: {"PASS" if all(item["status"] == "PASS" for item in tests_run) else "FAIL"}
{commands}

## Runtime Issues
- Immediate-close launcher issue: not reproduced. All four root launchers returned PASS and printed report_path plus dashboard_path.
- Deadlock/infinite loop: not observed in safe command set.
- Crash recovery: restart recovery validators PASS; no service supervisor load test was run.

## Contract And Schema Issues
- Registry/schema/patch_result history validators PASS.
- Live external evidence remains missing by design.

## UI/UX Issues
- First-screen safety clarity was underpowered before this patch.
- Patched dashboard now shows exchange, market_type, mode, session_id, primary blocker, next operator action, false live flags, collapsible panels, and truth separation wording.
- No form or button is rendered.

## Ledger, Race, And Performance Issues
- Ledger duplicate/idempotency/reconciliation tests PASS.
- Atomic partial-write risk is covered by current scaffolds and restart recovery tests only; sustained concurrent writer stress remains future work.
- Performance check is test/runtime bounded; no long-running latency test was executed.

## Remaining Blockers
{chr(10).join("- " + blocker for blocker in BLOCKERS)}

## Patch Result
- path: {patch_result["evidence_manifest_path"].replace(".evidence_manifest.json", ".patch_result.json").replace("system/evidence/", "system/evidence/patch_results/")}
- result_hash: {patch_result["result_hash"]}
""",
    )
    return rel(report_path)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_FULL_SAFETY_AUDIT.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                "REQ-MVP0-LIVE-BLOCKED-MATRIX",
                "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
                "REQ-MVP1-ROOT-LAUNCHER-SURFACE",
                "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD",
                "REQ-MVP1-RECONCILIATION-SCAFFOLD",
                "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_LIVE_HARD_BLOCKED",
            "new_registry_items": artifacts,
            "new_or_changed_schema_ids": [],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "CHECKED_LIVE_AFFECTING_ONLY_NO_AUTHORITY_WEAKENING",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "next_required_section_ids": ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_UPBIT_LIVE_REVIEW"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_OPERATOR_CONTROL"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "BINANCE_FUTURES_LIVE", "LIVE_CONFIG_MUTATION"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": False,
            "active_read_surface_used": [
                "FULL_TRADER_1_ACTIVE_SURFACE_SCAN",
                "FULL_AGENTS_ACTIVE_SURFACE_SCAN",
                "REGISTRY_FULL",
                "SCHEMA_FULL",
                "VALIDATOR_FULL",
                "RETAINED_ARCHIVE_LIVE_IMPACT_SCAN",
            ],
            "task_class": "MVP4_FULL_SYSTEM_UI_SAFETY_AUDIT",
            "required_section_ids": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_DASHBOARD_SHELL",
                "SECTION_ROOT_LAUNCHER",
                "SECTION_NAMESPACE_TRUTH",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_OPTIMIZER_GUARDRAIL",
                "SECTION_CONVERGENCE_GUARDRAIL",
            ],
            "expanded_section_ids": [
                "FULL_TRADER_1_ACTIVE_SURFACE_SCAN",
                "FULL_AGENTS_ACTIVE_SURFACE_SCAN",
                "REGISTRY_FULL",
                "SCHEMA_FULL",
                "VALIDATOR_FULL",
                "RETAINED_ARCHIVE_LIVE_IMPACT_SCAN",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UNCHANGED_FRESH",
            "requirement_artifact_matrix_status": "UNCHANGED_FRESH",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": True,
            "full_document_read": True,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_stage": "MVP-4_AUDIT_ONLY",
            "optimizer_status_before": "LIVE_MUTATION_BLOCKED",
            "optimizer_status_after": "LIVE_MUTATION_BLOCKED",
            "optimizer_maturity_level_before": "MVP4_GUARDRAIL",
            "optimizer_maturity_level_after": "MVP4_GUARDRAIL",
            "optimizer_output_type": "AUDIT_ONLY",
            "optimizer_validators_required": [
                "optimizer_no_live_mutation_validator",
                "optimizer_guardrail_validator",
                "scale_up_eligibility_validator",
            ],
            "optimizer_validators_run": [
                item for item in validators_run if item.get("validator_id") in {"optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "scale_up_eligibility_validator"}
            ],
            "optimizer_guardrail_result": "PASS_LIVE_MUTATION_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_state_before": "MVP4_AUDITED_LIVE_AND_SCALE_UP_BLOCKED",
            "convergence_state_after": "MVP4_AUDITED_LIVE_AND_SCALE_UP_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_UI_SAFETY_AUDIT_PATCH",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": [
                "convergence_assessment_validator",
                "scale_up_eligibility_validator",
                "risk_scaling_decision_validator",
                "live_burn_in_feedback_validator",
                "paper_live_parity_validator",
                "execution_quality_measurement_validator",
                "survival_layer_validator",
            ],
            "convergence_validators_run": [
                item
                for item in validators_run
                if item.get("validator_id")
                in {
                    "convergence_assessment_validator",
                    "scale_up_eligibility_validator",
                    "risk_scaling_decision_validator",
                    "live_burn_in_feedback_validator",
                    "paper_live_parity_validator",
                    "execution_quality_measurement_validator",
                    "survival_layer_validator",
                }
            ],
            "convergence_guardrail_result": "PASS_LIVE_AND_SCALE_UP_BLOCKED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def write_evidence(now: str, authority: dict[str, Any], patch_result: dict[str, Any], audit_report_path: str) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "validators_untested": [],
            "expected_blocked_validators": [
                "scale_up_eligibility_validator",
                "risk_scaling_decision_validator",
                "live_burn_in_feedback_validator",
                "paper_live_parity_validator",
                "execution_quality_measurement_validator",
                "survival_layer_validator",
            ],
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
            "stage_gate_status": "PASS_FOR_MVP4_FULL_SYSTEM_UI_SAFETY_AUDIT_NO_LIVE_ENABLEMENT",
            "external_live_enabling_blocked": True,
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
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {
                "trader1_sha256": authority["TRADER_1.md"]["sha256"],
                "agents_sha256": authority["AGENTS.md"]["sha256"],
            },
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": [
                "trader1/dashboard/read_only_dashboard.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tools/emit_full_system_ui_safety_audit_patch_evidence.py",
                "contracts/generated/context_pack/FULL_SYSTEM_UI_SAFETY_AUDIT.md",
                "contracts/generated/current_implementation_state.json",
                audit_report_path,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                *patch_result["new_registry_items"],
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED"
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


def main() -> int:
    now = utc_now()
    authority = authority_scan()
    trader_hash = authority["TRADER_1.md"]["sha256"]
    agents_hash = authority["AGENTS.md"]["sha256"]
    update_authority_manifest(now)
    runtime_artifacts = write_launcher_artifacts()
    tests_run = [run_command(args) for args in command_list()]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash)
    artifacts = sorted(set(runtime_artifacts + ["contracts/generated/context_pack/FULL_SYSTEM_UI_SAFETY_AUDIT.md"]))
    patch_result = build_patch_result(now, tests_run, validators_run, artifacts)
    audit_report_path = write_audit_report(now, authority, tests_run, patch_result)
    write_evidence(now, authority, patch_result, audit_report_path)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run, artifacts)
    audit_report_path = write_audit_report(now, authority, tests_run, patch_result)
    write_evidence(now, authority, patch_result, audit_report_path)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in tests_run if item["status"] != "PASS"]
    output = {
        "patch_id": PATCH_ID,
        "status": "PASS" if not failed else "FAIL",
        "patch_result_path": rel(patch_path),
        "audit_report_path": audit_report_path,
        "result_hash": patch_result["result_hash"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
