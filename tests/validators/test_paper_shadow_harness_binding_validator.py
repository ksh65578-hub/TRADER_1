import unittest

from trader1.validation.mvp0_validators import paper_shadow_harness_binding_validator


class PaperShadowHarnessBindingValidatorTest(unittest.TestCase):
    def test_validator_passes(self):
        result = paper_shadow_harness_binding_validator()

        self.assertEqual(result.status, "PASS", result.message)


if __name__ == "__main__":
    unittest.main()
