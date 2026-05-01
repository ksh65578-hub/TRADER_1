import unittest

from trader1.core.events.intent_wal import intent_wal_event_hash, validate_intent_wal_chain
from trader1.core.ledger.restart_recovery import (
    build_restart_recovery_report,
    restart_recovery_hash,
    validate_restart_recovery_report,
)
from trader1.validation.mvp0_validators import run_validators


class RestartRecoveryTest(unittest.TestCase):
    def test_restart_recovery_resumes_paper_only_without_live_permission(self):
        report = build_restart_recovery_report(restart_id="restart-pass")
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(report["recovery_action"], "RESUME_PAPER_ONLY")
        self.assertTrue(report["ledger_recovered"])
        self.assertTrue(report["intent_wal_recovered"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])
        self.assertTrue(report["windows_path_recovery_checked"])
        self.assertTrue(report["atomic_write_recovery_checked"])
        self.assertTrue(report["partial_write_recovery_checked"])
        self.assertTrue(report["stale_lock_recovery_checked"])
        self.assertTrue(report["recovery_artifact_paths"])
        self.assertTrue(all("\\" not in path and not path.startswith("/") for path in report["recovery_artifact_paths"]))

    def test_intent_wal_chain_is_hash_linked(self):
        report = build_restart_recovery_report(restart_id="restart-wal")
        result = validate_intent_wal_chain(report["intent_wal_events"])
        self.assertEqual(result.status, "PASS")
        self.assertIsNone(report["intent_wal_events"][0]["previous_wal_hash"])
        self.assertEqual(report["intent_wal_events"][1]["previous_wal_hash"], report["intent_wal_events"][0]["wal_event_hash"])

    def test_missing_intent_wal_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-no-wal", intent_wal_events=[])
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LEDGER_UNAVAILABLE")

    def test_missing_ledger_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-no-ledger", ledger_events=[], intent_wal_events=[])
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LEDGER_UNAVAILABLE")

    def test_crafted_pass_without_single_writer_recovery_is_blocked(self):
        report = build_restart_recovery_report(restart_id="restart-no-single-writer")
        report["single_writer_recovered"] = False
        report["restart_recovery_status"] = "PASS"
        report["recovery_action"] = "RESUME_PAPER_ONLY"
        report["primary_blocker_code"] = None
        report["blockers"] = []
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_recovered_flag_mismatch_fails_closed(self):
        report = build_restart_recovery_report(restart_id="restart-flag-mismatch")
        report["ledger_recovered"] = False
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")

    def test_cross_scope_wal_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-cross")
        report["intent_wal_events"][1]["exchange"] = "BINANCE"
        report["intent_wal_events"][1]["wal_event_hash"] = intent_wal_event_hash(report["intent_wal_events"][1])
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_duplicate_source_ledger_event_in_wal_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-duplicate-source")
        duplicate = dict(report["intent_wal_events"][0])
        duplicate["wal_event_id"] = "restart-duplicate-source-wal-duplicate"
        duplicate["previous_wal_hash"] = report["intent_wal_events"][-1]["wal_event_hash"]
        duplicate["wal_event_hash"] = intent_wal_event_hash(duplicate)
        report["intent_wal_events"].append(duplicate)
        report["intent_wal_head_hash"] = duplicate["wal_event_hash"]
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_wal_source_outside_recovered_ledger_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-wal-source-outside-ledger")
        report["intent_wal_events"][0]["source_ledger_event_hash"] = "A" * 64
        report["intent_wal_events"][0]["wal_event_hash"] = intent_wal_event_hash(report["intent_wal_events"][0])
        report["intent_wal_events"][1]["previous_wal_hash"] = report["intent_wal_events"][0]["wal_event_hash"]
        report["intent_wal_events"][1]["wal_event_hash"] = intent_wal_event_hash(report["intent_wal_events"][1])
        report["intent_wal_head_hash"] = report["intent_wal_events"][1]["wal_event_hash"]
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_missing_wal_for_intent_ledger_event_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-missing-wal-source")
        report["intent_wal_events"] = report["intent_wal_events"][:1]
        report["intent_wal_head_hash"] = report["intent_wal_events"][0]["wal_event_hash"]
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_non_hex_wal_source_hash_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-non-hex-wal-source")
        report["intent_wal_events"][0]["source_ledger_event_hash"] = "Z" * 64
        report["intent_wal_events"][0]["wal_event_hash"] = intent_wal_event_hash(report["intent_wal_events"][0])
        report["intent_wal_events"][1]["previous_wal_hash"] = report["intent_wal_events"][0]["wal_event_hash"]
        report["intent_wal_events"][1]["wal_event_hash"] = intent_wal_event_hash(report["intent_wal_events"][1])
        report["intent_wal_head_hash"] = report["intent_wal_events"][1]["wal_event_hash"]
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LEDGER_INTEGRITY_FAIL")

    def test_live_permission_mutation_is_blocked(self):
        report = build_restart_recovery_report(restart_id="restart-live")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["can_submit_order"] = True
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_order_adapter_call_mutation_is_blocked(self):
        report = build_restart_recovery_report(restart_id="restart-adapter")
        report["order_adapter_called"] = True
        report["restart_recovery_hash"] = restart_recovery_hash(report)
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_hash_tamper_fails(self):
        report = build_restart_recovery_report(restart_id="restart-tamper")
        report["session_id"] = "tampered-session"
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_windows_drive_artifact_path_blocks_recovery(self):
        report = build_restart_recovery_report(
            restart_id="restart-drive-path",
            recovery_artifact_paths=["C:/TRADER_1/system/runtime/restart_recovery_report.json"],
        )
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_backslash_artifact_path_blocks_recovery(self):
        report = build_restart_recovery_report(
            restart_id="restart-backslash-path",
            recovery_artifact_paths=["system\\runtime\\restart_recovery_report.json"],
        )
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_parent_traversal_artifact_path_blocks_recovery(self):
        report = build_restart_recovery_report(
            restart_id="restart-traversal-path",
            recovery_artifact_paths=["system/runtime/../restart_recovery_report.json"],
        )
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_partial_write_recovery_missing_blocks_pass(self):
        report = build_restart_recovery_report(
            restart_id="restart-partial-write-missing",
            partial_write_recovery_checked=False,
        )
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_empty_recovery_artifact_paths_blocks_recovery(self):
        report = build_restart_recovery_report(restart_id="restart-empty-paths", recovery_artifact_paths=[])
        result = validate_restart_recovery_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "RECONCILIATION_REQUIRED")

    def test_restart_recovery_validator_passes_current_contract(self):
        results = run_validators(["restart_recovery_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
