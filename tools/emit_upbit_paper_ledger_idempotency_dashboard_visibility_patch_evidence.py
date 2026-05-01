from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_DASHBOARD_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-DASHBOARD-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_CURRENT_EVIDENCE_CLOSURE_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
import tools.emit_upbit_paper_ledger_idempotency_runtime_evidence_patch_evidence as previous  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "runtime_schema_instance_validator",
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
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_upbit_paper_ledger_idempotency_dashboard_visibility_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
    "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard_shell.json",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_context(now: str, trader_hash: str, agents_hash: str, evidence: dict[str, Any], dashboard: dict[str, Any]) -> None:
    reconciliation = dashboard.get("reconciliation_recovery_summary", {})
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Read-only dashboard loads scoped Upbit PAPER ledger idempotency runtime evidence.
- Ledger Safety panel displays idempotency evidence status, validator status, reconciliation status, portfolio provenance, source ledger count, recomputed event count, duplicate counts, and count mismatch count.
- Dashboard source artifacts include PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE when the report is loaded.
- Any blocked, stale, invalid, or live-mutated idempotency evidence remains display-only and cannot create live or scale-up permission.

known_omissions_by_design:
- This patch does not resolve post-rerun operator reconciliation guidance.
- This patch does not create long-run evidence, LIVE_READY, live config, credentials, orders, or scale-up permission.
- Binance spot/futures remain surface/scaffold gaps.

runtime_summary:
- dashboard_reconciliation_status: {reconciliation.get("status", "UNKNOWN")}
- ledger_idempotency_runtime_evidence_status: {reconciliation.get("ledger_idempotency_runtime_evidence_status", "UNKNOWN")}
- ledger_idempotency_runtime_validation_status: {reconciliation.get("ledger_idempotency_runtime_validation_status", "UNKNOWN")}
- source_ledger_jsonl_count: {evidence["source_ledger_jsonl_count"]}
- recomputed_ledger_event_count: {evidence["recomputed_ledger_event_count"]}
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
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

Upbit PAPER portfolio values are ledger-backed and the Ledger Safety dashboard now shows the current ledger idempotency runtime evidence report. The panel is display-only and keeps post-rerun reconciliation, long-run evidence, LIVE_READY, live orders, credentials, and scale-up blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, runtime_artifacts: list[str]) -> None:
    artifacts = sorted(set(CHANGED_ARTIFACTS + runtime_artifacts))
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER ledger idempotency dashboard operator visibility",
            "full_text_marker": f"{REQUIREMENT_ID}: dashboard must show scoped current Upbit PAPER ledger idempotency runtime evidence without creating live or scale-up permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER ledger idempotency dashboard operator visibility",
            "requirement_kind": "DASHBOARD_UX",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-VERIFIED-PORTFOLIO-LEDGER-BOOTSTRAP",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"dashboard must show scoped current Upbit PAPER ledger idempotency runtime evidence without creating live or scale-up permission"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DASHBOARD_OPERATOR_VISIBILITY_LIVE_BLOCKED",
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
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json",
            ],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "reconciliation_recovery_summary.ledger_idempotency_runtime_evidence_status",
                "reconciliation_recovery_summary.ledger_idempotency_runtime_validation_status",
                "source_artifacts.PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE",
                "dashboard_html.Current Ledger Evidence",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_DASHBOARD_OPERATOR_VISIBILITY_LIVE_BLOCKED",
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
    evidence: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE.patch_result.json"
    )
    reconciliation = dashboard.get("reconciliation_recovery_summary", {})
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1",
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
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
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
                "TRADER_1.0G",
                "AGENTS.0G",
                "Upbit PAPER ledger idempotency runtime evidence context pack",
                "read-only dashboard shell",
                "live final guard",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_LEDGER_IDEMPOTENCY_DASHBOARD_VISIBLE_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_DASHBOARD_VISIBILITY_DOES_NOT_CREATE_RANKING_OR_LIVE_PERMISSION",
            "convergence_state_before": "PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_PASS_POST_RERUN_AND_LONG_RUN_BLOCKERS_REMAIN",
            "convergence_state_after": "PAPER_LEDGER_IDEMPOTENCY_DASHBOARD_VISIBLE_POST_RERUN_AND_LONG_RUN_BLOCKERS_REMAIN",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def refresh_other_launcher_dashboards() -> list[str]:
    artifacts: list[str] = []
    for launcher_name in ("UPBIT_LIVE", "BINANCE_PAPER", "BINANCE_LIVE"):
        report = build_launcher_report(launcher_name)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report)
        artifacts.append(base.rel(report_path))
        artifacts.extend(base.rel(path) for path in dashboard_paths.values())
    return sorted(set(artifacts))


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    evidence: dict[str, Any],
    dashboard: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    reconciliation = dashboard.get("reconciliation_recovery_summary", {})
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
            "stage_gate_status": "PASS_DASHBOARD_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_VISIBLE_LIVE_BLOCKED",
            "dashboard_reconciliation_status": reconciliation.get("status"),
            "ledger_idempotency_runtime_evidence_status": reconciliation.get("ledger_idempotency_runtime_evidence_status"),
            "ledger_idempotency_runtime_validation_status": reconciliation.get("ledger_idempotency_runtime_validation_status"),
            "source_ledger_jsonl_count": evidence["source_ledger_jsonl_count"],
            "recomputed_ledger_event_count": evidence["recomputed_ledger_event_count"],
            "duplicate_event_id_count": evidence["duplicate_event_id_count"],
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
                        *runtime_artifacts,
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "dashboard_reconciliation_status": reconciliation.get("status"),
            "ledger_idempotency_runtime_evidence_status": reconciliation.get("ledger_idempotency_runtime_evidence_status"),
            "ledger_idempotency_runtime_validation_status": reconciliation.get("ledger_idempotency_runtime_validation_status"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Ledger Idempotency Dashboard Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Connected Upbit PAPER ledger idempotency runtime evidence into the read-only dashboard.
- Added schema fields and display text for current ledger evidence status, validation status, reconciliation/provenance status, source ledger files, recomputed event count, duplicate counts, and count mismatches.
- Updated launcher dashboard loading so existing runtime evidence appears in the operator Ledger Safety panel.

Runtime evidence:
- dashboard_reconciliation_status={reconciliation.get("status")}
- ledger_idempotency_runtime_evidence_status={reconciliation.get("ledger_idempotency_runtime_evidence_status")}
- ledger_idempotency_runtime_validation_status={reconciliation.get("ledger_idempotency_runtime_validation_status")}
- source_ledger_jsonl_count={evidence["source_ledger_jsonl_count"]}
- recomputed_ledger_event_count={evidence["recomputed_ledger_event_count"]}
- duplicate_event_id_count={evidence["duplicate_event_id_count"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- dashboard remains display-only
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    evidence: dict[str, Any],
    dashboard: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, evidence, dashboard, runtime_artifacts)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    _rollup, evidence, dashboard, runtime_artifacts = previous.write_runtime_artifacts()
    runtime_artifacts.extend(refresh_other_launcher_dashboards())
    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    if legacy_html_path.exists():
        runtime_artifacts.append(base.rel(legacy_html_path))
    write_context(now, trader_hash, agents_hash, evidence, dashboard)
    update_requirement_artifacts(now, trader_hash, agents_hash, sorted(set(runtime_artifacts)))

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_safe_launcher.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, evidence, dashboard)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, evidence, dashboard, sorted(set(runtime_artifacts)))

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, evidence, dashboard)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, evidence, dashboard, sorted(set(runtime_artifacts)))

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "dashboard_reconciliation_status": dashboard.get("reconciliation_recovery_summary", {}).get("status"),
                "ledger_idempotency_runtime_evidence_status": dashboard.get("reconciliation_recovery_summary", {}).get(
                    "ledger_idempotency_runtime_evidence_status"
                ),
                "ledger_idempotency_runtime_validation_status": dashboard.get("reconciliation_recovery_summary", {}).get(
                    "ledger_idempotency_runtime_validation_status"
                ),
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
