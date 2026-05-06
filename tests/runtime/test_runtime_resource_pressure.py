import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.runtime.health.runtime_resource_pressure import _safe_file_size, inspect_runtime_resource_pressure
from trader1.validation.mvp0_validators import run_validators


class RuntimeResourcePressureTest(unittest.TestCase):
    def test_empty_runtime_directory_is_pass(self):
        with TemporaryDirectory() as tmp:
            pressure = inspect_runtime_resource_pressure(Path(tmp))

        self.assertEqual(pressure.status, "PASS")
        self.assertIsNone(pressure.blocker_code)
        self.assertIn("PASS", pressure.heartbeat_component_overrides()["disk"]["status"])

    def test_runtime_artifact_growth_warns_before_hard_block(self):
        with TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            for index in range(3):
                (runtime_dir / f"artifact_{index}.json").write_text("{}", encoding="utf-8")
            pressure = inspect_runtime_resource_pressure(runtime_dir, warn_file_count=2, fail_file_count=10)

        self.assertEqual(pressure.status, "WARN")
        self.assertIsNone(pressure.blocker_code)
        self.assertEqual(pressure.heartbeat_component_overrides()["disk"]["status"], "WARN")

    def test_file_count_review_threshold_warns_without_disk_pressure(self):
        with TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            for index in range(12):
                (runtime_dir / f"artifact_{index}.json").write_text("{}", encoding="utf-8")
            pressure = inspect_runtime_resource_pressure(
                runtime_dir,
                warn_file_count=2,
                fail_file_count=10,
                hard_file_count=100,
                warn_bytes=10_000,
                fail_bytes=20_000,
            )

        self.assertEqual(pressure.status, "WARN")
        self.assertIsNone(pressure.blocker_code)
        self.assertIn("review threshold", pressure.message)
        self.assertEqual(pressure.heartbeat_component_overrides()["queue_backlog"]["status"], "WARN")

    def test_append_only_paper_audit_history_uses_cycle_scaled_file_budget(self):
        with TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            cycle_dir = runtime_dir / "paper_runtime" / "cycles"
            cycle_dir.mkdir(parents=True)
            for index in range(3):
                (cycle_dir / f"cycle-{index}.runtime_cycle.json").write_text("{}", encoding="utf-8")
            for index in range(12):
                (runtime_dir / f"artifact_{index}.json").write_text("{}", encoding="utf-8")
            pressure = inspect_runtime_resource_pressure(
                runtime_dir,
                warn_file_count=2,
                fail_file_count=10,
                hard_file_count=100,
                warn_bytes=10_000,
                fail_bytes=20_000,
            )

        self.assertEqual(pressure.status, "PASS")
        self.assertIsNone(pressure.blocker_code)
        self.assertIn("3 audit cycle(s)", pressure.message)
        self.assertEqual(pressure.heartbeat_component_overrides()["queue_backlog"]["status"], "PASS")

    def test_byte_pressure_hard_blocks(self):
        with TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            (runtime_dir / "large_artifact.json").write_text("123456789", encoding="utf-8")
            pressure = inspect_runtime_resource_pressure(runtime_dir, warn_bytes=4, fail_bytes=8)

        self.assertEqual(pressure.status, "FAIL")
        self.assertEqual(pressure.blocker_code, "RESOURCE_LIMIT_BLOCK")
        self.assertIn("bytes crossed fail threshold", pressure.message)
        self.assertEqual(pressure.heartbeat_component_overrides()["disk"]["status"], "FAIL")
        self.assertEqual(pressure.heartbeat_component_overrides()["queue_backlog"]["status"], "FAIL")

    def test_disappearing_atomic_temp_file_is_ignored(self):
        with TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            disappearing = runtime_dir / ".artifact.json.123.tmp"
            disappearing.write_text("partial", encoding="utf-8")
            disappearing.unlink()

            self.assertIsNone(_safe_file_size(disappearing))
            pressure = inspect_runtime_resource_pressure(runtime_dir)

        self.assertEqual(pressure.status, "PASS")

    def test_stale_runtime_write_lock_hard_blocks(self):
        with TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            lock = runtime_dir / ".runtime_write.lock"
            lock.write_text("stale", encoding="utf-8")
            old_time = time.time() - 120
            os.utime(lock, (old_time, old_time))
            pressure = inspect_runtime_resource_pressure(runtime_dir, stale_lock_seconds=1)

        self.assertEqual(pressure.status, "FAIL")
        self.assertEqual(pressure.blocker_code, "RESOURCE_LIMIT_BLOCK")
        self.assertEqual(pressure.heartbeat_component_overrides()["queue_backlog"]["status"], "FAIL")

    def test_runtime_resource_pressure_validator_passes_current_artifacts(self):
        result = run_validators(["runtime_resource_pressure_validator"])[0]
        self.assertEqual(result["status"], "PASS")
        self.assertIn("runtime session directories", result["notes"])


if __name__ == "__main__":
    unittest.main()
