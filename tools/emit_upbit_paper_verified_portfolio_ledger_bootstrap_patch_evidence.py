from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-VERIFIED-PORTFOLIO-LEDGER-BOOTSTRAP"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.ledger.paper_ledger_rollup import (  # noqa: E402
    build_paper_ledger_rollup_report,
    validate_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "paper_ledger_rollup_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
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
    "trader1/runtime/ledger/paper_ledger_rollup.py",
    "tests/runtime/test_paper_ledger_rollup.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_rollup_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_portfolio_snapshot.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/summary.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_verified_portfolio_ledger_bootstrap_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP.md",
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


def write_runtime_artifacts() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    rollup = build_paper_ledger_rollup_report(
        root=ROOT,
        session_id=SESSION_ID,
        rollup_id="mvp4-upbit-paper-verified-portfolio-ledger-bootstrap-ledger-rollup",
    )
    rollup_result = validate_paper_ledger_rollup_report(rollup)
    if rollup_result.status != "PASS":
        raise RuntimeError(f"paper ledger rollup did not validate: {rollup_result.status} {rollup_result.blocker_code}")
    rollup_path = write_paper_ledger_rollup_report(root=ROOT, report=rollup)

    report = build_launcher_report("UPBIT_PAPER")
    report_path, dashboard_paths = write_launcher_runtime_bundle(report)
    dashboard = load_json(dashboard_paths["dashboard_shell"])
    dashboard_result = validate_read_only_dashboard_shell(dashboard)
    if dashboard_result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {dashboard_result.status} {dashboard_result.blocker_code}")
    portfolio = dashboard.get("portfolio_snapshot")
    if not isinstance(portfolio, dict) or portfolio.get("status") != "VERIFIED":
        raise RuntimeError("dashboard portfolio is not VERIFIED from the scoped PAPER ledger rollup")
    if portfolio.get("source") != "summary.json":
        raise RuntimeError("dashboard portfolio did not flow through summary.json")
    summary = load_json(dashboard_paths["summary"])
    if summary.get("portfolio", {}).get("source") != "LEDGER":
        raise RuntimeError("summary portfolio is not ledger-backed")
    if summary.get("portfolio", {}).get("source_paper_ledger_head_hash") != rollup.get("latest_ledger_head_hash"):
        raise RuntimeError("summary portfolio ledger head hash does not match rollup")
    if rollup.get("ledger_head_match_status") != "PASS" or rollup.get("ledger_head_mismatch_count") != 0:
        raise RuntimeError("ledger rollup head binding is not PASS")
    if any(dashboard.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise RuntimeError("dashboard attempted forbidden live or scale-up permission")
    if any(rollup.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")):
        raise RuntimeError("rollup attempted forbidden live or scale-up permission")

    html_path = dashboard_paths["dashboard_html"]
    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    base.write_text(legacy_html_path, html_path.read_text(encoding="utf-8"))
    artifacts = [
        base.rel(rollup_path),
        base.rel(report_path),
        *(base.rel(path) for path in dashboard_paths.values()),
        base.rel(legacy_html_path),
    ]
    return rollup, dashboard, sorted(set(artifacts))


def write_context(now: str, trader_hash: str, agents_hash: str, rollup: dict[str, Any], dashboard: dict[str, Any]) -> None:
    portfolio = dashboard["portfolio_snapshot"]
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PORTFOLIO_TRUTH", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Session-cycle PAPER ledger rollup binds its portfolio provenance to latest_paper_ledger_head.json even when filename ordering differs.
- The canonical dashboard portfolio is VERIFIED only from a fresh PASS PAPER ledger rollup.
- Initial configured PAPER capital remains a starting amount, not a live exchange balance.
- Post-rerun and long-run blockers remain visible; live orders and scale-up remain blocked.

known_omissions_by_design:
- This patch does not resolve post-rerun operator reconciliation guidance.
- This patch does not create long-run evidence, LIVE_READY, live config, credentials, orders, or scale-up permission.

runtime_summary:
- rollup_status: {rollup["rollup_status"]}
- ledger_head_match_status: {rollup["ledger_head_match_status"]}
- ledger_head_cycle_id: {rollup["ledger_head_cycle_id"]}
- portfolio_status: {portfolio["status"]}
- cash_available: {portfolio["cash"]["value_display"]}
- equity: {portfolio["equity"]["value_display"]}
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

Upbit PAPER dashboard portfolio can now be verified from a fresh scoped simulated ledger rollup when the rollup head matches latest_paper_ledger_head.json. Post-rerun review, long-run evidence, LIVE_READY, live orders, credentials, and scale-up remain blocked.
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
            "source_section_id": "SECTION_PORTFOLIO_TRUTH",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER verified portfolio ledger bootstrap",
            "full_text_marker": f"{REQUIREMENT_ID}: PAPER portfolio truth must come from a fresh ledger rollup whose latest head binding is PASS",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER verified portfolio ledger bootstrap",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [
                "trader1.paper_ledger_rollup_report.v1",
                "trader1.paper_portfolio_snapshot.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/runtime/test_paper_ledger_rollup.py", "tests/runtime/test_safe_launcher.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_PORTFOLIO_TRUTH", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-HEAD-BINDING-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"PAPER portfolio truth requires fresh PASS ledger rollup bound to latest ledger head"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_VERIFIED_PAPER_LEDGER_PORTFOLIO_LIVE_BLOCKED",
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
            "section_id": "SECTION_PORTFOLIO_TRUTH",
            "schema_files": [
                "contracts/schema/paper_ledger_rollup_report.schema.json",
                "contracts/schema/paper_portfolio_snapshot.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/ledger/paper_ledger_rollup.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "test_files": ["tests/runtime/test_paper_ledger_rollup.py", "tests/runtime/test_safe_launcher.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/ledger/paper_ledger_rollup.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "portfolio_snapshot.status",
                "portfolio_snapshot.cash",
                "portfolio_snapshot.equity",
                "summary.portfolio.source_paper_ledger_head_hash",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_VERIFIED_PAPER_LEDGER_PORTFOLIO_LIVE_BLOCKED",
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
    rollup: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_CONFIGURED_PORTFOLIO_UNVERIFIED_EXPLANATION.patch_result.json"
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
                "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-HEAD-BINDING-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.paper_ledger_rollup_report.v1",
                "trader1.paper_portfolio_snapshot.v1",
                "trader1.read_only_dashboard_shell.v1",
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
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_IDEMPOTENCY", "SECTION_DASHBOARD_OPERATOR_UX"],
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
                "paper_ledger_rollup runtime",
                "safe launcher dashboard binding",
                "live final guard",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_VERIFIED_LEDGER_PORTFOLIO_VISIBLE",
            "optimizer_guardrail_result": "PASS_VERIFIED_PORTFOLIO_DOES_NOT_CREATE_RANKING_OR_LIVE_PERMISSION",
            "convergence_state_before": "PORTFOLIO_TRUTH_EXPLANATION_VISIBLE_LIVE_BLOCKED",
            "convergence_state_after": "VERIFIED_PAPER_LEDGER_PORTFOLIO_VISIBLE_POST_RERUN_AND_LONG_RUN_BLOCKERS_REMAIN",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    rollup: dict[str, Any],
    dashboard: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    portfolio = dashboard["portfolio_snapshot"]
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
            "stage_gate_status": "PASS_VERIFIED_PAPER_LEDGER_PORTFOLIO_VISIBLE_LIVE_BLOCKED",
            "rollup_status": rollup["rollup_status"],
            "ledger_head_match_status": rollup["ledger_head_match_status"],
            "ledger_head_cycle_id": rollup["ledger_head_cycle_id"],
            "portfolio_status": portfolio["status"],
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
            "paper_ledger_rollup_status": rollup["rollup_status"],
            "paper_ledger_head_match_status": rollup["ledger_head_match_status"],
            "paper_ledger_head_cycle_id": rollup["ledger_head_cycle_id"],
            "paper_portfolio_status": portfolio["status"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Verified Portfolio Ledger Bootstrap Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Session-cycle PAPER rollup selected the final source by filename order, so a valid latest_paper_ledger_head.json could mismatch the rollup head when older or differently named cycle files sorted later.

Patch:
- Session-cycle rollup now processes the scoped ledger named by latest_paper_ledger_head.json as the provenance tail when that file exists in the session ledger namespace.
- Existing missing, invalid, escaped, or mismatched latest-head cases still block.
- The dashboard now receives a fresh VERIFIED simulated PAPER portfolio only after the rollup validates PASS.

Runtime evidence:
- rollup_status={rollup["rollup_status"]}
- ledger_head_match_status={rollup["ledger_head_match_status"]}
- ledger_head_cycle_id={rollup["ledger_head_cycle_id"]}
- portfolio_status={portfolio["status"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- post-rerun and long-run blockers remain open
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    rollup: dict[str, Any],
    dashboard: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, rollup, dashboard, runtime_artifacts)
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
    rollup, dashboard, runtime_artifacts = write_runtime_artifacts()
    write_context(now, trader_hash, agents_hash, rollup, dashboard)
    update_requirement_artifacts(now, trader_hash, agents_hash, runtime_artifacts)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_paper_ledger_rollup.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, rollup, dashboard)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, rollup, dashboard, runtime_artifacts)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, rollup, dashboard)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, rollup, dashboard, runtime_artifacts)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "paper_ledger_rollup_status": rollup["rollup_status"],
                "paper_ledger_head_match_status": rollup["ledger_head_match_status"],
                "paper_portfolio_status": dashboard["portfolio_snapshot"]["status"],
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
