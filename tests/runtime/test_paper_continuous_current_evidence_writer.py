import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.runtime.portfolio.paper_continuous_current_evidence_writer import (
    PAPER_CONTINUOUS_WRITER_NOT_IMPLEMENTED_STATUS,
    PAPER_CONTINUOUS_WRITER_STALE_STATUS,
    PAPER_CONTINUOUS_WRITER_WRITING_STATUS,
    build_paper_continuous_current_evidence_writer_report,
    paper_continuous_current_evidence_writer_report_hash,
    validate_paper_continuous_current_evidence_writer_report,
)
from trader1.runtime.portfolio.paper_current_truth_refresh import build_paper_current_truth_refresh_report


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
        self.assertEqual(report["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
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
