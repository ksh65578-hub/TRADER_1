import unittest

from trader1.runtime.readiness.official_api_verification import (
    build_official_api_verification_report,
    official_api_report_hash,
    validate_official_api_verification_report,
)
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators


class OfficialApiVerificationReportTest(unittest.TestCase):
    def test_unverified_official_api_report_blocks_live_readiness(self):
        report = build_official_api_verification_report(authority=current_authority_hashes())
        result = validate_official_api_verification_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "API_UNVERIFIED")
        self.assertEqual(report["result"], "UNVERIFIED")
        self.assertIsNone(report["expires_at_utc"])
        self.assertFalse(report["live_order_ready"])
        self.assertFalse(report["live_order_allowed"])
        self.assertFalse(report["can_live_trade"])

    def test_official_api_hash_tamper_fails(self):
        report = build_official_api_verification_report(authority=current_authority_hashes())
        report["exchange"] = "BINANCE"
        result = validate_official_api_verification_report(report)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_official_api_live_mutation_blocks(self):
        report = build_official_api_verification_report(authority=current_authority_hashes())
        report["live_order_ready"] = True
        report["report_hash"] = official_api_report_hash(report)
        result = validate_official_api_verification_report(report)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_upbit_live_review_validator_passes_current_contract(self):
        results = run_validators(["upbit_live_review_preflight_validator"])
        self.assertEqual(results[0]["status"], "PASS")

    def test_official_api_verification_validator_passes_current_contract(self):
        results = run_validators(["official_api_verification_validator"])
        self.assertEqual(results[0]["status"], "PASS")
        self.assertIn("without external calls", results[0]["notes"])


if __name__ == "__main__":
    unittest.main()
