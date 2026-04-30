import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_artifact_writer import (
    RUNTIME_REPORT_FILENAME,
    WRITER_FILENAME,
    shadow_observation_artifact_writer_hash,
    shadow_runtime_artifact_dir,
    validate_shadow_observation_artifact_writer_report,
    write_shadow_observation_runtime_artifacts,
)
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    shadow_observation_persistent_runtime_hash,
)
from trader1.research.shadow.shadow_observation_scheduler import (
    build_shadow_observation_scheduler_guard_report,
)
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle


def _scheduler_guard_report() -> dict:
    observations = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="shadow-writer-source",
            session_id=f"shadow-writer-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"shadow-writer-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"shadow-writer-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id="shadow-writer-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    return build_shadow_observation_scheduler_guard_report(
        scheduler_id="shadow-writer-scheduler",
        stream_report=stream,
        writer_id="writer-a",
        active_writer_id="writer-a",
    )


def _runtime_report() -> dict:
    return build_shadow_observation_persistent_runtime_report(
        runtime_id="shadow-writer-runtime",
        scheduler_guard_report=_scheduler_guard_report(),
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=10,
    )


class ShadowObservationArtifactWriterTest(unittest.TestCase):
    def test_writer_commits_runtime_stub_atomically_and_display_only(self):
        runtime_report = _runtime_report()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer_report = write_shadow_observation_runtime_artifacts(
                root=root,
                writer_id="shadow-writer-pass",
                runtime_report=runtime_report,
            )

            artifact_dir = shadow_runtime_artifact_dir(root, runtime_report)
            runtime_path = artifact_dir / RUNTIME_REPORT_FILENAME
            writer_path = artifact_dir / WRITER_FILENAME
            self.assertTrue(runtime_path.exists())
            self.assertTrue(writer_path.exists())
            self.assertEqual(list(artifact_dir.glob("*.tmp")), [])
            self.assertEqual(json.loads(runtime_path.read_text(encoding="utf-8"))["runtime_report_hash"], runtime_report["runtime_report_hash"])
            self.assertEqual(json.loads(writer_path.read_text(encoding="utf-8"))["writer_report_hash"], writer_report["writer_report_hash"])

            result = validate_shadow_observation_artifact_writer_report(writer_report, runtime_report=runtime_report)
            self.assertEqual(result.status, "PASS")
            self.assertEqual(writer_report["writer_status"], "PASS")
            self.assertEqual(writer_report["dashboard_visibility_status"], "VISIBLE_AS_STUB_ONLY")
            self.assertEqual(writer_report["artifact_truth_role"], "shadow_runtime_stub_display_truth_only")
            self.assertIn("/shadow/", writer_report["artifact_path"])
            self.assertFalse(writer_report["actual_persistent_runtime_executed"])
            self.assertFalse(writer_report["long_run_evidence_eligible"])
            self.assertFalse(writer_report["promotion_eligible"])
            self.assertFalse(writer_report["live_order_ready"])
            self.assertFalse(writer_report["live_order_allowed"])
            self.assertFalse(writer_report["can_live_trade"])
            self.assertFalse(writer_report["scale_up_allowed"])

    def test_writer_blocks_invalid_runtime_report_without_runtime_artifact(self):
        runtime_report = _runtime_report()
        runtime_report["live_order_allowed"] = True
        runtime_report["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(runtime_report)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer_report = write_shadow_observation_runtime_artifacts(
                root=root,
                writer_id="shadow-writer-blocked",
                runtime_report=runtime_report,
            )

            artifact_dir = shadow_runtime_artifact_dir(root, runtime_report)
            self.assertFalse((artifact_dir / RUNTIME_REPORT_FILENAME).exists())
            self.assertTrue((artifact_dir / WRITER_FILENAME).exists())
            result = validate_shadow_observation_artifact_writer_report(writer_report)
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
            self.assertEqual(writer_report["writer_status"], "BLOCKED")
            self.assertEqual(writer_report["dashboard_visibility_status"], "BLOCKED_FROM_DASHBOARD")
            self.assertFalse(writer_report["live_order_allowed"])

    def test_writer_validator_blocks_live_or_long_run_claim_drift(self):
        runtime_report = _runtime_report()
        with TemporaryDirectory() as tmp:
            writer_report = write_shadow_observation_runtime_artifacts(
                root=Path(tmp),
                writer_id="shadow-writer-mutation",
                runtime_report=runtime_report,
            )
            writer_report["long_run_evidence_eligible"] = True
            writer_report["writer_report_hash"] = shadow_observation_artifact_writer_hash(writer_report)

            result = validate_shadow_observation_artifact_writer_report(writer_report, runtime_report=runtime_report)
            self.assertEqual(result.status, "BLOCKED")
            self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")


if __name__ == "__main__":
    unittest.main()
