import unittest

from trader1.runtime.readiness.readiness_surface import (
    build_readiness_surface,
    render_first_line,
    surface_hash,
    validate_readiness_surface,
)
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators


class ReadinessSurfaceTest(unittest.TestCase):
    def test_can_start_and_live_review_do_not_create_live_readiness(self):
        surface = build_readiness_surface(
            authority=current_authority_hashes(),
            can_start=True,
            can_collect_data=True,
            can_live_review=True,
        )
        self.assertTrue(surface["can_start"])
        self.assertTrue(surface["can_live_review"])
        self.assertFalse(surface["live_order_ready"])
        self.assertFalse(surface["live_order_allowed"])
        self.assertFalse(surface["can_live_trade"])
        self.assertEqual(surface["primary_blocker_code"], "LIVE_READY_MISSING")
        self.assertEqual(render_first_line(surface), "LIVE TRADING: BLOCKED - LIVE_READY snapshot missing")
        self.assertEqual(validate_readiness_surface(surface).status, "PASS")

    def test_live_allowed_with_live_blocker_is_blocked(self):
        surface = build_readiness_surface(authority=current_authority_hashes())
        surface["live_order_ready"] = True
        surface["live_order_allowed"] = True
        surface["can_live_trade"] = True
        surface["live_trading_status"] = "LIVE_ACTIVE"
        surface["surface_hash"] = surface_hash(surface)
        result = validate_readiness_surface(surface)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_READY_MISSING")

    def test_standalone_ready_is_not_emitted_for_live_blocked_surface(self):
        surface = build_readiness_surface(authority=current_authority_hashes())
        self.assertNotEqual(render_first_line(surface), "READY")
        self.assertTrue(render_first_line(surface).startswith("LIVE TRADING: BLOCKED - "))

    def test_readiness_surface_validator_passes_current_contract(self):
        results = run_validators(["readiness_surface_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

