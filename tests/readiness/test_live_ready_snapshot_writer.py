import unittest
from pathlib import Path

from trader1.runtime.readiness.live_ready_snapshot import (
    attach_writer_input_hash,
    build_blocked_live_ready_snapshot,
    build_writer_input,
    evaluate_live_ready_snapshot_writer,
    validate_live_ready_snapshot,
)
from trader1.validation.mvp0_validators import current_authority_hashes, sha256_file, sha256_json, run_validators


ROOT = Path(__file__).resolve().parents[2]


def hashes():
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_bundle_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))}
    )
    source_tree_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "trader1").rglob("*.py")) if "__pycache__" not in path.parts}
    )
    return registry_hash, schema_bundle_hash, source_tree_hash


def writer_input():
    registry_hash, schema_bundle_hash, source_tree_hash = hashes()
    return build_writer_input(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        strategy_id="mvp0_strategy",
        strategy_build_id="mvp0_strategy_build",
        parameter_hash="mvp0_parameter_hash",
        risk_profile="CONSERVATIVE",
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )


class LiveReadySnapshotWriterTest(unittest.TestCase):
    def test_writer_input_is_not_snapshot_without_writer_pass_and_evidence(self):
        result = evaluate_live_ready_snapshot_writer(writer_input(), evidence_manifest_present=False)
        self.assertEqual(result.status, "BLOCKED")
        self.assertFalse(result.would_write_snapshot)
        self.assertFalse(result.live_order_ready)
        self.assertFalse(result.live_order_allowed)
        self.assertEqual(result.blocker_code, "LIVE_READY_SNAPSHOT_WRITER_UNTESTED")

    def test_stage_b_output_is_not_live_ready_snapshot(self):
        candidate = writer_input()
        candidate["promotion_input_type"] = "REFINEMENT_CANDIDATE"
        candidate["live_ready_snapshot_writer_status"] = "PASS"
        candidate["blockers"] = []
        candidate = attach_writer_input_hash(candidate)
        result = evaluate_live_ready_snapshot_writer(candidate, evidence_manifest_present=True)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "PROMOTION_INPUT_TYPE_INVALID")

    def test_missing_evidence_manifest_blocks_writer_pass(self):
        candidate = writer_input()
        candidate["live_ready_snapshot_writer_status"] = "PASS"
        candidate["blockers"] = []
        candidate = attach_writer_input_hash(candidate)
        result = evaluate_live_ready_snapshot_writer(candidate, evidence_manifest_present=False)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_READY_SNAPSHOT_WRITER_FAILED")

    def test_scope_mismatch_blocks_snapshot_write(self):
        candidate = writer_input()
        candidate["live_ready_snapshot_writer_status"] = "PASS"
        candidate["blockers"] = []
        candidate["evidence_manifest_hash"] = "E" * 64
        candidate = attach_writer_input_hash(candidate)
        result = evaluate_live_ready_snapshot_writer(
            candidate,
            expected_scope={"exchange": "BINANCE", "market_type": "SPOT", "strategy_id": "mvp0_strategy", "risk_profile": "CONSERVATIVE", "parameter_hash": "mvp0_parameter_hash"},
            evidence_manifest_present=True,
        )
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SNAPSHOT_SCOPE_MISMATCH")

    def test_live_order_allowed_snapshot_requires_all_live_evidence(self):
        registry_hash, schema_bundle_hash, source_tree_hash = hashes()
        snapshot = build_blocked_live_ready_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            registry_hash=registry_hash,
            schema_bundle_hash=schema_bundle_hash,
            source_tree_hash=source_tree_hash,
        )
        self.assertEqual(validate_live_ready_snapshot(snapshot).status, "PASS")
        snapshot["live_ready"] = True
        snapshot["live_order_allowed"] = True
        result = validate_live_ready_snapshot(snapshot)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "API_UNVERIFIED")

    def test_live_ready_true_without_live_order_allowed_still_requires_evidence(self):
        registry_hash, schema_bundle_hash, source_tree_hash = hashes()
        snapshot = build_blocked_live_ready_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            registry_hash=registry_hash,
            schema_bundle_hash=schema_bundle_hash,
            source_tree_hash=source_tree_hash,
        )
        snapshot["live_ready"] = True
        snapshot["live_order_allowed"] = False
        result = validate_live_ready_snapshot(snapshot)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "API_UNVERIFIED")
        self.assertFalse(result.live_order_ready)
        self.assertFalse(result.live_order_allowed)

    def test_placeholder_evidence_ids_block_live_ready_candidate(self):
        registry_hash, schema_bundle_hash, source_tree_hash = hashes()
        snapshot = build_blocked_live_ready_snapshot(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            registry_hash=registry_hash,
            schema_bundle_hash=schema_bundle_hash,
            source_tree_hash=source_tree_hash,
        )
        snapshot.update(
            {
                "live_ready": True,
                "live_order_allowed": False,
                "manual_order_test_required": False,
                "operator_approval_required": False,
                "official_api_verification_id": "official-api-placeholder",
                "read_only_burn_in_id": "read-only-burn-in-placeholder",
                "emergency_protection_evidence_id": "emergency-protection-placeholder",
                "invalidated_by": [],
                "validator_rollup_status": "PASS",
                "manifest_hash": "mvp0-blocked-manifest",
            }
        )
        result = validate_live_ready_snapshot(snapshot)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_READY_SNAPSHOT_WRITER_FAILED")
        self.assertFalse(result.live_order_ready)

    def test_writer_pass_with_placeholder_evidence_hash_is_blocked(self):
        candidate = writer_input()
        candidate["live_ready_snapshot_writer_status"] = "PASS"
        candidate["blockers"] = []
        candidate = attach_writer_input_hash(candidate)
        result = evaluate_live_ready_snapshot_writer(candidate, evidence_manifest_present=True)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_READY_SNAPSHOT_WRITER_FAILED")
        self.assertFalse(result.would_write_snapshot)

    def test_live_ready_snapshot_writer_validator_passes_current_contract(self):
        results = run_validators(["live_ready_snapshot_writer_validator"])
        self.assertEqual(results[0]["status"], "PASS")

    def test_live_ready_snapshot_validator_passes_current_contract(self):
        results = run_validators(["live_ready_snapshot_validator"])
        self.assertEqual(results[0]["status"], "PASS")
        self.assertIn("missing evidence", results[0]["notes"])


if __name__ == "__main__":
    unittest.main()
