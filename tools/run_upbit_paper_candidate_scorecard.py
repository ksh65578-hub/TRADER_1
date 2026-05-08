from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.research.profitability.candidate_scorecard import (
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    performance_inputs_from_runtime_sample_history,
    write_upbit_paper_candidate_scorecard,
)
from trader1.research.profitability.convergence_memory import write_upbit_paper_convergence_memory_artifacts
from trader1.research.profitability.overfit_diagnostic import (
    overfit_diagnostic_from_upbit_paper_runtime,
    robustness_inputs_from_overfit_diagnostic,
    write_overfit_diagnostic_report,
)
from trader1.research.shadow.shadow_runner import validate_paper_shadow_evidence_accumulation_report
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history_sources,
    write_upbit_paper_runtime_sample_history,
)
from trader1.validation.mvp0_validators import _candidate_scorecard_net_ev_errors, _overfit_diagnostic_errors


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _paper_runtime_base(root: Path, session_id: str) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _paper_shadow_evidence_accumulation_path(root: Path, session_id: str) -> Path:
    return _paper_runtime_base(root, session_id) / "paper_shadow_evidence_accumulation_report.json"


def _blocked_result(message: str, blocker_code: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "message": message,
        "blocker_code": blocker_code,
        **extra,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _paper_shadow_identity_matches(scorecard: dict[str, Any], evidence: dict[str, Any]) -> bool:
    for field in ("candidate_id", "strategy_id", "strategy_build_id", "parameter_hash", "exchange", "market_type"):
        if str(scorecard.get(field) or "") != str(evidence.get(field) or ""):
            return False
    return True


def _paper_shadow_scorecard_binding(
    *,
    root: Path,
    session_id: str,
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    path = _paper_shadow_evidence_accumulation_path(root, session_id)
    if not path.exists():
        return {
            "status": "MISSING",
            "blocker_code": "MEASUREMENT_MISSING",
            "path": None,
            "extra_source_modes": [],
            "extra_source_artifact_ids": [],
            "profit_cycle_dependency_statuses": {},
            "message": "PAPER/SHADOW scorecard-input evidence is not present yet.",
        }

    evidence = _load_json(path)
    result = validate_paper_shadow_evidence_accumulation_report(evidence)
    if result.status != "PASS":
        return {
            "status": result.status,
            "blocker_code": result.blocker_code or "MEASUREMENT_MISSING",
            "path": _relative_path(path, root),
            "extra_source_modes": [],
            "extra_source_artifact_ids": [],
            "profit_cycle_dependency_statuses": {},
            "message": result.message,
        }
    if not _paper_shadow_identity_matches(scorecard, evidence):
        return {
            "status": "BLOCKED",
            "blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "path": _relative_path(path, root),
            "extra_source_modes": [],
            "extra_source_artifact_ids": [],
            "profit_cycle_dependency_statuses": {},
            "message": "PAPER/SHADOW evidence identity does not match the current candidate scorecard.",
        }

    evidence_hash = str(evidence.get("evidence_hash") or "")
    source_ids = [str(item) for item in evidence.get("source_evidence_ids") or []]
    source_ids.extend(str(item) for item in evidence.get("supporting_source_evidence_ids") or [])
    source_ids.append(f"paper_shadow_evidence_accumulation:{evidence.get('evidence_report_id')}:{evidence_hash}")
    return {
        "status": "PASS",
        "blocker_code": None,
        "path": _relative_path(path, root),
        "extra_source_modes": ["SHADOW"],
        "extra_source_artifact_ids": sorted(set(source_ids)),
        "profit_cycle_dependency_statuses": {
            "paper_shadow_evidence_accumulation_validator_status": "PASS",
        },
        "paper_sample_count": evidence.get("paper_sample_count"),
        "shadow_sample_count": evidence.get("shadow_sample_count"),
        "evidence_window_count": evidence.get("evidence_window_count"),
        "long_run_evidence_eligible": evidence.get("long_run_evidence_eligible"),
        "message": "PAPER/SHADOW scorecard-input evidence is validated and bound to convergence memory.",
    }


def build_current_upbit_paper_candidate_scorecard(*, root: Path, session_id: str) -> dict[str, Any]:
    root = Path(root).resolve()
    history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
    history_result = validate_upbit_paper_runtime_sample_history_sources(root=root, history=history)
    if history_result.status != "PASS":
        history_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
        return _blocked_result(
            history_result.message,
            history_result.blocker_code or "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
            runtime_sample_history_path=_relative_path(history_path, root),
            runtime_sample_history_status=history_result.status,
            runtime_sample_status=history.get("runtime_sample_status"),
            accepted_cycle_sample_count=history.get("accepted_cycle_sample_count"),
            invalid_source_count=history.get("invalid_source_count"),
        )
    if not history.get("samples"):
        return _blocked_result(
            "no PAPER runtime samples are available for candidate scorecard input",
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
        )

    latest_sample = history["samples"][-1]
    runtime_path = root / latest_sample["source_runtime_cycle_path"]
    runtime = _load_json(runtime_path)
    runtime_result = validate_upbit_paper_runtime_cycle_report(runtime)
    if runtime_result.status != "PASS":
        return _blocked_result(
            runtime_result.message,
            runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
            source_runtime_cycle_path=str(latest_sample.get("source_runtime_cycle_path")),
        )
    if runtime.get("cycle_hash") != latest_sample.get("source_runtime_cycle_hash"):
        return _blocked_result(
            "latest PAPER runtime sample hash does not match the runtime cycle artifact",
            "RECONCILIATION_REQUIRED",
            source_runtime_cycle_path=str(latest_sample.get("source_runtime_cycle_path")),
        )

    base_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
    diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
    )
    diagnostic_errors = _overfit_diagnostic_errors(diagnostic)
    if diagnostic_errors:
        return _blocked_result(
            "overfit diagnostic failed contract validation",
            "SCHEMA_IDENTITY_MISMATCH",
            diagnostic_errors=diagnostic_errors,
        )

    robustness_statuses, robustness_source_ids = robustness_inputs_from_overfit_diagnostic(diagnostic)
    performance_statuses, performance_metrics, performance_source_ids = performance_inputs_from_runtime_sample_history(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
    )
    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime,
        robustness_statuses=robustness_statuses,
        robustness_source_evidence_ids=robustness_source_ids,
        performance_statuses=performance_statuses,
        performance_metrics=performance_metrics,
        performance_source_evidence_ids=performance_source_ids,
    )
    scorecard_errors = _candidate_scorecard_net_ev_errors(scorecard)
    if scorecard_errors:
        return _blocked_result(
            "candidate scorecard failed contract validation",
            "SCORECARD_SCHEMA_INVALID",
            scorecard_errors=scorecard_errors,
        )

    paper_shadow_binding = _paper_shadow_scorecard_binding(
        root=root,
        session_id=session_id,
        scorecard=scorecard,
    )
    history_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
    diagnostic_path = write_overfit_diagnostic_report(root=root, report=diagnostic)
    scorecard_path = write_upbit_paper_candidate_scorecard(root=root, scorecard=scorecard)
    convergence_memory = write_upbit_paper_convergence_memory_artifacts(
        root=root,
        scorecard=scorecard,
        extra_source_modes=paper_shadow_binding["extra_source_modes"],
        extra_source_artifact_ids=paper_shadow_binding["extra_source_artifact_ids"],
        profit_cycle_dependency_statuses=paper_shadow_binding["profit_cycle_dependency_statuses"],
    )
    return {
        "status": "PASS",
        "message": "Upbit PAPER candidate scorecard, non-live convergence memory, and profit convergence cycle report were written from ledger-bound runtime samples and overfit diagnostics",
        "session_id": session_id,
        "runtime_sample_history_path": _relative_path(history_path, root),
        "overfit_diagnostic_path": _relative_path(diagnostic_path, root),
        "candidate_scorecard_path": _relative_path(scorecard_path, root),
        "strategy_performance_memory_path": _relative_path(convergence_memory["strategy_performance_memory_path"], root),
        "convergence_objective_profile_path": _relative_path(
            convergence_memory["convergence_objective_profile_path"],
            root,
        ),
        "exploration_exploitation_policy_path": _relative_path(
            convergence_memory["exploration_exploitation_policy_path"],
            root,
        ),
        "optimizer_memory_state_path": _relative_path(convergence_memory["optimizer_memory_state_path"], root),
        "failure_analysis_path": (
            _relative_path(convergence_memory["failure_analysis_path"], root)
            if convergence_memory["failure_analysis_path"] is not None
            else None
        ),
        "profit_convergence_cycle_report_path": _relative_path(
            convergence_memory["profit_convergence_cycle_report_path"],
            root,
        ),
        "source_runtime_cycle_path": str(latest_sample["source_runtime_cycle_path"]),
        "source_runtime_cycle_hash": runtime["cycle_hash"],
        "scorecard_id": scorecard["scorecard_id"],
        "candidate_id": scorecard["candidate_id"],
        "scorecard_scope": scorecard["scorecard_scope"],
        "ranking_eligible": scorecard["ranking_eligible"],
        "scorecard_blocker_codes": [blocker["code"] for blocker in scorecard["blockers"]],
        "diagnostic_status": diagnostic["diagnostic_status"],
        "robustness_eligible": diagnostic["robustness_eligible"],
        "sample_count": diagnostic["sample_count"],
        "min_required_sample_count": diagnostic["min_required_sample_count"],
        "overfit_blocker_codes": [blocker["code"] for blocker in diagnostic["blockers"]],
        "performance_closed_trade_sample_count": scorecard["closed_trade_sample_count"],
        "performance_profit_factor": scorecard["profit_factor"],
        "performance_max_drawdown_pct": scorecard["max_drawdown_pct"],
        "performance_realized_vs_expected_edge_bps": scorecard["realized_vs_expected_edge_bps"],
        "performance_fill_quality_score": scorecard["fill_quality_score"],
        "performance_execution_cost_comparison_status": scorecard["execution_cost_comparison_status"],
        "performance_execution_cost_delta_bps": scorecard["execution_cost_delta_bps"],
        "performance_max_allowed_execution_cost_delta_bps": scorecard["max_allowed_execution_cost_delta_bps"],
        "paper_shadow_scorecard_binding_status": paper_shadow_binding["status"],
        "paper_shadow_scorecard_binding_blocker_code": paper_shadow_binding["blocker_code"],
        "paper_shadow_scorecard_binding_path": paper_shadow_binding["path"],
        "paper_shadow_scorecard_binding_message": paper_shadow_binding["message"],
        "paper_shadow_scorecard_binding_paper_sample_count": paper_shadow_binding.get("paper_sample_count"),
        "paper_shadow_scorecard_binding_shadow_sample_count": paper_shadow_binding.get("shadow_sample_count"),
        "paper_shadow_scorecard_binding_evidence_window_count": paper_shadow_binding.get("evidence_window_count"),
        "paper_shadow_scorecard_binding_long_run_evidence_eligible": paper_shadow_binding.get("long_run_evidence_eligible"),
        "strategy_performance_memory_status": convergence_memory["strategy_performance_memory"]["performance_status"],
        "strategy_performance_memory_scope": convergence_memory["strategy_performance_memory"]["performance_scope"],
        "convergence_objective_profile_status": convergence_memory["convergence_objective_profile"]["objective_status"],
        "exploration_exploitation_policy_status": convergence_memory["exploration_exploitation_policy"]["policy_status"],
        "exploration_exploitation_transition_decision": convergence_memory["exploration_exploitation_policy"]["transition_decision"],
        "exploration_exploitation_policy_blocker_codes": [
            blocker["code"] for blocker in convergence_memory["exploration_exploitation_policy"]["blockers"]
        ],
        "optimizer_memory_sequence_number": convergence_memory["optimizer_memory_state"]["memory_sequence_number"],
        "failure_analysis_status": (
            convergence_memory["failure_analysis"]["failure_status"]
            if convergence_memory["failure_analysis"] is not None
            else "NOT_REQUIRED"
        ),
        "profit_convergence_cycle_status": convergence_memory["profit_convergence_cycle_report"]["cycle_status"],
        "profit_convergence_cycle_claim": convergence_memory["profit_convergence_cycle_report"]["convergence_claim"],
        "profit_convergence_cycle_blocker_codes": [
            blocker["code"] for blocker in convergence_memory["profit_convergence_cycle_report"]["blockers"]
        ],
        "invalid_runtime_source_count": history["invalid_source_count"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the non-live Upbit PAPER candidate scorecard from current runtime samples and overfit diagnostics."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_current_upbit_paper_candidate_scorecard(root=args.root, session_id=args.session_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
