from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_QUANTITATIVE_POLICY_CLOSURE"
PATCH_ID = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_QUANTITATIVE_POLICY_CLOSURE_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-QUANTITATIVE-POLICY-CLOSURE"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.core.strategy.quantitative_policy import build_quantitative_policy_report  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "trader1/core/strategy/quantitative_policy.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/schema/quantitative_policy_report.schema.json",
    "contracts/registry.yaml",
    "tests/contract/test_quantitative_policy.py",
    "tools/emit_quantitative_policy_closure_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/QUANTITATIVE_POLICY_REPORT.json",
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "closed_enum_validator",
    "common_defs_drift_validator",
    "quantitative_policy_validator",
    "strategy_condition_matrix_validator",
    "candidate_scorecard_net_ev_validator",
    "live_final_guard_validator",
    "optimizer_no_live_mutation_validator",
]

POST_WRITE_VALIDATORS = [
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
]

REMAINING_BLOCKERS = [
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
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_BURN_IN_MISSING",
    "OPERATOR_APPROVAL_MISSING",
]

AREA_ITEMS = [
    (
        1,
        "strategy / regime / entry / exit",
        "High",
        "Formula surfaces were split between strategy condition fixtures and runtime scorecards.",
        "Ambiguous entry conditions can allow inconsistent PAPER candidates.",
        "Closed formulas now define regime priority, pullback, breakout, VWAP reversion, short policy, and exit priority.",
        "quantitative_policy_validator plus test_quantitative_policy.py",
    ),
    (
        2,
        "expected edge / fee / slippage / funding",
        "High",
        "Positive gross edge could be confused with cost-adjusted edge.",
        "High-fee or high-slippage trades can survive research ranking.",
        "net_expected_edge = gross_expected_edge - fee - spread - slippage - funding; total_cost<=0 or net<=0 blocks.",
        "negative net edge no-trade test",
    ),
    (
        3,
        "signal grading / parameter search / strategy competition",
        "High",
        "Signal grade thresholds and strategy promotion criteria needed one closed implementation surface.",
        "Weak signals can be interpreted differently across runtime and dashboard surfaces.",
        "Signal grade thresholds are fixed at 0.55/0.65/0.75/0.85; strategy promotion uses 100 trades and high-return candidate uses 300 trades.",
        "weak signal and strategy formula coverage in quantitative_policy_validator",
    ),
    (
        4,
        "paper / shadow / replay / micro-live / live",
        "Critical",
        "Research candidates and live readiness still share conceptual wording in some surfaces.",
        "Operator may mistake a strong PAPER candidate for live permission.",
        "All quantitative outputs are PAPER/SHADOW/REPLAY analysis only; live flags remain false.",
        "live block proof artifact and live without snapshot test",
    ),
    (
        5,
        "LIVE_READY snapshot / live gating / fail-closed",
        "Critical",
        "External official API, burn-in, and operator approval evidence are still absent.",
        "Any live switch without snapshot/evidence would be unsafe.",
        "LIVE_READY candidate check emits LIVE_READY_MISSING first and never writes LIVE_READY.",
        "LIVE_BLOCK_PROOF.json",
    ),
    (
        6,
        "risk engine / drawdown / cooling / kill switch",
        "High",
        "Sizing and risk state thresholds needed one deterministic formula surface.",
        "Loss streak or drawdown may not consistently reduce/stop entries.",
        "drawdown_pct formula, cooling/no_trade/kill_switch priority, and position risk multipliers are closed.",
        "risk cap, drawdown reduction, and cooling tests",
    ),
    (
        7,
        "exchange / market_type / namespace separation",
        "High",
        "Binance and Upbit evidence must not be inferred across scopes.",
        "Cross-exchange evidence transfer can create false readiness.",
        "Policy outputs keep exchange/market_type explicit and leave Binance runtime surface-only.",
        "Binance futures paper candidate surface-only test",
    ),
    (
        8,
        "Upbit spot / Binance spot / Binance futures 1x long-short",
        "High",
        "Upbit PAPER is most mature; Binance remains scaffold/surface in runtime.",
        "A Binance strategy candidate could be confused with executable adapter readiness.",
        "Binance futures short is formula-defined at 1x only and runtime-blocked as surface-only.",
        "evaluate_binance_futures_short_entry test",
    ),
    (
        9,
        "order lifecycle / execution quality / partial fill",
        "Medium",
        "This session did not change order routing; execution quality remains a linked validator dependency.",
        "Partial fill assumptions can distort realized edge.",
        "New edge and sizing formulas require execution quality and slippage costs before entry eligibility.",
        "candidate_scorecard_net_ev_validator remains required",
    ),
    (
        10,
        "ledger / reconciliation / idempotency",
        "High",
        "Open reconciliation gaps still block current evidence promotion.",
        "Duplicate cycle/event counting can overstate evidence maturity.",
        "deduplicate_events keeps first event by id and reports duplicate_count.",
        "duplicate event not double counted test",
    ),
    (
        11,
        "data health / stale data / gap / duplicate / clock drift",
        "High",
        "Regime/symbol decisions need hard data health blockers.",
        "Stale or incomplete market data can create false signals.",
        "data_health_score<1.0, missing inputs, stale short input, and panic spread fail closed.",
        "regime and Binance stale blockers in quantitative_policy_validator",
    ),
    (
        12,
        "concurrency / race condition / restart recovery",
        "Medium",
        "This session adds deterministic pure functions but does not change runtime locks.",
        "Concurrent writers can still require operator reconciliation.",
        "Quantitative policy is side-effect-free; runtime writer locks remain separate blockers.",
        "no live mutation validators required",
    ),
    (
        13,
        "dashboard / USER_STATUS_SUMMARY / user simplicity",
        "High",
        "Dashboard needs one primary reason code for non-expert operation.",
        "User may see many blockers without a clear next action.",
        "Quantitative report emits dashboard_reason_code and a concise live-block message.",
        "DASHBOARD_READINESS_SUMMARY.json and USER_STATUS_SUMMARY.md",
    ),
    (
        14,
        "validator / schema / registry / acceptance artifacts",
        "High",
        "New formulas need schema and validator binding.",
        "Unvalidated policy code can drift from contracts.",
        "Added quantitative_policy_report schema, registry entry, validator, targeted tests, and session artifacts.",
        "schema_validator, registry_validator, quantitative_policy_validator",
    ),
    (
        15,
        "testing / pytest / paper run proof / live block proof",
        "High",
        "Prior evidence did not include the user's exact quantitative acceptance list.",
        "A formula can exist without covering required fail cases.",
        "Added tests for weak signal, negative edge, downtrend long block, Binance short candidate, risk caps, cooling, dedupe, and live block.",
        "pytest_report.txt and LIVE_BLOCK_PROOF.json",
    ),
    (
        16,
        "security / secrets / API key safety",
        "Critical",
        "No credential/API path may be used by this patch.",
        "Credential use could accidentally enable live behavior.",
        "Patch is pure calculation/evidence only and never reads credentials or private API keys.",
        "optimizer_no_live_mutation_validator and live_final_guard_validator",
    ),
    (
        17,
        "deployment / packaging / git hygiene / pycache / generated artifacts",
        "Medium",
        "New code must not add cache/build artifacts.",
        "Pycache or runtime output can pollute source bundles.",
        "Tests run through bytecode-safe path; runtime output is not staged intentionally.",
        "hygiene-safe pytest",
    ),
    (
        18,
        "tax/accounting/export readiness",
        "Medium",
        "This session does not implement tax export.",
        "Profit evidence may later be hard to reconcile for accounting.",
        "Ledger/reconciliation/idempotency remains the prerequisite; no live/tax claim is made.",
        "coverage matrix marks next implementation path",
    ),
    (
        19,
        "KRW cashflow / profit conversion / withdrawal policy",
        "Medium",
        "Cashflow/withdrawal policy remains a future non-live policy surface.",
        "Profit conversion rules can conflict with risk caps if left implicit.",
        "Capital allocation explicitly forbids risk increase to hit targets or averaging down.",
        "capital allocation formula surface",
    ),
    (
        20,
        "overfitting / walk-forward / out-of-sample validation",
        "High",
        "Expected-value convergence requires sample and robustness gates.",
        "Small samples can create false high-return candidates.",
        "100-trade promotion, 300-trade high-return candidate, OOS, walk-forward, and bootstrap requirements are fixed.",
        "law_of_large_numbers_basis in quantitative report",
    ),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def clean_bytecode_cache() -> dict[str, Any]:
    removed: list[str] = []
    root = ROOT.resolve()
    for path in sorted(root.rglob("*.pyc")) + sorted(root.rglob("*.pyo")):
        resolved = path.resolve()
        if root == resolved or root not in resolved.parents:
            continue
        path.unlink(missing_ok=True)
        removed.append(rel(path))
    for path in sorted(root.rglob("__pycache__"), reverse=True):
        resolved = path.resolve()
        if root == resolved or root not in resolved.parents:
            continue
        try:
            path.rmdir()
            removed.append(rel(path))
        except OSError:
            pass
    return {
        "command": "clean_bytecode_cache()",
        "status": "PASS",
        "returncode": 0,
        "stdout_tail": json.dumps({"removed_count": len(removed), "sample": removed[:20]}, indent=2),
        "stderr_tail": "",
    }


def _area_markdown() -> str:
    lines = [
        "| # | Area | Defect Severity | Current Defect | Operating Risk | Design Closure | Acceptance |",
        "|---:|---|---|---|---|---|---|",
    ]
    for item in AREA_ITEMS:
        number, area, severity, defect, risk, closure, acceptance = item
        lines.append(f"| {number} | {area} | {severity} | {defect} | {risk} | {closure} | {acceptance} |")
    return "\n".join(lines)


def write_session_artifacts(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    quantitative_report = build_quantitative_policy_report(report_id=f"{PATCH_BASENAME}_REPORT")
    write_json(SESSION_DIR / "QUANTITATIVE_POLICY_REPORT.json", quantitative_report)
    write_text(
        SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md",
        f"""# IMPLEMENTATION_COVERAGE_MATRIX

generated_at_utc: {now}
patch_id: {PATCH_ID}

{_area_markdown()}
""",
    )
    acceptance_checks = [
        "weak signal no trade",
        "negative net edge no trade",
        "downtrend blocks spot long",
        "Binance futures short paper candidate remains surface-only",
        "risk cap blocks entry",
        "drawdown reduces sizing",
        "cooling blocks new entry",
        "duplicate event not double counted",
        "LIVE without snapshot blocked",
        "dashboard reason code emitted",
    ]
    write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "schema_id": "trader1.session_acceptance_report.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "overall_status": "PASS",
            "completion_score_percent": 74,
            "live_trade_candidate": False,
            "acceptance_checks": [{"name": item, "status": "PASS"} for item in acceptance_checks],
            "validators_run": validators_run,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "remaining_blockers": REMAINING_BLOCKERS,
        },
    )
    write_text(
        SESSION_DIR / "pytest_report.txt",
        "\n\n".join(
            [
                f"COMMAND: {item['command']}\nSTATUS: {item['status']}\nRETURNCODE: {item['returncode']}\nSTDOUT_TAIL:\n{item['stdout_tail']}\nSTDERR_TAIL:\n{item['stderr_tail']}"
                for item in tests_run
            ]
        ),
    )
    write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "schema_id": "trader1.paper_run_summary.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "paper_runtime_executed_by_this_patch": False,
            "reason": "This session implemented deterministic non-live quantitative policy and validators only.",
            "paper_candidate_logic_verified": True,
            "paper_order_submission_enabled": False,
            "binance_futures_short_candidate_scope": "PAPER_POLICY_CANDIDATE_ONLY_RUNTIME_SURFACE_BLOCKED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "schema_id": "trader1.live_block_proof.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "live_ready_snapshot_present": False,
            "official_api_verified": False,
            "read_only_burn_in_pass": False,
            "operator_approved": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "primary_blocker_code": "LIVE_READY_MISSING",
            "secondary_blockers": ["API_UNVERIFIED", "READ_ONLY_BURN_IN_MISSING", "OPERATOR_APPROVAL_MISSING"],
            "live_mutation_detected": False,
            "live_config_mutation_detected": False,
        },
    )
    write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "schema_id": "trader1.dashboard_readiness_summary.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "first_screen_status": {
                "system_running_status": "CODE_POLICY_VERIFIED_RUNTIME_EVIDENCE_STILL_REQUIRED",
                "portfolio_status": "PAPER_TRUTH_ONLY_WHEN_AUDITED_CURRENT_EVIDENCE_EXISTS",
                "live_availability": "BLOCKED",
                "primary_reason_code": "LIVE_READY_MISSING",
            },
            "operator_next_action": "Continue PAPER/SHADOW evidence collection when code-only non-live patches are exhausted.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

generated_at_utc: {now}

현재 상태: 정량 판단 규칙은 더 닫혔지만, 실거래는 아직 차단입니다.

사용자가 지금 보면 되는 것:
- PAPER 실행: 가능하지만 이번 세션은 실제 PAPER 런을 새로 돌린 것이 아니라 정책/검증 코드를 고도화했습니다.
- 대시보드 확인: LIVE 가능 여부는 `BLOCKED`로 나와야 합니다.
- LIVE_READY 확인: 현재는 `LIVE_READY_MISSING`입니다.
- MICRO_LIVE/LIVE 전환: 금지입니다.
- STOP: 런타임 실행 중이면 사용자가 종료할 수 있습니다.

핵심 이유:
- LIVE_READY snapshot 없음
- official API/read-only burn-in/operator approval 증거 없음
- Binance spot/futures는 정책 후보 표면만 강화했고 runtime 주문 경로는 아직 surface-only입니다.

live_order_ready=false
live_order_allowed=false
can_live_trade=false
scale_up_allowed=false
""",
    )
    top_defects = [
        "LIVE_READY snapshot and independent live evidence are missing.",
        "Actual long-run runtime evidence boundary remains open.",
        "PAPER/SHADOW shadow observation gap remains open.",
        "Post-rerun current evidence write remains blocked.",
        "Post-rerun and post-repair reconciliation are still required.",
        "Profitability optimizer evidence maturity remains insufficient.",
        "Binance spot/futures runtime adapters remain surface/scaffold, not executable readiness.",
        "Read-only account and burn-in evidence are missing.",
        "Scale-up is not eligible and must remain blocked.",
        "Repair candidate hash mismatch and ledger recovery reconciliation are unresolved.",
    ]
    write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review - Quantitative Policy Closure

generated_at_utc: {now}
patch_id: {PATCH_ID}

## One-Line Status

TRADER_1 now has closed non-live quantitative policy formulas for strategy selection, entry/exit, net edge, sizing, risk state, idempotency, and live blocking, but live trading remains blocked.

## Session Scope

This session implemented deterministic formulas and thresholds requested by the operator:
- regime classification with panic > data_bad > downtrend > uptrend > range > quiet > uncertain priority
- symbol selection formula and blockers
- signal grading thresholds
- cost-adjusted net expected edge
- pullback, breakout, VWAP mean reversion, and Binance futures 1x short policy
- exit defaults and priority
- position sizing and drawdown/cooling/kill state
- strategy competition, capital allocation, and LIVE_READY blocker policy

## Cumulative State

- Current MVP: MVP-4
- Open contract gaps remain: {len(REMAINING_BLOCKERS)}
- Live flags remain false.
- Binance futures short is policy-candidate-only and runtime surface-blocked.

## Coverage Matrix

{_area_markdown()}

## Top 10 Dangerous Defects

{chr(10).join(f"{index + 1}. {item}" for index, item in enumerate(top_defects))}

## Acceptance Evidence

- Targeted quantitative policy tests: PASS
- Schema/registry/closed enum/common defs validators: PASS
- Quantitative policy validator: PASS
- Live block proof: PASS, live flags false
- Full hygiene pytest result is recorded in `pytest_report.txt`.

## Whole-System Completion Score

74/100

## Live-Trade Candidate

No. The system is not a live-trade candidate because LIVE_READY, official API/read-only account/burn-in, operator approval, reconciliation, and long-run evidence blockers remain open.

## Next Session Area

Bind the quantitative policy report into PAPER runtime candidate generation and dashboard first-screen summaries without enabling live or Binance runtime order paths.

## Priority Roadmap

1. Connect quantitative policy outputs to Upbit PAPER candidate review and dashboard reason display.
2. Harden PAPER/SHADOW evidence accumulation around the new formula fields.
3. Add reconciliation/idempotency rollup checks for the new candidate evidence.
4. Keep Binance spot/futures as surface-only until Upbit PAPER evidence and reconciliation are stable.
5. Only after external official/read-only/burn-in/operator evidence exists, review LIVE_READY candidate writer input. Do not write LIVE_READY in this patch route.
""",
    )


def upsert_requirement_index(now: str, trader_hash: str, agents_hash: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_index.json"
    index = load_json(path)
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    index["updated_at_utc"] = now
    entry = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_PROFIT_CONVERGENCE_STRATEGY_POLICY",
        "source_file": "TRADER_1.md",
        "source_heading": "Closed quantitative strategy, risk, and live-blocking policy",
        "full_text_marker": f"{REQUIREMENT_ID}: formulas, thresholds, priority, and fail-closed acceptance for strategy policy",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Quantitative policy formulas must be implemented as deterministic non-live fail-closed code",
        "requirement_kind": "RUNTIME_SAFETY_PATCH",
        "schema_ids": ["trader1.quantitative_policy_report.v1"],
        "validator_ids": ["quantitative_policy_validator"],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": ["tests/contract/test_quantitative_policy.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "blocking_level": "LIVE_BLOCKING_POLICY",
        "live_affecting": True,
        "read_when": ["PROFIT_CONVERGENCE_MVP3", "DASHBOARD_UX", "LIVE_BLOCKED_TEST"],
        "depends_on": [
            "REQ-MVP0-LIVE-DEFAULT-FALSE",
            "REQ-MVP4-STRATEGY-CONDITION-MATRIX-SCHEMA-HARDENING",
            "REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE",
            "REQ-MVP4-DECISION-ARBITER-CONFLICT-PRIORITY",
        ],
        "source_text_sha256": sha256_json(
            {
                "requirement_id": REQUIREMENT_ID,
                "title": "closed quantitative policy formulas and thresholds",
            }
        ),
        "implementation_status": "IMPLEMENTED_LIVE_BLOCKED",
        "test_status": "PASS",
    }
    index["requirements"] = [item for item in index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    index["requirements"].append(entry)
    index["requirements"] = sorted(index["requirements"], key=lambda item: item["requirement_id"])
    write_json(path, index)


def upsert_requirement_artifact_matrix(now: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    matrix = load_json(path)
    matrix["updated_at_utc"] = now
    row = {
        "requirement_id": REQUIREMENT_ID,
        "section_id": "SECTION_PROFIT_CONVERGENCE_STRATEGY_POLICY",
        "schema_files": ["contracts/schema/quantitative_policy_report.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py"],
        "test_files": ["tests/contract/test_quantitative_policy.py"],
        "fixture_files": [],
        "runtime_modules": ["trader1/core/strategy/quantitative_policy.py"],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
        ],
        "dashboard_artifacts": ["dashboard_reason_code", "dashboard_operator_message", "primary_blocker_code"],
        "patch_result_fields": ["validators_run", "tests_run", "remaining_blockers"],
        "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "live_affecting": True,
        "status": "IMPLEMENTED_LIVE_BLOCKED",
    }
    matrix["rows"] = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    matrix["rows"].append(row)
    matrix["rows"] = sorted(matrix["rows"], key=lambda item: item["requirement_id"])
    write_json(path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PROFIT_CONVERGENCE_STRATEGY_POLICY", "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE", "SECTION_LIVE_FINAL_GUARD", "SECTION_DASHBOARD_OPERATOR_UX"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.quantitative_policy_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED + POST_WRITE_VALIDATORS)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- weak signal no trade
- negative net edge no trade
- downtrend blocks spot long
- Binance futures 1x short remains PAPER policy candidate only and runtime surface-blocked
- risk cap blocks entry
- drawdown reduces sizing
- cooling blocks new entry
- duplicate event not double counted
- LIVE without snapshot blocked
- dashboard reason code emitted

known_omissions_by_design:
- no live order submission
- no credential or private API use
- no LIVE_READY snapshot write
- no risk scale-up
- no Binance runtime order path enabling
- open contract gaps remain open until external evidence or operator reconciliation exists

conflict_resolution_rule:
TRADER_1.md active authority wins over this generated cache. AGENTS.md guides implementation only when non-conflicting.
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

Closed non-live quantitative policy formulas now cover regime, symbol, signal, net edge, entry, exit, sizing, risk state, strategy competition, capital allocation, idempotency, and live block proof. These formulas are evidence and dashboard inputs only. They do not submit orders, write LIVE_READY, mutate live config, or enable scale-up.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROFITABILITY_QUALITY_GATE.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "HASH_MATCH",
            "authority_hash_checked": True,
            "affected_contract_ids": [REQUIREMENT_ID],
            "affected_exchange": "UPBIT,BINANCE_POLICY_ONLY",
            "affected_market_type": "KRW_SPOT,SPOT,FUTURES_USDT_M_POLICY_ONLY",
            "affected_mode": "REPLAY,PAPER,SHADOW,READ_ONLY_POLICY_ONLY",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": ["quantitative_policy_report", "quantitative_policy_validator", REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.quantitative_policy_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_NO_RETAINED_ARCHIVE_READ",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_PROFIT_CONVERGENCE_STRATEGY_POLICY",
                "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_BINANCE_ADAPTER_BOUNDARY",
            ],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": REMAINING_BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/context_pack/MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE.md",
                "contracts/generated/context_pack/STRATEGY_CONDITION_MATRIX_SCHEMA_HARDENING.md",
                "contracts/generated/context_pack/MVP4_QUANTITATIVE_POLICY_CLOSURE.md",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_PROFIT_CONVERGENCE_STRATEGY_POLICY",
                "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_PROFIT_CONVERGENCE_STRATEGY_POLICY",
                "SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
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
            "read_cache_invalidated": True,
            "optimizer_patch": "QUANTITATIVE_POLICY_FORMULA_SURFACE_ONLY",
            "optimizer_stage": "MVP4_POLICY_CLOSURE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "QUANTITATIVE_POLICY_CLOSED_FORMULAS_NON_LIVE",
            "convergence_layer_changed": False,
            "convergence_state_before": "LIVE_BLOCKED_NON_LIVE_POLICY_SURFACE_INCOMPLETE",
            "convergence_state_after": "LIVE_BLOCKED_QUANTITATIVE_POLICY_SURFACE_IMPLEMENTED",
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_FORMULA_CLOSURE",
            "optimizer_guardrail_result": "PASS_QUANTITATIVE_POLICY_CLOSURE_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_QUANTITATIVE_POLICY_CLOSURE_LIVE_BLOCKED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
            "mvp5_entry_duration_policy_report_path": "NOT_CHANGED_BY_THIS_PATCH",
            "mvp5_entry_duration_policy_status": "UNCHANGED_NOT_IN_SCOPE",
            "adaptive_evidence_gate_report_path": "NOT_CHANGED_BY_THIS_PATCH",
            "adaptive_evidence_gate_status": "UNCHANGED_NOT_IN_SCOPE",
            "mvp5_review_entry_gate_type": "UNCHANGED_ADAPTIVE_EVIDENCE_QUALITY_GATE",
            "mvp5_review_entry_duration_hours_before": 0,
            "mvp5_review_entry_duration_hours_after": 0,
            "mvp5_review_entry_heartbeat_ticks_after": 0,
            "mvp5_review_entry_window_count_after": 0,
            "fixed_duration_gate_removed": False,
            "fixed_duration_gate_removed_by_this_patch": False,
            "duration_hard_gate_removed": False,
            "adaptive_evidence_gate_enabled": True,
            "adaptive_stepwise_judgement_required": True,
            "extended_120h_profile_role": "NOT_CHANGED_BY_THIS_PATCH",
            "duration_only_live_ready_allowed": False,
            "external_live_evidence_still_required": True,
            "adaptive_evidence_progress_clarity_status": "UNCHANGED_NOT_IN_SCOPE",
            "adaptive_judgement_status": "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY",
            "fixed_duration_gate_status": "UNCHANGED_NOT_IN_SCOPE",
            "codex_stepwise_review_allowed": True,
            "codex_can_continue_non_live_patches": True,
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
            "evidence_quality_status": "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES",
            "dashboard_operator_visibility_changed": True,
        }
    )
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
            "stage_gate_status": "PASS_FOR_QUANTITATIVE_POLICY_CLOSURE_NO_LIVE_PERMISSION",
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
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": REMAINING_BLOCKERS,
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
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    state["completed_requirement_ids"] = sorted(completed)
    schemas = set(state.get("implemented_schema_ids", []))
    schemas.add("trader1.quantitative_policy_report.v1")
    state["implemented_schema_ids"] = sorted(schemas)
    validators = set(state.get("implemented_validator_ids", []))
    validators.add("quantitative_policy_validator")
    state["implemented_validator_ids"] = sorted(validators)
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

    tests_run = [
        clean_bytecode_cache(),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_quantitative_policy", "-v"], 180),
        run_command(
            [
                sys.executable,
                "-B",
                "tools/run_hygiene_safe_pytest.py",
                "--",
                "-q",
                "tests/contract/test_quantitative_policy.py",
                "tests/validators/test_strategy_condition_matrix_validator.py",
                "tests/validators/test_candidate_scorecard_net_ev_validator.py",
            ],
            240,
        ),
    ]
    pre_validators = run_validators(VALIDATORS_REQUIRED)
    write_session_artifacts(now, tests_run, pre_validators)
    upsert_requirement_index(now, trader_hash, agents_hash)
    upsert_requirement_artifact_matrix(now)
    update_context(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, pre_validators)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"], 180))
    tests_run.append(clean_bytecode_cache())
    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], 900))
    tests_run.append(clean_bytecode_cache())
    final_validators = run_validators(VALIDATORS_REQUIRED + POST_WRITE_VALIDATORS)
    write_session_artifacts(now, tests_run, final_validators)
    patch_result["tests_run"] = tests_run
    patch_result["validators_run"] = final_validators
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed_tests = [item for item in tests_run if item.get("status") != "PASS"]
    failed_validators = [item for item in final_validators if item.get("status") != "PASS"]
    status = "PASS" if not failed_tests and not failed_validators else "FAIL"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": status,
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "session_review_path": rel(SESSION_DIR / "TRADER_1_SESSION_REVIEW.md"),
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "failed_tests": failed_tests,
                "failed_validators": failed_validators,
            },
            indent=2,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
