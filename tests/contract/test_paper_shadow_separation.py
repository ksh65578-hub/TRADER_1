import unittest

from trader1.research.shadow.shadow_runner import (
    build_paper_shadow_separation_report,
    paper_shadow_separation_hash,
    validate_paper_shadow_separation_report,
)


class PaperShadowSeparationTest(unittest.TestCase):
    def test_paper_shadow_paths_are_namespace_separated(self):
        report = build_paper_shadow_separation_report(separation_report_id="sep-pass")
        result = validate_paper_shadow_separation_report(report)
        self.assertEqual(result.status, "PASS")
        self.assertIn("/paper/", report["paper_artifact_path"])
        self.assertIn("/shadow/", report["shadow_artifact_path"])

    def test_raw_join_attempt_blocks(self):
        report = build_paper_shadow_separation_report(separation_report_id="sep-raw", raw_join_attempted=True)
        result = validate_paper_shadow_separation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_same_session_blocks(self):
        report = build_paper_shadow_separation_report(
            separation_report_id="sep-session",
            paper_session_id="same",
            shadow_session_id="same",
        )
        result = validate_paper_shadow_separation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_live_mutation_blocks(self):
        report = build_paper_shadow_separation_report(separation_report_id="sep-live")
        report["live_order_allowed"] = True
        report["can_live_trade"] = True
        report["separation_hash"] = paper_shadow_separation_hash(report)
        result = validate_paper_shadow_separation_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
