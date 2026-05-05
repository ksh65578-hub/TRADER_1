# Implementation Coverage Matrix

Patch: `MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_OPERATOR_RESOLUTION_AUDIT_BINDING_20260506_001`

| Area | Defect Grade | Session Finding | Patch / Acceptance |
| --- | --- | --- | --- |
| strategy / regime / entry / exit | Medium | No strategy promotion can rely on unresolved current-evidence repair artifacts. | Source-bound operator resolution audit remains unresolved and blocks promotion. |
| expected edge / fee / slippage / funding | Medium | Cost-aware scorecards remain evidence-only until reconciliation is clean. | No optimizer or scorecard live claim is created. |
| signal grading / parameter search / strategy competition | Medium | Candidate ranking can be misleading if source resolution is hidden. | Dashboard priority now exposes source-bound unresolved audit status. |
| paper / shadow / replay / micro-live / live | Critical | Post-rerun PAPER evidence could be mistaken for current evidence. | Current-evidence write/use counts are fixed at 0 and validator-blocked on drift. |
| LIVE_READY snapshot / live gating / fail-closed | Critical | A resolution audit must not imply LIVE_READY. | All live flags and LIVE_READY writes remain false. |
| risk engine / drawdown / cooling / kill switch | High | Scale-up must not follow unresolved reconciliation. | scale_up_allowed remains false and no risk scale-up path changed. |
| exchange / market_type / namespace separation | High | Upbit PAPER audit evidence must not transfer to Binance readiness. | Scope is explicit UPBIT/KRW_SPOT/PAPER source binding only. |
| Upbit spot / Binance spot / Binance futures | High | Binance remains surface/scaffold until scoped evidence exists. | No Binance runtime or live readiness is generated. |
| order lifecycle / execution quality / partial fill | Critical | No order lifecycle path may consume unresolved evidence. | No order adapter, endpoint, or credential path is touched. |
| ledger / reconciliation / idempotency | High | Post-rerun reconciliation is still unresolved. | Resolution audit binding keeps ledger/current evidence blocked. |
| data health / stale / gap / duplicate / clock drift | High | Source hash drift could invalidate operator audit. | Source review guidance and decision audit hash-match fields are schema/test bound. |
| concurrency / race condition / restart recovery | Medium | Concurrent current-evidence writes must remain impossible from this route. | Write and usable counters are zero and validator-blocked on drift. |
| dashboard / USER_STATUS_SUMMARY / user simplicity | High | Operator view needs the exact first blocker reason. | Live card shows operator resolution binding, unresolved/resolved counts, and safe next action. |
| validator / schema / registry / acceptance artifacts | High | New binding fields need closed schema coverage. | Residual binding schema and dashboard shell schema require the new fields. |
| testing / pytest / paper run proof / live block proof | High | Drift cases needed negative tests. | Contract and dashboard tests cover source hash and write/use drift. |
| security / secrets / API key safety | Critical | External/live tasks must not load credentials. | Patch records credential/private API/order path as false. |
| deployment / packaging / git hygiene / pycache / generated artifacts | Medium | Runtime monitor dirt must not be staged. | Patch references runtime source evidence without modifying runtime output. |
| tax/accounting/export readiness | Low | No accounting/export change is safe before reconciliation. | No tax/accounting/export path changed. |
| KRW cashflow / profit conversion / withdrawal policy | Low | No withdrawal/cashflow policy can be enabled. | No cashflow or withdrawal logic changed. |
| overfitting / walk-forward / out-of-sample validation | Medium | Unresolved reconciliation can contaminate optimizer assessment. | Current evidence remains blocked before optimizer/live assessment. |
