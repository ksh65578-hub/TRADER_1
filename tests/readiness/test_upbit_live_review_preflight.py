import unittest

from trader1.dashboard.live_review_dashboard import build_live_review_dashboard, live_review_dashboard_hash, validate_live_review_dashboard
from trader1.runtime.readiness.live_preflight import (
    build_upbit_live_review_preflight,
    live_preflight_hash,
    validate_live_preflight_report,
)
from trader1.validation.mvp0_validators import current_authority_hashes


class UpbitLiveReviewPreflightTest(unittest.TestCase):
    def test_can_live_review_true_but_live_order_ready_false(self):
        report = build_upbit_live_review_preflight(authority=current_authority_hashes())
        self.assertTrue(report["can_live_review"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])
        self.assertFalse(report["can_submit_order"])
        self.assertFalse(report["order_adapter_called"])
        self.assertTrue(report["live_new_order_blocked"])
        self.assertEqual(validate_live_preflight_report(report).status, "PASS")

    def test_preflight_blocks_live_new_order(self):
        report = build_upbit_live_review_preflight(authority=current_authority_hashes())
        report["can_submit_order"] = True
        report["live_order_ready"] = True
        report["preflight_hash"] = live_preflight_hash(report)
        result = validate_live_preflight_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_official_api_missing_blocks_live_test(self):
        report = build_upbit_live_review_preflight(authority=current_authority_hashes())
        codes = {blocker["code"] for blocker in report["blockers"]}
        self.assertIn("API_UNVERIFIED", codes)
        self.assertEqual(report["official_api_verification_report"]["result"], "UNVERIFIED")
        self.assertFalse(report["live_order_ready"])

    def test_read_only_burn_in_does_not_imply_live_order_ready(self):
        report = build_upbit_live_review_preflight(
            authority=current_authority_hashes(),
            read_only_burn_in_status="PASS",
        )
        codes = {blocker["code"] for blocker in report["blockers"]}
        self.assertNotIn("READ_ONLY_BURN_IN_MISSING", codes)
        self.assertIn("LIVE_READY_MISSING", codes)
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertEqual(validate_live_preflight_report(report).status, "PASS")

    def test_preflight_blocks_status_and_blocker_mismatch(self):
        report = build_upbit_live_review_preflight(authority=current_authority_hashes())
        report["preflight_status"] = "PASS"
        report["preflight_hash"] = live_preflight_hash(report)
        result = validate_live_preflight_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        report = build_upbit_live_review_preflight(authority=current_authority_hashes())
        report["primary_blocker_code"] = "API_UNVERIFIED"
        report["readiness_surface"]["primary_blocker_code"] = "LIVE_READY_MISSING"
        report["preflight_hash"] = live_preflight_hash(report)
        result = validate_live_preflight_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_live_review_dashboard_is_display_only(self):
        preflight = build_upbit_live_review_preflight(authority=current_authority_hashes())
        dashboard = build_live_review_dashboard(authority=current_authority_hashes(), preflight_report=preflight)
        self.assertTrue(dashboard["display_only"])
        self.assertFalse(dashboard["order_controls_present"])
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertTrue(dashboard["first_line"].startswith("LIVE TRADING: BLOCKED - "))
        self.assertEqual(validate_live_review_dashboard(dashboard).status, "PASS")

    def test_live_review_dashboard_blocks_display_truth_mismatch(self):
        preflight = build_upbit_live_review_preflight(authority=current_authority_hashes())
        dashboard = build_live_review_dashboard(authority=current_authority_hashes(), preflight_report=preflight)
        dashboard["preflight_status"] = "PASS"
        dashboard["dashboard_hash"] = live_review_dashboard_hash(dashboard)
        result = validate_live_review_dashboard(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

        dashboard = build_live_review_dashboard(authority=current_authority_hashes(), preflight_report=preflight)
        dashboard["first_line"] = "LIVE TRADING: REVIEW ONLY - live orders blocked"
        dashboard["dashboard_hash"] = live_review_dashboard_hash(dashboard)
        result = validate_live_review_dashboard(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
