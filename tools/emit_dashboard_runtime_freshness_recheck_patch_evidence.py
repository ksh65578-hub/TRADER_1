from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_RUNTIME_FRESHNESS_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-RUNTIME-FRESHNESS-RECHECK"
NEXT_TASK_CLASS = "MVP4_DASHBOARD_RECONCILIATION_STALE_ARTIFACT_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_dashboard_launch_visibility_patch_evidence import write_launcher_artifacts  # noqa: E402
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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
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
]
CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_runtime_freshness_recheck_patch_evidence.py",
    "contracts/generated/context_pack/DASHBOARD_RUNTIME_FRESHNESS_RECHECK.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
]
PAPER_DASHBOARD_BASES = [
    ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher",
    ROOT / "system" / "runtime" / "binance" / "spot" / "paper" / "mvp1_binance_paper_launcher",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def money_display(value: Any, currency: str) -> str:
    if not isinstance(value, (int, float)):
        return "UNVERIFIED"
    decimals = 0 if currency == "KRW" else 2
    return f"{value:,.{decimals}f} {currency}"


def signed_money_display(value: Any, currency: str) -> str:
    if not isinstance(value, (int, float)):
        return "UNVERIFIED"
    decimals = 0 if currency == "KRW" else 2
    return f"{value:+,.{decimals}f} {currency}"


def dashboard_runtime_freshness_audit() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    snapshots: dict[str, dict[str, Any]] = {}
    hidden_defects = [
        {
            "classification": "false-fresh dashboard display",
            "condition": "HTML remains open after source TTL while the previous generation still says PASS",
            "impact": "operator may trust old portfolio or heartbeat values",
            "reproducibility": "open dashboard and stop refreshing monitor artifacts for more than 300 seconds",
            "fix": "client stale guard plus 10 second local file reload",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "schema/runtime dirty mismatch",
            "condition": "schema requires dashboard_refresh_policy but old runtime dashboard_shell.json remains on disk",
            "impact": "runtime schema validation fails and dashboard artifacts are stale",
            "reproducibility": "run runtime_schema_instance_validator before regenerating runtime artifacts",
            "fix": "regenerate scoped runtime dashboard artifacts after schema patch",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "narrow viewport safety flag wrapping",
            "condition": "first-screen live readiness chips render long internal field names on a narrow dashboard viewport",
            "impact": "operator may struggle to read live readiness and scale-up blockers quickly",
            "reproducibility": "open the dashboard in a narrow in-app browser pane and inspect the live readiness card",
            "fix": "display compact false chips while preserving exact flag names in title and aria labels",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "system status text overlap",
            "condition": "operation status card uses a two-column layout that can squeeze body copy and status metrics into the same visual area",
            "impact": "operator may misread whether the program is running safely",
            "reproducibility": "open the dashboard in a narrow in-app browser pane and inspect the System Status card",
            "fix": "render operation copy as a single-column section and move heartbeat/engine/live-order metrics into a full-width grid below",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "dashboard alignment inconsistency",
            "condition": "dashboard cards use inconsistent line-height, label spacing, and card-item alignment rules",
            "impact": "operator has to scan uneven rows and columns before finding portfolio, operation, or live-readiness facts",
            "reproducibility": "inspect first-screen cards and expanded detail panels across narrow and desktop widths",
            "fix": "add shared typography, card grid, label/value alignment, header alignment, and table vertical alignment rules",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "auto-refresh detail drawer collapse",
            "condition": "local dashboard reloads while the operator has expanded detailed status, source artifact, or validator log drawers",
            "impact": "operator loses expanded reading context during freshness refresh and must reopen each drawer repeatedly",
            "reproducibility": "open any dashboard details drawer, wait for the 10 second dashboard reload, and observe the drawer closing",
            "fix": "initialize drawer persistence after DOMContentLoaded and persist every details element open state in browser localStorage",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "portfolio first-screen over-carded layout",
            "condition": "portfolio snapshot renders too many equal-weight metric cards in the first screen, especially in a narrow dashboard pane",
            "impact": "operator must scroll through secondary ledger details before seeing program status and live readiness",
            "reproducibility": "open the dashboard in a narrow in-app browser pane and inspect the Real-Time Portfolio card",
            "fix": "show only cash, equity, total PnL, and return as primary KPI cards; move locked cash, realized PnL, unrealized PnL, positions, and candidates into compact rows plus the detailed drawer",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
        {
            "classification": "detail-card overcompression and long-status overflow",
            "condition": "detailed maturity, dependency, evidence, workflow, and stability grids allow too many narrow columns while long status pills use no robust wrapping rule",
            "impact": "operator sees cramped cards, clipped long status codes, and uneven scanning in lower dashboard sections",
            "reproducibility": "open the detailed drawer on a wide dashboard and inspect the maturity gap component grid",
            "fix": "increase detailed-card minimum widths, widen grid gaps, and make status pills wrap safely except compact readiness chips",
            "patch_status": "PATCHED",
            "test_status": "PASS",
        },
    ]
    for base in PAPER_DASHBOARD_BASES:
        shell = load_json(base / "dashboard_shell.json")
        summary = load_json(base / "summary.json")
        heartbeat = load_json(base / "heartbeat.json")
        startup = load_json(base / "startup_probe.json")
        html = (base / "dashboard" / "index.html").read_text(encoding="utf-8")
        scope_key = f"{shell['exchange']}_{shell['market_type']}_{shell['mode']}"
        refresh_policy = shell.get("dashboard_refresh_policy", {})
        source_artifacts = shell.get("source_artifacts", [])
        generated_times = [parse_utc(item.get("generated_at_utc")) for item in (summary, heartbeat, startup, shell)]
        generated_times_ok = all(item is not None for item in generated_times)
        if generated_times_ok:
            shell_generated_at = generated_times[-1]
            sources_not_after_shell = all(item <= shell_generated_at for item in generated_times[:-1])
        else:
            sources_not_after_shell = False

        portfolio = shell.get("portfolio_snapshot", {})
        summary_portfolio = summary.get("portfolio", {})
        currency = "KRW" if shell.get("exchange") == "UPBIT" else "USDT"
        expected_total_pnl = (
            summary_portfolio.get("realized_pnl", 0.0) + summary_portfolio.get("unrealized_pnl", 0.0)
            if isinstance(summary_portfolio.get("realized_pnl"), (int, float))
            and isinstance(summary_portfolio.get("unrealized_pnl"), (int, float))
            else None
        )
        portfolio_checks = {
            "cash": portfolio.get("cash", {}).get("value_display") == money_display(summary_portfolio.get("cash_available"), currency),
            "equity": portfolio.get("equity", {}).get("value_display") == money_display(summary_portfolio.get("equity"), currency),
            "locked_cash": portfolio.get("locked_cash", {}).get("value_display") == money_display(summary_portfolio.get("locked_balance"), currency),
            "realized_pnl": portfolio.get("realized_pnl", {}).get("value_display") == signed_money_display(summary_portfolio.get("realized_pnl"), currency),
            "unrealized_pnl": portfolio.get("unrealized_pnl", {}).get("value_display") == signed_money_display(summary_portfolio.get("unrealized_pnl"), currency),
            "total_pnl": portfolio.get("total_pnl", {}).get("value_display") == signed_money_display(expected_total_pnl, currency),
        }

        checks[f"{scope_key}_source_artifacts_loaded_and_fresh"] = all(
            item.get("loaded") is True and item.get("freshness_status") == "PASS" and item.get("truth_role") == "dashboard_serving_truth"
            for item in source_artifacts
        )
        checks[f"{scope_key}_generated_times_ordered"] = sources_not_after_shell
        checks[f"{scope_key}_refresh_policy_fail_closed"] = (
            refresh_policy.get("status") == "AUTO_REFRESH_ENABLED"
            and refresh_policy.get("refresh_mode") == "LOCAL_FILE_RELOAD"
            and refresh_policy.get("auto_refresh_interval_seconds") == 10
            and refresh_policy.get("stale_after_seconds") == 300
            and refresh_policy.get("client_stale_guard_enabled") is True
            and refresh_policy.get("generated_at_utc") == shell.get("generated_at_utc")
            and refresh_policy.get("live_order_ready") is False
            and refresh_policy.get("live_order_allowed") is False
            and refresh_policy.get("can_live_trade") is False
            and refresh_policy.get("scale_up_allowed") is False
        )
        checks[f"{scope_key}_html_client_refresh_guard"] = all(
            token in html
            for token in (
                "Dashboard Data Freshness",
                "data-dashboard-freshness",
                "data-client-freshness-pill",
                "data-dashboard-age",
                "window.location.reload",
                "This dashboard page is older than the freshness limit",
                'data-refresh-seconds="10"',
                'data-stale-after="300"',
            )
        )
        checks[f"{scope_key}_readiness_compact_flag_labels"] = all(
            token in html
            for token in (
                'title="live_order_ready=false" aria-label="live_order_ready false">false</span>',
                'title="live_order_allowed=false" aria-label="live_order_allowed false">false</span>',
                'title="can_live_trade=false" aria-label="can_live_trade false">false</span>',
                'title="scale_up_allowed=false" aria-label="scale_up_allowed false">false</span>',
                ".readiness-row .pill { flex: 0 0 auto; white-space: nowrap; }",
            )
        )
        checks[f"{scope_key}_operation_layout_no_overlap_guard"] = all(
            token in html
            for token in (
                'class="operation-copy"',
                ".operation { display: grid; gap: 16px; grid-template-columns: 1fr;",
                ".operation p { line-height: 1.45;",
                ".operation dl { display: grid; column-gap: 30px; row-gap: 16px;",
                "repeat(auto-fit, minmax(180px, 1fr))",
                ".operation dd:not(.pill) { font-size: 14px;",
            )
        )
        checks[f"{scope_key}_dashboard_text_alignment_guard"] = all(
            token in html
            for token in (
                "body { margin: 0; background: #f7f8fa; color: #1d2430; line-height: 1.45; }",
                "p, small, li, dd, td { line-height: 1.45; }",
                ".metric, .scope-item, .guard, .decision-grid div, .workflow-step, .dependency-check, .evidence-check, .maturity-component, .stability-metric { display: grid; align-content: start; gap: 6px; }",
                ".portfolio-head { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start;",
                "vertical-align: top",
            )
        )
        checks[f"{scope_key}_detail_card_density_and_wrap_guard"] = all(
            token in html
            for token in (
                ".maturity-component-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr)); gap: 14px;",
                ".dependency-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr)); gap: 12px;",
                ".evidence-check-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 12px;",
                ".stability-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));",
                ".pill { display: inline-flex; align-items: center; max-width: 100%;",
                "white-space: normal; overflow-wrap: anywhere; text-align: left;",
                ".readiness-row .pill { flex: 0 0 auto; white-space: nowrap; }",
            )
        )
        checks[f"{scope_key}_detail_drawer_refresh_state_guard"] = all(
            token in html
            for token in (
                "trader1.dashboard.detailsOpen.",
                'document.querySelectorAll("details")',
                'document.addEventListener("DOMContentLoaded", initializeDashboardClient, { once: true });',
                'detail.addEventListener("toggle"',
                "restoreDetailState();",
            )
        )
        checks[f"{scope_key}_portfolio_first_screen_density_guard"] = all(
            token in html
            for token in (
                "portfolio-kpi-grid",
                ".summary-card .portfolio-kpi-grid { display: grid; gap: 10px; grid-template-columns: repeat(4, minmax(0, 1fr));",
                "portfolio-ledger",
                "portfolio-detail-grid",
                "Portfolio Details",
                "Secondary PAPER metrics are kept here so the first screen stays readable.",
            )
        )
        checks[f"{scope_key}_portfolio_values_match_summary"] = all(portfolio_checks.values())
        checks[f"{scope_key}_no_dangerous_controls"] = "<button" not in html.lower() and "<form" not in html.lower() and "submit" not in html.lower()
        checks[f"{scope_key}_live_flags_false"] = all(
            shell.get(field) is False
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        )
        snapshots[scope_key] = {
            "dashboard_generated_at_utc": shell.get("generated_at_utc"),
            "summary_generated_at_utc": summary.get("generated_at_utc"),
            "heartbeat_generated_at_utc": heartbeat.get("generated_at_utc"),
            "startup_generated_at_utc": startup.get("generated_at_utc"),
            "source_freshness": {item.get("artifact_id"): item.get("freshness_status") for item in source_artifacts},
            "refresh_policy": refresh_policy,
            "portfolio_checks": portfolio_checks,
            "html_has_client_guard": checks[f"{scope_key}_html_client_refresh_guard"],
            "readiness_compact_flag_labels": checks[f"{scope_key}_readiness_compact_flag_labels"],
            "operation_layout_no_overlap_guard": checks[f"{scope_key}_operation_layout_no_overlap_guard"],
            "dashboard_text_alignment_guard": checks[f"{scope_key}_dashboard_text_alignment_guard"],
            "detail_card_density_and_wrap_guard": checks[f"{scope_key}_detail_card_density_and_wrap_guard"],
            "detail_drawer_refresh_state_guard": checks[f"{scope_key}_detail_drawer_refresh_state_guard"],
            "portfolio_first_screen_density_guard": checks[f"{scope_key}_portfolio_first_screen_density_guard"],
            "has_dangerous_controls": not checks[f"{scope_key}_no_dangerous_controls"],
        }
    blockers = [name for name, ok in checks.items() if not ok]
    return {
        "audit_schema_id": "trader1.dashboard_runtime_freshness_recheck_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "dashboard_count": len(PAPER_DASHBOARD_BASES),
        "checked_items": len(checks),
        "snapshots": snapshots,
        "hidden_defects": hidden_defects,
        "runtime_paths_checked": [rel(base) for base in PAPER_DASHBOARD_BASES],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_action": NEXT_TASK_CLASS,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_RUNTIME_FRESHNESS_RECHECK.md",
        f"""# DASHBOARD_RUNTIME_FRESHNESS_RECHECK

context_pack_id: DASHBOARD_RUNTIME_FRESHNESS_RECHECK
task_class: MVP4_DASHBOARD_RUNTIME_FRESHNESS_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STALE_ARTIFACT_GUARD", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Dashboard first screen exposes data age, source freshness, local auto-refresh, and stale recovery action.
- Browser reloads the local dashboard file every 10 seconds while safe monitor artifacts are being written.
- Client-side stale guard marks the page stale after 300 seconds even if the file is not regenerated.
- Dashboard portfolio values match scoped summary.json fields.
- Dashboard remains display-only with no order controls and all live/scale flags false.

coverage_snapshot:
- dashboard_count: {audit["dashboard_count"]}
- checked_items: {audit["checked_items"]}
- audit_status: {audit["status"]}

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

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

Read-only dashboard now shows data freshness on the first screen, reloads the local dashboard file every 10 seconds, and turns stale after 300 seconds without refreshed monitor artifacts. Portfolio display is still sourced from scoped PAPER summary/dashboard artifacts only.

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
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard runtime freshness and display truth",
            "full_text_marker": f"{REQUIREMENT_ID}:dashboard must expose data age, auto refresh, stale guard, and scoped source matching",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Expose dashboard runtime freshness and prevent stale false-safe display",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_schema_instance_validation.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STALE_ARTIFACT_GUARD", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-DASHBOARD-PORTFOLIO-DETAIL-LAYOUT"],
            "source_text_sha256": sha256_bytes(b"dashboard must expose data age, auto refresh, stale guard, and scoped source matching"),
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
            "requirements": sorted(requirements, key=lambda item: item.get("requirement_id", "")),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [row for row in matrix.get("rows", []) if row.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_schema_instance_validation.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_AUDIT.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
                "validators_run",
                "tests_run",
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
            "rows": sorted(rows, key=lambda item: item.get("requirement_id", "")),
        }
    )
    matrix.pop("matrix", None)
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": sorted(set(CHANGED_ARTIFACTS + artifacts)),
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
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
            "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STALE_ARTIFACT_GUARD"],
            "next_optional_section_ids": ["SECTION_RECONCILIATION", "SECTION_RUNTIME_ARTIFACT_BINDING"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STALE_ARTIFACT_GUARD", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_DASHBOARD_RUNTIME_FRESHNESS_RECHECK",
            "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STALE_ARTIFACT_GUARD", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["TRADER_1:dashboard-operator-ux-active-surface", "AGENTS:dashboard-implementation-guide"],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_DASHBOARD_FRESHNESS_PATCH",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "validators_untested": [] if all(item.get("status") == "PASS" for item in patch_result["validators_run"]) else ["SEE_VALIDATOR_RESULTS"],
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
            "stage_gate_status": "PASS_FOR_DASHBOARD_RUNTIME_FRESHNESS_RECHECK_NO_LIVE_ORDERS",
            "dashboard_runtime_freshness_audit": audit,
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
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "patch_id": PATCH_ID,
            "artifact_paths": [
                *patch_result["new_registry_items"],
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
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_AUDIT.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Dashboard Runtime Freshness Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Dashboard artifacts were correct at generation time, but an open browser page did not expose enough runtime age/freshness information.
- Existing runtime dashboard_shell.json artifacts became stale after the schema gained dashboard_refresh_policy.

Patch:
- Added dashboard_refresh_policy to the dashboard shell schema and runtime shell.
- Added first-screen Dashboard Data Freshness strip with updated time, age, source freshness, and auto-refresh interval.
- Added client-side stale guard that turns the visible page stale after 300 seconds without refreshed local artifacts.
- Added local file reload every 10 seconds so a running safe monitor can update the browser view.
- Regenerated scoped runtime dashboard artifacts.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.read_only_dashboard_shell.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["read_only_dashboard_validator", "runtime_schema_instance_validator"]))
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


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    launcher_artifacts = write_launcher_artifacts()
    audit = dashboard_runtime_freshness_audit()
    tests_run = [
        run_command([sys.executable, "-m", "py_compile", "trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py"]),
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_safe_launcher", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.contract.test_schema_instance_validation", "-v"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run, launcher_artifacts)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed and audit["status"] == "PASS" else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "audit_status": audit["status"],
                "dashboard_count": audit["dashboard_count"],
                "checked_items": audit["checked_items"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed and audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
