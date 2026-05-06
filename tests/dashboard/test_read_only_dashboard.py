import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from trader1.config.config_schema import build_runtime_config
from trader1.dashboard.read_only_dashboard import (
    build_read_only_dashboard_shell,
    dashboard_shell_hash,
    render_dashboard_html,
    validate_dashboard_visual_layout_contract,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.summary_writer import build_summary_shell
from trader1.core.ledger.restart_recovery import build_restart_recovery_report
from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle
from trader1.runtime.boot.startup_probe import build_startup_probe
from trader1.runtime.health.heartbeat import build_heartbeat
from trader1.runtime.health.stability_history import append_stability_history
from trader1.runtime.portfolio.paper_portfolio import (
    build_initial_paper_portfolio_snapshot,
    build_paper_portfolio_snapshot_from_fill,
)
from trader1.runtime.paper.operational_cycle import build_upbit_operational_paper_cycle
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    upbit_paper_ledger_idempotency_runtime_evidence_hash,
)
from trader1.runtime.paper.upbit_paper_post_rerun_current_evidence_closure_recheck import (
    upbit_paper_post_rerun_current_evidence_closure_recheck_hash,
)
from trader1.runtime.paper.upbit_paper_post_rerun_operator_reconciliation_queue import (
    upbit_paper_post_rerun_operator_reconciliation_queue_hash,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_repair_path import (
    upbit_paper_post_rerun_reconciliation_repair_path_hash,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (
    upbit_paper_post_repair_reconciliation_hash,
)
from trader1.runtime.paper.upbit_paper_repair_operator_queue import (
    upbit_paper_repair_operator_queue_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_post_regeneration_reconciliation import (
    stale_loop_post_regeneration_reconciliation_hash,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation_operator_queue_closure import (
    build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
)
from trader1.runtime.paper.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard import (
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_precheck import (
    build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
    upbit_paper_repaired_current_evidence_audited_writer_precheck_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_design import (
    build_upbit_paper_repaired_current_evidence_audited_writer_design_report,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_dry_run import (
    build_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
    upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_locked_output import (
    build_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report,
    upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer_implementation_prep import (
    build_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report,
    upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (
    AUDITED_WRITER_IDEMPOTENT_STATUS,
    AUDITED_WRITER_WRITTEN_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    upbit_paper_audited_current_evidence_snapshot_hash,
    upbit_paper_repaired_current_evidence_audited_writer_report_hash,
)
from trader1.runtime.paper.upbit_paper_runtime import build_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    run_upbit_paper_persistent_loop,
    upbit_paper_runtime_recovery_guard_hash,
)
from trader1.runtime.paper.upbit_public_rest_continuity_history import (
    build_upbit_public_rest_continuity_history_report,
    upbit_public_rest_continuity_history_hash,
)
from tools.run_upbit_paper_runtime_evidence_collection_profile import (
    run_upbit_paper_runtime_evidence_collection_profile,
)
from trader1.runtime.readiness.readiness_surface import build_readiness_surface
from trader1.runtime.reconciliation.reconciliation import build_reconciliation_report
from trader1.research.shadow.shadow_observation import build_shadow_observation_report
from trader1.research.shadow.shadow_observation_actual_runtime_harness import build_shadow_observation_actual_runtime_harness_report
from trader1.research.shadow.shadow_observation_persistent_runtime import (
    build_shadow_observation_persistent_runtime_report,
    shadow_observation_persistent_runtime_hash,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
)
from trader1.research.shadow.shadow_observation_scheduler import build_shadow_observation_scheduler_guard_report
from trader1.research.shadow.shadow_observation_stream import build_shadow_observation_stream_report
from trader1.reports.residual_operator_reconciliation_submission_template_packet import (
    build_residual_operator_reconciliation_submission_template_packet_report,
)
from trader1.reports.residual_operator_reconciliation_submission_security_quarantine import (
    build_residual_operator_reconciliation_submission_security_quarantine_report,
)
from trader1.reports.residual_operator_reconciliation_submission_review_queue import (
    build_residual_operator_reconciliation_submission_review_queue_report,
)
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators, sha256_file, sha256_json


ROOT = Path(__file__).resolve().parents[2]


def registry():
    return json.loads((ROOT / "contracts" / "registry.yaml").read_text(encoding="utf-8"))


def hashes():
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_bundle_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))}
    )
    source_tree_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "trader1").rglob("*.py")) if "__pycache__" not in path.parts}
    )
    return registry_hash, schema_bundle_hash, source_tree_hash


def krw_display(value):
    return f"{Decimal(str(value)):,.0f} KRW"


def build_inputs(
    session_id="test_read_only_dashboard",
    with_paper_portfolio=True,
    heartbeat_component_overrides=None,
    paper_portfolio_snapshot=None,
):
    registry_hash, schema_bundle_hash, source_tree_hash = hashes()
    config = build_runtime_config(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        registry_hash=registry_hash,
    )
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        component_overrides=heartbeat_component_overrides,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    paper_portfolio = paper_portfolio_snapshot
    if paper_portfolio is None:
        paper_portfolio = (
            build_initial_paper_portfolio_snapshot(
                exchange="UPBIT",
                market_type="KRW_SPOT",
                session_id=session_id,
            )
            if with_paper_portfolio
            else None
        )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=paper_portfolio,
    )
    return summary, heartbeat, startup_probe


def optimizer_feedback_fixture(name="optimizer_feedback_pass.json"):
    return json.loads((ROOT / "tests" / "validators" / "fixtures" / name).read_text(encoding="utf-8"))


def convergence_assessment_fixture(name="convergence_assessment_pass.json"):
    return json.loads((ROOT / "tests" / "validators" / "fixtures" / name).read_text(encoding="utf-8"))


def exploration_policy_fixture(name="exploration_exploitation_policy_pass.json"):
    return json.loads((ROOT / "tests" / "validators" / "fixtures" / name).read_text(encoding="utf-8"))


def parameter_narrowing_fixture(name="parameter_narrowing_pass.json"):
    return json.loads((ROOT / "tests" / "validators" / "fixtures" / name).read_text(encoding="utf-8"))


def paper_exposure_quality_fixture(name="paper_exposure_quality_pass.json"):
    return json.loads((ROOT / "tests" / "validators" / "fixtures" / name).read_text(encoding="utf-8"))


def profitability_maturity_rollup_fixture():
    return json.loads(
        (ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json").read_text(
            encoding="utf-8"
        )
    )


def residual_open_gap_action_plan_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_handoff_packet_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_execution_guide_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_evidence_progress_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_evidence_completion_acceptance_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_reconciliation_review_cards_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_reconciliation_intake_preflight_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_reconciliation_submission_manifest_preflight_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "evidence"
            / "audit_reports"
            / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT.report.json"
        ).read_text(encoding="utf-8")
    )


def residual_operator_reconciliation_submission_template_packet_fixture():
    path = (
        ROOT
        / "system"
        / "evidence"
        / "audit_reports"
        / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET.report.json"
    )
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_residual_operator_reconciliation_submission_template_packet_report(
        residual_operator_reconciliation_intake_preflight_fixture(),
        residual_operator_reconciliation_submission_manifest_preflight_fixture(),
        json.loads((ROOT / "contracts" / "generated" / "current_implementation_state.json").read_text(encoding="utf-8")),
        patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET",
        generated_at_utc="2026-05-06T00:00:00Z",
        trader1_sha256="TEST_TRADER_HASH",
        agents_sha256="TEST_AGENTS_HASH",
    )


def residual_operator_reconciliation_submission_security_quarantine_fixture():
    path = (
        ROOT
        / "system"
        / "evidence"
        / "audit_reports"
        / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_SECURITY_QUARANTINE.report.json"
    )
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_residual_operator_reconciliation_submission_security_quarantine_report(
        residual_operator_reconciliation_submission_manifest_preflight_fixture(),
        residual_operator_reconciliation_submission_template_packet_fixture(),
        json.loads((ROOT / "contracts" / "generated" / "current_implementation_state.json").read_text(encoding="utf-8")),
        patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_SECURITY_QUARANTINE",
        generated_at_utc="2026-05-06T00:00:00Z",
        trader1_sha256="TEST_TRADER_HASH",
        agents_sha256="TEST_AGENTS_HASH",
    )


def residual_operator_reconciliation_submission_review_queue_fixture():
    path = (
        ROOT
        / "system"
        / "evidence"
        / "audit_reports"
        / "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE.report.json"
    )
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return build_residual_operator_reconciliation_submission_review_queue_report(
        residual_operator_reconciliation_submission_manifest_preflight_fixture(),
        residual_operator_reconciliation_submission_template_packet_fixture(),
        residual_operator_reconciliation_submission_security_quarantine_fixture(),
        json.loads((ROOT / "contracts" / "generated" / "current_implementation_state.json").read_text(encoding="utf-8")),
        patch_id="TEST_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE",
        generated_at_utc="2026-05-06T00:00:00Z",
        trader1_sha256="TEST_TRADER_HASH",
        agents_sha256="TEST_AGENTS_HASH",
    )


def candidate_scorecard_fixture(session_id="test_read_only_dashboard"):
    runtime = build_upbit_paper_runtime_cycle_report(
        cycle_id=f"dashboard-scorecard-{session_id}",
        session_id=session_id,
    )
    return candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)


def build_dashboard(
    with_paper_portfolio=True,
    heartbeat_component_overrides=None,
    paper_portfolio_snapshot=None,
    reconciliation_report=None,
    restart_recovery_report=None,
    upbit_paper_persistent_loop_report=None,
    upbit_paper_runtime_recovery_guard_report=None,
    upbit_paper_runtime_evidence_collection_profile_report=None,
    optimizer_feedback_report=None,
    convergence_assessment_report=None,
    exploration_exploitation_policy=None,
    parameter_narrowing_report=None,
    paper_exposure_quality_report=None,
    upbit_paper_post_rerun_reconciliation_blocker_rollup_report=None,
    profitability_maturity_rollup_report=None,
    candidate_scorecard=None,
    upbit_public_rest_continuity_history=None,
    shadow_runtime_harness_report=None,
    shadow_persistent_runtime_report=None,
    upbit_paper_post_rerun_operator_resolution_audit_report=None,
    upbit_paper_post_rerun_operator_reconciliation_queue_report=None,
    upbit_paper_post_rerun_resolution_current_evidence_closure_report=None,
    upbit_paper_post_rerun_current_evidence_closure_recheck_report=None,
    upbit_paper_post_rerun_reconciliation_repair_path_report=None,
    upbit_paper_post_repair_reconciliation_report=None,
    upbit_paper_repair_operator_queue_report=None,
    upbit_paper_stale_loop_post_regeneration_reconciliation_report=None,
    upbit_paper_stale_loop_reconciliation_operator_queue_closure_report=None,
    upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=None,
    upbit_paper_repaired_current_evidence_audited_writer_precheck_report=None,
    upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=None,
    upbit_paper_repaired_current_evidence_audited_writer_locked_output_report=None,
    upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report=None,
    upbit_paper_repaired_current_evidence_audited_writer_report=None,
    audited_current_evidence_snapshot=None,
    audited_paper_portfolio_snapshot=None,
    upbit_paper_ledger_idempotency_runtime_evidence_report=None,
    residual_open_gap_operator_action_plan_report=None,
    residual_operator_handoff_packet_report=None,
    residual_operator_execution_guide_report=None,
    residual_operator_evidence_progress_report=None,
    residual_operator_evidence_completion_acceptance_report=None,
    residual_operator_reconciliation_review_cards_report=None,
    residual_operator_reconciliation_intake_preflight_report=None,
    residual_operator_reconciliation_submission_manifest_preflight_report=None,
    residual_operator_reconciliation_submission_template_packet_report=None,
    residual_operator_reconciliation_submission_security_quarantine_report=None,
    residual_operator_reconciliation_submission_review_queue_report=None,
):
    summary, heartbeat, startup_probe = build_inputs(
        with_paper_portfolio=with_paper_portfolio,
        heartbeat_component_overrides=heartbeat_component_overrides,
        paper_portfolio_snapshot=paper_portfolio_snapshot,
    )
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_read_only_dashboard",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        reconciliation_report=reconciliation_report,
        restart_recovery_report=restart_recovery_report,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
        upbit_paper_post_rerun_operator_reconciliation_queue_report=upbit_paper_post_rerun_operator_reconciliation_queue_report,
        upbit_paper_post_rerun_operator_resolution_audit_report=upbit_paper_post_rerun_operator_resolution_audit_report,
        upbit_paper_post_rerun_resolution_current_evidence_closure_report=upbit_paper_post_rerun_resolution_current_evidence_closure_report,
        upbit_paper_post_rerun_current_evidence_closure_recheck_report=upbit_paper_post_rerun_current_evidence_closure_recheck_report,
        upbit_paper_post_rerun_reconciliation_repair_path_report=upbit_paper_post_rerun_reconciliation_repair_path_report,
        upbit_paper_post_repair_reconciliation_report=upbit_paper_post_repair_reconciliation_report,
        upbit_paper_repair_operator_queue_report=upbit_paper_repair_operator_queue_report,
        upbit_paper_stale_loop_post_regeneration_reconciliation_report=upbit_paper_stale_loop_post_regeneration_reconciliation_report,
        upbit_paper_stale_loop_reconciliation_operator_queue_closure_report=upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=upbit_paper_repaired_current_evidence_audited_writer_precheck_report,
        upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=upbit_paper_repaired_current_evidence_audited_writer_dry_run_report,
        upbit_paper_repaired_current_evidence_audited_writer_locked_output_report=upbit_paper_repaired_current_evidence_audited_writer_locked_output_report,
        upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report=upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report,
        upbit_paper_repaired_current_evidence_audited_writer_report=upbit_paper_repaired_current_evidence_audited_writer_report,
        audited_current_evidence_snapshot=audited_current_evidence_snapshot,
        audited_paper_portfolio_snapshot=audited_paper_portfolio_snapshot,
        upbit_paper_ledger_idempotency_runtime_evidence_report=upbit_paper_ledger_idempotency_runtime_evidence_report,
        residual_open_gap_operator_action_plan_report=residual_open_gap_operator_action_plan_report,
        residual_operator_handoff_packet_report=residual_operator_handoff_packet_report,
        residual_operator_execution_guide_report=residual_operator_execution_guide_report,
        residual_operator_evidence_progress_report=residual_operator_evidence_progress_report,
        residual_operator_evidence_completion_acceptance_report=residual_operator_evidence_completion_acceptance_report,
        residual_operator_reconciliation_review_cards_report=residual_operator_reconciliation_review_cards_report,
        residual_operator_reconciliation_intake_preflight_report=residual_operator_reconciliation_intake_preflight_report,
        residual_operator_reconciliation_submission_manifest_preflight_report=residual_operator_reconciliation_submission_manifest_preflight_report,
        residual_operator_reconciliation_submission_template_packet_report=residual_operator_reconciliation_submission_template_packet_report,
        residual_operator_reconciliation_submission_security_quarantine_report=residual_operator_reconciliation_submission_security_quarantine_report,
        residual_operator_reconciliation_submission_review_queue_report=residual_operator_reconciliation_submission_review_queue_report,
        upbit_paper_persistent_loop_report=upbit_paper_persistent_loop_report,
        upbit_paper_runtime_recovery_guard_report=upbit_paper_runtime_recovery_guard_report,
        upbit_paper_runtime_evidence_collection_profile_report=upbit_paper_runtime_evidence_collection_profile_report,
        optimizer_feedback_report=optimizer_feedback_report,
        convergence_assessment_report=convergence_assessment_report,
        exploration_exploitation_policy=exploration_exploitation_policy,
        parameter_narrowing_report=parameter_narrowing_report,
        paper_exposure_quality_report=paper_exposure_quality_report,
        profitability_maturity_rollup_report=profitability_maturity_rollup_report,
        candidate_scorecard=candidate_scorecard,
        upbit_public_rest_continuity_history=upbit_public_rest_continuity_history,
        shadow_runtime_harness_report=shadow_runtime_harness_report,
        shadow_persistent_runtime_report=shadow_persistent_runtime_report,
    )


def paper_runtime_recovery_guard_fixture(session_id="test_read_only_dashboard", blocked=False):
    blockers = []
    if blocked:
        blockers = [
            {
                "code": "PARTIAL_WRITE_RECOVERY_REQUIRED",
                "severity": "HIGH",
                "message": "orphan runtime temp files require operator review before continuing PAPER runtime",
            }
        ]
    report = {
        "schema_id": "trader1.upbit_paper_runtime_recovery_guard_report.v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project_id": "TRADER_1",
        "guard_id": "test-dashboard-paper-runtime-recovery-guard",
        "loop_id": "test-dashboard-paper-runtime-loop",
        "exchange": "UPBIT",
        "market_type": "KRW_SPOT",
        "mode": "PAPER",
        "session_id": session_id,
        "latest_cycle_path": "system/runtime/upbit/krw_spot/paper/test_read_only_dashboard/upbit_paper_runtime_cycle_report.json",
        "latest_cycle_status": "PASS",
        "latest_cycle_hash": "A" * 64,
        "latest_cycle_recoverable": True,
        "canonical_jsonl_checked_count": 2,
        "corrupted_jsonl_quarantined_count": 1 if blocked else 0,
        "ledger_jsonl_checked_count": 1,
        "corrupted_ledger_jsonl_quarantined_count": 0,
        "ledger_jsonl_invalid_count": 0,
        "orphan_tmp_file_count": 1 if blocked else 0,
        "artifact_paths": [
            "system/runtime/upbit/krw_spot/paper/test_read_only_dashboard/upbit_paper_runtime_cycle_report.json"
        ],
        "recovery_guard_status": "BLOCKED" if blocked else "PASS",
        "primary_blocker_code": "PARTIAL_WRITE_RECOVERY_REQUIRED" if blocked else None,
        "blockers": blockers,
        "resume_action": "SAFE_MODE_RECONCILE" if blocked else "RESUME_PAPER_ONLY",
        "paper_runtime_resume_allowed": not blocked,
        "runtime_evidence_role": "PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE",
        "actual_long_run_evidence_created": False,
        "long_run_evidence_eligible": False,
        "long_run_blocker_code": "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
        "long_run_next_action": "Collect validated long-run PAPER and SHADOW runtime evidence before live review.",
        "promotion_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "guard_hash": "",
    }
    report["guard_hash"] = upbit_paper_runtime_recovery_guard_hash(report)
    return report


def build_dashboard_with_paper_runtime_recovery_guard(report=None):
    report = report or paper_runtime_recovery_guard_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_runtime_recovery_guard_report=report,
    )


def build_dashboard_with_paper_runtime_evidence_collection_profile(report=None):
    report = report or run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_runtime_evidence_collection_profile_report=report,
    )


def paper_persistent_loop_fixture(session_id="test_read_only_dashboard"):
    with TemporaryDirectory() as tmp:
        return run_upbit_paper_persistent_loop(
            root=Path(tmp),
            loop_id="test-dashboard-paper-persistent-loop",
            session_id=session_id,
            requested_cycle_count=1,
        )


def ledger_idempotency_runtime_evidence_fixture(
    session_id="mvp1_upbit_paper_launcher",
    evidence_id="test-dashboard-ledger-idempotency-runtime-evidence",
):
    with TemporaryDirectory() as tmp:
        runtime_root = Path(tmp)
        run_upbit_paper_persistent_loop(
            root=runtime_root,
            loop_id=evidence_id,
            session_id=session_id,
            requested_cycle_count=1,
        )
        return build_upbit_paper_ledger_idempotency_runtime_evidence_report(
            root=runtime_root,
            session_id=session_id,
            evidence_id=evidence_id,
        )


def build_dashboard_with_paper_persistent_loop(report=None):
    report = report or paper_persistent_loop_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_persistent_loop_report=report,
    )


def build_dashboard_with_paper_exposure_quality(report=None):
    report = report or paper_exposure_quality_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        paper_exposure_quality_report=report,
    )


def build_dashboard_with_operation_gate():
    session_id = "test_read_only_dashboard"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    operation_gate = build_upbit_operational_paper_cycle(
        operation_gate_id="test-dashboard-profitability-maturity",
        session_id=session_id,
    )
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        paper_operation_gate_report=operation_gate,
    )


def build_dashboard_with_reconciliation(reconciliation_report=None, restart_recovery_report=None):
    session_id = "test_read_only_dashboard_reconciliation"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    reconciliation_report = reconciliation_report or build_reconciliation_report(
        reconciliation_id="test-dashboard-reconciliation",
        session_id=session_id,
    )
    restart_recovery_report = restart_recovery_report or build_restart_recovery_report(
        restart_id="test-dashboard-restart",
        session_id=session_id,
    )
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        reconciliation_report=reconciliation_report,
        restart_recovery_report=restart_recovery_report,
    )


def build_dashboard_with_ledger_idempotency_runtime_evidence(report=None):
    report = report or ledger_idempotency_runtime_evidence_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_ledger_idempotency_runtime_evidence_report=report,
    )


def post_rerun_blocker_rollup_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
        ).read_text(encoding="utf-8")
    )


def post_rerun_review_guidance_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json"
        ).read_text(encoding="utf-8")
    )


def post_rerun_operator_reconciliation_queue_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_operator_reconciliation_queue_report.json"
        ).read_text(encoding="utf-8")
    )


def post_rerun_resolution_audit_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_operator_resolution_audit_report.json"
        ).read_text(encoding="utf-8")
    )


def post_rerun_resolution_current_evidence_closure_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"
        ).read_text(encoding="utf-8")
    )


def post_rerun_current_evidence_closure_recheck_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json"
        ).read_text(encoding="utf-8")
    )


def post_rerun_reconciliation_repair_path_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_rerun_reconciliation_repair_path_report.json"
        ).read_text(encoding="utf-8")
    )


def post_repair_reconciliation_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_post_repair_reconciliation_report.json"
        ).read_text(encoding="utf-8")
    )


def repair_operator_queue_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_repair_operator_queue_report.json"
        ).read_text(encoding="utf-8")
    )


def stale_loop_post_regeneration_reconciliation_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
        ).read_text(encoding="utf-8")
    )


def stale_loop_operator_queue_closure_fixture(post_report=None, ledger_report=None):
    post_report = post_report or stale_loop_post_regeneration_reconciliation_fixture()
    ledger_report = ledger_report or ledger_idempotency_runtime_evidence_fixture(
        session_id=post_report["session_id"],
        evidence_id="test-dashboard-stale-loop-operator-queue-closure-ledger",
    )
    return build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
        post_regeneration_reconciliation_report=post_report,
        ledger_idempotency_evidence_report=ledger_report,
        closure_id="test-dashboard-stale-loop-operator-queue-closure",
    )


def stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture():
    return json.loads(
        (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / "mvp1_upbit_paper_launcher"
            / "paper_runtime"
            / "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json"
        ).read_text(encoding="utf-8")
    )


def audited_writer_precheck_fixture(source_guard_report=None):
    return build_upbit_paper_repaired_current_evidence_audited_writer_precheck_report(
        root=ROOT,
        source_current_evidence_guard_report=source_guard_report
        or stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture(),
        audited_writer_precheck_id="test-dashboard-audited-writer-precheck",
    )


def audited_writer_design_fixture(source_precheck_report=None, source_guard_report=None):
    return build_upbit_paper_repaired_current_evidence_audited_writer_design_report(
        root=ROOT,
        source_audited_writer_precheck_report=source_precheck_report
        or audited_writer_precheck_fixture(source_guard_report),
        audited_writer_design_id="test-dashboard-audited-writer-design",
    )


def audited_writer_dry_run_fixture(source_design_report=None):
    return build_upbit_paper_repaired_current_evidence_audited_writer_dry_run_report(
        root=ROOT,
        source_audited_writer_design_report=source_design_report or audited_writer_design_fixture(),
        audited_writer_dry_run_id="test-dashboard-audited-writer-dry-run",
    )


def audited_writer_locked_output_fixture(source_dry_run_report=None):
    return build_upbit_paper_repaired_current_evidence_audited_writer_locked_output_report(
        root=ROOT,
        source_audited_writer_dry_run_report=source_dry_run_report or audited_writer_dry_run_fixture(),
        audited_writer_locked_output_id="test-dashboard-audited-writer-locked-output",
    )


def audited_writer_implementation_prep_fixture(source_locked_output_report=None):
    with TemporaryDirectory() as tmp:
        return build_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report(
            root=Path(tmp),
            source_audited_writer_locked_output_report=source_locked_output_report or audited_writer_locked_output_fixture(),
            audited_writer_implementation_prep_id="test-dashboard-audited-writer-implementation-prep",
        )


def audited_writer_output_fixture():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        implementation_prep = audited_writer_implementation_prep_fixture()
        ledger_rollup = json.loads(
            (
                ROOT
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / "mvp1_upbit_paper_launcher"
                / "ledger"
                / "paper_ledger_rollup_report.json"
            ).read_text(encoding="utf-8")
        )
        writer_report = build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=implementation_prep,
            source_ledger_rollup_report=ledger_rollup,
            audited_writer_id="test-dashboard-audited-current-evidence-writer",
        )
        runtime_base = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / implementation_prep["session_id"]
        )
        current_evidence = json.loads(
            (
                runtime_base
                / "paper_runtime"
                / "current_evidence"
                / "audited_current_evidence_snapshot.json"
            ).read_text(encoding="utf-8")
        )
        paper_portfolio = json.loads(
            (runtime_base / "paper_runtime" / "portfolio" / "paper_portfolio_snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        return writer_report, current_evidence, paper_portfolio, implementation_prep


def audited_writer_full_activation_outputs_fixture():
    source_guard = stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
    precheck = audited_writer_precheck_fixture(source_guard)
    design = audited_writer_design_fixture(precheck)
    dry_run = audited_writer_dry_run_fixture(design)
    locked_output = audited_writer_locked_output_fixture(dry_run)
    implementation_prep = audited_writer_implementation_prep_fixture(locked_output)
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        ledger_rollup = json.loads(
            (
                ROOT
                / "system"
                / "runtime"
                / "upbit"
                / "krw_spot"
                / "paper"
                / "mvp1_upbit_paper_launcher"
                / "ledger"
                / "paper_ledger_rollup_report.json"
            ).read_text(encoding="utf-8")
        )
        writer_report = build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=root,
            source_implementation_prep_report=implementation_prep,
            source_ledger_rollup_report=ledger_rollup,
            audited_writer_id="test-dashboard-audited-current-evidence-writer-full-chain",
        )
        runtime_base = (
            root
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "paper"
            / implementation_prep["session_id"]
        )
        current_evidence = json.loads(
            (
                runtime_base
                / "paper_runtime"
                / "current_evidence"
                / "audited_current_evidence_snapshot.json"
            ).read_text(encoding="utf-8")
        )
        paper_portfolio = json.loads(
            (runtime_base / "paper_runtime" / "portfolio" / "paper_portfolio_snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        return writer_report, current_evidence, paper_portfolio, precheck, dry_run, locked_output, implementation_prep


def build_dashboard_with_audited_current_evidence_writer(outputs=None):
    writer_report, current_evidence, paper_portfolio, implementation_prep = outputs or audited_writer_output_fixture()
    session_id = writer_report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id, with_paper_portfolio=False)
    return build_read_only_dashboard_shell(
        exchange=writer_report["exchange"],
        market_type=writer_report["market_type"],
        mode=writer_report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report=implementation_prep,
        upbit_paper_repaired_current_evidence_audited_writer_report=writer_report,
        audited_current_evidence_snapshot=current_evidence,
        audited_paper_portfolio_snapshot=paper_portfolio,
    )


def build_dashboard_with_full_audited_writer_activation_chain(outputs=None):
    (
        writer_report,
        current_evidence,
        paper_portfolio,
        precheck,
        dry_run,
        locked_output,
        implementation_prep,
    ) = outputs or audited_writer_full_activation_outputs_fixture()
    session_id = writer_report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id, with_paper_portfolio=False)
    return build_read_only_dashboard_shell(
        exchange=writer_report["exchange"],
        market_type=writer_report["market_type"],
        mode=writer_report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=precheck,
        upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=dry_run,
        upbit_paper_repaired_current_evidence_audited_writer_locked_output_report=locked_output,
        upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report=implementation_prep,
        upbit_paper_repaired_current_evidence_audited_writer_report=writer_report,
        audited_current_evidence_snapshot=current_evidence,
        audited_paper_portfolio_snapshot=paper_portfolio,
    )


def build_dashboard_with_post_rerun_blocker_rollup(report=None):
    report = report or post_rerun_blocker_rollup_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=report,
    )


def build_dashboard_with_post_rerun_review_guidance(report=None, rollup_report=None):
    report = report or post_rerun_review_guidance_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=rollup_report,
        upbit_paper_post_rerun_operator_reconciliation_review_guidance_report=report,
    )


def build_dashboard_with_post_rerun_operator_reconciliation_queue(report=None, rollup_report=None, guidance_report=None):
    report = report or post_rerun_operator_reconciliation_queue_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=rollup_report,
        upbit_paper_post_rerun_operator_reconciliation_review_guidance_report=guidance_report,
        upbit_paper_post_rerun_operator_reconciliation_queue_report=report,
    )


def build_dashboard_with_post_rerun_resolution_audit(report=None, rollup_report=None, guidance_report=None):
    report = report or post_rerun_resolution_audit_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=rollup_report,
        upbit_paper_post_rerun_operator_reconciliation_review_guidance_report=guidance_report,
        upbit_paper_post_rerun_operator_resolution_audit_report=report,
    )


def build_dashboard_with_residual_priority_resolution_binding():
    report = post_rerun_resolution_audit_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
        residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
        residual_operator_execution_guide_report=residual_operator_execution_guide_fixture(),
        residual_operator_evidence_progress_report=residual_operator_evidence_progress_fixture(),
        upbit_paper_post_rerun_operator_resolution_audit_report=report,
    )


def build_dashboard_with_post_rerun_resolution_closure(
    report=None,
    audit_report=None,
    rollup_report=None,
    guidance_report=None,
):
    report = report or post_rerun_resolution_current_evidence_closure_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_reconciliation_blocker_rollup_report=rollup_report,
        upbit_paper_post_rerun_operator_reconciliation_review_guidance_report=guidance_report,
        upbit_paper_post_rerun_operator_resolution_audit_report=audit_report,
        upbit_paper_post_rerun_resolution_current_evidence_closure_report=report,
    )


def build_dashboard_with_post_rerun_current_evidence_closure_recheck(
    report=None,
    closure_report=None,
    ledger_idempotency_report=None,
    with_paper_portfolio=True,
):
    report = report or post_rerun_current_evidence_closure_recheck_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_resolution_current_evidence_closure_report=closure_report,
        upbit_paper_post_rerun_current_evidence_closure_recheck_report=report,
        upbit_paper_ledger_idempotency_runtime_evidence_report=ledger_idempotency_report,
    )


def build_dashboard_with_post_rerun_reconciliation_repair_path(
    report=None,
    closure_report=None,
    recheck_report=None,
    ledger_idempotency_report=None,
    with_paper_portfolio=True,
    paper_portfolio_snapshot=None,
):
    report = report or post_rerun_reconciliation_repair_path_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
        paper_portfolio_snapshot=paper_portfolio_snapshot,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_resolution_current_evidence_closure_report=closure_report,
        upbit_paper_post_rerun_current_evidence_closure_recheck_report=recheck_report,
        upbit_paper_post_rerun_reconciliation_repair_path_report=report,
        upbit_paper_ledger_idempotency_runtime_evidence_report=ledger_idempotency_report,
    )


def build_dashboard_with_post_repair_reconciliation(
    report=None,
    repair_path_report=None,
    with_paper_portfolio=True,
    paper_portfolio_snapshot=None,
):
    report = report or post_repair_reconciliation_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
        paper_portfolio_snapshot=paper_portfolio_snapshot,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_rerun_reconciliation_repair_path_report=repair_path_report,
        upbit_paper_post_repair_reconciliation_report=report,
    )


def build_dashboard_with_repair_operator_queue(
    report=None,
    post_repair_report=None,
    with_paper_portfolio=True,
):
    report = report or repair_operator_queue_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_repair_reconciliation_report=post_repair_report,
        upbit_paper_repair_operator_queue_report=report,
    )


def build_dashboard_with_stale_loop_post_regeneration_reconciliation(
    report=None,
    post_repair_report=None,
    with_paper_portfolio=True,
    ledger_idempotency_report=None,
    stale_loop_operator_queue_closure_report=None,
    paper_portfolio_snapshot=None,
):
    report = report or stale_loop_post_regeneration_reconciliation_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
        paper_portfolio_snapshot=paper_portfolio_snapshot,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_post_repair_reconciliation_report=post_repair_report,
        upbit_paper_stale_loop_post_regeneration_reconciliation_report=report,
        upbit_paper_stale_loop_reconciliation_operator_queue_closure_report=stale_loop_operator_queue_closure_report,
        upbit_paper_ledger_idempotency_runtime_evidence_report=ledger_idempotency_report,
    )


def build_dashboard_with_stale_loop_operator_queue_closure(
    report=None,
    post_report=None,
    ledger_idempotency_report=None,
    with_paper_portfolio=True,
):
    post_report = post_report or stale_loop_post_regeneration_reconciliation_fixture()
    ledger_idempotency_report = ledger_idempotency_report or ledger_idempotency_runtime_evidence_fixture(
        session_id=post_report["session_id"],
        evidence_id="test-dashboard-stale-loop-operator-queue-closure-ledger",
    )
    report = report or stale_loop_operator_queue_closure_fixture(post_report, ledger_idempotency_report)
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_stale_loop_post_regeneration_reconciliation_report=post_report,
        upbit_paper_stale_loop_reconciliation_operator_queue_closure_report=report,
        upbit_paper_ledger_idempotency_runtime_evidence_report=ledger_idempotency_report,
    )


def build_dashboard_with_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard(
    report=None,
    with_paper_portfolio=True,
):
    report = report or stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(
        session_id=session_id,
        with_paper_portfolio=with_paper_portfolio,
    )
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=report,
    )


def build_dashboard_with_audited_writer_precheck(report=None, source_guard_report=None):
    report = report or audited_writer_precheck_fixture(source_guard_report)
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=source_guard_report,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=report,
    )


def build_dashboard_with_audited_writer_dry_run(
    report=None,
    source_design_report=None,
    source_precheck_report=None,
    source_guard_report=None,
):
    source_guard_report = source_guard_report or stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
    source_precheck_report = source_precheck_report or audited_writer_precheck_fixture(source_guard_report)
    source_design_report = source_design_report or audited_writer_design_fixture(source_precheck_report)
    report = report or audited_writer_dry_run_fixture(source_design_report)
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=source_guard_report,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=source_precheck_report,
        upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=report,
    )


def build_dashboard_with_audited_writer_locked_output(
    report=None,
    source_dry_run_report=None,
    source_design_report=None,
    source_precheck_report=None,
    source_guard_report=None,
):
    source_guard_report = source_guard_report or stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
    source_precheck_report = source_precheck_report or audited_writer_precheck_fixture(source_guard_report)
    source_design_report = source_design_report or audited_writer_design_fixture(source_precheck_report)
    source_dry_run_report = source_dry_run_report or audited_writer_dry_run_fixture(source_design_report)
    report = report or audited_writer_locked_output_fixture(source_dry_run_report)
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=source_guard_report,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=source_precheck_report,
        upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=source_dry_run_report,
        upbit_paper_repaired_current_evidence_audited_writer_locked_output_report=report,
    )


def build_dashboard_with_audited_writer_implementation_prep(
    report=None,
    source_locked_output_report=None,
    source_dry_run_report=None,
    source_design_report=None,
    source_precheck_report=None,
    source_guard_report=None,
):
    source_guard_report = source_guard_report or stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
    source_precheck_report = source_precheck_report or audited_writer_precheck_fixture(source_guard_report)
    source_design_report = source_design_report or audited_writer_design_fixture(source_precheck_report)
    source_dry_run_report = source_dry_run_report or audited_writer_dry_run_fixture(source_design_report)
    source_locked_output_report = source_locked_output_report or audited_writer_locked_output_fixture(source_dry_run_report)
    report = report or audited_writer_implementation_prep_fixture(source_locked_output_report)
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report=source_guard_report,
        upbit_paper_repaired_current_evidence_audited_writer_precheck_report=source_precheck_report,
        upbit_paper_repaired_current_evidence_audited_writer_dry_run_report=source_dry_run_report,
        upbit_paper_repaired_current_evidence_audited_writer_locked_output_report=source_locked_output_report,
        upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report=report,
    )


def build_dashboard_with_history():
    dashboard = build_dashboard()
    dashboard["generated_at_utc"] = "2026-04-30T00:00:00Z"
    dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
    history = append_stability_history(None, dashboard)
    next_dashboard = json.loads(json.dumps(dashboard))
    next_dashboard["generated_at_utc"] = "2026-04-30T01:05:00Z"
    next_dashboard["dashboard_hash"] = dashboard_shell_hash(next_dashboard)
    history = append_stability_history(history, next_dashboard)
    summary, heartbeat, startup_probe = build_inputs()
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_read_only_dashboard",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        stability_history=history,
    )


def build_dashboard_with_sparse_day_history():
    dashboard = build_dashboard()
    dashboard["generated_at_utc"] = "2026-04-30T00:00:00Z"
    dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
    history = append_stability_history(None, dashboard)
    next_dashboard = json.loads(json.dumps(dashboard))
    next_dashboard["generated_at_utc"] = "2026-05-01T00:05:00Z"
    next_dashboard["dashboard_hash"] = dashboard_shell_hash(next_dashboard)
    history = append_stability_history(history, next_dashboard)
    summary, heartbeat, startup_probe = build_inputs()
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_read_only_dashboard",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        stability_history=history,
    )


def build_dashboard_with_short_history():
    dashboard = build_dashboard()
    dashboard["generated_at_utc"] = "2026-04-30T00:00:00Z"
    dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
    history = append_stability_history(None, dashboard)
    next_dashboard = json.loads(json.dumps(dashboard))
    next_dashboard["generated_at_utc"] = "2026-04-30T00:03:00Z"
    next_dashboard["dashboard_hash"] = dashboard_shell_hash(next_dashboard)
    history = append_stability_history(history, next_dashboard)
    summary, heartbeat, startup_probe = build_inputs()
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="test_read_only_dashboard",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        stability_history=history,
    )


def build_dashboard_with_optimizer_feedback(report=None):
    session_id = "mvp4_optimizer_feedback_fixture"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        optimizer_feedback_report=report or optimizer_feedback_fixture(),
    )


def build_dashboard_with_convergence_assessment(report=None):
    report = report or convergence_assessment_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        convergence_assessment_report=report,
    )


def build_dashboard_with_exploration_policy(report=None):
    report = report or exploration_policy_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        exploration_exploitation_policy=report,
    )


def build_dashboard_with_parameter_narrowing(report=None):
    report = report or parameter_narrowing_fixture()
    session_id = report["session_id"]
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange=report["exchange"],
        market_type=report["market_type"],
        mode=report["mode"],
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        parameter_narrowing_report=report,
    )


def shadow_runtime_writer_visibility_fixture():
    return {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "writer_status": "PASS",
        "dashboard_visibility_status": "VISIBLE_AS_STUB_ONLY",
        "artifact_truth_role": "shadow_runtime_stub_display_truth_only",
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_dashboard_with_shadow_runtime_writer(report=None):
    session_id = "test_read_only_dashboard_shadow_writer"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        shadow_runtime_writer_report=report or shadow_runtime_writer_visibility_fixture(),
    )


def build_dashboard_with_shadow_runtime_harness(report=None):
    session_id = "test_read_only_dashboard_shadow_harness"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        shadow_runtime_harness_report=report
        or build_shadow_observation_actual_runtime_harness_report(
            harness_id="test-dashboard-shadow-runtime-harness",
            runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
            monotonic_timer_started=True,
            monotonic_timer_stopped=True,
            measured_runtime_seconds_verified=True,
        ),
    )


def shadow_persistent_runtime_fixture(runtime_id="test-dashboard-shadow-persistent-runtime"):
    observations = []
    for index in range(3):
        paper_gate = build_upbit_operational_paper_cycle(
            operation_gate_id="dashboard-shadow-persistent-source",
            session_id=f"dashboard-shadow-persistent-paper-{index}",
            requested_entry=True,
        )
        observations.append(
            build_shadow_observation_report(
                observation_id=f"dashboard-shadow-persistent-observation-{index}",
                paper_operation_gate_report=paper_gate,
                shadow_session_id=f"dashboard-shadow-persistent-shadow-{index}",
                shadow_sample_count=30,
            )
        )
    stream = build_shadow_observation_stream_report(
        stream_id="dashboard-shadow-persistent-stream",
        observations=observations,
        min_required_observation_count=3,
        min_required_evidence_span_hours=24,
        evidence_span_hours=24,
    )
    scheduler = build_shadow_observation_scheduler_guard_report(
        scheduler_id="dashboard-shadow-persistent-scheduler",
        stream_report=stream,
        writer_id="dashboard-writer",
        active_writer_id="dashboard-writer",
    )
    return build_shadow_observation_persistent_runtime_report(
        runtime_id=runtime_id,
        scheduler_guard_report=scheduler,
        requested_cycle_count=3,
        completed_cycle_count=3,
        max_cycle_count=10,
    )


def build_dashboard_with_shadow_persistent_runtime(report=None):
    session_id = "test_read_only_dashboard_shadow_persistent"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        shadow_persistent_runtime_report=report or shadow_persistent_runtime_fixture(),
    )


def build_dashboard_with_shadow_runtime_orchestration(orchestration_report=None):
    session_id = "test_read_only_dashboard_shadow_runtime_orchestration"
    summary, heartbeat, startup_probe = build_inputs(session_id=session_id)
    persistent = shadow_persistent_runtime_fixture("test-dashboard-shadow-runtime-orchestration-persistent")
    harness = build_shadow_observation_actual_runtime_harness_report(
        harness_id="test-dashboard-shadow-runtime-orchestration-harness",
        runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
        monotonic_timer_started=True,
        monotonic_timer_stopped=True,
        measured_runtime_seconds_verified=True,
        source_runtime_report=persistent,
    )
    orchestration = orchestration_report or build_shadow_observation_runtime_orchestration_report(
        orchestration_id="test-dashboard-shadow-runtime-orchestration",
        persistent_runtime_report=persistent,
        actual_runtime_harness_report=harness,
    )
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        shadow_persistent_runtime_report=persistent,
        shadow_runtime_harness_report=harness,
        shadow_runtime_orchestration_report=orchestration,
    )


class ReadOnlyDashboardTest(unittest.TestCase):
    def test_dashboard_shell_is_display_only_and_live_blocked(self):
        dashboard = build_dashboard()
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        self.assertTrue(dashboard["display_only"])
        self.assertTrue(dashboard["dashboard_truth_only"])
        refresh = dashboard["dashboard_refresh_policy"]
        self.assertEqual(refresh["title"], "Dashboard Data Freshness")
        self.assertEqual(refresh["status"], "AUTO_REFRESH_ENABLED")
        self.assertEqual(refresh["source"], "heartbeat.json")
        self.assertEqual(refresh["auto_refresh_interval_seconds"], 10)
        self.assertEqual(refresh["stale_after_seconds"], 300)
        self.assertTrue(refresh["client_stale_guard_enabled"])
        self.assertEqual(refresh["refresh_mode"], "LOCAL_FILE_RELOAD")
        self.assertEqual(refresh["generated_at_utc"], dashboard["generated_at_utc"])
        self.assertTrue(refresh["display_only"])
        self.assertTrue(refresh["dashboard_truth_only"])
        self.assertFalse(refresh["live_order_ready"])
        self.assertFalse(refresh["live_order_allowed"])
        self.assertFalse(refresh["can_live_trade"])
        self.assertFalse(refresh["scale_up_allowed"])
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_binds_quantitative_policy_as_display_only_live_blocked_status(self):
        dashboard = build_dashboard()
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))

        policy = dashboard["quantitative_policy_status"]
        self.assertEqual(result.status, "PASS")
        self.assertEqual(policy["status"], "LIVE_BLOCKED")
        self.assertEqual(policy["policy_status"], "IMPLEMENTED_LIVE_BLOCKED")
        self.assertEqual(policy["decision_surface"], "DASHBOARD_ONLY")
        self.assertEqual(policy["dashboard_reason_code"], "LIVE_READY_MISSING")
        self.assertEqual(policy["minimum_trade_count"], 100)
        self.assertEqual(policy["high_return_candidate_trade_count"], 300)
        self.assertFalse(policy["live_order_ready"])
        self.assertFalse(policy["live_order_allowed"])
        self.assertFalse(policy["can_live_trade"])
        self.assertFalse(policy["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("Quantitative Strategy Review", html)
        self.assertIn("Net Edge After Cost", html)
        self.assertIn("LIVE blocked", html)
        self.assertIn("high-return=300 trades", html)

    def test_dashboard_blocks_quantitative_policy_status_live_flag_drift(self):
        dashboard = build_dashboard()
        dashboard["quantitative_policy_status"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)

        result = validate_read_only_dashboard_shell(dashboard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(dashboard["can_submit_order"])
        self.assertEqual(dashboard["final_action"], "NO_TRADE")
        self.assertEqual(dashboard["operation_status"]["status"], "RUNNING_SAFE_MODE")
        self.assertEqual(dashboard["operation_status"]["severity"], "NORMAL")
        self.assertIn(dashboard["operation_status"]["color_token"], {"green", "blue"})
        self.assertEqual(dashboard["operation_status"]["portfolio_status"], dashboard["portfolio_snapshot"]["status"])
        self.assertEqual(
            dashboard["operation_status"]["portfolio_blocking_reason"],
            dashboard["portfolio_snapshot"]["blocking_reason"],
        )
        self.assertEqual(dashboard["operation_status"]["portfolio_next_action"], dashboard["portfolio_snapshot"]["next_action"])
        self.assertIn("No recovery needed", dashboard["operation_status"]["recovery_hint"])
        self.assertEqual(dashboard["operation_status"]["launcher_execution_mode"], "SAFE_BOOT_OR_EXPLICIT_MONITOR")
        self.assertEqual(dashboard["operation_status"]["runtime_presence"], "DASHBOARD_HEARTBEAT_ONLY")
        self.assertIn("continuous PAPER engine", dashboard["operation_status"]["operator_meaning"])
        self.assertTrue(dashboard["operation_status"]["live_orders_blocked"])
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["title"], "Ledger & Reconciliation")
        self.assertEqual(reconciliation["status"], "NOT_LOADED")
        self.assertEqual(reconciliation["severity"], "WARNING")
        self.assertEqual(reconciliation["color_token"], "yellow")
        self.assertEqual(reconciliation["reconciliation_status"], "NOT_LOADED")
        self.assertEqual(reconciliation["restart_recovery_status"], "NOT_LOADED")
        self.assertEqual(reconciliation["ledger_state"], "NOT_LOADED")
        self.assertEqual(reconciliation["single_writer_state"], "NOT_LOADED")
        self.assertEqual(reconciliation["idempotency_state"], "NOT_LOADED")
        self.assertEqual(reconciliation["primary_blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertTrue(reconciliation["display_only"])
        self.assertFalse(reconciliation["live_order_ready"])
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(reconciliation["can_live_trade"])
        self.assertFalse(reconciliation["scale_up_allowed"])
        self.assertFalse(reconciliation["can_submit_order"])
        stability = dashboard["stability_trends"]
        self.assertEqual(stability["title"], "Stability Trends")
        self.assertEqual(stability["status"], "STABLE")
        self.assertEqual(stability["severity"], "NORMAL")
        self.assertIn(stability["color_token"], {"green", "blue"})
        self.assertEqual(stability["history_window"], "CURRENT_SNAPSHOT_ONLY")
        self.assertEqual({metric["metric_id"] for metric in stability["metrics"]}, {
            "heartbeat_age",
            "source_freshness",
            "resource_health",
            "runtime_artifact_pressure",
            "event_latency",
            "queue_backlog",
            "rate_limit_pressure",
        })
        self.assertTrue(stability["display_only"])
        self.assertFalse(stability["live_order_allowed"])
        self.assertFalse(stability["scale_up_allowed"])
        long_run = dashboard["long_run_operator_summary"]
        self.assertEqual(long_run["title"], "Long-Run Operation")
        self.assertEqual(long_run["status"], "RUNNING_NOW")
        self.assertEqual(long_run["severity"], "NORMAL")
        self.assertEqual(long_run["color_token"], "blue")
        self.assertEqual(long_run["history_sample_count"], 0)
        self.assertEqual(long_run["source"], "heartbeat.json")
        self.assertEqual(long_run["latency_trend_status"], "PASS")
        self.assertEqual(long_run["resource_pressure_status"], "PASS")
        self.assertEqual(long_run["dashboard_refresh_delay_status"], "PASS")
        self.assertTrue(long_run["display_only"])
        self.assertFalse(long_run["live_order_ready"])
        self.assertFalse(long_run["live_order_allowed"])
        self.assertFalse(long_run["can_live_trade"])
        self.assertFalse(long_run["scale_up_allowed"])
        market_data = dashboard["market_data_continuity_status"]
        self.assertEqual(market_data["title"], "Market Data Continuity")
        self.assertEqual(market_data["status"], "NOT_LOADED")
        self.assertEqual(market_data["severity"], "WARNING")
        self.assertEqual(market_data["color_token"], "yellow")
        self.assertEqual(market_data["source"], "NOT_LOADED")
        self.assertEqual(market_data["evidence_role"], "PAPER_DATA_CONTINUITY_HISTORY_ONLY_NOT_LIVE_READY")
        self.assertFalse(market_data["long_run_evidence_eligible"])
        self.assertFalse(market_data["promotion_eligible"])
        self.assertFalse(market_data["live_order_ready"])
        self.assertFalse(market_data["live_order_allowed"])
        self.assertFalse(market_data["can_live_trade"])
        self.assertFalse(market_data["scale_up_allowed"])
        runtime_boundary = dashboard["runtime_evidence_boundary"]
        self.assertEqual(runtime_boundary["title"], "Runtime Evidence Boundary")
        self.assertEqual(runtime_boundary["status"], "ACTUAL_LONG_RUN_COLLECTING")
        self.assertEqual(runtime_boundary["actual_long_run_evidence_status"], "COLLECTING")
        self.assertEqual(runtime_boundary["short_window_evidence_status"], "NOT_LOADED")
        self.assertEqual(runtime_boundary["stub_runtime_evidence_status"], "NOT_LOADED")
        self.assertEqual(runtime_boundary["long_run_operator_status"], long_run["status"])
        self.assertEqual(runtime_boundary["color_token"], "blue")
        self.assertFalse(runtime_boundary["live_review_evidence_eligible"])
        self.assertFalse(runtime_boundary["live_order_ready"])
        self.assertFalse(runtime_boundary["live_order_allowed"])
        self.assertFalse(runtime_boundary["can_live_trade"])
        self.assertFalse(runtime_boundary["scale_up_allowed"])
        self.assertEqual(runtime_boundary["runtime_continuity_ladder_status"], "ACTUAL_LONG_RUN_COLLECTING")
        self.assertEqual(runtime_boundary["runtime_continuity_ladder_current_step_id"], "SHORT_WINDOW_PAPER_SHADOW_CHECK")
        self.assertEqual(runtime_boundary["runtime_continuity_ladder_highest_passed_step_id"], "CURRENT_HEARTBEAT")
        self.assertEqual(runtime_boundary["runtime_continuity_ladder_blocking_count"], 3)
        self.assertFalse(runtime_boundary["runtime_continuity_ladder_live_review_allowed"])
        self.assertFalse(runtime_boundary["runtime_continuity_ladder_gap_closure_allowed"])
        ladder_steps = runtime_boundary["runtime_continuity_ladder_steps"]
        self.assertEqual([step["step_id"] for step in ladder_steps], [
            "PAPER_VALUE_SNAPSHOT",
            "CURRENT_HEARTBEAT",
            "SHORT_WINDOW_PAPER_SHADOW_CHECK",
            "BOUNDED_RUNTIME_PROFILE",
            "ACTUAL_LONG_RUN_VALIDATED",
        ])
        ladder_by_id = {step["step_id"]: step for step in ladder_steps}
        self.assertEqual(ladder_by_id["PAPER_VALUE_SNAPSHOT"]["status"], "PASS")
        self.assertEqual(ladder_by_id["CURRENT_HEARTBEAT"]["status"], "PASS")
        self.assertEqual(ladder_by_id["SHORT_WINDOW_PAPER_SHADOW_CHECK"]["status"], "MISSING")
        self.assertEqual(ladder_by_id["BOUNDED_RUNTIME_PROFILE"]["status"], "MISSING")
        self.assertEqual(ladder_by_id["ACTUAL_LONG_RUN_VALIDATED"]["status"], "COLLECTING")
        for step in ladder_steps:
            self.assertFalse(step["counts_as_live_ready_evidence"])
            self.assertFalse(step["counts_as_gap_closure_evidence"])
            self.assertFalse(step["live_order_allowed"])
            self.assertFalse(step["scale_up_allowed"])
        requirement_ids = [item["requirement_id"] for item in runtime_boundary["evidence_requirements"]]
        self.assertEqual(requirement_ids, [
            "PERSISTENT_RUNTIME_SOURCE",
            "SHORT_WINDOW_HARNESS_SOURCE",
            "RUNTIME_ORCHESTRATION_SOURCE_PAIRING",
            "ACTUAL_RUNTIME_DURATION",
            "ACTUAL_CYCLE_COUNT",
            "EVIDENCE_WINDOW_COUNT",
            "HEARTBEAT_FRESHNESS_HISTORY",
            "RECOVERY_AND_PARTIAL_WRITE_CLEAN",
        ])
        requirement_by_id = {
            item["requirement_id"]: item for item in runtime_boundary["evidence_requirements"]
        }
        self.assertEqual(requirement_by_id["PERSISTENT_RUNTIME_SOURCE"]["status"], "MISSING")
        self.assertEqual(requirement_by_id["SHORT_WINDOW_HARNESS_SOURCE"]["status"], "MISSING")
        self.assertEqual(requirement_by_id["RUNTIME_ORCHESTRATION_SOURCE_PAIRING"]["status"], "MISSING")
        self.assertEqual(requirement_by_id["ACTUAL_RUNTIME_DURATION"]["status"], "COLLECTING")
        self.assertEqual(requirement_by_id["HEARTBEAT_FRESHNESS_HISTORY"]["status"], "PASS")
        self.assertEqual(runtime_boundary["evidence_requirements_blocking_count"], 7)
        for item in runtime_boundary["evidence_requirements"]:
            self.assertTrue(item["blocking_for_live_review"])
            self.assertTrue(item["display_only"])
            self.assertTrue(item["dashboard_truth_only"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["title"], "Operator Next Action")
        self.assertEqual(operator_action["status"], "ACTION_REQUIRED")
        self.assertEqual(operator_action["severity"], "WARNING")
        self.assertEqual(operator_action["color_token"], "yellow")
        self.assertEqual(operator_action["primary_action"], "RESOLVE_BLOCKER")
        self.assertEqual(operator_action["primary_blocker_code"], dashboard["blocking_reason"])
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertTrue(operator_action["paper_review_only"])
        self.assertTrue(operator_action["live_review_blocked"])
        self.assertFalse(operator_action["dangerous_controls_present"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["title"], "Operator Workflow")
        self.assertEqual(workflow["status"], "ACTION_REQUIRED")
        self.assertEqual(workflow["current_step"], "INSPECT_DASHBOARD")
        self.assertEqual(workflow["step_count"], 4)
        self.assertEqual([step["step_id"] for step in workflow["steps"]], [
            "RUN_PAPER",
            "INSPECT_DASHBOARD",
            "COLLECT_EVIDENCE",
            "LIVE_REVIEW_BLOCKED",
        ])
        self.assertEqual(workflow["steps"][1]["status"], "CURRENT")
        self.assertEqual(workflow["steps"][2]["status"], "WAITING")
        self.assertEqual(workflow["steps"][-1]["status"], "BLOCKED")
        self.assertFalse(workflow["steps"][-1]["current"])
        self.assertTrue(workflow["live_review_blocked"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["title"], "Strategy Evidence Maturity")
        self.assertEqual(maturity["status"], "COLLECTING")
        self.assertEqual(maturity["severity"], "WARNING")
        self.assertEqual(maturity["color_token"], "yellow")
        self.assertEqual(maturity["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertFalse(maturity["scorecard_input_eligible"])
        self.assertEqual(maturity["evidence_progress_status"], "NOT_STARTED")
        self.assertEqual(maturity["evidence_progress_pct"], 0)
        self.assertEqual(maturity["maturity_gap_status"], "OPEN_HIGH")
        self.assertEqual(maturity["maturity_gap_count"], 10)
        self.assertEqual(maturity["maturity_component_count"], 10)
        self.assertEqual(maturity["paper_scorecard_component_pass_count"], 0)
        self.assertEqual(len(maturity["maturity_components"]), 10)
        self.assertTrue(all(item["live_review_blocker"] for item in maturity["maturity_components"]))
        self.assertTrue(all(item["live_order_allowed"] is False for item in maturity["maturity_components"]))
        self.assertTrue(all(item["next_required_evidence"] for item in maturity["maturity_components"]))
        self.assertIn("entry, exit, and no-trade", maturity["maturity_components"][0]["next_required_evidence"])
        self.assertIn("Live remains blocked", maturity["maturity_gap_summary"])
        self.assertEqual(maturity["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertEqual(maturity["live_readiness_status"], "NOT_LIVE_READY")
        self.assertIn("not LIVE_READY", maturity["operator_warning"])
        self.assertEqual([item["check_id"] for item in maturity["evidence_checklist"]], [
            "PAPER_SAMPLES",
            "SHADOW_SAMPLES",
            "COST_EVIDENCE",
            "ENTRY_REASON",
            "NO_TRADE_REASON",
        ])
        self.assertTrue(all(item["status"] == "MISSING" for item in maturity["evidence_checklist"]))
        self.assertTrue(maturity["display_only"])
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["scale_up_allowed"])
        self.assertEqual(maturity["rollup_source"], "NOT_LOADED")
        self.assertEqual(maturity["rollup_source_status"], "NOT_LOADED")
        self.assertEqual(maturity["rollup_required_component_count"], 10)
        convergence = dashboard["convergence_assessment_status"]
        self.assertEqual(convergence["title"], "Convergence Assessment")
        self.assertEqual(convergence["status"], "UNTESTED")
        self.assertEqual(convergence["severity"], "WARNING")
        self.assertEqual(convergence["color_token"], "yellow")
        self.assertEqual(convergence["dependency_pass_count"], 0)
        self.assertEqual(convergence["required_dependency_count"], 10)
        self.assertEqual(len(convergence["dependency_statuses"]), 10)
        self.assertTrue(all(item["status"] == "UNTESTED" for item in convergence["dependency_statuses"]))
        self.assertEqual(convergence["convergence_claim"], "NO_CLAIM")
        self.assertIn("not LIVE_READY", convergence["operator_warning"])
        self.assertIn("live orders blocked", convergence["operator_warning"])
        self.assertIn("scale-up blocked", convergence["operator_warning"])
        self.assertTrue(convergence["display_only"])
        self.assertFalse(convergence["writer_input_eligible"])
        self.assertFalse(convergence["model_promotion_allowed"])
        self.assertFalse(convergence["scale_up_recommendation_allowed"])
        self.assertFalse(convergence["live_order_ready"])
        self.assertFalse(convergence["live_order_allowed"])
        self.assertFalse(convergence["can_live_trade"])
        self.assertFalse(convergence["scale_up_allowed"])
        exploration = dashboard["exploration_policy_status"]
        self.assertEqual(exploration["title"], "Exploration / Exploitation Policy")
        self.assertEqual(exploration["status"], "UNTESTED")
        self.assertEqual(exploration["severity"], "WARNING")
        self.assertEqual(exploration["color_token"], "yellow")
        self.assertEqual(exploration["policy_status"], "UNTESTED")
        self.assertEqual(exploration["controller_state"], "BLOCKED")
        self.assertEqual(exploration["transition_decision"], "BLOCK_TRANSITION")
        self.assertEqual(exploration["recommendation_scope"], "BLOCKED")
        self.assertEqual(exploration["dependency_pass_count"], 0)
        self.assertEqual(exploration["required_dependency_count"], 6)
        self.assertEqual(len(exploration["dependency_statuses"]), 6)
        self.assertTrue(all(item["status"] == "UNTESTED" for item in exploration["dependency_statuses"]))
        self.assertFalse(exploration["exploitation_allowed_for_paper_ranking"])
        self.assertIn("not LIVE_READY", exploration["operator_warning"])
        self.assertIn("live orders blocked", exploration["operator_warning"])
        self.assertIn("scale-up blocked", exploration["operator_warning"])
        self.assertTrue(exploration["display_only"])
        self.assertFalse(exploration["live_permission_created"])
        self.assertFalse(exploration["live_config_mutation_allowed"])
        self.assertFalse(exploration["writes_live_ready_snapshot"])
        self.assertFalse(exploration["active_snapshot_mutation_allowed"])
        self.assertFalse(exploration["order_submission_allowed"])
        self.assertFalse(exploration["exchange_account_call_allowed"])
        self.assertFalse(exploration["scale_up_recommendation_allowed"])
        self.assertFalse(exploration["live_order_ready"])
        self.assertFalse(exploration["live_order_allowed"])
        self.assertFalse(exploration["can_live_trade"])
        self.assertFalse(exploration["scale_up_allowed"])
        risk = dashboard["risk_exposure_snapshot"]
        self.assertEqual(risk["title"], "Risk Exposure")
        self.assertEqual(risk["status"], "ATTENTION")
        self.assertEqual(risk["severity"], "WARNING")
        self.assertEqual(risk["color_token"], "yellow")
        self.assertEqual(risk["risk_review_scope"], "PAPER_DISPLAY_ONLY")
        self.assertEqual(risk["exposure_data_status"], "COMPLETE")
        self.assertEqual(risk["drawdown_data_status"], "VERIFIED")
        self.assertEqual(risk["scale_up_blocker_code"], "SCALE_UP_NOT_ELIGIBLE")
        self.assertEqual(risk["paper_exposure_quality_status"], "UNAVAILABLE")
        self.assertEqual(risk["paper_exposure_quality_source"], "NOT_LOADED")
        self.assertEqual(risk["paper_exposure_quality_recommendation"], "NO_SCALE_UP")
        self.assertEqual(risk["paper_exposure_quality_sample_display"], "0/0")
        self.assertIn("paper_exposure_quality_report", risk["paper_exposure_quality_next_required_evidence"])
        self.assertIn("No paper exposure quality report", risk["paper_exposure_quality_message"])
        self.assertEqual(risk["equity_display"], "1,000,000 KRW")
        self.assertEqual(risk["exposure_pct_display"], "0.00%")
        self.assertEqual(risk["drawdown_pct_display"], "0.00%")
        self.assertFalse(risk["live_order_allowed"])
        self.assertFalse(risk["scale_up_allowed"])
        feedback = dashboard["execution_feedback_snapshot"]
        self.assertEqual(feedback["title"], "Execution Feedback")
        self.assertEqual(feedback["status"], "COLLECTING")
        self.assertEqual(feedback["severity"], "WARNING")
        self.assertEqual(feedback["color_token"], "yellow")
        self.assertEqual(feedback["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertEqual(feedback["execution_quality_status"], "UNTESTED")
        self.assertEqual(feedback["risk_review_status"], "UNTESTED")
        self.assertFalse(feedback["feedback_eligible"])
        self.assertFalse(feedback["promotion_eligible"])
        self.assertTrue(feedback["display_only"])
        self.assertFalse(feedback["live_order_ready"])
        self.assertFalse(feedback["live_order_allowed"])
        self.assertFalse(feedback["can_live_trade"])
        self.assertFalse(feedback["scale_up_allowed"])
        decision = dashboard["decision_trace"]
        self.assertEqual(decision["final_action"], "NO_TRADE")
        self.assertEqual(decision["no_trade_reason"], dashboard["blocking_reason"])
        self.assertEqual(decision["entry_status"], "BLOCKED")
        self.assertFalse(decision["live_order_allowed"])
        self.assertFalse(decision["scale_up_allowed"])
        recent = dashboard["recent_events"]
        self.assertEqual(recent["title"], "Recent Activity")
        self.assertTrue(recent["display_only"])
        self.assertFalse(recent["live_order_allowed"])
        self.assertFalse(recent["scale_up_allowed"])
        self.assertTrue(any(item["event_type"] == "NO_TRADE" for item in recent["items"]))
        positions = dashboard["position_snapshot"]
        self.assertEqual(positions["status"], "NONE")
        self.assertEqual(positions["open_position_count"], 0)
        self.assertEqual(positions["empty_message"], "No open PAPER positions")
        self.assertFalse(positions["can_live_trade"])
        self.assertFalse(positions["scale_up_allowed"])
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "VERIFIED")
        self.assertEqual(portfolio["truth_role"], "dashboard_serving_truth")
        self.assertTrue(portfolio["display_only"])
        self.assertTrue(portfolio["dashboard_truth_only"])
        self.assertFalse(portfolio["live_order_ready"])
        self.assertFalse(portfolio["live_order_allowed"])
        self.assertFalse(portfolio["can_live_trade"])
        self.assertEqual(portfolio["source_snapshot_status"], "PASS")
        self.assertEqual(portfolio["source_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertEqual(len(portfolio["source_snapshot_hash"]), 64)
        self.assertIsInstance(portfolio["source_snapshot_generated_at_utc"], str)
        self.assertEqual(portfolio["configured_paper_capital"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["configured_paper_capital"]["freshness_status"], "PASS")
        self.assertEqual(portfolio["cash"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["equity"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["positions"]["value_display"], "0")
        self.assertEqual(portfolio["return_pct"]["value_display"], "0.00%")

    def test_dashboard_projects_market_data_continuity_history_as_display_only(self):
        history = build_upbit_public_rest_continuity_history_report(
            history_id="dashboard-continuity-empty",
            session_id="test_read_only_dashboard",
            continuity_attempts=[],
        )
        dashboard = build_dashboard(upbit_public_rest_continuity_history=history)
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        html = render_dashboard_html(dashboard)

        self.assertEqual(result.status, "PASS")
        market_data = dashboard["market_data_continuity_status"]
        self.assertEqual(market_data["title"], "Market Data Continuity")
        self.assertEqual(market_data["status"], "BLOCKED")
        self.assertEqual(market_data["severity"], "WARNING")
        self.assertEqual(market_data["color_token"], "yellow")
        self.assertEqual(market_data["source"], "rest_continuity_history.json")
        self.assertEqual(market_data["primary_blocker_code"], "DATA_UNAVAILABLE")
        self.assertEqual(market_data["total_attempt_count"], 0)
        self.assertFalse(market_data["long_run_evidence_eligible"])
        self.assertFalse(market_data["promotion_eligible"])
        self.assertFalse(market_data["live_order_ready"])
        self.assertFalse(market_data["live_order_allowed"])
        self.assertFalse(market_data["can_live_trade"])
        self.assertFalse(market_data["scale_up_allowed"])
        self.assertTrue(
            any(item["artifact_id"] == "MARKET_DATA_CONTINUITY_HISTORY" for item in dashboard["source_artifacts"])
        )
        self.assertIn("Market data", html)
        self.assertIn("Market Data Continuity", html)
        self.assertIn("rest_continuity_history.json", html)
        self.assertIn("PAPER data only", html)
        self.assertIn("not LIVE_READY", html)

    def test_dashboard_blocks_market_data_continuity_live_permission_mutation(self):
        history = build_upbit_public_rest_continuity_history_report(
            history_id="dashboard-continuity-live-mutation",
            session_id="test_read_only_dashboard",
            continuity_attempts=[],
        )
        history["live_order_allowed"] = True
        history["history_hash"] = upbit_public_rest_continuity_history_hash(history)
        dashboard = build_dashboard(upbit_public_rest_continuity_history=history)
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        market_data = dashboard["market_data_continuity_status"]

        self.assertEqual(result.status, "PASS")
        self.assertEqual(market_data["status"], "INVALID")
        self.assertEqual(market_data["severity"], "ERROR")
        self.assertEqual(market_data["color_token"], "red")
        self.assertEqual(market_data["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(market_data["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_projects_paper_runtime_recovery_guard_pass_display_only(self):
        dashboard = build_dashboard_with_paper_runtime_recovery_guard()
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        recovery = dashboard["paper_runtime_recovery_guard_status"]
        self.assertEqual(recovery["title"], "PAPER Runtime Recovery Guard")
        self.assertEqual(recovery["status"], "PASS")
        self.assertEqual(recovery["severity"], "NORMAL")
        self.assertEqual(recovery["color_token"], "green")
        self.assertEqual(recovery["latest_cycle_status"], "PASS")
        self.assertTrue(recovery["latest_cycle_recoverable"])
        self.assertEqual(recovery["ledger_jsonl_checked_count"], 1)
        self.assertEqual(recovery["corrupted_ledger_jsonl_quarantined_count"], 0)
        self.assertEqual(recovery["ledger_jsonl_invalid_count"], 0)
        self.assertTrue(recovery["paper_runtime_resume_allowed"])
        self.assertEqual(recovery["runtime_evidence_role"], "PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE")
        self.assertFalse(recovery["actual_long_run_evidence_created"])
        self.assertFalse(recovery["long_run_evidence_eligible"])
        self.assertEqual(recovery["long_run_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertFalse(recovery["promotion_eligible"])
        self.assertFalse(recovery["live_order_ready"])
        self.assertFalse(recovery["live_order_allowed"])
        self.assertFalse(recovery["can_live_trade"])
        self.assertFalse(recovery["scale_up_allowed"])
        self.assertTrue(any(item["artifact_id"] == "PAPER_RUNTIME_RECOVERY_GUARD" for item in dashboard["source_artifacts"]))
        html = render_dashboard_html(dashboard)
        self.assertIn("PAPER Runtime Recovery Guard", html)
        self.assertIn("ledger JSONL", html)
        self.assertIn("not LIVE_READY", html)
        self.assertIn("long-run eligible=False", html)
        self.assertIn("LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT", html)

    def test_dashboard_projects_paper_runtime_recovery_guard_partial_write_blocked(self):
        dashboard = build_dashboard_with_paper_runtime_recovery_guard(paper_runtime_recovery_guard_fixture(blocked=True))
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        recovery = dashboard["paper_runtime_recovery_guard_status"]
        self.assertEqual(recovery["status"], "BLOCKED")
        self.assertEqual(recovery["severity"], "ERROR")
        self.assertEqual(recovery["color_token"], "red")
        self.assertEqual(recovery["primary_blocker_code"], "PARTIAL_WRITE_RECOVERY_REQUIRED")
        self.assertEqual(recovery["resume_action"], "SAFE_MODE_RECONCILE")
        self.assertFalse(recovery["paper_runtime_resume_allowed"])

    def test_dashboard_blocks_paper_runtime_recovery_guard_live_permission_mutation(self):
        dashboard = build_dashboard_with_paper_runtime_recovery_guard()
        dashboard["paper_runtime_recovery_guard_status"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_paper_runtime_recovery_guard_false_long_run_eligibility(self):
        dashboard = build_dashboard_with_paper_runtime_recovery_guard()
        dashboard["paper_runtime_recovery_guard_status"]["long_run_evidence_eligible"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_projects_paper_runtime_evidence_profile_pass_display_only(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=1)
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile(report)
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))

        self.assertEqual(result.status, "PASS")
        profile = dashboard["paper_runtime_evidence_collection_profile_status"]
        self.assertEqual(profile["title"], "PAPER Runtime Evidence Profile")
        self.assertEqual(profile["status"], "PASS")
        self.assertEqual(profile["severity"], "NORMAL")
        self.assertEqual(profile["color_token"], "blue")
        self.assertEqual(profile["completed_cycle_count"], 1)
        self.assertEqual(profile["accepted_cycle_sample_count"], 1)
        self.assertEqual(profile["component_pass_count"], profile["component_count"])
        self.assertEqual(profile["component_blocked_count"], 0)
        self.assertEqual(profile["ledger_runtime_evidence_status"], "PASS")
        self.assertEqual(profile["idempotency_status"], "PASS")
        self.assertEqual(profile["reconciliation_status"], "PASS")
        self.assertEqual(profile["mismatch_count"], 0)
        self.assertEqual(profile["runtime_evidence_role"], "BOUNDED_PAPER_RUNTIME_EVIDENCE_PROFILE_NOT_LONG_RUN")
        self.assertFalse(profile["current_evidence_write_allowed"])
        self.assertFalse(profile["actual_long_run_evidence_created"])
        self.assertFalse(profile["long_run_evidence_eligible"])
        self.assertEqual(profile["long_run_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertEqual(profile["collection_depth_status"], "BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH")
        self.assertEqual(profile["collection_depth_blocker_code"], "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT")
        self.assertIn("SHADOW", profile["collection_depth_missing_runtime_modes"])
        self.assertEqual(profile["collection_depth_shadow_runtime_status"], "PRESENT_NOT_LONG_RUN")
        self.assertEqual(profile["collection_depth_pairing_status"], "PAIRED_NOT_LONG_RUN")
        self.assertGreater(profile["collection_depth_missing_span_seconds"], 0)
        self.assertGreater(profile["collection_depth_missing_cycle_count"], 0)
        self.assertEqual(profile["runtime_mode_depth_status"], "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH")
        self.assertEqual(profile["runtime_mode_depth_blocker_code"], "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
        self.assertEqual(profile["runtime_mode_depth_missing_modes"], ["PAPER", "SHADOW"])
        self.assertEqual(profile["runtime_mode_depth_missing_mode_count"], 2)
        self.assertEqual(profile["paper_mode_source_status"], "PRESENT_BOUNDED_NOT_LONG_RUN")
        self.assertEqual(profile["shadow_mode_source_status"], "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertGreater(profile["paper_mode_missing_span_seconds"], 0)
        self.assertGreater(profile["paper_mode_missing_cycle_count"], 0)
        self.assertGreater(profile["shadow_mode_missing_span_seconds"], 0)
        self.assertGreater(profile["shadow_mode_missing_cycle_count"], 0)
        self.assertFalse(profile["paper_mode_counts_as_actual_long_run_evidence"])
        self.assertFalse(profile["shadow_mode_counts_as_actual_long_run_evidence"])
        self.assertFalse(profile["bounded_profile_counts_as_long_run_evidence"])
        self.assertFalse(profile["dashboard_display_counts_as_long_run_evidence"])
        self.assertFalse(profile["promotion_eligible"])
        self.assertFalse(profile["live_order_ready"])
        self.assertFalse(profile["live_order_allowed"])
        self.assertFalse(profile["can_live_trade"])
        self.assertFalse(profile["scale_up_allowed"])
        self.assertTrue(
            any(
                item["artifact_id"] == "UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE"
                for item in dashboard["source_artifacts"]
            )
        )
        html = render_dashboard_html(dashboard)
        self.assertIn("PAPER Runtime Evidence Profile", html)
        self.assertIn("current writes=False", html)
        self.assertIn("not LIVE_READY", html)
        self.assertIn("Collection Depth", html)
        self.assertIn("missing modes=SHADOW", html)
        self.assertIn("Per-Mode Long Run", html)
        self.assertIn("missing modes=PAPER, SHADOW", html)
        self.assertIn("LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT", html)

    def test_dashboard_projects_paper_runtime_evidence_profile_duplicate_ledger_blocked(self):
        report = run_upbit_paper_runtime_evidence_collection_profile(
            requested_cycle_count=1,
            duplicate_ledger_events=True,
        )
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile(report)
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))

        self.assertEqual(result.status, "PASS")
        profile = dashboard["paper_runtime_evidence_collection_profile_status"]
        self.assertEqual(profile["status"], "BLOCKED")
        self.assertEqual(profile["severity"], "ERROR")
        self.assertEqual(profile["color_token"], "red")
        self.assertEqual(profile["primary_blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertGreater(profile["duplicate_event_id_count"], 0)
        self.assertEqual(profile["ledger_runtime_evidence_status"], "BLOCKED")
        self.assertFalse(profile["current_evidence_write_allowed"])
        self.assertFalse(profile["live_order_allowed"])

    def test_dashboard_blocks_paper_runtime_evidence_profile_live_permission_mutation(self):
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile()
        dashboard["paper_runtime_evidence_collection_profile_status"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_paper_runtime_evidence_profile_hidden_collection_depth(self):
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile()
        dashboard["paper_runtime_evidence_collection_profile_status"]["collection_depth_missing_runtime_modes"] = []
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_dashboard_blocks_paper_runtime_evidence_profile_shadow_pairing_drift(self):
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile()
        dashboard["paper_runtime_evidence_collection_profile_status"]["collection_depth_pairing_status"] = "MISSING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_dashboard_blocks_paper_runtime_evidence_profile_hidden_per_mode_depth(self):
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile()
        dashboard["paper_runtime_evidence_collection_profile_status"]["runtime_mode_depth_missing_modes"] = ["SHADOW"]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")

    def test_dashboard_blocks_paper_runtime_evidence_profile_per_mode_false_long_run_claim(self):
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile()
        dashboard["paper_runtime_evidence_collection_profile_status"]["paper_mode_counts_as_actual_long_run_evidence"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_paper_runtime_evidence_profile_false_bounded_depth_claim(self):
        dashboard = build_dashboard_with_paper_runtime_evidence_collection_profile()
        dashboard["paper_runtime_evidence_collection_profile_status"]["bounded_profile_counts_as_long_run_evidence"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_projects_profitability_maturity_rollup_without_live_permission(self):
        dashboard = build_dashboard(profitability_maturity_rollup_report=profitability_maturity_rollup_fixture())
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["evidence_source"], "profitability_evidence_maturity_rollup.json")
        self.assertEqual(maturity["rollup_source"], "profitability_evidence_maturity_rollup.json")
        self.assertEqual(maturity["rollup_source_status"], "LOADED")
        self.assertEqual(maturity["rollup_component_count"], 10)
        self.assertEqual(maturity["rollup_required_component_count"], 10)
        self.assertTrue(maturity["rollup_coverage_complete"])
        self.assertEqual(maturity["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertEqual(maturity["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertEqual(maturity["live_readiness_status"], "NOT_LIVE_READY")
        self.assertEqual(maturity["primary_blocker_code"], "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY")
        self.assertEqual(maturity["promotion_threshold_status"], "BLOCKED_FOR_THRESHOLD_EVIDENCE")
        self.assertEqual(maturity["promotion_threshold_replay_closed_trades"], 1)
        self.assertEqual(maturity["promotion_threshold_min_replay_closed_trades"], 100)
        self.assertEqual(maturity["promotion_threshold_paper_runtime_hours"], 0.1)
        self.assertEqual(maturity["promotion_threshold_min_paper_runtime_hours"], 0)
        self.assertEqual(
            maturity["promotion_threshold_paper_runtime_hours_gate_role"],
            "OBSERVED_CONTEXT_ONLY_NO_FIXED_RUNTIME_FLOOR",
        )
        self.assertEqual(maturity["promotion_threshold_high_or_critical_contract_gap_count"], 1)
        self.assertEqual(
            maturity["promotion_threshold_missing_code_count"],
            len(maturity["promotion_threshold_missing_codes"]),
        )
        self.assertNotIn("PAPER_RUNTIME_HOURS_BELOW_MIN", maturity["promotion_threshold_missing_codes"])
        self.assertIn("HIGH_OR_CRITICAL_CONTRACT_GAP_OPEN", maturity["promotion_threshold_missing_codes"])
        self.assertTrue(maturity["promotion_threshold_explicit_insufficient_sample_blocker"])
        html = render_dashboard_html(dashboard)
        self.assertIn("runtime=0.1h observed", html)
        self.assertNotIn("runtime=0.1/72h", html)
        self.assertEqual(maturity["robustness_source_type_status"], "BLOCKED_FOR_SOURCE_TYPE_EVIDENCE")
        self.assertEqual(maturity["robustness_source_type_missing_count"], 4)
        self.assertEqual(
            maturity["robustness_source_type_missing_types"],
            ["BOOTSTRAP", "CONCENTRATION", "OOS", "WALK_FORWARD"],
        )
        self.assertEqual(maturity["robustness_source_type_oos_count"], 0)
        self.assertEqual(maturity["robustness_source_type_walk_forward_count"], 0)
        self.assertEqual(maturity["robustness_source_type_bootstrap_count"], 0)
        self.assertEqual(maturity["robustness_source_type_concentration_count"], 0)
        self.assertEqual(
            maturity["robustness_source_type_primary_blocker_code"],
            "ROBUSTNESS_SOURCE_TYPE_EVIDENCE_REQUIRED",
        )
        self.assertTrue(maturity["robustness_source_type_explicit_blocker"])
        self.assertEqual(maturity["paper_scorecard_component_pass_count"], 4)
        self.assertEqual(maturity["maturity_gap_count"], 6)
        self.assertTrue(any(item["status"] == "PAPER_SCORECARD_INPUT_ONLY" for item in maturity["maturity_components"]))
        paper_shadow_component = maturity["maturity_components"][8]
        self.assertEqual(paper_shadow_component["component_id"], "paper_shadow_evidence_accumulation")
        self.assertEqual(paper_shadow_component["status"], "BLOCKED_LONG_RUN_EVIDENCE")
        self.assertTrue(paper_shadow_component["paper_scorecard_input_eligible"])
        self.assertFalse(paper_shadow_component["long_run_evidence_eligible"])
        self.assertEqual(
            paper_shadow_component["long_run_blocker_code"],
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
        )
        self.assertFalse(maturity["scorecard_input_eligible"])
        self.assertFalse(maturity["live_order_ready"])
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["can_live_trade"])
        self.assertFalse(maturity["scale_up_allowed"])

    def test_dashboard_blocks_profitability_rollup_hidden_promotion_threshold_gap(self):
        rollup = profitability_maturity_rollup_fixture()
        rollup["promotion_threshold_evidence"]["missing_threshold_codes"] = []
        dashboard = build_dashboard(profitability_maturity_rollup_report=rollup)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["rollup_source_status"], "BLOCKED")
        self.assertEqual(maturity["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["scale_up_allowed"])

    def test_dashboard_blocks_profitability_rollup_fixed_runtime_hour_floor(self):
        rollup = profitability_maturity_rollup_fixture()
        rollup["promotion_threshold_evidence"]["min_paper_runtime_hours"] = 72
        dashboard = build_dashboard(profitability_maturity_rollup_report=rollup)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["rollup_source_status"], "LOADED")
        self.assertEqual(maturity["primary_blocker_code"], "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY")
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["scale_up_allowed"])

    def test_dashboard_blocks_profitability_rollup_live_flag_drift(self):
        rollup = profitability_maturity_rollup_fixture()
        rollup["live_order_allowed"] = True
        dashboard = build_dashboard(profitability_maturity_rollup_report=rollup)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["status"], "BLOCKED")
        self.assertEqual(maturity["severity"], "ERROR")
        self.assertEqual(maturity["color_token"], "red")
        self.assertEqual(maturity["rollup_source_status"], "BLOCKED")
        self.assertEqual(maturity["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(maturity["live_order_ready"])
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["can_live_trade"])
        self.assertFalse(maturity["scale_up_allowed"])

    def test_dashboard_blocks_profitability_rollup_missing_component(self):
        rollup = profitability_maturity_rollup_fixture()
        rollup["components"] = rollup["components"][:-1]
        rollup["component_count"] = len(rollup["components"])
        rollup["coverage_complete"] = False
        dashboard = build_dashboard(profitability_maturity_rollup_report=rollup)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["rollup_source_status"], "BLOCKED")
        self.assertEqual(maturity["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(maturity["maturity_gap_count"], 10)

    def test_dashboard_blocks_profitability_rollup_hidden_robustness_source_type_gap(self):
        rollup = profitability_maturity_rollup_fixture()
        rollup["robustness_source_type_evidence"]["missing_source_types"] = []
        dashboard = build_dashboard(profitability_maturity_rollup_report=rollup)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["rollup_source_status"], "BLOCKED")
        self.assertEqual(maturity["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["scale_up_allowed"])

    def test_dashboard_projects_candidate_scorecard_as_display_only(self):
        scorecard = candidate_scorecard_fixture()
        dashboard = build_dashboard(candidate_scorecard=scorecard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["evidence_source"], "candidate_scorecard.json")
        self.assertEqual(maturity["candidate_scorecard_source"], "candidate_scorecard.json")
        self.assertEqual(maturity["candidate_scorecard_status"], "PAPER_RANKING_BLOCKED")
        self.assertEqual(maturity["candidate_scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertEqual(maturity["candidate_scorecard_objective_basis"], "NET_EV_AFTER_COST")
        self.assertEqual(maturity["candidate_scorecard_net_ev_after_cost_bps"], scorecard["net_ev_after_cost_bps"])
        self.assertEqual(maturity["candidate_scorecard_candidate_id"], scorecard["candidate_id"])
        self.assertFalse(maturity["candidate_scorecard_ranking_eligible"])
        self.assertFalse(maturity["scorecard_input_eligible"])
        self.assertFalse(maturity["live_order_allowed"])
        sources = [source for source in dashboard["source_artifacts"] if source["artifact_id"] == "CANDIDATE_SCORECARD"]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["filename"], "candidate_scorecard.json")

        html = render_dashboard_html(dashboard)
        self.assertIn("PAPER Scorecard", html)
        self.assertIn(scorecard["candidate_id"], html)
        self.assertIn("Net EV after cost", html)
        self.assertEqual(validate_dashboard_visual_layout_contract(html).status, "PASS")

    def test_dashboard_blocks_candidate_scorecard_live_flag_drift(self):
        scorecard = candidate_scorecard_fixture()
        scorecard["live_order_allowed"] = True
        dashboard = build_dashboard(candidate_scorecard=scorecard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["candidate_scorecard_status"], "BLOCKED")
        self.assertEqual(maturity["candidate_scorecard_scope"], "BLOCKED_DISPLAY_ONLY")
        self.assertEqual(maturity["candidate_scorecard_primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(maturity["candidate_scorecard_ranking_eligible"])
        self.assertFalse(maturity["live_order_allowed"])

    def test_dashboard_blocks_candidate_scorecard_cross_scope(self):
        scorecard = candidate_scorecard_fixture()
        scorecard["session_id"] = "wrong_session"
        dashboard = build_dashboard(candidate_scorecard=scorecard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["candidate_scorecard_status"], "BLOCKED")
        self.assertEqual(maturity["candidate_scorecard_primary_blocker_code"], "SNAPSHOT_SCOPE_MISMATCH")
        self.assertFalse(maturity["candidate_scorecard_ranking_eligible"])

    def test_dashboard_blocks_live_permission_mutation(self):
        dashboard = build_dashboard()
        dashboard["live_order_ready"] = True
        dashboard["live_order_allowed"] = True
        dashboard["can_submit_order"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_order_action(self):
        dashboard = build_dashboard()
        dashboard["final_action"] = "ENTER_LONG"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_execution_truth_source(self):
        dashboard = build_dashboard()
        dashboard["source_artifacts"][0]["truth_role"] = "ledger"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_refresh_policy_live_permission(self):
        dashboard = build_dashboard()
        dashboard["dashboard_refresh_policy"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_missing_client_stale_guard(self):
        dashboard = build_dashboard()
        dashboard["dashboard_refresh_policy"]["client_stale_guard_enabled"] = False
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LATENCY_TTL_EXPIRED")

    def test_dashboard_projects_reconciliation_recovery_pass_as_display_only(self):
        dashboard = build_dashboard_with_reconciliation()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "PASS")
        self.assertEqual(reconciliation["severity"], "NORMAL")
        self.assertEqual(reconciliation["color_token"], "green")
        self.assertEqual(reconciliation["reconciliation_status"], "PASS")
        self.assertEqual(reconciliation["restart_recovery_status"], "PASS")
        self.assertEqual(reconciliation["ledger_state"], "PAPER_LEDGER_MATCHED")
        self.assertEqual(reconciliation["single_writer_state"], "RECOVERED")
        self.assertEqual(reconciliation["idempotency_state"], "RECOVERED")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_READY_MISSING")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(reconciliation["can_submit_order"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Ledger &amp; Reconciliation", html)
        self.assertIn("reconciliation-green", html)
        self.assertIn("PAPER_LEDGER_MATCHED", html)
        self.assertIn("single-writer=RECOVERED", html)
        self.assertIn("Display-only ledger safety", html)

    def test_dashboard_projects_ledger_idempotency_runtime_evidence(self):
        dashboard = build_dashboard_with_ledger_idempotency_runtime_evidence()
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["ledger_idempotency_runtime_evidence_status"], "PASS")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_validation_status"], "PASS")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_reconciliation_status"], "PASS")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_portfolio_provenance_status"], "PASS")
        self.assertGreater(reconciliation["ledger_idempotency_runtime_source_ledger_jsonl_count"], 0)
        self.assertGreater(reconciliation["ledger_idempotency_runtime_recomputed_ledger_event_count"], 0)
        self.assertEqual(reconciliation["ledger_idempotency_runtime_duplicate_event_id_count"], 0)
        self.assertEqual(reconciliation["ledger_idempotency_runtime_duplicate_dedup_key_count"], 0)
        self.assertEqual(reconciliation["ledger_idempotency_runtime_duplicate_semantic_event_count"], 0)
        self.assertEqual(reconciliation["ledger_idempotency_runtime_duplicate_filled_order_key_count"], 0)
        self.assertEqual(reconciliation["ledger_idempotency_runtime_source_count_mismatch_count"], 0)
        self.assertFalse(reconciliation["live_order_allowed"])
        source = {
            item["artifact_id"]: item for item in dashboard["source_artifacts"]
        }["PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE"]
        self.assertEqual(source["filename"], "upbit_paper_ledger_idempotency_runtime_evidence_report.json")
        self.assertEqual(source["freshness_status"], "PASS")
        html = render_dashboard_html(dashboard)
        self.assertIn("Current Ledger Evidence", html)
        self.assertIn("ledger-files=", html)
        self.assertIn("count-mismatch=0", html)

    def test_dashboard_blocks_ledger_idempotency_runtime_evidence_live_mutation(self):
        report = ledger_idempotency_runtime_evidence_fixture(
            session_id="mvp1_upbit_paper_launcher",
            evidence_id="test-dashboard-ledger-idempotency-live-mutation",
        )
        report["live_order_allowed"] = True
        report["evidence_hash"] = upbit_paper_ledger_idempotency_runtime_evidence_hash(report)
        dashboard = build_dashboard_with_ledger_idempotency_runtime_evidence(report)
        result = validate_read_only_dashboard_shell(dashboard, set(registry()["enums"]["live_blocker_code"]["values"]))
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["ledger_idempotency_runtime_evidence_status"], "BLOCKED")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_blocks_reconciliation_mismatch_display(self):
        session_id = "test_read_only_dashboard_reconciliation"
        report = build_reconciliation_report(
            reconciliation_id="test-dashboard-reconciliation-mismatch",
            session_id=session_id,
            exchange_snapshot={
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "session_id": session_id,
                "balances": {"KRW": "1000000"},
                "positions": [],
                "open_orders": [],
            },
            internal_state={
                "exchange": "UPBIT",
                "market_type": "KRW_SPOT",
                "mode": "PAPER",
                "session_id": session_id,
                "balances": {"KRW": "900000"},
                "positions": [],
                "open_orders": [],
            },
        )
        dashboard = build_dashboard_with_reconciliation(reconciliation_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["severity"], "ERROR")
        self.assertEqual(reconciliation["color_token"], "red")
        self.assertEqual(reconciliation["reconciliation_status"], "MISMATCH")
        self.assertEqual(reconciliation["mismatch_count"], 1)
        self.assertEqual(reconciliation["primary_blocker_code"], "RECONCILIATION_REQUIRED")
        self.assertFalse(reconciliation["live_order_allowed"])

    def test_dashboard_projects_post_rerun_blocker_rollup_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_blocker_rollup()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["severity"], "ERROR")
        self.assertEqual(reconciliation["color_token"], "red")
        self.assertEqual(reconciliation["source"], "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json")
        self.assertEqual(reconciliation["post_rerun_blocker_rollup_status"], "BLOCKED")
        self.assertEqual(reconciliation["post_rerun_blocker_rollup_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_blocker_rollup_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_primary_blocker_item_count"], 8)
        self.assertGreaterEqual(reconciliation["post_rerun_unique_blocker_count"], 1)
        self.assertEqual(reconciliation["post_rerun_current_evidence_write_authorized_count"], 0)
        self.assertEqual(reconciliation["post_rerun_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["post_rerun_candidate_current_evidence_usable_count"], 0)
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", reconciliation["post_rerun_blocker_codes"])
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["severity"], "ERROR")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Post-Rerun Blockers", html)
        self.assertIn("rollup=BLOCKED", html)
        self.assertIn("current-writes=0", html)

    def test_dashboard_projects_post_rerun_review_guidance_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_review_guidance()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["severity"], "ERROR")
        self.assertEqual(reconciliation["color_token"], "red")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
        )
        self.assertEqual(
            reconciliation["post_rerun_review_guidance_status"],
            "BLOCKED_RECONCILIATION_REVIEW_REQUIRED",
        )
        self.assertEqual(reconciliation["post_rerun_review_guidance_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_review_guidance_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_review_step_count"], 4)
        self.assertEqual(reconciliation["post_rerun_forbidden_output_count"], 6)
        self.assertEqual(reconciliation["post_rerun_guidance_current_evidence_write_authorized_count"], 0)
        self.assertEqual(reconciliation["post_rerun_guidance_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["post_rerun_guidance_candidate_current_evidence_usable_count"], 0)
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", reconciliation["post_rerun_blocker_codes"])
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["severity"], "ERROR")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("guidance=BLOCKED_RECONCILIATION_REVIEW_REQUIRED", html)
        self.assertIn("steps=4", html)
        self.assertIn("forbidden=6", html)
        self.assertIn("guidance-writes=0", html)

    def test_dashboard_prefers_review_guidance_source_when_rollup_and_guidance_loaded(self):
        dashboard = build_dashboard_with_post_rerun_review_guidance(
            rollup_report=post_rerun_blocker_rollup_fixture()
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json",
        )
        self.assertEqual(reconciliation["post_rerun_blocker_rollup_status"], "BLOCKED")
        self.assertEqual(
            reconciliation["post_rerun_review_guidance_status"],
            "BLOCKED_RECONCILIATION_REVIEW_REQUIRED",
        )

    def test_dashboard_projects_post_rerun_operator_reconciliation_queue_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_operator_reconciliation_queue(
            rollup_report=post_rerun_blocker_rollup_fixture(),
            guidance_report=post_rerun_review_guidance_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertEqual(dashboard["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
        )
        self.assertEqual(reconciliation["post_rerun_operator_reconciliation_queue_status"], "BLOCKED")
        self.assertEqual(reconciliation["post_rerun_operator_reconciliation_queue_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_operator_queue_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_operator_queue_required_count"], 8)
        self.assertEqual(reconciliation["post_rerun_operator_queue_review_ready_reconciliation_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_operator_queue_blocked_pre_review_item_count"], 0)
        self.assertEqual(reconciliation["post_rerun_operator_queue_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["post_rerun_operator_queue_candidate_current_evidence_usable_count"], 0)
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", reconciliation["post_rerun_operator_queue_blocker_codes"])
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", reconciliation["post_rerun_blocker_codes"])
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "POST_RERUN_OPERATOR_RECONCILIATION_QUEUE"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_post_rerun_operator_reconciliation_queue_report.json",
        )
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("post-rerun operator queue has 8 reconciliation item", portfolio["source_snapshot_freshness_message"])
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Post-Rerun Operator Queue", html)
        self.assertIn("queue=BLOCKED", html)
        self.assertIn("review-ready=8", html)
        self.assertIn("queue-writes=0", html)
        self.assertIn("queue-usable=0", html)

    def test_dashboard_blocks_post_rerun_operator_queue_live_or_current_evidence_drift(self):
        report = post_rerun_operator_reconciliation_queue_fixture()
        report["candidate_current_evidence_usable_count"] = 1
        report["live_order_allowed"] = True
        report["queue_hash"] = upbit_paper_post_rerun_operator_reconciliation_queue_hash(report)
        dashboard = build_dashboard_with_post_rerun_operator_reconciliation_queue(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["post_rerun_operator_reconciliation_queue_status"], "INVALID")
        self.assertEqual(reconciliation["post_rerun_operator_reconciliation_queue_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_projects_post_rerun_resolution_audit_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_resolution_audit()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["severity"], "ERROR")
        self.assertEqual(reconciliation["color_token"], "red")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_post_rerun_operator_resolution_audit_report.json",
        )
        self.assertEqual(
            reconciliation["post_rerun_resolution_audit_status"],
            "UNRESOLVED_RECONCILIATION_REVIEW_ONLY",
        )
        self.assertEqual(reconciliation["post_rerun_resolution_audit_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_resolution_unresolved_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_resolution_resolved_item_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_control_count"], 4)
        self.assertEqual(reconciliation["post_rerun_resolution_controls_satisfied_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_current_evidence_write_authorized_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_source_review_guidance_file_load_status"], "PASS")
        self.assertTrue(reconciliation["post_rerun_resolution_source_review_guidance_file_hash_match"])
        self.assertEqual(reconciliation["post_rerun_resolution_source_decision_audit_file_load_status"], "PASS")
        self.assertTrue(reconciliation["post_rerun_resolution_source_decision_audit_file_hash_match"])
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", reconciliation["post_rerun_blocker_codes"])
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["severity"], "ERROR")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Post-Rerun Resolution", html)
        self.assertIn("resolution=UNRESOLVED_RECONCILIATION_REVIEW_ONLY", html)
        self.assertIn("unresolved=8", html)
        self.assertIn("resolved=0", html)
        self.assertIn("controls=4", html)
        self.assertIn("satisfied=0", html)
        self.assertIn("resolution-writes=0", html)
        self.assertIn("source-bindings=PASS/PASS", html)

    def test_dashboard_prefers_resolution_audit_source_when_all_post_rerun_sources_loaded(self):
        dashboard = build_dashboard_with_post_rerun_resolution_audit(
            rollup_report=post_rerun_blocker_rollup_fixture(),
            guidance_report=post_rerun_review_guidance_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_post_rerun_operator_resolution_audit_report.json",
        )
        self.assertEqual(reconciliation["post_rerun_blocker_rollup_status"], "BLOCKED")
        self.assertEqual(
            reconciliation["post_rerun_review_guidance_status"],
            "BLOCKED_RECONCILIATION_REVIEW_REQUIRED",
        )
        self.assertEqual(
            reconciliation["post_rerun_resolution_audit_status"],
            "UNRESOLVED_RECONCILIATION_REVIEW_ONLY",
        )

    def test_dashboard_projects_post_rerun_resolution_closure_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_resolution_closure(
            audit_report=post_rerun_resolution_audit_fixture(),
            rollup_report=post_rerun_blocker_rollup_fixture(),
            guidance_report=post_rerun_review_guidance_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["severity"], "ERROR")
        self.assertEqual(reconciliation["color_token"], "red")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
        )
        self.assertEqual(
            reconciliation["post_rerun_resolution_closure_status"],
            "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED",
        )
        self.assertEqual(reconciliation["post_rerun_resolution_closure_validation_status"], "PASS")
        self.assertEqual(
            reconciliation["post_rerun_resolution_closure_source_resolution_audit_file_load_status"],
            "PASS",
        )
        self.assertTrue(reconciliation["post_rerun_resolution_closure_source_resolution_audit_file_hash_match"])
        self.assertEqual(reconciliation["post_rerun_resolution_closure_source_unresolved_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_source_resolved_item_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_closed_item_count"], 8)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_current_evidence_closed_count"], 8)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_controls_satisfied_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_current_evidence_write_authorized_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["post_rerun_resolution_closure_candidate_current_evidence_usable_count"], 0)
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", reconciliation["post_rerun_blocker_codes"])
        self.assertIn(
            "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
            reconciliation["post_rerun_blocker_codes"],
        )
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_post_rerun_resolution_current_evidence_closure_report.json",
        )
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Post-Rerun Closure", html)
        self.assertIn("closure=CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED", html)
        self.assertIn("closed=8", html)
        self.assertIn("evidence-closed=8", html)
        self.assertIn("closure-writes=0", html)
        self.assertIn("closure-source=PASS", html)

    def test_dashboard_blocks_post_rerun_resolution_closure_current_evidence_drift(self):
        dashboard = build_dashboard_with_post_rerun_resolution_closure(
            audit_report=post_rerun_resolution_audit_fixture(),
        )
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["post_rerun_resolution_closure_current_evidence_write_allowed_count"] = 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_post_rerun_resolution_closure_source_binding_drift(self):
        dashboard = build_dashboard_with_post_rerun_resolution_closure(
            audit_report=post_rerun_resolution_audit_fixture(),
        )
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["post_rerun_resolution_closure_source_resolution_audit_file_hash_match"] = False
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_projects_post_rerun_closure_recheck_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_current_evidence_closure_recheck(
            closure_report=post_rerun_resolution_current_evidence_closure_fixture(),
            ledger_idempotency_report=ledger_idempotency_runtime_evidence_fixture(
                session_id="mvp1_upbit_paper_launcher",
                evidence_id="test-dashboard-post-rerun-closure-recheck-ledger",
            ),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["source"], "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json")
        self.assertEqual(
            reconciliation["post_rerun_current_evidence_closure_recheck_status"],
            "BLOCKED_POST_RERUN_CLOSURE_CONFIRMED",
        )
        self.assertEqual(reconciliation["post_rerun_current_evidence_closure_recheck_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_current_evidence_bridge_status"], "BLOCKED_BY_POST_RERUN_CLOSURE")
        self.assertEqual(
            reconciliation["post_rerun_current_evidence_portfolio_recheck_status"],
            "LEDGER_PROVENANCE_PASS_BUT_OPERATOR_CURRENT_EVIDENCE_BLOCKED",
        )
        self.assertEqual(
            reconciliation["post_rerun_current_evidence_closure_recheck_source_closure_file_load_status"],
            "PASS",
        )
        self.assertEqual(
            reconciliation["post_rerun_current_evidence_closure_recheck_source_ledger_file_load_status"],
            "PASS",
        )
        self.assertTrue(reconciliation["post_rerun_current_evidence_closure_recheck_source_closure_file_hash_match"])
        self.assertTrue(reconciliation["post_rerun_current_evidence_closure_recheck_source_ledger_file_hash_match"])
        self.assertEqual(reconciliation["post_rerun_current_evidence_closure_recheck_ledger_runtime_evidence_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_current_evidence_closure_recheck_ledger_reconciliation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_current_evidence_closure_recheck_ledger_idempotency_status"], "PASS")
        self.assertEqual(
            reconciliation["post_rerun_current_evidence_closure_recheck_ledger_portfolio_provenance_status"],
            "PASS",
        )
        self.assertFalse(reconciliation["post_rerun_current_evidence_closure_recheck_current_evidence_write_allowed"])
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "POST_RERUN_CURRENT_EVIDENCE_CLOSURE_RECHECK"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_post_rerun_current_evidence_closure_recheck_report.json",
        )
        html = render_dashboard_html(dashboard)
        self.assertIn("Closure Recheck", html)
        self.assertIn("bridge=BLOCKED_BY_POST_RERUN_CLOSURE", html)
        self.assertIn("recheck-writes=False", html)

    def test_dashboard_explains_unverified_portfolio_when_recheck_blocks_current_evidence(self):
        dashboard = build_dashboard_with_post_rerun_current_evidence_closure_recheck(
            closure_report=post_rerun_resolution_current_evidence_closure_fixture(),
            ledger_idempotency_report=ledger_idempotency_runtime_evidence_fixture(
                session_id="mvp1_upbit_paper_launcher",
                evidence_id="test-dashboard-post-rerun-closure-recheck-ledger-unverified-portfolio",
            ),
            with_paper_portfolio=False,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("ledger provenance recheck is PASS", portfolio["source_snapshot_freshness_message"])
        self.assertIn("current evidence remains blocked", portfolio["source_snapshot_freshness_message"])
        self.assertIn("portfolio recheck status", portfolio["cash"]["detail"])
        self.assertIn("Resolve post-rerun reconciliation", portfolio["next_action"])
        self.assertEqual(dashboard["operation_status"]["portfolio_status"], "UNVERIFIED")
        self.assertEqual(
            dashboard["operation_status"]["portfolio_blocking_reason"],
            "POST_RERUN_RECONCILIATION_REQUIRED",
        )

    def test_dashboard_blocks_post_rerun_closure_recheck_live_or_write_drift(self):
        report = post_rerun_current_evidence_closure_recheck_fixture()
        report["current_evidence_write_allowed"] = True
        report["live_order_allowed"] = True
        report["recheck_hash"] = upbit_paper_post_rerun_current_evidence_closure_recheck_hash(report)
        dashboard = build_dashboard_with_post_rerun_current_evidence_closure_recheck(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["post_rerun_current_evidence_closure_recheck_status"], "INVALID")
        self.assertEqual(reconciliation["post_rerun_current_evidence_closure_recheck_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_projects_post_rerun_reconciliation_repair_path_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_rerun_reconciliation_repair_path(
            closure_report=post_rerun_resolution_current_evidence_closure_fixture(),
            recheck_report=post_rerun_current_evidence_closure_recheck_fixture(),
            ledger_idempotency_report=ledger_idempotency_runtime_evidence_fixture(
                session_id="mvp1_upbit_paper_launcher",
                evidence_id="test-dashboard-post-rerun-repair-path-ledger",
            ),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["source"], "upbit_paper_post_rerun_reconciliation_repair_path_report.json")
        self.assertEqual(
            reconciliation["post_rerun_reconciliation_repair_path_status"],
            "BLOCKED_REPAIR_PATH_DECLARED",
        )
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_repair_gate_count"], 4)
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_satisfied_gate_count"], 0)
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_blocked_gate_count"], 4)
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(
            reconciliation["post_rerun_reconciliation_repair_path_first_gate_id"],
            "VALIDATED_OPERATOR_RESOLUTION_ACCEPTANCE",
        )
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_first_gate_status"], "BLOCKED")
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_source_closure_file_load_status"], "PASS")
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_source_recheck_file_load_status"], "PASS")
        self.assertTrue(reconciliation["post_rerun_reconciliation_repair_path_source_closure_file_hash_match"])
        self.assertTrue(reconciliation["post_rerun_reconciliation_repair_path_source_recheck_file_hash_match"])
        self.assertEqual(
            reconciliation[
                "post_rerun_reconciliation_repair_path_source_recheck_persistent_loop_validation_status"
            ],
            "PASS",
        )
        self.assertEqual(
            reconciliation["post_rerun_reconciliation_repair_path_source_recheck_persistent_loop_hash_self_check"],
            "PASS",
        )
        self.assertTrue(
            reconciliation["post_rerun_reconciliation_repair_path_source_recheck_head_cycle_in_persistent_loop"]
        )
        self.assertEqual(
            reconciliation["post_rerun_reconciliation_repair_path_source_recheck_runtime_input_role"],
            "PUBLIC_MARKET_DATA_COLLECTION",
        )
        self.assertTrue(
            reconciliation[
                "post_rerun_reconciliation_repair_path_source_recheck_runtime_public_data_hash_match"
            ]
        )
        self.assertGreaterEqual(
            reconciliation["post_rerun_reconciliation_repair_path_source_recheck_canonical_event_count"],
            5,
        )
        self.assertEqual(
            reconciliation["post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_status"],
            "PASS",
        )
        self.assertEqual(
            reconciliation["post_rerun_reconciliation_repair_path_source_recheck_runtime_depth_mismatch_count"],
            0,
        )
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "POST_RERUN_RECONCILIATION_REPAIR_PATH"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_post_rerun_reconciliation_repair_path_report.json",
        )
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("repair gates are 0/4 satisfied", portfolio["source_snapshot_freshness_message"])
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["workflow_step"], "INSPECT_DASHBOARD")
        self.assertEqual(operator_action["primary_action_label"], "Inspect post-rerun repair path")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertIn("post-rerun repair path has 0/4 satisfied repair gates", operator_action["one_line_blocker"])
        self.assertIn("runtime-depth=PASS", operator_action["one_line_blocker"])
        self.assertIn("current-evidence writes=0", operator_action["one_line_blocker"])
        self.assertIn("operator resolution acceptance", operator_action["next_operator_action"])
        self.assertIn("current-evidence rebuild", operator_action["next_operator_action"])
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertEqual(workflow["current_step"], "INSPECT_DASHBOARD")
        self.assertIn("Post-rerun repair path is blocked", workflow["summary"])
        self.assertIn("current evidence and portfolio truth writes remain blocked", workflow["summary"])
        self.assertEqual(workflow["steps"][1]["status"], "CURRENT")
        self.assertIn("runtime-depth support is visible", workflow["steps"][1]["detail"])
        self.assertIn("no repair gate has authorized current evidence", workflow["steps"][1]["detail"])
        self.assertEqual(workflow["steps"][2]["status"], "WAITING")
        self.assertIn("operator resolution and current-ledger rebuild evidence", workflow["steps"][2]["detail"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Repair Path", html)
        self.assertIn("Inspect post-rerun repair path", html)
        self.assertIn("repair=BLOCKED_REPAIR_PATH_DECLARED", html)
        self.assertIn("gates=0/4", html)
        self.assertIn("repair-runtime-depth=PASS", html)
        self.assertIn("repair-runtime-mismatch=0", html)
        self.assertIn("current-evidence writes=0", html)
        self.assertIn("repair-writes=0", html)

    def test_dashboard_keeps_post_rerun_repair_path_portfolio_unverified_when_ledger_evidence_is_bound(self):
        report = post_rerun_reconciliation_repair_path_fixture()
        ledger_report = ledger_idempotency_runtime_evidence_fixture(
            session_id=report["session_id"],
            evidence_id="test-dashboard-post-rerun-repair-path-bound-ledger",
        )
        paper_portfolio = build_initial_paper_portfolio_snapshot(
            exchange=report["exchange"],
            market_type=report["market_type"],
            session_id=report["session_id"],
            source_runtime_cycle_id=ledger_report["portfolio_source_runtime_cycle_id"],
            source_paper_ledger_head_hash=ledger_report["portfolio_source_paper_ledger_head_hash"],
        )

        dashboard = build_dashboard_with_post_rerun_reconciliation_repair_path(
            report=report,
            closure_report=post_rerun_resolution_current_evidence_closure_fixture(),
            recheck_report=post_rerun_current_evidence_closure_recheck_fixture(),
            ledger_idempotency_report=ledger_report,
            paper_portfolio_snapshot=paper_portfolio,
        )

        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertIsNone(portfolio["source_runtime_cycle_id"])
        self.assertIsNone(portfolio["source_paper_ledger_head_hash"])
        self.assertEqual(portfolio["cash"]["value_display"], "UNVERIFIED")
        self.assertEqual(portfolio["equity"]["value_display"], "UNVERIFIED")
        self.assertIn("repair gates are 0/4 satisfied", portfolio["source_snapshot_freshness_message"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_post_rerun_reconciliation_repair_path_live_or_write_drift(self):
        report = post_rerun_reconciliation_repair_path_fixture()
        report["current_evidence_write_allowed_count"] = 1
        report["live_order_allowed"] = True
        report["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(report)
        dashboard = build_dashboard_with_post_rerun_reconciliation_repair_path(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_status"], "INVALID")
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_blocks_post_rerun_reconciliation_repair_path_runtime_depth_drift(self):
        report = post_rerun_reconciliation_repair_path_fixture()
        report["source_recheck_ledger_source_runtime_depth_status"] = "BLOCKED"
        report["source_recheck_ledger_source_runtime_depth_mismatch_count"] = 1
        report["repair_path_hash"] = upbit_paper_post_rerun_reconciliation_repair_path_hash(report)
        dashboard = build_dashboard_with_post_rerun_reconciliation_repair_path(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_status"], "INVALID")
        self.assertEqual(reconciliation["post_rerun_reconciliation_repair_path_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(
            reconciliation["primary_blocker_code"],
            "POST_RERUN_RECONCILIATION_REPAIR_PATH_SOURCE_BINDING_REQUIRED",
        )
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_blocks_post_rerun_reconciliation_repair_path_operator_action_drift(self):
        dashboard = build_dashboard_with_post_rerun_reconciliation_repair_path(
            closure_report=post_rerun_resolution_current_evidence_closure_fixture(),
            recheck_report=post_rerun_current_evidence_closure_recheck_fixture(),
            ledger_idempotency_report=ledger_idempotency_runtime_evidence_fixture(
                session_id="mvp1_upbit_paper_launcher",
                evidence_id="test-dashboard-post-rerun-repair-path-operator-drift-ledger",
            ),
        )
        dashboard["operator_action_summary"]["primary_action_label"] = "Stop review and inspect the blocker"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_projects_post_repair_reconciliation_for_operator_visibility(self):
        dashboard = build_dashboard_with_post_repair_reconciliation(
            repair_path_report=post_rerun_reconciliation_repair_path_fixture()
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["source"], "upbit_paper_post_repair_reconciliation_report.json")
        self.assertEqual(reconciliation["primary_blocker_code"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertEqual(reconciliation["post_repair_reconciliation_status"], "BLOCKED")
        self.assertEqual(reconciliation["post_repair_reconciliation_validation_status"], "PASS")
        self.assertEqual(reconciliation["post_repair_repair_candidate_count"], 1)
        self.assertEqual(reconciliation["post_repair_reconciliation_item_count"], 1)
        self.assertEqual(reconciliation["post_repair_candidate_rollup_pass_count"], 1)
        self.assertEqual(reconciliation["post_repair_source_loop_expected_rollup_hash_mismatch_count"], 1)
        self.assertEqual(reconciliation["post_repair_hash_reconciliation_operator_action_required_count"], 1)
        self.assertEqual(reconciliation["post_repair_candidate_current_evidence_usable_count"], 0)
        self.assertEqual(reconciliation["post_repair_candidate_current_evidence_blocked_count"], 1)
        self.assertIn("POST_REPAIR_RECONCILIATION_REQUIRED", reconciliation["post_repair_blocker_codes"])
        self.assertIn(
            "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
            reconciliation["post_repair_blocker_codes"],
        )
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "POST_REPAIR_RECONCILIATION"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(sources[0]["filename"], "upbit_paper_post_repair_reconciliation_report.json")
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("post-repair reconciliation keeps 1 repair candidate", portfolio["source_snapshot_freshness_message"])
        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["workflow_step"], "INSPECT_DASHBOARD")
        self.assertEqual(operator_action["primary_action_label"], "Inspect post-repair reconciliation")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertIn("post-repair reconciliation has 1 operator action item(s)", operator_action["one_line_blocker"])
        self.assertIn("hash-mismatch=1", operator_action["one_line_blocker"])
        self.assertIn("current-evidence usable=0", operator_action["one_line_blocker"])
        self.assertIn("hash mismatch", operator_action["next_operator_action"])
        self.assertIn("explicit operator reconciliation", operator_action["next_operator_action"])
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])
        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertEqual(workflow["current_step"], "INSPECT_DASHBOARD")
        self.assertIn("Post-repair reconciliation is blocked", workflow["summary"])
        self.assertIn("current evidence and portfolio truth writes remain blocked", workflow["summary"])
        self.assertEqual(workflow["steps"][1]["status"], "CURRENT")
        self.assertIn("repaired candidates remain blocked by hash mismatch", workflow["steps"][1]["detail"])
        self.assertIn("cannot become current evidence", workflow["steps"][1]["detail"])
        self.assertEqual(workflow["steps"][2]["status"], "WAITING")
        self.assertIn("operator hash reconciliation evidence", workflow["steps"][2]["detail"])
        self.assertIn("portfolio truth write", workflow["steps"][2]["detail"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Post Repair", html)
        self.assertIn("Inspect post-repair reconciliation", html)
        self.assertIn("post-repair=BLOCKED", html)
        self.assertIn("hash-mismatch=1", html)
        self.assertIn("usable=0", html)

    def test_dashboard_keeps_post_repair_portfolio_unverified_when_ledger_evidence_is_bound(self):
        report = post_repair_reconciliation_fixture()
        ledger_report = ledger_idempotency_runtime_evidence_fixture(
            session_id=report["session_id"],
            evidence_id="test-dashboard-post-repair-bound-ledger",
        )
        paper_portfolio = build_initial_paper_portfolio_snapshot(
            exchange=report["exchange"],
            market_type=report["market_type"],
            session_id=report["session_id"],
            source_runtime_cycle_id=ledger_report["portfolio_source_runtime_cycle_id"],
            source_paper_ledger_head_hash=ledger_report["portfolio_source_paper_ledger_head_hash"],
        )

        dashboard = build_dashboard_with_post_repair_reconciliation(
            report=report,
            repair_path_report=post_rerun_reconciliation_repair_path_fixture(),
            paper_portfolio_snapshot=paper_portfolio,
        )

        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "POST_REPAIR_RECONCILIATION_REQUIRED")
        self.assertIsNone(portfolio["source_runtime_cycle_id"])
        self.assertIsNone(portfolio["source_paper_ledger_head_hash"])
        self.assertEqual(portfolio["cash"]["value_display"], "UNVERIFIED")
        self.assertEqual(portfolio["equity"]["value_display"], "UNVERIFIED")
        self.assertIn("post-repair reconciliation keeps 1 repair candidate", portfolio["source_snapshot_freshness_message"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_post_repair_reconciliation_operator_action_drift(self):
        dashboard = build_dashboard_with_post_repair_reconciliation(
            repair_path_report=post_rerun_reconciliation_repair_path_fixture()
        )
        dashboard["operator_action_summary"]["primary_action_label"] = "Stop review and inspect the blocker"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_post_repair_reconciliation_live_or_current_evidence_drift(self):
        report = post_repair_reconciliation_fixture()
        report["items"][0]["candidate_current_evidence_usable"] = True
        report["candidate_current_evidence_usable_count"] = 1
        report["candidate_current_evidence_blocked_count"] = 0
        report["live_order_allowed"] = True
        report["post_repair_reconciliation_hash"] = upbit_paper_post_repair_reconciliation_hash(report)
        dashboard = build_dashboard_with_post_repair_reconciliation(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["post_repair_reconciliation_status"], "INVALID")
        self.assertEqual(reconciliation["post_repair_reconciliation_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_projects_repair_operator_queue_for_operator_visibility(self):
        dashboard = build_dashboard_with_repair_operator_queue(
            post_repair_report=post_repair_reconciliation_fixture()
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["source"], "upbit_paper_repair_operator_queue_report.json")
        self.assertEqual(
            reconciliation["primary_blocker_code"],
            "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
        )
        self.assertEqual(reconciliation["repair_operator_queue_status"], "BLOCKED")
        self.assertEqual(reconciliation["repair_operator_queue_validation_status"], "PASS")
        self.assertEqual(reconciliation["repair_operator_queue_item_count"], 6)
        self.assertEqual(reconciliation["repair_operator_queue_ledger_candidate_review_ready_count"], 1)
        self.assertEqual(reconciliation["repair_operator_queue_runtime_cycle_rerun_required_count"], 5)
        self.assertEqual(reconciliation["repair_operator_queue_recovery_guard_rerun_required_count"], 1)
        self.assertEqual(reconciliation["repair_operator_queue_hash_operator_reconciliation_required_count"], 1)
        self.assertEqual(reconciliation["repair_operator_queue_candidate_current_evidence_usable_count"], 0)
        self.assertIn(
            "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
            reconciliation["repair_operator_queue_blocker_codes"],
        )
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "REPAIR_OPERATOR_QUEUE"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(sources[0]["filename"], "upbit_paper_repair_operator_queue_report.json")
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(
            portfolio["blocking_reason"],
            "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
        )
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("repair operator queue has 6 blocked repair item", portfolio["source_snapshot_freshness_message"])
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Repair Operator Queue", html)
        self.assertIn("ledger-ready=1", html)
        self.assertIn("cycle-rerun=5", html)
        self.assertIn("hash-operator=1", html)
        self.assertIn("queue-usable=0", html)

    def test_dashboard_blocks_repair_operator_queue_live_or_current_evidence_drift(self):
        report = repair_operator_queue_fixture()
        report["candidate_current_evidence_usable_count"] = 1
        report["live_order_allowed"] = True
        report["queue_hash"] = upbit_paper_repair_operator_queue_hash(report)
        dashboard = build_dashboard_with_repair_operator_queue(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["repair_operator_queue_status"], "INVALID")
        self.assertEqual(reconciliation["repair_operator_queue_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_projects_stale_loop_post_regeneration_reconciliation_for_operator_visibility(self):
        dashboard = build_dashboard_with_stale_loop_post_regeneration_reconciliation(
            post_repair_report=post_repair_reconciliation_fixture()
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["source"], "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json")
        self.assertEqual(
            reconciliation["primary_blocker_code"],
            "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
        )
        self.assertEqual(reconciliation["stale_loop_post_regeneration_reconciliation_status"], "BLOCKED")
        self.assertEqual(reconciliation["stale_loop_post_regeneration_reconciliation_validation_status"], "PASS")
        self.assertEqual(reconciliation["stale_loop_post_regeneration_item_count"], 16)
        self.assertEqual(reconciliation["stale_loop_post_regeneration_planned_item_count"], 16)
        self.assertEqual(reconciliation["stale_loop_post_regeneration_accepted_count"], 10)
        self.assertEqual(reconciliation["stale_loop_post_regeneration_blocked_reconciliation_count"], 6)
        self.assertEqual(reconciliation["stale_loop_post_regeneration_invalid_count"], 0)
        self.assertEqual(reconciliation["stale_loop_post_regeneration_current_evidence_usable_count"], 10)
        self.assertEqual(reconciliation["stale_loop_post_regeneration_excluded_from_current_evidence_count"], 6)
        self.assertIn(
            "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
            reconciliation["stale_loop_post_regeneration_blocker_codes"],
        )
        reason_counts = {
            item["reason_code"]: item["count"]
            for item in reconciliation["stale_loop_post_regeneration_blocked_repair_reason_counts"]
        }
        self.assertEqual(reason_counts["LEDGER_ROLLUP_BLOCKED"], 6)
        self.assertEqual(reason_counts["LEDGER_ROLLUP_RECONCILIATION_REQUIRED"], 6)
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "STALE_LOOP_POST_REGENERATION_RECONCILIATION"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json",
        )
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("accepted 10 current-schema artifact", portfolio["source_snapshot_freshness_message"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Stale Loop Post Regeneration", html)
        self.assertIn("post-regeneration=BLOCKED", html)
        self.assertIn("accepted=10", html)
        self.assertIn("blocked=6", html)
        self.assertIn("ledger-blocked=6", html)
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_projects_stale_loop_operator_queue_closure_for_operator_visibility(self):
        dashboard = build_dashboard_with_stale_loop_operator_queue_closure()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["primary_blocker_code"],
            "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
        )
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_status"], "BLOCKED")
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_validation_status"], "PASS")
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_item_count"], 6)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_source_blocked_item_count"], 6)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_ledger_recheck_ready_count"], 5)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_recovery_guard_required_count"], 1)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_runtime_cycle_rerun_required_count"], 0)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_operator_review_required_count"], 0)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_current_evidence_write_allowed_count"], 0)
        self.assertEqual(reconciliation["stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count"], 0)
        self.assertIn(
            "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
            reconciliation["stale_loop_operator_queue_closure_blocker_codes"],
        )
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "STALE_LOOP_OPERATOR_QUEUE_CLOSURE"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json",
        )
        html = render_dashboard_html(dashboard)
        self.assertIn("Stale Loop Operator Queue Closure", html)
        self.assertIn("ledger-ready=5", html)
        self.assertIn("recovery=1", html)
        self.assertIn("writes=0", html)
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_stale_loop_operator_queue_closure_evidence_write_drift(self):
        dashboard = build_dashboard_with_stale_loop_operator_queue_closure()
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["stale_loop_operator_queue_closure_current_evidence_write_allowed_count"] = 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_projects_repaired_current_evidence_guard_for_operator_visibility(self):
        dashboard = build_dashboard_with_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json",
        )
        self.assertEqual(reconciliation["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_status"],
            "BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED",
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_validation_status"],
            "PASS",
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_candidate_count"],
            3,
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_review_ready_count"],
            3,
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_blocked_count"],
            3,
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_clean_candidate_count"],
            3,
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_duplicate_total_count"],
            0,
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_ledger_jsonl_count"],
            6,
        )
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_ledger_event_count"],
            36,
        )
        self.assertEqual(
            reconciliation[
                "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_current_evidence_write_allowed_count"
            ],
            0,
        )
        self.assertEqual(
            reconciliation[
                "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_candidate_current_evidence_usable_count"
            ],
            0,
        )
        self.assertEqual(
            reconciliation[
                "stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_portfolio_truth_write_allowed_count"
            ],
            0,
        )
        self.assertIn(
            "ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_CURRENT_WRITES_BLOCKED",
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_blocker_codes"],
        )
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json",
        )
        self.assertEqual(sources[0]["freshness_status"], "PASS")

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(
            portfolio["blocking_reason"],
            "ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD_CURRENT_WRITES_BLOCKED",
        )
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("clean review-only evidence", portfolio["source_snapshot_freshness_message"])

        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["workflow_step"], "INSPECT_DASHBOARD")
        self.assertEqual(operator_action["primary_action_label"], "Inspect repaired current-evidence blocker")
        self.assertEqual(operator_action["primary_blocker_code"], "POST_RERUN_RECONCILIATION_REQUIRED")
        self.assertIn(
            "isolated event-id repaired candidates are review-only",
            operator_action["one_line_blocker"],
        )
        self.assertIn("current-evidence writes=0", operator_action["one_line_blocker"])
        self.assertIn("Current evidence writes", operator_action["next_operator_action"])
        self.assertIn("remain blocked", operator_action["next_operator_action"])
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])

        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertEqual(workflow["current_step"], "INSPECT_DASHBOARD")
        self.assertIn("current evidence and portfolio truth writes remain blocked", workflow["summary"])
        self.assertIn("configured PAPER capital is not verified cash or equity", workflow["steps"][1]["detail"])
        self.assertEqual(workflow["steps"][1]["status"], "CURRENT")
        self.assertIn("Keep repaired candidates review-only", workflow["steps"][2]["detail"])
        self.assertEqual(workflow["steps"][2]["status"], "WAITING")
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("Inspect repaired current-evidence blocker", html)
        self.assertIn("current-evidence writes=0", html)
        self.assertIn("Current evidence writes", html)
        self.assertIn("remain blocked", html)
        self.assertIn("Repaired Current Evidence Guard", html)
        self.assertIn("guard=BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED", html)
        self.assertIn("candidates=3/3", html)
        self.assertIn("ledger=6/36", html)
        self.assertIn("writes=0", html)
        self.assertIn("portfolio-writes=0", html)
        self.assertFalse(reconciliation["live_order_ready"])
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_repaired_current_evidence_guard_write_drift(self):
        report = stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
        report["current_evidence_write_allowed_count"] = 1
        report["event_id_scope_repaired_current_evidence_guard_hash"] = (
            upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_hash(report)
        )
        dashboard = build_dashboard_with_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard(report)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(
            reconciliation["stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_status"],
            "INVALID",
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_repaired_current_evidence_guard_operator_action_drift(self):
        dashboard = build_dashboard_with_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard()
        dashboard["operator_action_summary"]["one_line_blocker"] = (
            "POST_RERUN_RECONCILIATION_REQUIRED: live orders remain blocked."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_repaired_current_evidence_guard_operator_workflow_drift(self):
        dashboard = build_dashboard_with_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard()
        dashboard["operator_workflow_summary"]["summary"] = (
            "Operator flow is blocked until the red dashboard issue is inspected."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_projects_audited_writer_precheck_for_operator_visibility(self):
        source_guard = stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_fixture()
        precheck = audited_writer_precheck_fixture(source_guard)
        dashboard = build_dashboard_with_audited_writer_precheck(precheck, source_guard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json",
        )
        self.assertEqual(reconciliation["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_status"],
            "BLOCKED_AUDITED_WRITER_DISABLED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_validation_status"],
            "PASS",
        )
        self.assertEqual(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_gate_count"], 7)
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_gate_pass_count"],
            6,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_gate_blocked_count"],
            1,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_candidate_ready_count"],
            3,
        )
        self.assertTrue(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_audit_inputs_clean"])
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_passed"])
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_enabled"])
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_current_evidence_write_allowed"]
        )
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_portfolio_truth_write_allowed"]
        )
        self.assertIn(
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_blocker_codes"],
        )
        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json",
        )
        self.assertEqual(sources[0]["freshness_status"], "PASS")

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("audited writer precheck", portfolio["source_snapshot_freshness_message"])

        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["workflow_step"], "INSPECT_DASHBOARD")
        self.assertEqual(operator_action["primary_action_label"], "Inspect audited writer precheck")
        self.assertEqual(operator_action["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertIn("audited current-evidence writer is not implemented", operator_action["one_line_blocker"])
        self.assertIn("portfolio truth writes=0", operator_action["one_line_blocker"])
        self.assertIn("audited writer", operator_action["next_operator_action"].lower())
        self.assertFalse(operator_action["safe_to_continue_paper"])
        self.assertFalse(operator_action["live_order_allowed"])
        self.assertFalse(operator_action["scale_up_allowed"])

        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertEqual(workflow["current_step"], "INSPECT_DASHBOARD")
        self.assertIn("Audited current-evidence writer is not implemented", workflow["summary"])
        self.assertIn("configured PAPER capital is not verified cash or equity", workflow["steps"][1]["detail"])
        self.assertIn("separate audited writer", workflow["steps"][2]["detail"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("Inspect audited writer precheck", html)
        self.assertIn("Audited Current Evidence Writer Precheck", html)
        self.assertIn("precheck=BLOCKED_AUDITED_WRITER_DISABLED", html)
        self.assertIn("gates=6/7", html)
        self.assertIn("blocked-gates=1", html)
        self.assertIn("candidate-ready=3", html)
        self.assertIn("writer-enabled=False", html)
        self.assertIn("current-writes=False", html)
        self.assertIn("portfolio-writes=False", html)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_precheck_drift(self):
        precheck = audited_writer_precheck_fixture()
        precheck["audited_writer_enabled"] = True
        precheck["audited_writer_precheck_hash"] = upbit_paper_repaired_current_evidence_audited_writer_precheck_hash(
            precheck
        )
        dashboard = build_dashboard_with_audited_writer_precheck(precheck)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_precheck_status"],
            "INVALID",
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_precheck_operator_action_drift(self):
        dashboard = build_dashboard_with_audited_writer_precheck()
        dashboard["operator_action_summary"]["primary_action_label"] = "Inspect repaired current-evidence blocker"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_audited_writer_precheck_operator_workflow_drift(self):
        dashboard = build_dashboard_with_audited_writer_precheck()
        dashboard["operator_workflow_summary"]["summary"] = (
            "Repaired isolated event-id candidates are review-only; current evidence and portfolio truth writes remain blocked."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_projects_audited_writer_dry_run_for_operator_visibility(self):
        dry_run = audited_writer_dry_run_fixture()
        dashboard = build_dashboard_with_audited_writer_dry_run(dry_run)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.json",
        )
        self.assertEqual(reconciliation["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_status"],
            "BLOCKED_DRY_RUN_ONLY_WRITER_NOT_ENABLED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_validation_status"],
            "PASS",
        )
        self.assertEqual(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_check_count"], 10)
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_check_pass_count"],
            9,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_check_blocked_count"],
            1,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_configured_initial_cash_krw"],
            1000000,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_configured_initial_cash_source"],
            "PAPER_CONFIG_ONLY_UNVERIFIED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_cash_status"],
            "UNVERIFIED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_portfolio_source_status"],
            "UNVERIFIED_UNTIL_AUDITED_WRITER",
        )
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_passed"])
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_writer_enabled"])
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_current_evidence_write_allowed"]
        )
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_current_evidence_artifact_written"]
        )
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_portfolio_truth_write_allowed"]
        )
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_portfolio_truth_artifact_written"]
        )
        self.assertIn(
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_blocker_codes"],
        )

        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_DRY_RUN"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_repaired_current_evidence_audited_writer_dry_run_report.json",
        )
        self.assertEqual(sources[0]["freshness_status"], "PASS")

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("audited writer dry-run", portfolio["source_snapshot_freshness_message"])

        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["primary_action_label"], "Inspect audited writer dry-run")
        self.assertIn("audited current-evidence writer dry-run is review-only", operator_action["one_line_blocker"])
        self.assertIn("portfolio truth writes=0", operator_action["one_line_blocker"])
        self.assertIn("dry-run", operator_action["next_operator_action"].lower())
        self.assertFalse(operator_action["safe_to_continue_paper"])

        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertIn("Audited current-evidence writer dry-run is review-only", workflow["summary"])
        self.assertIn("configured PAPER capital is config-only", workflow["steps"][1]["detail"])
        self.assertIn("dry-run previews display-only", workflow["steps"][2]["detail"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("Inspect audited writer dry-run", html)
        self.assertIn("Audited Current Evidence Writer Dry-Run", html)
        self.assertIn("dry-run=BLOCKED_DRY_RUN_ONLY_WRITER_NOT_ENABLED", html)
        self.assertIn("checks=9/10", html)
        self.assertIn("configured-cash=1000000", html)
        self.assertIn("cash=UNVERIFIED", html)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_dry_run_drift(self):
        dry_run = audited_writer_dry_run_fixture()
        dry_run["current_evidence_artifact_written"] = True
        dry_run["audited_writer_dry_run_hash"] = upbit_paper_repaired_current_evidence_audited_writer_dry_run_hash(
            dry_run
        )
        dashboard = build_dashboard_with_audited_writer_dry_run(dry_run)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_dry_run_status"],
            "INVALID",
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_dry_run_operator_action_drift(self):
        dashboard = build_dashboard_with_audited_writer_dry_run()
        dashboard["operator_action_summary"]["primary_action_label"] = "Inspect audited writer precheck"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_audited_writer_dry_run_operator_workflow_drift(self):
        dashboard = build_dashboard_with_audited_writer_dry_run()
        dashboard["operator_workflow_summary"]["summary"] = (
            "Audited current-evidence writer is not implemented; current evidence and portfolio truth writes remain blocked."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_projects_audited_writer_locked_output_for_operator_visibility(self):
        locked_output = audited_writer_locked_output_fixture()
        dashboard = build_dashboard_with_audited_writer_locked_output(locked_output)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_repaired_current_evidence_audited_writer_locked_output_report.json",
        )
        self.assertEqual(reconciliation["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_status"],
            "BLOCKED_LOCKED_OUTPUT_WRITER_NOT_ENABLED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_validation_status"],
            "PASS",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_control_count"],
            12,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_control_pass_count"],
            11,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_control_blocked_count"],
            1,
        )
        self.assertEqual(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_locked_output_configured_initial_cash_krw"
            ],
            1000000,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_cash_status"],
            "UNVERIFIED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_lock_path"],
            "paper_runtime/locks/audited_current_evidence_writer.lock",
        )
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_passed"])
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_writer_enabled"])
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_lock_acquired"])
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_lock_file_written"]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_locked_output_current_evidence_write_allowed"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_locked_output_current_evidence_artifact_written"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_locked_output_portfolio_truth_write_allowed"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_locked_output_portfolio_truth_artifact_written"
            ]
        )
        self.assertIn(
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_blocker_codes"],
        )

        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_LOCKED_OUTPUT"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_repaired_current_evidence_audited_writer_locked_output_report.json",
        )
        self.assertEqual(sources[0]["freshness_status"], "PASS")

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("locked-output", portfolio["source_snapshot_freshness_message"])

        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["primary_action_label"], "Inspect audited writer locked output")
        self.assertIn("audited current-evidence writer locked output is review-only", operator_action["one_line_blocker"])
        self.assertIn("portfolio truth writes=0", operator_action["one_line_blocker"])
        self.assertIn("lock writes=0", operator_action["one_line_blocker"])
        self.assertIn("locked output", operator_action["next_operator_action"].lower())
        self.assertFalse(operator_action["safe_to_continue_paper"])

        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertIn("Audited current-evidence writer locked output is review-only", workflow["summary"])
        self.assertIn("target paths are fixed", workflow["steps"][1]["detail"])
        self.assertIn("locked-output controls display-only", workflow["steps"][2]["detail"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("Inspect audited writer locked output", html)
        self.assertIn("Audited Current Evidence Writer Locked Output", html)
        self.assertIn("locked-output=BLOCKED_LOCKED_OUTPUT_WRITER_NOT_ENABLED", html)
        self.assertIn("controls=11/12", html)
        self.assertIn("blocked-controls=1", html)
        self.assertIn("configured-cash=1000000", html)
        self.assertIn("cash=UNVERIFIED", html)
        self.assertIn("lock-acquired=False", html)
        self.assertIn("lock-written=False", html)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_locked_output_drift(self):
        locked_output = audited_writer_locked_output_fixture()
        locked_output["lock_acquired"] = True
        locked_output["audited_writer_locked_output_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_locked_output_hash(locked_output)
        )
        dashboard = build_dashboard_with_audited_writer_locked_output(locked_output)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_locked_output_status"],
            "INVALID",
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_locked_output_operator_action_drift(self):
        dashboard = build_dashboard_with_audited_writer_locked_output()
        dashboard["operator_action_summary"]["primary_action_label"] = "Inspect audited writer dry-run"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_audited_writer_locked_output_operator_workflow_drift(self):
        dashboard = build_dashboard_with_audited_writer_locked_output()
        dashboard["operator_workflow_summary"]["summary"] = (
            "Audited current-evidence writer dry-run is review-only; current evidence and portfolio truth writes remain blocked."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_projects_audited_writer_implementation_prep_for_operator_visibility(self):
        implementation_prep = audited_writer_implementation_prep_fixture()
        dashboard = build_dashboard_with_audited_writer_implementation_prep(implementation_prep)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(
            reconciliation["source"],
            "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json",
        )
        self.assertEqual(reconciliation["primary_blocker_code"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_status"],
            "BLOCKED_IMPLEMENTATION_PREP_WRITER_NOT_ENABLED",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_validation_status"],
            "PASS",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_check_count"],
            11,
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_check_pass_count"],
            10,
        )
        self.assertEqual(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_check_blocked_count"
            ],
            1,
        )
        self.assertTrue(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_inputs_clean"]
        )
        self.assertEqual(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_target_state_count"
            ],
            3,
        )
        self.assertEqual(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_target_state_hash"
            ],
            implementation_prep["target_state_hash"],
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_manifest_status"],
            "PREPARED_NOT_WRITTEN",
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_manifest_hash"],
            implementation_prep["pre_write_idempotency_manifest"]["manifest_hash"],
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_lock_path"],
            "paper_runtime/locks/audited_current_evidence_writer.lock",
        )
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_passed"])
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_writer_enabled"]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_writer_implementation_allowed"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_lock_acquire_attempted"
            ]
        )
        self.assertFalse(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_lock_acquired"])
        self.assertFalse(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_lock_file_written"]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_current_evidence_write_allowed"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_current_evidence_artifact_written"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_idempotency_manifest_write_allowed"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_idempotency_manifest_written"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_portfolio_truth_write_allowed"
            ]
        )
        self.assertFalse(
            reconciliation[
                "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_portfolio_truth_artifact_written"
            ]
        )
        self.assertIn(
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_blocker_codes"],
        )

        sources = [
            source
            for source in dashboard["source_artifacts"]
            if source["artifact_id"] == "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP"
        ]
        self.assertEqual(len(sources), 1)
        self.assertEqual(
            sources[0]["filename"],
            "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json",
        )
        self.assertEqual(sources[0]["freshness_status"], "PASS")

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED")
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", portfolio["source_snapshot_freshness_message"])
        self.assertIn("implementation prep", portfolio["source_snapshot_freshness_message"])

        operator_action = dashboard["operator_action_summary"]
        self.assertEqual(operator_action["status"], "BLOCKED")
        self.assertEqual(operator_action["primary_action"], "STOP_AND_INSPECT")
        self.assertEqual(operator_action["primary_action_label"], "Inspect audited writer implementation prep")
        self.assertIn(
            "audited current-evidence writer implementation prep is review-only",
            operator_action["one_line_blocker"],
        )
        self.assertIn("portfolio truth writes=0", operator_action["one_line_blocker"])
        self.assertIn("idempotency manifest writes=0", operator_action["one_line_blocker"])
        self.assertIn("lock writes=0", operator_action["one_line_blocker"])
        self.assertIn("implementation prep", operator_action["next_operator_action"].lower())
        self.assertFalse(operator_action["safe_to_continue_paper"])

        workflow = dashboard["operator_workflow_summary"]
        self.assertEqual(workflow["status"], "BLOCKED")
        self.assertIn("Audited current-evidence writer implementation prep is review-only", workflow["summary"])
        self.assertIn("target paths and idempotency manifest are previewed", workflow["steps"][1]["detail"])
        self.assertIn("implementation-prep controls display-only", workflow["steps"][2]["detail"])
        self.assertFalse(workflow["live_order_allowed"])
        self.assertFalse(workflow["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("Inspect audited writer implementation prep", html)
        self.assertIn("Audited Current Evidence Writer Implementation Prep", html)
        self.assertIn("implementation-prep=BLOCKED_IMPLEMENTATION_PREP_WRITER_NOT_ENABLED", html)
        self.assertIn("checks=10/11", html)
        self.assertIn("blocked-checks=1", html)
        self.assertIn("targets=3", html)
        self.assertIn("manifest=PREPARED_NOT_WRITTEN", html)
        self.assertIn("lock-acquire-attempted=False", html)
        self.assertIn("idempotency-manifest-written=False", html)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_implementation_prep_drift(self):
        implementation_prep = audited_writer_implementation_prep_fixture()
        implementation_prep["lock_acquire_attempted"] = True
        implementation_prep["audited_writer_implementation_prep_hash"] = (
            upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_hash(implementation_prep)
        )
        dashboard = build_dashboard_with_audited_writer_implementation_prep(implementation_prep)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_status"],
            "INVALID",
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_implementation_prep_operator_action_drift(self):
        dashboard = build_dashboard_with_audited_writer_implementation_prep()
        dashboard["operator_action_summary"]["primary_action_label"] = "Inspect audited writer locked output"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_audited_writer_implementation_prep_operator_workflow_drift(self):
        dashboard = build_dashboard_with_audited_writer_implementation_prep()
        dashboard["operator_workflow_summary"]["summary"] = (
            "Audited current-evidence writer locked output is review-only; current evidence, portfolio truth, and lock writes remain blocked."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_projects_audited_current_evidence_writer_portfolio_truth(self):
        outputs = audited_writer_output_fixture()
        _writer_report, current_evidence, _paper_portfolio, _implementation_prep = outputs
        dashboard = build_dashboard_with_audited_current_evidence_writer(outputs)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "VERIFIED")
        self.assertEqual(portfolio["source"], "audited_current_evidence_snapshot.json")
        self.assertEqual(portfolio["source_snapshot_status"], "PASS")
        self.assertEqual(portfolio["source_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertEqual(portfolio["paper_value_truth_status"], "PAPER_LEDGER_CURRENT_VALUES_VERIFIED")
        self.assertEqual(portfolio["runtime_continuity_status"], "SNAPSHOT_ONLY_NOT_LONG_RUN_PROOF")
        self.assertEqual(
            portfolio["audited_writer_lifecycle_status"],
            "AUDITED_SNAPSHOT_WRITTEN_CONTINUOUS_WRITER_BLOCKED",
        )
        self.assertIn("display only", portfolio["paper_value_truth_message"])
        self.assertIn("continuous current-evidence writer", portfolio["operator_truth_summary"])
        self.assertEqual(portfolio["audited_writer_readiness_ladder_status"], "BLOCKED_CONTINUOUS_WRITER")
        self.assertEqual(
            portfolio["audited_writer_readiness_ladder_highest_passed_step_id"],
            "SINGLE_RUN_AUDITED_SNAPSHOT",
        )
        self.assertEqual(
            portfolio["audited_writer_readiness_ladder_current_step_id"],
            "CONTINUOUS_CURRENT_EVIDENCE_WRITER",
        )
        self.assertEqual(portfolio["audited_writer_readiness_ladder_blocking_count"], 1)
        self.assertFalse(portfolio["audited_writer_readiness_ladder_current_evidence_write_allowed"])
        self.assertFalse(portfolio["audited_writer_readiness_ladder_portfolio_truth_write_allowed"])
        self.assertFalse(portfolio["audited_writer_readiness_ladder_live_order_allowed"])
        self.assertFalse(portfolio["audited_writer_readiness_ladder_gap_closure_allowed"])
        self.assertEqual(
            portfolio["audited_writer_activation_preflight_status"],
            "SNAPSHOT_ONLY_SOURCE_CHAIN_PARTIAL",
        )
        self.assertEqual(
            portfolio["audited_writer_activation_preflight_current_stage_id"],
            "PRECHECK_REPORT",
        )
        self.assertEqual(portfolio["audited_writer_activation_preflight_loaded_stage_count"], 3)
        self.assertEqual(portfolio["audited_writer_activation_preflight_pass_review_count"], 1)
        self.assertEqual(portfolio["audited_writer_activation_preflight_pass_snapshot_count"], 1)
        self.assertEqual(portfolio["audited_writer_activation_preflight_blocking_count"], 4)
        self.assertEqual(
            portfolio["audited_writer_activation_preflight_primary_blocker_code"],
            "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
        )
        self.assertFalse(portfolio["audited_writer_activation_preflight_writer_enablement_allowed"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_current_evidence_write_allowed"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_portfolio_truth_write_allowed"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_live_review_allowed"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_gap_closure_allowed"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_live_order_allowed"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_can_live_trade"])
        self.assertFalse(portfolio["audited_writer_activation_preflight_scale_up_allowed"])
        self.assertEqual(
            [step["step_id"] for step in portfolio["audited_writer_readiness_ladder_steps"]],
            [
                "SOURCE_GUARD_CLEAN",
                "WRITER_PRECHECK_REVIEW_ONLY",
                "WRITER_DRY_RUN_REVIEW_ONLY",
                "LOCKED_OUTPUT_REVIEW_ONLY",
                "IMPLEMENTATION_PREP_REVIEW_ONLY",
                "SINGLE_RUN_AUDITED_SNAPSHOT",
                "CONTINUOUS_CURRENT_EVIDENCE_WRITER",
            ],
        )
        self.assertEqual(portfolio["audited_writer_readiness_ladder_steps"][-1]["status"], "BLOCKED")
        self.assertEqual(
            [stage["stage_id"] for stage in portfolio["audited_writer_activation_preflight_stages"]],
            [
                "PRECHECK_REPORT",
                "DRY_RUN_REPORT",
                "LOCKED_OUTPUT_REPORT",
                "IMPLEMENTATION_PREP_REPORT",
                "SINGLE_RUN_AUDITED_WRITER_OUTPUT",
                "CONTINUOUS_WRITER_LOOP",
            ],
        )
        self.assertEqual(
            [stage["status"] for stage in portfolio["audited_writer_activation_preflight_stages"]],
            [
                "NOT_LOADED",
                "NOT_LOADED",
                "NOT_LOADED",
                "PASS_REVIEW_ONLY",
                "PASS_SNAPSHOT_ONLY",
                "BLOCKED",
            ],
        )
        for stage in portfolio["audited_writer_activation_preflight_stages"]:
            self.assertFalse(stage["current_evidence_write_allowed"])
            self.assertFalse(stage["portfolio_truth_write_allowed"])
            self.assertFalse(stage["writer_enablement_allowed"])
            self.assertFalse(stage["counts_as_live_ready_evidence"])
            self.assertFalse(stage["counts_as_gap_closure_evidence"])
            self.assertFalse(stage["live_order_ready"])
            self.assertFalse(stage["live_order_allowed"])
            self.assertFalse(stage["can_live_trade"])
            self.assertFalse(stage["scale_up_allowed"])
            self.assertFalse(stage["gap_closure_allowed"])
            self.assertTrue(stage["display_only"])
            self.assertTrue(stage["dashboard_truth_only"])
        self.assertEqual(portfolio["configured_paper_capital"]["value_display"], "1,000,000 KRW")
        expected_cash_display = krw_display(current_evidence["verified_cash_krw"])
        expected_equity_display = krw_display(current_evidence["verified_equity_krw"])
        expected_total_pnl_display = krw_display(current_evidence["verified_total_pnl_krw"])
        self.assertEqual(portfolio["cash"]["value_display"], expected_cash_display)
        self.assertEqual(portfolio["equity"]["value_display"], expected_equity_display)
        self.assertEqual(portfolio["total_pnl"]["value_display"], expected_total_pnl_display)
        self.assertEqual(portfolio["positions"]["value_display"], "1")
        self.assertEqual(portfolio["blocking_reason"], "LIVE_READY_MISSING")

        positions = dashboard["position_snapshot"]
        self.assertEqual(positions["source"], "paper_portfolio_snapshot.json")
        self.assertEqual(positions["status"], "OPEN")
        self.assertEqual(positions["open_position_count"], 1)

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertIn(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_status"],
            {AUDITED_WRITER_WRITTEN_STATUS, AUDITED_WRITER_IDEMPOTENT_STATUS},
        )
        self.assertEqual(
            reconciliation["upbit_paper_repaired_current_evidence_audited_writer_validation_status"],
            "PASS",
        )
        self.assertTrue(reconciliation["upbit_paper_repaired_current_evidence_audited_writer_verified_for_display"])
        self.assertFalse(reconciliation["live_order_ready"])
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(reconciliation["can_live_trade"])
        self.assertFalse(reconciliation["scale_up_allowed"])

        source_status = {
            source["artifact_id"]: source["freshness_status"]
            for source in dashboard["source_artifacts"]
            if source["artifact_id"]
            in {
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT",
            }
        }
        self.assertEqual(
            source_status,
            {
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER": "PASS",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT": "PASS",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT": "PASS",
            },
        )

        html = render_dashboard_html(dashboard)
        self.assertIn("Audited Current Evidence Writer", html)
        self.assertIn("writer=PASS_AUDITED_CURRENT_EVIDENCE_WRITTEN", html)
        self.assertIn(expected_cash_display, html)
        self.assertIn(expected_equity_display, html)
        self.assertIn("PAPER_LEDGER_CURRENT_VALUES_VERIFIED", html)
        self.assertIn("SNAPSHOT_ONLY_NOT_LONG_RUN_PROOF", html)
        self.assertIn("AUDITED_SNAPSHOT_WRITTEN_CONTINUOUS_WRITER_BLOCKED", html)
        self.assertIn("Audited writer ladder", html)
        self.assertIn("Continuous current-evidence writer", html)
        self.assertIn("Activation preflight", html)
        self.assertIn("Continuous writer loop", html)
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_projects_full_audited_writer_activation_chain_as_snapshot_only_blocked(self):
        dashboard = build_dashboard_with_full_audited_writer_activation_chain()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "VERIFIED")
        self.assertEqual(
            portfolio["audited_writer_activation_preflight_status"],
            "SNAPSHOT_ONLY_CONTINUOUS_WRITER_BLOCKED",
        )
        self.assertEqual(
            portfolio["audited_writer_activation_preflight_current_stage_id"],
            "CONTINUOUS_WRITER_LOOP",
        )
        self.assertEqual(portfolio["audited_writer_activation_preflight_loaded_stage_count"], 6)
        self.assertEqual(portfolio["audited_writer_activation_preflight_pass_review_count"], 4)
        self.assertEqual(portfolio["audited_writer_activation_preflight_pass_snapshot_count"], 1)
        self.assertEqual(portfolio["audited_writer_activation_preflight_blocking_count"], 1)
        self.assertEqual(
            portfolio["audited_writer_activation_preflight_primary_blocker_code"],
            "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
        )
        self.assertEqual(
            [stage["status"] for stage in portfolio["audited_writer_activation_preflight_stages"]],
            [
                "PASS_REVIEW_ONLY",
                "PASS_REVIEW_ONLY",
                "PASS_REVIEW_ONLY",
                "PASS_REVIEW_ONLY",
                "PASS_SNAPSHOT_ONLY",
                "BLOCKED",
            ],
        )
        html = render_dashboard_html(dashboard)
        self.assertIn("Activation preflight", html)
        self.assertIn("Snapshot Only Continuous Writer Blocked", html)
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_compacts_audited_writer_blocker_decision_for_single_run_snapshot(self):
        dashboard = build_dashboard_with_full_audited_writer_activation_chain()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(
            portfolio["audited_writer_blocker_decision_status"],
            "SNAPSHOT_DISPLAY_ONLY_CONTINUOUS_WRITER_BLOCKED",
        )
        self.assertEqual(
            portfolio["audited_writer_blocker_decision_code"],
            "CONTINUOUS_CURRENT_EVIDENCE_WRITER_BLOCKED",
        )
        self.assertEqual(
            portfolio["audited_writer_blocker_truth_class"],
            "SINGLE_RUN_AUDITED_PAPER_SNAPSHOT_DISPLAY_ONLY",
        )
        self.assertEqual(portfolio["audited_writer_blocker_priority_rank"], 3)
        self.assertEqual(portfolio["audited_writer_blocker_current_stage_id"], "CONTINUOUS_WRITER_LOOP")
        self.assertTrue(portfolio["audited_writer_blocker_allows_single_run_paper_display"])
        self.assertTrue(portfolio["audited_writer_blocker_blocks_continuous_current_evidence_write"])
        self.assertIn(
            "continuous current-evidence writer remains blocked",
            portfolio["audited_writer_blocker_summary"],
        )
        for field in (
            "audited_writer_blocker_current_evidence_write_allowed",
            "audited_writer_blocker_portfolio_truth_write_allowed",
            "audited_writer_blocker_live_review_allowed",
            "audited_writer_blocker_gap_closure_allowed",
            "audited_writer_blocker_live_order_ready",
            "audited_writer_blocker_live_order_allowed",
            "audited_writer_blocker_can_live_trade",
            "audited_writer_blocker_scale_up_allowed",
        ):
            self.assertFalse(portfolio[field])

        html = render_dashboard_html(dashboard)
        self.assertIn("Writer blocker:", html)
        self.assertIn("SNAPSHOT_DISPLAY_ONLY_CONTINUOUS_WRITER_BLOCKED", html)
        self.assertIn("CONTINUOUS_CURRENT_EVIDENCE_WRITER_BLOCKED", html)
        self.assertNotIn("<button", html)
        self.assertNotIn("<form", html)
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_compacts_audited_writer_blocker_decision_for_precheck_blocker(self):
        dashboard = build_dashboard_with_audited_writer_precheck()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["audited_writer_blocker_decision_status"], "BLOCKED_INPUTS")
        self.assertEqual(
            portfolio["audited_writer_blocker_decision_code"],
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED",
        )
        self.assertEqual(portfolio["audited_writer_blocker_truth_class"], "CONFIGURED_PAPER_BASELINE_ONLY")
        self.assertEqual(portfolio["audited_writer_blocker_priority_rank"], 1)
        self.assertEqual(portfolio["audited_writer_blocker_current_stage_id"], "DRY_RUN_REPORT")
        self.assertFalse(portfolio["audited_writer_blocker_allows_single_run_paper_display"])
        self.assertTrue(portfolio["audited_writer_blocker_blocks_continuous_current_evidence_write"])
        self.assertIn("configured PAPER capital is not current cash", portfolio["audited_writer_blocker_summary"])
        self.assertFalse(portfolio["audited_writer_blocker_current_evidence_write_allowed"])
        self.assertFalse(portfolio["audited_writer_blocker_portfolio_truth_write_allowed"])
        self.assertFalse(portfolio["audited_writer_blocker_live_review_allowed"])
        self.assertFalse(portfolio["audited_writer_blocker_gap_closure_allowed"])
        self.assertFalse(portfolio["audited_writer_blocker_live_order_ready"])
        self.assertFalse(portfolio["audited_writer_blocker_live_order_allowed"])
        self.assertFalse(portfolio["audited_writer_blocker_can_live_trade"])
        self.assertFalse(portfolio["audited_writer_blocker_scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_blocker_decision_permission_drift(self):
        dashboard = build_dashboard_with_full_audited_writer_activation_chain()
        portfolio = dashboard["portfolio_snapshot"]
        portfolio["audited_writer_blocker_current_evidence_write_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_audited_writer_blocker_decision_status_drift(self):
        dashboard = build_dashboard_with_full_audited_writer_activation_chain()
        portfolio = dashboard["portfolio_snapshot"]
        portfolio["audited_writer_blocker_decision_status"] = "BLOCKED_INPUTS"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_keeps_audited_current_evidence_writer_portfolio_unverified_on_live_drift(self):
        writer_report, current_evidence, paper_portfolio, implementation_prep = audited_writer_output_fixture()
        current_evidence = dict(current_evidence)
        current_evidence["live_order_allowed"] = True
        current_evidence["snapshot_hash"] = upbit_paper_audited_current_evidence_snapshot_hash(current_evidence)

        dashboard = build_dashboard_with_audited_current_evidence_writer(
            (writer_report, current_evidence, paper_portfolio, implementation_prep)
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source"], "audited_current_evidence_snapshot.json")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "LIVE_FINAL_GUARD_FAILED")
        self.assertEqual(portfolio["audited_writer_readiness_ladder_status"], "BLOCKED_INPUTS")
        self.assertEqual(portfolio["cash"]["value_display"], "UNVERIFIED")
        positions = dashboard["position_snapshot"]
        self.assertEqual(positions["status"], "UNVERIFIED")
        self.assertEqual(positions["source"], "audited_current_evidence_snapshot.json")
        self.assertEqual(positions["open_position_count"], 0)
        self.assertEqual(positions["rows"], [])
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_audited_writer_readiness_ladder_permission_drift(self):
        dashboard = build_dashboard_with_audited_current_evidence_writer()
        portfolio = dashboard["portfolio_snapshot"]
        portfolio["audited_writer_readiness_ladder_current_evidence_write_allowed"] = True
        portfolio["audited_writer_readiness_ladder_steps"][0]["current_evidence_write_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_audited_writer_activation_preflight_permission_drift(self):
        dashboard = build_dashboard_with_audited_current_evidence_writer()
        portfolio = dashboard["portfolio_snapshot"]
        portfolio["audited_writer_activation_preflight_current_evidence_write_allowed"] = True
        portfolio["audited_writer_activation_preflight_stages"][0]["current_evidence_write_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_audited_writer_activation_preflight_continuous_writer_pass_drift(self):
        dashboard = build_dashboard_with_audited_current_evidence_writer()
        portfolio = dashboard["portfolio_snapshot"]
        continuous_stage = portfolio["audited_writer_activation_preflight_stages"][-1]
        continuous_stage["status"] = "PASS_REVIEW_ONLY"
        continuous_stage["validation_status"] = "PASS"
        continuous_stage["review_only"] = True
        continuous_stage["blocks_writer_activation_until_pass"] = False
        portfolio["audited_writer_activation_preflight_pass_review_count"] = 2
        portfolio["audited_writer_activation_preflight_blocking_count"] = 3
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_audited_writer_readiness_ladder_continuous_writer_pass_drift(self):
        dashboard = build_dashboard_with_audited_current_evidence_writer()
        portfolio = dashboard["portfolio_snapshot"]
        continuous_step = portfolio["audited_writer_readiness_ladder_steps"][-1]
        continuous_step["status"] = "PASS"
        continuous_step["blocks_current_evidence_write_until_pass"] = False
        continuous_step["blocks_portfolio_truth_write_until_pass"] = False
        continuous_step["blocks_live_review_until_pass"] = False
        portfolio["audited_writer_readiness_ladder_blocking_count"] = 0
        portfolio["audited_writer_readiness_ladder_highest_passed_step_id"] = "CONTINUOUS_CURRENT_EVIDENCE_WRITER"
        portfolio["audited_writer_readiness_ladder_current_step_id"] = "CONTINUOUS_CURRENT_EVIDENCE_WRITER"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_keeps_stale_audited_current_evidence_portfolio_values_stale_not_unverified(self):
        writer_report, current_evidence, paper_portfolio, implementation_prep = audited_writer_output_fixture()
        current_evidence = dict(current_evidence)
        writer_report = dict(writer_report)
        writer_report["artifacts"] = [
            dict(artifact) if isinstance(artifact, dict) else artifact
            for artifact in writer_report.get("artifacts", [])
        ]
        current_evidence["generated_at_utc"] = "2026-01-01T00:00:00Z"
        current_evidence["snapshot_hash"] = upbit_paper_audited_current_evidence_snapshot_hash(current_evidence)
        for artifact in writer_report["artifacts"]:
            if artifact.get("artifact_id") == "AUDITED_CURRENT_EVIDENCE_SNAPSHOT":
                artifact["payload_hash"] = current_evidence["snapshot_hash"]
        writer_report["audited_writer_report_hash"] = upbit_paper_repaired_current_evidence_audited_writer_report_hash(
            writer_report
        )

        dashboard = build_dashboard_with_audited_current_evidence_writer(
            (writer_report, current_evidence, paper_portfolio, implementation_prep)
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)

        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "STALE")
        self.assertEqual(portfolio["source"], "audited_current_evidence_snapshot.json")
        self.assertEqual(portfolio["source_snapshot_status"], "PASS")
        self.assertEqual(portfolio["blocking_reason"], "LATENCY_TTL_EXPIRED")
        self.assertEqual(portfolio["paper_value_truth_status"], "PAPER_LEDGER_LAST_VERIFIED_VALUES_STALE")
        self.assertEqual(portfolio["runtime_continuity_status"], "STALE_SNAPSHOT_NOT_RUNTIME_PROOF")
        self.assertEqual(
            portfolio["audited_writer_lifecycle_status"],
            "AUDITED_SNAPSHOT_WRITTEN_CONTINUOUS_WRITER_BLOCKED",
        )
        self.assertIn("Last verified audited PAPER ledger values", portfolio["paper_value_truth_message"])
        self.assertIn("continuous current-evidence writer", portfolio["operator_truth_summary"])
        self.assertEqual(portfolio["configured_paper_capital"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["configured_paper_capital"]["freshness_status"], "PASS")
        self.assertEqual(portfolio["cash"]["value_display"], krw_display(current_evidence["verified_cash_krw"]))
        self.assertEqual(portfolio["cash"]["freshness_status"], "STALE")
        self.assertEqual(portfolio["cash"]["label"], "Current Cash")
        self.assertEqual(portfolio["equity"]["label"], "Current Equity")
        self.assertIn("Verified simulated PAPER ledger equity", portfolio["equity"]["detail"])
        self.assertIn("Audited PAPER current evidence is stale", portfolio["source_snapshot_freshness_message"])
        positions = dashboard["position_snapshot"]
        self.assertEqual(positions["status"], "STALE")
        self.assertEqual(positions["source"], "paper_portfolio_snapshot.json")
        self.assertEqual(positions["open_position_count"], 1)
        self.assertEqual(len(positions["rows"]), 1)
        source_status = {
            source["artifact_id"]: source["freshness_status"]
            for source in dashboard["source_artifacts"]
            if source["artifact_id"]
            in {
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT",
            }
        }
        self.assertEqual(
            source_status,
            {
                "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER": "PASS",
                "AUDITED_CURRENT_EVIDENCE_SNAPSHOT": "STALE",
                "AUDITED_PAPER_PORTFOLIO_SNAPSHOT": "PASS",
            },
        )
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Configured baseline: 1,000,000 KRW", html)
        self.assertIn("Current values:</strong> Last verified PAPER ledger", html)
        self.assertIn("PAPER_LEDGER_LAST_VERIFIED_VALUES_STALE", html)
        self.assertIn("STALE_SNAPSHOT_NOT_RUNTIME_PROOF", html)

    def test_dashboard_displays_bound_verified_portfolio_when_stale_loop_reconciliation_blocks_writes(self):
        report = stale_loop_post_regeneration_reconciliation_fixture()
        with TemporaryDirectory() as tmp:
            runtime_root = Path(tmp)
            run_upbit_paper_persistent_loop(
                root=runtime_root,
                loop_id="test-dashboard-bound-portfolio-truth-reconciliation",
                session_id=report["session_id"],
                requested_cycle_count=1,
            )
            ledger_report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
                root=runtime_root,
                session_id=report["session_id"],
                evidence_id="test-dashboard-bound-portfolio-truth-reconciliation",
            )
        paper_portfolio = build_initial_paper_portfolio_snapshot(
            exchange=report["exchange"],
            market_type=report["market_type"],
            session_id=report["session_id"],
            source_runtime_cycle_id=ledger_report["portfolio_source_runtime_cycle_id"],
            source_paper_ledger_head_hash=ledger_report["portfolio_source_paper_ledger_head_hash"],
        )
        dashboard = build_dashboard_with_stale_loop_post_regeneration_reconciliation(
            report=report,
            ledger_idempotency_report=ledger_report,
            paper_portfolio_snapshot=paper_portfolio,
        )

        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "VERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "PASS")
        self.assertEqual(portfolio["source_paper_ledger_head_hash"], ledger_report["portfolio_source_paper_ledger_head_hash"])
        self.assertEqual(portfolio["cash"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["equity"]["value_display"], "1,000,000 KRW")
        self.assertEqual(portfolio["blocking_reason"], "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED")
        self.assertIn("current-evidence writes and live review remain blocked", portfolio["source_snapshot_freshness_message"])

        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["status"], "BLOCKED")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_evidence_status"], "PASS")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_reconciliation_status"], "PASS")
        self.assertEqual(reconciliation["ledger_idempotency_runtime_portfolio_provenance_status"], "PASS")
        self.assertEqual(dashboard["operation_status"]["status"], "CHECKING_SAFE_MODE")
        self.assertEqual(dashboard["operation_status"]["portfolio_status"], "VERIFIED")
        self.assertEqual(
            dashboard["operation_status"]["primary_blocker"],
            "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
        )
        self.assertFalse(dashboard["live_order_ready"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_keeps_stale_loop_portfolio_unverified_when_ledger_evidence_is_not_bound(self):
        report = stale_loop_post_regeneration_reconciliation_fixture()
        ledger_report = ledger_idempotency_runtime_evidence_fixture(
            session_id=report["session_id"],
            evidence_id="test-dashboard-unbound-portfolio-truth-reconciliation",
        )
        paper_portfolio = build_initial_paper_portfolio_snapshot(
            exchange=report["exchange"],
            market_type=report["market_type"],
            session_id=report["session_id"],
        )
        dashboard = build_dashboard_with_stale_loop_post_regeneration_reconciliation(
            report=report,
            ledger_idempotency_report=ledger_report,
            paper_portfolio_snapshot=paper_portfolio,
        )

        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["status"], "UNVERIFIED")
        self.assertEqual(portfolio["source_snapshot_status"], "BLOCKED")
        self.assertEqual(portfolio["blocking_reason"], "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED")
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["scale_up_allowed"])

    def test_dashboard_blocks_stale_loop_post_regeneration_live_or_evidence_drift(self):
        report = stale_loop_post_regeneration_reconciliation_fixture()
        report["long_run_evidence_eligible"] = True
        report["live_order_allowed"] = True
        report["post_reconciliation_hash"] = stale_loop_post_regeneration_reconciliation_hash(report)
        dashboard = build_dashboard_with_stale_loop_post_regeneration_reconciliation(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        reconciliation = dashboard["reconciliation_recovery_summary"]
        self.assertEqual(reconciliation["stale_loop_post_regeneration_reconciliation_status"], "INVALID")
        self.assertEqual(reconciliation["stale_loop_post_regeneration_reconciliation_validation_status"], "BLOCKED")
        self.assertEqual(reconciliation["status"], "INVALID")
        self.assertEqual(reconciliation["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(reconciliation["live_order_allowed"])
        self.assertFalse(dashboard["live_order_allowed"])

    def test_dashboard_blocks_post_rerun_resolution_audit_current_evidence_drift(self):
        dashboard = build_dashboard_with_post_rerun_resolution_audit()
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["post_rerun_resolution_current_evidence_write_allowed_count"] = 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_post_rerun_resolution_audit_source_binding_drift(self):
        dashboard = build_dashboard_with_post_rerun_resolution_audit()
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["post_rerun_resolution_source_review_guidance_file_hash_match"] = False
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_post_rerun_review_guidance_current_evidence_drift(self):
        dashboard = build_dashboard_with_post_rerun_review_guidance()
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["post_rerun_guidance_current_evidence_write_allowed_count"] = 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_post_rerun_blocker_rollup_current_evidence_drift(self):
        dashboard = build_dashboard_with_post_rerun_blocker_rollup()
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["post_rerun_current_evidence_write_allowed_count"] = 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_post_rerun_blocker_rollup_false_operator_status(self):
        dashboard = build_dashboard_with_post_rerun_blocker_rollup()
        dashboard["operator_action_summary"]["status"] = "PAPER_REVIEW_READY"
        dashboard["operator_action_summary"]["severity"] = "NORMAL"
        dashboard["operator_action_summary"]["color_token"] = "blue"
        dashboard["operator_action_summary"]["safe_to_continue_paper"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_reconciliation_summary_live_permission(self):
        dashboard = build_dashboard_with_reconciliation()
        dashboard["reconciliation_recovery_summary"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_reconciliation_false_pass_with_mismatch(self):
        dashboard = build_dashboard_with_reconciliation()
        reconciliation = dashboard["reconciliation_recovery_summary"]
        reconciliation["status"] = "PASS"
        reconciliation["reconciliation_status"] = "MISMATCH"
        reconciliation["mismatch_count"] = 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_portfolio_execution_truth(self):
        dashboard = build_dashboard()
        dashboard["portfolio_snapshot"]["truth_role"] = "ledger"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_portfolio_live_permission(self):
        dashboard = build_dashboard()
        dashboard["portfolio_snapshot"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_portfolio_scale_up_permission(self):
        dashboard = build_dashboard()
        dashboard["portfolio_snapshot"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_verified_portfolio_missing_snapshot_hash(self):
        dashboard = build_dashboard()
        dashboard["portfolio_snapshot"]["source_snapshot_hash"] = None
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_verified_portfolio_snapshot_status_drift(self):
        dashboard = build_dashboard()
        dashboard["portfolio_snapshot"]["source_snapshot_status"] = "BLOCKED"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_verified_portfolio_balance_kind_drift(self):
        dashboard = build_dashboard()
        dashboard["portfolio_snapshot"]["source_balance_kind"] = "EXCHANGE_BALANCE"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_unverified_fresh_portfolio_value(self):
        dashboard = build_dashboard(with_paper_portfolio=False)
        dashboard["portfolio_snapshot"]["cash"]["freshness_status"] = "PASS"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_false_normal_operation_status(self):
        summary, _, startup_probe = build_inputs()
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard_false_normal",
            summary=summary,
            heartbeat=None,
            startup_probe=startup_probe,
        )
        dashboard["operation_status"]["severity"] = "NORMAL"
        dashboard["operation_status"]["color_token"] = "green"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LATENCY_TTL_EXPIRED")

    def test_dashboard_blocks_red_non_error_status_color(self):
        dashboard = build_dashboard()
        dashboard["operation_status"]["color_token"] = "red"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_operation_portfolio_status_mismatch(self):
        dashboard = build_dashboard()
        dashboard["operation_status"]["portfolio_status"] = "UNVERIFIED"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_decision_trace_live_permission(self):
        dashboard = build_dashboard()
        dashboard["decision_trace"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_decision_trace_scale_up_permission(self):
        dashboard = build_dashboard()
        dashboard["decision_trace"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_decision_trace_reason_mismatch(self):
        dashboard = build_dashboard()
        dashboard["decision_trace"]["no_trade_reason"] = "LIVE_READY_MISSING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_position_snapshot_execution_truth(self):
        dashboard = build_dashboard()
        dashboard["position_snapshot"]["truth_role"] = "ledger"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_position_snapshot_live_permission(self):
        dashboard = build_dashboard()
        dashboard["position_snapshot"]["can_live_trade"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_position_snapshot_scale_up_permission(self):
        dashboard = build_dashboard()
        dashboard["position_snapshot"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_recent_events_live_permission(self):
        dashboard = build_dashboard()
        dashboard["recent_events"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_recent_events_scale_up_permission(self):
        dashboard = build_dashboard()
        dashboard["recent_events"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_recent_events_execution_truth(self):
        dashboard = build_dashboard()
        dashboard["recent_events"]["truth_role"] = "ledger"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_no_trade_without_recent_no_trade_event(self):
        dashboard = build_dashboard()
        dashboard["recent_events"]["items"] = [
            item for item in dashboard["recent_events"]["items"] if item["event_type"] != "NO_TRADE"
        ]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_stability_trends_live_permission(self):
        dashboard = build_dashboard()
        dashboard["stability_trends"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_stability_trends_execution_truth(self):
        dashboard = build_dashboard()
        dashboard["stability_trends"]["truth_role"] = "ledger"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_profitability_maturity_shows_scorecard_input_without_live_permission(self):
        dashboard = build_dashboard_with_operation_gate()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        maturity = dashboard["profitability_maturity"]
        self.assertEqual(maturity["status"], "COLLECTING")
        self.assertEqual(maturity["severity"], "WARNING")
        self.assertEqual(maturity["color_token"], "yellow")
        self.assertFalse(maturity["scorecard_input_eligible"])
        self.assertEqual(maturity["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertLess(maturity["paper_sample_count"], maturity["min_required_samples"])
        self.assertLess(maturity["shadow_sample_count"], maturity["min_required_samples"])
        self.assertEqual(maturity["actual_runtime_source_status"], "MISSING")
        self.assertEqual(maturity["actual_runtime_source_count"], 0)
        self.assertFalse(maturity["long_run_evidence_eligible"])
        self.assertEqual(maturity["long_run_blocker_code"], "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING")
        self.assertIn("validated non-live persistent runtime source", maturity["actual_runtime_source_summary"])
        self.assertEqual(maturity["cost_evidence_status"], "PASS")
        self.assertEqual(maturity["entry_reason_status"], "PASS")
        self.assertEqual(maturity["no_trade_reason_status"], "UNTESTED")
        self.assertEqual(maturity["evidence_progress_status"], "IN_PROGRESS")
        self.assertEqual(maturity["evidence_progress_pct"], 40)
        self.assertEqual(maturity["evidence_progress_summary"], "2/5 evidence checks complete")
        self.assertTrue(any(item["status"] == "MISSING" for item in maturity["evidence_checklist"]))
        self.assertEqual(maturity["maturity_gap_status"], "OPEN_HIGH")
        self.assertEqual(maturity["maturity_component_count"], 10)
        self.assertEqual(maturity["paper_scorecard_component_pass_count"], 1)
        self.assertEqual(maturity["maturity_gap_count"], 9)
        self.assertIn("Live remains blocked", maturity["maturity_gap_summary"])
        self.assertTrue(all(item["live_review_blocker"] for item in maturity["maturity_components"]))
        self.assertFalse(any(item["live_order_allowed"] for item in maturity["maturity_components"]))
        self.assertTrue(all(item["next_required_evidence"] for item in maturity["maturity_components"]))
        self.assertIn("net EV after all costs", maturity["maturity_components"][5]["next_required_evidence"])
        self.assertEqual(maturity["scorecard_scope"], "PAPER_EVIDENCE_COLLECTION_ONLY")
        self.assertEqual(maturity["live_readiness_status"], "NOT_LIVE_READY")
        self.assertIn("not LIVE_READY", maturity["operator_warning"])
        self.assertFalse(maturity["live_order_ready"])
        self.assertFalse(maturity["live_order_allowed"])
        self.assertFalse(maturity["can_live_trade"])
        self.assertFalse(maturity["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Collecting", html)
        self.assertIn("BLOCK_RANKING", html)
        self.assertIn("Evidence Progress: 40%", html)
        self.assertIn("Maturity Gap: OPEN_HIGH", html)
        self.assertIn("9 maturity gaps remain", html)
        self.assertIn("Strategy Entry Exit No Trade", html)
        self.assertIn("EVIDENCE_MISSING", html)
        self.assertIn("RECORDED_GAP", html)
        self.assertIn("Next: Validate optimizer ranking against net EV after all costs", html)
        self.assertIn("PAPER_EVIDENCE_COLLECTION_ONLY", html)
        self.assertIn("NOT_LIVE_READY", html)
        self.assertIn("Long-Run Evidence", html)
        self.assertIn("MISSING", html)
        self.assertIn("0 runtime sources", html)
        self.assertIn("not LIVE_READY", html)
        self.assertIn("maturity-yellow", html)
        self.assertIn("before ranking", html)

    def test_dashboard_blocks_profitability_long_run_without_runtime_source(self):
        dashboard = build_dashboard_with_operation_gate()
        maturity = dashboard["profitability_maturity"]
        maturity["long_run_evidence_eligible"] = True
        maturity["long_run_blocker_code"] = None
        maturity["actual_runtime_source_status"] = "MISSING"
        maturity["actual_runtime_source_count"] = 0
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)

        result = validate_read_only_dashboard_shell(dashboard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_dashboard_blocks_validated_runtime_status_without_source_ids(self):
        dashboard = build_dashboard_with_operation_gate()
        maturity = dashboard["profitability_maturity"]
        maturity["actual_runtime_source_status"] = "VALIDATED_NON_LIVE_RUNTIME"
        maturity["actual_runtime_source_count"] = 0
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)

        result = validate_read_only_dashboard_shell(dashboard)

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_profitability_maturity_live_permission(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_profitability_maturity_live_ready_wording_drift(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["live_readiness_status"] = "LIVE_READY"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_scorecard_scope_without_live_warning(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["operator_warning"] = "Scorecard input is ready."
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_scorecard_scope_with_misleading_live_ready_warning(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["operator_warning"] = (
            "PAPER scorecard input is LIVE_READY but live orders remain blocked."
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_scorecard_scope_when_input_ineligible(self):
        dashboard = build_dashboard()
        dashboard["profitability_maturity"]["scorecard_scope"] = "PAPER_SCORECARD_INPUT_ONLY"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_profitability_checklist_live_permission(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["evidence_checklist"][0]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_profitability_component_live_permission(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["maturity_components"][0]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_profitability_component_without_next_evidence(self):
        dashboard = build_dashboard_with_operation_gate()
        dashboard["profitability_maturity"]["maturity_components"][0]["next_required_evidence"] = ""
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_profitability_component_order_mismatch(self):
        dashboard = build_dashboard_with_operation_gate()
        components = dashboard["profitability_maturity"]["maturity_components"]
        components[0], components[1] = components[1], components[0]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_profitability_maturity_hiding_open_gap(self):
        dashboard = build_dashboard_with_operation_gate()
        maturity = dashboard["profitability_maturity"]
        for component in maturity["maturity_components"]:
            component["status"] = "PAPER_SCORECARD_EVIDENCE_PASS"
            component["paper_scorecard_input_eligible"] = True
        maturity["paper_scorecard_component_pass_count"] = 10
        maturity["maturity_gap_count"] = 0
        maturity["maturity_gap_summary"] = "10/10 components complete."
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_false_profitability_progress_ready(self):
        dashboard = build_dashboard()
        maturity = dashboard["profitability_maturity"]
        maturity["evidence_progress_status"] = "READY"
        maturity["evidence_progress_pct"] = 100
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_profitability_checklist_order_mismatch(self):
        dashboard = build_dashboard()
        checklist = dashboard["profitability_maturity"]["evidence_checklist"]
        checklist[0], checklist[1] = checklist[1], checklist[0]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_scorecard_live_gap_status_when_input_ineligible(self):
        dashboard = build_dashboard()
        dashboard["profitability_maturity"]["maturity_gap_status"] = "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_risk_exposure_live_permission(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_risk_exposure_scale_up_blocker_drift(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["scale_up_blocker_code"] = "NONE"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_execution_feedback_shows_paper_ranking_review_without_live_permission(self):
        dashboard = build_dashboard_with_optimizer_feedback()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        feedback = dashboard["execution_feedback_snapshot"]
        self.assertEqual(feedback["status"], "READY_FOR_PAPER_RANKING_REVIEW")
        self.assertEqual(feedback["severity"], "NORMAL")
        self.assertEqual(feedback["color_token"], "blue")
        self.assertEqual(feedback["execution_quality_status"], "PASS")
        self.assertEqual(feedback["risk_review_status"], "PASS")
        self.assertEqual(feedback["exposure_review_status"], "PASS")
        self.assertEqual(feedback["drawdown_review_status"], "PASS")
        self.assertEqual(feedback["optimizer_ranking_action"], "ALLOW_RANKING")
        self.assertTrue(feedback["feedback_eligible"])
        self.assertFalse(feedback["promotion_eligible"])
        self.assertFalse(feedback["live_order_ready"])
        self.assertFalse(feedback["live_order_allowed"])
        self.assertFalse(feedback["can_live_trade"])
        self.assertFalse(feedback["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Execution Feedback", html)
        self.assertIn("Ready For Paper Ranking Review", html)
        self.assertIn("Risk Review", html)
        self.assertIn("ALLOW_RANKING", html)
        self.assertIn("feedback-blue", html)
        self.assertIn("Execution feedback is PAPER/SHADOW analysis-only", html)

    def test_dashboard_convergence_assessment_shows_dependency_closure_without_live_permission(self):
        dashboard = build_dashboard_with_convergence_assessment()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        convergence = dashboard["convergence_assessment_status"]
        self.assertEqual(convergence["status"], "LOCALLY_IMPROVING")
        self.assertEqual(convergence["severity"], "NORMAL")
        self.assertEqual(convergence["color_token"], "blue")
        self.assertEqual(convergence["assessment_status"], "LOCALLY_IMPROVING")
        self.assertEqual(convergence["convergence_claim"], "LOCALLY_IMPROVING")
        self.assertEqual(convergence["objective_score_band"], "LOCAL_IMPROVING")
        self.assertEqual(convergence["model_drift_status"], "NO_DRIFT")
        self.assertEqual(convergence["dependency_pass_count"], 10)
        self.assertEqual(convergence["required_dependency_count"], 10)
        self.assertEqual(convergence["primary_blocker_code"], "LIVE_READY_MISSING")
        self.assertTrue(all(item["status"] == "PASS" for item in convergence["dependency_statuses"]))
        self.assertFalse(convergence["writer_input_eligible"])
        self.assertFalse(convergence["model_promotion_allowed"])
        self.assertFalse(convergence["scale_up_recommendation_allowed"])
        self.assertFalse(convergence["live_order_ready"])
        self.assertFalse(convergence["live_order_allowed"])
        self.assertFalse(convergence["can_live_trade"])
        self.assertFalse(convergence["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Convergence Assessment", html)
        self.assertIn("Dependency Closure", html)
        self.assertIn("Model Drift", html)
        self.assertIn("Live Boundary", html)
        self.assertIn("Locally Improving", html)
        self.assertIn("10/10 dependency validators PASS", html)
        self.assertIn("not LIVE_READY", html)
        self.assertIn("live orders blocked", html)
        self.assertIn("scale-up blocked", html)
        self.assertIn("convergence-blue", html)
        self.assertIn("Writer Input=False", html)
        self.assertIn("Display-only convergence review", html)

    def test_dashboard_blocks_convergence_assessment_writer_input_or_scale_up_drift(self):
        report = convergence_assessment_fixture()
        report["writer_input_eligible"] = True
        dashboard = build_dashboard_with_convergence_assessment(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        convergence = dashboard["convergence_assessment_status"]
        self.assertEqual(convergence["status"], "BLOCKED")
        self.assertEqual(convergence["severity"], "ERROR")
        self.assertEqual(convergence["color_token"], "red")
        self.assertEqual(convergence["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(convergence["writer_input_eligible"])
        self.assertFalse(convergence["scale_up_recommendation_allowed"])
        convergence["writer_input_eligible"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_false_convergence_improving_without_dependency_closure(self):
        dashboard = build_dashboard()
        convergence = dashboard["convergence_assessment_status"]
        convergence["status"] = "LOCALLY_IMPROVING"
        convergence["severity"] = "NORMAL"
        convergence["color_token"] = "blue"
        convergence["convergence_claim"] = "LOCALLY_IMPROVING"
        convergence["primary_blocker_code"] = "LIVE_READY_MISSING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_convergence_dependency_count_mismatch(self):
        dashboard = build_dashboard_with_convergence_assessment()
        dashboard["convergence_assessment_status"]["dependency_pass_count"] = 9
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_exploration_policy_shows_paper_ranking_review_without_live_permission(self):
        dashboard = build_dashboard_with_exploration_policy()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        exploration = dashboard["exploration_policy_status"]
        self.assertEqual(exploration["status"], "PAPER_RANKING_REVIEW_ELIGIBLE")
        self.assertEqual(exploration["severity"], "NORMAL")
        self.assertEqual(exploration["color_token"], "blue")
        self.assertEqual(exploration["policy_status"], "PAPER_RANKING_REVIEW_ELIGIBLE")
        self.assertEqual(exploration["controller_state"], "EXPLOITING_PAPER_ONLY")
        self.assertEqual(exploration["transition_decision"], "LIMITED_EXPLOITATION_REVIEW")
        self.assertEqual(exploration["recommendation_scope"], "PAPER_RANKING_REVIEW_ONLY")
        self.assertEqual(exploration["objective_basis"], "NET_EV_AFTER_COST")
        self.assertEqual(exploration["dependency_pass_count"], 6)
        self.assertEqual(exploration["required_dependency_count"], 6)
        self.assertTrue(all(item["status"] == "PASS" for item in exploration["dependency_statuses"]))
        self.assertEqual(exploration["candidate_count"], 12)
        self.assertEqual(exploration["exploration_candidate_budget"], 20)
        self.assertEqual(exploration["candidate_budget_status"], "PASS")
        self.assertTrue(exploration["exploitation_allowed_for_paper_ranking"])
        self.assertEqual(exploration["primary_blocker_code"], "LIVE_READY_MISSING")
        self.assertFalse(exploration["live_order_ready"])
        self.assertFalse(exploration["live_order_allowed"])
        self.assertFalse(exploration["can_live_trade"])
        self.assertFalse(exploration["scale_up_allowed"])
        self.assertFalse(exploration["live_permission_created"])
        self.assertFalse(exploration["live_config_mutation_allowed"])
        self.assertFalse(exploration["writes_live_ready_snapshot"])
        self.assertFalse(exploration["active_snapshot_mutation_allowed"])
        self.assertFalse(exploration["order_submission_allowed"])
        self.assertFalse(exploration["exchange_account_call_allowed"])
        self.assertFalse(exploration["scale_up_recommendation_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Exploration / Exploitation Policy", html)
        self.assertIn("Candidate Budget", html)
        self.assertIn("PAPER Ranking", html)
        self.assertIn("Paper Ranking Review Eligible", html)
        self.assertIn("PAPER_RANKING_REVIEW_ONLY", html)
        self.assertIn("not LIVE_READY", html)
        self.assertIn("live orders blocked", html)
        self.assertIn("scale-up blocked", html)
        self.assertIn("exploration-policy-blue", html)
        self.assertIn("PAPER ranking review only", html)

    def test_dashboard_blocks_exploration_policy_live_or_scale_drift(self):
        report = exploration_policy_fixture()
        report["scale_up_recommendation_allowed"] = True
        dashboard = build_dashboard_with_exploration_policy(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        exploration = dashboard["exploration_policy_status"]
        self.assertEqual(exploration["status"], "BLOCKED")
        self.assertEqual(exploration["severity"], "ERROR")
        self.assertEqual(exploration["color_token"], "red")
        self.assertEqual(exploration["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(exploration["scale_up_recommendation_allowed"])
        exploration["order_submission_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_false_exploration_policy_eligible_without_dependency_closure(self):
        dashboard = build_dashboard()
        exploration = dashboard["exploration_policy_status"]
        exploration["status"] = "PAPER_RANKING_REVIEW_ELIGIBLE"
        exploration["severity"] = "NORMAL"
        exploration["color_token"] = "blue"
        exploration["exploitation_allowed_for_paper_ranking"] = True
        exploration["recommendation_scope"] = "PAPER_RANKING_REVIEW_ONLY"
        exploration["transition_decision"] = "LIMITED_EXPLOITATION_REVIEW"
        exploration["primary_blocker_code"] = "LIVE_READY_MISSING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_exploration_policy_dependency_count_mismatch(self):
        dashboard = build_dashboard_with_exploration_policy()
        dashboard["exploration_policy_status"]["dependency_pass_count"] = 5
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_exploration_policy_candidate_budget_exceeded(self):
        report = exploration_policy_fixture()
        report["candidate_count"] = 21
        dashboard = build_dashboard_with_exploration_policy(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        exploration = dashboard["exploration_policy_status"]
        self.assertEqual(exploration["status"], "BLOCKED")
        self.assertEqual(exploration["color_token"], "yellow")
        self.assertEqual(exploration["primary_blocker_code"], "OPTIMIZER_RESOURCE_BUDGET_EXCEEDED")

    def test_dashboard_parameter_narrowing_shows_paper_review_without_live_permission(self):
        dashboard = build_dashboard_with_parameter_narrowing()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        narrowing = dashboard["parameter_narrowing_status"]
        self.assertEqual(narrowing["status"], "PAPER_PARAMETER_REVIEW_ELIGIBLE")
        self.assertEqual(narrowing["severity"], "NORMAL")
        self.assertEqual(narrowing["color_token"], "blue")
        self.assertEqual(narrowing["narrowing_status"], "PAPER_PARAMETER_REVIEW_ELIGIBLE")
        self.assertEqual(narrowing["recommendation_scope"], "PAPER_PARAMETER_REVIEW_ONLY")
        self.assertEqual(narrowing["parameter_write_scope"], "PROPOSAL_ONLY")
        self.assertEqual(narrowing["objective_basis"], "NET_EV_AFTER_COST")
        self.assertEqual(narrowing["dependency_pass_count"], 7)
        self.assertEqual(narrowing["required_dependency_count"], 7)
        self.assertTrue(all(item["status"] == "PASS" for item in narrowing["dependency_statuses"]))
        self.assertEqual(narrowing["paper_sample_count"], 360)
        self.assertEqual(narrowing["shadow_sample_count"], 340)
        self.assertEqual(narrowing["parameter_count_before"], 12)
        self.assertEqual(narrowing["parameter_count_after"], 8)
        self.assertTrue(narrowing["narrowing_allowed_for_paper_ranking"])
        self.assertEqual(narrowing["primary_blocker_code"], "LIVE_READY_MISSING")
        self.assertFalse(narrowing["live_order_ready"])
        self.assertFalse(narrowing["live_order_allowed"])
        self.assertFalse(narrowing["can_live_trade"])
        self.assertFalse(narrowing["scale_up_allowed"])
        self.assertFalse(narrowing["live_permission_created"])
        self.assertFalse(narrowing["live_config_mutation_allowed"])
        self.assertFalse(narrowing["writes_live_ready_snapshot"])
        self.assertFalse(narrowing["active_snapshot_mutation_allowed"])
        self.assertFalse(narrowing["active_config_mutation_allowed"])
        self.assertFalse(narrowing["optimizer_winner_live_config_allowed"])
        self.assertFalse(narrowing["paper_winner_live_config_allowed"])
        self.assertFalse(narrowing["order_submission_allowed"])
        self.assertFalse(narrowing["exchange_account_call_allowed"])
        self.assertFalse(narrowing["scale_up_recommendation_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Parameter Narrowing", html)
        self.assertIn("Parameter Proposal", html)
        self.assertIn("Paper Parameter Review Eligible", html)
        self.assertIn("PAPER_PARAMETER_REVIEW_ONLY", html)
        self.assertIn("PROPOSAL_ONLY", html)
        self.assertIn("7/7 dependency validators PASS", html)
        self.assertIn("360 PAPER / 340 SHADOW samples", html)
        self.assertIn("proposal-only", html)
        self.assertIn("not LIVE_READY", html)
        self.assertIn("live orders blocked", html)
        self.assertIn("scale-up blocked", html)
        self.assertIn("parameter-narrowing-blue", html)
        self.assertIn("active config, live config, execution truth, and scale-up remain separate", html)

    def test_dashboard_blocks_parameter_narrowing_live_or_active_config_drift(self):
        report = parameter_narrowing_fixture()
        report["active_config_mutation_allowed"] = True
        dashboard = build_dashboard_with_parameter_narrowing(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        narrowing = dashboard["parameter_narrowing_status"]
        self.assertEqual(narrowing["status"], "BLOCKED")
        self.assertEqual(narrowing["severity"], "ERROR")
        self.assertEqual(narrowing["color_token"], "red")
        self.assertEqual(narrowing["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(narrowing["active_config_mutation_allowed"])
        narrowing["active_config_mutation_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_false_parameter_narrowing_eligible_without_dependency_closure(self):
        dashboard = build_dashboard()
        narrowing = dashboard["parameter_narrowing_status"]
        narrowing["status"] = "PAPER_PARAMETER_REVIEW_ELIGIBLE"
        narrowing["severity"] = "NORMAL"
        narrowing["color_token"] = "blue"
        narrowing["narrowing_allowed_for_paper_ranking"] = True
        narrowing["recommendation_scope"] = "PAPER_PARAMETER_REVIEW_ONLY"
        narrowing["parameter_write_scope"] = "PROPOSAL_ONLY"
        narrowing["primary_blocker_code"] = "LIVE_READY_MISSING"
        narrowing["paper_sample_count"] = 360
        narrowing["shadow_sample_count"] = 340
        narrowing["min_required_sample_count"] = 300
        narrowing["parameter_count_before"] = 12
        narrowing["parameter_count_after"] = 8
        narrowing["max_narrowing_pct"] = 40.0
        narrowing["narrowing_pct"] = 33.33
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_parameter_narrowing_dependency_count_mismatch(self):
        dashboard = build_dashboard_with_parameter_narrowing()
        dashboard["parameter_narrowing_status"]["dependency_pass_count"] = 6
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_parameter_narrowing_over_narrowing(self):
        report = parameter_narrowing_fixture()
        report["narrowing_pct"] = 50.0
        dashboard = build_dashboard_with_parameter_narrowing(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        narrowing = dashboard["parameter_narrowing_status"]
        self.assertEqual(narrowing["status"], "BLOCKED")
        self.assertEqual(narrowing["color_token"], "yellow")
        self.assertEqual(narrowing["primary_blocker_code"], "PARAMETER_NARROWING_UNVERIFIED")
        self.assertFalse(narrowing["narrowing_allowed_for_paper_ranking"])

    def test_dashboard_blocks_parameter_narrowing_sample_insufficient(self):
        report = parameter_narrowing_fixture()
        report["shadow_sample_count"] = 299
        dashboard = build_dashboard_with_parameter_narrowing(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        narrowing = dashboard["parameter_narrowing_status"]
        self.assertEqual(narrowing["status"], "BLOCKED")
        self.assertEqual(narrowing["color_token"], "yellow")
        self.assertEqual(narrowing["primary_blocker_code"], "PARAMETER_NARROWING_UNVERIFIED")
        self.assertFalse(narrowing["narrowing_allowed_for_paper_ranking"])

    def test_dashboard_blocks_execution_feedback_live_permission(self):
        report = optimizer_feedback_fixture()
        report["live_order_allowed"] = True
        dashboard = build_dashboard_with_optimizer_feedback(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["status"], "BLOCKED")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["primary_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        dashboard["execution_feedback_snapshot"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_execution_feedback_hash_mismatch(self):
        report = optimizer_feedback_fixture()
        report["realized_slippage_bps"] = report["realized_slippage_bps"] + 1
        dashboard = build_dashboard_with_optimizer_feedback(report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["status"], "BLOCKED")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["color_token"], "red")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["primary_blocker_code"], "EVIDENCE_HASH_MISMATCH")

    def test_dashboard_blocks_false_execution_feedback_ready_without_risk_pass(self):
        dashboard = build_dashboard()
        feedback = dashboard["execution_feedback_snapshot"]
        feedback["status"] = "READY_FOR_PAPER_RANKING_REVIEW"
        feedback["severity"] = "NORMAL"
        feedback["color_token"] = "blue"
        feedback["feedback_eligible"] = True
        feedback["optimizer_ranking_action"] = "ALLOW_RANKING"
        feedback["feedback_report_id"] = "fake_feedback"
        feedback["candidate_id"] = "fake_candidate"
        feedback["strategy_id"] = "fake_strategy"
        feedback["parameter_hash"] = "A" * 64
        feedback["primary_blocker_code"] = "LIVE_READY_MISSING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_false_low_risk_without_verified_portfolio(self):
        dashboard = build_dashboard(with_paper_portfolio=False)
        dashboard["risk_exposure_snapshot"]["status"] = "LOW_RISK"
        dashboard["risk_exposure_snapshot"]["severity"] = "NORMAL"
        dashboard["risk_exposure_snapshot"]["color_token"] = "green"
        dashboard["risk_exposure_snapshot"]["freshness_status"] = "PASS"
        dashboard["risk_exposure_snapshot"]["exposure_pct_display"] = "0.00%"
        dashboard["risk_exposure_snapshot"]["drawdown_pct_display"] = "0.00%"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_risk_exposure_warns_on_missing_position_notional(self):
        summary, heartbeat, startup_probe = build_inputs()
        summary["positions"] = [{"symbol": "KRW-BTC", "side": "LONG", "quantity": "0.1"}]
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["status"], "ATTENTION")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["color_token"], "yellow")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["exposure_pct_display"], "PARTIAL")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["exposure_data_status"], "PARTIAL")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["drawdown_data_status"], "VERIFIED")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["open_position_count"], 1)

    def test_dashboard_risk_exposure_warns_on_missing_drawdown_hard_truth(self):
        summary, heartbeat, startup_probe = build_inputs()
        summary["portfolio"].pop("mdd", None)
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        risk = dashboard["risk_exposure_snapshot"]
        self.assertEqual(risk["status"], "ATTENTION")
        self.assertEqual(risk["severity"], "WARNING")
        self.assertEqual(risk["color_token"], "yellow")
        self.assertEqual(risk["drawdown_pct_display"], "UNVERIFIED")
        self.assertEqual(risk["drawdown_data_status"], "UNVERIFIED")
        self.assertIn("drawdown hard truth is missing", risk["primary_blocker_message"])

    def test_dashboard_blocks_false_low_risk_with_unverified_drawdown(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["status"] = "LOW_RISK"
        dashboard["risk_exposure_snapshot"]["severity"] = "NORMAL"
        dashboard["risk_exposure_snapshot"]["color_token"] = "green"
        dashboard["risk_exposure_snapshot"]["drawdown_data_status"] = "UNVERIFIED"
        dashboard["risk_exposure_snapshot"]["drawdown_pct_display"] = "UNVERIFIED"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_false_low_risk_without_paper_exposure_quality_report(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["status"] = "LOW_RISK"
        dashboard["risk_exposure_snapshot"]["severity"] = "NORMAL"
        dashboard["risk_exposure_snapshot"]["color_token"] = "green"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_missing_paper_exposure_quality_next_evidence(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["paper_exposure_quality_next_required_evidence"] = ""
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_drawdown_data_status_schema_drift(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["drawdown_data_status"] = "COMPLETE"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_false_profitability_ranking_permission(self):
        dashboard = build_dashboard()
        dashboard["profitability_maturity"]["optimizer_ranking_action"] = "ALLOW_RANKING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_false_stable_stability_trends(self):
        dashboard = build_dashboard()
        dashboard["stability_trends"]["metrics"][0]["status"] = "STALE"
        dashboard["stability_trends"]["status"] = "STABLE"
        dashboard["stability_trends"]["severity"] = "NORMAL"
        dashboard["stability_trends"]["color_token"] = "green"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LATENCY_TTL_EXPIRED")

    def test_dashboard_warns_on_rate_limit_pressure(self):
        dashboard = build_dashboard(
            heartbeat_component_overrides={
                "rate_limit_pressure": {"status": "WARN", "message": "rate limit pressure elevated"},
            }
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        stability = dashboard["stability_trends"]
        self.assertEqual(stability["status"], "ATTENTION")
        self.assertEqual(stability["severity"], "WARNING")
        self.assertEqual(stability["color_token"], "yellow")
        rate_metric = next(metric for metric in stability["metrics"] if metric["metric_id"] == "rate_limit_pressure")
        self.assertEqual(rate_metric["status"], "WARN")
        self.assertIn("rate limit pressure elevated", rate_metric["detail"])

    def test_dashboard_warns_on_runtime_artifact_pressure(self):
        dashboard = build_dashboard(
            heartbeat_component_overrides={
                "disk": {"status": "WARN", "message": "Runtime artifact pressure WARN: files=250"},
            }
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        stability = dashboard["stability_trends"]
        self.assertEqual(stability["status"], "ATTENTION")
        self.assertEqual(stability["severity"], "WARNING")
        artifact_metric = next(metric for metric in stability["metrics"] if metric["metric_id"] == "runtime_artifact_pressure")
        self.assertEqual(artifact_metric["status"], "WARN")
        self.assertIn("Runtime artifact pressure WARN", artifact_metric["detail"])

    def test_dashboard_uses_validated_stability_history(self):
        dashboard = build_dashboard_with_history()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        stability = dashboard["stability_trends"]
        self.assertEqual(stability["history_window"], "VALIDATED_HISTORY")
        self.assertEqual(stability["history_source"], "stability_history.json")
        self.assertEqual(stability["history_sample_count"], 2)
        self.assertEqual(stability["span_validation_status"], "SPAN_VALIDATED")
        self.assertGreaterEqual(stability["observed_span_seconds"], stability["min_validated_span_seconds"])
        self.assertEqual(stability["degraded_sample_count"], 0)
        self.assertFalse(stability["live_order_allowed"])
        long_run = dashboard["long_run_operator_summary"]
        self.assertEqual(long_run["status"], "DISPLAY_HISTORY_STABLE")
        self.assertEqual(long_run["severity"], "NORMAL")
        self.assertEqual(long_run["color_token"], "green")
        self.assertEqual(long_run["source"], "stability_history.json")
        self.assertEqual(long_run["history_sample_count"], 2)
        self.assertEqual(long_run["span_validation_status"], "SPAN_VALIDATED")
        self.assertGreaterEqual(long_run["observed_span_seconds"], long_run["min_validated_span_seconds"])
        self.assertEqual(long_run["stable_sample_count"], 2)
        self.assertEqual(long_run["degraded_sample_count"], 0)
        self.assertEqual(long_run["stale_sample_count"], 0)
        self.assertFalse(long_run["live_order_allowed"])
        self.assertFalse(long_run["scale_up_allowed"])
        self.assertEqual(long_run["primary_blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertIn("display stability history is clean", long_run["summary"])
        self.assertIn("display history alone cannot satisfy live-review evidence", long_run["next_action"])
        runtime_boundary = dashboard["runtime_evidence_boundary"]
        self.assertEqual(runtime_boundary["status"], "ACTUAL_LONG_RUN_COLLECTING")
        self.assertEqual(runtime_boundary["actual_long_run_evidence_status"], "COLLECTING")
        self.assertEqual(runtime_boundary["primary_blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertIn("86400s duration", runtime_boundary["one_line_summary"])
        self.assertIn("2880 stable samples", runtime_boundary["one_line_summary"])
        self.assertIn("display history alone is not enough", runtime_boundary["one_line_summary"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Display History Stable", html)
        self.assertNotIn(">Validated Stable<", html)
        requirements = {item["requirement_id"]: item for item in runtime_boundary["evidence_requirements"]}
        self.assertEqual(requirements["ACTUAL_RUNTIME_DURATION"]["status"], "COLLECTING")
        self.assertEqual(requirements["ACTUAL_CYCLE_COUNT"]["status"], "COLLECTING")
        self.assertEqual(requirements["EVIDENCE_WINDOW_COUNT"]["status"], "COLLECTING")
        self.assertEqual(requirements["RECOVERY_AND_PARTIAL_WRITE_CLEAN"]["status"], "COLLECTING")
        self.assertFalse(runtime_boundary["live_review_evidence_eligible"])
        self.assertFalse(runtime_boundary["live_order_allowed"])
        self.assertFalse(runtime_boundary["can_live_trade"])
        self.assertFalse(runtime_boundary["scale_up_allowed"])

    def test_dashboard_does_not_hide_validated_history_when_current_sources_are_stale(self):
        baseline = build_dashboard()
        baseline["generated_at_utc"] = "2026-04-30T00:00:00Z"
        baseline["dashboard_hash"] = dashboard_shell_hash(baseline)
        history = append_stability_history(None, baseline)
        next_baseline = json.loads(json.dumps(baseline))
        next_baseline["generated_at_utc"] = "2026-04-30T01:05:00Z"
        next_baseline["dashboard_hash"] = dashboard_shell_hash(next_baseline)
        history = append_stability_history(history, next_baseline)
        summary, _heartbeat, startup_probe = build_inputs()

        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=None,
            startup_probe=startup_probe,
            stability_history=history,
        )

        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        stability = dashboard["stability_trends"]
        self.assertEqual(stability["history_window"], "VALIDATED_HISTORY")
        self.assertEqual(stability["history_source"], "stability_history.json")
        self.assertEqual(stability["span_validation_status"], "SPAN_VALIDATED")
        self.assertEqual(stability["severity"], "WARNING")
        long_run = dashboard["long_run_operator_summary"]
        self.assertEqual(long_run["status"], "STALE")
        self.assertEqual(long_run["history_window"], "VALIDATED_HISTORY")
        self.assertFalse(long_run["live_order_allowed"])

    def test_dashboard_keeps_sparse_day_history_collecting(self):
        dashboard = build_dashboard_with_sparse_day_history()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        long_run = dashboard["long_run_operator_summary"]
        self.assertEqual(long_run["status"], "DISPLAY_HISTORY_STABLE")
        self.assertGreaterEqual(long_run["observed_span_seconds"], 86400)
        self.assertEqual(long_run["history_sample_count"], 2)
        self.assertEqual(long_run["stable_sample_count"], 2)
        runtime_boundary = dashboard["runtime_evidence_boundary"]
        self.assertEqual(runtime_boundary["status"], "ACTUAL_LONG_RUN_COLLECTING")
        self.assertEqual(runtime_boundary["actual_long_run_evidence_status"], "COLLECTING")
        self.assertEqual(runtime_boundary["primary_blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertIn("2880 stable samples", runtime_boundary["one_line_summary"])
        self.assertIn("Use dedicated persistent PAPER/SHADOW runtime evidence", runtime_boundary["one_line_summary"])
        requirements = {item["requirement_id"]: item for item in runtime_boundary["evidence_requirements"]}
        self.assertEqual(requirements["ACTUAL_RUNTIME_DURATION"]["status"], "COLLECTING")
        self.assertEqual(requirements["ACTUAL_CYCLE_COUNT"]["status"], "COLLECTING")
        self.assertIn("persistent PAPER/SHADOW evidence", requirements["ACTUAL_CYCLE_COUNT"]["detail"])
        self.assertEqual(requirements["EVIDENCE_WINDOW_COUNT"]["status"], "COLLECTING")
        self.assertEqual(requirements["RECOVERY_AND_PARTIAL_WRITE_CLEAN"]["status"], "COLLECTING")
        self.assertFalse(runtime_boundary["live_review_evidence_eligible"])
        self.assertFalse(runtime_boundary["live_order_allowed"])
        self.assertFalse(runtime_boundary["can_live_trade"])
        self.assertFalse(runtime_boundary["scale_up_allowed"])

    def test_dashboard_blocks_sparse_day_history_false_runtime_boundary_validated(self):
        dashboard = build_dashboard_with_sparse_day_history()
        dashboard["runtime_evidence_boundary"]["status"] = "ACTUAL_LONG_RUN_VALIDATED"
        dashboard["runtime_evidence_boundary"]["actual_long_run_evidence_status"] = "VALIDATED_STABLE"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_dashboard_keeps_short_span_history_collecting(self):
        dashboard = build_dashboard_with_short_history()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        stability = dashboard["stability_trends"]
        self.assertEqual(stability["history_window"], "CURRENT_SNAPSHOT_ONLY")
        self.assertEqual(stability["history_source"], "stability_history.json")
        self.assertEqual(stability["history_sample_count"], 2)
        self.assertEqual(stability["span_validation_status"], "INSUFFICIENT_SPAN")
        self.assertLess(stability["observed_span_seconds"], stability["min_validated_span_seconds"])
        long_run = dashboard["long_run_operator_summary"]
        self.assertEqual(long_run["status"], "RUNNING_NOW")
        self.assertEqual(long_run["source"], "heartbeat.json")
        self.assertEqual(long_run["span_validation_status"], "INSUFFICIENT_SPAN")

    def test_dashboard_blocks_fake_validated_stability_history(self):
        dashboard = build_dashboard()
        dashboard["stability_trends"]["history_window"] = "VALIDATED_HISTORY"
        dashboard["stability_trends"]["history_source"] = "stability_history.json"
        dashboard["stability_trends"]["history_sample_count"] = 1
        dashboard["stability_trends"]["span_validation_status"] = "SPAN_VALIDATED"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_false_validated_long_run_without_history(self):
        dashboard = build_dashboard()
        long_run = dashboard["long_run_operator_summary"]
        long_run["status"] = "VALIDATED_STABLE"
        long_run["severity"] = "NORMAL"
        long_run["color_token"] = "green"
        long_run["source"] = "stability_history.json"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_dashboard_blocks_long_run_live_permission(self):
        dashboard = build_dashboard()
        dashboard["long_run_operator_summary"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_operator_action_live_permission(self):
        dashboard = build_dashboard()
        dashboard["operator_action_summary"]["live_order_ready"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_operator_action_dangerous_controls(self):
        dashboard = build_dashboard()
        dashboard["operator_action_summary"]["dangerous_controls_present"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_operator_action_blocker_mismatch(self):
        dashboard = build_dashboard()
        dashboard["operator_action_summary"]["primary_blocker_code"] = "API_UNVERIFIED"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_false_safe_operator_monitoring_status(self):
        dashboard = build_dashboard()
        dashboard["risk_exposure_snapshot"]["status"] = "UNVERIFIED"
        dashboard["operator_action_summary"]["status"] = "PAPER_MONITORING"
        dashboard["operator_action_summary"]["safe_to_continue_paper"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_stability_trends_scale_up_permission(self):
        dashboard = build_dashboard()
        dashboard["stability_trends"]["scale_up_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_operator_workflow_live_permission(self):
        dashboard = build_dashboard()
        dashboard["operator_workflow_summary"]["steps"][0]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_operator_workflow_step_mismatch(self):
        dashboard = build_dashboard()
        dashboard["operator_workflow_summary"]["current_step"] = "RUN_PAPER"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_operator_workflow_unblocked_live_step(self):
        dashboard = build_dashboard()
        dashboard["operator_workflow_summary"]["steps"][-1]["status"] = "WAITING"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_long_run_hiding_validated_history(self):
        dashboard = build_dashboard_with_history()
        dashboard["long_run_operator_summary"]["status"] = "RUNNING_NOW"
        dashboard["long_run_operator_summary"]["color_token"] = "blue"
        dashboard["long_run_operator_summary"]["source"] = "heartbeat.json"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_false_stable_long_run_with_stale_sample(self):
        dashboard = build_dashboard_with_history()
        dashboard["stability_trends"]["degraded_sample_count"] = 1
        dashboard["stability_trends"]["stale_sample_count"] = 1
        dashboard["long_run_operator_summary"]["degraded_sample_count"] = 1
        dashboard["long_run_operator_summary"]["stale_sample_count"] = 1
        dashboard["long_run_operator_summary"]["stable_sample_count"] = 1
        dashboard["long_run_operator_summary"]["status"] = "VALIDATED_STABLE"
        dashboard["long_run_operator_summary"]["severity"] = "NORMAL"
        dashboard["long_run_operator_summary"]["color_token"] = "green"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    def test_dashboard_allows_stale_sample_overlap_with_degraded_sample(self):
        dashboard = build_dashboard()
        dashboard["stability_trends"]["status"] = "ATTENTION"
        dashboard["stability_trends"]["severity"] = "WARNING"
        dashboard["stability_trends"]["color_token"] = "yellow"
        dashboard["stability_trends"]["history_sample_count"] = 1
        dashboard["stability_trends"]["degraded_sample_count"] = 1
        dashboard["stability_trends"]["stale_sample_count"] = 1
        dashboard["long_run_operator_summary"]["status"] = "STALE"
        dashboard["long_run_operator_summary"]["severity"] = "WARNING"
        dashboard["long_run_operator_summary"]["color_token"] = "yellow"
        dashboard["long_run_operator_summary"]["source"] = "heartbeat.json"
        dashboard["long_run_operator_summary"]["history_sample_count"] = 1
        dashboard["long_run_operator_summary"]["stable_sample_count"] = 0
        dashboard["long_run_operator_summary"]["degraded_sample_count"] = 1
        dashboard["long_run_operator_summary"]["stale_sample_count"] = 1
        dashboard["runtime_evidence_boundary"]["status"] = "STALE"
        dashboard["runtime_evidence_boundary"]["actual_long_run_evidence_status"] = "STALE"
        dashboard["runtime_evidence_boundary"]["long_run_operator_status"] = "STALE"
        dashboard["runtime_evidence_boundary"]["severity"] = "WARNING"
        dashboard["runtime_evidence_boundary"]["color_token"] = "yellow"
        dashboard["runtime_evidence_boundary"]["primary_blocker_code"] = "LATENCY_TTL_EXPIRED"
        ladder = dashboard["runtime_evidence_boundary"]
        ladder["runtime_continuity_ladder_status"] = "VALUE_SNAPSHOT_ONLY"
        ladder["runtime_continuity_ladder_current_step_id"] = "CURRENT_HEARTBEAT"
        ladder["runtime_continuity_ladder_highest_passed_step_id"] = "PAPER_VALUE_SNAPSHOT"
        ladder["runtime_continuity_ladder_blocking_count"] = 4
        ladder_steps = {
            step["step_id"]: step
            for step in ladder["runtime_continuity_ladder_steps"]
        }
        ladder_steps["CURRENT_HEARTBEAT"]["status"] = "STALE"
        ladder_steps["CURRENT_HEARTBEAT"]["blocks_live_review_until_pass"] = True
        ladder_steps["ACTUAL_LONG_RUN_VALIDATED"]["status"] = "STALE"
        ladder_steps["ACTUAL_LONG_RUN_VALIDATED"]["blocks_live_review_until_pass"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")

    def test_dashboard_missing_paper_portfolio_stays_unverified(self):
        dashboard = build_dashboard(with_paper_portfolio=False)
        result = validate_read_only_dashboard_shell(dashboard)
        html = render_dashboard_html(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["portfolio_snapshot"]["status"], "UNVERIFIED")
        self.assertEqual(dashboard["portfolio_snapshot"]["configured_paper_capital"]["value_display"], "1,000,000 KRW")
        self.assertEqual(dashboard["portfolio_snapshot"]["configured_paper_capital"]["freshness_status"], "PASS")
        self.assertIn("Configured PAPER Capital", dashboard["portfolio_snapshot"]["configured_paper_capital"]["label"])
        self.assertIn("Known PAPER configuration baseline", dashboard["portfolio_snapshot"]["configured_paper_capital"]["detail"])
        self.assertIn("Configured PAPER capital is 1,000,000 KRW", dashboard["portfolio_snapshot"]["source_snapshot_freshness_message"])
        self.assertIn("configured PAPER capital is not exchange balance", dashboard["portfolio_snapshot"]["next_action"])
        self.assertEqual(dashboard["portfolio_snapshot"]["cash"]["label"], "Current Cash")
        self.assertEqual(dashboard["portfolio_snapshot"]["equity"]["label"], "Current Equity")
        self.assertEqual(dashboard["portfolio_snapshot"]["return_pct"]["label"], "Current Return")
        self.assertEqual(dashboard["portfolio_snapshot"]["cash"]["value_display"], "UNVERIFIED")
        self.assertIn("Current cash is UNVERIFIED", dashboard["portfolio_snapshot"]["cash"]["detail"])
        self.assertIn("Current equity is UNVERIFIED", dashboard["portfolio_snapshot"]["equity"]["detail"])
        self.assertEqual(dashboard["portfolio_snapshot"]["realized_pnl"]["value_display"], "UNVERIFIED")
        self.assertEqual(dashboard["operation_status"]["severity"], "WARNING")
        self.assertEqual(dashboard["operation_status"]["color_token"], "yellow")
        self.assertEqual(dashboard["operation_status"]["label"], "Running without verified portfolio")
        self.assertIn("portfolio", dashboard["operation_status"]["message"])
        self.assertEqual(dashboard["operation_status"]["portfolio_status"], "UNVERIFIED")
        self.assertEqual(dashboard["operation_status"]["portfolio_blocking_reason"], "HARD_TRUTH_MISSING")
        self.assertEqual(dashboard["operation_status"]["portfolio_next_action"], dashboard["portfolio_snapshot"]["next_action"])
        self.assertEqual(dashboard["operation_status"]["launcher_execution_mode"], "SAFE_BOOT_OR_EXPLICIT_MONITOR")
        self.assertEqual(dashboard["operation_status"]["runtime_presence"], "DASHBOARD_HEARTBEAT_ONLY")
        self.assertIn("continuous PAPER engine", dashboard["operation_status"]["operator_meaning"])
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertIn("Current values:</strong> Needs verification", html)
        self.assertIn('title="raw portfolio status">UNVERIFIED</span>', html)
        self.assertIn("Configured PAPER Capital", html)
        self.assertIn("1,000,000 KRW", html)
        self.assertIn("Known PAPER configuration baseline", html)
        self.assertIn("UNVERIFIED applies to current cash, equity", html)
        self.assertIn("current cash, equity, PnL, and return require a fresh verified simulated ledger snapshot", html)

    def test_dashboard_blocks_operation_status_without_runtime_presence_warning(self):
        dashboard = build_dashboard()
        dashboard["operation_status"]["operator_meaning"] = "Everything is running."
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_normal_operation_when_portfolio_is_unverified(self):
        dashboard = build_dashboard(with_paper_portfolio=False)
        dashboard["operation_status"]["status"] = "RUNNING_SAFE_MODE"
        dashboard["operation_status"]["severity"] = "NORMAL"
        dashboard["operation_status"]["color_token"] = "green"
        dashboard["operation_status"]["label"] = "Running safely"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_first_screen_expands_portfolio_positions_and_candidates(self):
        summary, heartbeat, startup_probe = build_inputs()
        summary["portfolio"]["realized_pnl"] = 12500
        summary["portfolio"]["unrealized_pnl"] = -2500
        summary["portfolio"]["locked_balance"] = 10000
        summary["positions"] = [
            {
                "symbol": "KRW-BTC",
                "side": "LONG",
                "quantity": "0.01",
                "avg_price": "100000000",
                "mark_price": "99900000",
                "market_value": "999000",
                "cost_basis": "1000000",
                "unrealized_pnl": "-2500 KRW",
            }
        ]
        summary["entry_candidates"] = [{"symbol": "KRW-ETH"}, {"symbol": "KRW-XRP"}]
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        portfolio = dashboard["portfolio_snapshot"]
        self.assertEqual(portfolio["locked_cash"]["value_display"], "10,000 KRW")
        self.assertEqual(portfolio["realized_pnl"]["value_display"], "+12,500 KRW")
        self.assertEqual(portfolio["unrealized_pnl"]["value_display"], "-2,500 KRW")
        self.assertEqual(portfolio["total_pnl"]["value_display"], "+10,000 KRW")
        self.assertEqual(portfolio["entry_candidates"]["value_display"], "2")
        self.assertIsNone(portfolio["source_runtime_cycle_id"])
        self.assertIsNone(portfolio["source_paper_ledger_head_hash"])
        self.assertIsInstance(portfolio["source_snapshot_age_seconds"], int)
        self.assertEqual(portfolio["source_snapshot_stale_after_seconds"], 300)
        self.assertIn("display-only", portfolio["source_snapshot_freshness_message"])
        html = render_dashboard_html(dashboard)
        self.assertIn("portfolio-kpi-grid", html)
        self.assertIn("portfolio-ledger", html)
        self.assertIn("Portfolio Details", html)
        self.assertIn("portfolio-detail-grid", html)
        self.assertIn("Held Positions", html)
        self.assertIn("KRW-BTC | LONG | qty 0.01 | avg 100000000 | mark 99900000 | value 999000 | PnL -2500 KRW", html)
        self.assertIn("Mark Price", html)
        self.assertIn("Market Value", html)
        self.assertIn("Cost Basis", html)
        self.assertIn("Entry Candidates", html)
        self.assertIn("KRW-ETH", html)
        self.assertIn("KRW-XRP", html)
        self.assertIn("table-wrap", html)

    def test_dashboard_position_detail_reads_paper_portfolio_fill_fields(self):
        session_id = "test_read_only_dashboard_position_fill"
        paper_portfolio = build_paper_portfolio_snapshot_from_fill(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            session_id=session_id,
            symbol="KRW-BTC",
            side="BUY",
            quantity="0.01",
            fill_price="1000500",
            mark_price="1000000",
            fee_amount="5",
            source_runtime_cycle_id="dashboard-position-fill-cycle",
            source_paper_ledger_head_hash="D" * 64,
        )
        summary, heartbeat, startup_probe = build_inputs(
            session_id=session_id,
            paper_portfolio_snapshot=paper_portfolio,
        )
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id=session_id,
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["portfolio_snapshot"]["positions"]["value_display"], "1")
        self.assertEqual(dashboard["portfolio_snapshot"]["source_runtime_cycle_id"], "dashboard-position-fill-cycle")
        self.assertEqual(dashboard["portfolio_snapshot"]["source_paper_ledger_head_hash"], "D" * 64)
        self.assertEqual(dashboard["portfolio_snapshot"]["source_snapshot_hash"], paper_portfolio["snapshot_hash"])
        self.assertEqual(dashboard["portfolio_snapshot"]["source_snapshot_status"], "PASS")
        self.assertEqual(
            dashboard["portfolio_snapshot"]["source_snapshot_generated_at_utc"],
            paper_portfolio["generated_at_utc"],
        )
        self.assertEqual(dashboard["portfolio_snapshot"]["source_balance_kind"], "SIMULATED_PAPER_LEDGER")
        self.assertEqual(
            dashboard["portfolio_snapshot"]["paper_value_truth_status"],
            "PAPER_LEDGER_CURRENT_VALUES_VERIFIED",
        )
        self.assertEqual(
            dashboard["portfolio_snapshot"]["runtime_continuity_status"],
            "SNAPSHOT_ONLY_NOT_LONG_RUN_PROOF",
        )
        self.assertEqual(
            dashboard["portfolio_snapshot"]["audited_writer_lifecycle_status"],
            "SUMMARY_LEDGER_ONLY_NO_AUDITED_WRITER",
        )
        self.assertIsInstance(dashboard["portfolio_snapshot"]["source_snapshot_age_seconds"], int)
        self.assertEqual(dashboard["portfolio_snapshot"]["source_snapshot_stale_after_seconds"], 300)
        rows = dashboard["position_snapshot"]["rows"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["symbol"], "KRW-BTC")
        self.assertEqual(row["side"], "LONG")
        self.assertEqual(row["quantity"], "0.01")
        self.assertEqual(row["avg_price"], "1000500")
        self.assertEqual(row["mark_price"], "1000000")
        self.assertEqual(row["market_value"], "10000")
        self.assertEqual(row["cost_basis"], "10010")
        self.assertEqual(row["unrealized_pnl"], "-10")
        self.assertNotIn("UNKNOWN", row.values())
        html = render_dashboard_html(dashboard)
        self.assertIn("Runtime cycle: dashboard-position-fill-cycle", html)
        self.assertIn("Ledger head: DDDDDDDDDDDD...", html)
        self.assertIn(f"Snapshot: {paper_portfolio['snapshot_hash'][:12]}...", html)
        self.assertIn("Balance: SIMULATED_PAPER_LEDGER", html)
        self.assertIn("Age:", html)
        self.assertIn("PAPER_LEDGER_CURRENT_VALUES_VERIFIED", html)
        self.assertIn("SUMMARY_LEDGER_ONLY_NO_AUDITED_WRITER", html)
        self.assertIn("KRW-BTC | LONG | qty 0.01 | avg 1000500 | mark 1000000 | value 10000 | PnL -10", html)
        self.assertIn("<td>1000500</td>", html)
        self.assertIn("<td>1000000</td>", html)
        self.assertIn("<td>10000</td>", html)
        self.assertIn("<td>10010</td>", html)

        stale_dashboard = dict(dashboard)
        stale_dashboard["portfolio_snapshot"] = dict(dashboard["portfolio_snapshot"])
        stale_dashboard["portfolio_snapshot"]["source_snapshot_age_seconds"] = 301
        stale_dashboard["dashboard_hash"] = dashboard_shell_hash(stale_dashboard)
        stale_result = validate_read_only_dashboard_shell(stale_dashboard)
        self.assertEqual(stale_result.status, "BLOCKED")
        self.assertEqual(stale_result.blocker_code, "LATENCY_TTL_EXPIRED")

        drift_dashboard = dict(dashboard)
        drift_dashboard["portfolio_snapshot"] = dict(dashboard["portfolio_snapshot"])
        drift_dashboard["portfolio_snapshot"]["runtime_continuity_status"] = "STALE_SNAPSHOT_NOT_RUNTIME_PROOF"
        drift_dashboard["dashboard_hash"] = dashboard_shell_hash(drift_dashboard)
        drift_result = validate_read_only_dashboard_shell(drift_dashboard)
        self.assertEqual(drift_result.status, "BLOCKED")
        self.assertEqual(drift_result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_projects_paper_exposure_quality_report(self):
        dashboard = build_dashboard_with_paper_exposure_quality()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        risk = dashboard["risk_exposure_snapshot"]
        self.assertEqual(risk["status"], "LOW_RISK")
        self.assertEqual(risk["paper_exposure_quality_status"], "PASS_PAPER_ONLY")
        self.assertEqual(risk["paper_exposure_quality_source"], "paper_exposure_quality_report.json")
        self.assertEqual(risk["paper_exposure_quality_recommendation"], "KEEP_PAPER")
        self.assertEqual(risk["paper_exposure_quality_sample_display"], "160/120")
        self.assertFalse(risk["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("Paper Quality", html)
        self.assertIn("PASS_PAPER_ONLY", html)
        self.assertIn("samples=160/120", html)
        self.assertIn("KEEP_PAPER", html)
        self.assertIn("paper_exposure_quality_report.json", html)
        self.assertIn("scale-up blocked", html)

    def test_dashboard_blocks_paper_exposure_quality_live_or_scale_drift(self):
        dashboard = build_dashboard_with_paper_exposure_quality(
            paper_exposure_quality_fixture("paper_exposure_quality_scale_up_fail.json")
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        risk = dashboard["risk_exposure_snapshot"]
        self.assertEqual(risk["status"], "BLOCKED")
        self.assertEqual(risk["severity"], "ERROR")
        self.assertEqual(risk["color_token"], "red")
        self.assertEqual(risk["paper_exposure_quality_status"], "BLOCKED_RECOVERY_REVIEW")
        self.assertEqual(risk["paper_exposure_quality_blocker_code"], "LIVE_FINAL_GUARD_FAILED")
        self.assertFalse(risk["live_order_ready"])
        self.assertFalse(risk["live_order_allowed"])
        self.assertFalse(risk["can_live_trade"])
        self.assertFalse(risk["scale_up_allowed"])

    def test_stale_summary_demotes_paper_portfolio_values(self):
        summary, heartbeat, startup_probe = build_inputs()
        summary["generated_at_utc"] = "2000-01-01T00:00:00Z"
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["source_artifacts"][0]["freshness_status"], "STALE")
        self.assertEqual(dashboard["portfolio_snapshot"]["status"], "STALE")
        self.assertEqual(dashboard["portfolio_snapshot"]["configured_paper_capital"]["value_display"], "1,000,000 KRW")
        self.assertEqual(dashboard["portfolio_snapshot"]["configured_paper_capital"]["freshness_status"], "PASS")
        self.assertEqual(dashboard["portfolio_snapshot"]["cash"]["value_display"], "UNVERIFIED")
        self.assertEqual(dashboard["portfolio_snapshot"]["cash"]["freshness_status"], "STALE")
        self.assertEqual(
            dashboard["portfolio_snapshot"]["paper_value_truth_status"],
            "CURRENT_VALUES_UNVERIFIED_CONFIGURED_BASELINE_ONLY",
        )
        self.assertEqual(dashboard["portfolio_snapshot"]["runtime_continuity_status"], "NO_CURRENT_RUNTIME_PROOF")
        self.assertEqual(
            dashboard["portfolio_snapshot"]["audited_writer_lifecycle_status"],
            "NO_AUDITED_WRITER_EVIDENCE",
        )
        self.assertEqual(dashboard["portfolio_snapshot"]["blocking_reason"], "LATENCY_TTL_EXPIRED")
        self.assertEqual(dashboard["operation_status"]["severity"], "WARNING")
        self.assertEqual(dashboard["operation_status"]["color_token"], "yellow")
        self.assertEqual(dashboard["operation_status"]["label"], "Running with stale portfolio")
        self.assertIn("portfolio", dashboard["operation_status"]["message"])
        self.assertEqual(dashboard["operation_status"]["portfolio_status"], "STALE")
        self.assertEqual(dashboard["operation_status"]["portfolio_blocking_reason"], "LATENCY_TTL_EXPIRED")
        self.assertEqual(dashboard["operation_status"]["portfolio_next_action"], dashboard["portfolio_snapshot"]["next_action"])
        self.assertEqual(dashboard["risk_exposure_snapshot"]["status"], "STALE")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["color_token"], "yellow")
        self.assertEqual(dashboard["risk_exposure_snapshot"]["exposure_pct_display"], "UNVERIFIED")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["status"], "STALE")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["color_token"], "yellow")
        self.assertEqual(dashboard["execution_feedback_snapshot"]["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertEqual(dashboard["exploration_policy_status"]["status"], "STALE")
        self.assertEqual(dashboard["exploration_policy_status"]["color_token"], "yellow")
        self.assertFalse(dashboard["exploration_policy_status"]["exploitation_allowed_for_paper_ranking"])

    def test_future_clock_skew_demotes_paper_portfolio_values(self):
        summary, heartbeat, startup_probe = build_inputs()
        summary["generated_at_utc"] = "2999-01-01T00:00:00Z"
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=heartbeat,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["source_artifacts"][0]["freshness_status"], "STALE")
        self.assertEqual(dashboard["portfolio_snapshot"]["status"], "STALE")
        self.assertEqual(dashboard["portfolio_snapshot"]["next_action"], "Rerun PAPER to refresh dashboard portfolio values before review")

    def test_dashboard_blocks_forbidden_wording(self):
        dashboard = build_dashboard()
        dashboard["panels"][0]["message"] = "profit guaranteed"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_missing_source_stays_no_trade(self):
        summary, _, startup_probe = build_inputs()
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard",
            summary=summary,
            heartbeat=None,
            startup_probe=startup_probe,
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(dashboard["final_action"], "NO_TRADE")
        self.assertIsNotNone(dashboard["blocking_reason"])
        self.assertEqual(dashboard["operation_status"]["severity"], "WARNING")
        self.assertEqual(dashboard["operation_status"]["color_token"], "yellow")
        self.assertIn("Heartbeat", dashboard["operation_status"]["message"])
        self.assertIn("Rerun the PAPER launcher", dashboard["operation_status"]["recovery_hint"])
        self.assertEqual(dashboard["stability_trends"]["status"], "ATTENTION")
        self.assertEqual(dashboard["stability_trends"]["color_token"], "yellow")
        self.assertEqual(dashboard["long_run_operator_summary"]["status"], "STALE")
        self.assertEqual(dashboard["long_run_operator_summary"]["color_token"], "yellow")

    def test_dashboard_schema_metric_count_matches_runtime_metrics(self):
        schema = json.loads((ROOT / "contracts" / "schema" / "read_only_dashboard_shell.schema.json").read_text(encoding="utf-8"))
        metric_schema = schema["$defs"]["stability_trends"]["properties"]["metrics"]
        dashboard = build_dashboard()
        metric_count = len(dashboard["stability_trends"]["metrics"])
        self.assertEqual(metric_schema["minItems"], metric_count)
        self.assertEqual(metric_schema["maxItems"], metric_count)

    def test_dashboard_can_show_shadow_runtime_writer_as_display_only_source(self):
        dashboard = build_dashboard_with_shadow_runtime_writer()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        writer_sources = [source for source in dashboard["source_artifacts"] if source["artifact_id"] == "SHADOW_RUNTIME_WRITER"]
        self.assertEqual(len(writer_sources), 1)
        self.assertEqual(writer_sources[0]["filename"], "shadow_observation_runtime_artifact_writer_report.json")
        self.assertEqual(writer_sources[0]["freshness_status"], "PASS")
        self.assertEqual(writer_sources[0]["truth_role"], "dashboard_serving_truth")
        self.assertFalse(dashboard["live_order_allowed"])
        self.assertFalse(dashboard["can_live_trade"])
        self.assertFalse(dashboard["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("SHADOW_RUNTIME_WRITER=PASS", html)
        self.assertIn("shadow_observation_runtime_artifact_writer_report.json", html)
        self.assertIn("Dashboard display truth only", html)

    def test_dashboard_shows_shadow_runtime_harness_without_live_permission(self):
        dashboard = build_dashboard_with_shadow_runtime_harness()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        harness_sources = [source for source in dashboard["source_artifacts"] if source["artifact_id"] == "SHADOW_RUNTIME_HARNESS"]
        self.assertEqual(len(harness_sources), 1)
        self.assertEqual(harness_sources[0]["filename"], "actual_runtime_harness_report.json")
        self.assertEqual(harness_sources[0]["freshness_status"], "PASS")
        self.assertEqual(harness_sources[0]["truth_role"], "dashboard_serving_truth")
        harness = dashboard["shadow_runtime_harness_status"]
        self.assertEqual(harness["status"], "SHORT_WINDOW_EXECUTED")
        self.assertEqual(harness["color_token"], "blue")
        self.assertTrue(harness["actual_non_live_runtime_harness_executed"])
        self.assertEqual(harness["runtime_evidence_status"], "BLOCKED_LONG_RUN_EVIDENCE_MISSING")
        self.assertFalse(harness["long_run_evidence_eligible"])
        self.assertEqual(harness["optimizer_input_role"], "BLOCKER_ONLY_NOT_RANKING_INPUT")
        self.assertFalse(harness["live_order_allowed"])
        self.assertFalse(harness["can_live_trade"])
        self.assertFalse(harness["scale_up_allowed"])
        html = render_dashboard_html(dashboard)
        self.assertIn("SHADOW_RUNTIME_HARNESS=PASS", html)
        self.assertIn("actual_runtime_harness_report.json", html)
        self.assertIn("PAPER/SHADOW check", html)
        self.assertIn("Short Window Executed", html)
        self.assertIn("not execution truth and not LIVE_READY evidence", html)
        self.assertIn("long_run_evidence_eligible=false", html)

    def test_dashboard_shows_persistent_runtime_stub_as_not_long_run_evidence(self):
        dashboard = build_dashboard_with_shadow_persistent_runtime()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        persistent_sources = [
            source for source in dashboard["source_artifacts"] if source["artifact_id"] == "SHADOW_PERSISTENT_RUNTIME"
        ]
        self.assertEqual(len(persistent_sources), 1)
        self.assertEqual(persistent_sources[0]["filename"], "shadow_observation_persistent_runtime_report.json")
        self.assertEqual(persistent_sources[0]["freshness_status"], "PASS")
        self.assertEqual(persistent_sources[0]["truth_role"], "dashboard_serving_truth")

        persistent = dashboard["shadow_persistent_runtime_status"]
        self.assertEqual(persistent["status"], "STUB_ONLY")
        self.assertEqual(persistent["severity"], "WARNING")
        self.assertEqual(persistent["color_token"], "yellow")
        self.assertEqual(persistent["runtime_duration_evidence_source"], "STUB_ESTIMATE_ONLY")
        self.assertEqual(persistent["duration_evidence_role"], "NOT_LONG_RUN_EVIDENCE")
        self.assertEqual(persistent["estimated_runtime_seconds"], 90)
        self.assertEqual(persistent["observed_runtime_seconds"], 0)
        self.assertFalse(persistent["actual_persistent_runtime_executed"])
        self.assertFalse(persistent["long_run_evidence_eligible"])
        self.assertEqual(persistent["primary_blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(persistent["live_order_ready"])
        self.assertFalse(persistent["live_order_allowed"])
        self.assertFalse(persistent["can_live_trade"])
        self.assertFalse(persistent["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("SHADOW_PERSISTENT_RUNTIME=PASS", html)
        self.assertIn("Persistent Runtime Evidence", html)
        self.assertIn("STUB_ESTIMATE_ONLY", html)
        self.assertIn("NOT_LONG_RUN_EVIDENCE", html)
        self.assertIn("estimated=90s", html)
        self.assertIn("observed=0s", html)
        self.assertIn("Estimated runtime is a stub calculation only", html)
        self.assertIn("Runtime Evidence Boundary", html)
        self.assertIn("Actual long-run evidence", html)
        self.assertIn("Long-Run Evidence Requirements", html)
        self.assertIn("Persistent runtime source", html)
        self.assertIn("Runtime source pairing", html)
        self.assertIn("live_review_evidence_eligible=false", html)

        boundary = dashboard["runtime_evidence_boundary"]
        self.assertEqual(boundary["status"], "ACTUAL_LONG_RUN_COLLECTING")
        self.assertEqual(boundary["actual_long_run_evidence_status"], "COLLECTING")
        self.assertEqual(boundary["stub_runtime_evidence_status"], "STUB_ONLY")
        self.assertIn("not actual long-run evidence", boundary["stub_boundary_message"])
        self.assertFalse(boundary["live_review_evidence_eligible"])
        self.assertFalse(boundary["live_order_allowed"])
        self.assertFalse(boundary["can_live_trade"])
        self.assertFalse(boundary["scale_up_allowed"])
        requirements = {item["requirement_id"]: item for item in boundary["evidence_requirements"]}
        self.assertEqual(requirements["PERSISTENT_RUNTIME_SOURCE"]["status"], "PASS")
        self.assertEqual(requirements["SHORT_WINDOW_HARNESS_SOURCE"]["status"], "MISSING")
        self.assertEqual(requirements["RUNTIME_ORCHESTRATION_SOURCE_PAIRING"]["status"], "MISSING")
        self.assertEqual(requirements["ACTUAL_RUNTIME_DURATION"]["status"], "COLLECTING")

    def test_dashboard_projects_paper_persistent_loop_as_bounded_runtime_evidence(self):
        dashboard = build_dashboard_with_paper_persistent_loop()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        loop_sources = [source for source in dashboard["source_artifacts"] if source["artifact_id"] == "PAPER_PERSISTENT_LOOP"]
        self.assertEqual(len(loop_sources), 1)
        self.assertEqual(loop_sources[0]["filename"], "upbit_paper_persistent_loop_report.json")
        self.assertEqual(loop_sources[0]["freshness_status"], "PASS")
        self.assertEqual(loop_sources[0]["truth_role"], "dashboard_serving_truth")

        loop_status = dashboard["paper_persistent_loop_status"]
        self.assertEqual(loop_status["status"], "PASS")
        self.assertEqual(loop_status["runtime_evidence_role"], "BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE")
        self.assertEqual(loop_status["completed_cycle_count"], 1)
        self.assertTrue(loop_status["actual_paper_runtime_executed"])
        self.assertTrue(loop_status["current_evidence_write_allowed"])
        self.assertTrue(loop_status["paper_runtime_resume_allowed"])
        self.assertFalse(loop_status["long_run_evidence_eligible"])
        self.assertFalse(loop_status["promotion_eligible"])
        self.assertFalse(loop_status["live_order_ready"])
        self.assertFalse(loop_status["live_order_allowed"])
        self.assertFalse(loop_status["can_live_trade"])
        self.assertFalse(loop_status["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        self.assertIn("PAPER_PERSISTENT_LOOP=PASS", html)
        self.assertIn("PAPER Persistent Runtime", html)
        self.assertIn("BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE", html)
        self.assertIn("Display-only bounded PAPER loop status", html)

    def test_dashboard_blocks_paper_persistent_loop_live_or_long_run_drift(self):
        dashboard = build_dashboard_with_paper_persistent_loop()
        dashboard["paper_persistent_loop_status"]["long_run_evidence_eligible"] = True
        dashboard["paper_persistent_loop_status"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_runtime_evidence_boundary_false_validated_long_run(self):
        dashboard = build_dashboard_with_shadow_persistent_runtime()
        dashboard["runtime_evidence_boundary"]["status"] = "ACTUAL_LONG_RUN_VALIDATED"
        dashboard["runtime_evidence_boundary"]["actual_long_run_evidence_status"] = "VALIDATED_STABLE"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_runtime_evidence_boundary_live_review_drift(self):
        dashboard = build_dashboard_with_shadow_persistent_runtime()
        dashboard["runtime_evidence_boundary"]["live_review_evidence_eligible"] = True
        dashboard["runtime_evidence_boundary"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_runtime_continuity_ladder_live_or_gap_claim(self):
        dashboard = build_dashboard_with_shadow_persistent_runtime()
        ladder = dashboard["runtime_evidence_boundary"]
        ladder["runtime_continuity_ladder_live_review_allowed"] = True
        ladder["runtime_continuity_ladder_gap_closure_allowed"] = True
        ladder["runtime_continuity_ladder_steps"][0]["counts_as_live_ready_evidence"] = True
        ladder["runtime_continuity_ladder_steps"][0]["counts_as_gap_closure_evidence"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_runtime_continuity_ladder_source_drift(self):
        dashboard = build_dashboard_with_shadow_runtime_harness()
        steps = {
            step["step_id"]: step
            for step in dashboard["runtime_evidence_boundary"]["runtime_continuity_ladder_steps"]
        }
        steps["SHORT_WINDOW_PAPER_SHADOW_CHECK"]["status"] = "MISSING"
        dashboard["runtime_evidence_boundary"]["runtime_continuity_ladder_blocking_count"] += 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_runtime_evidence_boundary_source_status_drift(self):
        dashboard = build_dashboard_with_shadow_runtime_harness()
        dashboard["runtime_evidence_boundary"]["short_window_evidence_status"] = "NOT_LOADED"
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_runtime_evidence_requirement_false_pass(self):
        dashboard = build_dashboard()
        requirements = {
            item["requirement_id"]: item
            for item in dashboard["runtime_evidence_boundary"]["evidence_requirements"]
        }
        requirements["ACTUAL_RUNTIME_DURATION"]["status"] = "PASS"
        dashboard["runtime_evidence_boundary"]["evidence_requirements_blocking_count"] -= 1
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_runtime_evidence_requirement_missing_checklist(self):
        dashboard = build_dashboard()
        del dashboard["runtime_evidence_boundary"]["evidence_requirements"]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_shows_runtime_orchestration_guard_as_display_only(self):
        dashboard = build_dashboard_with_shadow_runtime_orchestration()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        sources = [source for source in dashboard["source_artifacts"] if source["artifact_id"] == "SHADOW_RUNTIME_ORCHESTRATION"]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["filename"], "runtime_orchestration_report.json")
        self.assertEqual(sources[0]["freshness_status"], "PASS")
        self.assertEqual(sources[0]["truth_role"], "dashboard_serving_truth")

        orchestration = dashboard["shadow_runtime_orchestration_status"]
        self.assertEqual(orchestration["status"], "BOUNDARY_VERIFIED")
        self.assertEqual(orchestration["severity"], "NORMAL")
        self.assertEqual(orchestration["color_token"], "blue")
        self.assertEqual(orchestration["source_validation_status"], "PASS")
        self.assertTrue(orchestration["source_runtime_hash_pairing_verified"])
        self.assertEqual(orchestration["source_binding_count"], 2)
        self.assertEqual(orchestration["persistent_runtime_status"], "STUB_ONLY")
        self.assertEqual(orchestration["short_window_harness_status"], "SHORT_WINDOW_EXECUTED")
        self.assertEqual(orchestration["observed_actual_runtime_seconds"], 0)
        self.assertEqual(orchestration["observed_actual_cycle_count"], 0)
        self.assertEqual(orchestration["observed_evidence_window_count"], 0)
        self.assertEqual(orchestration["runtime_evidence_role"], "ORCHESTRATION_BLOCKER_ONLY_NOT_LONG_RUN")
        self.assertEqual(orchestration["optimizer_ranking_action"], "BLOCK_RANKING")
        self.assertFalse(orchestration["scorecard_input_eligible"])
        self.assertFalse(orchestration["promotion_eligible"])
        self.assertFalse(orchestration["live_order_allowed"])
        self.assertFalse(orchestration["can_live_trade"])
        self.assertFalse(orchestration["scale_up_allowed"])
        runtime_requirements = {
            item["requirement_id"]: item
            for item in dashboard["runtime_evidence_boundary"]["evidence_requirements"]
        }
        self.assertEqual(runtime_requirements["PERSISTENT_RUNTIME_SOURCE"]["status"], "PASS")
        self.assertEqual(runtime_requirements["SHORT_WINDOW_HARNESS_SOURCE"]["status"], "PASS")
        self.assertEqual(runtime_requirements["RUNTIME_ORCHESTRATION_SOURCE_PAIRING"]["status"], "PASS")
        self.assertEqual(runtime_requirements["ACTUAL_RUNTIME_DURATION"]["status"], "COLLECTING")
        self.assertEqual(dashboard["runtime_evidence_boundary"]["evidence_requirements_blocking_count"], 4)

        html = render_dashboard_html(dashboard)
        self.assertIn("Runtime Orchestration Guard", html)
        self.assertIn("Source Pairing", html)
        self.assertIn("pairing=True", html)
        self.assertIn("optimizer ranking block ranking", html)
        self.assertIn("Display-only source pairing guard", html)

    def test_dashboard_blocks_runtime_orchestration_without_source_artifact(self):
        dashboard = build_dashboard_with_shadow_runtime_orchestration()
        dashboard["source_artifacts"] = [
            source for source in dashboard["source_artifacts"] if source["artifact_id"] != "SHADOW_RUNTIME_ORCHESTRATION"
        ]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_runtime_orchestration_live_scorecard_or_runtime_drift(self):
        dashboard = build_dashboard_with_shadow_runtime_orchestration()
        dashboard["shadow_runtime_orchestration_status"]["observed_actual_runtime_seconds"] = 3600
        dashboard["shadow_runtime_orchestration_status"]["scorecard_input_eligible"] = True
        dashboard["shadow_runtime_orchestration_status"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_persistent_runtime_stub_observed_duration_drift(self):
        report = shadow_persistent_runtime_fixture("test-dashboard-shadow-persistent-observed-drift")
        report["observed_runtime_seconds"] = 90
        dashboard = build_dashboard_with_shadow_persistent_runtime(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        persistent = dashboard["shadow_persistent_runtime_status"]
        self.assertEqual(persistent["status"], "BLOCKED")
        self.assertEqual(persistent["severity"], "ERROR")
        self.assertEqual(persistent["color_token"], "red")
        self.assertEqual(persistent["primary_blocker_code"], "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
        self.assertFalse(persistent["live_order_allowed"])
        self.assertFalse(persistent["can_live_trade"])
        self.assertFalse(persistent["scale_up_allowed"])

    def test_dashboard_blocks_persistent_runtime_source_report_status_drift(self):
        report = shadow_persistent_runtime_fixture("test-dashboard-shadow-persistent-source-status-drift")
        report["runtime_status"] = "BLOCKED"
        report["source_scheduler_guard_status"] = "BLOCKED"
        report["source_scheduler_validation_status"] = "BLOCKED"
        report["primary_blocker_code"] = "DATA_QUALITY_INSUFFICIENT"
        dashboard = build_dashboard_with_shadow_persistent_runtime(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        persistent = dashboard["shadow_persistent_runtime_status"]
        self.assertEqual(persistent["status"], "BLOCKED")
        self.assertEqual(persistent["severity"], "ERROR")
        self.assertEqual(persistent["color_token"], "red")
        self.assertEqual(persistent["primary_blocker_code"], "DATA_QUALITY_INSUFFICIENT")
        self.assertFalse(persistent["live_order_allowed"])
        self.assertFalse(persistent["can_live_trade"])
        self.assertFalse(persistent["scale_up_allowed"])

    def test_dashboard_blocks_persistent_runtime_budget_drift(self):
        report = shadow_persistent_runtime_fixture("test-dashboard-shadow-persistent-budget-drift")
        report["max_runtime_seconds"] = 60
        report["runtime_report_hash"] = shadow_observation_persistent_runtime_hash(report)
        dashboard = build_dashboard_with_shadow_persistent_runtime(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")
        persistent = dashboard["shadow_persistent_runtime_status"]
        self.assertEqual(persistent["status"], "BLOCKED")
        self.assertEqual(persistent["severity"], "ERROR")
        self.assertEqual(persistent["color_token"], "red")
        self.assertEqual(persistent["primary_blocker_code"], "RESOURCE_LIMIT_BLOCK")
        self.assertFalse(persistent["long_run_evidence_eligible"])
        self.assertFalse(persistent["live_order_allowed"])
        self.assertFalse(persistent["can_live_trade"])
        self.assertFalse(persistent["scale_up_allowed"])

    def test_dashboard_blocks_persistent_runtime_without_source_artifact(self):
        dashboard = build_dashboard_with_shadow_persistent_runtime()
        dashboard["source_artifacts"] = [
            source for source in dashboard["source_artifacts"] if source["artifact_id"] != "SHADOW_PERSISTENT_RUNTIME"
        ]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_persistent_runtime_live_or_long_run_drift(self):
        dashboard = build_dashboard_with_shadow_persistent_runtime()
        dashboard["shadow_persistent_runtime_status"]["actual_persistent_runtime_executed"] = True
        dashboard["shadow_persistent_runtime_status"]["long_run_evidence_eligible"] = True
        dashboard["shadow_persistent_runtime_status"]["live_order_allowed"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_blocks_shadow_runtime_harness_without_source_artifact(self):
        dashboard = build_dashboard_with_shadow_runtime_harness()
        dashboard["source_artifacts"] = [
            source for source in dashboard["source_artifacts"] if source["artifact_id"] != "SHADOW_RUNTIME_HARNESS"
        ]
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "HARD_TRUTH_MISSING")

    def test_dashboard_blocks_shadow_runtime_harness_source_when_status_not_loaded(self):
        dashboard = build_dashboard()
        dashboard["source_artifacts"].append(
            {
                "artifact_id": "SHADOW_RUNTIME_HARNESS",
                "path": "system/runtime/upbit/krw_spot/shadow/test/actual_runtime_harness_report.json",
                "filename": "actual_runtime_harness_report.json",
                "truth_role": "dashboard_serving_truth",
                "loaded": True,
                "freshness_status": "PASS",
            }
        )
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_blocks_shadow_runtime_harness_live_or_long_run_drift(self):
        dashboard = build_dashboard_with_shadow_runtime_harness()
        dashboard["shadow_runtime_harness_status"]["live_order_allowed"] = True
        dashboard["shadow_runtime_harness_status"]["long_run_evidence_eligible"] = True
        dashboard["dashboard_hash"] = dashboard_shell_hash(dashboard)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_marks_negative_shadow_harness_measurement_as_error(self):
        report = build_shadow_observation_actual_runtime_harness_report(
            harness_id="test-dashboard-shadow-runtime-negative-runtime",
            requested_cycle_count=3,
            completed_cycle_count=3,
            measured_runtime_seconds=-1,
            runtime_measurement_source="MONOTONIC_LOCAL_TIMER_VERIFIED",
            monotonic_timer_started=True,
            monotonic_timer_stopped=True,
            measured_runtime_seconds_verified=True,
        )
        dashboard = build_dashboard_with_shadow_runtime_harness(report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS")

        harness = dashboard["shadow_runtime_harness_status"]
        self.assertEqual(harness["status"], "BLOCKED")
        self.assertEqual(harness["severity"], "ERROR")
        self.assertEqual(harness["color_token"], "red")
        self.assertEqual(harness["primary_blocker_code"], "DATA_QUALITY_INSUFFICIENT")
        self.assertIn("invalid negative runtime measurements", harness["one_line_summary"])
        self.assertFalse(harness["live_order_allowed"])
        self.assertFalse(harness["can_live_trade"])
        self.assertFalse(harness["scale_up_allowed"])

    def test_dashboard_html_has_no_order_controls(self):
        html = render_dashboard_html(build_dashboard())
        self.assertIn("System Status", html)
        self.assertIn("Running safely", html)
        self.assertIn("Program heartbeat is fresh", html)
        self.assertIn("Launcher mode", html)
        self.assertIn("SAFE_BOOT_OR_EXPLICIT_MONITOR", html)
        self.assertIn("Runtime presence", html)
        self.assertIn("DASHBOARD_HEARTBEAT_ONLY", html)
        self.assertIn("continuous PAPER engine", html)
        self.assertIn("body { margin: 0; max-width: 100%; overflow-x: hidden; background: #f7f8fa; color: #1d2430; font-size: 16px; line-height: 1.5; }", html)
        self.assertIn("main { display: grid; gap: 18px; padding: 18px; width: 100%; max-width: 1440px; margin: 0 auto; }", html)
        self.assertIn("h1, h2, h3, p, dl, dd, small, strong, span { overflow-wrap: anywhere; word-break: normal; }", html)
        self.assertIn("p, small, li, dd, td { line-height: 1.5; }", html)
        self.assertIn(".metric, .scope-item, .guard, .decision-grid div, .workflow-step, .dependency-check, .evidence-check, .maturity-component, .stability-metric { display: grid; align-content: start; gap: 6px; }", html)
        self.assertIn(".operator-decision-surface { display: grid; gap: 12px;", html)
        self.assertIn(".decision-surface-head { display: flex; flex-wrap: wrap;", html)
        self.assertIn(".operator-answer-grid { display: grid; gap: 18px; grid-template-columns: minmax(min(100%, 300px), 0.9fr) minmax(min(100%, 420px), 1.35fr) minmax(min(100%, 280px), 0.85fr);", html)
        self.assertIn(".operator-quick-status { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 190px), 1fr));", html)
        self.assertIn(".operator-answer-card { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 18px;", html)
        self.assertIn(".answer-signal-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));", html)
        self.assertIn(".summary-card .portfolio-kpi-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 160px), 1fr));", html)
        self.assertIn(".portfolio-ledger { display: grid; gap: 0; grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr));", html)
        self.assertIn('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">', html)
        self.assertIn(".portfolio-detail-grid { display: grid; gap: 12px;", html)
        self.assertIn(".maturity-component-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr)); gap: 14px;", html)
        self.assertIn(".dependency-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr)); gap: 12px;", html)
        self.assertIn(".evidence-check-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 12px;", html)
        self.assertIn(".pill { display: inline-flex; align-items: center; max-width: 100%;", html)
        self.assertIn("white-space: normal; overflow-wrap: anywhere; text-align: left;", html)
        self.assertIn('class="operation-copy"', html)
        self.assertIn(".operation { display: grid; gap: 16px; grid-template-columns: 1fr;", html)
        self.assertIn(".operation p { line-height: 1.5;", html)
        self.assertIn(".operation dl { display: grid; column-gap: 36px; row-gap: 16px;", html)
        self.assertIn("repeat(auto-fit, minmax(min(100%, 210px), 1fr))", html)
        self.assertIn(".operation dd:not(.pill) { font-size: 14px;", html)
        self.assertIn(".portfolio-head { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start;", html)
        self.assertIn("vertical-align: top", html)
        self.assertIn("Recovery:", html)
        self.assertIn("No recovery needed", html)
        self.assertIn("Stability Trends", html)
        self.assertIn("Current Snapshot Only", html)
        self.assertIn("samples=0", html)
        self.assertIn("Heartbeat age", html)
        self.assertIn("Source freshness", html)
        self.assertIn("Runtime artifact pressure", html)
        self.assertIn("Event latency", html)
        self.assertIn("Queue backlog", html)
        self.assertIn("Rate-limit pressure", html)
        self.assertIn("stability-green", html)
        self.assertIn("Long-Run Operation", html)
        self.assertIn("Running Now", html)
        self.assertIn("longrun-blue", html)
        self.assertIn("Market Data Continuity", html)
        self.assertIn("market-data-yellow", html)
        self.assertIn("History Samples", html)
        self.assertIn("Latency / Refresh", html)
        self.assertIn("Resources / Retry", html)
        self.assertIn("Display-only operating summary", html)
        self.assertIn("What To Do Now", html)
        self.assertIn("Resolve dashboard blocker", html)
        self.assertIn("operator-action-yellow", html)
        self.assertIn("PAPER review only", html)
        self.assertIn("LIVE blocked", html)
        self.assertIn("no order buttons", html)
        self.assertIn("Ledger &amp; Reconciliation", html)
        self.assertIn("Ledger Safety", html)
        self.assertIn("reconciliation-yellow", html)
        self.assertIn("report=NOT_LOADED", html)
        self.assertIn("validator=UNTESTED", html)
        self.assertIn("ledger=NOT_LOADED", html)
        self.assertIn("single-writer=NOT_LOADED", html)
        self.assertIn("idempotency=NOT_LOADED", html)
        self.assertIn("Display-only ledger safety", html)
        self.assertIn("Operator Workflow", html)
        self.assertIn("Run PAPER", html)
        self.assertIn("Inspect Dashboard", html)
        self.assertIn("Collect Evidence", html)
        self.assertIn("LIVE Review Blocked", html)
        self.assertIn("workflow-yellow", html)
        self.assertIn("Strategy Evidence Maturity", html)
        self.assertIn("Strategy Evidence", html)
        self.assertIn("Paper / Shadow Samples", html)
        self.assertIn("Optimizer Input", html)
        self.assertIn("Evidence Quality", html)
        self.assertIn("Evidence Progress: 0%", html)
        self.assertIn("Maturity Gap: OPEN_HIGH", html)
        self.assertIn("10 maturity gaps remain", html)
        self.assertIn("Strategy Entry Exit No Trade", html)
        self.assertIn("Symbol Selection Regime", html)
        self.assertIn("Risk Sizing Exposure", html)
        self.assertIn("EVIDENCE_MISSING", html)
        self.assertIn("RECORDED_GAP", html)
        self.assertIn("PAPER_EVIDENCE_COLLECTION_ONLY", html)
        self.assertIn("NOT_LIVE_READY", html)
        self.assertIn("PAPER samples", html)
        self.assertIn("SHADOW samples", html)
        self.assertIn("Cost evidence", html)
        self.assertIn("Entry reasons", html)
        self.assertIn("No-trade reasons", html)
        self.assertIn("BLOCK_RANKING", html)
        self.assertIn("maturity-yellow", html)
        self.assertIn("analysis-only", html)
        self.assertIn("Convergence Assessment", html)
        self.assertIn("Convergence Review", html)
        self.assertIn("Dependency Closure", html)
        self.assertIn("Model Drift", html)
        self.assertIn("Live Boundary", html)
        self.assertIn("0/10 dependency validators PASS", html)
        self.assertIn("CONVERGENCE_STATE_UNTESTED", html)
        self.assertIn("convergence-yellow", html)
        self.assertIn("Writer Input=False", html)
        self.assertIn("Model Promotion=False", html)
        self.assertIn("Scale-Up Recommendation=False", html)
        self.assertIn("Display-only convergence review", html)
        self.assertIn("Exploration / Exploitation Policy", html)
        self.assertIn("Optimizer Policy", html)
        self.assertIn("Candidate Budget", html)
        self.assertIn("PAPER Ranking", html)
        self.assertIn("0/6 dependency validators PASS", html)
        self.assertIn("EXPLORATION_POLICY_UNTESTED", html)
        self.assertIn("exploration-policy-yellow", html)
        self.assertIn("PAPER ranking review only", html)
        self.assertIn("Parameter Narrowing", html)
        self.assertIn("Parameter Proposal", html)
        self.assertIn("Review Scope", html)
        self.assertIn("Sample Coverage", html)
        self.assertIn("Parameter Set", html)
        self.assertIn("0/7 dependency validators PASS", html)
        self.assertIn("PARAMETER_NARROWING_UNVERIFIED", html)
        self.assertIn("parameter-narrowing-yellow", html)
        self.assertIn("proposal-only", html)
        self.assertIn("Display-only parameter proposal", html)
        self.assertIn("Risk Exposure", html)
        self.assertIn("risk-yellow", html)
        self.assertIn("Exposure", html)
        self.assertIn("Drawdown", html)
        self.assertIn("Scale-Up", html)
        self.assertIn("Data Quality", html)
        self.assertIn("exposure=COMPLETE", html)
        self.assertIn("drawdown=VERIFIED", html)
        self.assertIn("Paper Quality", html)
        self.assertIn("UNAVAILABLE", html)
        self.assertIn("samples=0/0", html)
        self.assertIn("Next evidence", html)
        self.assertIn("paper_exposure_quality_report", html)
        self.assertIn("Risk Recommendation", html)
        self.assertIn("NO_SCALE_UP", html)
        self.assertIn("scale_up_allowed=false", html)
        self.assertIn("No paper exposure quality report is loaded", html)
        self.assertIn("Execution Feedback", html)
        self.assertIn("feedback-yellow", html)
        self.assertIn("Execution Quality", html)
        self.assertIn("Risk Review", html)
        self.assertIn("Net EV Drift", html)
        self.assertIn("Cost Drift", html)
        self.assertIn("Optimizer Ranking", html)
        self.assertIn("Execution feedback is PAPER/SHADOW analysis-only", html)
        self.assertIn("Trading Decision", html)
        self.assertIn("Recent Activity", html)
        self.assertIn("No-trade reason", html)
        self.assertIn("No trade", html)
        self.assertIn("Entry", html)
        self.assertIn("Exit", html)
        self.assertIn("Open PAPER Positions", html)
        self.assertIn("No open PAPER positions", html)
        self.assertIn("operation-green", html)
        self.assertIn("--ok: #15803d", html)
        self.assertIn("--safe: #0f6fb3", html)
        self.assertIn("--warn: #b7791f", html)
        self.assertIn("--danger: #b42318", html)
        self.assertIn("READ ONLY", html)
        self.assertIn("LIVE ORDERS BLOCKED", html)
        self.assertIn("Dashboard Data Freshness", html)
        self.assertIn("data-dashboard-freshness", html)
        self.assertIn("data-client-freshness-pill", html)
        self.assertIn("data-dashboard-age", html)
        self.assertIn("Auto Refresh", html)
        self.assertIn("source-summary", html)
        self.assertIn("source-count-total", html)
        self.assertIn("source-count-pass", html)
        self.assertIn("source-count-attention", html)
        self.assertIn("data-source-status=\"SUMMARY=PASS\"", html)
        self.assertIn("source-artifacts-table", html)
        self.assertIn("This dashboard page is older than the freshness limit", html)
        self.assertIn("window.location.reload", html)
        self.assertIn("trader1.dashboard.detailsOpen.", html)
        self.assertIn('document.querySelectorAll("details")', html)
        self.assertIn('document.addEventListener("DOMContentLoaded", initializeDashboardClient, { once: true });', html)
        self.assertIn('detail.addEventListener("toggle"', html)
        self.assertIn("data-refresh-seconds=\"10\"", html)
        self.assertIn("data-stale-after=\"300\"", html)
        self.assertIn("Primary Blocker", html)
        self.assertIn("Next operator action", html)
        self.assertIn("Dashboard display truth only", html)
        self.assertIn("Engine, ledger, and exchange truth remain separate", html)
        self.assertIn("System Health", html)
        self.assertIn("operator quick status", html)
        self.assertIn("Run", html)
        self.assertIn("Portfolio", html)
        self.assertIn("Live", html)
        self.assertIn("Portfolio Detail", html)
        self.assertIn("Live Execution", html)
        self.assertIn("Portfolio Snapshot", html)
        self.assertIn("Current values:</strong> Verified PAPER ledger", html)
        self.assertIn("PAPER LEDGER VERIFIED (SIMULATED)", html)
        self.assertIn("Configured PAPER Capital", html)
        self.assertIn("Cash", html)
        self.assertIn("Equity", html)
        self.assertIn("Locked Cash", html)
        self.assertIn("Realized PnL", html)
        self.assertIn("Unrealized PnL", html)
        self.assertIn("Total PnL", html)
        self.assertIn("Open Positions", html)
        self.assertIn("Entry Candidates", html)
        self.assertIn("Return", html)
        self.assertIn("1,000,000 KRW", html)
        self.assertIn("0.00%", html)
        self.assertIn("Simulated PAPER ledger, not exchange balance", html)
        self.assertIn("UPBIT", html)
        self.assertIn("KRW_SPOT", html)
        self.assertIn("PAPER", html)
        self.assertIn("live_order_ready=false", html)
        self.assertIn("live_order_allowed=false", html)
        self.assertIn("can_live_trade=false", html)
        self.assertIn("scale_up_allowed=false", html)
        self.assertIn('title="live_order_ready=false" aria-label="live_order_ready false">false</span>', html)
        self.assertIn('title="live_order_allowed=false" aria-label="live_order_allowed false">false</span>', html)
        self.assertIn('title="can_live_trade=false" aria-label="can_live_trade false">false</span>', html)
        self.assertIn('title="scale_up_allowed=false" aria-label="scale_up_allowed false">false</span>', html)
        self.assertIn("html { box-sizing: border-box; max-width: 100%; overflow-x: hidden; }", html)
        self.assertIn("h1, h2, h3, p, dl, dd, small, strong, span { overflow-wrap: anywhere; word-break: normal; }", html)
        self.assertIn(".readiness-row { display: flex; flex-wrap: wrap;", html)
        self.assertIn(".readiness-row .pill { flex: 0 1 auto; white-space: normal; }", html)
        self.assertIn(".operation dd:not(.pill) { font-size: 14px; line-height: 1.4; white-space: normal; overflow-wrap: anywhere;", html)
        self.assertIn(".decision-grid p, .decision-grid small, .evidence-requirement p, .evidence-requirement small { overflow-wrap: anywhere;", html)
        self.assertIn("operator priority answers", html)
        self.assertIn("operator decision surface", html)
        self.assertIn("Check these first", html)
        self.assertIn("Is it running normally?", html)
        self.assertIn("What is the PAPER portfolio?", html)
        self.assertIn("Can live orders run?", html)
        self.assertIn("No. Live orders cannot run.", html)
        self.assertIn("13 blockers remain: operator review 4, ledger/rerun 3, evidence/policy 6.", html)
        self.assertIn("Operator review", html)
        self.assertIn("Ledger/rerun", html)
        self.assertIn("Evidence/policy", html)
        self.assertIn("No repeated recheck remains", html)
        self.assertIn("All live and scale permissions are false.", html)
        self.assertIn("Portfolio Detail", html)
        self.assertIn("portfolio-quicklook", html)
        self.assertIn("Held Positions", html)
        self.assertIn("Live Execution", html)
        self.assertIn("Blocked", html)
        self.assertIn("Detailed status, evidence, and validator logs", html)
        self.assertIn("table-wrap", html)
        self.assertIn("<details class=\"detail-drawer\" data-detail-key=\"main-detail-drawer\">", html)
        self.assertIn("data-detail-key=\"status-panels\"", html)
        self.assertIn("data-detail-key=\"source-artifacts\"", html)
        self.assertIn('detail.getAttribute("data-detail-key")', html)
        self.assertNotIn("<details open>", html)
        self.assertNotIn("·", html)
        self.assertIn("Source Artifacts", html)
        self.assertNotIn("submit", html.lower())
        self.assertNotIn("<button", html.lower())
        self.assertNotIn("<form", html.lower())
        self.assertIn("not LIVE_READY", html)
        self.assertNotIn(">LIVE_READY<", html)
        self.assertNotIn("LIVE_READY=true", html)

    def test_dashboard_first_screen_prioritizes_operator_questions(self):
        html = render_dashboard_html(build_dashboard())
        decision_start = html.index('<section class="operator-decision-surface" aria-label="operator decision surface">')
        quick_start = html.index('<section class="operator-quick-status" aria-label="operator quick status">')
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        detail_start = html.index('<details class="detail-drawer" data-detail-key="main-detail-drawer">')
        freshness_start = html.index('<section class="freshness-strip" data-dashboard-freshness')
        decision_html = html[decision_start:quick_start]
        quick_html = html[quick_start:answer_start]
        answer_html = html[answer_start:portfolio_start]
        portfolio_html = html[portfolio_start:detail_start]

        self.assertLess(decision_start, quick_start)
        self.assertLess(quick_start, answer_start)
        self.assertLess(answer_start, portfolio_start)
        self.assertLess(portfolio_start, detail_start)
        self.assertLess(detail_start, freshness_start)
        self.assertIn("Operator View", decision_html)
        self.assertIn("Check these first", decision_html)
        self.assertIn("Run", quick_html)
        self.assertIn("Portfolio", quick_html)
        self.assertIn("Live", quick_html)
        self.assertIn("Is it running normally?", quick_html)
        self.assertIn("What is the PAPER portfolio?", quick_html)
        self.assertIn("Can live orders run?", quick_html)
        self.assertIn("No", quick_html)
        self.assertIn("Reason:", quick_html)
        self.assertIn("13 blockers remain", quick_html)
        self.assertIn("live_order_allowed=false", quick_html)
        self.assertIn("System Health", answer_html)
        self.assertIn("Portfolio Detail", answer_html)
        self.assertIn("Live Execution", answer_html)
        self.assertIn("No. Live orders cannot run.", answer_html)
        self.assertIn("Operator review", answer_html)
        self.assertIn("Ledger/rerun", answer_html)
        self.assertIn("Evidence/policy", answer_html)
        self.assertIn("No repeated recheck remains", answer_html)
        self.assertIn("All live and scale permissions are false.", answer_html)
        self.assertIn("live_order_allowed=false", answer_html)
        self.assertIn("Current values:</strong> Verified PAPER ledger", answer_html)
        self.assertIn("PAPER LEDGER VERIFIED (SIMULATED)", answer_html)
        self.assertNotIn("Source Artifacts", answer_html)
        self.assertNotIn("Ledger &amp; Reconciliation", answer_html)
        self.assertIn("PAPER Portfolio Details", portfolio_html)
        self.assertIn("Open PAPER Positions", portfolio_html)
        self.assertIn("Held Positions", portfolio_html)
        self.assertNotIn("Source Artifacts", portfolio_html)

    def test_dashboard_live_card_exposes_residual_next_actions(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture()
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        action_plan = dashboard["residual_open_gap_action_plan"]
        self.assertEqual(action_plan["source_status"], "LOADED")
        self.assertEqual(action_plan["open_gap_count"], 13)
        self.assertEqual(action_plan["implementation_recheck_action_count"], 0)
        self.assertFalse(action_plan["live_order_allowed"])
        self.assertFalse(action_plan["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Next Actions", answer_html)
        self.assertIn("Operator reconciliation: 4", answer_html)
        self.assertIn("PAPER ledger rerun: 3", answer_html)
        self.assertIn("PAPER/SHADOW evidence: 3", answer_html)
        self.assertIn("<strong>Evidence/policy</strong><span>6 left</span>", answer_html)
        self.assertIn("Other blocked evidence/policy: 3", answer_html)
        self.assertIn("No repeated implementation recheck remains", answer_html)
        self.assertIn("live_order_allowed=false", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_residual_operator_handoff_packets(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        handoff = dashboard["residual_operator_handoff_packet"]
        self.assertEqual(handoff["source_status"], "LOADED")
        self.assertEqual(handoff["status"], "BLOCKED_HANDOFF_REQUIRED")
        self.assertEqual(handoff["open_gap_count"], 13)
        self.assertEqual(handoff["handoff_packet_count"], 6)
        self.assertEqual(handoff["blocked_handoff_packet_count"], 6)
        self.assertEqual(handoff["handoff_ready_count"], 0)
        self.assertFalse(handoff["current_evidence_write_allowed"])
        self.assertFalse(handoff["gap_closure_allowed_by_this_patch"])
        self.assertFalse(handoff["live_order_allowed"])
        self.assertFalse(handoff["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Handoff:", answer_html)
        self.assertIn("6 total", answer_html)
        self.assertIn("6 blocked", answer_html)
        self.assertIn("0 ready", answer_html)
        self.assertIn("Operator reconciliation: 4", answer_html)
        self.assertIn("PAPER ledger rerun: 3", answer_html)
        self.assertIn("PAPER/SHADOW evidence: 3", answer_html)
        self.assertIn("Start with operator reconciliation and PAPER ledger rerun packets", answer_html)
        self.assertIn("live_order_allowed=false", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_residual_operator_execution_guide(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
            residual_operator_execution_guide_report=residual_operator_execution_guide_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        guide = dashboard["residual_operator_execution_guide"]
        self.assertEqual(guide["source_status"], "LOADED")
        self.assertEqual(guide["status"], "BLOCKED_GUIDE_ONLY")
        self.assertEqual(guide["open_gap_count"], 13)
        self.assertEqual(guide["execution_step_count"], 6)
        self.assertEqual(guide["local_paper_shadow_runtime_step_count"], 1)
        self.assertEqual(guide["external_or_policy_evidence_step_count"], 2)
        self.assertEqual(guide["minimum_observation_hours"], 0)
        self.assertTrue(guide["operator_runtime_required_before_mvp5"])
        self.assertTrue(guide["mvp5_entry_blocked_until_operator_evidence"])
        self.assertEqual(guide["binance_runtime_status"], "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS")
        self.assertFalse(guide["current_evidence_write_allowed"])
        self.assertFalse(guide["gap_closure_allowed_by_this_patch"])
        self.assertFalse(guide["live_config_mutation_allowed"])
        self.assertFalse(guide["live_ready_write_allowed"])
        self.assertFalse(guide["live_order_allowed"])
        self.assertFalse(guide["scale_up_allowed"])

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Execution guide:", answer_html)
        self.assertIn("6 blocked execution steps", answer_html)
        self.assertIn("1 local PAPER/SHADOW command", answer_html)
        self.assertIn("Adaptive evidence gate", answer_html)
        self.assertNotIn("48h minimum", answer_html)
        self.assertIn("MVP-5 blocked", answer_html)
        self.assertIn("Binance remains scaffold-only", answer_html)
        self.assertIn("live_order_allowed=false", answer_html)
        self.assertNotIn("TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_residual_operator_evidence_progress(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
            residual_operator_execution_guide_report=residual_operator_execution_guide_fixture(),
            residual_operator_evidence_progress_report=residual_operator_evidence_progress_fixture(),
            upbit_paper_post_rerun_operator_resolution_audit_report=post_rerun_resolution_audit_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        progress = dashboard["residual_operator_evidence_progress"]
        self.assertEqual(progress["source_status"], "LOADED")
        self.assertEqual(progress["status"], "BLOCKED_EVIDENCE_MISSING")
        self.assertEqual(progress["open_gap_count"], 13)
        self.assertEqual(progress["evidence_item_count"], 20)
        self.assertEqual(progress["present_blocked_evidence_item_count"], 3)
        self.assertEqual(progress["missing_operator_evidence_item_count"], 4)
        self.assertEqual(progress["placeholder_pending_evidence_item_count"], 3)
        self.assertEqual(progress["external_evidence_required_item_count"], 7)
        self.assertEqual(progress["local_runtime_output_item_count"], 3)
        self.assertEqual(progress["local_runtime_command_count"], 1)
        self.assertEqual(progress["local_runtime_completed_count"], 0)
        self.assertEqual(progress["minimum_observation_hours_required"], 0)
        self.assertEqual(progress["execution_step_count"], 6)
        self.assertEqual(
            progress["adaptive_judgement_status"],
            "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY",
        )
        self.assertEqual(progress["fixed_duration_gate_status"], "REMOVED_NO_FIXED_RUNTIME_FLOOR")
        self.assertTrue(progress["codex_stepwise_review_allowed"])
        self.assertTrue(progress["codex_can_continue_non_live_patches"])
        self.assertFalse(progress["user_runtime_required_for_next_non_live_patch"])
        self.assertTrue(progress["user_runtime_required_for_gap_closure"])
        self.assertEqual(
            progress["evidence_quality_status"],
            "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES",
        )
        self.assertIn("No immediate user action", progress["user_action_summary"])
        self.assertTrue(progress["operator_no_action_needed_for_next_patch"])
        self.assertEqual(progress["operator_decision_status"], "BLOCKED_DECISION_CARDS_READY")
        self.assertEqual(progress["operator_decision_card_count"], 6)
        self.assertEqual(
            progress["single_next_operator_decision"]["action_class"],
            "OPERATOR_RECONCILIATION_ACTION",
        )
        self.assertEqual(
            progress["single_next_operator_decision"]["decision_status"],
            "BLOCKED_OPERATOR_RECONCILIATION_REQUIRED",
        )
        self.assertGreaterEqual(len(progress["operator_decision_preview"]), 3)
        self.assertEqual(
            [item["action_class"] for item in progress["operator_decision_preview"]],
            [
                "OPERATOR_RECONCILIATION_ACTION",
                "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION",
                "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
            ],
        )
        self.assertEqual(
            [
                item["operator_can_run_local_command"]
                for item in progress["operator_decision_preview"]
            ],
            [False, False, True],
        )
        self.assertFalse(progress["operator_evidence_ready_for_mvp5"])
        self.assertFalse(progress["any_evidence_item_ready_for_closure"])
        self.assertTrue(progress["mvp5_entry_blocked_until_operator_evidence"])
        self.assertEqual(progress["binance_runtime_status"], "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS")
        self.assertFalse(progress["current_evidence_write_allowed"])
        self.assertFalse(progress["gap_closure_allowed_by_this_patch"])
        self.assertFalse(progress["live_config_mutation_allowed"])
        self.assertFalse(progress["live_ready_write_allowed"])
        self.assertFalse(progress["live_order_ready"])
        self.assertFalse(progress["live_order_allowed"])
        self.assertFalse(progress["can_live_trade"])
        self.assertFalse(progress["scale_up_allowed"])
        self.assertGreaterEqual(len(progress["status_breakdown_items"]), 5)
        self.assertGreaterEqual(len(progress["evidence_item_preview"]), 3)

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_EVIDENCE_PROGRESS"
        )
        self.assertEqual(source["filename"], "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json")
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Evidence Progress:", answer_html)
        self.assertIn("20 required evidence items", answer_html)
        self.assertIn("external=7", answer_html)
        self.assertIn("missing=4", answer_html)
        self.assertIn("placeholder=3", answer_html)
        self.assertIn("local-runtime=3", answer_html)
        self.assertIn("1 local PAPER/SHADOW command", answer_html)
        self.assertIn("Adaptive evidence gate", answer_html)
        self.assertIn("Codex review:", answer_html)
        self.assertIn("User action:", answer_html)
        self.assertIn("No immediate user action", answer_html)
        self.assertIn("Decision cards:", answer_html)
        self.assertIn("6 blocked card(s)", answer_html)
        self.assertIn("next=Operator reconciliation", answer_html)
        self.assertIn("BLOCKED_OPERATOR_RECONCILIATION_REQUIRED", answer_html)
        self.assertIn("Decision next:", answer_html)
        self.assertNotIn("48h minimum", answer_html)
        self.assertIn("MVP-5 blocked", answer_html)
        self.assertIn("live_order_allowed=false", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_paper_shadow_completion_acceptance(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
            residual_operator_execution_guide_report=residual_operator_execution_guide_fixture(),
            residual_operator_evidence_progress_report=residual_operator_evidence_progress_fixture(),
            residual_operator_evidence_completion_acceptance_report=residual_operator_evidence_completion_acceptance_fixture(),
            upbit_paper_post_rerun_operator_resolution_audit_report=post_rerun_resolution_audit_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        completion = dashboard["residual_operator_evidence_completion_acceptance"]
        self.assertEqual(completion["source_status"], "LOADED")
        self.assertEqual(completion["status"], "PENDING_OPERATOR_RUNTIME_EVIDENCE")
        self.assertEqual(completion["preflight_status"], "NON_LIVE_OPERATOR_RUN_PRECHECK_PASS")
        self.assertEqual(completion["acceptance_status"], "PENDING_OPERATOR_RUNTIME_EVIDENCE")
        self.assertEqual(completion["completion_gate_count"], 12)
        self.assertEqual(completion["completion_pending_count"], 12)
        self.assertEqual(completion["completion_accepted_count"], 0)
        self.assertEqual(completion["completion_artifact_gate_count"], 5)
        self.assertEqual(completion["completion_validator_gate_count"], 6)
        self.assertEqual(completion["completion_safety_invariant_gate_count"], 1)
        self.assertEqual(completion["expected_runtime_artifact_count"], 5)
        self.assertEqual(completion["required_validator_count"], 6)
        self.assertEqual(completion["first_pending_gate_id"], "RUNTIME_ARTIFACT_01")
        self.assertEqual(completion["first_pending_gate_validator"], "runtime_schema_instance_validator")
        self.assertTrue(completion["mvp5_entry_blocked_until_operator_evidence"])
        self.assertFalse(completion["operator_run_started_by_this_patch"])
        self.assertFalse(completion["operator_run_completed_by_this_patch"])
        self.assertFalse(completion["operator_run_evidence_ready_for_mvp5"])
        self.assertFalse(completion["command_executed_by_this_patch"])
        self.assertTrue(completion["non_live_operator_command_preflight_passed"])
        self.assertFalse(completion["credential_values_read"])
        self.assertFalse(completion["credential_environment_inspection_performed"])
        self.assertFalse(completion["current_evidence_write_allowed"])
        self.assertFalse(completion["gap_closure_allowed_by_this_patch"])
        self.assertFalse(completion["live_config_mutation_allowed"])
        self.assertFalse(completion["live_ready_write_allowed"])
        self.assertFalse(completion["live_order_ready"])
        self.assertFalse(completion["live_order_allowed"])
        self.assertFalse(completion["can_live_trade"])
        self.assertFalse(completion["scale_up_allowed"])
        self.assertEqual(
            [item["count"] for item in completion["completion_gate_breakdown_items"]],
            [5, 6, 1],
        )
        self.assertGreaterEqual(len(completion["pending_gate_preview"]), 4)

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE"
        )
        self.assertEqual(
            source["filename"],
            "MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_COMPLETION_ACCEPTANCE.report.json",
        )
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("PAPER/SHADOW completion:", answer_html)
        self.assertIn("12/12 pending", answer_html)
        self.assertIn("5 required", answer_html)
        self.assertIn("6 PASS required", answer_html)
        self.assertIn("RUNTIME_ARTIFACT_01", answer_html)
        self.assertIn("runtime_schema_instance_validator", answer_html)
        self.assertIn("dashboard cannot close gaps", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_operator_reconciliation_review_cards(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
            residual_operator_execution_guide_report=residual_operator_execution_guide_fixture(),
            residual_operator_evidence_progress_report=residual_operator_evidence_progress_fixture(),
            residual_operator_reconciliation_review_cards_report=residual_operator_reconciliation_review_cards_fixture(),
            upbit_paper_post_rerun_operator_resolution_audit_report=post_rerun_resolution_audit_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        review = dashboard["residual_operator_reconciliation_review_cards"]
        self.assertEqual(review["source_status"], "LOADED")
        self.assertEqual(review["status"], "BLOCKED_RECONCILIATION_REVIEW_ONLY")
        self.assertEqual(review["open_gap_count"], 13)
        self.assertEqual(review["operator_reconciliation_gap_count"], 4)
        self.assertEqual(review["review_card_count"], 8)
        self.assertEqual(review["blocked_review_card_count"], 8)
        self.assertEqual(review["review_ready_count"], 0)
        self.assertEqual(review["control_card_count"], 4)
        self.assertEqual(review["unsatisfied_control_count"], 4)
        self.assertEqual(review["satisfied_control_count"], 0)
        self.assertEqual(review["operator_resolution_audit_status"], "UNRESOLVED_RECONCILIATION_REVIEW_ONLY")
        self.assertEqual(review["operator_resolution_binding_status"], "BOUND_BLOCKED")
        self.assertEqual(review["operator_resolution_unresolved_item_count"], 8)
        self.assertEqual(review["operator_resolution_resolved_item_count"], 0)
        self.assertEqual(review["operator_resolution_controls_satisfied_count"], 0)
        self.assertEqual(review["operator_resolution_current_evidence_write_allowed_count"], 0)
        self.assertEqual(review["operator_resolution_candidate_current_evidence_usable_count"], 0)
        self.assertTrue(review["source_hashes_verified"])
        self.assertEqual(review["single_next_review_card"]["review_status"], "BLOCKED_REVIEW_ONLY")
        self.assertEqual(
            review["single_next_review_card"]["resolution_reason_code"],
            "POST_RERUN_RECONCILIATION_REQUIRED",
        )
        self.assertEqual(len(review["review_card_preview"]), 3)
        self.assertEqual(len(review["control_card_preview"]), 4)
        self.assertTrue(review["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(review["operator_action_required_for_gap_closure"])
        self.assertFalse(review["current_evidence_write_allowed"])
        self.assertFalse(review["gap_closure_allowed_by_this_patch"])
        self.assertFalse(review["live_ready_write_allowed"])
        self.assertFalse(review["live_config_mutation_allowed"])
        self.assertFalse(review["live_order_ready"])
        self.assertFalse(review["live_order_allowed"])
        self.assertFalse(review["can_live_trade"])
        self.assertFalse(review["scale_up_allowed"])

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS"
        )
        self.assertEqual(source["filename"], "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_REVIEW_CARDS.report.json")
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Operator reconciliation review:", answer_html)
        self.assertIn("8 operator reconciliation review cards remain blocked", answer_html)
        self.assertIn("4 controls are unsatisfied", answer_html)
        self.assertIn("current-evidence writes stay 0", answer_html)
        self.assertIn("Review next:", answer_html)
        self.assertIn("Source binding:", answer_html)
        self.assertIn("BOUND_BLOCKED", answer_html)
        self.assertIn("source-bound=True", answer_html)
        self.assertIn("current-evidence writes=0", answer_html)
        self.assertIn("usable=0", answer_html)
        self.assertIn("First review card:", answer_html)
        self.assertIn("BLOCKED_REVIEW_ONLY", answer_html)
        self.assertIn("POST_RERUN_RECONCILIATION_REQUIRED", answer_html)
        self.assertIn("8 review cards", answer_html)
        self.assertIn("4 controls", answer_html)
        self.assertIn("8 unresolved items", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_operator_reconciliation_intake_preflight(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_handoff_packet_report=residual_operator_handoff_packet_fixture(),
            residual_operator_execution_guide_report=residual_operator_execution_guide_fixture(),
            residual_operator_evidence_progress_report=residual_operator_evidence_progress_fixture(),
            residual_operator_reconciliation_review_cards_report=residual_operator_reconciliation_review_cards_fixture(),
            residual_operator_reconciliation_intake_preflight_report=residual_operator_reconciliation_intake_preflight_fixture(),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        intake = dashboard["residual_operator_reconciliation_intake_preflight"]
        self.assertEqual(intake["source_status"], "LOADED")
        self.assertEqual(intake["status"], "BLOCKED_RECONCILIATION_INTAKE_PACKAGE_MISSING")
        self.assertEqual(intake["open_gap_count"], 13)
        self.assertEqual(intake["review_card_count"], 8)
        self.assertEqual(intake["required_intake_item_count"], 32)
        self.assertEqual(intake["missing_intake_item_count"], 32)
        self.assertEqual(intake["ready_for_review_intake_item_count"], 0)
        self.assertEqual(intake["accepted_intake_item_count"], 0)
        self.assertEqual(intake["control_requirement_count"], 4)
        self.assertEqual(intake["unsatisfied_control_requirement_count"], 4)
        self.assertIn(
            intake["operator_reconciliation_submission_manifest_status"],
            {"MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST", "PRESENT_NOT_VALIDATED"},
        )
        self.assertEqual(
            intake["paper_shadow_operator_evidence_intake_status"],
            "BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE",
        )
        self.assertEqual(
            intake["single_next_intake_item"]["intake_item_status"],
            "MISSING_OPERATOR_RECONCILIATION_EVIDENCE",
        )
        self.assertEqual(
            intake["single_next_intake_item"]["resolution_reason_code"],
            "POST_RERUN_RECONCILIATION_REQUIRED",
        )
        self.assertEqual(len(intake["intake_item_preview"]), 4)
        self.assertTrue(intake["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(intake["operator_action_required_for_gap_closure"])
        self.assertFalse(intake["current_evidence_write_allowed"])
        self.assertFalse(intake["gap_closure_allowed_by_this_patch"])
        self.assertFalse(intake["live_ready_write_allowed"])
        self.assertFalse(intake["live_config_mutation_allowed"])
        self.assertFalse(intake["live_order_ready"])
        self.assertFalse(intake["live_order_allowed"])
        self.assertFalse(intake["can_live_trade"])
        self.assertFalse(intake["scale_up_allowed"])

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT"
        )
        self.assertEqual(source["filename"], "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.report.json")
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Operator reconciliation intake:", answer_html)
        self.assertIn("32 reconciliation evidence inputs remain missing", answer_html)
        self.assertIn("current-evidence writes stay 0", answer_html)
        self.assertIn("Intake next:", answer_html)
        self.assertIn("Manifest:", answer_html)
        self.assertIn("BLOCKED_AWAITING_OPERATOR_EVIDENCE_PACKAGE", answer_html)
        self.assertIn("First missing input:", answer_html)
        self.assertIn("MISSING_OPERATOR_RECONCILIATION_EVIDENCE", answer_html)
        self.assertIn("32 inputs", answer_html)
        self.assertIn("32 missing", answer_html)
        self.assertIn("0 ready", answer_html)
        self.assertIn("0 accepted", answer_html)
        self.assertIn("4 controls", answer_html)
        self.assertIn("4 unsatisfied", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_operator_submission_manifest_preflight(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_reconciliation_submission_manifest_preflight_report=(
                residual_operator_reconciliation_submission_manifest_preflight_fixture()
            ),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        manifest = dashboard["residual_operator_reconciliation_submission_manifest_preflight"]
        self.assertEqual(manifest["source_status"], "LOADED")
        self.assertEqual(manifest["status"], "BLOCKED_MANIFEST_MISSING")
        self.assertEqual(manifest["open_gap_count"], 13)
        self.assertEqual(manifest["manifest_schema_id"], "trader1.residual_operator_reconciliation_submission_manifest.v1")
        self.assertEqual(
            manifest["manifest_path"],
            "system/evidence/operator_submissions/residual_operator_reconciliation_submission_manifest.json",
        )
        self.assertEqual(manifest["manifest_status"], "MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST")
        self.assertEqual(manifest["manifest_schema_validation_status"], "NOT_RUN_MISSING")
        self.assertFalse(manifest["operator_submission_present"])
        self.assertFalse(manifest["operator_submission_validated"])
        self.assertFalse(manifest["operator_submission_accepted"])
        self.assertFalse(manifest["manifest_structural_check_only"])
        self.assertEqual(manifest["required_manifest_item_count"], 32)
        self.assertEqual(manifest["manifest_item_count"], 0)
        self.assertEqual(manifest["missing_manifest_item_count"], 32)
        self.assertEqual(manifest["required_control_count"], 4)
        self.assertEqual(manifest["manifest_control_count"], 0)
        self.assertEqual(manifest["missing_control_count"], 4)
        self.assertEqual(manifest["unsafe_manifest_flag_count"], 0)
        self.assertEqual(manifest["path_policy_violation_count"], 0)
        self.assertEqual(manifest["source_hash_mismatch_count"], 0)
        self.assertTrue(manifest["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(manifest["operator_action_required_for_gap_closure"])
        self.assertFalse(manifest["current_evidence_write_allowed"])
        self.assertFalse(manifest["gap_closure_allowed_by_this_patch"])
        self.assertFalse(manifest["live_ready_write_allowed"])
        self.assertFalse(manifest["live_config_mutation_allowed"])
        self.assertFalse(manifest["live_order_ready"])
        self.assertFalse(manifest["live_order_allowed"])
        self.assertFalse(manifest["can_live_trade"])
        self.assertFalse(manifest["scale_up_allowed"])

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT"
        )
        self.assertEqual(source["filename"], "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT.report.json")
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Submission manifest preflight:", answer_html)
        self.assertIn("Operator reconciliation submission manifest is MISSING_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST", answer_html)
        self.assertIn("Structural check:", answer_html)
        self.assertIn("accepted=false", answer_html)
        self.assertIn("current-evidence writes=false", answer_html)
        self.assertIn("LIVE_READY=false", answer_html)
        self.assertIn("32 items", answer_html)
        self.assertIn("32 missing", answer_html)
        self.assertIn("4 missing", answer_html)
        self.assertIn("0 flags", answer_html)
        self.assertIn("0 violations", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_operator_submission_template_packet(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_reconciliation_submission_template_packet_report=(
                residual_operator_reconciliation_submission_template_packet_fixture()
            ),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        template = dashboard["residual_operator_reconciliation_submission_template_packet"]
        self.assertEqual(template["source_status"], "LOADED")
        self.assertEqual(template["status"], "TEMPLATE_PACKET_READY_FOR_OPERATOR_PREPARATION_ONLY")
        self.assertEqual(template["open_gap_count"], 13)
        self.assertEqual(template["template_packet_scope"], "OPERATOR_PREPARATION_ONLY_NOT_EVIDENCE")
        self.assertEqual(
            template["actual_submission_manifest_path"],
            "system/evidence/operator_submissions/residual_operator_reconciliation_submission_manifest.json",
        )
        self.assertFalse(template["actual_submission_manifest_written_by_this_patch"])
        self.assertTrue(template["operator_submission_required"])
        self.assertFalse(template["operator_submission_validated"])
        self.assertFalse(template["operator_submission_accepted"])
        self.assertEqual(template["required_manifest_item_count"], 32)
        self.assertEqual(template["template_manifest_item_count"], 32)
        self.assertEqual(template["required_control_count"], 4)
        self.assertEqual(template["template_control_count"], 4)
        self.assertTrue(template["operator_no_action_needed_for_next_non_live_patch"])
        self.assertTrue(template["operator_action_required_for_gap_closure"])
        self.assertFalse(template["current_evidence_write_allowed"])
        self.assertFalse(template["gap_closure_allowed_by_this_patch"])
        self.assertFalse(template["live_ready_write_allowed"])
        self.assertFalse(template["live_config_mutation_allowed"])
        self.assertFalse(template["live_order_ready"])
        self.assertFalse(template["live_order_allowed"])
        self.assertFalse(template["can_live_trade"])
        self.assertFalse(template["scale_up_allowed"])

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET"
        )
        self.assertEqual(source["filename"], "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET.report.json")
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Submission template packet:", answer_html)
        self.assertIn("preparation-only with 32 manifest items and 4 controls", answer_html)
        self.assertIn("Actual manifest target:", answer_html)
        self.assertIn("written_by_patch=false", answer_html)
        self.assertIn("accepted=false", answer_html)
        self.assertIn("LIVE_READY=false", answer_html)
        self.assertIn("32 of 32", answer_html)
        self.assertIn("4 of 4", answer_html)
        self.assertIn("not evidence", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_operator_submission_security_quarantine(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_reconciliation_submission_security_quarantine_report=(
                residual_operator_reconciliation_submission_security_quarantine_fixture()
            ),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        quarantine = dashboard["residual_operator_reconciliation_submission_security_quarantine"]
        self.assertEqual(quarantine["source_status"], "LOADED")
        self.assertEqual(quarantine["status"], "QUARANTINE_PENDING_OPERATOR_SUBMISSION")
        self.assertEqual(quarantine["open_gap_count"], 13)
        self.assertEqual(quarantine["quarantine_scope"], "METADATA_ONLY_NO_FILE_CONTENT_READ")
        self.assertEqual(
            quarantine["allowed_submission_prefix"],
            "system/evidence/operator_submissions/residual_operator_reconciliation/",
        )
        self.assertEqual(quarantine["allowed_artifact_extensions"], [".json", ".jsonl", ".md", ".txt", ".csv"])
        self.assertGreaterEqual(quarantine["forbidden_path_token_count"], 10)
        self.assertTrue(quarantine["operator_submission_required"])
        self.assertFalse(quarantine["operator_submission_validated"])
        self.assertFalse(quarantine["operator_submission_accepted"])
        self.assertEqual(quarantine["required_manifest_item_count"], 32)
        self.assertEqual(quarantine["template_manifest_item_count"], 32)
        self.assertEqual(quarantine["required_control_count"], 4)
        self.assertEqual(quarantine["template_control_count"], 4)
        self.assertEqual(quarantine["security_control_count"], 4)
        self.assertGreaterEqual(quarantine["quarantine_blocker_count"], 1)
        self.assertFalse(quarantine["evidence_file_content_read"])
        self.assertFalse(quarantine["evidence_artifact_hash_recomputed"])
        self.assertFalse(quarantine["secret_pattern_content_scan_performed"])
        self.assertFalse(quarantine["current_evidence_write_allowed"])
        self.assertFalse(quarantine["gap_closure_allowed_by_this_patch"])
        self.assertFalse(quarantine["live_ready_write_allowed"])
        self.assertFalse(quarantine["live_config_mutation_allowed"])
        self.assertFalse(quarantine["credential_values_read"])
        self.assertFalse(quarantine["live_order_ready"])
        self.assertFalse(quarantine["live_order_allowed"])
        self.assertFalse(quarantine["can_live_trade"])
        self.assertFalse(quarantine["scale_up_allowed"])

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_SECURITY_QUARANTINE"
        )
        self.assertEqual(
            source["filename"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_SECURITY_QUARANTINE.report.json",
        )
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Submission quarantine:", answer_html)
        self.assertIn("metadata only", answer_html)
        self.assertIn("Allowed folder:", answer_html)
        self.assertIn("file contents read=false", answer_html)
        self.assertIn("secret scan=false", answer_html)
        self.assertIn("accepted=false", answer_html)
        self.assertIn("LIVE_READY=false", answer_html)
        self.assertIn("32 missing", answer_html)
        self.assertIn("not read", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_live_card_exposes_operator_submission_review_queue(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture(),
            residual_operator_reconciliation_submission_review_queue_report=(
                residual_operator_reconciliation_submission_review_queue_fixture()
            ),
        )
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        queue = dashboard["residual_operator_reconciliation_submission_review_queue"]
        self.assertEqual(queue["source_status"], "LOADED")
        self.assertEqual(queue["status"], "BLOCKED_OPERATOR_SUBMISSION_MISSING")
        self.assertEqual(queue["open_gap_count"], 13)
        self.assertTrue(queue["review_order_locked"])
        self.assertEqual(queue["review_phase_count"], 4)
        self.assertEqual(queue["blocked_phase_count"], 4)
        self.assertEqual(queue["review_ready_phase_count"], 0)
        self.assertEqual(queue["accepted_phase_count"], 0)
        self.assertEqual(queue["single_next_operator_step"], "CREATE_OPERATOR_SUBMISSION_MANIFEST")
        self.assertFalse(queue["operator_submission_present"])
        self.assertFalse(queue["operator_submission_validated"])
        self.assertFalse(queue["operator_submission_accepted"])
        self.assertEqual(queue["required_manifest_item_count"], 32)
        self.assertEqual(queue["manifest_item_count"], 0)
        self.assertEqual(queue["missing_manifest_item_count"], 32)
        self.assertEqual(queue["required_control_count"], 4)
        self.assertEqual(queue["security_control_count"], 4)
        self.assertEqual([step["phase_id"] for step in queue["review_steps"]], [
            "TEMPLATE_PACKET",
            "MANIFEST_PREFLIGHT",
            "SECURITY_QUARANTINE",
            "OPERATOR_ACCEPTANCE",
        ])
        self.assertFalse(queue["evidence_file_content_read"])
        self.assertFalse(queue["current_evidence_write_allowed"])
        self.assertFalse(queue["gap_closure_allowed_by_this_patch"])
        self.assertFalse(queue["live_ready_write_allowed"])
        self.assertFalse(queue["live_order_allowed"])
        self.assertFalse(queue["scale_up_allowed"])

        source = next(
            item
            for item in dashboard["source_artifacts"]
            if item["artifact_id"] == "RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE"
        )
        self.assertEqual(
            source["filename"],
            "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_REVIEW_QUEUE.report.json",
        )
        self.assertEqual(source["freshness_status"], "PASS")

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Submission review queue:", answer_html)
        self.assertIn("Next operator step:", answer_html)
        self.assertIn("ordered review only", answer_html)
        self.assertIn("evidence read=false", answer_html)
        self.assertIn("accepted=false", answer_html)
        self.assertIn("current evidence write=false", answer_html)
        self.assertIn("LIVE_READY=false", answer_html)
        self.assertIn("4/4 blocked", answer_html)
        self.assertIn("32 items", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_residual_operator_priority_queue_is_deterministic_and_display_only(self):
        dashboard = build_dashboard_with_residual_priority_resolution_binding()
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "PASS", result.message)
        priority = dashboard["residual_operator_priority"]
        self.assertEqual(priority["source_status"], "LOADED")
        self.assertEqual(priority["status"], "ACTION_REQUIRED")
        self.assertEqual(priority["open_gap_count"], 13)
        self.assertEqual(priority["queue_item_count"], 6)
        self.assertEqual(priority["queue_gap_count"], 13)
        self.assertEqual(
            [item["action_class"] for item in priority["queue_items"]],
            [
                "OPERATOR_RECONCILIATION_ACTION",
                "PAPER_LEDGER_RERUN_RECONCILIATION_ACTION",
                "PAPER_SHADOW_EVIDENCE_COLLECTION_ACTION",
                "EXTERNAL_LIVE_READINESS_EVIDENCE_ACTION",
                "SEALED_BASELINE_PRESERVATION_ACTION",
                "SCALE_UP_POLICY_EVIDENCE_ACTION",
            ],
        )
        self.assertEqual(priority["single_next_action_class"], "OPERATOR_RECONCILIATION_ACTION")
        self.assertEqual(priority["single_next_action_priority"], 1)
        self.assertEqual(priority["single_next_action_gap_count"], 4)
        self.assertFalse(priority["user_runtime_required_for_next_non_live_patch"])
        self.assertFalse(priority["current_evidence_write_allowed"])
        self.assertFalse(priority["gap_closure_allowed_by_this_patch"])
        self.assertFalse(priority["live_config_mutation_allowed"])
        self.assertFalse(priority["live_ready_write_allowed"])
        self.assertFalse(priority["live_order_ready"])
        self.assertFalse(priority["live_order_allowed"])
        self.assertFalse(priority["can_live_trade"])
        self.assertFalse(priority["scale_up_allowed"])
        self.assertEqual(priority["operator_reconciliation_resolution_binding_status"], "BOUND_BLOCKED")
        self.assertEqual(
            priority["operator_reconciliation_resolution_audit_status"],
            "UNRESOLVED_RECONCILIATION_REVIEW_ONLY",
        )
        self.assertEqual(priority["operator_reconciliation_resolution_validation_status"], "PASS")
        self.assertEqual(priority["operator_reconciliation_unresolved_item_count"], 8)
        self.assertEqual(priority["operator_reconciliation_resolved_item_count"], 0)
        self.assertEqual(priority["operator_reconciliation_controls_satisfied_count"], 0)
        self.assertEqual(priority["operator_reconciliation_current_evidence_write_allowed_count"], 0)
        self.assertEqual(priority["operator_reconciliation_candidate_current_evidence_usable_count"], 0)
        self.assertTrue(priority["operator_reconciliation_source_bindings_verified"])
        self.assertEqual(priority["gap_action_map_coverage_status"], "COVERS_ALL_OPEN_GAPS")
        self.assertEqual(priority["gap_action_map_count"], 13)
        self.assertEqual(priority["gap_action_map_owner_order"], [
            "OPERATOR",
            "CODEX_NON_LIVE",
            "PAPER_SHADOW_RUNTIME",
            "EXTERNAL_EVIDENCE",
            "CODEX_AUDIT_ONLY",
            "SCALE_POLICY",
        ])
        self.assertEqual(priority["first_gap_action_owner"], "OPERATOR")
        self.assertEqual(
            priority["first_gap_action_id"],
            "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
        )
        action_map = priority["gap_action_map"]
        self.assertEqual(len(action_map), 13)
        self.assertEqual(len({item["gap_id"] for item in action_map}), 13)
        self.assertEqual(
            [item["owner"] for item in action_map[:4]],
            ["OPERATOR", "OPERATOR", "OPERATOR", "OPERATOR"],
        )
        self.assertEqual(action_map[4]["owner"], "CODEX_NON_LIVE")
        self.assertEqual(action_map[7]["owner"], "PAPER_SHADOW_RUNTIME")
        self.assertEqual(action_map[10]["owner"], "EXTERNAL_EVIDENCE")
        self.assertEqual(action_map[11]["owner"], "CODEX_AUDIT_ONLY")
        self.assertEqual(action_map[12]["owner"], "SCALE_POLICY")
        for item in action_map:
            self.assertEqual(item["reason_code"], item["gap_id"])
            self.assertTrue(item["display_only"])
            self.assertTrue(item["dashboard_truth_only"])
            self.assertFalse(item["current_evidence_write_allowed"])
            self.assertFalse(item["gap_closure_allowed_by_this_patch"])
            self.assertFalse(item["live_ready_write_allowed"])
            self.assertFalse(item["live_config_mutation_allowed"])
            self.assertFalse(item["live_order_ready"])
            self.assertFalse(item["live_order_allowed"])
            self.assertFalse(item["can_live_trade"])
            self.assertFalse(item["scale_up_allowed"])
        for item in priority["queue_items"]:
            self.assertEqual(item["gap_count"], len(item["gap_ids"]))
            self.assertFalse(item["allows_live_order"])
            self.assertFalse(item["allows_live_config_mutation"])
            self.assertFalse(item["allows_scale_up"])

        html = render_dashboard_html(dashboard)
        answer_start = html.index('<section class="operator-answer-grid" aria-label="operator priority answers">')
        portfolio_start = html.index('<section class="primary-portfolio-detail" aria-label="primary portfolio detail">')
        answer_html = html[answer_start:portfolio_start]
        self.assertIn("Priority:</strong> #1 Operator reconciliation - 4 gap(s)", answer_html)
        self.assertIn("safety &gt; no-trade &gt; operator reconciliation", answer_html)
        self.assertIn("First action:", answer_html)
        self.assertIn("Review and reconcile repaired", answer_html)
        self.assertIn("Operator resolution binding:", answer_html)
        self.assertIn("BOUND_BLOCKED", answer_html)
        self.assertIn("current-evidence writes=0", answer_html)
        self.assertIn("source-bound=True", answer_html)
        self.assertIn("Action map:</strong> 13 gap(s); coverage=COVERS_ALL_OPEN_GAPS", answer_html)
        self.assertIn("owners=OPERATOR=4, CODEX_NON_LIVE=3", answer_html)
        self.assertIn("BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION", answer_html)
        self.assertIn("Acceptance:", answer_html)
        self.assertIn("live_order_allowed=false", answer_html)
        self.assertNotIn("<button", answer_html.lower())
        self.assertNotIn("<form", answer_html.lower())

    def test_dashboard_rejects_residual_operator_priority_permission_drift(self):
        dashboard = build_dashboard(
            residual_open_gap_operator_action_plan_report=residual_open_gap_action_plan_fixture()
        )
        dashboard["residual_operator_priority"]["live_ready_write_allowed"] = True
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_rejects_residual_operator_action_map_permission_drift(self):
        dashboard = build_dashboard_with_residual_priority_resolution_binding()
        dashboard["residual_operator_priority"]["gap_action_map"][0]["gap_closure_allowed_by_this_patch"] = True
        dashboard["residual_operator_priority"]["gap_action_map"][0]["live_order_allowed"] = True
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_rejects_residual_operator_action_map_gap_binding_drift(self):
        dashboard = build_dashboard_with_residual_priority_resolution_binding()
        duplicate = dict(dashboard["residual_operator_priority"]["gap_action_map"][0])
        dashboard["residual_operator_priority"]["gap_action_map"][1] = duplicate
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "CONTRACT_GAP_HIGH")

    def test_dashboard_rejects_residual_operator_priority_resolution_write_drift(self):
        dashboard = build_dashboard_with_residual_priority_resolution_binding()
        dashboard["residual_operator_priority"]["operator_reconciliation_current_evidence_write_allowed_count"] = 1
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_rejects_residual_operator_priority_resolution_source_binding_drift(self):
        dashboard = build_dashboard_with_residual_priority_resolution_binding()
        dashboard["residual_operator_priority"]["operator_reconciliation_source_bindings_verified"] = False
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_rejects_residual_operator_priority_order_drift(self):
        report = residual_open_gap_action_plan_fixture()
        report["action_items"][3]["priority"] = 1
        dashboard = build_dashboard(residual_open_gap_operator_action_plan_report=report)
        priority = dashboard["residual_operator_priority"]
        self.assertEqual(priority["source_status"], "LOADED")
        self.assertEqual(priority["status"], "INVALID")
        self.assertFalse(priority["live_order_allowed"])
        self.assertFalse(priority["scale_up_allowed"])
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")

    def test_dashboard_rejects_residual_operator_evidence_progress_permission_drift(self):
        report = residual_operator_evidence_progress_fixture()
        report["live_ready_write_allowed"] = True
        dashboard = build_dashboard(residual_operator_evidence_progress_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        progress = dashboard["residual_operator_evidence_progress"]
        self.assertEqual(progress["source_status"], "LOADED")
        self.assertEqual(progress["status"], "INVALID")
        self.assertFalse(progress["live_ready_write_allowed"])
        self.assertFalse(progress["live_order_allowed"])
        self.assertFalse(progress["scale_up_allowed"])

    def test_dashboard_rejects_completion_acceptance_permission_drift(self):
        report = residual_operator_evidence_completion_acceptance_fixture()
        report["operator_completion_acceptance_items"][0]["live_order_allowed"] = True
        dashboard = build_dashboard(residual_operator_evidence_completion_acceptance_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        completion = dashboard["residual_operator_evidence_completion_acceptance"]
        self.assertEqual(completion["source_status"], "LOADED")
        self.assertEqual(completion["status"], "INVALID")
        self.assertFalse(completion["live_order_allowed"])
        self.assertFalse(completion["live_ready_write_allowed"])
        self.assertFalse(completion["scale_up_allowed"])

    def test_dashboard_rejects_residual_operator_decision_card_permission_drift(self):
        report = residual_operator_evidence_progress_fixture()
        report["operator_decision_cards"][0]["live_order_allowed"] = True
        dashboard = build_dashboard(residual_operator_evidence_progress_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        progress = dashboard["residual_operator_evidence_progress"]
        self.assertEqual(progress["source_status"], "LOADED")
        self.assertEqual(progress["status"], "INVALID")
        self.assertFalse(progress["live_order_allowed"])
        self.assertFalse(progress["scale_up_allowed"])

    def test_dashboard_rejects_residual_operator_decision_card_runtime_blocker_drift(self):
        report = residual_operator_evidence_progress_fixture()
        report["operator_decision_cards"][0]["user_runtime_required_for_next_non_live_patch"] = True
        dashboard = build_dashboard(residual_operator_evidence_progress_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        progress = dashboard["residual_operator_evidence_progress"]
        self.assertEqual(progress["status"], "INVALID")
        self.assertFalse(progress["user_runtime_required_for_next_non_live_patch"])

    def test_dashboard_rejects_operator_reconciliation_review_card_permission_drift(self):
        report = residual_operator_reconciliation_review_cards_fixture()
        report["review_cards"][0]["current_evidence_write_allowed"] = True
        report["review_cards"][0]["live_order_allowed"] = True
        dashboard = build_dashboard(residual_operator_reconciliation_review_cards_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        review = dashboard["residual_operator_reconciliation_review_cards"]
        self.assertEqual(review["source_status"], "LOADED")
        self.assertEqual(review["status"], "INVALID")
        self.assertFalse(review["current_evidence_write_allowed"])
        self.assertFalse(review["live_order_allowed"])
        self.assertFalse(review["scale_up_allowed"])

    def test_dashboard_rejects_operator_reconciliation_review_source_binding_drift(self):
        report = residual_operator_reconciliation_review_cards_fixture()
        report["source_hashes_verified"] = False
        report["operator_resolution_current_evidence_write_allowed_count"] = 1
        dashboard = build_dashboard(residual_operator_reconciliation_review_cards_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        review = dashboard["residual_operator_reconciliation_review_cards"]
        self.assertEqual(review["status"], "INVALID")
        self.assertFalse(review["source_hashes_verified"])
        self.assertEqual(review["operator_resolution_current_evidence_write_allowed_count"], 0)

    def test_dashboard_rejects_operator_reconciliation_intake_permission_drift(self):
        report = residual_operator_reconciliation_intake_preflight_fixture()
        report["intake_items"][0]["current_evidence_write_allowed"] = True
        report["intake_items"][0]["review_ready"] = True
        report["live_ready_write_allowed"] = True
        dashboard = build_dashboard(residual_operator_reconciliation_intake_preflight_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        intake = dashboard["residual_operator_reconciliation_intake_preflight"]
        self.assertEqual(intake["source_status"], "LOADED")
        self.assertEqual(intake["status"], "INVALID")
        self.assertFalse(intake["current_evidence_write_allowed"])
        self.assertFalse(intake["live_ready_write_allowed"])
        self.assertFalse(intake["live_order_allowed"])
        self.assertFalse(intake["scale_up_allowed"])

    def test_dashboard_rejects_operator_reconciliation_intake_ready_drift(self):
        report = residual_operator_reconciliation_intake_preflight_fixture()
        report["ready_for_review_intake_item_count"] = 1
        report["accepted_intake_item_count"] = 1
        report["operator_reconciliation_submission_manifest_status"] = "VALIDATED"
        dashboard = build_dashboard(residual_operator_reconciliation_intake_preflight_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        intake = dashboard["residual_operator_reconciliation_intake_preflight"]
        self.assertEqual(intake["status"], "INVALID")
        self.assertEqual(intake["ready_for_review_intake_item_count"], 0)
        self.assertEqual(intake["accepted_intake_item_count"], 0)

    def test_dashboard_rejects_operator_submission_manifest_preflight_permission_drift(self):
        report = residual_operator_reconciliation_submission_manifest_preflight_fixture()
        report["operator_submission_accepted"] = True
        report["current_evidence_write_allowed"] = True
        report["live_ready_write_allowed"] = True
        dashboard = build_dashboard(residual_operator_reconciliation_submission_manifest_preflight_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        manifest = dashboard["residual_operator_reconciliation_submission_manifest_preflight"]
        self.assertEqual(manifest["source_status"], "LOADED")
        self.assertEqual(manifest["status"], "INVALID")
        self.assertFalse(manifest["operator_submission_accepted"])
        self.assertFalse(manifest["current_evidence_write_allowed"])
        self.assertFalse(manifest["live_ready_write_allowed"])
        self.assertFalse(manifest["live_order_allowed"])
        self.assertFalse(manifest["scale_up_allowed"])

    def test_dashboard_rejects_operator_submission_manifest_preflight_structural_drift(self):
        report = residual_operator_reconciliation_submission_manifest_preflight_fixture()
        report["manifest_preflight_status"] = "BLOCKED_MANIFEST_STRUCTURAL_REVIEW_ONLY"
        report["manifest_schema_validation_status"] = "PASS_STRUCTURAL_ONLY"
        report["operator_submission_present"] = True
        report["manifest_structural_check_only"] = True
        report["manifest_item_count"] = 32
        report["missing_manifest_item_count"] = 1
        dashboard = build_dashboard(residual_operator_reconciliation_submission_manifest_preflight_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        manifest = dashboard["residual_operator_reconciliation_submission_manifest_preflight"]
        self.assertEqual(manifest["source_status"], "LOADED")
        self.assertEqual(manifest["status"], "INVALID")
        self.assertFalse(manifest["operator_submission_validated"])
        self.assertFalse(manifest["operator_submission_accepted"])

    def test_dashboard_rejects_operator_submission_template_packet_permission_drift(self):
        report = residual_operator_reconciliation_submission_template_packet_fixture()
        report["actual_submission_manifest_written_by_this_patch"] = True
        report["operator_submission_accepted"] = True
        report["current_evidence_write_allowed"] = True
        report["live_ready_write_allowed"] = True
        dashboard = build_dashboard(residual_operator_reconciliation_submission_template_packet_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        template = dashboard["residual_operator_reconciliation_submission_template_packet"]
        self.assertEqual(template["source_status"], "LOADED")
        self.assertEqual(template["status"], "INVALID")
        self.assertFalse(template["actual_submission_manifest_written_by_this_patch"])
        self.assertFalse(template["operator_submission_accepted"])
        self.assertFalse(template["current_evidence_write_allowed"])
        self.assertFalse(template["live_ready_write_allowed"])
        self.assertFalse(template["live_order_allowed"])
        self.assertFalse(template["scale_up_allowed"])

    def test_dashboard_rejects_operator_submission_template_packet_scope_drift(self):
        report = residual_operator_reconciliation_submission_template_packet_fixture()
        report["template_packet_scope"] = "EVIDENCE_PACKAGE"
        report["template_manifest_item_count"] = 31
        dashboard = build_dashboard(residual_operator_reconciliation_submission_template_packet_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        template = dashboard["residual_operator_reconciliation_submission_template_packet"]
        self.assertEqual(template["source_status"], "LOADED")
        self.assertEqual(template["status"], "INVALID")
        self.assertFalse(template["operator_submission_validated"])
        self.assertFalse(template["operator_submission_accepted"])

    def test_dashboard_rejects_operator_submission_security_quarantine_permission_drift(self):
        report = residual_operator_reconciliation_submission_security_quarantine_fixture()
        report["evidence_file_content_read"] = True
        report["secret_pattern_content_scan_performed"] = True
        report["operator_submission_accepted"] = True
        report["current_evidence_write_allowed"] = True
        report["live_ready_write_allowed"] = True
        dashboard = build_dashboard(residual_operator_reconciliation_submission_security_quarantine_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        quarantine = dashboard["residual_operator_reconciliation_submission_security_quarantine"]
        self.assertEqual(quarantine["source_status"], "LOADED")
        self.assertEqual(quarantine["status"], "INVALID")
        self.assertFalse(quarantine["evidence_file_content_read"])
        self.assertFalse(quarantine["secret_pattern_content_scan_performed"])
        self.assertFalse(quarantine["operator_submission_accepted"])
        self.assertFalse(quarantine["current_evidence_write_allowed"])
        self.assertFalse(quarantine["live_ready_write_allowed"])
        self.assertFalse(quarantine["live_order_allowed"])
        self.assertFalse(quarantine["scale_up_allowed"])

    def test_dashboard_rejects_operator_submission_security_quarantine_policy_drift(self):
        report = residual_operator_reconciliation_submission_security_quarantine_fixture()
        report["quarantine_scope"] = "CONTENT_SCAN"
        report["allowed_artifact_extensions"] = [".json"]
        report["security_control_count"] = 3
        dashboard = build_dashboard(residual_operator_reconciliation_submission_security_quarantine_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        quarantine = dashboard["residual_operator_reconciliation_submission_security_quarantine"]
        self.assertEqual(quarantine["source_status"], "LOADED")
        self.assertEqual(quarantine["status"], "INVALID")
        self.assertFalse(quarantine["current_evidence_write_allowed"])
        self.assertFalse(quarantine["live_order_allowed"])
        self.assertFalse(quarantine["scale_up_allowed"])

    def test_dashboard_rejects_operator_submission_review_queue_permission_drift(self):
        report = residual_operator_reconciliation_submission_review_queue_fixture()
        report["operator_submission_accepted"] = True
        report["evidence_file_content_read"] = True
        report["current_evidence_write_allowed"] = True
        report["live_ready_write_allowed"] = True
        report["live_order_allowed"] = True
        dashboard = build_dashboard(residual_operator_reconciliation_submission_review_queue_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        queue = dashboard["residual_operator_reconciliation_submission_review_queue"]
        self.assertEqual(queue["source_status"], "LOADED")
        self.assertEqual(queue["status"], "INVALID")
        self.assertFalse(queue["operator_submission_accepted"])
        self.assertFalse(queue["evidence_file_content_read"])
        self.assertFalse(queue["current_evidence_write_allowed"])
        self.assertFalse(queue["live_ready_write_allowed"])
        self.assertFalse(queue["live_order_allowed"])
        self.assertFalse(queue["scale_up_allowed"])

    def test_dashboard_rejects_operator_submission_review_queue_order_drift(self):
        report = residual_operator_reconciliation_submission_review_queue_fixture()
        report["review_order_locked"] = False
        report["review_ready_phase_count"] = 1
        report["review_steps"] = list(reversed(report["review_steps"]))
        dashboard = build_dashboard(residual_operator_reconciliation_submission_review_queue_report=report)
        result = validate_read_only_dashboard_shell(dashboard)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.blocker_code, "LIVE_FINAL_GUARD_FAILED")
        queue = dashboard["residual_operator_reconciliation_submission_review_queue"]
        self.assertEqual(queue["source_status"], "LOADED")
        self.assertEqual(queue["status"], "INVALID")
        self.assertFalse(queue["current_evidence_write_allowed"])
        self.assertFalse(queue["live_order_allowed"])
        self.assertFalse(queue["scale_up_allowed"])

    def test_dashboard_visual_layout_contract_blocks_cramped_regression(self):
        html = render_dashboard_html(build_dashboard())
        result = validate_dashboard_visual_layout_contract(html)
        self.assertEqual(result.status, "PASS", result.message)

        cramped = html.replace(
            "grid-template-columns: repeat(auto-fit, minmax(min(100%, 190px), 1fr));",
            "grid-template-columns: repeat(5, minmax(0, 1fr));",
        )
        result = validate_dashboard_visual_layout_contract(cramped)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.blocker_code, "SCHEMA_IDENTITY_MISMATCH")

    def test_dashboard_freshness_header_summarizes_long_source_list(self):
        dashboard = build_dashboard()
        dashboard["source_artifacts"] = [
            {
                "artifact_id": f"SOURCE_{index}_WITH_LONG_NAME",
                "filename": f"source_{index}_with_long_name.json",
                "freshness_status": "PASS" if index % 2 == 0 else "STALE",
                "truth_role": "dashboard_serving_truth",
            }
            for index in range(24)
        ]
        html = render_dashboard_html(dashboard)
        result = validate_dashboard_visual_layout_contract(html)
        self.assertEqual(result.status, "PASS", result.message)

        freshness_start = html.index('<section class="freshness-strip" data-dashboard-freshness')
        freshness_end = html.index("</section>", freshness_start)
        freshness_section = html[freshness_start:freshness_end]
        self.assertIn("Total 24", freshness_section)
        self.assertIn("PASS 12", freshness_section)
        self.assertIn("Attention 12", freshness_section)
        self.assertNotIn("SOURCE_0_WITH_LONG_NAME=PASS", freshness_section)
        self.assertNotIn("SOURCE_23_WITH_LONG_NAME=STALE", freshness_section)
        self.assertIn('data-source-status="SOURCE_23_WITH_LONG_NAME=STALE"', html)

    def test_dashboard_visual_layout_contract_requires_persistent_detail_keys(self):
        html = render_dashboard_html(build_dashboard())
        missing_stable_key = html.replace(' data-detail-key="main-detail-drawer"', "")
        result = validate_dashboard_visual_layout_contract(missing_stable_key)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("detail_main_key", result.message)

    def test_dashboard_html_exposes_safe_missing_truth(self):
        summary, _, startup_probe = build_inputs()
        dashboard = build_read_only_dashboard_shell(
            exchange="UPBIT",
            market_type="KRW_SPOT",
            mode="PAPER",
            session_id="test_read_only_dashboard_missing_truth",
            summary=summary,
            heartbeat=None,
            startup_probe=startup_probe,
        )
        html = render_dashboard_html(dashboard)
        self.assertIn("Heartbeat needs refresh", html)
        self.assertIn("Rerun the PAPER launcher", html)
        self.assertIn("operation-yellow", html)
        self.assertIn("stability-yellow", html)
        self.assertIn("longrun-yellow", html)
        self.assertIn("operator-action-yellow", html)
        self.assertIn("Primary Blocker", html)
        self.assertIn(str(dashboard["blocking_reason"]), html)
        self.assertIn("STALE", html)
        self.assertIn("live_order_allowed=false", html)

    def test_read_only_dashboard_validator_passes_current_contract(self):
        results = run_validators(["read_only_dashboard_validator"])
        self.assertEqual(results[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
