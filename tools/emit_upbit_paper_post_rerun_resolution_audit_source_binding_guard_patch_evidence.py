from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_upbit_paper_post_rerun_operator_resolution_audit_patch_evidence as base  # noqa: E402


PATCH_BASENAME = "MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RESOLUTION-AUDIT-SOURCE-BINDING-GUARD"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_DASHBOARD_BINDING"


def configure() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.CHANGED_ARTIFACTS = [
        "contracts/registry.yaml",
        "contracts/schema/patch_result.schema.json",
        "contracts/schema/upbit_paper_post_rerun_operator_resolution_audit_report.schema.json",
        "trader1/runtime/paper/upbit_paper_post_rerun_operator_resolution_audit.py",
        "trader1/validation/mvp0_validators.py",
        "tests/runtime/test_upbit_paper_post_rerun_operator_resolution_audit.py",
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_operator_resolution_audit_report.json",
        "contracts/security/source_bundle_manifest.json",
        "tools/emit_upbit_paper_post_rerun_operator_resolution_audit_patch_evidence.py",
        "tools/emit_upbit_paper_post_rerun_resolution_audit_source_binding_guard_patch_evidence.py",
        f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    ]
    base.BLOCKERS = [
        "POST_RERUN_RECONCILIATION_REQUIRED",
        "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
        "POST_RERUN_RESOLUTION_AUDIT_SOURCE_BINDING_REQUIRED",
        "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
        "LIVE_READY_MISSING",
        "API_UNVERIFIED",
        "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
        "READ_ONLY_BURN_IN_MISSING",
        "MANUAL_ORDER_TEST_MISSING",
        "OPERATOR_APPROVAL_MISSING",
        "LIVE_ENABLING_EVIDENCE_MISSING",
        "SCALE_UP_NOT_ELIGIBLE",
    ]


def main() -> int:
    configure()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
