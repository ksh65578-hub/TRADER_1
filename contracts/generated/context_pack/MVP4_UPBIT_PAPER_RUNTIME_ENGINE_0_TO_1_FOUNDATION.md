# MVP4_UPBIT_PAPER_RUNTIME_ENGINE_0_TO_1_FOUNDATION

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_ENGINE_0_TO_1_FOUNDATION
task_class: MVP4_UPBIT_PAPER_RUNTIME_ENGINE_0_TO_1_FOUNDATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

Included section ids:
- SECTION_UPBIT_PAPER_RUNTIME
- SECTION_CANONICAL_MARKET_EVENT
- SECTION_LEDGER_RECONCILIATION
- SECTION_DASHBOARD_OPERATOR_UX
- SECTION_LIVE_FINAL_GUARD

Included requirement ids:
- REQ-MVP4-UPBIT-PAPER-RUNTIME-ENGINE-0-TO-1
- REQ-MVP4-PAPER-PORTFOLIO-PNL-DETAIL
- REQ-MVP4-PAPER-RUNTIME-CANDIDATE-NET-EV-AFTER-COST
- REQ-MVP4-DASHBOARD-PAPER-RUNTIME-PORTFOLIO-BINDING
- REQ-MVP4-LIVE-SAFETY-INVARIANTS

Acceptance checklist:
- Upbit PAPER runtime uses fixture/public market data only.
- Strategy candidates expose edge, cost, net EV after cost, and no-trade reason.
- Positive PAPER-only candidate writes simulated fill, PAPER ledger events, and portfolio/PnL snapshot.
- Negative edge stays NO_TRADE and writes no fill ledger events.
- Launcher dashboard binds fresh same-session PAPER runtime evidence into portfolio, positions, candidates, and market context.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

Known omissions by design:
- No real exchange/private/account call.
- No LIVE_ENABLING_PATCH.
- No persistent public market data collector yet.
- No MVP-5 live readiness claim.

Conflict resolution rule: TRADER_1.md wins over this generated context pack.
