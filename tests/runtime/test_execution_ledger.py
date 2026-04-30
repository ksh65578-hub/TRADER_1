import unittest

from trader1.runtime.ledger.execution_ledger import (
    build_ledger_event,
    build_minimal_intent_chain,
    ledger_event_hash,
    validate_ledger_chain,
    validate_ledger_event,
)
from trader1.validation.mvp0_validators import run_validators


def build_chain():
    return build_minimal_intent_chain(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_execution_ledger",
        intent_id="intent-1",
        client_order_id="client-1",
        symbol="KRW-BTC",
        side="BUY",
    )


class ExecutionLedgerTest(unittest.TestCase):
    def test_minimal_intent_chain_is_hash_linked(self):
        chain = build_chain()
        result = validate_ledger_chain(chain)
        self.assertEqual(result.status, "PASS")
        self.assertIsNone(chain[0]["previous_hash"])
        self.assertEqual(chain[1]["previous_hash"], chain[0]["event_hash"])

    def test_unknown_event_type_requires_reconciliation(self):
        event = build_chain()[0]
        event["event_type"] = "UNKNOWN_EVENT"
        event["event_hash"] = ledger_event_hash(event)
        result = validate_ledger_event(event)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_hash_tamper_fails_integrity(self):
        event = build_chain()[0]
        event["symbol"] = "KRW-ETH"
        result = validate_ledger_event(event)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")

    def test_duplicate_dedup_key_requires_reconciliation(self):
        chain = build_chain()
        chain[1]["dedup_key"] = chain[0]["dedup_key"]
        chain[1]["event_hash"] = ledger_event_hash(chain[1])
        result = validate_ledger_chain(chain)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_duplicate_event_id_requires_reconciliation(self):
        chain = build_chain()
        chain[1]["event_id"] = chain[0]["event_id"]
        chain[1]["event_hash"] = ledger_event_hash(chain[1])
        result = validate_ledger_chain(chain)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_intent_event_ids_include_intent_id_for_cross_cycle_rollup(self):
        first = build_minimal_intent_chain(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_execution_ledger",
            intent_id="intent-a",
            client_order_id="client-a",
            symbol="KRW-BTC",
            side="BUY",
        )
        second = build_minimal_intent_chain(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_execution_ledger",
            intent_id="intent-b",
            client_order_id="client-b",
            symbol="KRW-BTC",
            side="BUY",
        )
        first_ids = {event["event_id"] for event in first}
        second_ids = {event["event_id"] for event in second}
        self.assertTrue(first_ids.isdisjoint(second_ids))

    def test_duplicate_semantic_event_requires_reconciliation(self):
        chain = build_chain()
        duplicate = build_ledger_event(
            event_id="test_execution_ledger-intent-duplicate",
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_execution_ledger",
            event_type="ORDER_INTENT_CREATED",
            source="LOCAL",
            dedup_key="intent:intent-1-duplicate",
            previous_hash=chain[-1]["event_hash"],
            intent_id="intent-1",
            client_order_id="client-1",
            symbol="KRW-BTC",
            side="BUY",
        )
        result = validate_ledger_chain([*chain, duplicate])
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_cross_scope_chain_is_blocked(self):
        chain = build_chain()
        chain[1]["exchange"] = "BINANCE"
        chain[1]["event_hash"] = ledger_event_hash(chain[1])
        result = validate_ledger_chain(chain)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_spot_short_event_is_blocked(self):
        event = build_ledger_event(
            event_id="short-1",
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_execution_ledger",
            event_type="ORDER_INTENT_CREATED",
            source="LOCAL",
            dedup_key="short-1",
            intent_id="short-intent",
            client_order_id="short-client",
            symbol="KRW-BTC",
            side="SELL_SHORT",
        )
        result = validate_ledger_event(event)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_ledger_durability_validator_passes_current_contract(self):
        results = run_validators(["ledger_durability_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
