import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.evidence_write_helper_coverage import build_evidence_write_helper_audit, scan_evidence_write_helpers


ROOT = Path(__file__).resolve().parents[2]


class EvidenceWriteHelperCoverageTest(unittest.TestCase):
    def test_legacy_direct_writers_are_audited_and_no_new_direct_writer_appears(self):
        baseline_path = ROOT / "tests" / "runtime" / "fixtures" / "evidence_write_helper_legacy_direct_writers.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        allowed_legacy = set(baseline["legacy_local_direct_writer_paths"])

        audit = build_evidence_write_helper_audit(root=ROOT)
        discovered = set(audit["legacy_local_direct_writer_paths"])

        self.assertLessEqual(discovered, allowed_legacy)
        self.assertEqual(audit["status"], "BLOCKED" if discovered else "PASS")
        self.assertFalse(audit["live_order_ready"])
        self.assertFalse(audit["live_order_allowed"])
        self.assertFalse(audit["can_live_trade"])
        self.assertFalse(audit["scale_up_allowed"])

    def test_atomic_writer_coverage_is_measured_and_regression_visible(self):
        audit = build_evidence_write_helper_audit(root=ROOT)

        self.assertGreater(audit["writer_file_count"], 0)
        self.assertGreater(audit["covered_writer_count"], 0)
        self.assertGreaterEqual(audit["coverage_pct"], 0)
        self.assertLessEqual(audit["coverage_pct"], 100)
        if audit["legacy_local_direct_writer_count"]:
            self.assertTrue(audit["blockers"])
            self.assertEqual(audit["blockers"][0]["code"], "CONTRACT_GAP_HIGH")
        else:
            self.assertEqual(audit["next_action"], "Continue enforcing shared atomic writer coverage.")

    def test_direct_path_write_without_shared_helper_is_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools_dir = root / "tools"
            tools_dir.mkdir()
            (tools_dir / "bad_writer.py").write_text(
                "from pathlib import Path\n\n"
                "def emit(path: Path) -> None:\n"
                "    path.write_text('{\"status\":\"PASS\"}', encoding='utf-8')\n",
                encoding="utf-8",
            )

            scan = scan_evidence_write_helpers(root=root)
            self.assertEqual(scan["writer_file_count"], 1)
            self.assertEqual(scan["rows"][0]["classification"], "LOCAL_DIRECT")
            self.assertEqual(scan["rows"][0]["direct_write_line_numbers"], [4])

    def test_local_atomic_helper_without_fsync_is_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools_dir = root / "tools"
            tools_dir.mkdir()
            (tools_dir / "weak_atomic_writer.py").write_text(
                "import os\n\n"
                "def _atomic_write_text(path, value):\n"
                "    tmp = path.with_name(f'.{path.name}.tmp')\n"
                "    tmp.write_text(value, encoding='utf-8')\n"
                "    os.replace(tmp, path)\n\n"
                "def write_json(path, value):\n"
                "    _atomic_write_text(path, str(value))\n",
                encoding="utf-8",
            )

            scan = scan_evidence_write_helpers(root=root)
            self.assertEqual(scan["writer_file_count"], 1)
            self.assertEqual(scan["rows"][0]["classification"], "LOCAL_DIRECT")


if __name__ == "__main__":
    unittest.main()
