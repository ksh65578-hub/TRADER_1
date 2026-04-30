from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_LIVE_TRUE_FIELDS = [
    "valid_live_ready_snapshot",
    "exact_scope_match",
    "official_api_verification_fresh",
    "manual_order_test_pass",
    "operator_approval_valid",
    "read_only_burn_in_pass",
    "emergency_protection_available",
    "ledger_reconciliation_pass",
    "blocking_validators_pass",
    "no_high_contract_gap",
    "no_critical_contract_gap",
    "live_final_guard_pass",
]


BLOCKED_CASES: dict[str, str] = {
    "live_ready_missing": "LIVE_READY_MISSING",
    "official_api_stale": "OFFICIAL_API_VERIFICATION_EXPIRED",
    "operator_approval_missing": "OPERATOR_APPROVAL_MISSING",
    "manual_order_test_missing": "MANUAL_ORDER_TEST_MISSING",
    "reconciliation_stale": "RECONCILIATION_REQUIRED",
    "symbol_rule_unknown": "SYMBOL_RULE_UNVERIFIED",
    "risk_veto_active": "RISK_VETO",
    "high_contract_gap": "CONTRACT_GAP_HIGH",
    "critical_contract_gap": "CONTRACT_GAP_CRITICAL",
    "stale_data": "STALE_ORDERBOOK",
    "validator_fail": "LIVE_FINAL_GUARD_FAILED",
    "source_identity_mismatch": "SOURCE_IDENTITY_MISMATCH",
    "emergency_flatten_unavailable": "EMERGENCY_FLATTEN_UNAVAILABLE",
    "final_guard_disabled": "LIVE_FINAL_GUARD_FAILED",
    "local_state_only_protection": "API_UNVERIFIED",
    "artifact_hygiene_fail": "BUNDLE_HYGIENE_FAIL",
    "config_invalid": "PREFLIGHT_FAILED",
    "edge_model_incomplete": "MEASUREMENT_MISSING",
    "sizing_trace_missing": "MEASUREMENT_MISSING",
    "regime_confidence_too_low": "STRATEGY_CONFIDENCE_LOW",
    "strategy_unit_scope_mismatch": "SNAPSHOT_SCOPE_MISMATCH",
    "active_snapshot_invalid": "SNAPSHOT_SCOPE_MISMATCH",
    "unvalidated_strategy_thresholds": "STRATEGY_NOT_ELIGIBLE",
    "spoofed_all_live_flags": "LIVE_ENABLING_EVIDENCE_MISSING",
    "spoofed_live_enabling_patch": "LIVE_ENABLING_EVIDENCE_MISSING",
}


@dataclass(frozen=True)
class LiveGateDecision:
    final_decision: str
    order_adapter_called: bool
    live_order_ready: bool
    live_order_allowed: bool
    can_live_trade: bool
    primary_blocker_code: str
    blockers: tuple[str, ...]


def evaluate_live_order_gate(signal: dict[str, Any]) -> LiveGateDecision:
    """Fail-closed MVP-0 live order gate.

    This function is intentionally conservative: it proves blocked behavior for
    negative test fixtures and does not submit or simulate live orders.
    """
    declared_blocker = signal.get("blocker_code")
    missing_requirements = [name for name in REQUIRED_LIVE_TRUE_FIELDS if signal.get(name) is not True]
    explicit_blockers = [str(code) for code in signal.get("blockers", []) if code]

    blocker_codes = []
    if declared_blocker:
        blocker_codes.append(str(declared_blocker))
    blocker_codes.extend(explicit_blockers)
    if missing_requirements and "LIVE_READY_MISSING" not in blocker_codes:
        blocker_codes.append("LIVE_READY_MISSING")

    live_order_ready = bool(signal.get("live_order_ready")) and not blocker_codes
    live_order_allowed = bool(signal.get("live_order_allowed")) and live_order_ready and not blocker_codes
    can_live_trade = bool(signal.get("can_live_trade")) and live_order_allowed and not blocker_codes

    if blocker_codes or not can_live_trade:
        return LiveGateDecision(
            final_decision="BLOCKED",
            order_adapter_called=False,
            live_order_ready=False,
            live_order_allowed=False,
            can_live_trade=False,
            primary_blocker_code=blocker_codes[0] if blocker_codes else "LIVE_READY_MISSING",
            blockers=tuple(blocker_codes or ["LIVE_READY_MISSING"]),
        )

    return LiveGateDecision(
        final_decision="BLOCKED",
        order_adapter_called=False,
        live_order_ready=False,
        live_order_allowed=False,
        can_live_trade=False,
        primary_blocker_code="LIVE_ENABLING_EVIDENCE_MISSING",
        blockers=("LIVE_ENABLING_EVIDENCE_MISSING",),
    )
