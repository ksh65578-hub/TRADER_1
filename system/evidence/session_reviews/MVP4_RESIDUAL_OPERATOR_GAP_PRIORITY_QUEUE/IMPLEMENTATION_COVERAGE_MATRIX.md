# Implementation Coverage Matrix

Patch: `MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_OPERATOR_GAP_PRIORITY_QUEUE_20260506_001`

| Area | Defect Grade | Session Finding | Patch / Acceptance |
| --- | --- | --- | --- |
| strategy / regime / entry / exit | Medium | Residual evidence tasks could distract from strategy work. | Priority queue keeps strategy changes behind evidence/reconciliation blockers. |
| expected edge / fee / slippage / funding | Medium | Profitability maturity remains open. | Queue keeps optimizer evidence maturity open and does not claim edge closure. |
| signal grading / parameter search / competition | Medium | Optimizer maturity can be confused with readiness. | Dashboard states evidence maturity is after operator/ledger work. |
| paper / shadow / replay / micro-live / live | Critical | Operator could jump to live evidence before PAPER reconciliation. | Queue fixes operator reconciliation, ledger rerun, PAPER/SHADOW evidence before live evidence. |
| LIVE_READY snapshot / live gating / fail-closed | Critical | A next-action list can be mistaken for permission. | Priority surface has live_ready_write_allowed=false and live flags false. |
| risk engine / drawdown / cooling / kill switch | High | Scale-up blocker might be hidden behind other tasks. | Scale-up remains last priority and scale_up_allowed=false. |
| exchange / market_type / namespace separation | High | Upbit evidence could be inferred into Binance. | No cross-exchange readiness is generated; Binance remains scaffold-only through existing progress report. |
| Upbit spot / Binance spot / futures | High | Binance implementation is not ready for runtime claims. | Patch is display-only and does not add Binance readiness. |
| order lifecycle / execution quality / partial fill | Critical | Dashboard actions must not call order paths. | No controls or adapters are added; HTML tests reject buttons/forms. |
| ledger / reconciliation / idempotency | High | Ledger rerun gaps remain interleaved with operator gaps. | Queue makes ledger rerun second after operator reconciliation. |
| data health / stale / gap / duplicate / clock drift | High | Gap counts can drift silently. | Validator checks queue gap count equals open gap count and item gap_ids. |
| concurrency / race condition / restart recovery | Medium | Concurrent closure attempts must be ordered. | Conflict rule fixes safety > no-trade > operator > ledger > evidence order. |
| dashboard / USER_STATUS_SUMMARY / user simplicity | High | Non-expert user needed one first action. | First screen now shows Priority #1 and First action. |
| validator / schema / registry / acceptance artifacts | High | New dashboard projection needed closed schema. | Schema and validation cover priority object and drift cases. |
| testing / pytest / paper run proof / live block proof | High | Priority and live drift needed tests. | Added deterministic queue, permission drift, and ordering drift tests. |
| security / secrets / API key safety | Critical | External evidence tasks could imply credential use. | Live/API key use stays forbidden and live proof records no credentials. |
| deployment / packaging / git hygiene / pycache / generated artifacts | Medium | Runtime output dirt should not be staged. | Changed artifact list excludes system/runtime local monitor output. |
| tax/accounting/export readiness | Low | No export path changed. | Left unchanged; no live/accounting mutation. |
| KRW cashflow / profit conversion / withdrawal policy | Low | No withdrawal path changed. | Left blocked; scale-up and live remain false. |
| overfitting / walk-forward / out-of-sample validation | Medium | Optimizer maturity remains open. | Priority queue keeps maturity evidence open until audited evidence exists. |
