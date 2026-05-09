import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.core.ledger.paper_ledger import build_upbit_paper_fill_chain
from trader1.runtime.ledger.execution_ledger import build_ledger_event
from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    paper_ledger_head_report_hash,
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.runtime.ledger.paper_ledger_input_manifest import (
    build_paper_ledger_input_manifest,
    paper_ledger_input_manifest_hash,
    validate_paper_ledger_input_manifest,
    write_paper_ledger_input_manifest,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash
from trader1.validation.mvp0_validators import run_validators


class PaperLedgerRollupTest(unittest.TestCase):
    def _write_cycle_ledger(
        self,
        root: Path,
        cycle_id: str,
        client_order_id: str,
        price: str,
        *,
        symbol: str = "KRW-BTC",
        side: str = "BUY",
        quantity: str = "0.001",
        fee_amount: str = "1",
    ) -> tuple[Path, list[dict]]:
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
        ledger_dir.mkdir(parents=True, exist_ok=True)
        events = build_upbit_paper_fill_chain(
            session_id="mvp1_upbit_paper_launcher",
            symbol=symbol,
            intent_id=f"{cycle_id}-intent",
            client_order_id=client_order_id,
            side=side,
            quantity=quantity,
            price=price,
            fee_amount=fee_amount,
        )
        ledger_path = ledger_dir / f"{cycle_id}.paper_ledger_events.jsonl"
        ledger_path.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")
        return ledger_path, events

    def _write_latest_head(self, root: Path, cycle_id: str, ledger_path: Path, events: list[dict]) -> None:
        ledger_head = {
            "schema_id": "trader1.paper_ledger_head.v1",
            "generated_at_utc": "2026-05-01T00:00:00Z",
            "project_id": "TRADER_1",
            "exchange": "UPBIT",
            "market_type": "KRW_SPOT",
            "mode": "PAPER",
            "session_id": "mvp1_upbit_paper_launcher",
            "cycle_id": cycle_id,
            "ledger_event_count": len(events),
            "ledger_events_path": ledger_path.relative_to(root).as_posix(),
            "ledger_head_hash": events[-1]["event_hash"],
            "display_only": True,
            "dashboard_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        ledger_head["head_report_hash"] = paper_ledger_head_report_hash(ledger_head)
        (ledger_path.parents[1] / "latest_paper_ledger_head.json").write_text(json.dumps(ledger_head, indent=2), encoding="utf-8")

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
            self.assertEqual(rollup["ledger_input_scope"], "SESSION_REPAIR_MANIFEST")
            self.assertIn(
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_input_manifest.json",
                rollup["artifact_paths"],
            )
            self.assertEqual(rollup["ledger_jsonl_count"], 1)
            self.assertEqual(rollup["filled_order_count"], 1)
            self.assertEqual(rollup["duplicate_ledger_path_count"], 0)
            self.assertEqual(rollup["duplicate_event_count"], 0)
            self.assertEqual(rollup["duplicate_order_count"], 0)
            self.assertEqual(rollup["lifecycle_incomplete_order_count"], 0)
            self.assertEqual(rollup["ledger_head_match_status"], "PASS")
            self.assertEqual(rollup["ledger_head_mismatch_count"], 0)
            self.assertEqual(
                rollup["ledger_head_cycle_id"],
                "test-paper-ledger-rollup-cycle-1",
            )
            self.assertEqual(rollup["portfolio_snapshot"]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(
                rollup["portfolio_snapshot"]["source_runtime_cycle_id"],
                "test-paper-ledger-rollup-cycle-1",
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

    def test_rollup_passes_empty_no_trade_state_without_live_permission(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-empty-no-trade-rollup",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(rollup["ledger_jsonl_count"], 0)
            self.assertEqual(rollup["ledger_event_count"], 0)
            self.assertEqual(rollup["filled_order_count"], 0)
            self.assertEqual(rollup["ledger_head_match_status"], "NOT_APPLICABLE")
            self.assertEqual(rollup["portfolio_snapshot"]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(rollup["portfolio_snapshot"]["cash_available"], "1000000")
            self.assertEqual(rollup["portfolio_snapshot"]["open_position_count"], 0)
            self.assertFalse(rollup["live_order_ready"])
            self.assertFalse(rollup["live_order_allowed"])
            self.assertFalse(rollup["can_live_trade"])
            self.assertFalse(rollup["scale_up_allowed"])

    def test_persistent_loop_cash_guard_prevents_negative_rollup_during_repeated_runs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest_loop = None
            for index in range(4):
                latest_loop = run_upbit_paper_persistent_loop(
                    root=root,
                    loop_id=f"test-paper-ledger-cash-guard-{index + 1}",
                    requested_cycle_count=20,
                )

            self.assertIsNotNone(latest_loop)
            self.assertEqual(latest_loop["loop_status"], "PASS")
            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-cash-guard-rollup",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            self.assertLess(rollup["filled_order_count"], 80)
            self.assertGreaterEqual(float(rollup["portfolio_snapshot"]["cash_available"]), 0.0)
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_applies_sell_fills_to_cash_realized_pnl_and_open_quantity(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_cycle_ledger(
                root,
                "paper-rollup-buy-cycle",
                "paper-rollup-buy-client",
                "1000000",
                quantity="0.01",
                fee_amount="5",
            )
            sell_path, sell_events = self._write_cycle_ledger(
                root,
                "paper-rollup-sell-cycle",
                "paper-rollup-sell-client",
                "1100000",
                side="SELL",
                quantity="0.004",
                fee_amount="2",
            )
            self._write_latest_head(root, "paper-rollup-sell-cycle", sell_path, sell_events)

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-sell",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(rollup["filled_order_count"], 2)
            portfolio = rollup["portfolio_snapshot"]
            self.assertEqual(portfolio["cash_available"], "994393")
            self.assertEqual(portfolio["realized_pnl"], "396")
            self.assertEqual(portfolio["unrealized_pnl"], "597")
            self.assertEqual(portfolio["total_pnl"], "993")
            self.assertEqual(portfolio["open_position_count"], 1)
            self.assertEqual(portfolio["positions"][0]["quantity"], "0.006")
            self.assertEqual(portfolio["positions"][0]["mark_price"], "1100000")
            self.assertFalse(rollup["live_order_allowed"])

    def test_rollup_repairs_legacy_fixture_price_basis_before_public_price_sell(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_quantity = "0.3463095211056538627341496479"
            legacy_price = "1000550.025"
            public_sell_price = "118597831.4746155513075135494"
            sold_quantity = "0.001150372728159621253407039209"
            self._write_cycle_ledger(
                root,
                "paper-rollup-legacy-buy-cycle",
                "paper-rollup-legacy-buy-client",
                legacy_price,
                quantity=legacy_quantity,
                fee_amount="173.25",
            )
            sell_path, sell_events = self._write_cycle_ledger(
                root,
                "paper-rollup-public-sell-cycle",
                "paper-rollup-public-sell-client",
                public_sell_price,
                side="SELL",
                quantity=sold_quantity,
                fee_amount="68.21585544636981194186223329",
            )
            self._write_latest_head(root, "paper-rollup-public-sell-cycle", sell_path, sell_events)

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-legacy-public-sell",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            portfolio = rollup["portfolio_snapshot"]
            self.assertEqual(portfolio["open_position_count"], 1)
            position = portfolio["positions"][0]
            self.assertEqual(position["symbol"], "KRW-BTC")
            self.assertEqual(
                position["price_basis_repair_status"],
                "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION",
            )
            self.assertEqual(
                position["price_basis_repair_source"],
                "LEGACY_STATIC_FIXTURE_PRICE_BASIS_TO_UPBIT_KRW_BTC_PUBLIC_MARK",
            )
            original_cost = Decimal(legacy_quantity) * Decimal(legacy_price)
            normalized_quantity = original_cost / Decimal(public_sell_price)
            expected_remaining_quantity = normalized_quantity - Decimal(sold_quantity)
            remaining_quantity = Decimal(position["quantity"])
            average_entry = Decimal(position["average_entry_price"])
            market_value = Decimal(position["market_value"])

            self.assertGreater(remaining_quantity, Decimal("0"))
            self.assertLess(remaining_quantity, Decimal("0.01"))
            self.assertLess(abs(remaining_quantity - expected_remaining_quantity), Decimal("0.00000000000000000000000001"))
            self.assertLess(abs(average_entry - Decimal(public_sell_price)), Decimal("0.00000001"))
            self.assertLess(market_value, Decimal("250000"))
            self.assertEqual(position["price_basis_original_quantity"], legacy_quantity)
            self.assertFalse(rollup["live_order_ready"])
            self.assertFalse(rollup["live_order_allowed"])
            self.assertFalse(rollup["can_live_trade"])
            self.assertFalse(rollup["scale_up_allowed"])

            manifest = build_paper_ledger_input_manifest(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                manifest_id="test-paper-ledger-manifest-legacy-public-sell",
            )
            manifest_result = validate_paper_ledger_input_manifest(manifest)
            self.assertEqual(manifest_result.status, "PASS")
            self.assertEqual(manifest["accepted_ledger_path_count_at_manifest"], 2)
            self.assertEqual(manifest["excluded_ledger_path_count"], 0)
            write_paper_ledger_input_manifest(root=root, manifest=manifest)

            manifest_rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-manifest-rollup-legacy-public-sell",
            )
            manifest_rollup_result = validate_paper_ledger_rollup_report(manifest_rollup)
            self.assertEqual(manifest_rollup_result.status, "PASS")
            self.assertEqual(manifest_rollup["ledger_input_scope"], "SESSION_REPAIR_MANIFEST")
            self.assertEqual(manifest_rollup["ledger_jsonl_count"], 2)
            self.assertEqual(
                manifest_rollup["portfolio_snapshot"]["positions"][0]["price_basis_repair_status"],
                "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION",
            )

    def test_rollup_repairs_legacy_fixture_altcoin_price_basis_before_public_price_sell(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_quantity = "0.007"
            legacy_price = "1000870"
            public_sell_price = "405"
            sold_quantity = "4"
            self._write_cycle_ledger(
                root,
                "paper-rollup-legacy-ada-buy-cycle",
                "paper-rollup-legacy-ada-buy-client",
                legacy_price,
                symbol="KRW-ADA",
                quantity=legacy_quantity,
                fee_amount="3",
            )
            sell_path, sell_events = self._write_cycle_ledger(
                root,
                "paper-rollup-public-ada-sell-cycle",
                "paper-rollup-public-ada-sell-client",
                public_sell_price,
                symbol="KRW-ADA",
                side="SELL",
                quantity=sold_quantity,
                fee_amount="1",
            )
            self._write_latest_head(root, "paper-rollup-public-ada-sell-cycle", sell_path, sell_events)

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-legacy-alt-public-sell",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            portfolio = rollup["portfolio_snapshot"]
            self.assertEqual(portfolio["open_position_count"], 1)
            position = portfolio["positions"][0]
            self.assertEqual(position["symbol"], "KRW-ADA")
            self.assertEqual(
                position["price_basis_repair_status"],
                "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION",
            )
            self.assertEqual(
                position["price_basis_repair_source"],
                "LEGACY_STATIC_FIXTURE_PRICE_BASIS_TO_UPBIT_KRW_SPOT_PUBLIC_MARK",
            )
            original_cost = Decimal(legacy_quantity) * Decimal(legacy_price)
            normalized_quantity = original_cost / Decimal(public_sell_price)
            expected_remaining_quantity = normalized_quantity - Decimal(sold_quantity)

            self.assertGreater(Decimal(position["quantity"]), Decimal("0"))
            self.assertLess(
                abs(Decimal(position["quantity"]) - expected_remaining_quantity),
                Decimal("0.00000000000000000000000001"),
            )
            self.assertEqual(position["average_entry_price"], public_sell_price)
            self.assertEqual(position["mark_price"], public_sell_price)
            self.assertFalse(rollup["live_order_ready"])
            self.assertFalse(rollup["live_order_allowed"])
            self.assertFalse(rollup["can_live_trade"])
            self.assertFalse(rollup["scale_up_allowed"])

    def test_input_manifest_filters_cash_overrun_ledgers_from_default_rollup(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest_path = None
            latest_events = None
            latest_cycle_id = None
            for index in range(12):
                cycle_id = f"cash-overrun-cycle-{index + 1:02d}"
                latest_path, latest_events = self._write_cycle_ledger(
                    root,
                    cycle_id,
                    f"client-cash-overrun-{index + 1:02d}",
                    "100000000",
                )
                latest_cycle_id = cycle_id
            self.assertIsNotNone(latest_path)
            self.assertIsNotNone(latest_events)
            self.assertIsNotNone(latest_cycle_id)
            self._write_latest_head(root, str(latest_cycle_id), latest_path, latest_events)

            blocked_rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-overrun-blocked",
            )
            blocked_result = validate_paper_ledger_rollup_report(blocked_rollup)
            self.assertEqual(blocked_result.status, "BLOCKED")
            self.assertEqual(blocked_result.blocker_code, "RISK_VETO")

            manifest = build_paper_ledger_input_manifest(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                manifest_id="test-paper-ledger-input-manifest",
            )
            manifest_result = validate_paper_ledger_input_manifest(manifest)
            self.assertEqual(manifest_result.status, "PASS")
            self.assertEqual(manifest["accepted_ledger_path_count_at_manifest"], 3)
            self.assertEqual(manifest["excluded_ledger_path_count"], 9)
            self.assertTrue(
                {
                    item["exclude_reason_code"]
                    for item in manifest["excluded_ledger_paths"]
                }.issubset({"EXPOSURE_CAP_EXCEEDED", "CASH_BELOW_ZERO"})
            )
            manifest_path = write_paper_ledger_input_manifest(root=root, manifest=manifest)
            self.assertTrue(manifest_path.exists())

            repaired_rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-overrun-repaired",
            )
            repaired_result = validate_paper_ledger_rollup_report(repaired_rollup)
            self.assertEqual(repaired_result.status, "PASS")
            self.assertEqual(repaired_rollup["ledger_input_scope"], "SESSION_REPAIR_MANIFEST")
            self.assertEqual(repaired_rollup["ledger_jsonl_count"], 3)
            self.assertEqual(repaired_rollup["filled_order_count"], 3)
            self.assertEqual(repaired_rollup["ledger_head_match_status"], "NOT_APPLICABLE")
            self.assertIn(
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_input_manifest.json",
                repaired_rollup["artifact_paths"],
            )
            self.assertFalse(repaired_rollup["live_order_allowed"])

    def test_manifest_rollup_ignores_stale_excluded_ledger_paths_after_cleanup(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest_path = None
            latest_events = None
            latest_cycle_id = None
            for index in range(12):
                cycle_id = f"stale-excluded-cycle-{index + 1:02d}"
                latest_path, latest_events = self._write_cycle_ledger(
                    root,
                    cycle_id,
                    f"client-stale-excluded-{index + 1:02d}",
                    "100000000",
                )
                latest_cycle_id = cycle_id
            self.assertIsNotNone(latest_path)
            self.assertIsNotNone(latest_events)
            self.assertIsNotNone(latest_cycle_id)
            self._write_latest_head(root, str(latest_cycle_id), latest_path, latest_events)

            manifest = build_paper_ledger_input_manifest(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                manifest_id="test-paper-ledger-stale-excluded-manifest",
            )
            manifest_result = validate_paper_ledger_input_manifest(manifest)
            self.assertEqual(manifest_result.status, "PASS")
            self.assertGreater(manifest["excluded_ledger_path_count"], 0)
            stale_excluded_path = root / manifest["excluded_ledger_paths"][0]["path"]
            write_paper_ledger_input_manifest(root=root, manifest=manifest)
            stale_excluded_path.unlink()

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-stale-excluded-rollup",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(rollup["ledger_input_scope"], "SESSION_REPAIR_MANIFEST")
            self.assertNotIn(stale_excluded_path.relative_to(root).as_posix(), rollup["artifact_paths"])
            self.assertFalse(rollup["live_order_allowed"])

    def test_manifest_rollup_ignores_stale_latest_head_target_after_cleanup(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_path, first_events = self._write_cycle_ledger(
                root,
                "stale-head-surviving-cycle",
                "client-stale-head-surviving",
                "1000000",
            )
            latest_path, latest_events = self._write_cycle_ledger(
                root,
                "stale-head-missing-cycle",
                "client-stale-head-missing",
                "1000100",
            )
            self._write_latest_head(root, "stale-head-missing-cycle", latest_path, latest_events)

            manifest = build_paper_ledger_input_manifest(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                manifest_id="test-paper-ledger-stale-head-manifest",
            )
            manifest_result = validate_paper_ledger_input_manifest(manifest)
            self.assertEqual(manifest_result.status, "PASS")
            self.assertEqual(manifest["accepted_ledger_path_count_at_manifest"], 2)
            write_paper_ledger_input_manifest(root=root, manifest=manifest)
            latest_path.unlink()

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-stale-head-rollup",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(rollup["ledger_input_scope"], "SESSION_REPAIR_MANIFEST")
            self.assertEqual(rollup["ledger_jsonl_count"], 1)
            self.assertEqual(rollup["ledger_head_match_status"], "NOT_APPLICABLE")
            self.assertEqual(rollup["portfolio_snapshot"]["source_runtime_cycle_id"], "stale-head-surviving-cycle")
            self.assertEqual(rollup["latest_ledger_head_hash"], first_events[-1]["event_hash"])
            self.assertFalse(rollup["live_order_allowed"])

    def test_input_manifest_accounts_for_sell_fills_before_exposure_filtering(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_cycle_ledger(
                root,
                "manifest-buy-cycle",
                "manifest-buy-client",
                "1000000",
                quantity="0.005",
                fee_amount="1",
            )
            sell_path, sell_events = self._write_cycle_ledger(
                root,
                "manifest-sell-cycle",
                "manifest-sell-client",
                "1010000",
                side="SELL",
                quantity="0.005",
                fee_amount="1",
            )
            self._write_latest_head(root, "manifest-sell-cycle", sell_path, sell_events)

            manifest = build_paper_ledger_input_manifest(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                manifest_id="test-paper-ledger-input-manifest-sell-aware",
            )
            manifest_result = validate_paper_ledger_input_manifest(manifest)
            self.assertEqual(manifest_result.status, "PASS")
            self.assertEqual(manifest["accepted_ledger_path_count_at_manifest"], 2)
            self.assertEqual(manifest["excluded_ledger_path_count"], 0)
            self.assertEqual(manifest["final_position_market_value_after_accepted"], "0")
            self.assertEqual(manifest["final_cash_available_after_accepted"], "1000048")
            write_paper_ledger_input_manifest(root=root, manifest=manifest)

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-sell-aware-manifest",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(rollup["ledger_input_scope"], "SESSION_REPAIR_MANIFEST")
            self.assertEqual(rollup["portfolio_snapshot"]["open_position_count"], 0)
            self.assertEqual(rollup["portfolio_snapshot"]["position_market_value"], "0")
            self.assertEqual(rollup["portfolio_snapshot"]["cash_available"], "1000048")
            self.assertFalse(rollup["live_order_allowed"])

    def test_input_manifest_blocks_live_permission_mutation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_cycle_ledger(root, "manifest-live-mutation-cycle", "manifest-live-client", "1000000")
            manifest = build_paper_ledger_input_manifest(root=root, session_id="mvp1_upbit_paper_launcher")
            manifest["live_order_allowed"] = True
            manifest["manifest_hash"] = paper_ledger_input_manifest_hash(manifest)

            result = validate_paper_ledger_input_manifest(manifest)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_session_glob_binds_portfolio_to_latest_head_when_filename_sort_differs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_path, current_events = self._write_cycle_ledger(
                root,
                "aaa-current-head-cycle",
                "client-current-head",
                "1000000",
            )
            self._write_cycle_ledger(
                root,
                "zzz-older-lexicographic-tail-cycle",
                "client-older-tail",
                "1000100",
            )
            self._write_latest_head(root, "aaa-current-head-cycle", current_path, current_events)

            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-paper-ledger-rollup-head-order",
            )
            result = validate_paper_ledger_rollup_report(rollup)

            self.assertEqual(result.status, "PASS")
            self.assertEqual(rollup["ledger_jsonl_count"], 2)
            self.assertEqual(rollup["filled_order_count"], 2)
            self.assertEqual(rollup["ledger_head_match_status"], "PASS")
            self.assertEqual(rollup["ledger_head_cycle_id"], "aaa-current-head-cycle")
            self.assertEqual(rollup["latest_ledger_head_hash"], current_events[-1]["event_hash"])
            self.assertEqual(rollup["portfolio_snapshot"]["source_runtime_cycle_id"], "aaa-current-head-cycle")
            self.assertEqual(rollup["portfolio_snapshot"]["source_paper_ledger_head_hash"], current_events[-1]["event_hash"])
            self.assertFalse(rollup["live_order_allowed"])

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
