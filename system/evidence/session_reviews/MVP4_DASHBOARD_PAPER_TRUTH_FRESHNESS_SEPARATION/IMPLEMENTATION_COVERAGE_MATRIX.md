# IMPLEMENTATION_COVERAGE_MATRIX

generated_at_utc: 2026-05-05T23:26:23Z
patch_id: MVP4_DASHBOARD_PAPER_TRUTH_FRESHNESS_SEPARATION_20260506_001

| # | Area | Severity | Current finding | Closure / acceptance |
|---|---|---|---|---|
| 1 | strategy / regime / entry / exit | High | Closed formulas exist, but long-run PAPER evidence is still below promotion needs. | Keep strategy output paper/shadow-only until evidence gates pass. |
| 2 | expected edge / fee / slippage / funding | High | Cost-aware scoring exists; realized execution evidence is immature. | Block candidates when cost model is missing or net edge is non-positive. |
| 3 | signal grading / parameter search / strategy competition | High | Score gates exist; sample counts are not mature. | Weak signals no-trade and promotion requires trade/sample thresholds. |
| 4 | paper / shadow / replay / micro-live / live | Critical | PAPER snapshot display improved; long-run proof remains open. | PAPER/SHADOW evidence must accumulate before live readiness review. |
| 5 | LIVE_READY snapshot / live gating / fail-closed | Critical | No valid LIVE_READY snapshot. | All live and scale flags remain false. |
| 6 | risk engine / drawdown / cooling / kill switch | High | Risk gates remain fail-closed; scale-up is ineligible. | Drawdown/cooling/kill switch continue to block entry or sizing. |
| 7 | exchange / market_type / namespace separation | High | Upbit PAPER evidence cannot transfer to Binance. | Exchange/market_type/mode evidence remains scoped. |
| 8 | Upbit spot / Binance spot / Binance futures 1x long-short | High | Upbit PAPER path is deepest; Binance is still surface/scaffold. | Binance remains not live-ready and clearly separated. |
| 9 | order lifecycle / execution quality / partial fill | High | PAPER ledger is visible; live execution is still blocked. | No adapter call without live final guard and external evidence. |
| 10 | ledger / reconciliation / idempotency | Critical | Last verified simulated ledger values can now remain visible as stale truth. | Reconciliation gaps remain open and cannot be closed by display changes. |
| 11 | data health / stale data / gap / duplicate / clock drift | High | This patch clarifies stale semantics without lowering TTL. | Stale means last verified value, not runtime proof. |
| 12 | concurrency / race condition / restart recovery | Medium | Writer activation remains blocked; snapshot display is read-only. | No single-writer ownership or live mutation changed. |
| 13 | dashboard / USER_STATUS_SUMMARY / user simplicity | High | Patched this session. | First screen can show portfolio values and exact freshness/runtime/writer meaning. |
| 14 | validator / schema / registry / acceptance artifacts | Medium | Schema and tests were extended. | Validators and patch result must pass. |
| 15 | testing / pytest / paper run proof / live block proof | High | Tests prove display semantics; no new PAPER run was started. | Artifacts state live blocked and no runtime gap closure. |
| 16 | security / secrets / API key safety | Critical | No credentials or private API use. | Credential/API usage remains forbidden. |
| 17 | deployment / packaging / git hygiene / pycache / generated artifacts | Medium | Generated artifacts are tracked through read cache. | Runtime local monitor output is not intentionally staged. |
| 18 | tax/accounting/export readiness | Low | No tax/export change. | Leave export work for a scoped non-live patch. |
| 19 | KRW cashflow / profit conversion / withdrawal policy | Medium | PAPER KRW values are clearer but simulated. | No live cashflow or withdrawal action. |
| 20 | overfitting / walk-forward / out-of-sample validation | High | Optimizer evidence remains immature. | OOS/walk-forward evidence required before promotion. |
