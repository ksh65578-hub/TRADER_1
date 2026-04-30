from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any


RUNTIME_ROOTS_WITH_MODE = {
    "data",
    "logs",
    "runtime",
    "reports",
    "validation",
}

RUNTIME_ROOTS_WITH_SESSION = {
    "evidence",
}

DASHBOARD_SERVING_TRUTH = {
    "summary.json",
    "heartbeat.json",
    "startup_probe.json",
    "action_queue.json",
    "operator_status.json",
    "readiness_surface.json",
    "recent_no_trade_context.json",
    "recent_entry_context.json",
}

EXECUTION_TRUTH_ROLES = {
    "ledger",
    "intent_wal",
    "order_events",
    "fill_events",
    "balance_snapshots",
    "position_snapshots",
    "exchange_reconciliation_snapshot",
    "risk_decisions",
    "final_decisions",
}

TRUTH_RANK = {
    "execution_truth": 4,
    "exchange_reconciliation_snapshot": 3,
    "analysis_truth": 2,
    "dashboard_serving_truth": 1,
}


@dataclass(frozen=True)
class NamespaceScope:
    exchange: str
    market_type: str
    mode: str
    session_id: str | None = None
    strategy_id: str | None = None
    symbol: str | None = None


@dataclass(frozen=True)
class NamespaceValidationResult:
    status: str
    blocker_code: str | None
    message: str


def _slug_map(registry: dict[str, Any]) -> dict[str, str]:
    return registry.get("path_slugs", {})


def _scope_slugs(scope: NamespaceScope, registry: dict[str, Any]) -> tuple[str, str, str]:
    slugs = _slug_map(registry)
    return slugs.get(scope.exchange, scope.exchange.lower()), slugs.get(scope.market_type, scope.market_type.lower()), slugs.get(scope.mode, scope.mode.lower())


def artifact_path(root: str, scope: NamespaceScope, registry: dict[str, Any], filename: str | None = None) -> str:
    exchange, market_type, mode = _scope_slugs(scope, registry)
    parts = ["system", root, exchange, market_type]
    if root == "snapshots":
        parts.append("LIVE_READY")
    else:
        parts.append(mode)
    if root in RUNTIME_ROOTS_WITH_SESSION:
        if not scope.session_id:
            raise ValueError("session_id is required for evidence artifacts")
        parts.append(scope.session_id)
    if filename:
        parts.append(filename)
    return "/".join(parts)


def validate_artifact_path(path: str, scope: NamespaceScope, registry: dict[str, Any]) -> NamespaceValidationResult:
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if len(parts) < 4 or parts[0] != "system":
        return NamespaceValidationResult("FAIL", "SNAPSHOT_SCOPE_MISMATCH", "artifact path must start with system/<root>/<exchange>/<market_type>")
    root = parts[1]
    exchange, market_type, mode = _scope_slugs(scope, registry)
    if parts[2] != exchange or parts[3] != market_type:
        return NamespaceValidationResult("FAIL", "SNAPSHOT_SCOPE_MISMATCH", "artifact exchange or market_type segment does not match scope")
    if root in RUNTIME_ROOTS_WITH_MODE:
        if len(parts) < 5 or parts[4] != mode:
            return NamespaceValidationResult("FAIL", "SNAPSHOT_SCOPE_MISMATCH", "artifact mode segment does not match scope")
    if root in RUNTIME_ROOTS_WITH_SESSION:
        if len(parts) < 6 or parts[4] != mode or parts[5] != scope.session_id:
            return NamespaceValidationResult("FAIL", "SNAPSHOT_SCOPE_MISMATCH", "evidence artifact mode or session segment does not match scope")
    if root == "snapshots":
        if len(parts) < 5 or parts[4] != "LIVE_READY":
            return NamespaceValidationResult("FAIL", "SNAPSHOT_SCOPE_MISMATCH", "snapshot path must use LIVE_READY namespace")
    return NamespaceValidationResult("PASS", None, "artifact path is namespace scoped")


def validate_namespace_join(left: NamespaceScope, right: NamespaceScope) -> NamespaceValidationResult:
    if left.exchange != right.exchange:
        return NamespaceValidationResult("BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "cross-exchange raw data join is forbidden")
    if left.market_type != right.market_type:
        return NamespaceValidationResult("BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "cross-market_type raw data join is forbidden")
    if left.mode != right.mode:
        return NamespaceValidationResult("BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "cross-mode raw data join is forbidden")
    if left.session_id and right.session_id and left.session_id != right.session_id:
        return NamespaceValidationResult("BLOCKED", "SNAPSHOT_SCOPE_MISMATCH", "cross-session raw data join is forbidden")
    return NamespaceValidationResult("PASS", None, "namespace join is scoped")


def validate_truth_override(source_role: str, target_role: str) -> NamespaceValidationResult:
    if source_role not in TRUTH_RANK or target_role not in TRUTH_RANK:
        return NamespaceValidationResult("FAIL", "UNKNOWN_BLOCKED", "unknown truth role")
    if TRUTH_RANK[source_role] < TRUTH_RANK[target_role]:
        return NamespaceValidationResult("BLOCKED", "LIVE_FINAL_GUARD_FAILED", "lower truth tier cannot override higher truth tier")
    return NamespaceValidationResult("PASS", None, "truth hierarchy preserved")


def classify_dashboard_artifact(filename: str) -> str:
    return "dashboard_serving_truth" if filename in DASHBOARD_SERVING_TRUTH else "analysis_truth"
