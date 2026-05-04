from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_profitability_optimizer_evidence_maturity_recheck_patch_evidence as base  # noqa: E402


PATCH_BASENAME = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-IMPLEMENTATION-DEPTH-RECHECK"
CONTRACT_GAP_ID = "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK"

ROBUSTNESS_SOURCE_TYPE_EVIDENCE = {
    "status": "BLOCKED_FOR_SOURCE_TYPE_EVIDENCE",
    "required_source_types": ["OOS", "WALK_FORWARD", "BOOTSTRAP", "CONCENTRATION"],
    "present_source_types": [],
    "missing_source_types": ["OOS", "WALK_FORWARD", "BOOTSTRAP", "CONCENTRATION"],
    "source_type_counts": {
        "oos_count": 0,
        "walk_forward_count": 0,
        "bootstrap_count": 0,
        "concentration_count": 0,
    },
    "min_required_per_source_type": 1,
    "source_artifact_paths": [
        "contracts/schema/overfit_diagnostic_report.schema.json",
        "tests/validators/fixtures/overfit_diagnostic_pass.json",
    ],
    "source_evidence_ids": [
        "REQ-MVP4-OOS-ROBUSTNESS-SCHEMA-HARDENING",
        "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY-IMPLEMENTATION-DEPTH-RECHECK",
    ],
    "primary_blocker_code": "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED",
    "explicit_source_type_blocker": True,
    "live_order_ready": False,
    "live_order_allowed": False,
    "can_live_trade": False,
    "scale_up_allowed": False,
}

CHANGED_ARTIFACTS = sorted(
    set(
        base.CHANGED_ARTIFACTS
        + [
            "contracts/schema/profitability_evidence_maturity_rollup.schema.json",
            "contracts/schema/read_only_dashboard_shell.schema.json",
            "trader1/dashboard/read_only_dashboard.py",
            "trader1/validation/mvp0_validators.py",
            "tests/dashboard/test_read_only_dashboard.py",
            "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
            f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            "tools/emit_profitability_optimizer_evidence_maturity_implementation_depth_recheck_patch_evidence.py",
        ]
    )
)

BLOCKERS = sorted(set(base.BLOCKERS + ["ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED"]))


def _patch_base_globals() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


_original_refresh_rollup = base.refresh_rollup
_original_update_contract_gap = base.update_contract_gap
_original_update_navigation = base.update_navigation
_original_build_patch_result = base.build_patch_result


def refresh_rollup(path: Path, now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    rollup = _original_refresh_rollup(path, now, trader_hash, agents_hash)
    rollup["robustness_source_type_evidence"] = dict(ROBUSTNESS_SOURCE_TYPE_EVIDENCE)
    rollup["rollup_hash"] = ""
    rollup["rollup_hash"] = base.sha256_json({key: value for key, value in rollup.items() if key != "rollup_hash"})
    base.write_json(path, rollup)
    return rollup


def update_contract_gap(now: str, trader_hash: str, agents_hash: str) -> None:
    _original_update_contract_gap(now, trader_hash, agents_hash)
    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    gap = base.load_json(gap_path)
    blocker_codes = {item.get("code") for item in gap.get("blockers", []) if isinstance(item, dict)}
    if "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED" not in blocker_codes:
        gap.setdefault("blockers", []).append(
            {
                "code": "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED",
                "severity": "HIGH",
                "message": (
                    "OOS, walk-forward, bootstrap, and concentration source-type evidence is now explicit "
                    "and remains missing; optimizer evidence maturity is live-blocked."
                ),
                "source_requirement_id": REQUIREMENT_ID,
            }
        )
    gap["notes"] = (
        "Implementation-depth recheck added explicit robustness_source_type_evidence for OOS, walk-forward, "
        "bootstrap, and concentration evidence. All four source types remain missing, the gap remains OPEN, "
        "and no live review, live order, or scale-up permission is created."
    )
    base.write_json(gap_path, gap)


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    _original_update_navigation(now, trader_hash, agents_hash)
    context_pack_path = ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md"
    base.write_text(
        context_pack_path,
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR", "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1"]
included_validator_ids: {json.dumps(base.VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Rollup requires robustness_source_type_evidence.
- OOS, walk-forward, bootstrap, and concentration evidence source types are counted separately.
- Missing source types keep ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED visible.
- False PASS, hidden missing source types, and live/scale drift fail closed.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not create OOS, walk-forward, bootstrap, concentration, read-only burn-in, manual order, or operator approval evidence.
- No live execution, credential use, LIVE_READY write, live config mutation, or risk scale-up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str] | None = None,
) -> dict[str, Any]:
    patch_result = _original_build_patch_result(now, tests_run, validators_run, validators_required)
    patch_result.update(
        {
            "task_class": "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK",
            "optimizer_patch": "PROFITABILITY_EVIDENCE_MATURITY_ROBUSTNESS_SOURCE_TYPE_DEPTH_RECHECK_NO_LIVE_MUTATION",
            "optimizer_status_after": "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_EXPLICIT_LIVE_BLOCKED",
            "optimizer_maturity_level_after": "MVP4_ROBUSTNESS_SOURCE_TYPE_EXPLICIT_LIVE_BLOCKED",
            "convergence_state_after": "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_EXPLICIT_LIVE_BLOCKED",
            "remaining_blockers": BLOCKERS,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_OPTIMIZER_GUARDRAIL",
            ],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def main() -> int:
    _patch_base_globals()
    base.refresh_rollup = refresh_rollup
    base.update_contract_gap = update_contract_gap
    base.update_navigation = update_navigation
    base.build_patch_result = build_patch_result
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
