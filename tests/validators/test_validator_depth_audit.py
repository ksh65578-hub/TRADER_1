import unittest

from tools.audit_validator_depth import build_validator_depth_audit


class ValidatorDepthAuditTest(unittest.TestCase):
    def test_implemented_validators_have_no_blocking_depth_gaps(self):
        audit = build_validator_depth_audit()
        self.assertEqual(audit["audit_status"], "PASS")
        self.assertEqual(audit["blocking_gap_count"], 0)
        self.assertGreaterEqual(audit["implemented_validator_count"], 70)
        self.assertFalse(audit["live_order_ready"])
        self.assertFalse(audit["live_order_allowed"])
        self.assertFalse(audit["can_live_trade"])
        self.assertFalse(audit["scale_up_allowed"])

    def test_convergence_objective_profile_is_not_schema_only(self):
        audit = build_validator_depth_audit()
        reports = {item["validator_id"]: item for item in audit["validator_reports"]}
        report = reports["convergence_objective_profile_validator"]
        self.assertNotIn(report["depth_class"], {"DEPTH_0_DECLARED_ONLY", "DEPTH_1_SCHEMA_OR_WRAPPER_ONLY"})
        self.assertGreaterEqual(report["fail_or_blocked_calls"], 4)
        self.assertGreaterEqual(report["branch_count"], 4)


if __name__ == "__main__":
    unittest.main()
