# IMPLEMENTATION_COVERAGE_MATRIX

generated_at_utc: 2026-05-06T01:24:22Z
patch_id: MVP4_DASHBOARD_AUDITED_WRITER_ACTIVATION_PREFLIGHT_20260506_001

| # | Area | Severity | Current finding | Closure / acceptance |
|---|---|---|---|---|
| 1 | strategy / regime / entry / exit | High | Closed strategy formulas exist; runtime evidence remains immature. | Keep strategy outputs paper/shadow-only until evidence floors pass. |
| 2 | expected edge / fee / slippage / funding | High | Cost-aware net edge exists; realized sample evidence remains limited. | Negative or missing cost model remains no-trade. |
| 3 | signal grading / parameter search / strategy competition | High | Promotion requires more samples than currently present. | Weak/immature candidates remain blocked from live. |
| 4 | paper / shadow / replay / micro-live / live | Critical | Patched PAPER/SHADOW evidence activation-preflight display. | Short-window and bounded profile evidence cannot become live permission. |
| 5 | LIVE_READY snapshot / live gating / fail-closed | Critical | No LIVE_READY snapshot is written. | All live flags remain false. |
| 6 | risk engine / drawdown / cooling / kill switch | High | Risk scaling remains unavailable. | Scale-up remains false. |
| 7 | exchange / market_type / namespace separation | High | Upbit PAPER evidence is still not transferable to Binance. | Namespace remains scoped. |
| 8 | Upbit spot / Binance spot / Binance futures 1x long-short | High | Upbit PAPER path is deepest; Binance remains surface/scaffold. | No Binance readiness inference. |
| 9 | order lifecycle / execution quality / partial fill | High | No order-capable path is touched. | Display-only dashboard patch. |
| 10 | ledger / reconciliation / idempotency | Critical | Ledger values can display while reconciliation gaps stay open. | No open gap closure. |
| 11 | data health / stale data / gap / duplicate / clock drift | High | Activation preflight makes stale/current distinction clearer. | TTL and long-run floors unchanged. |
| 12 | concurrency / race condition / restart recovery | Medium | No writer ownership changed. | Continuous writer remains blocked. |
| 13 | dashboard / USER_STATUS_SUMMARY / user simplicity | High | Patched this session. | First screen now shows activation preflight. |
| 14 | validator / schema / registry / acceptance artifacts | Medium | Schema and tests extended. | Patch result and validators must pass. |
| 15 | testing / pytest / paper run proof / live block proof | High | Tests prove activation preflight invariants; no new PAPER run was started. | Runtime proof not claimed. |
| 16 | security / secrets / API key safety | Critical | No credentials or private API use. | Credential/API usage remains forbidden. |
| 17 | deployment / packaging / git hygiene / pycache / generated artifacts | Medium | Generated artifacts tracked. | Runtime monitor output remains unstaged unless intended. |
| 18 | tax/accounting/export readiness | Low | No tax/export change. | Leave for later scoped non-live patch. |
| 19 | KRW cashflow / profit conversion / withdrawal policy | Medium | PAPER values remain simulated. | No live cashflow action. |
| 20 | overfitting / walk-forward / out-of-sample validation | High | OOS evidence remains immature. | No optimizer promotion. |
