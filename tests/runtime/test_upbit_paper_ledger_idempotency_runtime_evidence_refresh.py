import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.ledger.paper_ledger_rollup import (
    build_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop
from tools.run_upbit_paper_ledger_idempotency_runtime_evidence_refresh import (
    refresh_upbit_paper_ledger_idempotency_runtime_evidence,
)


class UpbitPaperLedgerIdempotencyRuntimeEvidenceRefreshTest(unittest.TestCase):
    def test_refresh_writes_current_paper_evidence_and_stays_live_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-refresh-pass",
                requested_cycle_count=2,
            )

            result = refresh_upbit_paper_ledger_idempotency_runtime_evidence(root=root)

            self.assertEqual(result.validation.status, "PASS")
            self.assertTrue(result.output_path.exists())
            loaded = json.loads(result.output_path.read_text(encoding="utf-8"))
            loaded_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(loaded)
            self.assertEqual(loaded_result.status, "PASS")
            self.assertEqual(loaded["runtime_evidence_status"], "PASS")
            self.assertEqual(loaded["idempotency_status"], "PASS")
            self.assertEqual(loaded["reconciliation_status"], "PASS")
            self.assertEqual(loaded["source_runtime_depth_status"], "PASS")
            self.assertTrue(loaded["ledger_head_cycle_in_persistent_loop"])
            self.assertEqual(loaded["source_runtime_input_role"], "MULTI_SYMBOL_PUBLIC_MARKET_DATA_COLLECTION")
            self.assertEqual(loaded["source_public_market_data_hash"], loaded["source_runtime_public_market_data_hash"])
            self.assertGreaterEqual(loaded["source_ledger_jsonl_count"], 1)
            self.assertFalse(loaded["current_evidence_write_allowed"])
            self.assertFalse(loaded["live_order_ready"])
            self.assertFalse(loaded["live_order_allowed"])
            self.assertFalse(loaded["can_live_trade"])
            self.assertFalse(loaded["scale_up_allowed"])

    def test_refresh_writes_blocked_duplicate_evidence_without_live_permission(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-refresh-duplicate",
                requested_cycle_count=1,
            )
            ledger_path = next(
                root / artifact
                for artifact in loop["cycle_results"][0]["artifact_paths"]
                if artifact.endswith(".paper_ledger_events.jsonl")
            )
            ledger_path.with_name("duplicate-refresh.paper_ledger_events.jsonl").write_text(
                ledger_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            rollup = build_paper_ledger_rollup_report(
                root=root,
                session_id="mvp1_upbit_paper_launcher",
                rollup_id="test-upbit-paper-idempotency-refresh-duplicate",
            )
            write_paper_ledger_rollup_report(root=root, report=rollup)

            result = refresh_upbit_paper_ledger_idempotency_runtime_evidence(root=root)

            self.assertEqual(result.validation.status, "BLOCKED")
            self.assertEqual(result.validation.blocker_code, "RECONCILIATION_REQUIRED")
            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.report["runtime_evidence_status"], "BLOCKED")
            self.assertEqual(result.report["source_runtime_depth_status"], "PASS")
            self.assertGreater(result.report["duplicate_event_id_count"], 0)
            self.assertFalse(result.report["live_order_allowed"])
            self.assertFalse(result.report["can_live_trade"])
            self.assertFalse(result.report["scale_up_allowed"])

    def test_cli_refresh_blocks_output_path_escape(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="test-upbit-paper-idempotency-refresh-cli",
                requested_cycle_count=1,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "tools/run_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                    "--root",
                    str(root),
                    "--output",
                    "../escaped.json",
                ],
                cwd=Path(__file__).resolve().parents[2],
                text=True,
                capture_output=True,
                timeout=60,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("escapes root", completed.stderr)


if __name__ == "__main__":
    unittest.main()
