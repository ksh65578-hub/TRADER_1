from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from trader1.adapters.upbit.market_data import (
    DEFAULT_DISCOVERY_EVALUATION_LIMIT,
    fetch_upbit_krw_market_symbols_read_only,
    fetch_upbit_public_ticker_snapshot_read_only,
    rank_upbit_krw_symbols_by_public_ticker,
)

from trader1.core.ledger.paper_ledger import validate_upbit_paper_ledger
from trader1.runtime.ledger.paper_ledger_input_manifest import (
    build_paper_ledger_input_manifest,
    validate_paper_ledger_input_manifest,
    write_paper_ledger_input_manifest,
)
from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    validate_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_runtime import (
    POSITION_ROTATION_EXIT_FIELDS,
    UpbitPaperRuntimeCycleValidationResult,
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    durable_atomic_write_json,
    durable_atomic_write_jsonl,
    recover_jsonl_records,
    upbit_public_market_data_collection_hash,
    validate_upbit_public_market_data_collection_report,
    write_upbit_public_market_data_collection_artifacts,
)
from trader1.runtime.portfolio.paper_portfolio import (
    PAPER_STARTING_CASH_BY_SCOPE,
    mark_paper_portfolio_snapshot_to_public_market,
    validate_paper_portfolio_snapshot,
)


UPBIT_PAPER_PERSISTENT_LOOP_SCHEMA_ID = "trader1.upbit_paper_persistent_loop_report.v1"
UPBIT_PAPER_RUNTIME_RECOVERY_GUARD_SCHEMA_ID = "trader1.upbit_paper_runtime_recovery_guard_report.v1"
DEFAULT_MAX_CYCLE_COUNT = 20
DEFAULT_UPBIT_PAPER_SYMBOL_UNIVERSE = (
    "KRW-BTC",
    "KRW-ETH",
    "KRW-XRP",
    "KRW-SOL",
    "KRW-DOGE",
    "KRW-ADA",
    "KRW-TRX",
    "KRW-LINK",
    "KRW-DOT",
    "KRW-AVAX",
    "KRW-SHIB",
    "KRW-BCH",
    "KRW-NEAR",
    "KRW-APT",
    "KRW-SUI",
    "KRW-ETC",
    "KRW-XLM",
    "KRW-HBAR",
    "KRW-STX",
    "KRW-ATOM",
)
DEFAULT_PUBLIC_DISCOVERY_EVALUATION_LIMIT = DEFAULT_DISCOVERY_EVALUATION_LIMIT
RECENT_FAILURE_FEEDBACK_LOOKBACK_CYCLES = 30
RECENT_FAILURE_FEEDBACK_COOLDOWN_CYCLES = 3
RUNTIME_QUALITY_FEEDBACK_COOLDOWN_CYCLES = 5
RUNTIME_QUALITY_FEEDBACK_MIN_PRELIMINARY_SAMPLE_COUNT = 20
RUNTIME_QUALITY_FEEDBACK_MAX_AGE_SECONDS = 6 * 60 * 60
RUNTIME_QUALITY_FEEDBACK_MAX_FUTURE_SKEW_SECONDS = 5 * 60
RECENT_FAILURE_FEEDBACK_EXIT_REASONS = {
    "REGIME_REVERSAL",
    "HARD_STOP",
    "TRAILING_STOP",
    "REGIME_ROTATION_EXIT",
    "ROTATION_OPPORTUNITY_COST",
}
BOUNDED_LOOP_RUNTIME_EVIDENCE_ROLE = "BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE"
RECOVERY_GUARD_RUNTIME_EVIDENCE_ROLE = "PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE"
LONG_RUN_EVIDENCE_BLOCKER_CODE = "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT"
LONG_RUN_EVIDENCE_NEXT_ACTION = (
    "Collect validated long-run PAPER and SHADOW runtime evidence before treating this as live-review or scale-up evidence."
)
LEGACY_RUNTIME_RISK_EXIT_LIFECYCLE_FIELDS = frozenset(
    {"risk_state", "exit_plan", "position_management_decision"}
)
LEGACY_RUNTIME_RISK_EXIT_LIFECYCLE_CONTRACT_MODE = (
    "LEGACY_RECHECK_WITHOUT_RUNTIME_RISK_EXIT_LIFECYCLE"
)
SYMBOL_EVIDENCE_SCORECARD_SCHEMA_UPGRADE_FIELDS = frozenset(
    {
        "symbol_selection_policy",
        "symbol_evidence_scorecards",
        "symbol_evidence_scorecard_count",
        "selected_symbol_evidence_scorecard",
    }
)
SYMBOL_EVIDENCE_SCORECARD_SCHEMA_UPGRADE_CONTRACT_MODE = (
    "LEGACY_RECHECK_WITHOUT_SYMBOL_EVIDENCE_SCORECARD"
)
CANDIDATE_COST_MODEL_SCHEMA_UPGRADE_FIELDS = frozenset({"cost_model_formula"})
POSITION_ROTATION_SCHEMA_UPGRADE_CONTRACT_MODE = "LEGACY_RECHECK_WITHOUT_POSITION_ROTATION_FIELDS"
FEATURE_SNAPSHOT_PROJECTION_UPGRADE_MESSAGES = frozenset(
    {
        "feature snapshot does not match public market data",
        "feature snapshot hash mismatch",
        "multi-symbol feature snapshot mismatch",
        "legacy feature snapshot projection scope mismatch",
        "legacy feature snapshot hash mismatch",
        "legacy multi-symbol feature snapshot scope mismatch",
    }
)
SYMBOL_EVIDENCE_SCORECARD_PROJECTION_UPGRADE_MESSAGE = (
    "symbol evidence scorecard does not match runtime symbol candidates"
)


@dataclass(frozen=True)
class UpbitPaperPersistentLoopValidationResult:
    status: str
    message: str
    blocker_code: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest().upper()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64


def upbit_paper_persistent_loop_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("loop_hash", None)
    return _sha256_json(payload)


def upbit_paper_runtime_recovery_guard_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("guard_hash", None)
    return _sha256_json(payload)


def _relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _runtime_base_dir(root: Path, session_id: str) -> Path:
    return root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / session_id


def _paper_cash_guard_context(*, root: Path, session_id: str, rollup_id: str) -> dict[str, Any]:
    base = _runtime_base_dir(root, session_id)
    cycle_dir = base / "ledger" / "cycles"
    ledger_paths = sorted(cycle_dir.glob("*.paper_ledger_events.jsonl")) if cycle_dir.exists() else []
    if not ledger_paths:
        _, starting_cash = PAPER_STARTING_CASH_BY_SCOPE[("UPBIT", "KRW_SPOT")]
        return {
            "status": "PASS",
            "cash_available": str(starting_cash),
            "equity": str(starting_cash),
            "position_market_value": "0",
            "portfolio_snapshot": None,
            "source": "PAPER_DEFAULT_STARTING_CASH_NO_LEDGER",
            "blocker_code": None,
            "message": None,
        }

    manifest = build_paper_ledger_input_manifest(
        root=root,
        session_id=session_id,
        manifest_id=f"{rollup_id}-ledger-input-manifest",
    )
    manifest_result = validate_paper_ledger_input_manifest(manifest)
    manifest_path = write_paper_ledger_input_manifest(root=root, manifest=manifest)
    if manifest_result.status != "PASS":
        return {
            "status": "BLOCKED",
            "cash_available": "-1",
            "equity": "0",
            "position_market_value": "0",
            "portfolio_snapshot": None,
            "source": "PAPER_LEDGER_INPUT_MANIFEST",
            "manifest_status": manifest_result.status,
            "manifest_path": _relative_posix(manifest_path, root),
            "blocker_code": manifest_result.blocker_code or "RECONCILIATION_REQUIRED",
            "message": manifest_result.message,
        }

    rollup = build_paper_ledger_rollup_report(
        root=root,
        session_id=session_id,
        rollup_id=rollup_id,
    )
    result = validate_paper_ledger_rollup_report(rollup)
    if result.status != "PASS":
        return {
            "status": "BLOCKED",
            "cash_available": "-1",
            "equity": "0",
            "position_market_value": "0",
            "portfolio_snapshot": None,
            "source": "PAPER_LEDGER_ROLLUP",
            "manifest_status": manifest_result.status,
            "manifest_path": _relative_posix(manifest_path, root),
            "blocker_code": result.blocker_code or "RECONCILIATION_REQUIRED",
            "message": result.message,
        }
    portfolio = rollup["portfolio_snapshot"]
    return {
        "status": "PASS",
        "cash_available": portfolio["cash_available"],
        "equity": portfolio["equity"],
        "position_market_value": portfolio["position_market_value"],
        "portfolio_snapshot": portfolio,
        "source": "PAPER_LEDGER_ROLLUP",
        "manifest_status": manifest_result.status,
        "manifest_path": _relative_posix(manifest_path, root),
        "blocker_code": None,
        "message": None,
    }


def _open_position_symbols(snapshot: dict[str, Any] | None) -> list[str]:
    if not isinstance(snapshot, dict):
        return []
    positions = snapshot.get("positions")
    if not isinstance(positions, list):
        return []
    symbols = [
        str(position.get("symbol"))
        for position in positions
        if isinstance(position, dict) and position.get("side") == "LONG" and position.get("symbol")
    ]
    return sorted(set(symbols))


def _merge_required_symbols(symbols: list[str], required_symbols: list[str], *, max_count: int) -> list[str]:
    merged: list[str] = []
    for symbol in [*required_symbols, *symbols]:
        if symbol not in merged:
            merged.append(symbol)
    if max_count < 1:
        return merged
    return merged[: max(max_count, len(required_symbols))]


def _mark_cash_guard_portfolio_to_public_market(
    *,
    cash_guard: dict[str, Any],
    usable_collections: list[dict[str, Any]],
) -> dict[str, Any]:
    portfolio = cash_guard.get("portfolio_snapshot")
    open_symbols = _open_position_symbols(portfolio if isinstance(portfolio, dict) else None)
    if not open_symbols:
        return cash_guard
    if len(open_symbols) != 1:
        marked_guard = dict(cash_guard)
        marked_guard.update(
            {
                "status": "BLOCKED",
                "cash_available": "-1",
                "equity": "0",
                "position_market_value": "0",
                "portfolio_snapshot": None,
                "blocker_code": "MEASUREMENT_MISSING",
                "message": "multiple open PAPER positions require complete public mark coverage before the next runtime cycle",
            }
        )
        return marked_guard
    collection = next((item for item in usable_collections if item.get("symbol") == open_symbols[0]), None)
    public_market_data = collection.get("public_market_data") if isinstance(collection, dict) else None
    if not isinstance(public_market_data, dict) or public_market_data.get("source") != "PUBLIC_REST_READ_ONLY":
        return cash_guard
    marked = mark_paper_portfolio_snapshot_to_public_market(
        paper_portfolio_snapshot=portfolio,
        public_market_data_collection_report=collection if isinstance(collection, dict) else None,
        require_public_mark=True,
    )
    result = validate_paper_portfolio_snapshot(marked)
    if result.status != "PASS" or marked.get("snapshot_status") != "PASS" or marked.get("mark_to_market_status") != "PASS_PUBLIC_MARK_TO_MARKET":
        marked_guard = dict(cash_guard)
        marked_guard.update(
            {
                "status": "BLOCKED",
                "cash_available": "-1",
                "equity": "0",
                "position_market_value": "0",
                "portfolio_snapshot": None,
                "blocker_code": result.blocker_code or "MEASUREMENT_MISSING",
                "message": result.message,
            }
        )
        return marked_guard
    marked_guard = dict(cash_guard)
    marked_guard.update(
        {
            "cash_available": marked["cash_available"],
            "equity": marked["equity"],
            "position_market_value": marked["position_market_value"],
            "portfolio_snapshot": marked,
            "source": "PAPER_LEDGER_ROLLUP_PUBLIC_MARK",
        }
    )
    return marked_guard


def _existing_runtime_state_detected(root: Path, session_id: str) -> bool:
    base = _runtime_base_dir(root, session_id)
    if not base.exists():
        return False
    direct_paths = (
        base / "upbit_paper_runtime_cycle_report.json",
        base / "ledger" / "latest_paper_ledger_head.json",
    )
    if any(path.exists() for path in direct_paths):
        return True
    patterns = (
        "**/*.tmp",
        "paper_runtime/cycles/*.json",
        "market_data/public/canonical/*.canonical_events.jsonl",
        "ledger/cycles/*.paper_ledger_events.jsonl",
    )
    return any(next(base.glob(pattern), None) is not None for pattern in patterns)


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(value, dict):
        return None, "not_object"
    return value, None


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("-1")


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else str(value.quantize(Decimal("1")))


def _safe_paper_only_cycle_for_failure_feedback(cycle: dict[str, Any]) -> bool:
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    if cycle.get("order_adapter_called") or cycle.get("live_key_loaded") or cycle.get("can_submit_order"):
        return False
    if cycle.get("paper_order_adapter") != "SIMULATED_PAPER_BROKER_ONLY":
        return False
    return cycle.get("cycle_hash") == upbit_paper_runtime_cycle_hash(cycle)


def _recent_negative_exit_failure_feedback(*, root: Path, session_id: str) -> list[dict[str, Any]]:
    base = _runtime_base_dir(root, session_id)
    cycles_dir = base / "paper_runtime" / "cycles"
    if not cycles_dir.exists():
        return []
    cycle_paths = sorted(cycles_dir.glob("*.runtime_cycle.json"))[-RECENT_FAILURE_FEEDBACK_LOOKBACK_CYCLES:]
    valid_cycles: list[dict[str, Any]] = []
    for path in cycle_paths:
        cycle, error = _safe_read_json(path)
        if error is not None or not isinstance(cycle, dict):
            continue
        if not _safe_paper_only_cycle_for_failure_feedback(cycle):
            continue
        valid_cycles.append(cycle)

    feedback: list[dict[str, Any]] = []
    previous_realized_pnl: Decimal | None = None
    for cycle_index, cycle in enumerate(valid_cycles):
        portfolio = cycle.get("paper_portfolio_snapshot")
        if not isinstance(portfolio, dict):
            continue
        current_realized_pnl = _decimal(portfolio.get("realized_pnl"))
        realized_delta = current_realized_pnl if previous_realized_pnl is None else current_realized_pnl - previous_realized_pnl
        previous_realized_pnl = current_realized_pnl
        if realized_delta >= 0:
            continue
        if cycle.get("final_decision") not in {"EXIT_POSITION", "REDUCE_POSITION"}:
            continue
        lifecycle = cycle.get("position_management_decision")
        if not isinstance(lifecycle, dict):
            continue
        exit_reason = str(lifecycle.get("position_exit_reason_code") or "")
        if exit_reason not in RECENT_FAILURE_FEEDBACK_EXIT_REASONS:
            continue
        cycles_since_failure = len(valid_cycles) - cycle_index - 1
        cooldown_remaining = max(0, RECENT_FAILURE_FEEDBACK_COOLDOWN_CYCLES - cycles_since_failure)
        if cooldown_remaining <= 0:
            continue
        selected = cycle.get("selected_candidate")
        if not isinstance(selected, dict):
            selected = {}
        symbol = str(lifecycle.get("managed_position_symbol") or selected.get("symbol") or cycle.get("selected_symbol") or "")
        if not symbol:
            continue
        feedback.append(
            {
                "source": "PAPER_RUNTIME_RECENT_NEGATIVE_EXIT_FEEDBACK",
                "symbol": symbol,
                "candidate_id": selected.get("candidate_id") or lifecycle.get("selected_candidate_id"),
                "strategy_family": selected.get("strategy_family"),
                "exit_reason_code": exit_reason,
                "realized_pnl_delta": _decimal_text(realized_delta),
                "source_runtime_cycle_id": cycle.get("cycle_id"),
                "source_runtime_cycle_hash": cycle.get("cycle_hash"),
                "cycles_since_failure": cycles_since_failure,
                "cooldown_cycles_remaining": cooldown_remaining,
                "cooldown_formula": "max(0,3-cycles_since_negative_exit); applies only to PAPER closed losses with known exit reason",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
    return feedback


def _overfit_diagnostic_report_hash(report: dict[str, Any]) -> str:
    payload = dict(report)
    payload.pop("diagnostic_hash", None)
    return _sha256_json(payload)


def _parse_utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _strategy_family_from_candidate_id(candidate_id: str) -> str | None:
    if candidate_id.endswith("-pullback-trend-long"):
        return "PULLBACK_TREND_LONG"
    if candidate_id.endswith("-breakout-retest-long"):
        return "BREAKOUT_RETEST_LONG"
    if candidate_id.endswith("-vwap-mean-reversion"):
        return "VWAP_MEAN_REVERSION"
    return None


def _recent_unfavorable_runtime_quality_feedback(*, root: Path, session_id: str) -> list[dict[str, Any]]:
    diagnostic_path = _runtime_base_dir(root, session_id) / "profitability" / "overfit_diagnostic_report.json"
    diagnostic, error = _safe_read_json(diagnostic_path)
    if error is not None or not isinstance(diagnostic, dict):
        return []
    if diagnostic.get("diagnostic_hash") != _overfit_diagnostic_report_hash(diagnostic):
        return []
    if diagnostic.get("exchange") != "UPBIT" or diagnostic.get("market_type") != "KRW_SPOT" or diagnostic.get("mode") != "PAPER":
        return []
    if diagnostic.get("session_id") != session_id:
        return []
    if diagnostic.get("live_order_ready") or diagnostic.get("live_order_allowed") or diagnostic.get("can_live_trade") or diagnostic.get("scale_up_allowed"):
        return []
    generated_at = _parse_utc_datetime(diagnostic.get("generated_at_utc"))
    if generated_at is None:
        return []
    feedback_age_seconds = (datetime.now(timezone.utc) - generated_at).total_seconds()
    if (
        feedback_age_seconds > RUNTIME_QUALITY_FEEDBACK_MAX_AGE_SECONDS
        or feedback_age_seconds < -RUNTIME_QUALITY_FEEDBACK_MAX_FUTURE_SKEW_SECONDS
    ):
        return []
    candidate_id = str(diagnostic.get("candidate_id") or "")
    symbol = str(diagnostic.get("symbol") or "")
    if not candidate_id or not symbol:
        return []
    try:
        preliminary_sample_count = int(diagnostic.get("preliminary_sample_count") or 0)
    except (TypeError, ValueError):
        preliminary_sample_count = 0
    if preliminary_sample_count < RUNTIME_QUALITY_FEEDBACK_MIN_PRELIMINARY_SAMPLE_COUNT:
        return []

    preliminary_statuses = {
        str(diagnostic.get("preliminary_robustness_status") or ""),
        str(diagnostic.get("preliminary_oos_status") or ""),
        str(diagnostic.get("preliminary_walk_forward_status") or ""),
        str(diagnostic.get("preliminary_bootstrap_status") or ""),
        str(diagnostic.get("preliminary_ranking_stability_status") or ""),
    }
    preliminary_net_ev = _decimal(diagnostic.get("preliminary_in_sample_net_ev_after_cost_bps"))
    preliminary_oos_ev = _decimal(diagnostic.get("preliminary_oos_net_ev_after_cost_bps"))
    preliminary_bootstrap_lower = _decimal(diagnostic.get("preliminary_bootstrap_confidence_lower_bps"))
    unfavorable = (
        diagnostic.get("overfit_status") == "HIGH"
        or "UNFAVORABLE_BLOCKED_BY_EVIDENCE" in preliminary_statuses
        or "FAIL" in preliminary_statuses
        or preliminary_net_ev < 0
        or preliminary_oos_ev < 0
        or preliminary_bootstrap_lower < 0
    )
    if not unfavorable:
        return []

    return [
        {
            "source": "PAPER_RUNTIME_PRELIMINARY_ROBUSTNESS_FEEDBACK",
            "feedback_kind": "PRELIMINARY_ROBUSTNESS_FAIL",
            "symbol": symbol,
            "candidate_id": candidate_id,
            "strategy_family": _strategy_family_from_candidate_id(candidate_id),
            "failure_reason_code": str(diagnostic.get("preliminary_primary_blocker_code") or "PRELIMINARY_ROBUSTNESS_FAIL"),
            "exit_reason_code": str(diagnostic.get("preliminary_primary_blocker_code") or "PRELIMINARY_ROBUSTNESS_FAIL"),
            "realized_pnl_delta": "0",
            "preliminary_sample_count": preliminary_sample_count,
            "preliminary_in_sample_net_ev_after_cost_bps": _decimal_text(preliminary_net_ev),
            "preliminary_oos_net_ev_after_cost_bps": _decimal_text(preliminary_oos_ev),
            "preliminary_bootstrap_confidence_lower_bps": _decimal_text(preliminary_bootstrap_lower),
            "preliminary_robustness_status": diagnostic.get("preliminary_robustness_status"),
            "source_generated_at_utc": diagnostic.get("generated_at_utc"),
            "source_feedback_age_seconds": str(max(0, int(feedback_age_seconds))),
            "source_runtime_cycle_id": diagnostic.get("diagnostic_id"),
            "source_runtime_cycle_hash": diagnostic.get("diagnostic_hash"),
            "cycles_since_failure": 0,
            "cooldown_cycles_remaining": RUNTIME_QUALITY_FEEDBACK_COOLDOWN_CYCLES,
            "cooldown_formula": "5-cycle PAPER cooldown when preliminary robustness/OOS/bootstrap evidence is unfavorable for the same candidate scope",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    ]


def _requires_legacy_quantitative_policy_recheck(cycle: dict[str, Any] | None) -> bool:
    if not isinstance(cycle, dict):
        return False
    summary = cycle.get("summary")
    return isinstance(summary, dict) and not isinstance(summary.get("quantitative_policy_summary"), dict)


def _requires_legacy_sizing_cap_recheck(cycle: dict[str, Any] | None) -> bool:
    if not isinstance(cycle, dict):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    sizing = cycle.get("sizing_decision")
    if not isinstance(sizing, dict):
        return False
    if sizing.get("live_order_ready") or sizing.get("live_order_allowed") or sizing.get("can_live_trade") or sizing.get("can_submit_order"):
        return False
    if sizing.get("order_adapter_called"):
        return False
    caps = sizing.get("caps")
    return isinstance(caps, dict) and "exposure_cap" not in caps


def _missing_runtime_fields(result: UpbitPaperRuntimeCycleValidationResult) -> set[str]:
    prefix = "paper runtime cycle missing fields: "
    if result.status != "FAIL" or result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return set()
    if not result.message.startswith(prefix):
        return set()
    try:
        parsed = ast.literal_eval(result.message[len(prefix) :])
    except (SyntaxError, ValueError):
        return set()
    if not isinstance(parsed, list):
        return set()
    return {str(item) for item in parsed}


def _requires_legacy_runtime_risk_exit_lifecycle_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if not isinstance(cycle, dict):
        return False
    missing = _missing_runtime_fields(runtime_result)
    allowed_additive_schema_missing = LEGACY_RUNTIME_RISK_EXIT_LIFECYCLE_FIELDS | SYMBOL_EVIDENCE_SCORECARD_SCHEMA_UPGRADE_FIELDS
    if not missing or not (missing & LEGACY_RUNTIME_RISK_EXIT_LIFECYCLE_FIELDS):
        return False
    if not missing.issubset(allowed_additive_schema_missing):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    snapshot = cycle.get("paper_portfolio_snapshot")
    if not isinstance(snapshot, dict):
        return False
    try:
        open_position_count = int(snapshot.get("open_position_count") or 0)
    except (TypeError, ValueError):
        return False
    if open_position_count != 0:
        return False
    if cycle.get("final_decision") == "ENTER_LONG":
        return False
    if cycle.get("paper_fill") is not None or cycle.get("paper_ledger_events"):
        return False
    return True


def _requires_symbol_evidence_scorecard_schema_upgrade_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if not isinstance(cycle, dict):
        return False
    missing = _missing_runtime_fields(runtime_result)
    allowed_additive_schema_missing = SYMBOL_EVIDENCE_SCORECARD_SCHEMA_UPGRADE_FIELDS | LEGACY_RUNTIME_RISK_EXIT_LIFECYCLE_FIELDS
    if not SYMBOL_EVIDENCE_SCORECARD_SCHEMA_UPGRADE_FIELDS.issubset(missing):
        return False
    if not missing.issubset(allowed_additive_schema_missing):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    if cycle.get("order_adapter_called") or cycle.get("live_key_loaded") or cycle.get("can_submit_order"):
        return False
    symbol_universe = cycle.get("symbol_universe")
    symbol_selection_universe = cycle.get("symbol_selection_universe")
    if not isinstance(symbol_universe, list) or not symbol_universe:
        return False
    if not isinstance(symbol_selection_universe, list) or len(symbol_selection_universe) != len(symbol_universe):
        return False
    if cycle.get("runtime_input_role") not in {
        "STATIC_FIXTURE",
        "PUBLIC_MARKET_DATA_COLLECTION",
        "MULTI_SYMBOL_MARKET_DATA_UNIVERSE",
        "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION",
    }:
        return False
    return True


def _strategy_candidate_missing_fields(result: UpbitPaperRuntimeCycleValidationResult) -> set[str]:
    prefix = "strategy candidate missing fields: "
    if result.status != "FAIL" or result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return set()
    if not result.message.startswith(prefix):
        return set()
    try:
        parsed = ast.literal_eval(result.message[len(prefix) :])
    except (SyntaxError, ValueError):
        return set()
    if not isinstance(parsed, list):
        return set()
    return {str(item) for item in parsed}


def _requires_candidate_cost_model_schema_upgrade_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if not isinstance(cycle, dict):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    if cycle.get("order_adapter_called") or cycle.get("live_key_loaded") or cycle.get("can_submit_order"):
        return False
    candidates = cycle.get("strategy_candidates")
    if not isinstance(candidates, list) or not candidates:
        return False
    has_legacy_cost_model = any(
        isinstance(candidate, dict)
        and (
            candidate.get("cost_model_source") == "PAPER_RUNTIME_STATIC_COST_MODEL"
            or "cost_model_formula" not in candidate
        )
        for candidate in candidates
    )
    if not has_legacy_cost_model:
        return False
    missing = _strategy_candidate_missing_fields(runtime_result)
    if missing and missing.issubset(CANDIDATE_COST_MODEL_SCHEMA_UPGRADE_FIELDS):
        return True
    return (
        runtime_result.blocker_code == "MEASUREMENT_MISSING"
        and runtime_result.message == "candidate cost model source is not adaptive PAPER public L2 proxy model"
    )


def _requires_position_rotation_schema_upgrade_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if not isinstance(cycle, dict):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    if cycle.get("order_adapter_called") or cycle.get("live_key_loaded") or cycle.get("can_submit_order"):
        return False
    lifecycle = cycle.get("position_management_decision")
    if not isinstance(lifecycle, dict):
        return False
    if lifecycle.get("live_order_ready") or lifecycle.get("live_order_allowed") or lifecycle.get("can_live_trade") or lifecycle.get("scale_up_allowed"):
        return False
    evaluation = lifecycle.get("position_exit_evaluation")
    if not isinstance(evaluation, dict):
        return False
    missing_rotation_fields = POSITION_ROTATION_EXIT_FIELDS - set(evaluation)
    return bool(missing_rotation_fields) and runtime_result.message.startswith("position exit evaluation missing rotation fields:")


def _safe_paper_only_cycle_for_projection_upgrade(cycle: dict[str, Any] | None) -> bool:
    if not isinstance(cycle, dict):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    if cycle.get("order_adapter_called") or cycle.get("live_key_loaded") or cycle.get("can_submit_order"):
        return False
    if cycle.get("paper_order_adapter") != "SIMULATED_PAPER_BROKER_ONLY":
        return False
    if cycle.get("cycle_hash") != upbit_paper_runtime_cycle_hash(cycle):
        return False
    return True


def _requires_feature_snapshot_projection_upgrade_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if runtime_result.status != "FAIL" or runtime_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return False
    if runtime_result.message not in FEATURE_SNAPSHOT_PROJECTION_UPGRADE_MESSAGES:
        return False
    return _safe_paper_only_cycle_for_projection_upgrade(cycle)


def _requires_symbol_evidence_scorecard_projection_upgrade_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if runtime_result.status != "FAIL" or runtime_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return False
    if runtime_result.message != SYMBOL_EVIDENCE_SCORECARD_PROJECTION_UPGRADE_MESSAGE:
        return False
    return _safe_paper_only_cycle_for_projection_upgrade(cycle)


def _requires_symbol_selection_policy_formula_upgrade_recheck(
    cycle: dict[str, Any] | None,
    runtime_result: UpbitPaperRuntimeCycleValidationResult,
) -> bool:
    if runtime_result.status != "FAIL" or runtime_result.blocker_code != "SCHEMA_IDENTITY_MISMATCH":
        return False
    if runtime_result.message != "symbol selection policy does not match runtime formula":
        return False
    if not isinstance(cycle, dict):
        return False
    if cycle.get("exchange") != "UPBIT" or cycle.get("market_type") != "KRW_SPOT" or cycle.get("mode") != "PAPER":
        return False
    if cycle.get("live_order_ready") or cycle.get("live_order_allowed") or cycle.get("can_live_trade") or cycle.get("scale_up_allowed"):
        return False
    if cycle.get("order_adapter_called") or cycle.get("live_key_loaded") or cycle.get("can_submit_order"):
        return False
    policy = cycle.get("symbol_selection_policy")
    if not isinstance(policy, dict):
        return False
    if policy.get("live_order_ready") or policy.get("live_order_allowed") or policy.get("can_live_trade") or policy.get("scale_up_allowed"):
        return False
    if not isinstance(policy.get("selection_formula"), str) or not isinstance(policy.get("candidate_formula"), str):
        return False
    symbol_universe = cycle.get("symbol_universe")
    symbol_selection_universe = cycle.get("symbol_selection_universe")
    if not isinstance(symbol_universe, list) or not symbol_universe:
        return False
    if not isinstance(symbol_selection_universe, list) or len(symbol_selection_universe) != len(symbol_universe):
        return False
    return True


def build_upbit_paper_runtime_recovery_guard_report(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    loop_id: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    base = _runtime_base_dir(root, session_id)
    latest_path = base / "upbit_paper_runtime_cycle_report.json"
    blockers: list[dict[str, str]] = []
    artifact_paths: list[str] = []

    orphan_tmp_files = sorted(path for path in base.rglob("*.tmp") if path.is_file()) if base.exists() else []
    if orphan_tmp_files:
        blockers.append(
            {
                "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                "severity": "HIGH",
                "message": "orphan runtime temp files require operator review before continuing PAPER runtime",
            }
        )
    artifact_paths.extend(_relative_posix(path, root) for path in orphan_tmp_files)

    corrupted_jsonl_quarantined_count = 0
    jsonl_paths = sorted((base / "market_data" / "public" / "canonical").glob("*.canonical_events.jsonl"))
    for path in jsonl_paths:
        records, quarantine_path = recover_jsonl_records(path)
        artifact_paths.append(_relative_posix(path, root))
        if quarantine_path is not None:
            corrupted_jsonl_quarantined_count += 1
            artifact_paths.append(_relative_posix(quarantine_path, root))
            blockers.append(
                {
                    "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                    "severity": "HIGH",
                    "message": "corrupted canonical JSONL was quarantined; resume requires reconcile review",
                }
            )
        if not records:
            blockers.append(
                {
                    "code": "DATA_UNAVAILABLE",
                    "severity": "HIGH",
                    "message": "canonical JSONL exists but has no recoverable records",
                }
            )

    corrupted_ledger_jsonl_quarantined_count = 0
    ledger_jsonl_invalid_count = 0
    ledger_jsonl_paths = sorted((base / "ledger" / "cycles").glob("*.paper_ledger_events.jsonl"))
    for path in ledger_jsonl_paths:
        records, quarantine_path = recover_jsonl_records(path)
        artifact_paths.append(_relative_posix(path, root))
        if quarantine_path is not None:
            corrupted_ledger_jsonl_quarantined_count += 1
            artifact_paths.append(_relative_posix(quarantine_path, root))
            blockers.append(
                {
                    "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                    "severity": "HIGH",
                    "message": "corrupted PAPER ledger JSONL was quarantined; resume requires reconcile review",
                }
            )
        if not records:
            continue
        ledger_status, ledger_blocker, ledger_message = validate_upbit_paper_ledger(records)
        if ledger_status != "PASS":
            ledger_jsonl_invalid_count += 1
            blockers.append(
                {
                    "code": ledger_blocker or "LEDGER_INTEGRITY_FAIL",
                    "severity": "HIGH",
                    "message": ledger_message,
                }
            )

    latest_cycle, latest_error = _safe_read_json(latest_path)
    latest_cycle_status = "MISSING"
    latest_cycle_hash = None
    latest_cycle_recoverable = False
    latest_cycle_contract_mode = "CURRENT"
    latest_cycle_schema_upgrade_required = False
    latest_cycle_schema_upgrade_reason = None
    if latest_error is not None:
        blockers.append(
            {
                "code": "HARD_TRUTH_MISSING" if latest_error == "missing" else "PARTIAL_WRITE_RECOVERY_REQUIRED",
                "severity": "HIGH",
                "message": "latest PAPER runtime cycle is missing or unreadable",
            }
        )
    else:
        artifact_paths.append(_relative_posix(latest_path, root))
        runtime_result = validate_upbit_paper_runtime_cycle_report(latest_cycle or {})
        legacy_quantitative_recheck = _requires_legacy_quantitative_policy_recheck(latest_cycle)
        legacy_sizing_cap_recheck = _requires_legacy_sizing_cap_recheck(latest_cycle)
        legacy_runtime_risk_exit_lifecycle_recheck = _requires_legacy_runtime_risk_exit_lifecycle_recheck(
            latest_cycle,
            runtime_result,
        )
        symbol_evidence_scorecard_schema_upgrade_recheck = _requires_symbol_evidence_scorecard_schema_upgrade_recheck(
            latest_cycle,
            runtime_result,
        )
        candidate_cost_model_schema_upgrade_recheck = _requires_candidate_cost_model_schema_upgrade_recheck(
            latest_cycle,
            runtime_result,
        )
        position_rotation_schema_upgrade_recheck = _requires_position_rotation_schema_upgrade_recheck(
            latest_cycle,
            runtime_result,
        )
        symbol_selection_policy_formula_upgrade_recheck = _requires_symbol_selection_policy_formula_upgrade_recheck(
            latest_cycle,
            runtime_result,
        )
        feature_snapshot_projection_upgrade_recheck = _requires_feature_snapshot_projection_upgrade_recheck(
            latest_cycle,
            runtime_result,
        )
        symbol_evidence_scorecard_projection_upgrade_recheck = _requires_symbol_evidence_scorecard_projection_upgrade_recheck(
            latest_cycle,
            runtime_result,
        )
        if runtime_result.status != "PASS" and (
            legacy_quantitative_recheck
            or legacy_sizing_cap_recheck
            or legacy_runtime_risk_exit_lifecycle_recheck
            or symbol_evidence_scorecard_schema_upgrade_recheck
            or candidate_cost_model_schema_upgrade_recheck
            or position_rotation_schema_upgrade_recheck
            or symbol_selection_policy_formula_upgrade_recheck
            or feature_snapshot_projection_upgrade_recheck
            or symbol_evidence_scorecard_projection_upgrade_recheck
        ):
            legacy_result = validate_upbit_paper_runtime_cycle_report(
                latest_cycle or {},
                require_quantitative_policy_summary=not legacy_quantitative_recheck,
                require_current_sizing_caps=not legacy_sizing_cap_recheck,
                require_symbol_evidence_scorecard_fields=not (
                    symbol_evidence_scorecard_schema_upgrade_recheck
                    or symbol_evidence_scorecard_projection_upgrade_recheck
                ),
                require_adaptive_candidate_cost_model=not candidate_cost_model_schema_upgrade_recheck,
                require_position_rotation_fields=not position_rotation_schema_upgrade_recheck,
                require_current_symbol_selection_policy=not symbol_selection_policy_formula_upgrade_recheck,
                require_current_feature_snapshot_projection=not feature_snapshot_projection_upgrade_recheck,
            )
            if _requires_feature_snapshot_projection_upgrade_recheck(latest_cycle, legacy_result):
                feature_snapshot_projection_upgrade_recheck = True
                legacy_result = validate_upbit_paper_runtime_cycle_report(
                    latest_cycle or {},
                    require_quantitative_policy_summary=not legacy_quantitative_recheck,
                    require_current_sizing_caps=not legacy_sizing_cap_recheck,
                    require_symbol_evidence_scorecard_fields=not (
                        symbol_evidence_scorecard_schema_upgrade_recheck
                        or symbol_evidence_scorecard_projection_upgrade_recheck
                    ),
                    require_adaptive_candidate_cost_model=not candidate_cost_model_schema_upgrade_recheck,
                    require_position_rotation_fields=not position_rotation_schema_upgrade_recheck,
                    require_current_symbol_selection_policy=not symbol_selection_policy_formula_upgrade_recheck,
                    require_current_feature_snapshot_projection=False,
                )
            if _requires_symbol_evidence_scorecard_projection_upgrade_recheck(latest_cycle, legacy_result):
                symbol_evidence_scorecard_projection_upgrade_recheck = True
                legacy_result = validate_upbit_paper_runtime_cycle_report(
                    latest_cycle or {},
                    require_quantitative_policy_summary=not legacy_quantitative_recheck,
                    require_current_sizing_caps=not legacy_sizing_cap_recheck,
                    require_symbol_evidence_scorecard_fields=False,
                    require_adaptive_candidate_cost_model=not candidate_cost_model_schema_upgrade_recheck,
                    require_position_rotation_fields=not position_rotation_schema_upgrade_recheck,
                    require_current_symbol_selection_policy=not symbol_selection_policy_formula_upgrade_recheck,
                    require_current_feature_snapshot_projection=not feature_snapshot_projection_upgrade_recheck,
                )
            if legacy_runtime_risk_exit_lifecycle_recheck and legacy_result.status != "PASS":
                legacy_result = UpbitPaperRuntimeCycleValidationResult(
                    "PASS",
                    (
                        "legacy no-position PAPER cycle is safe to supersede; "
                        "current runtime risk/exit/lifecycle fields will be regenerated"
                    ),
                    None,
                )
            if legacy_result.status == "PASS":
                runtime_result = legacy_result
                legacy_modes = []
                if legacy_quantitative_recheck:
                    legacy_modes.append("QUANTITATIVE_POLICY_SUMMARY")
                if legacy_sizing_cap_recheck:
                    legacy_modes.append("CURRENT_SIZING_EXPOSURE_CAP")
                if legacy_runtime_risk_exit_lifecycle_recheck:
                    legacy_modes.append("RUNTIME_RISK_EXIT_LIFECYCLE")
                if symbol_evidence_scorecard_schema_upgrade_recheck:
                    legacy_modes.append("SYMBOL_EVIDENCE_SCORECARD")
                if candidate_cost_model_schema_upgrade_recheck:
                    legacy_modes.append("ADAPTIVE_CANDIDATE_COST_MODEL")
                if position_rotation_schema_upgrade_recheck:
                    legacy_modes.append("POSITION_ROTATION_FIELDS")
                if symbol_selection_policy_formula_upgrade_recheck:
                    legacy_modes.append("SYMBOL_SELECTION_POLICY_FORMULA")
                if feature_snapshot_projection_upgrade_recheck:
                    legacy_modes.append("FEATURE_SNAPSHOT_PROJECTION")
                if symbol_evidence_scorecard_projection_upgrade_recheck:
                    legacy_modes.append("SYMBOL_EVIDENCE_SCORECARD_PROJECTION")
                latest_cycle_contract_mode = f"LEGACY_RECHECK_WITHOUT_{'_AND_'.join(legacy_modes)}"
                latest_cycle_schema_upgrade_required = True
                latest_cycle_schema_upgrade_reason = (
                    "latest PAPER cycle predates current runtime schema fields; "
                    "allowing PAPER-only regeneration while keeping all live flags false"
                )
        latest_cycle_status = runtime_result.status
        latest_cycle_hash = latest_cycle.get("cycle_hash") if isinstance(latest_cycle, dict) else None
        latest_cycle_recoverable = runtime_result.status == "PASS"
        if runtime_result.status != "PASS":
            blockers.append(
                {
                    "code": runtime_result.blocker_code or "RECONCILIATION_REQUIRED",
                    "severity": "HIGH",
                    "message": runtime_result.message,
                }
            )

    status = "PASS" if not blockers else "BLOCKED"
    report = {
        "schema_id": UPBIT_PAPER_RUNTIME_RECOVERY_GUARD_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "guard_id": f"{loop_id}-recovery-guard",
        "loop_id": loop_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "latest_cycle_path": _relative_posix(latest_path, root),
        "latest_cycle_status": latest_cycle_status,
        "latest_cycle_hash": latest_cycle_hash,
        "latest_cycle_recoverable": latest_cycle_recoverable,
        "latest_cycle_contract_mode": latest_cycle_contract_mode,
        "latest_cycle_schema_upgrade_required": latest_cycle_schema_upgrade_required,
        "latest_cycle_schema_upgrade_reason": latest_cycle_schema_upgrade_reason,
        "canonical_jsonl_checked_count": len(jsonl_paths),
        "corrupted_jsonl_quarantined_count": corrupted_jsonl_quarantined_count,
        "ledger_jsonl_checked_count": len(ledger_jsonl_paths),
        "corrupted_ledger_jsonl_quarantined_count": corrupted_ledger_jsonl_quarantined_count,
        "ledger_jsonl_invalid_count": ledger_jsonl_invalid_count,
        "orphan_tmp_file_count": len(orphan_tmp_files),
        "artifact_paths": sorted(set(artifact_paths)),
        "recovery_guard_status": status,
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "resume_action": "RESUME_PAPER_ONLY" if status == "PASS" else "SAFE_MODE_RECONCILE",
        "paper_runtime_resume_allowed": status == "PASS",
        "runtime_evidence_role": RECOVERY_GUARD_RUNTIME_EVIDENCE_ROLE,
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "long_run_next_action": LONG_RUN_EVIDENCE_NEXT_ACTION,
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "guard_hash": "",
    }
    report["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(report)
    return report


def write_upbit_paper_runtime_recovery_guard_report(*, root: Path, report: dict[str, Any]) -> Path:
    root = Path(root).resolve()
    runtime_dir = _runtime_base_dir(root, str(report["session_id"])) / "paper_runtime"
    path = runtime_dir / f"{report['guard_id']}.json"
    durable_atomic_write_json(path, report)
    canonical_path = runtime_dir / "upbit_paper_runtime_recovery_guard_report.json"
    if canonical_path != path:
        durable_atomic_write_json(canonical_path, report)
    return path


def _write_runtime_cycle_artifacts(*, root: Path, cycle: dict[str, Any]) -> dict[str, Any]:
    result = validate_upbit_paper_runtime_cycle_report(cycle)
    session_id = str(cycle.get("session_id", "UNKNOWN"))
    base = _runtime_base_dir(root, session_id)
    cycle_path = base / "paper_runtime" / "cycles" / f"{cycle.get('cycle_id')}.runtime_cycle.json"
    latest_path = base / "upbit_paper_runtime_cycle_report.json"
    writer_report_path = base / "paper_runtime" / "cycles" / f"{cycle.get('cycle_id')}.writer_report.json"
    ledger_path = base / "ledger" / "cycles" / f"{cycle.get('cycle_id')}.paper_ledger_events.jsonl"
    ledger_head_path = base / "ledger" / "latest_paper_ledger_head.json"
    if result.status != "PASS":
        writer = {
            "schema_id": "trader1.upbit_paper_runtime_cycle_writer_report.v1",
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "writer_status": "BLOCKED",
            "cycle_id": cycle.get("cycle_id"),
            "exchange": cycle.get("exchange"),
            "market_type": cycle.get("market_type"),
            "mode": cycle.get("mode"),
            "session_id": session_id,
            "primary_blocker_code": result.blocker_code,
            "blocker_message": result.message,
            "artifact_paths": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        durable_atomic_write_json(writer_report_path, writer)
        return writer
    durable_atomic_write_json(cycle_path, cycle)
    durable_atomic_write_json(latest_path, cycle)
    artifact_paths = [_relative_posix(cycle_path, root), _relative_posix(latest_path, root)]
    if cycle.get("paper_ledger_events"):
        durable_atomic_write_jsonl(ledger_path, cycle["paper_ledger_events"])
        ledger_head = {
            "schema_id": "trader1.paper_ledger_head.v1",
            "generated_at_utc": utc_now(),
            "project_id": "TRADER_1",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": session_id,
            "cycle_id": cycle["cycle_id"],
            "ledger_event_count": len(cycle["paper_ledger_events"]),
            "ledger_events_path": _relative_posix(ledger_path, root),
            "ledger_head_hash": cycle["paper_ledger_head_hash"],
            "display_only": True,
            "dashboard_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        ledger_head["head_report_hash"] = _sha256_json(ledger_head)
        durable_atomic_write_json(ledger_head_path, ledger_head)
        artifact_paths.extend([_relative_posix(ledger_path, root), _relative_posix(ledger_head_path, root)])
    writer = {
        "schema_id": "trader1.upbit_paper_runtime_cycle_writer_report.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "writer_status": "PASS",
        "cycle_id": cycle["cycle_id"],
        "exchange": cycle["exchange"],
        "market_type": cycle["market_type"],
        "mode": cycle["mode"],
        "session_id": session_id,
        "primary_blocker_code": None,
        "blocker_message": "PAPER runtime cycle artifacts written atomically; latest pointer remains PAPER-only",
        "artifact_paths": artifact_paths,
        "cycle_hash": cycle["cycle_hash"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    durable_atomic_write_json(writer_report_path, writer)
    return writer


def _normalized_krw_symbols(symbols: list[str] | tuple[str, ...] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for symbol in symbols or ():
        value = str(symbol).strip().upper()
        if not value.startswith("KRW-") or value in seen:
            continue
        quote, _, base = value.partition("-")
        if quote != "KRW" or not base or not base.replace("-", "").isalnum():
            continue
        normalized.append(value)
        seen.add(value)
    return normalized


def _resolve_default_symbol_universe(
    *,
    session_id: str,
    symbol_universe: list[str] | None,
    attempt_public_symbol_discovery: bool,
    require_public_symbol_discovery: bool,
    max_symbol_evaluation_count: int,
    public_discovery_timeout_seconds: float,
    market_symbols_fetcher: Callable[..., dict[str, Any]] | None,
    public_ticker_fetcher: Callable[..., dict[str, Any]] | None,
) -> tuple[list[str], dict[str, Any], list[dict[str, str]]]:
    explicit_universe = _normalized_krw_symbols(symbol_universe)
    if explicit_universe:
        return (
            explicit_universe,
            {
                "symbol_universe_source": "EXPLICIT_SYMBOL_UNIVERSE",
                "public_symbol_discovery_attempted": False,
                "symbol_universe_discovery_status": "SKIPPED",
                "symbol_universe_discovery_blocker_code": None,
                "symbol_universe_total_count": len(explicit_universe),
                "symbol_universe_evaluated_count": len(explicit_universe),
                "max_symbol_evaluation_count": len(explicit_universe),
                "public_symbol_discovery_market_count": 0,
                "public_ticker_ranked_symbol_count": 0,
                "public_ticker_eligible_symbol_count": 0,
                "public_symbol_discovery_report": None,
                "public_ticker_snapshot_report": None,
                "public_symbol_ranking_report": None,
            },
            [],
        )

    fallback_universe = _normalized_krw_symbols(list(DEFAULT_UPBIT_PAPER_SYMBOL_UNIVERSE))
    discovery_context: dict[str, Any] = {
        "symbol_universe_source": "STATIC_FALLBACK_CONFIGURED_KRW_UNIVERSE",
        "public_symbol_discovery_attempted": False,
        "symbol_universe_discovery_status": "SKIPPED",
        "symbol_universe_discovery_blocker_code": None,
        "symbol_universe_total_count": len(fallback_universe),
        "symbol_universe_evaluated_count": len(fallback_universe),
        "max_symbol_evaluation_count": max_symbol_evaluation_count,
        "public_symbol_discovery_market_count": 0,
        "public_ticker_ranked_symbol_count": 0,
        "public_ticker_eligible_symbol_count": 0,
        "public_symbol_discovery_report": None,
        "public_ticker_snapshot_report": None,
        "public_symbol_ranking_report": None,
    }
    if not attempt_public_symbol_discovery:
        return fallback_universe, discovery_context, []

    discovery_context["public_symbol_discovery_attempted"] = True
    discovery_fetcher = market_symbols_fetcher or fetch_upbit_krw_market_symbols_read_only
    ticker_fetcher = public_ticker_fetcher or fetch_upbit_public_ticker_snapshot_read_only
    discovery_report = discovery_fetcher(session_id=session_id, timeout_seconds=public_discovery_timeout_seconds)
    discovered_symbols = _normalized_krw_symbols(discovery_report.get("symbols") if isinstance(discovery_report, dict) else [])
    discovery_context["public_symbol_discovery_report"] = discovery_report
    discovery_context["public_symbol_discovery_market_count"] = len(discovered_symbols)
    discovery_context["symbol_universe_total_count"] = len(discovered_symbols) if discovered_symbols else len(fallback_universe)

    if not discovered_symbols or discovery_report.get("discovery_status") != "PASS":
        discovery_context["symbol_universe_source"] = "STATIC_FALLBACK_PUBLIC_DISCOVERY_UNAVAILABLE"
        discovery_context["symbol_universe_discovery_status"] = "BLOCKED_FALLBACK"
        discovery_context["symbol_universe_discovery_blocker_code"] = discovery_report.get("primary_blocker_code") or "DATA_UNAVAILABLE"
        blockers = []
        if require_public_symbol_discovery:
            blockers.append(
                {
                    "code": discovery_context["symbol_universe_discovery_blocker_code"],
                    "severity": "HIGH",
                    "message": "public Upbit KRW symbol discovery is required but unavailable",
                }
            )
        return fallback_universe, discovery_context, blockers

    ticker_report = ticker_fetcher(
        symbols=discovered_symbols,
        session_id=session_id,
        timeout_seconds=public_discovery_timeout_seconds,
    )
    discovery_context["public_ticker_snapshot_report"] = ticker_report
    ticker_by_symbol = ticker_report.get("ticker_by_symbol") if isinstance(ticker_report, dict) else {}
    if not isinstance(ticker_by_symbol, dict) or ticker_report.get("ticker_status") != "PASS":
        discovery_context["symbol_universe_source"] = "STATIC_FALLBACK_PUBLIC_TICKER_UNAVAILABLE"
        discovery_context["symbol_universe_discovery_status"] = "BLOCKED_FALLBACK"
        discovery_context["symbol_universe_discovery_blocker_code"] = ticker_report.get("primary_blocker_code") or "DATA_UNAVAILABLE"
        blockers = []
        if require_public_symbol_discovery:
            blockers.append(
                {
                    "code": discovery_context["symbol_universe_discovery_blocker_code"],
                    "severity": "HIGH",
                    "message": "public Upbit ticker ranking is required but unavailable",
                }
            )
        return fallback_universe, discovery_context, blockers

    ranking_report = rank_upbit_krw_symbols_by_public_ticker(
        symbols=discovered_symbols,
        ticker_by_symbol=ticker_by_symbol,
        session_id=session_id,
        limit=max_symbol_evaluation_count,
    )
    selected_symbols = _normalized_krw_symbols(ranking_report.get("selected_symbols_for_candle_evaluation", []))
    discovery_context["public_symbol_ranking_report"] = ranking_report
    discovery_context["public_ticker_ranked_symbol_count"] = int(ranking_report.get("ranked_symbol_count") or 0)
    discovery_context["public_ticker_eligible_symbol_count"] = int(ranking_report.get("eligible_symbol_count") or 0)
    if not selected_symbols or ranking_report.get("ranking_status") != "PASS":
        discovery_context["symbol_universe_source"] = "STATIC_FALLBACK_PUBLIC_RANKING_UNAVAILABLE"
        discovery_context["symbol_universe_discovery_status"] = "BLOCKED_FALLBACK"
        discovery_context["symbol_universe_discovery_blocker_code"] = ranking_report.get("primary_blocker_code") or "DATA_UNAVAILABLE"
        blockers = []
        if require_public_symbol_discovery:
            blockers.append(
                {
                    "code": discovery_context["symbol_universe_discovery_blocker_code"],
                    "severity": "HIGH",
                    "message": "public Upbit symbol ranking is required but unavailable",
                }
            )
        return fallback_universe, discovery_context, blockers

    discovery_context["symbol_universe_source"] = "PUBLIC_KRW_MARKET_DISCOVERY_TICKER_RANKED"
    discovery_context["symbol_universe_discovery_status"] = "PASS"
    discovery_context["symbol_universe_discovery_blocker_code"] = None
    discovery_context["symbol_universe_evaluated_count"] = len(selected_symbols)
    return selected_symbols, discovery_context, []


def run_upbit_paper_persistent_loop(
    *,
    root: Path,
    loop_id: str,
    session_id: str = "mvp1_upbit_paper_launcher",
    symbol: str = "KRW-BTC",
    symbol_universe: list[str] | None = None,
    requested_cycle_count: int = 2,
    max_cycle_count: int = DEFAULT_MAX_CYCLE_COUNT,
    market_data_sequence: list[dict[str, Any]] | None = None,
    market_data_universe_sequence: list[list[dict[str, Any]] | dict[str, dict[str, Any]]] | None = None,
    attempt_public_symbol_discovery: bool = False,
    require_public_symbol_discovery: bool = False,
    attempt_network_market_data: bool = False,
    max_symbol_evaluation_count: int = DEFAULT_PUBLIC_DISCOVERY_EVALUATION_LIMIT,
    public_discovery_timeout_seconds: float = 3.0,
    market_symbols_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_ticker_fetcher: Callable[..., dict[str, Any]] | None = None,
    public_candle_fetcher: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    blockers: list[dict[str, str]] = []
    cycle_results: list[dict[str, Any]] = []
    preflight_existing_runtime_state = _existing_runtime_state_detected(root, session_id)
    preflight_recovery_guard: dict[str, Any] | None = None
    preflight_recovery_guard_path: Path | None = None
    current_evidence_write_allowed = True
    if requested_cycle_count < 1 or requested_cycle_count > max_cycle_count or max_cycle_count > DEFAULT_MAX_CYCLE_COUNT:
        blockers.append({"code": "RUNTIME_BUDGET_EXCEEDED", "severity": "HIGH", "message": "requested PAPER loop cycles exceed bounded MVP-4 budget"})
        requested_cycle_count = max(0, min(requested_cycle_count, max_cycle_count, DEFAULT_MAX_CYCLE_COUNT))

    if preflight_existing_runtime_state:
        preflight_recovery_guard = build_upbit_paper_runtime_recovery_guard_report(root=root, session_id=session_id, loop_id=f"{loop_id}-preflight")
        preflight_recovery_guard_path = write_upbit_paper_runtime_recovery_guard_report(root=root, report=preflight_recovery_guard)
        current_evidence_write_allowed = preflight_recovery_guard.get("recovery_guard_status") == "PASS"
        if not current_evidence_write_allowed:
            blockers.append(
                {
                    "code": preflight_recovery_guard.get("primary_blocker_code") or "RECONCILIATION_REQUIRED",
                    "severity": "HIGH",
                    "message": "PAPER runtime preflight recovery guard blocked current evidence writes",
                }
            )

    default_symbol_universe, symbol_discovery_context, symbol_discovery_blockers = _resolve_default_symbol_universe(
        session_id=session_id,
        symbol_universe=symbol_universe,
        attempt_public_symbol_discovery=attempt_public_symbol_discovery,
        require_public_symbol_discovery=require_public_symbol_discovery,
        max_symbol_evaluation_count=max_symbol_evaluation_count,
        public_discovery_timeout_seconds=public_discovery_timeout_seconds,
        market_symbols_fetcher=market_symbols_fetcher,
        public_ticker_fetcher=public_ticker_fetcher,
    )
    blockers.extend(symbol_discovery_blockers)
    if symbol_discovery_blockers:
        current_evidence_write_allowed = False

    if current_evidence_write_allowed:
        for index in range(requested_cycle_count):
            collector_id = f"{loop_id}-collector-{index + 1}"
            cycle_id = f"{loop_id}-cycle-{index + 1}"
            cash_guard = _paper_cash_guard_context(
                root=root,
                session_id=session_id,
                rollup_id=f"{cycle_id}-pre-entry-cash-guard",
            )
            open_position_symbols = _open_position_symbols(cash_guard.get("portfolio_snapshot"))
            supplied_market_data = market_data_sequence[index] if market_data_sequence and index < len(market_data_sequence) else None
            supplied_market_data_universe = (
                market_data_universe_sequence[index]
                if market_data_universe_sequence and index < len(market_data_universe_sequence)
                else None
            )
            if isinstance(supplied_market_data_universe, dict):
                cycle_market_data_by_symbol = dict(supplied_market_data_universe)
                cycle_symbol_universe = _merge_required_symbols(
                    sorted(cycle_market_data_by_symbol),
                    open_position_symbols,
                    max_count=max_symbol_evaluation_count,
                )
                cycle_symbol_universe_source = "SUPPLIED_MARKET_DATA_UNIVERSE"
            elif isinstance(supplied_market_data_universe, list):
                cycle_market_data_by_symbol = {
                    str(item.get("symbol") or f"UNKNOWN-{item_index}"): item
                    for item_index, item in enumerate(supplied_market_data_universe, start=1)
                    if isinstance(item, dict)
                }
                cycle_symbol_universe = _merge_required_symbols(
                    list(cycle_market_data_by_symbol),
                    open_position_symbols,
                    max_count=max_symbol_evaluation_count,
                )
                cycle_symbol_universe_source = "SUPPLIED_MARKET_DATA_UNIVERSE"
            elif supplied_market_data is not None:
                cycle_market_data_by_symbol = {symbol: supplied_market_data}
                cycle_symbol_universe = _merge_required_symbols([symbol], open_position_symbols, max_count=max_symbol_evaluation_count)
                cycle_symbol_universe_source = "SUPPLIED_SINGLE_MARKET_DATA"
            else:
                cycle_market_data_by_symbol = {}
                cycle_symbol_universe = _merge_required_symbols(
                    list(default_symbol_universe),
                    open_position_symbols,
                    max_count=max_symbol_evaluation_count,
                )
                cycle_symbol_universe_source = str(symbol_discovery_context["symbol_universe_source"])
            collections: list[dict[str, Any]] = []
            collection_results: list[Any] = []
            collection_writers: list[dict[str, Any]] = []
            for symbol_index, universe_symbol in enumerate(cycle_symbol_universe, start=1):
                collection = build_upbit_public_market_data_collection_report(
                    collector_id=f"{collector_id}-{symbol_index}-{universe_symbol}",
                    session_id=session_id,
                    symbol=universe_symbol,
                    market_data=cycle_market_data_by_symbol.get(universe_symbol),
                    attempt_network=attempt_network_market_data and universe_symbol not in cycle_market_data_by_symbol,
                    fetcher=public_candle_fetcher,
                    timeout_seconds=public_discovery_timeout_seconds,
                )
                collection_result = validate_upbit_public_market_data_collection_report(collection)
                collection_writer = write_upbit_public_market_data_collection_artifacts(root=root, report=collection)
                collections.append(collection)
                collection_results.append(collection_result)
                collection_writers.append(collection_writer)
            usable_collection_rows = [
                (collection, result, writer)
                for collection, result, writer in zip(collections, collection_results, collection_writers)
                if result.status == "PASS" and writer.get("writer_status") == "PASS"
            ]
            usable_collections = [collection for collection, _, _ in usable_collection_rows]
            usable_collection_writers = [writer for _, _, writer in usable_collection_rows]
            collection_pass = bool(usable_collections)
            cycle: dict[str, Any] | None = None
            cycle_writer: dict[str, Any] | None = None
            recent_failure_feedback: list[dict[str, Any]] = []
            cycle_result_status = "BLOCKED"
            cycle_result_blocker = next((result.blocker_code for result in collection_results if result.blocker_code), None)
            if collection_pass:
                cash_guard = _mark_cash_guard_portfolio_to_public_market(
                    cash_guard=cash_guard,
                    usable_collections=usable_collections,
                )
                if cash_guard["status"] != "PASS":
                    blockers.append(
                        {
                            "code": cash_guard.get("blocker_code") or "RECONCILIATION_REQUIRED",
                            "severity": "HIGH",
                            "message": str(cash_guard.get("message") or "PAPER ledger cash guard blocked entry sizing"),
                        }
                    )
                recent_failure_feedback = [
                    *_recent_negative_exit_failure_feedback(root=root, session_id=session_id),
                    *_recent_unfavorable_runtime_quality_feedback(root=root, session_id=session_id),
                ]
                cycle = build_upbit_paper_runtime_cycle_report(
                    cycle_id=cycle_id,
                    session_id=session_id,
                    symbol=symbol,
                    source_collection_reports=usable_collections,
                    paper_cash_available=cash_guard["cash_available"],
                    paper_equity=cash_guard["equity"],
                    paper_position_market_value=cash_guard["position_market_value"],
                    paper_cash_source=cash_guard["source"],
                    current_paper_portfolio_snapshot=cash_guard.get("portfolio_snapshot"),
                    recent_failure_feedback=recent_failure_feedback,
                )
                runtime_result = validate_upbit_paper_runtime_cycle_report(cycle)
                cycle_result_status = runtime_result.status
                cycle_result_blocker = runtime_result.blocker_code
                cycle_writer = _write_runtime_cycle_artifacts(root=root, cycle=cycle)
            else:
                first_failed = next((result for result in collection_results if result.status != "PASS"), None)
                blockers.append(
                    {
                        "code": (first_failed.blocker_code if first_failed else None) or "DATA_UNAVAILABLE",
                        "severity": "HIGH",
                        "message": (first_failed.message if first_failed else "PAPER multi-symbol collection did not pass"),
                    }
                )
            if cycle_result_status != "PASS":
                blockers.append({"code": cycle_result_blocker or "UNKNOWN_BLOCKED", "severity": "HIGH", "message": "PAPER runtime cycle did not pass"})
            selected_candidate = cycle.get("selected_candidate") if isinstance(cycle, dict) else None
            if not isinstance(selected_candidate, dict):
                selected_candidate = {}
            cycle_results.append(
                {
                    "cycle_index": index + 1,
                    "collector_id": collector_id,
                    "cycle_id": cycle_id,
                    "collection_status": "PASS" if collection_pass else "BLOCKED",
                    "collection_hash": usable_collections[0].get("collection_hash") if usable_collections else None,
                    "collection_hashes_by_symbol": {item.get("symbol"): item.get("collection_hash") for item in collections},
                    "collection_writer_status": "PASS" if collection_pass else "BLOCKED",
                    "runtime_status": cycle_result_status,
                    "runtime_cycle_hash": cycle.get("cycle_hash") if isinstance(cycle, dict) else None,
                    "runtime_writer_status": cycle_writer.get("writer_status") if isinstance(cycle_writer, dict) else "NOT_WRITTEN",
                    "final_decision": cycle.get("final_decision") if isinstance(cycle, dict) else "BLOCKED",
                    "runtime_input_role": cycle.get("runtime_input_role") if isinstance(cycle, dict) else None,
                    "source_collection_report_hash": cycle.get("source_collection_report_hash") if isinstance(cycle, dict) else None,
                    "source_public_market_data_hash": cycle.get("source_public_market_data_hash") if isinstance(cycle, dict) else None,
                    "canonical_event_count": cycle.get("canonical_event_count") if isinstance(cycle, dict) else None,
                    "runtime_public_market_data_hash": cycle.get("runtime_public_market_data_hash") if isinstance(cycle, dict) else None,
                    "feature_snapshot_hash": cycle.get("feature_snapshot_hash") if isinstance(cycle, dict) else None,
                    "regime": cycle.get("regime") if isinstance(cycle, dict) else None,
                    "symbol_universe": cycle.get("symbol_universe") if isinstance(cycle, dict) else cycle_symbol_universe,
                    "symbol_universe_source": cycle_symbol_universe_source,
                    "symbol_universe_total_count": int(symbol_discovery_context["symbol_universe_total_count"]),
                    "symbol_universe_evaluated_count": (
                        len(cycle.get("symbol_universe"))
                        if isinstance(cycle, dict) and isinstance(cycle.get("symbol_universe"), list)
                        else len(cycle_symbol_universe)
                    ),
                    "selected_symbol": cycle.get("selected_symbol") if isinstance(cycle, dict) else None,
                    "selected_candidate_id": selected_candidate.get("candidate_id"),
                    "selected_candidate_net_ev_after_cost_bps": selected_candidate.get("net_ev_after_cost_bps"),
                    "selected_candidate_recent_failure_cooldown_status": selected_candidate.get(
                        "recent_failure_cooldown_status"
                    ),
                    "selected_candidate_recent_failure_cooldown_cycles_remaining": selected_candidate.get(
                        "recent_failure_cooldown_cycles_remaining"
                    ),
                    "selected_candidate_recent_failure_reason_code": selected_candidate.get("recent_failure_reason_code"),
                    "selected_candidate_recent_failure_feedback_kind": selected_candidate.get(
                        "recent_failure_feedback_kind"
                    ),
                    "runtime_quality_feedback_count": sum(
                        1 for item in recent_failure_feedback if item.get("feedback_kind") == "PRELIMINARY_ROBUSTNESS_FAIL"
                    ),
                    "runtime_quality_feedback_candidate_ids": sorted(
                        {
                            str(item.get("candidate_id"))
                            for item in recent_failure_feedback
                            if item.get("feedback_kind") == "PRELIMINARY_ROBUSTNESS_FAIL" and item.get("candidate_id")
                        }
                    ),
                    "strategy_regime_cost_linkage": cycle.get("strategy_regime_cost_linkage") if isinstance(cycle, dict) else None,
                    "artifact_paths": [
                        *(path for writer in usable_collection_writers for path in (writer.get("artifact_paths") or [])),
                        *(cycle_writer.get("artifact_paths") if isinstance(cycle_writer, dict) else []),
                    ],
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                }
            )
    completed_count = sum(1 for item in cycle_results if item.get("runtime_status") == "PASS")
    if current_evidence_write_allowed:
        recovery_guard = build_upbit_paper_runtime_recovery_guard_report(root=root, session_id=session_id, loop_id=loop_id)
        recovery_guard_path = write_upbit_paper_runtime_recovery_guard_report(root=root, report=recovery_guard)
    else:
        recovery_guard = preflight_recovery_guard or build_upbit_paper_runtime_recovery_guard_report(root=root, session_id=session_id, loop_id=loop_id)
        recovery_guard_path = preflight_recovery_guard_path or write_upbit_paper_runtime_recovery_guard_report(root=root, report=recovery_guard)
    if recovery_guard.get("recovery_guard_status") != "PASS":
        blockers.append(
            {
                "code": recovery_guard.get("primary_blocker_code") or "RECONCILIATION_REQUIRED",
                "severity": "HIGH",
                "message": "PAPER runtime recovery guard blocked resume",
            }
        )
    ledger_manifest_path = None
    ledger_manifest_status = "SKIPPED"
    ledger_manifest_primary_blocker_code = None
    ledger_manifest_existing_path = _runtime_base_dir(root, session_id) / "ledger" / "paper_ledger_input_manifest.json"
    if preflight_existing_runtime_state or ledger_manifest_existing_path.exists():
        ledger_manifest = build_paper_ledger_input_manifest(
            root=root,
            session_id=session_id,
            manifest_id=f"{loop_id}-ledger-input-manifest",
        )
        ledger_manifest_result = validate_paper_ledger_input_manifest(ledger_manifest)
        ledger_manifest_status = ledger_manifest_result.status
        ledger_manifest_primary_blocker_code = ledger_manifest_result.blocker_code
        ledger_manifest_path = write_paper_ledger_input_manifest(root=root, manifest=ledger_manifest)
        if ledger_manifest_result.status != "PASS":
            blockers.append(
                {
                    "code": ledger_manifest_result.blocker_code or "RECONCILIATION_REQUIRED",
                    "severity": "HIGH",
                    "message": ledger_manifest_result.message,
                }
            )
    ledger_rollup = build_paper_ledger_rollup_report(root=root, session_id=session_id, rollup_id=f"{loop_id}-ledger-rollup")
    ledger_rollup_path = write_paper_ledger_rollup_report(root=root, report=ledger_rollup)
    ledger_rollup_result = validate_paper_ledger_rollup_report(ledger_rollup)
    if ledger_rollup_result.status != "PASS":
        blockers.append(
            {
                "code": ledger_rollup_result.blocker_code or "RECONCILIATION_REQUIRED",
                "severity": "HIGH",
                "message": ledger_rollup_result.message,
            }
        )
    report = {
        "schema_id": UPBIT_PAPER_PERSISTENT_LOOP_SCHEMA_ID,
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "loop_id": loop_id,
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "symbol": symbol,
        "symbol_universe": list(default_symbol_universe),
        "symbol_universe_source": symbol_discovery_context["symbol_universe_source"],
        "public_symbol_discovery_attempted": symbol_discovery_context["public_symbol_discovery_attempted"],
        "symbol_universe_discovery_status": symbol_discovery_context["symbol_universe_discovery_status"],
        "symbol_universe_discovery_blocker_code": symbol_discovery_context["symbol_universe_discovery_blocker_code"],
        "symbol_universe_total_count": symbol_discovery_context["symbol_universe_total_count"],
        "symbol_universe_evaluated_count": symbol_discovery_context["symbol_universe_evaluated_count"],
        "max_symbol_evaluation_count": symbol_discovery_context["max_symbol_evaluation_count"],
        "public_symbol_discovery_market_count": symbol_discovery_context["public_symbol_discovery_market_count"],
        "public_ticker_ranked_symbol_count": symbol_discovery_context["public_ticker_ranked_symbol_count"],
        "public_ticker_eligible_symbol_count": symbol_discovery_context["public_ticker_eligible_symbol_count"],
        "public_symbol_discovery_report": symbol_discovery_context["public_symbol_discovery_report"],
        "public_ticker_snapshot_report": symbol_discovery_context["public_ticker_snapshot_report"],
        "public_symbol_ranking_report": symbol_discovery_context["public_symbol_ranking_report"],
        "loop_mode": "BOUNDED_PUBLIC_DATA_PAPER_LOOP",
        "requested_cycle_count": requested_cycle_count,
        "completed_cycle_count": completed_count,
        "max_cycle_count": max_cycle_count,
        "cycle_results": cycle_results,
        "loop_status": "PASS" if completed_count == requested_cycle_count and not blockers else "BLOCKED",
        "primary_blocker_code": blockers[0]["code"] if blockers else None,
        "blockers": blockers,
        "actual_paper_runtime_executed": completed_count > 0,
        "preflight_existing_runtime_state_detected": preflight_existing_runtime_state,
        "preflight_recovery_guard_status": preflight_recovery_guard["recovery_guard_status"] if preflight_recovery_guard else "SKIPPED",
        "preflight_recovery_guard_hash": preflight_recovery_guard["guard_hash"] if preflight_recovery_guard else None,
        "preflight_recovery_guard_primary_blocker_code": preflight_recovery_guard["primary_blocker_code"] if preflight_recovery_guard else None,
        "preflight_runtime_recovery_guard_path": _relative_posix(preflight_recovery_guard_path, root) if preflight_recovery_guard_path else None,
        "preflight_paper_runtime_resume_allowed": preflight_recovery_guard["paper_runtime_resume_allowed"] if preflight_recovery_guard else True,
        "current_evidence_write_allowed": current_evidence_write_allowed,
        "recovery_guard_status": recovery_guard["recovery_guard_status"],
        "recovery_guard_hash": recovery_guard["guard_hash"],
        "recovery_guard_primary_blocker_code": recovery_guard["primary_blocker_code"],
        "runtime_recovery_guard_path": _relative_posix(recovery_guard_path, root),
        "paper_ledger_rollup_status": ledger_rollup["rollup_status"],
        "paper_ledger_rollup_hash": ledger_rollup["rollup_hash"],
        "paper_ledger_rollup_primary_blocker_code": ledger_rollup["primary_blocker_code"],
        "paper_ledger_rollup_path": _relative_posix(ledger_rollup_path, root),
        "paper_ledger_input_manifest_status": ledger_manifest_status,
        "paper_ledger_input_manifest_primary_blocker_code": ledger_manifest_primary_blocker_code,
        "paper_ledger_input_manifest_path": _relative_posix(ledger_manifest_path, root) if ledger_manifest_path else None,
        "paper_runtime_resume_allowed": recovery_guard["paper_runtime_resume_allowed"],
        "partial_write_recovery_required": recovery_guard["recovery_guard_status"] != "PASS",
        "runtime_evidence_role": BOUNDED_LOOP_RUNTIME_EVIDENCE_ROLE,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": LONG_RUN_EVIDENCE_BLOCKER_CODE,
        "long_run_next_action": LONG_RUN_EVIDENCE_NEXT_ACTION,
        "promotion_eligible": False,
        "data_source_policy": "PUBLIC_OR_STATIC_FIXTURE_ONLY",
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "loop_hash": "",
    }
    report["loop_hash"] = upbit_paper_persistent_loop_hash(report)
    loop_path = _runtime_base_dir(root, session_id) / "paper_runtime" / f"{loop_id}.persistent_loop_report.json"
    durable_atomic_write_json(loop_path, report)
    canonical_loop_path = _runtime_base_dir(root, session_id) / "paper_runtime" / "upbit_paper_persistent_loop_report.json"
    durable_atomic_write_json(canonical_loop_path, report)
    return report


def validate_upbit_paper_persistent_loop_report(report: dict[str, Any]) -> UpbitPaperPersistentLoopValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "loop_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "symbol",
        "symbol_universe",
        "symbol_universe_source",
        "public_symbol_discovery_attempted",
        "symbol_universe_discovery_status",
        "symbol_universe_discovery_blocker_code",
        "symbol_universe_total_count",
        "symbol_universe_evaluated_count",
        "max_symbol_evaluation_count",
        "public_symbol_discovery_market_count",
        "public_ticker_ranked_symbol_count",
        "public_ticker_eligible_symbol_count",
        "public_symbol_discovery_report",
        "public_ticker_snapshot_report",
        "public_symbol_ranking_report",
        "loop_mode",
        "requested_cycle_count",
        "completed_cycle_count",
        "max_cycle_count",
        "cycle_results",
        "loop_status",
        "primary_blocker_code",
        "blockers",
        "actual_paper_runtime_executed",
        "preflight_existing_runtime_state_detected",
        "preflight_recovery_guard_status",
        "preflight_recovery_guard_hash",
        "preflight_recovery_guard_primary_blocker_code",
        "preflight_runtime_recovery_guard_path",
        "preflight_paper_runtime_resume_allowed",
        "current_evidence_write_allowed",
        "recovery_guard_status",
        "recovery_guard_hash",
        "recovery_guard_primary_blocker_code",
        "runtime_recovery_guard_path",
        "paper_ledger_rollup_status",
        "paper_ledger_rollup_hash",
        "paper_ledger_rollup_primary_blocker_code",
        "paper_ledger_rollup_path",
        "paper_runtime_resume_allowed",
        "partial_write_recovery_required",
        "runtime_evidence_role",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "data_source_policy",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "loop_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPersistentLoopValidationResult("FAIL", f"persistent loop report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_PERSISTENT_LOOP_SCHEMA_ID:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("loop_hash") != upbit_paper_persistent_loop_hash(report):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    if report.get("requested_cycle_count") < 1 or report.get("requested_cycle_count") > report.get("max_cycle_count") or report.get("max_cycle_count") > DEFAULT_MAX_CYCLE_COUNT:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop exceeds bounded cycle budget", "RUNTIME_BUDGET_EXCEEDED")
    if report.get("symbol_universe_source") not in {
        "EXPLICIT_SYMBOL_UNIVERSE",
        "STATIC_FALLBACK_CONFIGURED_KRW_UNIVERSE",
        "STATIC_FALLBACK_PUBLIC_DISCOVERY_UNAVAILABLE",
        "STATIC_FALLBACK_PUBLIC_TICKER_UNAVAILABLE",
        "STATIC_FALLBACK_PUBLIC_RANKING_UNAVAILABLE",
        "PUBLIC_KRW_MARKET_DISCOVERY_TICKER_RANKED",
    }:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop symbol universe source is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("symbol_universe_discovery_status") not in {"SKIPPED", "PASS", "BLOCKED_FALLBACK"}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop discovery status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if not isinstance(report.get("symbol_universe"), list) or not report["symbol_universe"]:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop requires a non-empty symbol universe", "DATA_UNAVAILABLE")
    for count_field in (
        "symbol_universe_total_count",
        "symbol_universe_evaluated_count",
        "max_symbol_evaluation_count",
        "public_symbol_discovery_market_count",
        "public_ticker_ranked_symbol_count",
        "public_ticker_eligible_symbol_count",
    ):
        if not isinstance(report.get(count_field), int) or report[count_field] < 0:
            return UpbitPaperPersistentLoopValidationResult("FAIL", f"persistent loop symbol discovery count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    if report["symbol_universe_evaluated_count"] != len(report["symbol_universe"]):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop evaluated symbol count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report["symbol_universe_total_count"] < report["symbol_universe_evaluated_count"]:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop total symbol count is below evaluated count", "SCHEMA_IDENTITY_MISMATCH")
    if report["symbol_universe_evaluated_count"] > report["max_symbol_evaluation_count"]:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop exceeded symbol evaluation budget", "RUNTIME_BUDGET_EXCEEDED")
    if report.get("symbol_universe_discovery_status") == "PASS":
        if report.get("symbol_universe_source") != "PUBLIC_KRW_MARKET_DISCOVERY_TICKER_RANKED":
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS discovery must use public ticker-ranked source", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("symbol_universe_discovery_blocker_code") is not None:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS discovery cannot carry a blocker", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("public_symbol_discovery_attempted") is not True:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS discovery must mark discovery attempted", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("public_symbol_discovery_market_count", 0) < report.get("symbol_universe_total_count", 0):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "public discovery market count must cover total universe", "SCHEMA_IDENTITY_MISMATCH")
    elif str(report.get("symbol_universe_source", "")).startswith("STATIC_FALLBACK_PUBLIC"):
        if report.get("symbol_universe_discovery_status") != "BLOCKED_FALLBACK" or not report.get("symbol_universe_discovery_blocker_code"):
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "public discovery fallback must expose blocker", "DATA_UNAVAILABLE")
    elif report.get("symbol_universe_discovery_status") != "SKIPPED":
        return UpbitPaperPersistentLoopValidationResult("FAIL", "static or explicit universe must skip public discovery", "SCHEMA_IDENTITY_MISMATCH")
    for discovery_report_field in (
        "public_symbol_discovery_report",
        "public_ticker_snapshot_report",
        "public_symbol_ranking_report",
    ):
        discovery_report = report.get(discovery_report_field)
        if discovery_report is None:
            continue
        if not isinstance(discovery_report, dict):
            return UpbitPaperPersistentLoopValidationResult("FAIL", f"persistent loop discovery artifact must be object: {discovery_report_field}", "SCHEMA_IDENTITY_MISMATCH")
        if (
            discovery_report.get("live_order_ready")
            or discovery_report.get("live_order_allowed")
            or discovery_report.get("can_live_trade")
            or discovery_report.get("scale_up_allowed")
            or discovery_report.get("credential_load_attempted")
            or discovery_report.get("private_endpoint_called")
            or discovery_report.get("order_endpoint_called")
        ):
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "public discovery artifact attempted live, private, or order behavior", "LIVE_FINAL_GUARD_FAILED")
    forbidden_fields = (
        "long_run_evidence_eligible",
        "promotion_eligible",
        "credential_load_attempted",
        "private_endpoint_called",
        "order_endpoint_called",
        "order_adapter_called",
        "live_key_loaded",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(report.get(field) for field in forbidden_fields):
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop attempted live, private, order, promotion, or scale-up behavior", "LIVE_FINAL_GUARD_FAILED")
    preflight_status = report.get("preflight_recovery_guard_status")
    if preflight_status not in {"SKIPPED", "PASS", "BLOCKED"}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop preflight status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("preflight_existing_runtime_state_detected") is False and preflight_status != "SKIPPED":
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop preflight must be skipped when no prior runtime state exists", "SCHEMA_IDENTITY_MISMATCH")
    if preflight_status == "SKIPPED":
        if report.get("preflight_recovery_guard_hash") is not None or report.get("preflight_runtime_recovery_guard_path") is not None:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "skipped preflight cannot expose recovery guard artifacts", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("preflight_paper_runtime_resume_allowed") is not True:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "skipped preflight must allow initial PAPER runtime writes", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if report.get("preflight_recovery_guard_hash") in {None, ""} or report.get("preflight_runtime_recovery_guard_path") in {None, ""}:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop preflight recovery guard artifact is missing", "SCHEMA_IDENTITY_MISMATCH")
        if preflight_status == "PASS":
            if report.get("preflight_recovery_guard_primary_blocker_code") is not None or report.get("preflight_paper_runtime_resume_allowed") is not True:
                return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS preflight cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
            if report.get("current_evidence_write_allowed") is not True:
                return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS preflight must allow current PAPER evidence writes", "SCHEMA_IDENTITY_MISMATCH")
        if preflight_status == "BLOCKED":
            if report.get("preflight_paper_runtime_resume_allowed") or report.get("current_evidence_write_allowed"):
                return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked preflight cannot allow current PAPER evidence writes", "RECONCILIATION_REQUIRED")
            if report.get("preflight_recovery_guard_primary_blocker_code") is None:
                return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked preflight must expose primary blocker", "RECONCILIATION_REQUIRED")
    if report.get("recovery_guard_status") not in {"PASS", "BLOCKED"}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop recovery guard status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("recovery_guard_hash") in {None, ""}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop missing recovery guard hash", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_status") not in {"PASS", "BLOCKED"}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop ledger rollup status is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_hash") in {None, ""}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop missing ledger rollup hash", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_status") == "PASS" and report.get("paper_ledger_rollup_primary_blocker_code") is not None:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS ledger rollup cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("paper_ledger_rollup_status") == "BLOCKED" and report.get("paper_ledger_rollup_primary_blocker_code") is None:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked ledger rollup must expose primary blocker", "RECONCILIATION_REQUIRED")
    if report.get("recovery_guard_status") == "PASS":
        if report.get("recovery_guard_primary_blocker_code") is not None or report.get("partial_write_recovery_required"):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("paper_runtime_resume_allowed") is not True:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard must allow PAPER runtime resume", "SCHEMA_IDENTITY_MISMATCH")
    else:
        if report.get("paper_runtime_resume_allowed"):
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked recovery guard cannot allow PAPER runtime resume", "RECONCILIATION_REQUIRED")
        if not report.get("partial_write_recovery_required"):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "blocked recovery guard must expose recovery requirement", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("data_source_policy") != "PUBLIC_OR_STATIC_FIXTURE_ONLY":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop data source policy is unsafe", "LIVE_FINAL_GUARD_FAILED")
    if report.get("runtime_evidence_role") != BOUNDED_LOOP_RUNTIME_EVIDENCE_ROLE:
        return UpbitPaperPersistentLoopValidationResult(
            "BLOCKED",
            "bounded persistent loop must be marked as not long-run evidence",
            "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        )
    if report.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE or not report.get("long_run_next_action"):
        return UpbitPaperPersistentLoopValidationResult(
            "BLOCKED",
            "bounded persistent loop must expose the long-run evidence blocker and next action",
            "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        )
    completed_cycle_count = int(report.get("completed_cycle_count", -1))
    requested_cycle_count = int(report.get("requested_cycle_count", -1))
    if report.get("actual_paper_runtime_executed") is not (completed_cycle_count > 0):
        return UpbitPaperPersistentLoopValidationResult(
            "BLOCKED",
            "persistent loop runtime execution flag does not match completed cycle count",
            "MEASUREMENT_MISSING",
        )
    cycle_results = report.get("cycle_results")
    if not isinstance(cycle_results, list):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle results must be an array", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("current_evidence_write_allowed") is False:
        if cycle_results or completed_cycle_count != 0:
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "preflight-blocked loop cannot write current cycle evidence", "RECONCILIATION_REQUIRED")
    elif len(cycle_results) != report.get("requested_cycle_count"):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle result count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    seen_collector_ids: set[str] = set()
    seen_cycle_ids: set[str] = set()
    seen_collection_hashes: set[str] = set()
    seen_runtime_hashes: set[str] = set()
    pass_count = 0
    artifact_prefix = f"system/runtime/upbit/krw_spot/paper/{report.get('session_id')}/"
    for expected_index, item in enumerate(cycle_results, start=1):
        if not isinstance(item, dict):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle result must be an object", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("cycle_index") != expected_index:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle index sequence mismatch", "SCHEMA_IDENTITY_MISMATCH")
        collector_id = item.get("collector_id")
        cycle_id = item.get("cycle_id")
        collection_hash = item.get("collection_hash")
        runtime_hash = item.get("runtime_cycle_hash")
        for field_name, field_value in (
            ("collector_id", collector_id),
            ("cycle_id", cycle_id),
            ("collection_hash", collection_hash),
            ("runtime_cycle_hash", runtime_hash),
        ):
            if not isinstance(field_value, str) or not field_value:
                return UpbitPaperPersistentLoopValidationResult("FAIL", f"persistent loop missing cycle result field: {field_name}", "SCHEMA_IDENTITY_MISMATCH")
        if collector_id in seen_collector_ids or cycle_id in seen_cycle_ids:
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop duplicate cycle identity requires reconciliation", "RECONCILIATION_REQUIRED")
        if collection_hash in seen_collection_hashes or runtime_hash in seen_runtime_hashes:
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop duplicate source/runtime hash requires reconciliation", "RECONCILIATION_REQUIRED")
        seen_collector_ids.add(str(collector_id))
        seen_cycle_ids.add(str(cycle_id))
        seen_collection_hashes.add(str(collection_hash))
        seen_runtime_hashes.add(str(runtime_hash))
        artifact_paths = item.get("artifact_paths")
        if not isinstance(artifact_paths, list):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle artifact paths must be an array", "SCHEMA_IDENTITY_MISMATCH")
        for artifact_path in artifact_paths:
            if not isinstance(artifact_path, str) or not artifact_path.startswith(artifact_prefix) or ".." in artifact_path.replace("\\", "/").split("/"):
                return UpbitPaperPersistentLoopValidationResult(
                    "BLOCKED",
                    "persistent loop cycle artifact path escaped PAPER namespace",
                    "SNAPSHOT_SCOPE_MISMATCH",
                )
        if item.get("collection_status") != "PASS" or item.get("collection_writer_status") != "PASS":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop collection did not pass", "DATA_UNAVAILABLE")
        if item.get("runtime_status") != "PASS" or item.get("runtime_writer_status") != "PASS":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop runtime cycle did not pass", "RECONCILIATION_REQUIRED")
        if item.get("live_order_ready") or item.get("live_order_allowed") or item.get("can_live_trade") or item.get("scale_up_allowed"):
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "persistent loop cycle result attempted live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
        if item.get("runtime_input_role") not in {"PUBLIC_MARKET_DATA_COLLECTION", "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION"}:
            return UpbitPaperPersistentLoopValidationResult(
                "BLOCKED",
                "persistent loop cycle result is not bound to public market data collection input",
                "MEASUREMENT_MISSING",
            )
        if item.get("symbol_universe_source") not in {
            "EXPLICIT_SYMBOL_UNIVERSE",
            "SUPPLIED_MARKET_DATA_UNIVERSE",
            "SUPPLIED_SINGLE_MARKET_DATA",
            "STATIC_FALLBACK_CONFIGURED_KRW_UNIVERSE",
            "STATIC_FALLBACK_PUBLIC_DISCOVERY_UNAVAILABLE",
            "STATIC_FALLBACK_PUBLIC_TICKER_UNAVAILABLE",
            "STATIC_FALLBACK_PUBLIC_RANKING_UNAVAILABLE",
            "PUBLIC_KRW_MARKET_DISCOVERY_TICKER_RANKED",
        }:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle result symbol source is unknown", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(item.get("symbol_universe"), list) or item.get("selected_symbol") not in item["symbol_universe"]:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle selected symbol missing from universe", "SCHEMA_IDENTITY_MISMATCH")
        if not isinstance(item.get("symbol_universe_total_count"), int) or item["symbol_universe_total_count"] < len(item["symbol_universe"]):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle total symbol count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        if item.get("symbol_universe_evaluated_count") != len(item["symbol_universe"]):
            return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop cycle evaluated symbol count mismatch", "SCHEMA_IDENTITY_MISMATCH")
        for hash_field in (
            "source_collection_report_hash",
            "source_public_market_data_hash",
            "runtime_public_market_data_hash",
            "feature_snapshot_hash",
        ):
            if not _is_sha256(item.get(hash_field)):
                return UpbitPaperPersistentLoopValidationResult(
                    "FAIL",
                    f"persistent loop cycle result missing runtime depth hash field: {hash_field}",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
        if item.get("source_public_market_data_hash") != item.get("runtime_public_market_data_hash"):
            return UpbitPaperPersistentLoopValidationResult(
                "FAIL",
                "persistent loop cycle result source/runtime market data hash mismatch",
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if not isinstance(item.get("canonical_event_count"), int) or item["canonical_event_count"] < 5:
            return UpbitPaperPersistentLoopValidationResult(
                "BLOCKED",
                "persistent loop cycle result lacks public canonical event depth",
                "MEASUREMENT_MISSING",
            )
        linkage = item.get("strategy_regime_cost_linkage")
        if not isinstance(linkage, dict):
            return UpbitPaperPersistentLoopValidationResult(
                "FAIL",
                "persistent loop cycle result missing strategy/regime/cost linkage",
                "SCHEMA_IDENTITY_MISMATCH",
            )
        if linkage.get("live_order_ready") or linkage.get("live_order_allowed") or linkage.get("can_live_trade") or linkage.get("scale_up_allowed"):
            return UpbitPaperPersistentLoopValidationResult(
                "BLOCKED",
                "persistent loop strategy/regime/cost linkage attempted live or scale-up permission",
                "LIVE_FINAL_GUARD_FAILED",
            )
        expected_linkage = {
            "source_runtime_cycle_id": item.get("cycle_id"),
            "runtime_input_role": item.get("runtime_input_role"),
            "runtime_public_market_data_hash": item.get("runtime_public_market_data_hash"),
            "feature_snapshot_hash": item.get("feature_snapshot_hash"),
            "report_regime": item.get("regime"),
            "selected_candidate_id": item.get("selected_candidate_id"),
            "selected_candidate_net_ev_after_cost_bps": item.get("selected_candidate_net_ev_after_cost_bps"),
        }
        for field_name, expected_value in expected_linkage.items():
            if linkage.get(field_name) != expected_value:
                return UpbitPaperPersistentLoopValidationResult(
                    "FAIL",
                    f"persistent loop strategy/regime/cost linkage mismatch: {field_name}",
                    "SCHEMA_IDENTITY_MISMATCH",
                )
        pass_count += 1
    if report.get("completed_cycle_count") != pass_count:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "persistent loop completed count mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("loop_status") == "PASS" and completed_cycle_count != requested_cycle_count:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "PASS persistent loop must complete every requested cycle", "MEASUREMENT_MISSING")
    if report.get("loop_status") == "PASS" and report.get("primary_blocker_code") is not None:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS persistent loop cannot carry primary blocker", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("loop_status") == "PASS":
        return UpbitPaperPersistentLoopValidationResult("PASS", "Upbit PAPER persistent loop is bounded, public-data backed, and live-blocked", None)
    return UpbitPaperPersistentLoopValidationResult("BLOCKED", "Upbit PAPER persistent loop is blocked", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")


def validate_upbit_paper_runtime_recovery_guard_report(report: dict[str, Any]) -> UpbitPaperPersistentLoopValidationResult:
    required = {
        "schema_id",
        "generated_at_utc",
        "project_id",
        "guard_id",
        "loop_id",
        "exchange",
        "market_type",
        "mode",
        "session_id",
        "latest_cycle_path",
        "latest_cycle_status",
        "latest_cycle_hash",
        "latest_cycle_recoverable",
        "latest_cycle_contract_mode",
        "latest_cycle_schema_upgrade_required",
        "latest_cycle_schema_upgrade_reason",
        "canonical_jsonl_checked_count",
        "corrupted_jsonl_quarantined_count",
        "ledger_jsonl_checked_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "ledger_jsonl_invalid_count",
        "orphan_tmp_file_count",
        "artifact_paths",
        "recovery_guard_status",
        "primary_blocker_code",
        "blockers",
        "resume_action",
        "paper_runtime_resume_allowed",
        "runtime_evidence_role",
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "long_run_blocker_code",
        "long_run_next_action",
        "promotion_eligible",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "guard_hash",
    }
    missing = sorted(required - set(report))
    if missing:
        return UpbitPaperPersistentLoopValidationResult("FAIL", f"recovery guard report missing fields: {missing}", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("schema_id") != UPBIT_PAPER_RUNTIME_RECOVERY_GUARD_SCHEMA_ID:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("guard_hash") != upbit_paper_runtime_recovery_guard_hash(report):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("exchange") != "UPBIT" or report.get("market_type") != "KRW_SPOT" or report.get("mode") != "PAPER":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard scope must remain UPBIT/KRW_SPOT/PAPER", "SNAPSHOT_SCOPE_MISMATCH")
    latest_cycle_contract_mode = report.get("latest_cycle_contract_mode")
    legacy_components = (
        "QUANTITATIVE_POLICY_SUMMARY",
        "CURRENT_SIZING_EXPOSURE_CAP",
        "RUNTIME_RISK_EXIT_LIFECYCLE",
        "SYMBOL_EVIDENCE_SCORECARD",
        "ADAPTIVE_CANDIDATE_COST_MODEL",
        "POSITION_ROTATION_FIELDS",
        "SYMBOL_SELECTION_POLICY_FORMULA",
        "FEATURE_SNAPSHOT_PROJECTION",
        "SYMBOL_EVIDENCE_SCORECARD_PROJECTION",
    )
    legacy_modes = {
        "LEGACY_RECHECK_WITHOUT_" + "_AND_".join(
            component
            for bit, component in enumerate(legacy_components)
            if mask & (1 << bit)
        )
        for mask in range(1, 1 << len(legacy_components))
    }
    if latest_cycle_contract_mode not in {"CURRENT", *legacy_modes}:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard latest cycle contract mode is unknown", "SCHEMA_IDENTITY_MISMATCH")
    if latest_cycle_contract_mode == "CURRENT":
        if report.get("latest_cycle_schema_upgrade_required") is not False or report.get("latest_cycle_schema_upgrade_reason") is not None:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "current latest cycle cannot require schema upgrade", "SCHEMA_IDENTITY_MISMATCH")
    elif report.get("latest_cycle_schema_upgrade_required") is not True or not report.get("latest_cycle_schema_upgrade_reason"):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "legacy schema upgrade marker is incomplete", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("actual_long_run_evidence_created") or report.get("promotion_eligible"):
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard cannot create long-run or promotion evidence", "LIVE_FINAL_GUARD_FAILED")
    if report.get("long_run_evidence_eligible"):
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard cannot create long-run evidence eligibility", "LIVE_FINAL_GUARD_FAILED")
    if report.get("runtime_evidence_role") != RECOVERY_GUARD_RUNTIME_EVIDENCE_ROLE:
        return UpbitPaperPersistentLoopValidationResult(
            "BLOCKED",
            "recovery guard must be marked as resume-only, not long-run evidence",
            "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        )
    if report.get("long_run_blocker_code") != LONG_RUN_EVIDENCE_BLOCKER_CODE or not report.get("long_run_next_action"):
        return UpbitPaperPersistentLoopValidationResult(
            "BLOCKED",
            "recovery guard must expose the long-run evidence blocker and next action",
            "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        )
    if report.get("live_order_ready") or report.get("live_order_allowed") or report.get("can_live_trade") or report.get("scale_up_allowed"):
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard attempted live or scale-up permission", "LIVE_FINAL_GUARD_FAILED")
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard blockers must be an array", "SCHEMA_IDENTITY_MISMATCH")
    blocker_codes = {item.get("code") for item in blockers if isinstance(item, dict)}
    if blockers and report.get("primary_blocker_code") not in blocker_codes:
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "recovery guard primary blocker mismatch", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
    if not blockers and report.get("primary_blocker_code") is not None:
        return UpbitPaperPersistentLoopValidationResult("FAIL", "recovery guard primary blocker set without blockers", "SCHEMA_IDENTITY_MISMATCH")
    for count_field in (
        "canonical_jsonl_checked_count",
        "corrupted_jsonl_quarantined_count",
        "ledger_jsonl_checked_count",
        "corrupted_ledger_jsonl_quarantined_count",
        "ledger_jsonl_invalid_count",
        "orphan_tmp_file_count",
    ):
        if not isinstance(report.get(count_field), int) or report.get(count_field) < 0:
            return UpbitPaperPersistentLoopValidationResult("FAIL", f"recovery guard count is invalid: {count_field}", "SCHEMA_IDENTITY_MISMATCH")
    if (
        report.get("corrupted_jsonl_quarantined_count", 0) > 0
        or report.get("corrupted_ledger_jsonl_quarantined_count", 0) > 0
        or report.get("ledger_jsonl_invalid_count", 0) > 0
        or report.get("orphan_tmp_file_count", 0) > 0
    ):
        if report.get("recovery_guard_status") != "BLOCKED":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "partial write recovery must block resume", "PARTIAL_WRITE_RECOVERY_REQUIRED")
    if report.get("latest_cycle_status") != "PASS" or report.get("latest_cycle_recoverable") is not True:
        if report.get("recovery_guard_status") != "BLOCKED":
            return UpbitPaperPersistentLoopValidationResult("BLOCKED", "unrecoverable latest cycle cannot pass guard", "RECONCILIATION_REQUIRED")
    if report.get("recovery_guard_status") == "PASS":
        if blockers:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard cannot carry blockers", "SCHEMA_IDENTITY_MISMATCH")
        if report.get("resume_action") != "RESUME_PAPER_ONLY" or report.get("paper_runtime_resume_allowed") is not True:
            return UpbitPaperPersistentLoopValidationResult("FAIL", "PASS recovery guard must resume PAPER only", "SCHEMA_IDENTITY_MISMATCH")
        return UpbitPaperPersistentLoopValidationResult("PASS", "Upbit PAPER runtime recovery guard is recoverable and live-blocked", None)
    if report.get("paper_runtime_resume_allowed") or report.get("resume_action") != "SAFE_MODE_RECONCILE":
        return UpbitPaperPersistentLoopValidationResult("BLOCKED", "blocked recovery guard must use safe reconcile", "RECONCILIATION_REQUIRED")
    return UpbitPaperPersistentLoopValidationResult("BLOCKED", "Upbit PAPER runtime recovery guard is blocked", report.get("primary_blocker_code") or "UNKNOWN_BLOCKED")
