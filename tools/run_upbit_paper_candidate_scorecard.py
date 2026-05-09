from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.research.profitability.candidate_scorecard import (
    candidate_generation_report_from_upbit_paper_runtime_cycle,
    candidate_scorecard_from_upbit_paper_runtime_cycle,
    performance_inputs_from_runtime_sample_history,
    validate_candidate_generation_report,
    write_upbit_paper_candidate_generation_report,
    write_upbit_paper_candidate_scorecard,
    write_upbit_paper_candidate_scorecard_snapshot,
)
from trader1.adapters.upbit.market_data import (
    DEFAULT_DISCOVERY_EVALUATION_LIMIT,
    fetch_upbit_krw_market_symbols_read_only,
    fetch_upbit_public_candle_history_read_only,
    fetch_upbit_public_ticker_snapshot_read_only,
    rank_upbit_krw_symbols_by_public_ticker,
)
from trader1.research.profitability.convergence_memory import write_upbit_paper_convergence_memory_artifacts
from trader1.research.profitability.overfit_diagnostic import (
    DEFAULT_MIN_REQUIRED_SAMPLE_COUNT,
    overfit_diagnostic_from_upbit_paper_runtime,
    overfit_diagnostic_report_hash,
    robustness_inputs_from_overfit_diagnostic,
    write_overfit_diagnostic_report_snapshot,
    write_overfit_diagnostic_report,
)
from trader1.research.replay.replay_runner import (
    build_public_replay_fetch_failure_report,
    build_public_replay_robustness_report,
    load_public_replay_robustness_report,
    validate_public_replay_robustness_report,
    write_public_replay_robustness_report,
)
from trader1.research.shadow.shadow_runner import validate_paper_shadow_evidence_accumulation_report
from trader1.runtime.paper.upbit_paper_runtime import (
    build_upbit_paper_runtime_cycle_report,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    durable_atomic_write_json,
    validate_upbit_public_market_data_collection_report,
)
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


def _diagnostic_sample_threshold_from_replay_report(replay_report: dict[str, Any] | None) -> int:
    if not isinstance(replay_report, dict):
        return DEFAULT_MIN_REQUIRED_SAMPLE_COUNT
    try:
        threshold = int(replay_report.get("min_required_sample_count") or 0)
    except (TypeError, ValueError):
        return DEFAULT_MIN_REQUIRED_SAMPLE_COUNT
    if threshold <= 0:
        return DEFAULT_MIN_REQUIRED_SAMPLE_COUNT
    return threshold


def _public_replay_robustness_context(
    *,
    loaded_report: dict[str, Any] | None,
    contract_status: str,
    contract_blocker_code: str | None,
    diagnostic: dict[str, Any],
) -> dict[str, Any]:
    report_present = isinstance(loaded_report, dict)
    replay_status = str(loaded_report.get("replay_status") or "MISSING") if report_present else "MISSING"
    sample_count = loaded_report.get("sample_count") if report_present else None
    source_bound = any(
        isinstance(source_id, str) and source_id.startswith("public_replay_robustness:")
        for source_id in diagnostic.get("source_evidence_ids") or []
    )
    diagnostic_blocker_codes = [
        str(blocker.get("code"))
        for blocker in diagnostic.get("blockers") or []
        if isinstance(blocker, dict) and blocker.get("code")
    ]

    if not report_present:
        status = "MISSING"
        blocker_code = contract_blocker_code or "MEASUREMENT_MISSING"
    elif contract_status != "PASS":
        status = "CONTRACT_BLOCKED" if contract_status == "BLOCKED" else "CONTRACT_FAIL"
        blocker_code = contract_blocker_code or "SCHEMA_IDENTITY_MISMATCH"
    elif "PUBLIC_REPLAY_ROBUSTNESS_FAILED" in diagnostic_blocker_codes:
        status = "FAILED_ROBUSTNESS_GATE"
        blocker_code = "PUBLIC_REPLAY_ROBUSTNESS_FAILED"
    elif source_bound and diagnostic.get("robustness_eligible") is True:
        status = "PASS"
        blocker_code = None
    elif source_bound:
        status = "BLOCKED_ROBUSTNESS_GATE"
        blocker_code = diagnostic_blocker_codes[0] if diagnostic_blocker_codes else "ROBUSTNESS_MATURITY_BLOCKED"
    else:
        status = "CONTRACT_PASS_NOT_BOUND"
        blocker_code = "MEASUREMENT_MISSING"

    return {
        "status": status,
        "blocker_code": blocker_code,
        "contract_status": contract_status,
        "contract_blocker_code": contract_blocker_code,
        "replay_status": replay_status,
        "sample_count": sample_count,
        "source_bound": source_bound,
        "oos_status": str(diagnostic.get("oos_status") or "UNTESTED"),
        "walk_forward_status": str(diagnostic.get("walk_forward_status") or "UNTESTED"),
        "bootstrap_status": str(diagnostic.get("bootstrap_status") or "UNTESTED"),
        "overfit_status": str(diagnostic.get("overfit_status") or "UNTESTED"),
    }


def _paper_runtime_base(root: Path, session_id: str) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _candidate_discovery_runtime_path(root: Path, session_id: str) -> Path:
    return _paper_runtime_base(root, session_id) / "profitability" / "candidate_generation_discovery_runtime_cycle.json"


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


def _bind_performance_sources_to_overfit_diagnostic(
    diagnostic: dict[str, Any],
    *,
    performance_source_ids: list[str],
) -> dict[str, Any]:
    if not performance_source_ids:
        return diagnostic
    bound = dict(diagnostic)
    source_ids = [
        source_id
        for source_id in bound.get("source_evidence_ids") or []
        if isinstance(source_id, str) and source_id
    ]
    source_ids.extend(
        source_id
        for source_id in performance_source_ids
        if isinstance(source_id, str) and source_id
    )
    bound["source_evidence_ids"] = sorted(set(source_ids))
    bound["diagnostic_hash"] = overfit_diagnostic_report_hash(bound)
    return bound


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


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if result == result and result not in {float("inf"), float("-inf")} else default


def _ordered_count_items(counter: Counter[str], *, limit: int = 12) -> list[dict[str, Any]]:
    return [
        {"code": code, "count": count}
        for code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _candidate_discovery_empty_diagnostics() -> dict[str, Any]:
    return {
        "evaluated_candidate_count": 0,
        "paper_entry_review_candidate_count": 0,
        "blocked_candidate_count": 0,
        "adaptive_expansion_attempted": False,
        "initial_symbol_count": 0,
        "expanded_symbol_count": 0,
        "max_expanded_symbol_count": 0,
        "strategy_family_candidate_counts": [],
        "strategy_family_review_ready_counts": [],
        "strategy_family_blocked_counts": [],
        "no_trade_reason_counts": [],
        "strategy_policy_reason_counts": [],
        "entry_block_reason_counts": [],
        "top_blocked_symbols": [],
    }


def _candidate_discovery_diagnostics(runtime: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(runtime, dict):
        return _candidate_discovery_empty_diagnostics()

    candidates = [candidate for candidate in runtime.get("strategy_candidates") or [] if isinstance(candidate, dict)]
    scorecards = [scorecard for scorecard in runtime.get("symbol_evidence_scorecards") or [] if isinstance(scorecard, dict)]
    universe = [item for item in runtime.get("symbol_selection_universe") or [] if isinstance(item, dict)]

    strategy_family_counter: Counter[str] = Counter()
    strategy_family_review_ready_counter: Counter[str] = Counter()
    strategy_family_blocked_counter: Counter[str] = Counter()
    no_trade_counter: Counter[str] = Counter()
    strategy_policy_counter: Counter[str] = Counter()
    entry_block_counter: Counter[str] = Counter()
    review_ready_count = 0

    for candidate in candidates:
        family = str(candidate.get("strategy_family") or "UNKNOWN")
        strategy_family_counter[family] += 1
        policy_reason = str(candidate.get("strategy_policy_reason") or "")
        if policy_reason:
            strategy_policy_counter[policy_reason] += 1
        if candidate.get("decision") == "PAPER_ENTRY_REVIEW":
            review_ready_count += 1
            strategy_family_review_ready_counter[family] += 1
            continue
        strategy_family_blocked_counter[family] += 1
        reason = str(candidate.get("no_trade_reason") or policy_reason or "UNKNOWN_NO_TRADE_REASON")
        no_trade_counter[reason] += 1

    for item in universe:
        reason = str(item.get("entry_block_reason") or "")
        if reason:
            entry_block_counter[reason] += 1

    blocked_symbols: list[dict[str, Any]] = []
    for scorecard in sorted(scorecards, key=lambda item: _safe_int(item.get("rank_input_order"))):
        if _safe_int(scorecard.get("paper_entry_review_candidate_count")) > 0:
            continue
        blocked_symbols.append(
            {
                "symbol": str(scorecard.get("symbol") or ""),
                "regime": scorecard.get("regime"),
                "market_state": scorecard.get("market_state"),
                "best_strategy_family": scorecard.get("best_strategy_family"),
                "best_no_trade_reason": scorecard.get("best_no_trade_reason"),
                "best_strategy_policy_reason": scorecard.get("best_strategy_policy_reason"),
                "no_trade_reasons": list(scorecard.get("no_trade_reasons") or [])[:5],
            }
        )

    return {
        "evaluated_candidate_count": len(candidates),
        "paper_entry_review_candidate_count": review_ready_count,
        "blocked_candidate_count": len(candidates) - review_ready_count,
        "adaptive_expansion_attempted": False,
        "initial_symbol_count": len(scorecards),
        "expanded_symbol_count": len(scorecards),
        "max_expanded_symbol_count": len(scorecards),
        "strategy_family_candidate_counts": _ordered_count_items(strategy_family_counter),
        "strategy_family_review_ready_counts": _ordered_count_items(strategy_family_review_ready_counter),
        "strategy_family_blocked_counts": _ordered_count_items(strategy_family_blocked_counter),
        "no_trade_reason_counts": _ordered_count_items(no_trade_counter),
        "strategy_policy_reason_counts": _ordered_count_items(strategy_policy_counter),
        "entry_block_reason_counts": _ordered_count_items(entry_block_counter),
        "top_blocked_symbols": blocked_symbols[:5],
    }


def _build_runtime_for_public_collection_reports(
    *,
    session_id: str,
    collection_reports: list[dict[str, Any]],
    selected_symbols: list[str],
) -> tuple[dict[str, Any] | None, Any]:
    runtime = build_upbit_paper_runtime_cycle_report(
        cycle_id=f"candidate-generation-discovery-{session_id}",
        session_id=session_id,
        symbol=str(collection_reports[0].get("symbol") or selected_symbols[0]),
        source_collection_reports=collection_reports,
    )
    runtime_validation = validate_upbit_paper_runtime_cycle_report(runtime)
    if runtime_validation.status != "PASS":
        return None, runtime_validation
    return runtime, runtime_validation


def _collect_public_candle_reports(
    *,
    session_id: str,
    selected_symbols: list[str],
    timeout_seconds: float,
    public_candle_fetcher: Callable[..., dict[str, Any]] | None,
    already_collected_symbols: set[str] | None = None,
    start_index: int = 1,
) -> list[dict[str, Any]]:
    already_collected_symbols = already_collected_symbols or set()
    collection_reports: list[dict[str, Any]] = []
    for offset, symbol in enumerate(selected_symbols, start=start_index):
        if symbol in already_collected_symbols:
            continue
        collection = build_upbit_public_market_data_collection_report(
            collector_id=f"candidate-generation-discovery-{offset}-{symbol}",
            session_id=session_id,
            symbol=symbol,
            attempt_network=True,
            fetcher=public_candle_fetcher,
            timeout_seconds=timeout_seconds,
        )
        validation = validate_upbit_public_market_data_collection_report(collection)
        if validation.status == "PASS":
            collection_reports.append(collection)
            already_collected_symbols.add(symbol)
    return collection_reports


def _candidate_discovery_context(
    *,
    status: str,
    blocker_code: str | None,
    message: str,
    symbol_count: int,
    ranked_symbol_count: int = 0,
    eligible_symbol_count: int = 0,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    discovery_diagnostics = _candidate_discovery_empty_diagnostics()
    if diagnostics:
        discovery_diagnostics.update(diagnostics)
    return {
        "status": status,
        "blocker_code": blocker_code,
        "message": message,
        "symbol_count": symbol_count,
        "ranked_symbol_count": ranked_symbol_count,
        "eligible_symbol_count": eligible_symbol_count,
        **discovery_diagnostics,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _alternative_replay_context(
    *,
    status: str,
    blocker_code: str | None,
    message: str,
    contract_status: str | None = None,
    contract_blocker_code: str | None = None,
    report_path: str | None = None,
    candidate_id: str | None = None,
    symbol: str | None = None,
    replay_status: str | None = None,
    sample_count: int = 0,
    primary_blocker_code: str | None = None,
    replay_closed_trade_sample_count: int = 0,
    replay_closed_trade_status: str | None = None,
    min_required_closed_trade_sample_count: int = 0,
    replay_closed_trade_deficit: int = 0,
    replay_closed_trade_maturity_status: str | None = None,
    replay_closed_trade_maturity_blocker_code: str | None = None,
    replay_strategy_exit_policy_sample_count: int = 0,
    replay_strategy_exit_policy_status: str | None = None,
    replay_strategy_exit_policy_mismatch_count: int = 0,
    replay_profit_factor: float = 0.0,
    replay_profit_factor_status: str | None = None,
    replay_realized_vs_expected_edge_bps: float = 0.0,
    replay_realized_vs_expected_edge_status: str | None = None,
    replay_execution_cost_delta_bps: float = 0.0,
    replay_execution_cost_status: str | None = None,
    report: dict[str, Any] | None = None,
    scorecard: dict[str, Any] | None = None,
    source_runtime_cycle_report: dict[str, Any] | None = None,
    candidate_review_evaluations: list[dict[str, Any]] | None = None,
    candidate_review_evaluated_count: int = 0,
    candidate_review_robust_candidate_count: int = 0,
    candidate_review_selection_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "blocker_code": blocker_code,
        "message": message,
        "contract_status": contract_status or status,
        "contract_blocker_code": contract_blocker_code,
        "report_path": report_path,
        "candidate_id": candidate_id,
        "symbol": symbol,
        "replay_status": replay_status,
        "sample_count": sample_count,
        "primary_blocker_code": primary_blocker_code,
        "replay_closed_trade_sample_count": replay_closed_trade_sample_count,
        "replay_closed_trade_status": replay_closed_trade_status or "UNTESTED",
        "min_required_closed_trade_sample_count": min_required_closed_trade_sample_count,
        "replay_closed_trade_deficit": replay_closed_trade_deficit,
        "replay_closed_trade_maturity_status": replay_closed_trade_maturity_status or "UNTESTED",
        "replay_closed_trade_maturity_blocker_code": replay_closed_trade_maturity_blocker_code,
        "replay_strategy_exit_policy_sample_count": replay_strategy_exit_policy_sample_count,
        "replay_strategy_exit_policy_status": replay_strategy_exit_policy_status or "UNTESTED",
        "replay_strategy_exit_policy_mismatch_count": replay_strategy_exit_policy_mismatch_count,
        "replay_profit_factor": replay_profit_factor,
        "replay_profit_factor_status": replay_profit_factor_status or "UNTESTED",
        "replay_realized_vs_expected_edge_bps": replay_realized_vs_expected_edge_bps,
        "replay_realized_vs_expected_edge_status": replay_realized_vs_expected_edge_status or "UNTESTED",
        "replay_execution_cost_delta_bps": replay_execution_cost_delta_bps,
        "replay_execution_cost_status": replay_execution_cost_status or "UNTESTED",
        "report": report,
        "scorecard": scorecard,
        "source_runtime_cycle_report": source_runtime_cycle_report,
        "candidate_review_evaluations": candidate_review_evaluations or [],
        "candidate_review_evaluated_count": candidate_review_evaluated_count,
        "candidate_review_robust_candidate_count": candidate_review_robust_candidate_count,
        "candidate_review_selection_reason": candidate_review_selection_reason,
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _build_bounded_public_discovery_runtime_cycle(
    *,
    session_id: str,
    symbol_limit: int,
    timeout_seconds: float,
    market_symbols_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_ticker_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_candle_fetcher: Callable[..., dict[str, Any]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    safe_limit = max(1, min(int(symbol_limit), DEFAULT_DISCOVERY_EVALUATION_LIMIT))
    discovery_fetcher = market_symbols_fetcher or fetch_upbit_krw_market_symbols_read_only
    ticker_fetcher = public_ticker_fetcher or fetch_upbit_public_ticker_snapshot_read_only
    symbol_report = discovery_fetcher(session_id=session_id, timeout_seconds=timeout_seconds)
    symbols = [str(symbol) for symbol in symbol_report.get("symbols") or [] if str(symbol).startswith("KRW-")]
    if symbol_report.get("discovery_status") != "PASS" or not symbols:
        return None, _candidate_discovery_context(
            status="BLOCKED",
            blocker_code=symbol_report.get("primary_blocker_code") or "DATA_UNAVAILABLE",
            message="bounded public candidate discovery could not load the KRW symbol universe",
            symbol_count=len(symbols),
        )

    ticker_report = ticker_fetcher(symbols=symbols, session_id=session_id, timeout_seconds=timeout_seconds)
    ticker_by_symbol = ticker_report.get("ticker_by_symbol") if isinstance(ticker_report.get("ticker_by_symbol"), dict) else {}
    ranking = rank_upbit_krw_symbols_by_public_ticker(
        symbols=symbols,
        ticker_by_symbol=ticker_by_symbol,
        session_id=session_id,
        limit=safe_limit,
    )
    selected_symbols = [str(symbol) for symbol in ranking.get("selected_symbols_for_candle_evaluation") or []]
    if ranking.get("ranking_status") != "PASS" or not selected_symbols:
        return None, _candidate_discovery_context(
            status="BLOCKED",
            blocker_code=ranking.get("primary_blocker_code") or "DATA_UNAVAILABLE",
            message="bounded public candidate discovery could not rank KRW symbols for candle evaluation",
            symbol_count=0,
            ranked_symbol_count=int(ranking.get("ranked_symbol_count") or 0),
            eligible_symbol_count=int(ranking.get("eligible_symbol_count") or 0),
        )

    ranked_symbols = [
        str(item.get("symbol"))
        for item in ranking.get("symbol_rankings") or []
        if isinstance(item, dict) and item.get("eligible_for_candle_evaluation") is True and item.get("symbol")
    ]
    if not ranked_symbols:
        ranked_symbols = selected_symbols
    initial_symbols = ranked_symbols[:safe_limit]
    attempted_symbol_count = len(initial_symbols)
    collected_symbols: set[str] = set()
    collection_reports = _collect_public_candle_reports(
        session_id=session_id,
        selected_symbols=initial_symbols,
        timeout_seconds=timeout_seconds,
        public_candle_fetcher=public_candle_fetcher,
        already_collected_symbols=collected_symbols,
    )

    adaptive_expansion_attempted = False
    max_expanded_symbol_count = max(
        safe_limit,
        min(DEFAULT_DISCOVERY_EVALUATION_LIMIT, safe_limit * 3, len(ranked_symbols)),
    )

    if not collection_reports:
        adaptive_expansion_attempted = max_expanded_symbol_count > safe_limit
        if adaptive_expansion_attempted:
            collection_reports.extend(
                _collect_public_candle_reports(
                    session_id=session_id,
                    selected_symbols=ranked_symbols[safe_limit:max_expanded_symbol_count],
                    timeout_seconds=timeout_seconds,
                    public_candle_fetcher=public_candle_fetcher,
                    already_collected_symbols=collected_symbols,
                    start_index=safe_limit + 1,
                )
            )
            attempted_symbol_count = max_expanded_symbol_count
    if not collection_reports:
        return None, _candidate_discovery_context(
            status="BLOCKED",
            blocker_code="DATA_UNAVAILABLE",
            message="bounded public candidate discovery found no valid public candle collections",
            symbol_count=0,
            ranked_symbol_count=int(ranking.get("ranked_symbol_count") or 0),
            eligible_symbol_count=int(ranking.get("eligible_symbol_count") or 0),
            diagnostics={
                "adaptive_expansion_attempted": adaptive_expansion_attempted,
                "initial_symbol_count": len(initial_symbols),
                "expanded_symbol_count": attempted_symbol_count,
                "max_expanded_symbol_count": max_expanded_symbol_count,
            },
        )

    runtime, runtime_validation = _build_runtime_for_public_collection_reports(
        session_id=session_id,
        collection_reports=collection_reports,
        selected_symbols=ranked_symbols,
    )
    if runtime_validation.status != "PASS":
        return None, _candidate_discovery_context(
            status=runtime_validation.status,
            blocker_code=runtime_validation.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
            message=runtime_validation.message,
            symbol_count=len(collection_reports),
            ranked_symbol_count=int(ranking.get("ranked_symbol_count") or 0),
            eligible_symbol_count=int(ranking.get("eligible_symbol_count") or 0),
        )
    discovery_diagnostics = _candidate_discovery_diagnostics(runtime)
    discovery_diagnostics.update(
        {
            "adaptive_expansion_attempted": adaptive_expansion_attempted,
            "initial_symbol_count": len(initial_symbols),
            "expanded_symbol_count": attempted_symbol_count,
            "max_expanded_symbol_count": max_expanded_symbol_count,
        }
    )

    if (
        discovery_diagnostics["paper_entry_review_candidate_count"] == 0
        and max_expanded_symbol_count > attempted_symbol_count
    ):
        adaptive_expansion_attempted = True
        collection_reports.extend(
            _collect_public_candle_reports(
                session_id=session_id,
                selected_symbols=ranked_symbols[attempted_symbol_count:max_expanded_symbol_count],
                timeout_seconds=timeout_seconds,
                public_candle_fetcher=public_candle_fetcher,
                already_collected_symbols=collected_symbols,
                start_index=attempted_symbol_count + 1,
            )
        )
        attempted_symbol_count = max_expanded_symbol_count
        expanded_runtime, expanded_runtime_validation = _build_runtime_for_public_collection_reports(
            session_id=session_id,
            collection_reports=collection_reports,
            selected_symbols=ranked_symbols,
        )
        if expanded_runtime_validation.status == "PASS":
            runtime = expanded_runtime
            discovery_diagnostics = _candidate_discovery_diagnostics(runtime)
            discovery_diagnostics.update(
                {
                    "adaptive_expansion_attempted": True,
                    "initial_symbol_count": len(initial_symbols),
                    "expanded_symbol_count": attempted_symbol_count,
                    "max_expanded_symbol_count": max_expanded_symbol_count,
                }
            )
        else:
            discovery_diagnostics.update(
                {
                    "adaptive_expansion_attempted": True,
                    "initial_symbol_count": len(initial_symbols),
                    "expanded_symbol_count": attempted_symbol_count,
                    "max_expanded_symbol_count": max_expanded_symbol_count,
                }
            )

    return runtime, _candidate_discovery_context(
        status="PASS",
        blocker_code=None,
        message=(
            "bounded public candidate discovery runtime cycle built from read-only public KRW market and candle data"
            if not discovery_diagnostics["adaptive_expansion_attempted"]
            else "bounded public candidate discovery expanded once after the initial public KRW set produced no entry-review candidate"
        ),
        symbol_count=len(collection_reports),
        ranked_symbol_count=int(ranking.get("ranked_symbol_count") or 0),
        eligible_symbol_count=int(ranking.get("eligible_symbol_count") or 0),
        diagnostics=discovery_diagnostics,
    )


def _review_ready_candidate_items(candidate_generation_report: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 12))
    return [
        item
        for item in candidate_generation_report.get("candidate_items") or []
        if isinstance(item, dict) and item.get("candidate_status") == "REVIEW_READY"
    ][:safe_limit]


def _source_runtime_for_candidate_item(
    item: dict[str, Any],
    *,
    runtime_cycle_report: dict[str, Any] | None,
    candidate_discovery_runtime: dict[str, Any] | None,
) -> dict[str, Any] | None:
    source_cycle_id = str(item.get("source_runtime_cycle_id") or "")
    source_cycle_hash = str(item.get("source_runtime_cycle_hash") or "").upper()
    for runtime_candidate in (runtime_cycle_report, candidate_discovery_runtime):
        if not isinstance(runtime_candidate, dict):
            continue
        if source_cycle_id and str(runtime_candidate.get("cycle_id") or "") != source_cycle_id:
            continue
        if source_cycle_hash and str(runtime_candidate.get("cycle_hash") or "").upper() != source_cycle_hash:
            continue
        return runtime_candidate
    return None


def _evaluation_or_report_metric(evaluation: dict[str, Any], replay_report: dict[str, Any], key: str) -> Any:
    value = evaluation.get(key)
    return value if value is not None else replay_report.get(key)


def _replay_closed_trade_maturity(report: dict[str, Any]) -> dict[str, Any]:
    closed_count = _safe_int(report.get("replay_closed_trade_sample_count"))
    min_required = _safe_int(
        report.get("min_required_closed_trade_sample_count")
        or report.get("min_required_sample_count")
    )
    if min_required <= 0:
        min_required = 1
    deficit = max(0, min_required - closed_count)
    status = str(report.get("replay_closed_trade_maturity_status") or "")
    if status not in {"PASS", "BLOCKED", "UNTESTED"}:
        if deficit <= 0:
            status = "PASS"
        elif closed_count > 0:
            status = "BLOCKED"
        else:
            status = "UNTESTED"
    blocker_code = report.get("replay_closed_trade_maturity_blocker_code")
    if status != "PASS" and not blocker_code:
        blocker_code = "REPLAY_CLOSED_TRADES_BELOW_MIN" if closed_count > 0 else "REPLAY_CLOSED_TRADES_MISSING"
    return {
        "min_required_closed_trade_sample_count": min_required,
        "replay_closed_trade_deficit": deficit,
        "replay_closed_trade_maturity_status": status,
        "replay_closed_trade_maturity_blocker_code": blocker_code,
    }


def _alternative_replay_selection_priority(evaluation: dict[str, Any]) -> tuple[Any, ...]:
    diagnostic = evaluation.get("diagnostic") if isinstance(evaluation.get("diagnostic"), dict) else {}
    replay_report = evaluation.get("report") if isinstance(evaluation.get("report"), dict) else {}
    scorecard = evaluation.get("scorecard") if isinstance(evaluation.get("scorecard"), dict) else {}
    status = str(evaluation.get("status") or "")
    replay_status = str(evaluation.get("replay_status") or replay_report.get("replay_status") or "")
    contract_status = str(evaluation.get("contract_status") or "")
    closed_trade_count = _safe_int(
        _evaluation_or_report_metric(evaluation, replay_report, "replay_closed_trade_sample_count")
    )
    strategy_exit_policy_count = _safe_int(
        _evaluation_or_report_metric(evaluation, replay_report, "replay_strategy_exit_policy_sample_count")
    )
    strategy_exit_mismatch_count = _safe_int(
        _evaluation_or_report_metric(evaluation, replay_report, "replay_strategy_exit_policy_mismatch_count")
    )
    closed_trade_status = str(
        evaluation.get("replay_closed_trade_status") or replay_report.get("replay_closed_trade_status") or ""
    )
    closed_trade_maturity = _replay_closed_trade_maturity(replay_report)
    closed_trade_maturity_status = str(
        evaluation.get("replay_closed_trade_maturity_status")
        or closed_trade_maturity["replay_closed_trade_maturity_status"]
    )
    closed_trade_deficit = _safe_int(
        evaluation.get("replay_closed_trade_deficit")
        if evaluation.get("replay_closed_trade_deficit") is not None
        else closed_trade_maturity["replay_closed_trade_deficit"]
    )
    strategy_exit_policy_status = str(
        evaluation.get("replay_strategy_exit_policy_status")
        or replay_report.get("replay_strategy_exit_policy_status")
        or ""
    )
    profit_factor_status = str(
        evaluation.get("replay_profit_factor_status") or replay_report.get("replay_profit_factor_status") or ""
    )
    realized_edge_status = str(
        evaluation.get("replay_realized_vs_expected_edge_status")
        or replay_report.get("replay_realized_vs_expected_edge_status")
        or ""
    )
    execution_cost_status = str(
        evaluation.get("replay_execution_cost_status") or replay_report.get("replay_execution_cost_status") or ""
    )
    return (
        1 if diagnostic.get("robustness_eligible") is True else 0,
        1 if status == "PASS" else 0,
        1 if replay_status == "PASS" else 0,
        1 if contract_status == "PASS" else 0,
        1 if closed_trade_count > 0 else 0,
        1 if closed_trade_maturity_status == "PASS" else 0,
        -closed_trade_deficit,
        1 if closed_trade_status == "PASS" else 0,
        closed_trade_count,
        1 if strategy_exit_policy_status == "PASS" else 0,
        strategy_exit_policy_count,
        -strategy_exit_mismatch_count,
        1 if profit_factor_status == "PASS" else 0,
        _safe_float(_evaluation_or_report_metric(evaluation, replay_report, "replay_profit_factor"), -999.0),
        1 if realized_edge_status == "PASS" else 0,
        _safe_float(
            _evaluation_or_report_metric(evaluation, replay_report, "replay_realized_vs_expected_edge_bps"),
            -999.0,
        ),
        1 if execution_cost_status == "PASS" else 0,
        -_safe_float(
            _evaluation_or_report_metric(evaluation, replay_report, "replay_execution_cost_delta_bps"),
            999.0,
        ),
        1 if diagnostic.get("oos_status") == "PASS" else 0,
        1 if diagnostic.get("walk_forward_status") == "PASS" else 0,
        1 if diagnostic.get("bootstrap_status") == "PASS" else 0,
        1 if diagnostic.get("concentration_risk_status") == "LOW" else 0,
        _safe_float(diagnostic.get("oos_net_ev_after_cost_bps"), -999.0),
        _safe_float(diagnostic.get("bootstrap_confidence_lower_bps"), -999.0),
        _safe_float(diagnostic.get("walk_forward_pass_rate"), -999.0),
        _safe_float(diagnostic.get("ranking_stability_score"), -999.0),
        _safe_float(scorecard.get("net_ev_after_cost_bps"), -999.0),
        -_safe_int(evaluation.get("candidate_index")),
        str(evaluation.get("candidate_id") or ""),
    )


def _public_candidate_review_evaluations(evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for item in evaluations:
        compact.append(
            {
                "candidate_id": item.get("candidate_id"),
                "symbol": item.get("symbol"),
                "status": item.get("status"),
                "blocker_code": item.get("blocker_code"),
                "replay_status": item.get("replay_status"),
                "sample_count": int(item.get("sample_count") or 0),
                "replay_closed_trade_sample_count": int(item.get("replay_closed_trade_sample_count") or 0),
                "replay_closed_trade_status": item.get("replay_closed_trade_status"),
                "min_required_closed_trade_sample_count": int(
                    item.get("min_required_closed_trade_sample_count") or 0
                ),
                "replay_closed_trade_deficit": int(item.get("replay_closed_trade_deficit") or 0),
                "replay_closed_trade_maturity_status": item.get("replay_closed_trade_maturity_status"),
                "replay_closed_trade_maturity_blocker_code": item.get(
                    "replay_closed_trade_maturity_blocker_code"
                ),
                "replay_strategy_exit_policy_sample_count": int(
                    item.get("replay_strategy_exit_policy_sample_count") or 0
                ),
                "replay_strategy_exit_policy_status": item.get("replay_strategy_exit_policy_status"),
                "replay_strategy_exit_policy_mismatch_count": int(
                    item.get("replay_strategy_exit_policy_mismatch_count") or 0
                ),
                "replay_profit_factor": _safe_float(item.get("replay_profit_factor")),
                "replay_profit_factor_status": item.get("replay_profit_factor_status"),
                "replay_realized_vs_expected_edge_bps": _safe_float(
                    item.get("replay_realized_vs_expected_edge_bps")
                ),
                "replay_realized_vs_expected_edge_status": item.get("replay_realized_vs_expected_edge_status"),
                "replay_execution_cost_delta_bps": _safe_float(item.get("replay_execution_cost_delta_bps")),
                "replay_execution_cost_status": item.get("replay_execution_cost_status"),
                "robustness_eligible": bool(item.get("robustness_eligible")),
                "oos_status": item.get("oos_status"),
                "walk_forward_status": item.get("walk_forward_status"),
                "bootstrap_status": item.get("bootstrap_status"),
                "overfit_status": item.get("overfit_status"),
                "diagnostic_blocker_codes": list(item.get("diagnostic_blocker_codes") or []),
            }
        )
    return compact


def _build_alternative_public_replay_evaluation(
    *,
    root: Path,
    session_id: str,
    item: dict[str, Any],
    candidate_index: int,
    history: dict[str, Any],
    runtime_cycle_report: dict[str, Any] | None,
    candidate_discovery_runtime: dict[str, Any] | None,
    target_count: int,
    page_size: int,
    timeout_seconds: float,
    max_replay_windows: int,
    min_required_sample_count: int,
    market_data_cache: dict[str, dict[str, Any]],
    public_replay_history_fetcher: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidate_id = str(item.get("candidate_id") or "")
    source_runtime = _source_runtime_for_candidate_item(
        item,
        runtime_cycle_report=runtime_cycle_report,
        candidate_discovery_runtime=candidate_discovery_runtime,
    )
    if not isinstance(source_runtime, dict):
        return {
            "status": "BLOCKED",
            "blocker_code": "MEASUREMENT_MISSING",
            "message": "candidate public replay requires the runtime cycle that produced the candidate",
            "candidate_id": candidate_id,
            "candidate_index": candidate_index,
            "symbol": str(item.get("symbol") or ""),
            "robustness_eligible": False,
        }

    try:
        alternative_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
            source_runtime,
            candidate_id=candidate_id,
        )
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "message": f"candidate could not be bound to its source runtime: {type(exc).__name__}",
            "candidate_id": candidate_id,
            "candidate_index": candidate_index,
            "symbol": str(item.get("symbol") or ""),
            "robustness_eligible": False,
        }
    if str(alternative_scorecard.get("candidate_id") or "") != candidate_id:
        return {
            "status": "BLOCKED",
            "blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "message": "candidate scope did not match candidate generation item",
            "candidate_id": str(alternative_scorecard.get("candidate_id") or ""),
            "candidate_index": candidate_index,
            "symbol": str(alternative_scorecard.get("symbol") or ""),
            "robustness_eligible": False,
        }

    history_fetcher = public_replay_history_fetcher or fetch_upbit_public_candle_history_read_only
    symbol = str(alternative_scorecard["symbol"])
    replay_id = f"public-replay-alternative:{alternative_scorecard['source_runtime_cycle_id']}:{alternative_scorecard['candidate_id']}"
    try:
        if symbol not in market_data_cache:
            market_data_cache[symbol] = history_fetcher(
                symbol=symbol,
                session_id=session_id,
                target_count=target_count,
                page_size=page_size,
                timeout_seconds=timeout_seconds,
            )
        replay_report = build_public_replay_robustness_report(
            candidate_scorecard=alternative_scorecard,
            market_data=market_data_cache[symbol],
            replay_id=replay_id,
            max_replay_windows=max_replay_windows,
            min_required_sample_count=min_required_sample_count,
        )
    except Exception as exc:
        replay_report = build_public_replay_fetch_failure_report(
            candidate_scorecard=alternative_scorecard,
            replay_id=replay_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            target_count=target_count,
            page_size=page_size,
            timeout_seconds=timeout_seconds,
            max_replay_windows=max_replay_windows,
            min_required_sample_count=min_required_sample_count,
        )

    replay_validation = validate_public_replay_robustness_report(
        replay_report,
        candidate_scorecard=alternative_scorecard,
    )
    report_path = write_public_replay_robustness_report(root=root, report=replay_report)
    replay_status = str(replay_report.get("replay_status") or "BLOCKED")
    gate_status = replay_validation.status
    gate_blocker_code = replay_validation.blocker_code
    gate_message = replay_validation.message
    if replay_validation.status == "PASS" and replay_status != "PASS":
        gate_status = "BLOCKED"
        gate_blocker_code = str(replay_report.get("primary_blocker_code") or "MEASUREMENT_MISSING")
        gate_message = (
            "candidate public replay report is contract-valid but replay robustness "
            f"gate is {replay_status}: {gate_blocker_code}"
        )
    closed_trade_maturity = _replay_closed_trade_maturity(replay_report)
    if (
        replay_validation.status == "PASS"
        and replay_status == "PASS"
        and closed_trade_maturity["replay_closed_trade_maturity_status"] != "PASS"
    ):
        gate_status = "BLOCKED"
        gate_blocker_code = str(
            closed_trade_maturity["replay_closed_trade_maturity_blocker_code"]
            or "REPLAY_CLOSED_TRADES_BELOW_MIN"
        )
        gate_message = (
            "candidate public replay window collection passed, but realized closed-trade samples "
            f"{int(replay_report.get('replay_closed_trade_sample_count') or 0)}/"
            f"{closed_trade_maturity['min_required_closed_trade_sample_count']} are insufficient "
            "for OOS, walk-forward, bootstrap, and profit-factor evidence"
        )

    diagnostic: dict[str, Any] | None = None
    diagnostic_blocker_codes: list[str] = []
    if gate_status == "PASS":
        diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
            candidate_scorecard=alternative_scorecard,
            runtime_sample_history=history,
            root=root,
            replay_robustness_report=replay_report,
            min_required_sample_count=_diagnostic_sample_threshold_from_replay_report(replay_report),
        )
        _, _, performance_source_ids = performance_inputs_from_runtime_sample_history(
            candidate_scorecard=alternative_scorecard,
            runtime_sample_history=history,
            root=root,
        )
        diagnostic = _bind_performance_sources_to_overfit_diagnostic(
            diagnostic,
            performance_source_ids=performance_source_ids,
        )
        diagnostic_errors = _overfit_diagnostic_errors(diagnostic)
        if diagnostic_errors:
            gate_status = "BLOCKED"
            gate_blocker_code = "SCHEMA_IDENTITY_MISMATCH"
            gate_message = "candidate overfit diagnostic failed contract validation"
        elif diagnostic.get("robustness_eligible") is not True:
            diagnostic_blockers = [
                str(blocker.get("code"))
                for blocker in diagnostic.get("blockers") or []
                if isinstance(blocker, dict) and blocker.get("code")
            ]
            gate_status = "BLOCKED"
            gate_blocker_code = diagnostic_blockers[0] if diagnostic_blockers else "ROBUSTNESS_MATURITY_BLOCKED"
            gate_message = (
                "candidate public replay collection passed, but OOS, walk-forward, bootstrap, "
                "and closed-trade profitability gates are not robust enough for alternative validation"
            )
        diagnostic_blocker_codes = [
            str(blocker.get("code"))
            for blocker in diagnostic.get("blockers") or []
            if isinstance(blocker, dict) and blocker.get("code")
        ]

    return {
        "status": gate_status,
        "blocker_code": gate_blocker_code,
        "message": gate_message,
        "candidate_id": candidate_id,
        "candidate_index": candidate_index,
        "symbol": symbol,
        "contract_status": replay_validation.status,
        "contract_blocker_code": replay_validation.blocker_code,
        "report_path": _relative_path(report_path, root),
        "replay_status": replay_status,
        "sample_count": int(replay_report.get("sample_count") or 0),
        "primary_blocker_code": replay_report.get("primary_blocker_code"),
        "replay_closed_trade_sample_count": int(replay_report.get("replay_closed_trade_sample_count") or 0),
        "replay_closed_trade_status": replay_report.get("replay_closed_trade_status") or "UNTESTED",
        **closed_trade_maturity,
        "replay_strategy_exit_policy_sample_count": int(
            replay_report.get("replay_strategy_exit_policy_sample_count") or 0
        ),
        "replay_strategy_exit_policy_status": replay_report.get("replay_strategy_exit_policy_status") or "UNTESTED",
        "replay_strategy_exit_policy_mismatch_count": int(
            replay_report.get("replay_strategy_exit_policy_mismatch_count") or 0
        ),
        "replay_profit_factor": _safe_float(replay_report.get("replay_profit_factor")),
        "replay_profit_factor_status": replay_report.get("replay_profit_factor_status") or "UNTESTED",
        "replay_realized_vs_expected_edge_bps": _safe_float(
            replay_report.get("replay_realized_vs_expected_edge_bps")
        ),
        "replay_realized_vs_expected_edge_status": replay_report.get("replay_realized_vs_expected_edge_status")
        or "UNTESTED",
        "replay_execution_cost_delta_bps": _safe_float(replay_report.get("replay_execution_cost_delta_bps")),
        "replay_execution_cost_status": replay_report.get("replay_execution_cost_status") or "UNTESTED",
        "robustness_eligible": bool(diagnostic.get("robustness_eligible")) if diagnostic else False,
        "oos_status": str(diagnostic.get("oos_status") or "UNTESTED") if diagnostic else "UNTESTED",
        "walk_forward_status": str(diagnostic.get("walk_forward_status") or "UNTESTED") if diagnostic else "UNTESTED",
        "bootstrap_status": str(diagnostic.get("bootstrap_status") or "UNTESTED") if diagnostic else "UNTESTED",
        "overfit_status": str(diagnostic.get("overfit_status") or "UNTESTED") if diagnostic else "UNTESTED",
        "diagnostic_blocker_codes": diagnostic_blocker_codes,
        "report": replay_report,
        "scorecard": alternative_scorecard,
        "diagnostic": diagnostic,
        "source_runtime_cycle_report": source_runtime,
    }


def _build_and_write_alternative_public_replay(
    *,
    root: Path,
    session_id: str,
    candidate_generation_report: dict[str, Any],
    history: dict[str, Any],
    runtime_cycle_report: dict[str, Any] | None,
    candidate_discovery_runtime: dict[str, Any] | None,
    target_count: int,
    page_size: int,
    timeout_seconds: float,
    max_replay_windows: int,
    min_required_sample_count: int,
    candidate_limit: int,
    public_replay_history_fetcher: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if candidate_generation_report.get("generation_status") != "ALTERNATIVE_REVIEW_READY":
        return _alternative_replay_context(
            status="NOT_REQUIRED",
            blocker_code=None,
            message="alternative public replay is not required until a bounded candidate is review-ready",
        )
    review_ready_items = _review_ready_candidate_items(candidate_generation_report, limit=candidate_limit)
    if not review_ready_items:
        return _alternative_replay_context(
            status="BLOCKED",
            blocker_code="STRATEGY_NOT_ELIGIBLE",
            message="alternative public replay found no bounded review-ready candidate",
        )

    market_data_cache: dict[str, dict[str, Any]] = {}
    evaluations = [
        _build_alternative_public_replay_evaluation(
            root=root,
            session_id=session_id,
            item=item,
            candidate_index=index,
            history=history,
            runtime_cycle_report=runtime_cycle_report,
            candidate_discovery_runtime=candidate_discovery_runtime,
            target_count=target_count,
            page_size=page_size,
            timeout_seconds=timeout_seconds,
            max_replay_windows=max_replay_windows,
            min_required_sample_count=min_required_sample_count,
            market_data_cache=market_data_cache,
            public_replay_history_fetcher=public_replay_history_fetcher,
        )
        for index, item in enumerate(review_ready_items, start=1)
    ]
    replay_passed = [item for item in evaluations if item.get("status") == "PASS" and isinstance(item.get("report"), dict)]
    if not replay_passed:
        first = max(evaluations, key=_alternative_replay_selection_priority)
        first_closed_trades = int(first.get("replay_closed_trade_sample_count") or 0)
        first_policy_samples = int(first.get("replay_strategy_exit_policy_sample_count") or 0)
        first_closed_trade_maturity = _replay_closed_trade_maturity(
            first.get("report") if isinstance(first.get("report"), dict) else first
        )
        selection_reason = (
            "BEST_CLOSED_TRADE_REPLAY_BLOCKED"
            if first_closed_trades > 0 or first_policy_samples > 0
            else "NO_PUBLIC_REPLAY_PASS"
        )
        return _alternative_replay_context(
            status="BLOCKED",
            blocker_code=str(first.get("blocker_code") or "DATA_QUALITY_INSUFFICIENT"),
            message="no bounded alternative candidate passed public replay contract and replay gates",
            candidate_id=str(first.get("candidate_id") or ""),
            symbol=str(first.get("symbol") or ""),
            contract_status=str(first.get("contract_status") or first.get("status") or "BLOCKED"),
            contract_blocker_code=first.get("contract_blocker_code"),
            report_path=first.get("report_path"),
            replay_status=str(first.get("replay_status") or "BLOCKED"),
            sample_count=int(first.get("sample_count") or 0),
            primary_blocker_code=first.get("primary_blocker_code"),
            replay_closed_trade_sample_count=first_closed_trades,
            replay_closed_trade_status=str(first.get("replay_closed_trade_status") or "UNTESTED"),
            min_required_closed_trade_sample_count=int(
                first.get("min_required_closed_trade_sample_count")
                or first_closed_trade_maturity["min_required_closed_trade_sample_count"]
            ),
            replay_closed_trade_deficit=int(
                first.get("replay_closed_trade_deficit")
                if first.get("replay_closed_trade_deficit") is not None
                else first_closed_trade_maturity["replay_closed_trade_deficit"]
            ),
            replay_closed_trade_maturity_status=str(
                first.get("replay_closed_trade_maturity_status")
                or first_closed_trade_maturity["replay_closed_trade_maturity_status"]
            ),
            replay_closed_trade_maturity_blocker_code=(
                first.get("replay_closed_trade_maturity_blocker_code")
                or first_closed_trade_maturity["replay_closed_trade_maturity_blocker_code"]
            ),
            replay_strategy_exit_policy_sample_count=first_policy_samples,
            replay_strategy_exit_policy_status=str(first.get("replay_strategy_exit_policy_status") or "UNTESTED"),
            replay_strategy_exit_policy_mismatch_count=int(
                first.get("replay_strategy_exit_policy_mismatch_count") or 0
            ),
            replay_profit_factor=_safe_float(first.get("replay_profit_factor")),
            replay_profit_factor_status=str(first.get("replay_profit_factor_status") or "UNTESTED"),
            replay_realized_vs_expected_edge_bps=_safe_float(first.get("replay_realized_vs_expected_edge_bps")),
            replay_realized_vs_expected_edge_status=str(
                first.get("replay_realized_vs_expected_edge_status") or "UNTESTED"
            ),
            replay_execution_cost_delta_bps=_safe_float(first.get("replay_execution_cost_delta_bps")),
            replay_execution_cost_status=str(first.get("replay_execution_cost_status") or "UNTESTED"),
            report=first.get("report") if isinstance(first.get("report"), dict) else None,
            scorecard=first.get("scorecard") if isinstance(first.get("scorecard"), dict) else None,
            source_runtime_cycle_report=first.get("source_runtime_cycle_report")
            if isinstance(first.get("source_runtime_cycle_report"), dict)
            else None,
            candidate_review_evaluations=_public_candidate_review_evaluations(evaluations),
            candidate_review_evaluated_count=len(evaluations),
            candidate_review_robust_candidate_count=0,
            candidate_review_selection_reason=selection_reason,
        )

    selected = max(replay_passed, key=_alternative_replay_selection_priority)
    selected_closed_trade_maturity = _replay_closed_trade_maturity(
        selected.get("report") if isinstance(selected.get("report"), dict) else selected
    )
    robust_count = sum(1 for item in replay_passed if item.get("robustness_eligible") is True)
    selection_reason = "ROBUSTNESS_ELIGIBLE_SELECTED" if selected.get("robustness_eligible") is True else "BEST_AVAILABLE_REPLAY_SELECTED"
    return _alternative_replay_context(
        status=str(selected.get("status") or "BLOCKED"),
        blocker_code=selected.get("blocker_code"),
        message=f"bounded multi-candidate public replay selected {selected.get('candidate_id')} by robustness-aware priority",
        contract_status=str(selected.get("contract_status") or selected.get("status") or "BLOCKED"),
        contract_blocker_code=selected.get("contract_blocker_code"),
        report_path=selected.get("report_path"),
        candidate_id=str(selected.get("candidate_id") or ""),
        symbol=str(selected.get("symbol") or ""),
        replay_status=str(selected.get("replay_status") or "BLOCKED"),
        sample_count=int(selected.get("sample_count") or 0),
        primary_blocker_code=selected.get("primary_blocker_code"),
        replay_closed_trade_sample_count=int(selected.get("replay_closed_trade_sample_count") or 0),
        replay_closed_trade_status=str(selected.get("replay_closed_trade_status") or "UNTESTED"),
        min_required_closed_trade_sample_count=int(
            selected.get("min_required_closed_trade_sample_count")
            or selected_closed_trade_maturity["min_required_closed_trade_sample_count"]
        ),
        replay_closed_trade_deficit=int(
            selected.get("replay_closed_trade_deficit")
            if selected.get("replay_closed_trade_deficit") is not None
            else selected_closed_trade_maturity["replay_closed_trade_deficit"]
        ),
        replay_closed_trade_maturity_status=str(
            selected.get("replay_closed_trade_maturity_status")
            or selected_closed_trade_maturity["replay_closed_trade_maturity_status"]
        ),
        replay_closed_trade_maturity_blocker_code=(
            selected.get("replay_closed_trade_maturity_blocker_code")
            or selected_closed_trade_maturity["replay_closed_trade_maturity_blocker_code"]
        ),
        replay_strategy_exit_policy_sample_count=int(selected.get("replay_strategy_exit_policy_sample_count") or 0),
        replay_strategy_exit_policy_status=str(selected.get("replay_strategy_exit_policy_status") or "UNTESTED"),
        replay_strategy_exit_policy_mismatch_count=int(
            selected.get("replay_strategy_exit_policy_mismatch_count") or 0
        ),
        replay_profit_factor=_safe_float(selected.get("replay_profit_factor")),
        replay_profit_factor_status=str(selected.get("replay_profit_factor_status") or "UNTESTED"),
        replay_realized_vs_expected_edge_bps=_safe_float(selected.get("replay_realized_vs_expected_edge_bps")),
        replay_realized_vs_expected_edge_status=str(
            selected.get("replay_realized_vs_expected_edge_status") or "UNTESTED"
        ),
        replay_execution_cost_delta_bps=_safe_float(selected.get("replay_execution_cost_delta_bps")),
        replay_execution_cost_status=str(selected.get("replay_execution_cost_status") or "UNTESTED"),
        report=selected.get("report") if isinstance(selected.get("report"), dict) else None,
        scorecard=selected.get("scorecard") if isinstance(selected.get("scorecard"), dict) else None,
        source_runtime_cycle_report=selected.get("source_runtime_cycle_report")
        if isinstance(selected.get("source_runtime_cycle_report"), dict)
        else None,
        candidate_review_evaluations=_public_candidate_review_evaluations(evaluations),
        candidate_review_evaluated_count=len(evaluations),
        candidate_review_robust_candidate_count=robust_count,
        candidate_review_selection_reason=selection_reason,
    )


def _build_and_write_alternative_review_scorecard(
    *,
    root: Path,
    history: dict[str, Any],
    alternative_replay_context: dict[str, Any],
) -> dict[str, Any]:
    replay_report = alternative_replay_context.get("report")
    source_runtime = alternative_replay_context.get("source_runtime_cycle_report")
    base_scorecard = alternative_replay_context.get("scorecard")
    if not isinstance(replay_report, dict):
        return {
            "status": "NOT_REQUIRED",
            "blocker_code": None,
            "message": "alternative review scorecard requires an alternative public replay report",
            "path": None,
            "overfit_diagnostic_path": None,
            "candidate_id": alternative_replay_context.get("candidate_id"),
            "ranking_eligible": False,
            "blocker_codes": [],
            "replay_closed_trade_sample_count": 0,
            "min_required_closed_trade_sample_count": 0,
            "replay_closed_trade_deficit": 0,
            "replay_closed_trade_maturity_status": "UNTESTED",
            "replay_strategy_exit_policy_sample_count": 0,
            "replay_profit_factor": 0.0,
            "replay_performance_scope": "NOT_RUN",
        }
    replay_sample_count = int(replay_report.get("sample_count") or 0)
    replay_closed_trade_count = int(replay_report.get("replay_closed_trade_sample_count") or 0)
    if alternative_replay_context.get("status") != "PASS" and replay_sample_count <= 0 and replay_closed_trade_count <= 0:
        return {
            "status": "NOT_REQUIRED",
            "blocker_code": None,
            "message": "alternative review scorecard is not written until public replay emits sample rows",
            "path": None,
            "overfit_diagnostic_path": None,
            "candidate_id": alternative_replay_context.get("candidate_id"),
            "ranking_eligible": False,
            "blocker_codes": [],
            "replay_closed_trade_sample_count": 0,
            "min_required_closed_trade_sample_count": 0,
            "replay_closed_trade_deficit": 0,
            "replay_closed_trade_maturity_status": "UNTESTED",
            "replay_strategy_exit_policy_sample_count": 0,
            "replay_profit_factor": 0.0,
            "replay_performance_scope": "NOT_RUN",
        }
    if not isinstance(source_runtime, dict) or not isinstance(base_scorecard, dict):
        return {
            "status": "BLOCKED",
            "blocker_code": "SNAPSHOT_SCOPE_MISMATCH",
            "message": "alternative review scorecard requires the source runtime and base scorecard",
            "path": None,
            "overfit_diagnostic_path": None,
            "candidate_id": alternative_replay_context.get("candidate_id"),
            "ranking_eligible": False,
            "blocker_codes": ["SNAPSHOT_SCOPE_MISMATCH"],
            "replay_closed_trade_sample_count": 0,
            "min_required_closed_trade_sample_count": 0,
            "replay_closed_trade_deficit": 0,
            "replay_closed_trade_maturity_status": "UNTESTED",
            "replay_strategy_exit_policy_sample_count": 0,
            "replay_profit_factor": 0.0,
            "replay_performance_scope": "NOT_RUN",
        }
    diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
        replay_robustness_report=replay_report,
        min_required_sample_count=_diagnostic_sample_threshold_from_replay_report(replay_report),
    )
    performance_statuses, performance_metrics, performance_source_ids = performance_inputs_from_runtime_sample_history(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
    )
    diagnostic = _bind_performance_sources_to_overfit_diagnostic(
        diagnostic,
        performance_source_ids=performance_source_ids,
    )
    diagnostic_errors = _overfit_diagnostic_errors(diagnostic)
    if diagnostic_errors:
        return {
            "status": "BLOCKED",
            "blocker_code": "SCHEMA_IDENTITY_MISMATCH",
            "message": "alternative review overfit diagnostic failed contract validation",
            "path": None,
            "overfit_diagnostic_path": None,
            "candidate_id": base_scorecard.get("candidate_id"),
            "ranking_eligible": False,
            "blocker_codes": ["SCHEMA_IDENTITY_MISMATCH"],
            "replay_closed_trade_sample_count": 0,
            "min_required_closed_trade_sample_count": 0,
            "replay_closed_trade_deficit": 0,
            "replay_closed_trade_maturity_status": "UNTESTED",
            "replay_strategy_exit_policy_sample_count": 0,
            "replay_profit_factor": 0.0,
            "replay_performance_scope": "NOT_RUN",
        }
    robustness_statuses, robustness_source_ids = robustness_inputs_from_overfit_diagnostic(diagnostic)
    closed_trade_maturity = _replay_closed_trade_maturity(replay_report)
    review_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        source_runtime,
        candidate_id=str(base_scorecard["candidate_id"]),
        robustness_statuses=robustness_statuses,
        robustness_source_evidence_ids=robustness_source_ids,
        performance_statuses=performance_statuses,
        performance_metrics=performance_metrics,
        performance_source_evidence_ids=performance_source_ids,
    )
    review_scorecard.update(
        {
            "replay_closed_trade_sample_count": int(replay_report.get("replay_closed_trade_sample_count") or 0),
            "replay_closed_trade_status": replay_report.get("replay_closed_trade_status") or "UNTESTED",
            "min_required_closed_trade_sample_count": closed_trade_maturity["min_required_closed_trade_sample_count"],
            "replay_closed_trade_deficit": closed_trade_maturity["replay_closed_trade_deficit"],
            "replay_closed_trade_maturity_status": closed_trade_maturity["replay_closed_trade_maturity_status"],
            "replay_closed_trade_maturity_blocker_code": closed_trade_maturity[
                "replay_closed_trade_maturity_blocker_code"
            ],
            "replay_strategy_exit_policy_sample_count": int(
                replay_report.get("replay_strategy_exit_policy_sample_count") or 0
            ),
            "replay_strategy_exit_policy_match_count": int(
                replay_report.get("replay_strategy_exit_policy_match_count") or 0
            ),
            "replay_strategy_exit_policy_mismatch_count": int(
                replay_report.get("replay_strategy_exit_policy_mismatch_count") or 0
            ),
            "replay_strategy_exit_policy_status": replay_report.get("replay_strategy_exit_policy_status") or "UNTESTED",
            "replay_strategy_exit_reason_counts": [
                {
                    "reason_code": str(item.get("reason_code") or ""),
                    "count": _safe_int(item.get("count")),
                }
                for item in replay_report.get("replay_strategy_exit_reason_counts", [])
                if isinstance(item, dict) and item.get("reason_code")
            ],
            "replay_profit_factor": _safe_float(replay_report.get("replay_profit_factor")),
            "replay_profit_factor_status": replay_report.get("replay_profit_factor_status") or "UNTESTED",
            "replay_max_drawdown_bps": _safe_float(replay_report.get("replay_max_drawdown_bps")),
            "replay_realized_vs_expected_edge_bps": _safe_float(
                replay_report.get("replay_realized_vs_expected_edge_bps")
            ),
            "replay_realized_vs_expected_edge_status": replay_report.get("replay_realized_vs_expected_edge_status")
            or "UNTESTED",
            "replay_fill_quality_score": _safe_float(replay_report.get("replay_fill_quality_score")),
            "replay_execution_cost_delta_bps": _safe_float(replay_report.get("replay_execution_cost_delta_bps")),
            "replay_execution_cost_status": replay_report.get("replay_execution_cost_status") or "UNTESTED",
            "replay_performance_scope": replay_report.get("replay_performance_scope")
            or "PUBLIC_REPLAY_ONLY_NOT_PAPER_RANKING",
        }
    )
    replay_context_status = str(alternative_replay_context.get("status") or "BLOCKED")
    replay_context_blocker_code = str(
        alternative_replay_context.get("blocker_code")
        or replay_report.get("primary_blocker_code")
        or "PUBLIC_REPLAY_ROBUSTNESS_FAILED"
    )
    if replay_context_status != "PASS":
        blockers = [item for item in review_scorecard.get("blockers", []) if isinstance(item, dict)]
        if replay_context_blocker_code not in {str(item.get("code") or "") for item in blockers}:
            blockers.append(
                {
                    "code": replay_context_blocker_code,
                    "severity": "HIGH",
                    "message": "alternative public replay remains blocked; scorecard is evidence-only and ranking remains disabled",
                }
            )
        review_scorecard["blockers"] = blockers
        review_scorecard["ranking_eligible"] = False
        review_scorecard["scorecard_scope"] = "PAPER_EVIDENCE_COLLECTION_ONLY"
    scorecard_errors = _candidate_scorecard_net_ev_errors(review_scorecard)
    if scorecard_errors:
        return {
            "status": "BLOCKED",
            "blocker_code": "SCORECARD_SCHEMA_INVALID",
            "message": "alternative review scorecard failed contract validation",
            "path": None,
            "overfit_diagnostic_path": None,
            "candidate_id": base_scorecard.get("candidate_id"),
            "ranking_eligible": False,
            "blocker_codes": ["SCORECARD_SCHEMA_INVALID"],
            "replay_closed_trade_sample_count": 0,
            "min_required_closed_trade_sample_count": 0,
            "replay_closed_trade_deficit": 0,
            "replay_closed_trade_maturity_status": "UNTESTED",
            "replay_strategy_exit_policy_sample_count": 0,
            "replay_profit_factor": 0.0,
            "replay_performance_scope": "NOT_RUN",
        }
    snapshot_path = write_upbit_paper_candidate_scorecard_snapshot(root=root, scorecard=review_scorecard)
    diagnostic_snapshot_path = write_overfit_diagnostic_report_snapshot(root=root, report=diagnostic)
    review_status = "PASS" if replay_context_status == "PASS" else "BLOCKED"
    review_blocker_code = None if review_status == "PASS" else replay_context_blocker_code
    return {
        "status": review_status,
        "blocker_code": review_blocker_code,
        "message": (
            "alternative review scorecard and overfit diagnostic snapshots written from passed public replay and runtime-bound performance inputs"
            if review_status == "PASS"
            else "alternative review scorecard snapshot written as blocked, evidence-only public replay input"
        ),
        "path": _relative_path(snapshot_path, root),
        "overfit_diagnostic_path": _relative_path(diagnostic_snapshot_path, root),
        "candidate_id": review_scorecard["candidate_id"],
        "ranking_eligible": bool(review_scorecard["ranking_eligible"]),
        "blocker_codes": [blocker["code"] for blocker in review_scorecard["blockers"]],
        "replay_closed_trade_sample_count": int(review_scorecard["replay_closed_trade_sample_count"]),
        "min_required_closed_trade_sample_count": int(
            review_scorecard["min_required_closed_trade_sample_count"]
        ),
        "replay_closed_trade_deficit": int(review_scorecard["replay_closed_trade_deficit"]),
        "replay_closed_trade_maturity_status": str(review_scorecard["replay_closed_trade_maturity_status"]),
        "replay_strategy_exit_policy_sample_count": int(review_scorecard["replay_strategy_exit_policy_sample_count"]),
        "replay_profit_factor": _safe_float(review_scorecard["replay_profit_factor"]),
        "replay_performance_scope": str(review_scorecard["replay_performance_scope"]),
    }


def _select_scorecard_runtime_sample(history: dict[str, Any]) -> tuple[dict[str, Any], str]:
    samples = [sample for sample in history.get("samples") or [] if isinstance(sample, dict)]
    if not samples:
        raise ValueError("no PAPER runtime samples are available for candidate scorecard input")

    active_scope = history.get("active_candidate_scope")
    active_scope = active_scope if isinstance(active_scope, dict) else {}
    active_cycle_hash = str(active_scope.get("latest_runtime_cycle_hash") or "")
    active_cycle_id = str(active_scope.get("latest_cycle_id") or "")
    active_candidate_decision = str(active_scope.get("latest_candidate_decision") or "")
    active_final_decision = str(active_scope.get("latest_final_decision") or "")
    evidence_bearing_scope = (
        active_scope
        and (
            active_candidate_decision == "PAPER_ENTRY_REVIEW"
            or active_final_decision in {"ENTER_LONG", "EXIT_POSITION", "REDUCE_POSITION"}
            or _safe_int(active_scope.get("entry_reason_count")) > 0
            or _safe_int(active_scope.get("exit_reason_count")) > 0
        )
    )
    if evidence_bearing_scope and (active_cycle_hash or active_cycle_id):
        for sample in reversed(samples):
            sample_hash = str(sample.get("source_runtime_cycle_hash") or "")
            sample_path = str(sample.get("source_runtime_cycle_path") or "")
            if (active_cycle_hash and sample_hash == active_cycle_hash) or (
                active_cycle_id and active_cycle_id in sample_path
            ):
                return sample, "ACTIVE_CANDIDATE_SCOPE"

    return samples[-1], "LATEST_RUNTIME_SAMPLE"


def build_current_upbit_paper_candidate_scorecard(
    *,
    root: Path,
    session_id: str,
    attempt_public_discovery: bool = False,
    candidate_discovery_symbol_limit: int = 12,
    candidate_discovery_timeout_seconds: float = 3.0,
    alternative_replay_target_count: int = 420,
    alternative_replay_page_size: int = 200,
    alternative_replay_timeout_seconds: float = 3.0,
    alternative_replay_max_windows: int = 420,
    alternative_replay_min_required_sample_count: int = 300,
    alternative_replay_candidate_limit: int = 5,
    market_symbols_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_ticker_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_candle_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_replay_history_fetcher: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
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

    try:
        scorecard_sample, scorecard_runtime_selection_source = _select_scorecard_runtime_sample(history)
    except ValueError as exc:
        return _blocked_result(str(exc), "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    runtime_path = root / scorecard_sample["source_runtime_cycle_path"]
    runtime = _load_json(runtime_path)
    runtime_result = validate_upbit_paper_runtime_cycle_report(runtime)
    if runtime_result.status != "PASS":
        return _blocked_result(
            runtime_result.message,
            runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH",
            source_runtime_cycle_path=str(scorecard_sample.get("source_runtime_cycle_path")),
            scorecard_runtime_selection_source=scorecard_runtime_selection_source,
        )
    if runtime.get("cycle_hash") != scorecard_sample.get("source_runtime_cycle_hash"):
        return _blocked_result(
            "selected PAPER runtime sample hash does not match the runtime cycle artifact",
            "RECONCILIATION_REQUIRED",
            source_runtime_cycle_path=str(scorecard_sample.get("source_runtime_cycle_path")),
            scorecard_runtime_selection_source=scorecard_runtime_selection_source,
        )

    base_scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
    loaded_replay_robustness_report = load_public_replay_robustness_report(
        root=root,
        session_id=session_id,
        candidate_id=str(base_scorecard.get("candidate_id") or ""),
    )
    replay_robustness_report = None
    replay_robustness_contract_status = "MISSING"
    replay_robustness_contract_blocker_code = "MEASUREMENT_MISSING"
    if isinstance(loaded_replay_robustness_report, dict):
        replay_validation = validate_public_replay_robustness_report(
            loaded_replay_robustness_report,
            candidate_scorecard=base_scorecard,
        )
        replay_robustness_contract_status = replay_validation.status
        replay_robustness_contract_blocker_code = replay_validation.blocker_code
        if replay_validation.status == "PASS":
            replay_robustness_report = loaded_replay_robustness_report
    diagnostic_kwargs = {
        "candidate_scorecard": base_scorecard,
        "runtime_sample_history": history,
        "root": root,
    }
    if replay_robustness_report is not None:
        diagnostic_kwargs["replay_robustness_report"] = replay_robustness_report
        diagnostic_kwargs["min_required_sample_count"] = _diagnostic_sample_threshold_from_replay_report(
            replay_robustness_report
        )
    diagnostic = overfit_diagnostic_from_upbit_paper_runtime(**diagnostic_kwargs)
    performance_statuses, performance_metrics, performance_source_ids = performance_inputs_from_runtime_sample_history(
        candidate_scorecard=base_scorecard,
        runtime_sample_history=history,
        root=root,
    )
    diagnostic = _bind_performance_sources_to_overfit_diagnostic(
        diagnostic,
        performance_source_ids=performance_source_ids,
    )
    diagnostic_errors = _overfit_diagnostic_errors(diagnostic)
    if diagnostic_errors:
        return _blocked_result(
            "overfit diagnostic failed contract validation",
            "SCHEMA_IDENTITY_MISMATCH",
            diagnostic_errors=diagnostic_errors,
        )
    public_replay_robustness_context = _public_replay_robustness_context(
        loaded_report=loaded_replay_robustness_report,
        contract_status=replay_robustness_contract_status,
        contract_blocker_code=replay_robustness_contract_blocker_code,
        diagnostic=diagnostic,
    )

    robustness_statuses, robustness_source_ids = robustness_inputs_from_overfit_diagnostic(diagnostic)
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
    candidate_discovery_runtime: dict[str, Any] | None = None
    candidate_discovery_context = _candidate_discovery_context(
        status="NOT_REQUESTED",
        blocker_code=None,
        message="bounded public candidate discovery was not requested",
        symbol_count=0,
    )
    alternative_replay_context = _alternative_replay_context(
        status="NOT_REQUIRED",
        blocker_code=None,
        message="alternative public replay is not required until a bounded candidate is review-ready",
    )
    candidate_generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
        runtime,
        candidate_scorecard=scorecard,
    )
    current_alternative_count = _safe_int(candidate_generation_report.get("alternative_candidate_count"))
    min_candidate_review_pool = max(2, min(_safe_int(alternative_replay_candidate_limit), 12))
    discovery_needed_for_review_pool = (
        candidate_generation_report.get("selected_candidate_retired_for_ranking") is True
        and (
            candidate_generation_report.get("generation_status") == "NO_ALTERNATIVE_READY"
            or current_alternative_count < min_candidate_review_pool
        )
    )
    if attempt_public_discovery and discovery_needed_for_review_pool:
        candidate_discovery_runtime, candidate_discovery_context = _build_bounded_public_discovery_runtime_cycle(
            session_id=session_id,
            symbol_limit=candidate_discovery_symbol_limit,
            timeout_seconds=candidate_discovery_timeout_seconds,
            market_symbols_fetcher=market_symbols_fetcher,
            public_ticker_fetcher=public_ticker_fetcher,
            public_candle_fetcher=public_candle_fetcher,
        )
        if candidate_discovery_runtime is not None:
            candidate_generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
                runtime,
                candidate_scorecard=scorecard,
                additional_runtime_cycle_reports=[candidate_discovery_runtime],
            )
    generation_status, generation_message, generation_blocker = validate_candidate_generation_report(
        candidate_generation_report,
        candidate_scorecard=scorecard,
    )
    if generation_status != "PASS":
        return _blocked_result(
            "candidate generation report failed contract validation",
            generation_blocker or "SCHEMA_IDENTITY_MISMATCH",
            candidate_generation_errors=[generation_message],
        )
    alternative_replay_context = _build_and_write_alternative_public_replay(
        root=root,
        session_id=session_id,
        candidate_generation_report=candidate_generation_report,
        history=history,
        runtime_cycle_report=runtime,
        candidate_discovery_runtime=candidate_discovery_runtime,
        target_count=alternative_replay_target_count,
        page_size=alternative_replay_page_size,
        timeout_seconds=alternative_replay_timeout_seconds,
        max_replay_windows=alternative_replay_max_windows,
        min_required_sample_count=alternative_replay_min_required_sample_count,
        candidate_limit=alternative_replay_candidate_limit,
        public_replay_history_fetcher=public_replay_history_fetcher,
    )
    if isinstance(alternative_replay_context.get("report"), dict):
        candidate_generation_report = candidate_generation_report_from_upbit_paper_runtime_cycle(
            runtime,
            candidate_scorecard=scorecard,
            additional_runtime_cycle_reports=(
                [candidate_discovery_runtime]
                if candidate_discovery_runtime is not None
                else None
            ),
            best_alternative_public_replay_report=alternative_replay_context["report"],
            preferred_alternative_candidate_id=str(alternative_replay_context.get("candidate_id") or ""),
        )
        generation_status, generation_message, generation_blocker = validate_candidate_generation_report(
            candidate_generation_report,
            candidate_scorecard=scorecard,
        )
        if generation_status != "PASS":
            return _blocked_result(
                "candidate generation report failed post-replay contract validation",
                generation_blocker or "SCHEMA_IDENTITY_MISMATCH",
                candidate_generation_errors=[generation_message],
            )

    alternative_review_scorecard_context = _build_and_write_alternative_review_scorecard(
        root=root,
        history=history,
        alternative_replay_context=alternative_replay_context,
    )
    paper_shadow_binding = _paper_shadow_scorecard_binding(
        root=root,
        session_id=session_id,
        scorecard=scorecard,
    )
    history_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
    diagnostic_path = write_overfit_diagnostic_report(root=root, report=diagnostic)
    scorecard_path = write_upbit_paper_candidate_scorecard(root=root, scorecard=scorecard)
    candidate_generation_path = write_upbit_paper_candidate_generation_report(
        root=root,
        report=candidate_generation_report,
    )
    candidate_discovery_runtime_path = None
    if candidate_discovery_runtime is not None:
        candidate_discovery_runtime_path = _candidate_discovery_runtime_path(root, session_id)
        durable_atomic_write_json(candidate_discovery_runtime_path, candidate_discovery_runtime)
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
        "candidate_generation_report_path": _relative_path(candidate_generation_path, root),
        "candidate_discovery_runtime_cycle_path": (
            _relative_path(candidate_discovery_runtime_path, root)
            if candidate_discovery_runtime_path is not None
            else None
        ),
        "candidate_discovery_status": candidate_discovery_context["status"],
        "candidate_discovery_blocker_code": candidate_discovery_context["blocker_code"],
        "candidate_discovery_message": candidate_discovery_context["message"],
        "candidate_discovery_symbol_count": candidate_discovery_context["symbol_count"],
        "candidate_discovery_ranked_symbol_count": candidate_discovery_context["ranked_symbol_count"],
        "candidate_discovery_eligible_symbol_count": candidate_discovery_context["eligible_symbol_count"],
        "candidate_discovery_adaptive_expansion_attempted": candidate_discovery_context[
            "adaptive_expansion_attempted"
        ],
        "candidate_discovery_initial_symbol_count": candidate_discovery_context["initial_symbol_count"],
        "candidate_discovery_expanded_symbol_count": candidate_discovery_context["expanded_symbol_count"],
        "candidate_discovery_max_expanded_symbol_count": candidate_discovery_context["max_expanded_symbol_count"],
        "candidate_discovery_evaluated_candidate_count": candidate_discovery_context["evaluated_candidate_count"],
        "candidate_discovery_paper_entry_review_candidate_count": candidate_discovery_context[
            "paper_entry_review_candidate_count"
        ],
        "candidate_discovery_blocked_candidate_count": candidate_discovery_context["blocked_candidate_count"],
        "candidate_discovery_strategy_family_candidate_counts": candidate_discovery_context[
            "strategy_family_candidate_counts"
        ],
        "candidate_discovery_strategy_family_review_ready_counts": candidate_discovery_context[
            "strategy_family_review_ready_counts"
        ],
        "candidate_discovery_strategy_family_blocked_counts": candidate_discovery_context[
            "strategy_family_blocked_counts"
        ],
        "candidate_discovery_no_trade_reason_counts": candidate_discovery_context["no_trade_reason_counts"],
        "candidate_discovery_strategy_policy_reason_counts": candidate_discovery_context["strategy_policy_reason_counts"],
        "candidate_discovery_entry_block_reason_counts": candidate_discovery_context["entry_block_reason_counts"],
        "candidate_discovery_top_blocked_symbols": candidate_discovery_context["top_blocked_symbols"],
        "alternative_public_replay_status": alternative_replay_context["status"],
        "alternative_public_replay_blocker_code": alternative_replay_context["blocker_code"],
        "alternative_public_replay_message": alternative_replay_context["message"],
        "alternative_public_replay_contract_status": alternative_replay_context["contract_status"],
        "alternative_public_replay_contract_blocker_code": alternative_replay_context["contract_blocker_code"],
        "alternative_public_replay_report_path": alternative_replay_context["report_path"],
        "alternative_public_replay_candidate_id": alternative_replay_context["candidate_id"],
        "alternative_public_replay_symbol": alternative_replay_context["symbol"],
        "alternative_public_replay_replay_status": alternative_replay_context["replay_status"],
        "alternative_public_replay_sample_count": alternative_replay_context["sample_count"],
        "alternative_public_replay_primary_blocker_code": alternative_replay_context["primary_blocker_code"],
        "alternative_public_replay_closed_trade_sample_count": alternative_replay_context[
            "replay_closed_trade_sample_count"
        ],
        "alternative_public_replay_closed_trade_status": alternative_replay_context["replay_closed_trade_status"],
        "alternative_public_replay_min_closed_trade_sample_count": alternative_replay_context[
            "min_required_closed_trade_sample_count"
        ],
        "alternative_public_replay_closed_trade_deficit": alternative_replay_context[
            "replay_closed_trade_deficit"
        ],
        "alternative_public_replay_closed_trade_maturity_status": alternative_replay_context[
            "replay_closed_trade_maturity_status"
        ],
        "alternative_public_replay_closed_trade_maturity_blocker_code": alternative_replay_context[
            "replay_closed_trade_maturity_blocker_code"
        ],
        "alternative_public_replay_strategy_exit_policy_sample_count": alternative_replay_context[
            "replay_strategy_exit_policy_sample_count"
        ],
        "alternative_public_replay_strategy_exit_policy_status": alternative_replay_context[
            "replay_strategy_exit_policy_status"
        ],
        "alternative_public_replay_strategy_exit_policy_mismatch_count": alternative_replay_context[
            "replay_strategy_exit_policy_mismatch_count"
        ],
        "alternative_public_replay_profit_factor": alternative_replay_context["replay_profit_factor"],
        "alternative_public_replay_profit_factor_status": alternative_replay_context["replay_profit_factor_status"],
        "alternative_public_replay_realized_vs_expected_edge_bps": alternative_replay_context[
            "replay_realized_vs_expected_edge_bps"
        ],
        "alternative_public_replay_realized_vs_expected_edge_status": alternative_replay_context[
            "replay_realized_vs_expected_edge_status"
        ],
        "alternative_public_replay_execution_cost_delta_bps": alternative_replay_context[
            "replay_execution_cost_delta_bps"
        ],
        "alternative_public_replay_execution_cost_status": alternative_replay_context[
            "replay_execution_cost_status"
        ],
        "alternative_public_replay_candidate_review_evaluated_count": alternative_replay_context[
            "candidate_review_evaluated_count"
        ],
        "alternative_public_replay_candidate_review_robust_candidate_count": alternative_replay_context[
            "candidate_review_robust_candidate_count"
        ],
        "alternative_public_replay_candidate_review_selection_reason": alternative_replay_context[
            "candidate_review_selection_reason"
        ],
        "alternative_public_replay_candidate_review_evaluations": alternative_replay_context[
            "candidate_review_evaluations"
        ],
        "alternative_review_scorecard_status": alternative_review_scorecard_context["status"],
        "alternative_review_scorecard_blocker_code": alternative_review_scorecard_context["blocker_code"],
        "alternative_review_scorecard_message": alternative_review_scorecard_context["message"],
        "alternative_review_scorecard_path": alternative_review_scorecard_context["path"],
        "alternative_review_overfit_diagnostic_path": alternative_review_scorecard_context["overfit_diagnostic_path"],
        "alternative_review_scorecard_candidate_id": alternative_review_scorecard_context["candidate_id"],
        "alternative_review_scorecard_ranking_eligible": alternative_review_scorecard_context["ranking_eligible"],
        "alternative_review_scorecard_blocker_codes": alternative_review_scorecard_context["blocker_codes"],
        "alternative_review_replay_closed_trade_sample_count": alternative_review_scorecard_context[
            "replay_closed_trade_sample_count"
        ],
        "alternative_review_replay_min_closed_trade_sample_count": alternative_review_scorecard_context[
            "min_required_closed_trade_sample_count"
        ],
        "alternative_review_replay_closed_trade_deficit": alternative_review_scorecard_context[
            "replay_closed_trade_deficit"
        ],
        "alternative_review_replay_closed_trade_maturity_status": alternative_review_scorecard_context[
            "replay_closed_trade_maturity_status"
        ],
        "alternative_review_replay_strategy_exit_policy_sample_count": alternative_review_scorecard_context[
            "replay_strategy_exit_policy_sample_count"
        ],
        "alternative_review_replay_profit_factor": alternative_review_scorecard_context["replay_profit_factor"],
        "alternative_review_replay_performance_scope": alternative_review_scorecard_context["replay_performance_scope"],
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
        "source_runtime_cycle_path": str(scorecard_sample["source_runtime_cycle_path"]),
        "source_runtime_cycle_hash": runtime["cycle_hash"],
        "scorecard_runtime_selection_source": scorecard_runtime_selection_source,
        "active_candidate_scope_candidate_id": (
            history.get("active_candidate_scope", {}).get("candidate_id")
            if isinstance(history.get("active_candidate_scope"), dict)
            else None
        ),
        "active_candidate_scope_sample_count": history.get("active_candidate_scope_sample_count"),
        "scorecard_id": scorecard["scorecard_id"],
        "candidate_id": scorecard["candidate_id"],
        "scorecard_scope": scorecard["scorecard_scope"],
        "ranking_eligible": scorecard["ranking_eligible"],
        "scorecard_blocker_codes": [blocker["code"] for blocker in scorecard["blockers"]],
        "candidate_generation_status": candidate_generation_report["generation_status"],
        "candidate_generation_primary_blocker_code": candidate_generation_report["primary_blocker_code"],
        "candidate_generation_alternative_candidate_count": candidate_generation_report["alternative_candidate_count"],
        "candidate_generation_best_alternative_candidate_id": candidate_generation_report["best_alternative_candidate_id"],
        "candidate_generation_best_alternative_symbol": candidate_generation_report["best_alternative_symbol"],
        "candidate_generation_best_alternative_public_replay_status": candidate_generation_report[
            "best_alternative_public_replay_status"
        ],
        "candidate_generation_best_alternative_public_replay_sample_count": candidate_generation_report[
            "best_alternative_public_replay_sample_count"
        ],
        "candidate_generation_best_alternative_public_replay_closed_trade_sample_count": candidate_generation_report[
            "best_alternative_public_replay_closed_trade_sample_count"
        ],
        "candidate_generation_best_alternative_public_replay_min_closed_trade_sample_count": candidate_generation_report[
            "best_alternative_public_replay_min_closed_trade_sample_count"
        ],
        "candidate_generation_best_alternative_public_replay_closed_trade_deficit": candidate_generation_report[
            "best_alternative_public_replay_closed_trade_deficit"
        ],
        "candidate_generation_best_alternative_public_replay_closed_trade_maturity_status": candidate_generation_report[
            "best_alternative_public_replay_closed_trade_maturity_status"
        ],
        "candidate_generation_best_alternative_public_replay_closed_trade_maturity_blocker_code": candidate_generation_report[
            "best_alternative_public_replay_closed_trade_maturity_blocker_code"
        ],
        "candidate_generation_next_action": candidate_generation_report["next_action"],
        "diagnostic_status": diagnostic["diagnostic_status"],
        "robustness_eligible": diagnostic["robustness_eligible"],
        "sample_count": diagnostic["sample_count"],
        "min_required_sample_count": diagnostic["min_required_sample_count"],
        "public_replay_robustness_status": public_replay_robustness_context["status"],
        "public_replay_robustness_blocker_code": public_replay_robustness_context["blocker_code"],
        "public_replay_robustness_contract_status": public_replay_robustness_context["contract_status"],
        "public_replay_robustness_contract_blocker_code": public_replay_robustness_context["contract_blocker_code"],
        "public_replay_robustness_replay_status": public_replay_robustness_context["replay_status"],
        "public_replay_robustness_sample_count": public_replay_robustness_context["sample_count"],
        "public_replay_robustness_source_bound": public_replay_robustness_context["source_bound"],
        "public_replay_robustness_oos_status": public_replay_robustness_context["oos_status"],
        "public_replay_robustness_walk_forward_status": public_replay_robustness_context["walk_forward_status"],
        "public_replay_robustness_bootstrap_status": public_replay_robustness_context["bootstrap_status"],
        "public_replay_robustness_overfit_status": public_replay_robustness_context["overfit_status"],
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
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
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
    parser.add_argument("--attempt-public-discovery", action="store_true")
    parser.add_argument("--candidate-discovery-symbol-limit", type=int, default=12)
    parser.add_argument("--candidate-discovery-timeout-seconds", type=float, default=3.0)
    parser.add_argument("--alternative-replay-target-count", type=int, default=420)
    parser.add_argument("--alternative-replay-page-size", type=int, default=200)
    parser.add_argument("--alternative-replay-timeout-seconds", type=float, default=3.0)
    parser.add_argument("--alternative-replay-max-windows", type=int, default=420)
    parser.add_argument("--alternative-replay-min-required-sample-count", type=int, default=300)
    parser.add_argument("--alternative-replay-candidate-limit", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_current_upbit_paper_candidate_scorecard(
        root=args.root,
        session_id=args.session_id,
        attempt_public_discovery=args.attempt_public_discovery,
        candidate_discovery_symbol_limit=args.candidate_discovery_symbol_limit,
        candidate_discovery_timeout_seconds=args.candidate_discovery_timeout_seconds,
        alternative_replay_target_count=args.alternative_replay_target_count,
        alternative_replay_page_size=args.alternative_replay_page_size,
        alternative_replay_timeout_seconds=args.alternative_replay_timeout_seconds,
        alternative_replay_max_windows=args.alternative_replay_max_windows,
        alternative_replay_min_required_sample_count=args.alternative_replay_min_required_sample_count,
        alternative_replay_candidate_limit=args.alternative_replay_candidate_limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
