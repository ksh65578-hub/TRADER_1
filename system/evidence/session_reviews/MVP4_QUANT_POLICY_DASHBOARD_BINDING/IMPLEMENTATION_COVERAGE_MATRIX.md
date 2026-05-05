# Implementation Coverage Matrix

Patch: `MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_QUANT_POLICY_DASHBOARD_BINDING_20260506_001`

| Area | Defect Grade | Session Finding | Patch / Acceptance |
| --- | --- | --- | --- |
| strategy / regime / entry / exit | High | Quant policy was not visible in operator status. | Summary and dashboard bind policy as dashboard-only. |
| expected edge / fee / slippage / funding | High | Net edge could remain buried in reports. | Dashboard shows net edge and cost displays. |
| signal grading / parameter search / competition | High | Signal grade lacked operator-facing context. | Dashboard shows signal grade/score with live blocked. |
| paper / shadow / replay / live | Critical | Policy summary could be mistaken for live permission. | All projected flags are false and validator-blocked. |
| LIVE_READY / gating / fail-closed | Critical | LIVE_READY remains absent. | LIVE_READY_MISSING remains the primary blocker for Upbit. |
| risk / drawdown / kill switch | High | Risk scale-up must stay separate. | Policy projection keeps scale_up_allowed=false. |
| exchange / market namespace | High | Upbit policy could leak into Binance readiness. | Binance summaries stay scaffold-only with Binance blocker codes. |
| Upbit / Binance spot / futures | High | Binance runtime remains surface only. | Binance dashboard policy does not use Upbit evidence. |
| order lifecycle / execution quality | Medium | No order path should read dashboard policy. | Policy binding is summary/dashboard only. |
| ledger / reconciliation / idempotency | High | Open ledger gaps remain. | No gap was closed; reconciliation blockers remain listed. |
| data health / stale / duplicates | High | Stale policy could be trusted. | Dashboard status has stale/invalid states and blockers. |
| concurrency / restart recovery | Medium | Writer locks remain separate. | No runtime writer or config mutation added. |
| dashboard / user simplicity | High | Non-expert user needed concise strategy review. | HTML adds a folded quantitative strategy panel. |
| validators / schema / registry | High | New fields needed closed schema checks. | Summary/dashboard schemas and validators now cover policy binding. |
| testing / live block proof | High | Policy live drift needed negative tests. | Added summary/dashboard live-flag drift tests. |
| security / API key safety | Critical | Live credentials remain forbidden. | No credential/API path added. |
| deployment / bundle hygiene | Medium | Generated/runtime dirt must stay unstaged. | Patch artifact list excludes system/runtime and source manifest dirt. |
| tax/accounting/export | Low | No tax export changed. | No scope change; remains future work. |
| KRW cashflow / withdrawal | Low | No withdrawal logic changed. | No scope change; live/withdrawal paths remain blocked. |
| overfit / walk-forward / OOS | High | Policy thresholds must remain visible. | 100/300 sample thresholds are projected in dashboard and validator. |
