import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.adapters.upbit.market_data import (
    build_upbit_public_candle_data_from_rest_payload,
    build_upbit_public_candle_fixture,
    validate_upbit_public_candle_data,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    build_upbit_paper_runtime_recovery_guard_report,
    run_upbit_paper_persistent_loop,
    upbit_paper_persistent_loop_hash,
    upbit_paper_runtime_recovery_guard_hash,
    validate_upbit_paper_persistent_loop_report,
    validate_upbit_paper_runtime_recovery_guard_report,
)
from trader1.runtime.paper.upbit_public_collector import (
    build_upbit_public_market_data_collection_report,
    recover_jsonl_records,
    upbit_public_market_data_collection_hash,
    validate_upbit_public_market_data_collection_report,
    write_upbit_public_market_data_collection_artifacts,
)
from trader1.validation.mvp0_validators import run_validators


class UpbitPublicCollectionPersistentLoopTest(unittest.TestCase):
    def _upbit_rest_payload(self) -> list[dict[str, object]]:
        return [
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": f"2026-04-30T09:{index:02d}:00",
                "opening_price": 1000000 + index * 1000,
                "high_price": 1002500 + index * 1000,
                "low_price": 998000 + index * 1000,
                "trade_price": 1000500 + index * 1000,
                "candle_acc_trade_volume": 2 + index,
            }
            for index in range(5, -1, -1)
        ]

    def test_public_collection_canonicalizes_fixture_without_private_or_live_behavior(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-positive",
            session_id="mvp1_upbit_paper_launcher",
        )
        result = validate_upbit_public_market_data_collection_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["canonical_event_count"], report["raw_sample_count"])
        self.assertGreaterEqual(report["canonical_event_count"], 5)
        self.assertEqual(len(report["public_market_data_hash"]), 64)
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_public_collection_blocks_payload_mutation_after_data_hash_binding(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-payload-mismatch",
            session_id="mvp1_upbit_paper_launcher",
        )
        report["public_market_data"]["candles"][0]["close"] = "1234567"
        report["collection_hash"] = upbit_public_market_data_collection_hash(report)

        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_public_rest_payload_canonicalizes_without_credentials_or_private_endpoint(self):
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=self._upbit_rest_payload(),
            session_id="mvp1_upbit_paper_launcher",
        )
        data_status, data_blocker, _ = validate_upbit_public_candle_data(
            data,
            symbol="KRW-BTC",
            session_id="mvp1_upbit_paper_launcher",
        )
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-read-only",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(data_status, "PASS")
        self.assertIsNone(data_blocker)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["data_source"], "PUBLIC_REST_READ_ONLY")
        self.assertEqual(report["canonical_event_count"], 6)
        self.assertFalse(report["credential_load_attempted"])
        self.assertFalse(report["private_endpoint_called"])
        self.assertFalse(report["order_endpoint_called"])
        self.assertFalse(report["live_order_allowed"])

    def test_public_rest_payload_blocks_authorization_header_or_private_endpoint(self):
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=self._upbit_rest_payload(),
            session_id="mvp1_upbit_paper_launcher",
        )
        data["authorization_header_present"] = True
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-auth-header",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_public_rest_payload_duplicate_timestamp_requires_reconcile(self):
        payload = self._upbit_rest_payload()
        payload[1]["candle_date_time_utc"] = payload[0]["candle_date_time_utc"]
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            session_id="mvp1_upbit_paper_launcher",
        )
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-duplicate-timestamp",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_public_rest_payload_out_of_order_timestamp_requires_reconcile(self):
        payload = self._upbit_rest_payload()
        data = build_upbit_public_candle_data_from_rest_payload(
            payload=payload,
            session_id="mvp1_upbit_paper_launcher",
        )
        data["candles"][3]["timestamp"] = "2026-04-30T08:59:00Z"
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-public-rest-out-of-order-timestamp",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_public_collection_blocks_private_field_mixing(self):
        data = build_upbit_public_candle_fixture(session_id="mvp1_upbit_paper_launcher")
        data["private_account_fields_present"] = True
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-private-mix",
            session_id="mvp1_upbit_paper_launcher",
            market_data=data,
        )
        result = validate_upbit_public_market_data_collection_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_public_collection_writer_recovers_partial_jsonl_without_live_permission(self):
        report = build_upbit_public_market_data_collection_report(
            collector_id="collection-writer",
            session_id="mvp1_upbit_paper_launcher",
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = write_upbit_public_market_data_collection_artifacts(root=root, report=report)
            self.assertEqual(writer["writer_status"], "PASS")
            self.assertEqual(writer["public_market_data_hash"], report["public_market_data_hash"])
            latest_pointer = json.loads((root / writer["artifact_paths"][3]).read_text(encoding="utf-8"))
            self.assertEqual(latest_pointer["public_market_data_hash"], report["public_market_data_hash"])
            canonical_path = root / writer["artifact_paths"][1]
            with canonical_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')
            records, quarantine_path = recover_jsonl_records(canonical_path)
            self.assertEqual(len(records), report["canonical_event_count"])
            self.assertIsNotNone(quarantine_path)
            self.assertFalse(writer["live_order_allowed"])

    def test_bounded_paper_loop_writes_latest_cycle_and_remains_live_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop",
                requested_cycle_count=2,
            )
            result = validate_upbit_paper_persistent_loop_report(loop)
            self.assertEqual(result.status, "PASS")
            self.assertEqual(loop["completed_cycle_count"], 2)
            self.assertTrue(loop["actual_paper_runtime_executed"])
            self.assertEqual(loop["recovery_guard_status"], "PASS")
            self.assertTrue(loop["paper_runtime_resume_allowed"])
            self.assertFalse(loop["partial_write_recovery_required"])
            self.assertEqual(loop["paper_ledger_rollup_status"], "PASS")
            self.assertIsNone(loop["paper_ledger_rollup_primary_blocker_code"])
            self.assertTrue((root / loop["paper_ledger_rollup_path"]).exists())
            self.assertFalse(loop["long_run_evidence_eligible"])
            self.assertFalse(loop["live_order_allowed"])
            guard_path = root / loop["runtime_recovery_guard_path"]
            guard = json.loads(guard_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_upbit_paper_runtime_recovery_guard_report(guard).status, "PASS")
            latest_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            self.assertEqual(latest["runtime_input_role"], "PUBLIC_MARKET_DATA_COLLECTION")
            self.assertFalse(latest["live_order_allowed"])
            ledger_artifacts = [
                artifact_path
                for cycle_result in loop["cycle_results"]
                for artifact_path in cycle_result["artifact_paths"]
                if artifact_path.endswith(".paper_ledger_events.jsonl")
            ]
            self.assertEqual(len(ledger_artifacts), 2)
            ledger_head_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/latest_paper_ledger_head.json"
            ledger_head = json.loads(ledger_head_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger_head["schema_id"], "trader1.paper_ledger_head.v1")
            self.assertEqual(ledger_head["ledger_head_hash"], latest["paper_ledger_head_hash"])
            self.assertFalse(ledger_head["live_order_allowed"])
            self.assertEqual(guard["ledger_jsonl_checked_count"], 2)
            self.assertEqual(guard["corrupted_ledger_jsonl_quarantined_count"], 0)
            self.assertEqual(guard["ledger_jsonl_invalid_count"], 0)
            rollup = json.loads((root / loop["paper_ledger_rollup_path"]).read_text(encoding="utf-8"))
            self.assertEqual(rollup["ledger_jsonl_count"], 2)
            self.assertEqual(rollup["filled_order_count"], 2)
            self.assertEqual(rollup["portfolio_snapshot"]["source"], "PAPER_LEDGER_ROLLUP")
            self.assertFalse(rollup["live_order_allowed"])

    def test_recovery_guard_blocks_orphan_tmp_file_before_resume(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-orphan-tmp",
                requested_cycle_count=1,
            )
            tmp_path = root / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/.orphan.tmp"
            tmp_path.write_text("partial", encoding="utf-8")

            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-orphan-tmp",
            )
            result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertFalse(guard["paper_runtime_resume_allowed"])

    def test_recovery_guard_quarantines_partial_canonical_jsonl(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-corrupt-jsonl",
                requested_cycle_count=1,
            )
            canonical_path = None
            for artifact_path in loop["cycle_results"][0]["artifact_paths"]:
                if artifact_path.endswith(".canonical_events.jsonl"):
                    canonical_path = root / artifact_path
                    break
            self.assertIsNotNone(canonical_path)
            with canonical_path.open("a", encoding="utf-8", newline="") as handle:
                handle.write('{"partial":')

            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-corrupt-jsonl",
            )
            result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertEqual(guard["corrupted_jsonl_quarantined_count"], 1)
            self.assertFalse(guard["paper_runtime_resume_allowed"])

    def test_recovery_guard_quarantines_partial_paper_ledger_jsonl(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            loop = run_upbit_paper_persistent_loop(
                root=root,
                loop_id="bounded-paper-loop-corrupt-ledger-jsonl",
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

            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=root,
                loop_id="bounded-paper-loop-corrupt-ledger-jsonl",
            )
            result = validate_upbit_paper_runtime_recovery_guard_report(guard)

            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "PARTIAL_WRITE_RECOVERY_REQUIRED")
            self.assertEqual(guard["corrupted_ledger_jsonl_quarantined_count"], 1)
            self.assertFalse(guard["paper_runtime_resume_allowed"])

    def test_recovery_guard_blocks_live_permission_mutation(self):
        with TemporaryDirectory() as tmp:
            guard = build_upbit_paper_runtime_recovery_guard_report(
                root=Path(tmp),
                loop_id="bounded-paper-loop-missing-latest",
            )
        guard["live_order_allowed"] = True
        guard["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(guard)

        result = validate_upbit_paper_runtime_recovery_guard_report(guard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_persistent_loop_hash_tamper_fails(self):
        with TemporaryDirectory() as tmp:
            loop = run_upbit_paper_persistent_loop(
                root=Path(tmp),
                loop_id="bounded-paper-loop-tamper",
                requested_cycle_count=1,
            )
            loop["completed_cycle_count"] = 0
            loop["loop_hash"] = upbit_paper_persistent_loop_hash(loop)
            result = validate_upbit_paper_persistent_loop_report(loop)
            self.assertEqual(result.status, "FAIL")
            self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_new_validators_pass_current_contract(self):
        results = run_validators(
            [
                "upbit_public_market_data_collection_validator",
                "upbit_paper_persistent_loop_validator",
            ]
        )
        self.assertEqual([result["status"] for result in results], ["PASS", "PASS"])


if __name__ == "__main__":
    unittest.main()
