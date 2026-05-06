# IMPLEMENTATION_COVERAGE_MATRIX

generated_at_utc: 2026-05-06T04:10:22Z
patch_id: MVP4_DASHBOARD_PAPER_SHADOW_ACTIONABILITY_VISIBILITY_20260506_001

| # | Area | Severity | Current finding | Closure / acceptance |
|---|---|---|---|---|
| 1 | strategy / regime / entry / exit | High | Strategy formulas exist; PAPER/SHADOW sample maturity remains blocking. | Actionability now points to missing evidence dimensions. |
| 2 | expected edge / fee / slippage / funding | High | Cost evidence remains mandatory. | Missing cost evidence maps to REASON_OR_COST_EVIDENCE_DEFICIT. |
| 3 | signal grading / parameter search / strategy competition | High | Scorecard input cannot become promotion evidence. | PAPER_SCORECARD_INPUT_READY_ONLY remains distinct from long-run readiness. |
| 4 | paper / shadow / replay / micro-live / live | Critical | Patched PAPER/SHADOW dashboard display only. | No micro-live/live path touched. |
| 5 | LIVE_READY snapshot / live gating / fail-closed | Critical | LIVE_READY remains unwritten. | All live flags remain false. |
| 6 | risk engine / drawdown / cooling / kill switch | High | Risk scaling unchanged. | Scale-up remains false. |
| 7 | exchange / market_type / namespace separation | High | MVP-4 scope remains Upbit KRW spot. | Binance evidence cannot be inferred. |
| 8 | Upbit spot / Binance spot / Binance futures 1x long-short | High | Upbit PAPER path is deepest; Binance remains scaffold/surface. | No Binance readiness claim. |
| 9 | order lifecycle / execution quality / partial fill | High | No order-capable path touched. | Actionability is dashboard-only. |
| 10 | ledger / reconciliation / idempotency | Critical | Open reconciliation gaps remain. | No current-evidence writer or gap closure. |
| 11 | data health / stale data / gap / duplicate / clock drift | High | Stale PAPER/SHADOW evidence now maps to DATA_FRESHNESS_DEFICIT. | TTL remains enforced. |
| 12 | concurrency / race condition / restart recovery | Medium | No writer ownership changed. | Runtime source binding remains non-live. |
| 13 | dashboard / USER_STATUS_SUMMARY / user simplicity | Medium | Dashboard now gives user-level next evidence action. | Next Evidence and Deficit Counts are visible. |
| 14 | validator / schema / registry / acceptance artifacts | Medium | Dashboard schema, validator, tests, and evidence updated. | Validators pass. |
| 15 | testing / pytest / paper run proof / live block proof | High | No new runtime run started. | Runtime proof not claimed. |
| 16 | security / secrets / API key safety | Critical | No credential/API use. | Live endpoints untouched. |
| 17 | deployment / packaging / git hygiene / pycache / generated artifacts | Medium | Generated artifacts tracked. | Runtime output remains unstaged. |
| 18 | tax/accounting/export readiness | Low | No tax/export change. | Future scoped patch. |
| 19 | KRW cashflow / profit conversion / withdrawal policy | Medium | PAPER values remain simulated. | No cashflow action. |
| 20 | overfitting / walk-forward / out-of-sample validation | High | OOS evidence remains immature. | No optimizer promotion. |
