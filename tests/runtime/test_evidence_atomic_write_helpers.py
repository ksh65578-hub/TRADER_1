import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text


class EvidenceAtomicWriteHelpersTest(unittest.TestCase):
    def test_write_text_replaces_existing_file_and_removes_temp_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("old", encoding="utf-8")

            write_text(path, "new")

            self.assertEqual(path.read_text(encoding="utf-8"), "new")
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_write_json_preserves_existing_file_when_serialization_fails(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text('{"status":"old"}\n', encoding="utf-8")

            with self.assertRaises(TypeError):
                write_json(path, {"bad": object()})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"status": "old"})
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_write_json_creates_parent_directory_with_valid_json(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "state.json"

            write_json(path, {"status": "PASS", "live_order_allowed": False})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"status": "PASS", "live_order_allowed": False})
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
