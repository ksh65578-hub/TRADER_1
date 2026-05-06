import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload
from trader1.runtime.ledger.paper_ledger_rollup import paper_ledger_rollup_hash
from trader1.runtime.paper.upbit_public_collector import build_upbit_public_market_data_collection_report
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    AUDITED_WRITER_BLOCKED_LEDGER_STATUS,
    AUDITED_WRITER_BLOCKED_SOURCE_STATUS,
    AUDITED_WRITER_BLOCKED_TARGET_STATUS,
    AUDITED_WRITER_IDEMPOTENT_STATUS,
    AUDITED_WRITER_REFRESHED_STATUS,
    AUDITED_WRITER_WRITTEN_STATUS,
    EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    upbit_paper_repaired_current_evidence_audited_writer_report_hash,
    validate_upbit_paper_audited_current_evidence_idempotency_manifest,
    validate_upbit_paper_audited_current_evidence_snapshot,
    validate_upbit_paper_repaired_current_evidence_audited_writer_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_implementation_prep import (
    upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash,
)
from trader1.runtime.portfolio.paper_portfolio import validate_paper_portfolio_snapshot
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


class UpbitPaperRepairedCurrentEvidenceAuditedWriterTest(unittest.TestCase):
    def source_implementation_prep(self) -> dict:
        return load_json(SOURCE_IMPLEMENTATION_PREP_PATH)

    def source_ledger_rollup(self) -> dict:
        return load_json(SOURCE_LEDGER_ROLLUP_PATH)

    def build_report(
        self,
        root: Path,
        *,
        prep: dict | None = None,
        ledger: dict | None = None,
        public_market_data_collection_report: dict | None = None,
    ) -> dict:
        return build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=prep or self.source_implementation_prep(),
            source_ledger_rollup_report=ledger or self.source_ledger_rollup(),
            public_market_data_collection_report=public_market_data_collection_report,
            audited_writer_id="test-upbit-paper-repaired-current-evidence-audited-writer",
        )

    def public_collection(self, *, close: str, minute_start: int = 30) -> dict:
        payload = []
        close_value = int(Decimal(close))
        for offset in range(6):
            minute = minute_start + 5 - offset
            trade_price = close_value - offset * 1000
            payload.append(
                {
                    "market": "KRW-BTC",
                    "candle_date_time_utc": f"2026-05-06T21:{minute:02d}:00",
                    "opening_price": str(trade_price - 500),
                    "high_price": str(trade_price + 1000),
                    "low_price": str(trade_price - 1000),
                    "trade_price": str(trade_price),
                    "candle_acc_trade_volume": str(10 + offset),
                }
            )
        market_data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            symbol="KRW-BTC",
            session_id=SESSION_ID,
        )
        return build_upbit_public_market_data_collection_report(
            collector_id=f"test-public-rest-mark-{close}",
            session_id=SESSION_ID,
            symbol="KRW-BTC",
            market_data=market_data,
        )

    def test_writer_publishes_verified_paper_current_evidence(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_portfolio = self.source_ledger_rollup()["portfolio_snapshot"]
            report = self.build_report(root)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertTrue(report["writer_passed"])
            self.assertEqual(report["writer_control_pass_count"], 11)
            self.assertEqual(report["writer_control_blocked_count"], 0)
            self.assertEqual(report["artifact_written_count"], 3)
            self.assertFalse(report["lock_present_after_run"])
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertFalse(report["scale_up_allowed"])

            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            manifest = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[1])
            portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])

            self.assertEqual(validate_upbit_paper_audited_current_evidence_snapshot(current_evidence).status, "PASS")
            self.assertEqual(
                validate_upbit_paper_audited_current_evidence_idempotency_manifest(manifest).status,
                "PASS",
            )
            self.assertEqual(validate_paper_portfolio_snapshot(portfolio).status, "PASS")
            self.assertEqual(current_evidence["portfolio_truth_status"], "VERIFIED_PAPER_LEDGER_ROLLUP")
            self.assertEqual(current_evidence["cash_status"], "VERIFIED")
            self.assertEqual(current_evidence["configured_initial_cash_krw"], "1000000")
            self.assertEqual(portfolio["source"], "PAPER_LEDGER_ROLLUP")
            self.assertEqual(portfolio["starting_cash"], "1000000")
            self.assertEqual(portfolio["cash_available"], source_portfolio["cash_available"])
            self.assertEqual(current_evidence["verified_cash_krw"], source_portfolio["cash_available"])
            self.assertEqual(current_evidence["verified_equity_krw"], source_portfolio["equity"])
            self.assertEqual(portfolio["open_position_count"], source_portfolio["open_position_count"])

            written_path = write_upbit_paper_repaired_current_evidence_audited_writer_report(
                root=root,
                report=report,
            )
            self.assertTrue(written_path.exists())
            loaded = load_json(written_path)
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_report(loaded).status,
                "PASS",
            )

    def test_writer_is_idempotent_when_outputs_match_sources(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.build_report(root)
            second = self.build_report(root)

            self.assertEqual(first["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertEqual(second["writer_status"], AUDITED_WRITER_IDEMPOTENT_STATUS)
            self.assertEqual(second["artifact_written_count"], 0)
            self.assertEqual(second["artifact_reused_count"], 3)
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(validate_upbit_paper_repaired_current_evidence_audited_writer_report(second).status, "PASS")

    def test_writer_marks_open_positions_to_public_market_current_truth(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            public_report = self.public_collection(close="1100000")
            source_portfolio = self.source_ledger_rollup()["portfolio_snapshot"]
            source_position = source_portfolio["positions"][0]

            report = self.build_report(root, public_market_data_collection_report=public_report)

            self.assertEqual(report["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertTrue(report["writer_passed"])
            self.assertEqual(report["source_public_market_data_hash"], public_report["collection_hash"])
            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            manifest = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[1])
            portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
            position = portfolio["positions"][0]
            expected_market_value = Decimal(source_position["quantity"]) * Decimal("1100000")
            expected_unrealized = expected_market_value - Decimal(source_position["cost_basis"])
            expected_equity = Decimal(source_portfolio["cash_available"]) + expected_market_value

            self.assertEqual(validate_upbit_paper_audited_current_evidence_snapshot(current_evidence).status, "PASS")
            self.assertEqual(
                validate_upbit_paper_audited_current_evidence_idempotency_manifest(manifest).status,
                "PASS",
            )
            self.assertEqual(validate_paper_portfolio_snapshot(portfolio).status, "PASS")
            self.assertEqual(portfolio["source"], "PAPER_LEDGER_ROLLUP_PUBLIC_MARK")
            self.assertEqual(portfolio["mark_to_market_status"], "PASS_PUBLIC_MARK_TO_MARKET")
            self.assertEqual(portfolio["mark_price_source"], "PUBLIC_REST_READ_ONLY_1M_CLOSE")
            self.assertEqual(portfolio["source_public_market_data_hash"], public_report["collection_hash"])
            self.assertEqual(portfolio["marked_to_market_position_count"], portfolio["open_position_count"])
            self.assertEqual(position["mark_price"], "1100000")
            self.assertEqual(Decimal(position["market_value"]), expected_market_value)
            self.assertEqual(Decimal(position["unrealized_pnl"]), expected_unrealized)
            self.assertEqual(Decimal(portfolio["equity"]), expected_equity)
            self.assertEqual(current_evidence["source_public_market_data_hash"], public_report["collection_hash"])
            self.assertEqual(current_evidence["verified_equity_krw"], portfolio["equity"])
            self.assertEqual(manifest["source_public_market_data_hash"], public_report["collection_hash"])
            self.assertFalse(portfolio["live_order_ready"])
            self.assertFalse(portfolio["live_order_allowed"])
            self.assertFalse(portfolio["can_live_trade"])
            self.assertFalse(portfolio["scale_up_allowed"])

    def test_writer_refreshes_same_ledger_when_public_mark_changes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_public = self.public_collection(close="1100000", minute_start=30)
            second_public = self.public_collection(close="1110000", minute_start=40)
            first = self.build_report(root, public_market_data_collection_report=first_public)
            refreshed = self.build_report(root, public_market_data_collection_report=second_public)

            self.assertEqual(first["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertEqual(refreshed["writer_status"], AUDITED_WRITER_REFRESHED_STATUS)
            self.assertTrue(refreshed["writer_passed"])
            self.assertEqual(refreshed["target_dirty_cause"], "STALE_CURRENT_TRUTH_REFRESHED")
            self.assertTrue(refreshed["stale_output_superseded"])
            self.assertEqual(refreshed["archived_artifact_count"], 3)
            self.assertEqual(
                refreshed["post_rerun_reconciliation_closure_status"],
                "PASS_STALE_CURRENT_TRUTH_REFRESHED",
            )
            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            manifest = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[1])
            portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])

            self.assertEqual(current_evidence["source_public_market_data_hash"], second_public["collection_hash"])
            self.assertEqual(manifest["source_public_market_data_hash"], second_public["collection_hash"])
            self.assertEqual(portfolio["source_public_market_data_hash"], second_public["collection_hash"])
            self.assertEqual(portfolio["positions"][0]["mark_price"], "1110000")
            self.assertFalse(refreshed["live_order_ready"])
            self.assertFalse(refreshed["live_order_allowed"])
            self.assertFalse(refreshed["can_live_trade"])
            self.assertFalse(refreshed["scale_up_allowed"])

    def test_writer_normalizes_legacy_static_price_basis_to_public_mark(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatched_public = self.public_collection(close="119000000", minute_start=30)
            source_position = self.source_ledger_rollup()["portfolio_snapshot"]["positions"][0]

            report = self.build_report(root, public_market_data_collection_report=mismatched_public)

            self.assertEqual(report["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertTrue(report["writer_passed"])
            self.assertEqual(validate_upbit_paper_repaired_current_evidence_audited_writer_report(report).status, "PASS")
            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
            position = portfolio["positions"][0]
            original_gross = Decimal(source_position["quantity"]) * Decimal(source_position["average_entry_price"])
            expected_quantity = original_gross / Decimal("119000000")

            self.assertEqual(portfolio["mark_to_market_status"], "PASS_PUBLIC_MARK_TO_MARKET")
            self.assertEqual(portfolio["price_basis_repair_status"], "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION")
            self.assertEqual(portfolio["price_basis_repair_count"], 1)
            self.assertEqual(position["price_basis_repair_status"], "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION")
            self.assertEqual(position["price_basis_original_average_entry_price"], source_position["average_entry_price"])
            self.assertEqual(Decimal(position["quantity"]), expected_quantity)
            self.assertEqual(position["average_entry_price"], "119000000")
            self.assertEqual(position["mark_price"], "119000000")
            self.assertEqual(Decimal(position["market_value"]), original_gross)
            self.assertEqual(current_evidence["verified_equity_krw"], portfolio["equity"])
            self.assertEqual(current_evidence["source_public_market_data_hash"], mismatched_public["collection_hash"])
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertFalse(report["scale_up_allowed"])

    def test_writer_blocks_non_repairable_public_mark_price_basis_mismatch(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatched_public = self.public_collection(close="7000000", minute_start=30)

            report = self.build_report(root, public_market_data_collection_report=mismatched_public)

            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_LEDGER_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "PUBLIC_MARK_PRICE_BASIS_MISMATCH")
            self.assertIn("PUBLIC_MARK_PRICE_BASIS_MISMATCH", report["blocker_codes"])
            self.assertEqual(validate_upbit_paper_repaired_current_evidence_audited_writer_report(report).status, "PASS")
            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            for relative_path in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS:
                self.assertFalse((runtime_base / relative_path).exists())
            self.assertFalse(report["live_order_ready"])
            self.assertFalse(report["live_order_allowed"])
            self.assertFalse(report["can_live_trade"])
            self.assertFalse(report["scale_up_allowed"])

    def test_writer_refreshes_repaired_price_basis_without_resizing_position(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_public = self.public_collection(close="119000000", minute_start=30)
            second_public = self.public_collection(close="119500000", minute_start=40)
            first = self.build_report(root, public_market_data_collection_report=first_public)
            first_runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            first_portfolio = load_json(first_runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
            first_position = first_portfolio["positions"][0]

            refreshed = self.build_report(root, public_market_data_collection_report=second_public)
            refreshed_portfolio = load_json(first_runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
            refreshed_position = refreshed_portfolio["positions"][0]

            self.assertEqual(first["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertEqual(refreshed["writer_status"], AUDITED_WRITER_REFRESHED_STATUS)
            self.assertEqual(first_position["quantity"], refreshed_position["quantity"])
            self.assertEqual(first_position["average_entry_price"], "119000000")
            self.assertEqual(refreshed_position["average_entry_price"], "119000000")
            self.assertEqual(refreshed_position["mark_price"], "119500000")
            self.assertEqual(
                refreshed_position["price_basis_repair_status"],
                "APPLIED_PUBLIC_MARK_PRICE_BASIS_NORMALIZATION",
            )
            self.assertEqual(refreshed_portfolio["price_basis_repair_count"], 1)
            self.assertFalse(refreshed["live_order_ready"])
            self.assertFalse(refreshed["live_order_allowed"])
            self.assertFalse(refreshed["can_live_trade"])
            self.assertFalse(refreshed["scale_up_allowed"])

    def test_writer_refreshes_stale_same_ledger_current_truth_without_live_permission(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer.utc_now",
                return_value="2026-05-06T00:00:00Z",
            ):
                first = self.build_report(root)
            with patch(
                "trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer.utc_now",
                return_value="2026-05-06T00:06:01Z",
            ):
                refreshed = self.build_report(root)

            self.assertEqual(first["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertEqual(refreshed["writer_status"], AUDITED_WRITER_REFRESHED_STATUS)
            self.assertEqual(refreshed["target_dirty_cause"], "STALE_CURRENT_TRUTH_REFRESHED")
            self.assertTrue(refreshed["stale_output_superseded"])
            self.assertEqual(refreshed["artifact_written_count"], 3)
            self.assertEqual(refreshed["archived_artifact_count"], 3)
            self.assertEqual(
                refreshed["post_rerun_reconciliation_closure_status"],
                "PASS_STALE_CURRENT_TRUTH_REFRESHED",
            )
            self.assertIsNone(refreshed["post_rerun_reconciliation_unresolved_cause"])
            self.assertFalse(refreshed["live_order_allowed"])
            self.assertFalse(refreshed["can_live_trade"])
            self.assertFalse(refreshed["scale_up_allowed"])
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_report(refreshed).status,
                "PASS",
            )

            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            self.assertEqual(current_evidence["generated_at_utc"], "2026-05-06T00:06:01Z")
            self.assertEqual(
                current_evidence["source_paper_ledger_head_hash"],
                self.source_ledger_rollup()["latest_ledger_head_hash"],
            )

            with patch(
                "trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer.utc_now",
                return_value="2026-05-06T00:06:02Z",
            ):
                replay = self.build_report(root)
            self.assertEqual(replay["writer_status"], AUDITED_WRITER_IDEMPOTENT_STATUS)
            self.assertEqual(replay["artifact_reused_count"], 3)

    def test_writer_archives_stale_current_truth_and_writes_current_ledger_truth(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale_ledger = json.loads(json.dumps(self.source_ledger_rollup()))
            stale_head_hash = "A" * 64
            stale_ledger["latest_ledger_head_hash"] = stale_head_hash
            stale_ledger["portfolio_snapshot"]["source_paper_ledger_head_hash"] = stale_head_hash
            stale_ledger["portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(
                stale_ledger["portfolio_snapshot"]
            )
            stale_ledger["rollup_hash"] = paper_ledger_rollup_hash(stale_ledger)

            stale_report = self.build_report(root, ledger=stale_ledger)
            current_report = self.build_report(root)

            self.assertEqual(stale_report["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertEqual(current_report["writer_status"], AUDITED_WRITER_WRITTEN_STATUS)
            self.assertTrue(current_report["writer_passed"])
            self.assertEqual(current_report["artifact_written_count"], 3)
            self.assertEqual(current_report["target_dirty_cause"], "STALE_LEDGER_SUPERSEDED")
            self.assertTrue(current_report["stale_output_superseded"])
            self.assertEqual(current_report["archived_artifact_count"], 3)
            self.assertEqual(
                current_report["post_rerun_reconciliation_closure_status"],
                "PASS_STALE_CURRENT_TRUTH_SUPERSEDED",
            )
            self.assertIsNone(current_report["post_rerun_reconciliation_unresolved_cause"])
            self.assertTrue(current_report["lock_acquired"])
            self.assertTrue(current_report["lock_released"])
            self.assertFalse(current_report["lock_present_after_run"])
            self.assertEqual(
                validate_upbit_paper_repaired_current_evidence_audited_writer_report(current_report).status,
                "PASS",
            )

            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            current_evidence = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
            portfolio = load_json(runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
            self.assertEqual(
                current_evidence["source_paper_ledger_head_hash"],
                self.source_ledger_rollup()["latest_ledger_head_hash"],
            )
            self.assertEqual(
                portfolio["source_paper_ledger_head_hash"],
                self.source_ledger_rollup()["latest_ledger_head_hash"],
            )
            for archived in current_report["archived_artifacts"]:
                self.assertTrue((runtime_base / archived["relative_archive_path"]).exists())
                self.assertFalse(archived["live_order_allowed"])
                self.assertFalse(archived["scale_up_allowed"])

            replay = self.build_report(root)
            self.assertEqual(replay["writer_status"], AUDITED_WRITER_IDEMPOTENT_STATUS)
            self.assertEqual(replay["artifact_written_count"], 0)
            self.assertEqual(replay["artifact_reused_count"], 3)

    def test_invalid_source_implementation_prep_blocks_writer(self):
        with TemporaryDirectory() as tmp:
            prep = self.source_implementation_prep()
            prep["live_order_allowed"] = True
            prep["audited_writer_implementation_prep_hash"] = (
                upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(prep)
            )

            report = self.build_report(Path(tmp), prep=prep)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_SOURCE_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
            self.assertEqual(report["artifact_written_count"], 0)
            self.assertFalse(report["live_order_allowed"])

    def test_invalid_ledger_rollup_blocks_writer(self):
        with TemporaryDirectory() as tmp:
            ledger = self.source_ledger_rollup()
            ledger["ledger_head_match_status"] = "MISMATCH"
            ledger["primary_blocker_code"] = "LEDGER_INTEGRITY_FAIL"
            ledger["blockers"] = [
                {
                    "code": "LEDGER_INTEGRITY_FAIL",
                    "severity": "HIGH",
                    "message": "test ledger head mismatch",
                }
            ]
            ledger["rollup_status"] = "BLOCKED"
            ledger["rollup_hash"] = paper_ledger_rollup_hash(ledger)

            report = self.build_report(Path(tmp), ledger=ledger)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_LEDGER_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "LEDGER_INTEGRITY_FAIL")
            self.assertEqual(report["artifact_written_count"], 0)

    def test_partial_existing_target_blocks_writer(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_base = root / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
            partial_path = runtime_base / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0]
            partial_path.parent.mkdir(parents=True, exist_ok=True)
            partial_path.write_text("{}\n", encoding="utf-8")

            report = self.build_report(root)
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "PASS", result.message)
            self.assertEqual(report["writer_status"], AUDITED_WRITER_BLOCKED_TARGET_STATUS)
            self.assertFalse(report["writer_passed"])
            self.assertEqual(report["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
            self.assertEqual(report["target_dirty_cause"], "PARTIAL_TARGET_SET")
            self.assertEqual(
                report["post_rerun_reconciliation_closure_status"],
                "BLOCKED_PRECISE_UNRESOLVED_CAUSE",
            )
            self.assertEqual(report["post_rerun_reconciliation_unresolved_cause"], "PARTIAL_TARGET_SET")
            self.assertEqual(report["artifact_written_count"], 0)

    def test_report_validation_blocks_live_mutation(self):
        with TemporaryDirectory() as tmp:
            report = self.build_report(Path(tmp))
            report["live_order_allowed"] = True
            report["audited_writer_report_hash"] = upbit_paper_repaired_current_evidence_audited_writer_report_hash(
                report
            )
            result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
