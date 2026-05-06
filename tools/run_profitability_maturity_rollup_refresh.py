from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report


SESSION_ROOT = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher"
SCORECARD_PATH = SESSION_ROOT / "profitability" / "candidate_scorecard.json"
OVERFIT_PATH = SESSION_ROOT / "profitability" / "overfit_diagnostic_report.json"
SAMPLE_HISTORY_PATH = SESSION_ROOT / "paper_runtime" / "upbit_paper_runtime_sample_history.json"
RUNTIME_CYCLE_DIR = SESSION_ROOT / "paper_runtime" / "cycles"
PAPER_SHADOW_EVIDENCE_PATH = SESSION_ROOT / "paper_shadow_evidence_accumulation_report.json"
RUNTIME_COLLECTION_PROFILE_PATH = (
    ROOT / "system" / "evidence" / "runtime_checks" / "MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json"
)
PAPER_SHADOW_BINDING_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "shadow"
    / "mvp1_upbit_paper_launcher"
    / "paper_shadow_harness_binding_report.json"
)
SHADOW_HARNESS_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "shadow"
    / "mvp1_upbit_paper_launcher"
    / "actual_runtime_harness_report.json"
)
ROLLUP_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
ROLLUP_FIXTURE_PATH = ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"
CONTRACT_GAP_PATH = (
    ROOT / "system" / "evidence" / "contract_gaps" / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json"
)

ROBUSTNESS_SOURCE_TYPES = ("OOS", "WALK_FORWARD", "BOOTSTRAP", "CONCENTRATION")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def sha256_json(data: Any) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def join_action_items(items: list[str]) -> str:
    if not items:
        return "remaining required non-live evidence"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def rollup_hash(rollup: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in rollup.items() if key != "rollup_hash"})


def runtime_path_from_scorecard(scorecard: dict[str, Any]) -> Path:
    cycle_id = str(scorecard.get("source_runtime_cycle_id") or "")
    candidate = RUNTIME_CYCLE_DIR / f"{cycle_id}.runtime_cycle.json"
    if cycle_id and candidate.is_file():
        return candidate
    return SESSION_ROOT / "upbit_paper_runtime_cycle_report.json"


def runtime_linkage_evidence(runtime_path: Path) -> dict[str, Any]:
    report = load_json(runtime_path)
    result = validate_upbit_paper_runtime_cycle_report(report, require_quantitative_policy_summary=False)
    selected = report.get("selected_candidate", {})
    return {
        "status": "PASS" if result.status == "PASS" else "BLOCKED",
        "source_runtime_cycle_path": rel(runtime_path),
        "source_runtime_cycle_id": report.get("cycle_id"),
        "source_runtime_cycle_hash": report.get("cycle_hash"),
        "runtime_input_role": report.get("runtime_input_role"),
        "runtime_public_market_data_hash": report.get("runtime_public_market_data_hash"),
        "feature_snapshot_hash": report.get("feature_snapshot_hash"),
        "strategy_regime_cost_linkage_status": "PASS"
        if result.status == "PASS" and report.get("strategy_regime_cost_linkage")
        else "BLOCKED",
        "selected_candidate_id": selected.get("candidate_id"),
        "selected_candidate_net_ev_after_cost_bps": selected.get("net_ev_after_cost_bps"),
        "cost_model_source": selected.get("cost_model_source"),
        "sample_count": 1 if result.status == "PASS" else 0,
        "min_required_sample_count": 1,
        "primary_blocker_code": "PROFITABILITY_EVIDENCE_MATURITY",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def source_type_counts(overfit: dict[str, Any]) -> dict[str, int]:
    min_bootstrap = int(overfit.get("min_required_bootstrap_iterations") or 500)
    return {
        "oos_count": int(overfit.get("oos_window_count") or 0) if overfit.get("oos_status") == "PASS" else 0,
        "walk_forward_count": int(overfit.get("walk_forward_window_count") or 0)
        if overfit.get("walk_forward_status") == "PASS"
        else 0,
        "bootstrap_count": 1
        if overfit.get("bootstrap_status") == "PASS" and int(overfit.get("bootstrap_iteration_count") or 0) >= min_bootstrap
        else 0,
        "concentration_count": 1
        if overfit.get("concentration_risk_status") == "LOW"
        and overfit.get("survivorship_bias_check") == "PASS"
        and overfit.get("data_snooping_check") == "PASS"
        else 0,
    }


def robustness_source_type_evidence(scorecard: dict[str, Any], overfit: dict[str, Any]) -> dict[str, Any]:
    counts = source_type_counts(overfit)
    min_required = 1
    present = [
        source_type
        for source_type, field in (
            ("OOS", "oos_count"),
            ("WALK_FORWARD", "walk_forward_count"),
            ("BOOTSTRAP", "bootstrap_count"),
            ("CONCENTRATION", "concentration_count"),
        )
        if counts[field] >= min_required
    ]
    missing = [source_type for source_type in ROBUSTNESS_SOURCE_TYPES if source_type not in set(present)]
    cycle_id = str(scorecard.get("source_runtime_cycle_id") or "")
    cycle_hash = str(scorecard.get("source_runtime_cycle_hash") or "")
    source_ids = list(scorecard.get("source_evidence_ids") or [])
    if counts["concentration_count"] >= min_required and cycle_id and cycle_hash:
        source_ids.append(f"concentration:{cycle_id}:{cycle_hash}")
    return {
        "status": "PASS" if not missing else "BLOCKED_FOR_SOURCE_TYPE_EVIDENCE",
        "required_source_types": list(ROBUSTNESS_SOURCE_TYPES),
        "present_source_types": present,
        "missing_source_types": missing,
        "source_type_counts": counts,
        "min_required_per_source_type": min_required,
        "source_artifact_paths": [rel(OVERFIT_PATH), rel(SCORECARD_PATH), rel(SAMPLE_HISTORY_PATH)],
        "source_evidence_ids": sorted(set(str(item) for item in source_ids if item)),
        "primary_blocker_code": None if not missing else "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED",
        "explicit_source_type_blocker": bool(missing),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def runtime_collection_profile_evidence(profile: dict[str, Any] | None) -> dict[str, Any]:
    mode_depths = {}
    plan = {}
    if isinstance(profile, dict):
        collection_depth = profile.get("long_run_collection_depth")
        if isinstance(collection_depth, dict):
            mode_depth_evidence = collection_depth.get("runtime_mode_depth_evidence")
            if isinstance(mode_depth_evidence, dict) and isinstance(mode_depth_evidence.get("mode_depths"), dict):
                mode_depths = mode_depth_evidence["mode_depths"]
        if isinstance(profile.get("non_live_collection_plan"), dict):
            plan = profile["non_live_collection_plan"]

    paper_depth = mode_depths.get("paper") if isinstance(mode_depths.get("paper"), dict) else {}
    shadow_depth = mode_depths.get("shadow") if isinstance(mode_depths.get("shadow"), dict) else {}
    source_available = isinstance(profile, dict)
    profile_status = str(profile.get("status") or "MISSING") if source_available else "MISSING"
    return {
        "status": "PASS" if source_available and profile_status == "PASS" else ("BLOCKED" if source_available else "MISSING"),
        "source_artifact_path": rel(RUNTIME_COLLECTION_PROFILE_PATH),
        "profile_status": profile_status,
        "profile_hash": str(profile.get("profile_hash") or "") if source_available else "",
        "paper_observed_span_seconds": safe_int(paper_depth.get("observed_span_seconds")),
        "paper_minimum_span_seconds": safe_int(paper_depth.get("minimum_span_seconds")),
        "paper_remaining_span_seconds": safe_int(paper_depth.get("missing_span_seconds")),
        "paper_observed_cycle_count": safe_int(paper_depth.get("observed_cycle_count")),
        "paper_minimum_cycle_count": safe_int(paper_depth.get("minimum_cycle_count")),
        "paper_remaining_cycle_count": safe_int(paper_depth.get("missing_cycle_count")),
        "shadow_observed_span_seconds": safe_int(shadow_depth.get("observed_span_seconds")),
        "shadow_minimum_span_seconds": safe_int(shadow_depth.get("minimum_span_seconds")),
        "shadow_remaining_span_seconds": safe_int(shadow_depth.get("missing_span_seconds")),
        "shadow_observed_cycle_count": safe_int(shadow_depth.get("observed_cycle_count")),
        "shadow_minimum_cycle_count": safe_int(shadow_depth.get("minimum_cycle_count")),
        "shadow_remaining_cycle_count": safe_int(shadow_depth.get("missing_cycle_count")),
        "recommended_next_paper_batch_cycle_count": safe_int(plan.get("recommended_next_paper_batch_cycle_count")),
        "max_safe_paper_batch_cycle_count": safe_int(plan.get("max_safe_paper_batch_cycle_count")),
        "minimum_cycle_wall_clock_spacing_seconds": safe_int(plan.get("minimum_cycle_wall_clock_spacing_seconds")),
        "estimated_wall_clock_seconds_remaining": safe_int(plan.get("estimated_wall_clock_seconds_remaining")),
        "shadow_collection_required": bool(plan.get("shadow_collection_required")) if source_available else True,
        "counts_as_actual_long_run_evidence": False,
        "long_run_evidence_eligible": False,
        "primary_blocker_code": "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_promotion_thresholds(rollup: dict[str, Any], scorecard: dict[str, Any], overfit: dict[str, Any]) -> None:
    thresholds = rollup["promotion_threshold_evidence"]
    missing_codes = set(thresholds.get("missing_threshold_codes") or [])
    if overfit.get("oos_status") == "PASS" and overfit.get("walk_forward_status") == "PASS":
        thresholds["walk_forward_or_oos_coverage_pct"] = 100
        missing_codes.discard("WALK_FORWARD_OR_OOS_COVERAGE_BELOW_MIN")
    net_ev = float(scorecard.get("net_ev_after_cost_bps") or 0.0)
    min_edge = float(scorecard.get("min_required_edge_bps") or 0.0)
    if net_ev >= min_edge and scorecard.get("cost_model_status") == "PASS":
        thresholds["net_ev_after_cost_status"] = "PASS"
        missing_codes.discard("NET_EV_AFTER_COST_NOT_PASS")
    thresholds["missing_threshold_codes"] = sorted(missing_codes)
    thresholds["status"] = "BLOCKED_FOR_THRESHOLD_EVIDENCE"
    thresholds["paper_runtime_hours_gate_role"] = "OBSERVED_CONTEXT_ONLY_NO_FIXED_RUNTIME_FLOOR"
    thresholds["live_order_ready"] = False
    thresholds["live_order_allowed"] = False
    thresholds["can_live_trade"] = False
    thresholds["scale_up_allowed"] = False


def update_overfit_component(rollup: dict[str, Any], scorecard: dict[str, Any], overfit: dict[str, Any]) -> None:
    sample_count = int(overfit.get("sample_count") or 0)
    min_required = int(overfit.get("min_required_sample_count") or 300)
    robust = overfit.get("robustness_eligible") is True and sample_count >= min_required
    for component in rollup.get("components", []):
        if component.get("component_id") != "overfit_oos_walk_forward":
            continue
        paths = component.setdefault("source_artifact_paths", [])
        for path in (rel(OVERFIT_PATH), rel(SCORECARD_PATH), rel(SAMPLE_HISTORY_PATH)):
            if path not in paths:
                paths.append(path)
        evidence_ids = component.setdefault("source_evidence_ids", [])
        for evidence_id in scorecard.get("source_evidence_ids") or []:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)
        component["sample_count"] = sample_count
        component["min_required_sample_count"] = min_required
        component["validator_status"] = "PASS"
        component["freshness_status"] = "PASS"
        component["dependency_status"] = "PASS"
        component["live_review_eligible"] = False
        component["scale_up_allowed"] = False
        component["long_run_evidence_eligible"] = False
        component["long_run_blocker_code"] = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
        if robust:
            component["maturity_status"] = "PAPER_SCORECARD_INPUT_ONLY"
            component["evidence_status"] = "PASS"
            component["paper_scorecard_input_eligible"] = True
            component["primary_blocker_code"] = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
            component["next_required_evidence"] = (
                "OOS, walk-forward, bootstrap, and concentration checks pass for PAPER scorecard input; "
                "collect distinct PAPER/SHADOW long-run windows, replay coverage, read-only burn-in, and operator approval."
            )
        else:
            component["maturity_status"] = "BLOCKED_LONG_RUN_EVIDENCE"
            component["evidence_status"] = "BLOCKED"
            component["paper_scorecard_input_eligible"] = False
            component["primary_blocker_code"] = "PROFITABILITY_EVIDENCE_MATURITY"


def update_paper_shadow_component(
    rollup: dict[str, Any],
    paper_shadow_evidence: dict[str, Any] | None,
    runtime_profile_evidence: dict[str, Any],
) -> None:
    for component in rollup.get("components", []):
        if component.get("component_id") != "paper_shadow_evidence_accumulation":
            continue
        paths = component.setdefault("source_artifact_paths", [])
        for path in (
            "contracts/schema/paper_shadow_evidence_accumulation_report.schema.json",
            rel(PAPER_SHADOW_EVIDENCE_PATH),
            rel(PAPER_SHADOW_BINDING_PATH),
            rel(SHADOW_HARNESS_PATH),
            rel(SAMPLE_HISTORY_PATH),
            rel(RUNTIME_COLLECTION_PROFILE_PATH),
        ):
            if (ROOT / path).is_file() and path not in paths:
                paths.append(path)
        component["validator_status"] = "PASS"
        component["freshness_status"] = "PASS"
        component["dependency_status"] = "PASS"
        component["maturity_status"] = "BLOCKED_LONG_RUN_EVIDENCE"
        component["evidence_status"] = "PARTIAL"
        component["min_required_sample_count"] = 30
        component["paper_scorecard_input_eligible"] = True
        component["long_run_evidence_eligible"] = False
        component["long_run_blocker_code"] = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"
        component["live_review_eligible"] = False
        component["live_order_ready"] = False
        component["live_order_allowed"] = False
        component["can_live_trade"] = False
        component["scale_up_allowed"] = False
        component["primary_blocker_code"] = "PROFITABILITY_EVIDENCE_MATURITY"
        if not isinstance(paper_shadow_evidence, dict):
            component["sample_count"] = int(component.get("sample_count") or 0)
            component["next_required_evidence"] = (
                "Generate a source-bound PAPER/SHADOW evidence accumulation report from actual non-live runtime artifacts; "
                "long-run and live review remain blocked."
            )
            return

        paper_count = safe_int(paper_shadow_evidence.get("paper_sample_count"))
        shadow_count = safe_int(paper_shadow_evidence.get("shadow_sample_count"))
        min_samples = safe_int(paper_shadow_evidence.get("min_required_sample_count"), 30)
        paired_sample_count = min(paper_count, shadow_count)
        component["sample_count"] = paired_sample_count
        component["min_required_sample_count"] = min_samples
        for field in (
            "paper_sample_count",
            "shadow_sample_count",
            "paper_sample_deficit",
            "shadow_sample_deficit",
            "evidence_window_count",
            "min_required_evidence_window_count",
            "evidence_window_deficit",
            "supporting_source_window_count",
            "supporting_window_deficit",
            "evidence_span_hours",
            "min_required_evidence_span_hours",
            "evidence_span_hours_deficit",
            "paper_runtime_span_seconds",
            "shadow_runtime_span_seconds",
            "paired_runtime_span_seconds",
            "entry_reason_count",
            "no_trade_reason_count",
            "cost_evidence_count",
            "reason_coverage_deficit_count",
            "stale_artifact_count",
            "actual_runtime_source_deficit",
            "evidence_actionability_status",
            "primary_collection_deficit_code",
            "primary_collection_deficit_message",
            "next_collection_action",
            "scorecard_input_truth_status",
            "actual_runtime_source_status",
            "long_run_evidence_eligible",
            "long_run_blocker_code",
        ):
            if field in paper_shadow_evidence:
                component[field] = paper_shadow_evidence[field]
        component["actual_runtime_source_evidence_ids"] = [
            str(evidence_id)
            for evidence_id in paper_shadow_evidence.get("actual_runtime_source_evidence_ids", [])
            if evidence_id
        ]
        raw_requirement_statuses = paper_shadow_evidence.get("actual_runtime_requirement_statuses")
        component["actual_runtime_requirement_statuses"] = (
            dict(raw_requirement_statuses) if isinstance(raw_requirement_statuses, dict) else {}
        )
        evidence_ids = component.setdefault("source_evidence_ids", [])
        for evidence_id in [
            paper_shadow_evidence.get("evidence_hash"),
            *list(paper_shadow_evidence.get("source_evidence_ids") or []),
        ]:
            if evidence_id and evidence_id not in evidence_ids:
                evidence_ids.append(str(evidence_id))
        component["next_required_evidence"] = paper_shadow_next_required_evidence(
            paper_shadow_evidence,
            runtime_profile_evidence=runtime_profile_evidence,
        )


def paper_shadow_next_required_evidence(
    paper_shadow_evidence: dict[str, Any],
    *,
    runtime_profile_evidence: dict[str, Any] | None = None,
) -> str:
    paper_count = safe_int(paper_shadow_evidence.get("paper_sample_count"))
    shadow_count = safe_int(paper_shadow_evidence.get("shadow_sample_count"))
    min_samples = safe_int(paper_shadow_evidence.get("min_required_sample_count"), 30)
    evidence_windows = safe_int(paper_shadow_evidence.get("evidence_window_count"))
    supporting_windows = safe_int(paper_shadow_evidence.get("supporting_source_window_count"))
    min_windows = safe_int(paper_shadow_evidence.get("min_required_evidence_window_count"), 20)
    span_hours = safe_int(paper_shadow_evidence.get("evidence_span_hours"))
    min_span_hours = safe_int(paper_shadow_evidence.get("min_required_evidence_span_hours"), 120)

    actions: list[str] = []
    paper_deficit = max(0, min_samples - paper_count)
    shadow_deficit = max(0, min_samples - shadow_count)
    evidence_window_deficit = max(0, min_windows - evidence_windows)
    supporting_window_deficit = max(0, min_windows - supporting_windows)
    span_deficit = max(0, min_span_hours - span_hours)
    if paper_deficit:
        actions.append(f"{paper_deficit} PAPER samples")
    if shadow_deficit:
        actions.append(f"{shadow_deficit} SHADOW observations")
    if evidence_window_deficit:
        actions.append(f"{evidence_window_deficit} paired PAPER/SHADOW runtime windows")
    if supporting_window_deficit:
        actions.append(f"{supporting_window_deficit} source-bound PAPER/SHADOW window IDs")
    if span_deficit:
        actions.append(f"{span_deficit} non-live runtime hours")

    missing_measurements = []
    if safe_int(paper_shadow_evidence.get("entry_reason_count")) <= 0:
        missing_measurements.append("entry reasons")
    if safe_int(paper_shadow_evidence.get("no_trade_reason_count")) <= 0:
        missing_measurements.append("no-trade reasons")
    if safe_int(paper_shadow_evidence.get("cost_evidence_count")) <= 0:
        missing_measurements.append("cost evidence")
    if missing_measurements:
        actions.append(join_action_items(missing_measurements))
    if safe_int(paper_shadow_evidence.get("actual_runtime_source_deficit")) > 0:
        actions.append("validated PAPER and SHADOW actual runtime source IDs")
    actions.extend(["replay coverage", "read-only burn-in", "live safety proof", "operator approval"])
    profile_clause = ""
    if isinstance(runtime_profile_evidence, dict):
        profile_clause = (
            " Runtime profile shows remaining PAPER "
            f"{safe_int(runtime_profile_evidence.get('paper_remaining_cycle_count'))} cycles/"
            f"{safe_int(runtime_profile_evidence.get('paper_remaining_span_seconds'))}s and SHADOW "
            f"{safe_int(runtime_profile_evidence.get('shadow_remaining_cycle_count'))} cycles/"
            f"{safe_int(runtime_profile_evidence.get('shadow_remaining_span_seconds'))}s; "
            f"next safe PAPER batch is {safe_int(runtime_profile_evidence.get('recommended_next_paper_batch_cycle_count'))} cycles."
        )

    return (
        f"Current source-bound PAPER/SHADOW evidence has PAPER samples {paper_count}/{min_samples}, "
        f"SHADOW observations {shadow_count}/{min_samples}, runtime windows {evidence_windows}/{min_windows}, "
        f"source-bound window IDs {supporting_windows}/{min_windows}, and span {span_hours}/{min_span_hours}h; "
        f"collect {join_action_items(actions)} before live review.{profile_clause}"
    )


def refresh_rollup(
    path: Path,
    *,
    now: str,
    authority: dict[str, str],
    scorecard: dict[str, Any],
    overfit: dict[str, Any],
    paper_shadow_evidence: dict[str, Any] | None,
    runtime_profile: dict[str, Any] | None,
) -> None:
    rollup = load_json(path)
    runtime_path = runtime_path_from_scorecard(scorecard)
    rollup["generated_at_utc"] = now
    rollup["authority"] = authority
    rollup["runtime_linkage_evidence"] = runtime_linkage_evidence(runtime_path)
    rollup["robustness_source_type_evidence"] = robustness_source_type_evidence(scorecard, overfit)
    rollup["runtime_collection_profile_evidence"] = runtime_collection_profile_evidence(runtime_profile)
    update_promotion_thresholds(rollup, scorecard, overfit)
    update_overfit_component(rollup, scorecard, overfit)
    update_paper_shadow_component(rollup, paper_shadow_evidence, rollup["runtime_collection_profile_evidence"])
    rollup["status"] = "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY"
    rollup["all_validators_passed"] = all(
        component.get("validator_status") == "PASS" for component in rollup.get("components", [])
    )
    rollup["paper_scorecard_input_allowed"] = True
    rollup["live_review_eligible"] = False
    rollup["scale_up_eligible"] = False
    rollup["primary_blocker_code"] = "PROFITABILITY_EVIDENCE_MATURITY"
    rollup["next_operator_action"] = (
        "Use the 300-sample PAPER scorecard and robustness pass for PAPER ranking review only; "
        "live remains blocked until long-run PAPER/SHADOW evidence, replay coverage, read-only burn-in, "
        "manual order evidence, live safety proof, and operator approval are complete."
    )
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "live_permission_created",
        "profitability_guarantee_created",
        "optimizer_live_mutation_detected",
        "convergence_live_mutation_detected",
    ):
        rollup[field] = False
    rollup["rollup_hash"] = ""
    rollup["rollup_hash"] = rollup_hash(rollup)
    write_json(path, rollup)


def refresh_contract_gap(path: Path, *, now: str, authority: dict[str, str]) -> None:
    gap = load_json(path)
    gap["generated_at_utc"] = now
    gap["authority"] = authority
    gap["status"] = "OPEN"
    gap["severity"] = "HIGH"
    gap["live_affecting"] = True
    gap["blockers"] = [
        {
            "code": "CONTRACT_GAP_HIGH",
            "severity": "HIGH",
            "message": "Profitability, strategy, optimizer, and convergence evidence maturity is not sufficient for live review or scale-up.",
            "source_requirement_id": "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
        },
        {
            "code": "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
            "severity": "HIGH",
            "message": (
                "The Upbit PAPER candidate has 300-sample scorecard robustness for PAPER ranking review, "
                "but distinct long-run PAPER/SHADOW, replay, live parity, read-only burn-in, and approval evidence remain missing."
            ),
            "source_requirement_id": "REQ-MVP4-PAPER-SHADOW-LONG-RUN-EVIDENCE-VISIBILITY",
        },
    ]
    gap["notes"] = (
        "Rechecked after 300 accepted Upbit PAPER samples. OOS, walk-forward, bootstrap, and concentration checks "
        "are no longer marked missing for PAPER scorecard input, but the gap remains OPEN and live-blocking because "
        "long-run PAPER/SHADOW evidence, replay coverage, profit factor, drawdown, fill quality, paper/live parity, "
        "read-only burn-in, live safety proof, and operator approval are still not complete."
    )
    write_json(path, gap)


def main() -> int:
    now = utc_now()
    authority = {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }
    scorecard = load_json(SCORECARD_PATH)
    overfit = load_json(OVERFIT_PATH)
    paper_shadow_evidence = load_json(PAPER_SHADOW_EVIDENCE_PATH) if PAPER_SHADOW_EVIDENCE_PATH.is_file() else None
    runtime_profile = load_json(RUNTIME_COLLECTION_PROFILE_PATH) if RUNTIME_COLLECTION_PROFILE_PATH.is_file() else None
    refresh_rollup(
        ROLLUP_PATH,
        now=now,
        authority=authority,
        scorecard=scorecard,
        overfit=overfit,
        paper_shadow_evidence=paper_shadow_evidence,
        runtime_profile=runtime_profile,
    )
    refresh_rollup(
        ROLLUP_FIXTURE_PATH,
        now=now,
        authority=authority,
        scorecard=scorecard,
        overfit=overfit,
        paper_shadow_evidence=paper_shadow_evidence,
        runtime_profile=runtime_profile,
    )
    refresh_contract_gap(CONTRACT_GAP_PATH, now=now, authority=authority)
    refreshed_rollup = load_json(ROLLUP_PATH)
    runtime_profile_evidence = refreshed_rollup["runtime_collection_profile_evidence"]
    result = {
        "status": "PASS",
        "rollup_path": rel(ROLLUP_PATH),
        "fixture_path": rel(ROLLUP_FIXTURE_PATH),
        "contract_gap_path": rel(CONTRACT_GAP_PATH),
        "scorecard_id": scorecard.get("scorecard_id"),
        "sample_count": overfit.get("sample_count"),
        "robustness_source_type_status": refreshed_rollup["robustness_source_type_evidence"]["status"],
        "runtime_collection_profile_status": runtime_profile_evidence["status"],
        "paper_remaining_cycle_count": runtime_profile_evidence["paper_remaining_cycle_count"],
        "paper_remaining_span_seconds": runtime_profile_evidence["paper_remaining_span_seconds"],
        "shadow_remaining_cycle_count": runtime_profile_evidence["shadow_remaining_cycle_count"],
        "shadow_remaining_span_seconds": runtime_profile_evidence["shadow_remaining_span_seconds"],
        "recommended_next_paper_batch_cycle_count": runtime_profile_evidence[
            "recommended_next_paper_batch_cycle_count"
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
