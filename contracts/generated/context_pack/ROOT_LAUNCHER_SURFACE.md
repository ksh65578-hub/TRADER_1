# ROOT_LAUNCHER_SURFACE

context_pack_id: ROOT_LAUNCHER_SURFACE
task_class: MVP4_ROOT_LAUNCHER_OPERATOR_VISIBILITY_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_MVP1_ROOT_LAUNCHER_FOUR", "SECTION_MVP1_SAFE_BOOT_SEQUENCE", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT", "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE"]
included_schema_ids: ["trader1.root_launcher_report.v1"]
included_validator_ids: ["root_launcher_guard_validator", "root_launcher_surface_validator", "live_final_guard_validator"]
included_artifact_ids: ["UPBIT_PAPER.py", "UPBIT_LIVE.py", "BINANCE_PAPER.py", "BINANCE_LIVE.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- root launchers write operator-visible reports
- interactive console execution pauses before closing
- non-interactive automation does not pause
- live launchers remain hard-blocked
- live_order_ready=false, live_order_allowed=false, can_live_trade=false

known_omissions_by_design:
- no live key loading
- no live order API
- no exchange account access
- no LIVE_READY snapshot write
- no MVP-5 live-enabling behavior

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T21:45:14Z
