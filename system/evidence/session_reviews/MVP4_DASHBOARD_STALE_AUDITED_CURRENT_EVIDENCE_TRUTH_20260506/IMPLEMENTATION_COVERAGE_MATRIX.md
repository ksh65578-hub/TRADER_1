# IMPLEMENTATION_COVERAGE_MATRIX

generated_at_utc: 2026-05-05T22:10:19Z
patch_id: MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_20260506_002

| # | Area | Severity | Current finding | Closure / acceptance |
|---|---|---|---|---|
| 1 | strategy / regime / entry / exit | High | Quantitative formulas exist, but long-run PAPER evidence is insufficient. | Keep no-trade on stale, negative edge, or downtrend spot-long conflict. |
| 2 | expected edge / fee / slippage / funding | High | Cost-aware surfaces exist; realized execution evidence remains immature. | Require total_cost > 0 and net_expected_edge > 0 before candidate use. |
| 3 | signal grading / parameter search / strategy competition | High | Scorecards and optimizer state exist, but sample counts remain below promotion thresholds. | Weak signals block entry; trade_count and PF gates remain mandatory. |
| 4 | paper / shadow / replay / micro-live / live | Critical | PAPER writer exists; long-run and SHADOW evidence remain open gaps. | Do not promote without PAPER/SHADOW evidence and live block proof. |
| 5 | LIVE_READY snapshot / live gating / fail-closed | Critical | No valid LIVE_READY snapshot; external evidence is missing. | live_order_ready=false and live_order_allowed=false. |
| 6 | risk engine / drawdown / cooling / kill switch | High | Risk formulas exist; scale-up remains ineligible. | Drawdown/cooling blocks sizing and entries. |
| 7 | exchange / market_type / namespace separation | High | Upbit evidence cannot transfer to Binance spot/futures. | Namespace-scoped evidence only. |
| 8 | Upbit spot / Binance spot / Binance futures 1x long-short | High | Upbit PAPER path is deepest; Binance remains surface/scaffold. | Binance stays not-yet-live and surface-only. |
| 9 | order lifecycle / execution quality / partial fill | High | PAPER ledger and idempotency exist; live execution is not enabled. | No adapter call without live final guard pass. |
| 10 | ledger / reconciliation / idempotency | Critical | Audited writer exists; residual reconciliation gaps remain open. | Preserve stale ledger truth as STALE, not UNVERIFIED. |
| 11 | data health / stale data / gap / duplicate / clock drift | High | This patch hardens stale display truth; missing data remains blocked. | Fresh cannot be mislabeled stale and stale cannot be VERIFIED. |
| 12 | concurrency / race condition / restart recovery | Medium | Writer lock/idempotency manifests exist; long-run restart proof remains incomplete. | Single-writer and idempotency validators stay required. |
| 13 | dashboard / USER_STATUS_SUMMARY / user simplicity | High | Patched this session. | First screen distinguishes normal, portfolio, and live blockers. |
| 14 | validator / schema / registry / acceptance artifacts | Medium | Session artifacts and patch_result are updated. | All required validators must PASS. |
| 15 | testing / pytest / paper run proof / live block proof | High | Tests prove stale display behavior and live blocks; no new run was executed. | Artifacts must state no live permission. |
| 16 | security / secrets / API key safety | Critical | No credential or private endpoint use in this patch. | Live/API key use remains forbidden. |
| 17 | deployment / packaging / git hygiene / pycache / generated artifacts | Medium | Bytecode-free and read-cache validators are part of acceptance. | Do not stage runtime local monitor outputs. |
| 18 | tax/accounting/export readiness | Low | No tax/export patch this session. | Keep evidence-only until ledger export work is scoped. |
| 19 | KRW cashflow / profit conversion / withdrawal policy | Medium | PAPER KRW equity is visible as stale or verified display truth only. | No withdrawal or live cashflow action. |
| 20 | overfitting / walk-forward / out-of-sample validation | High | Optimizer/convergence evidence remains immature. | Promotion requires OOS, walk-forward, and sample gates. |
