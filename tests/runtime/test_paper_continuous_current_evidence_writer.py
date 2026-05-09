import json
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    AUDITED_WRITER_UNVERIFIED_COLLECTION_STATUS,
    AUDITED_WRITER_REFRESHED_STATUS,
    EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    upbit_paper_repaired_current_evidence_audited_writer_report_hash,
)
from trader1.runtime.portfolio.paper_continuous_current_evidence_writer import (
    PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS,
    PAPER_CONTINUOUS_WRITER_REVIEW_ONLY_STATUS,
    PAPER_CONTINUOUS_WRITER_STALE_STATUS,
    PAPER_CONTINUOUS_WRITER_WRITING_STATUS,
    build_paper_continuous_current_evidence_writer_report,
    paper_continuous_current_evidence_writer_report_hash,
    validate_paper_continuous_current_evidence_writer_report,
)
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.runtime.portfolio.paper_current_truth_refresh import build_paper_current_truth_refresh_report
from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash


ROOT = Path(__file__).resolve().parents[2]
SESSION_ID = "mvp1_upbit_paper_launcher"
RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
SOURCE_IMPLEMENTATION_PREP_PATH = (
    RUNTIME_BASE
    / "paper_runtime"
    / "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json"
)
SOURCE_LEDGER_ROLLUP_PATH = RUNTIME_BASE / "ledger" / "paper_ledger_rollup_report.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def plus_seconds(value: str, seconds: int) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parsed + timedelta(seconds=seconds)).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PaperContinuousCurrentEvidenceWriterTest(unittest.TestCase):
    def _public_collection(self, *, close: str, symbol: str) -> dict:
        payload = []
        close_value = Decimal(close)
        step = max(Decimal("0.0001"), abs(close_value) * Decimal("0.001"))
        for offset in range(6):
            minute = 35 - offset
            trade_price = close_value - Decimal(offset) * step
            payload.append(
                {
                    "market": symbol,
                    "candle_date_time_utc": f"2026-05-06T21:{minute:02d}:00",
                    "opening_price": format(trade_price - (step / Decimal("2")), "f"),
                    "high_price": format(trade_price + step, "f"),
                    "low_price": format(max(Decimal("0"), trade_price - step), "f"),
                    "trade_price": format(trade_price, "f"),
                    "candle_acc_trade_volume": str(10 + offset),
                }
            )
        market_data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            symbol=symbol,
            session_id=SESSION_ID,
        )
        return build_upbit_public_market_data_collection_report(
            collector_id=f"test-continuous-public-rest-mark-{close}",
            session_id=SESSION_ID,
            symbol=symbol,
            market_data=market_data,
        )

    def _stale_krw_ada_ledger_rollup(self, *, average_entry_value: str = "50000") -> dict:
        ledger = deepcopy(load_json(SOURCE_LEDGER_ROLLUP_PATH))
        portfolio = deepcopy(ledger["portfolio_snapshot"])
        quantity = Decimal("0.007")
        average_entry = Decimal(average_entry_value)
        mark = Decimal(average_entry_value)
        fee = Decimal("3")
        cost_basis = quantity * average_entry + fee
        market_value = quantity * mark
        unrealized = market_value - cost_basis
        cash_available = Decimal(portfolio["cash_available"])
        locked_balance = Decimal(portfolio["locked_balance"])
        realized = Decimal(portfolio["realized_pnl"])
        starting = Decimal(portfolio["starting_cash"])
        equity = cash_available + locked_balance + market_value
        total_pnl = realized + unrealized
        return_pct = Decimal("0") if starting <= 0 else ((equity - starting) / starting * Decimal("100"))
        portfolio.update(
            {
                "position_market_value": str(market_value),
                "equity": str(equity),
                "unrealized_pnl": str(unrealized),
                "total_pnl": str(total_pnl),
                "return_pct": str(return_pct),
                "open_position_count": 1,
                "positions": [
                    {
                        "symbol": "KRW-ADA",
                        "side": "LONG",
                        "quantity": str(quantity),
                        "average_entry_price": str(average_entry),
                        "cost_basis": str(cost_basis),
                        "mark_price": str(mark),
                        "market_value": str(market_value),
                        "unrealized_pnl": str(unrealized),
                        "source": "PAPER_LEDGER_ROLLUP",
                        "paper_only": True,
                    }
                ],
            }
        )
        portfolio["snapshot_hash"] = paper_portfolio_hash(portfolio)
        ledger["portfolio_snapshot"] = portfolio
        ledger["rollup_hash"] = paper_ledger_rollup_hash(ledger)
        return ledger

    def _writer_bundle(self, root: Path) -> tuple[dict, dict, dict, dict]:
        writer = build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=load_json(SOURCE_IMPLEMENTATION_PREP_PATH),
            source_ledger_rollup_report=load_json(SOURCE_LEDGER_ROLLUP_PATH),
            audited_writer_id="test-continuous-current-evidence-writer",
        )
        runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
        current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
        portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
        refresh = build_paper_current_truth_refresh_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=SESSION_ID,
            paper_portfolio_snapshot=portfolio,
            heartbeat=None,
            startup_probe=None,
            generated_at_utc=writer["generated_at_utc"],
        )
        return writer, current_evidence, portfolio, refresh

    def _unverified_writer_bundle(self, root: Path) -> tuple[dict, dict, dict, dict]:
        writer = build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=load_json(SOURCE_IMPLEMENTATION_PREP_PATH),
            source_ledger_rollup_report=self._stale_krw_ada_ledger_rollup(),
            public_market_data_collection_report=self._public_collection(close="405", symbol="KRW-ADA"),
            audited_writer_id="test-continuous-current-evidence-writer-unverified",
        )
        runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
        current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
        portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
        refresh = build_paper_current_truth_refresh_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=SESSION_ID,
            paper_portfolio_snapshot=portfolio,
            heartbeat=None,
            startup_probe=None,
            generated_at_utc=writer["generated_at_utc"],
        )
        return writer, current_evidence, portfolio, refresh

    def _repaired_altcoin_writer_bundle(self, root: Path) -> tuple[dict, dict, dict, dict]:
        writer = build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=load_json(SOURCE_IMPLEMENTATION_PREP_PATH),
            source_ledger_rollup_report=self._stale_krw_ada_ledger_rollup(average_entry_value="1000870"),
            public_market_data_collection_report=self._public_collection(close="405", symbol="KRW-ADA"),
            audited_writer_id="test-continuous-current-evidence-writer-repaired-altcoin",
        )
        runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
        current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
        portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
        refresh = build_paper_current_truth_refresh_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=SESSION_ID,
            paper_portfolio_snapshot=portfolio,
            heartbeat=None,
            startup_probe=None,
            generated_at_utc=writer["generated_at_utc"],
        )
        return writer, current_evidence, portfolio, refresh

    def test_continuous_writer_reports_fresh_paper_current_truth(self):
        with TemporaryDirectory() as tmp:
            writer, current_evidence, portfolio, refresh = self._writer_bundle(Path(tmp))
            report = build_paper_continuous_current_evidence_writer_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id=SESSION_ID,
                audited_writer_report=writer,
                audited_current_evidence_snapshot=current_evidence,
                audited_paper_portfolio_snapshot=portfolio,
                paper_current_truth_refresh_report=refresh,
                generated_at_utc=plus_seconds(writer["generated_at_utc"], 1),
            )
            result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["continuous_writer_status"], PAPER_CONTINUOUS_WRITER_WRITING_STATUS)
        self.assertEqual(report["writer_state_model_status"], "IMPLEMENTED_WRITING_PAPER_TRUTH")
        self.assertEqual(report["truth_freshness_status"], "FRESH")
        self.assertTrue(report["writer_implemented"])
        self.assertTrue(report["writer_active_for_paper_current_truth"])
        self.assertTrue(report["source_hash_bound"])
        self.assertEqual(report["configured_capital_krw"], "1000000")
        self.assertEqual(report["current_refreshed_paper_equity_krw"], refresh["verified_equity"])
        self.assertIsNone(report["stale_display_only_equity_krw"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_refreshed_audited_writer_status_counts_as_fresh_paper_truth(self):
        with TemporaryDirectory() as tmp:
            writer, current_evidence, portfolio, refresh = self._writer_bundle(Path(tmp))
            writer["writer_status"] = AUDITED_WRITER_REFRESHED_STATUS
            writer["audited_writer_report_hash"] = upbit_paper_repaired_current_evidence_audited_writer_report_hash(
                writer
            )
            report = build_paper_continuous_current_evidence_writer_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id=SESSION_ID,
                audited_writer_report=writer,
                audited_current_evidence_snapshot=current_evidence,
                audited_paper_portfolio_snapshot=portfolio,
                paper_current_truth_refresh_report=refresh,
                generated_at_utc=plus_seconds(writer["generated_at_utc"], 1),
            )
            result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["continuous_writer_status"], PAPER_CONTINUOUS_WRITER_WRITING_STATUS)
        self.assertTrue(report["writer_source_valid"])
        self.assertTrue(report["writer_active_for_paper_current_truth"])
        self.assertTrue(report["source_hash_bound"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_unverified_audited_writer_artifacts_are_review_only_not_invalid(self):
        with TemporaryDirectory() as tmp:
            writer, current_evidence, portfolio, refresh = self._unverified_writer_bundle(Path(tmp))
            report = build_paper_continuous_current_evidence_writer_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id=SESSION_ID,
                audited_writer_report=writer,
                audited_current_evidence_snapshot=current_evidence,
                audited_paper_portfolio_snapshot=portfolio,
                paper_current_truth_refresh_report=refresh,
                generated_at_utc=plus_seconds(writer["generated_at_utc"], 1),
            )
            result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "PUBLIC_MARK_PRICE_BASIS_MISMATCH")
        self.assertEqual(writer["writer_status"], AUDITED_WRITER_UNVERIFIED_COLLECTION_STATUS)
        self.assertEqual(report["continuous_writer_status"], PAPER_CONTINUOUS_WRITER_REVIEW_ONLY_STATUS)
        self.assertEqual(report["writer_state_model_status"], PAPER_CONTINUOUS_WRITER_REVIEW_ONLY_STATUS)
        self.assertTrue(report["writer_source_valid"])
        self.assertTrue(report["current_snapshot_valid"])
        self.assertTrue(report["portfolio_snapshot_valid"])
        self.assertFalse(report["current_truth_refresh_valid"])
        self.assertTrue(report["source_hash_bound"])
        self.assertFalse(report["writer_active_for_paper_current_truth"])
        self.assertEqual(report["primary_blocker_code"], "PUBLIC_MARK_PRICE_BASIS_MISMATCH")
        self.assertIsNone(report["last_verified_paper_ledger_equity_krw"])
        self.assertIsNone(report["current_refreshed_paper_equity_krw"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_repaired_altcoin_price_basis_restores_fresh_paper_current_truth(self):
        with TemporaryDirectory() as tmp:
            writer, current_evidence, portfolio, refresh = self._repaired_altcoin_writer_bundle(Path(tmp))
            report = build_paper_continuous_current_evidence_writer_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id=SESSION_ID,
                audited_writer_report=writer,
                audited_current_evidence_snapshot=current_evidence,
                audited_paper_portfolio_snapshot=portfolio,
                paper_current_truth_refresh_report=refresh,
                generated_at_utc=plus_seconds(writer["generated_at_utc"], 1),
            )
            result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(report["continuous_writer_status"], PAPER_CONTINUOUS_WRITER_WRITING_STATUS)
        self.assertTrue(report["writer_active_for_paper_current_truth"])
        self.assertTrue(report["current_truth_refresh_valid"])
        self.assertEqual(refresh["refresh_status"], "PASS_PAPER_CURRENT_TRUTH_REFRESHED")
        self.assertEqual(portfolio["positions"][0]["symbol"], "KRW-ADA")
        self.assertEqual(portfolio["positions"][0]["average_entry_price"], "405")
        self.assertEqual(
            portfolio["price_basis_repair_source"],
            "LEGACY_STATIC_FIXTURE_PRICE_BASIS_TO_UPBIT_KRW_SPOT_PUBLIC_MARK",
        )
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["scale_up_allowed"])

    def test_continuous_writer_distinguishes_stale_display_truth(self):
        with TemporaryDirectory() as tmp:
            writer, current_evidence, portfolio, refresh = self._writer_bundle(Path(tmp))
            report = build_paper_continuous_current_evidence_writer_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id=SESSION_ID,
                audited_writer_report=writer,
                audited_current_evidence_snapshot=current_evidence,
                audited_paper_portfolio_snapshot=portfolio,
                paper_current_truth_refresh_report=refresh,
                generated_at_utc=plus_seconds(writer["generated_at_utc"], 301),
            )
            result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "STALE_CURRENT_TRUTH")
        self.assertEqual(report["continuous_writer_status"], PAPER_CONTINUOUS_WRITER_STALE_STATUS)
        self.assertEqual(report["writer_state_model_status"], "IMPLEMENTED_STALE")
        self.assertEqual(report["truth_freshness_status"], "STALE_DISPLAY_ONLY")
        self.assertFalse(report["writer_active_for_paper_current_truth"])
        self.assertIsNone(report["current_refreshed_paper_equity_krw"])
        self.assertEqual(report["stale_display_only_equity_krw"], portfolio["equity"])

    def test_missing_source_report_is_not_implemented_status_without_live_permission(self):
        report = build_paper_continuous_current_evidence_writer_report(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=SESSION_ID,
            audited_writer_report=None,
            audited_current_evidence_snapshot=None,
            audited_paper_portfolio_snapshot=None,
            paper_current_truth_refresh_report=None,
            generated_at_utc="2026-05-06T08:00:00Z",
        )
        result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(report["continuous_writer_status"], PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS)
        self.assertEqual(report["writer_state_model_status"], "NOT_IMPLEMENTED")
        self.assertEqual(report["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertFalse(report["writer_implemented"])
        self.assertFalse(report["live_order_allowed"])

    def test_live_flag_mutation_is_blocked(self):
        with TemporaryDirectory() as tmp:
            writer, current_evidence, portfolio, refresh = self._writer_bundle(Path(tmp))
            report = build_paper_continuous_current_evidence_writer_report(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                mode="PAPER",
                session_id=SESSION_ID,
                audited_writer_report=writer,
                audited_current_evidence_snapshot=current_evidence,
                audited_paper_portfolio_snapshot=portfolio,
                paper_current_truth_refresh_report=refresh,
                generated_at_utc=plus_seconds(writer["generated_at_utc"], 1),
            )
            report["live_order_allowed"] = True
            report["continuous_writer_report_hash"] = paper_continuous_current_evidence_writer_report_hash(report)
            result = validate_paper_continuous_current_evidence_writer_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
