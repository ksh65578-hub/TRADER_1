import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.ledger.execution_ledger import build_ledger_event
from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    paper_ledger_head_report_hash,
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash
from trader1.validation.mvp0_validators import run_validators


class PaperLedgerRollupTest(unittest.TestCase):
    def test_rollup_aggregates_multiple_cycle_ledgers_and_remains_live_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup",
                requested_cycle_count=2,
            )
            rollup_path = root / loop["paper_ledger_rollup_path"]
            rollup = json.loads(rollup_path.read_text(encoding="utf-8"))
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(rollup["ledger_input_scope"], "SESSION_CYCLE_GLOB")
            self.assertEqual(rollup["ledger_jsonl_count"], 2)
            self.assertEqual(rollup["filled_order_count"], 2)
            self.assertEqual(rollup["duplicate_ledger_path_count"], 0)
            self.assertEqual(rollup["duplicate_event_count"], 0)
            self.assertEqual(rollup["duplicate_order_count"], 0)
            self.assertEqual(rollup["lifecycle_incomplete_order_count"], 0)
            self.assertEqual(rollup["ledger_head_match_status"], "PASS")
            self.assertEqual(rollup["ledger_head_mismatch_count"], 0)
            self.assertEqual(
                rollup["ledger_head_cycle_id"],
                "test-paper-ledger-rollup-cycle-2",
            )
            self.assertEqual(rollup["portfolio_snapshot"]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(
                rollup["portfolio_snapshot"]["source_runtime_cycle_id"],
                "test-paper-ledger-rollup-cycle-2",
            )
            self.assertEqual(
                rollup["portfolio_snapshot"]["source_paper_ledger_head_hash"],
                rollup["latest_ledger_head_hash"],
            )
            self.assertEqual(rollup["portfolio_snapshot"]["open_position_count"], 1)
            self.assertFalse(rollup["live_order_ready"])
            self.assertFalse(rollup["live_order_allowed"])
            self.assertFalse(rollup["can_live_trade"])
            self.assertFalse(rollup["scale_up_allowed"])

    def test_rollup_blocks_duplicate_cross_cycle_ledger_events(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-duplicate",
                requested_cycle_count=1,
            )
            ledger_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".paper_ledger_events.jsonl"):
                    ledger_path = root / artifact_path
                    break
            self.assertIsNotNone(ledger_path)
            duplicate_path = ledger_path.with_name("duplicate-cross-cycle.paper_ledger_events.jsonl")
            duplicate_path.write_text(ledger_path.read_text(encoding="utf-8"), encoding="utf-8")

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-duplicate",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
            self.assertGreater(rollup["duplicate_event_count"], 0)
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_blocks_filled_order_without_complete_lifecycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger_dir = (
                root
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / "mvp1_upbit_paper_launcher"
                / "ledger"
                / "cycles"
            )
            ledger_dir.mkdir(parents=True)
            intent = build_ledger_event(
                event_id="incomplete-cycle-intent",
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                event_type="ORDER_INTENT_CREATED",
                source="LOCAL",
                dedup_key="intent:incomplete",
                intent_id="intent-incomplete",
                client_order_id="client-incomplete",
                symbol="KRW-BTC",
                side="BUY",
            )
            reservation = build_ledger_event(
                event_id="incomplete-cycle-reserve",
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                event_type="BUDGET_RESERVED",
                source="LOCAL",
                dedup_key="reserve:incomplete",
                previous_hash=intent["event_hash"],
                intent_id="intent-incomplete",
                client_order_id="client-incomplete",
                symbol="KRW-BTC",
                side="BUY",
            )
            filled = build_ledger_event(
                event_id="incomplete-cycle-filled",
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id="mvp1_upbit_paper_launcher",
                event_type="ORDER_FILLED",
                source="LOCAL",
                dedup_key="filled:incomplete",
                previous_hash=reservation["event_hash"],
                intent_id="intent-incomplete",
                client_order_id="client-incomplete",
                order_id="PAPER-client-incomplete",
                symbol="KRW-BTC",
                side="BUY",
                quantity="0.001",
                price="100000000",
                fee_amount="50",
                fee_asset="KRW",
                balance_delta={"KRW": "-50"},
                position_delta={"symbol": "KRW-BTC", "quantity": "0.001", "side": "BUY"},
            )
            ledger_path = ledger_dir / "incomplete-cycle.paper_ledger_events.jsonl"
            ledger_path.write_text(
                "\n".join(json.dumps(event, sort_keys=True) for event in (intent, reservation, filled)) + "\n",
                encoding="utf-8",
            )

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-lifecycle-incomplete",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
            self.assertEqual(rollup["lifecycle_incomplete_order_count"], 1)
            self.assertEqual(rollup["invalid_ledger_jsonl_count"], 1)
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_quarantines_partial_ledger_jsonl_and_blocks_resume_review(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-partial",
                requested_cycle_count=1,
            )
            ledger_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".paper_ledger_events.jsonl"):
                    ledger_path = root / artifact_path
                    break
            self.assertIsNotNone(ledger_path)
            with ledger_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-partial",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertEqual(rollup["corrupted_ledger_jsonl_quarantined_count"], 1)
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_blocks_scope_and_live_permission_mutation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-mutation",
                requested_cycle_count=1,
            )
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))

        scope_mutation = dict(rollup)
        scope_mutation["market_type"] = "SPOT"
        scope_mutation["rollup_hash"] = paper_ledger_rollup_hash(scope_mutation)
        scope_result = validate_paper_ledger_rollup_report(scope_mutation)
        self.assertEqual(scope_result.status, "BLOCKED")
        self.assertEqual(scope_result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

        live_mutation = dict(rollup)
        live_mutation["live_order_allowed"] = True
        live_mutation["rollup_hash"] = paper_ledger_rollup_hash(live_mutation)
        live_result = validate_paper_ledger_rollup_report(live_mutation)
        self.assertEqual(live_result.status, "BLOCKED")
        self.assertEqual(live_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_rollup_blocks_cross_scope_portfolio_snapshot(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-portfolio-scope",
                requested_cycle_count=1,
            )
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))

        rollup["portfolio_snapshot"]["exchange"] = "BINANCE"
        rollup["portfolio_snapshot"]["market_type"] = "SPOT"
        rollup["portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(rollup["portfolio_snapshot"])
        rollup["rollup_hash"] = paper_ledger_rollup_hash(rollup)

        result = validate_paper_ledger_rollup_report(rollup)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_rollup_blocks_filled_count_portfolio_mismatch(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-count-mismatch",
                requested_cycle_count=1,
            )
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))

        rollup["filled_order_count"] = 0
        rollup["rollup_hash"] = paper_ledger_rollup_hash(rollup)

        result = validate_paper_ledger_rollup_report(rollup)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_rollup_blocks_portfolio_ledger_head_provenance_mismatch(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-provenance-mismatch",
                requested_cycle_count=1,
            )
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))

        rollup["portfolio_snapshot"]["source_paper_ledger_head_hash"] = "F" * 64
        rollup["portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(rollup["portfolio_snapshot"])
        rollup["rollup_hash"] = paper_ledger_rollup_hash(rollup)

        result = validate_paper_ledger_rollup_report(rollup)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")

    def test_rollup_blocks_artifact_path_escape(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-path-escape",
                requested_cycle_count=1,
            )
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))

        rollup["artifact_paths"].append("system/runtime/upbit/krw_spot/live/mvp1_upbit_paper_launcher/ledger/unsafe.json")
        rollup["rollup_hash"] = paper_ledger_rollup_hash(rollup)

        result = validate_paper_ledger_rollup_report(rollup)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_rollup_blocks_duplicate_explicit_ledger_paths(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-duplicate-path",
                requested_cycle_count=1,
            )
            ledger_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".paper_ledger_events.jsonl"):
                    ledger_path = root / artifact_path
                    break
            self.assertIsNotNone(ledger_path)

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-duplicate-path",
                ledger_paths=[ledger_path, ledger_path],
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")
            self.assertEqual(rollup["ledger_input_scope"], "EXPLICIT_SCOPED_PATHS")
            self.assertEqual(rollup["duplicate_ledger_path_count"], 1)
            self.assertEqual(rollup["ledger_head_match_status"], "NOT_APPLICABLE")
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_blocks_missing_latest_ledger_head_report(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-missing-head",
                requested_cycle_count=1,
            )
            head_path = (
                root
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / "mvp1_upbit_paper_launcher"
                / "ledger"
                / "latest_paper_ledger_head.json"
            )
            head_path.unlink()

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-missing-head",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")
            self.assertEqual(rollup["ledger_head_match_status"], "MISSING")
            self.assertEqual(rollup["ledger_head_mismatch_count"], 1)
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_blocks_mismatched_latest_ledger_head_report(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-paper-ledger-rollup-mismatched-head",
                requested_cycle_count=1,
            )
            head_path = (
                root
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / "mvp1_upbit_paper_launcher"
                / "ledger"
                / "latest_paper_ledger_head.json"
            )
            ledger_head = json.loads(head_path.read_text(encoding="utf-8"))
            ledger_head["ledger_head_hash"] = "F" * 64
            ledger_head["head_report_hash"] = paper_ledger_head_report_hash(ledger_head)
            head_path.write_text(json.dumps(ledger_head, sort_keys=True), encoding="utf-8")

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-mismatched-head",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")
            self.assertEqual(rollup["ledger_head_match_status"], "MISMATCH")
            self.assertGreater(rollup["ledger_head_mismatch_count"], 0)
            self.assertFalse(rollup["live_order_allowed"])

    def test_paper_ledger_rollup_validator_passes_current_contract(self):
        results = run_validators(["paper_ledger_rollup_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
