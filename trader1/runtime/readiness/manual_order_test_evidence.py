from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trader1.runtime.readiness.readiness_surface import blocker_object


MANUAL_ORDER_TEST_SCHEMA_ID = "trader1.manual_order_test_evidence.v1"


@dataclass(frozen=True)
class ManualOrderTestValidationResult:
    status: str
    message: str
    blocker_code: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def manual_order_test_hash(evidence: dict[str, Any]) -> str:
    payload = dict(evidence)
    payload.pop("evidence_hash", None)
    return _sha256_json(payload)


def build_missing_manual_order_test_evidence(
    *,
    authority: dict[str, str],
    test_id: str = "mvp4-manual-order-test-missing",
    exchange: str = "UPBIT",
    market_type: str = "KRW_SPOT",
    symbol: str = "KRW-BTC",
) -> dict[str, Any]:
    evidence = {
        "schema_id": MANUAL_ORDER_TEST_SCHEMA_ID,
        "test_id": test_id,
        "created_at_utc": utc_now(),
        "expires_at_utc": None,
        "project_id": "TRADER_1",
        "authority": authority,
        "exchange": exchange,
        "market_type": market_type,
        "mode": "LIVE",
        "api_key_id_hash": None,
        "symbol": symbol,
        "order_type": "NOT_APPLICABLE",
        "notional": None,
        "submit_result": "SKIPPED",
        "cancel_result": "NOT_APPLICABLE",
        "fill_result": "NOT_APPLICABLE",
        "ledger_recorded": False,
        "reconciliation_result": "SKIPPED",
        "fee_recorded": False,
        "balance_delta_verified": False,
        "order_id_masked": None,
        "blocker_codes": ["MANUAL_ORDER_TEST_MISSING"],
        "blockers": [
            blocker_object("MANUAL_ORDER_TEST_MISSING", source_contract_id="REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")
        ],
        "evidence_manifest_hash": None,
        "result": "MISSING",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "order_adapter_called": False,
        "evidence_hash": "",
    }
    evidence["evidence_hash"] = manual_order_test_hash(evidence)
    return evidence


def validate_manual_order_test_evidence(evidence: dict[str, Any]) -> ManualOrderTestValidationResult:
    if evidence.get("schema_id") != MANUAL_ORDER_TEST_SCHEMA_ID:
        return ManualOrderTestValidationResult("FAIL", "manual order test schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if evidence.get("evidence_hash") != manual_order_test_hash(evidence):
        return ManualOrderTestValidationResult("FAIL", "manual order test hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if evidence.get("exchange") != "UPBIT" or evidence.get("market_type") != "KRW_SPOT" or evidence.get("mode") != "LIVE":
        return ManualOrderTestValidationResult("BLOCKED", "manual order test scope mismatch", "SNAPSHOT_SCOPE_MISMATCH")
    if evidence.get("live_order_ready") or evidence.get("live_order_allowed") or evidence.get("can_live_trade") or evidence.get("order_adapter_called"):
        return ManualOrderTestValidationResult("BLOCKED", "manual order test evidence cannot create live permission", "LIVE_FINAL_GUARD_FAILED")
    if evidence.get("result") != "PASS":
        return ManualOrderTestValidationResult("BLOCKED", "manual order test evidence is missing or not PASS", "MANUAL_ORDER_TEST_MISSING")
    required_pass = {
        "submit_result": "PASS",
        "reconciliation_result": "PASS",
        "ledger_recorded": True,
        "fee_recorded": True,
        "balance_delta_verified": True,
    }
    for key, expected in required_pass.items():
        if evidence.get(key) != expected:
            return ManualOrderTestValidationResult("BLOCKED", f"manual order PASS missing {key}", "MANUAL_ORDER_TEST_MISSING")
    if evidence.get("blocker_codes") or evidence.get("blockers"):
        return ManualOrderTestValidationResult("BLOCKED", "manual order PASS cannot carry blockers", "MANUAL_ORDER_TEST_MISSING")
    return ManualOrderTestValidationResult("PASS", "manual order test evidence is scoped and complete")
