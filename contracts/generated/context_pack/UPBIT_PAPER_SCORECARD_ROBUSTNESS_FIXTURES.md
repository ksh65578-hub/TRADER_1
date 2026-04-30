# UPBIT_PAPER_SCORECARD_ROBUSTNESS_FIXTURES

context_pack_id: UPBIT_PAPER_SCORECARD_ROBUSTNESS_FIXTURES
task_class: PROFIT_CONVERGENCE_MVP3
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

## Included Sections

- SECTION_TOKEN_NAVIGATION
- SECTION_PROFIT_CONVERGENCE_REINFORCEMENT
- SECTION_PROFITABILITY_OPTIMIZER
- SECTION_LIVE_FINAL_GUARD
- SECTION_UPBIT_PAPER_RUNTIME

## Requirement IDs

- REQ-MVP4-UPBIT-PAPER-SCORECARD-ROBUSTNESS-FIXTURES
- REQ-MVP4-UPBIT-PAPER-RUNTIME-SCORECARD-BRIDGE
- REQ-MVP4-PAPER-RUNTIME-CANDIDATE-NET-EV-AFTER-COST
- REQ-MVP4-OOS-ROBUSTNESS-SCHEMA-HARDENING

## Acceptance Checklist

- Ranking-eligible scorecards require OOS, walk-forward, and bootstrap source evidence ids.
- Runtime scorecard builder cannot treat three generic evidence ids as robustness closure.
- Validator negative fixtures fail closed when any robustness source type is missing.
- Ranking-eligible scorecards remain PAPER_SCORECARD_INPUT_ONLY and never create live or scale-up permission.

## Known Omissions By Design

- This patch adds stricter fixture and validator coverage; it does not create external OOS, walk-forward, bootstrap, or live burn-in evidence.
- This patch does not enable MVP-5 or live readiness.

## Conflict Resolution

TRADER_1.md wins over this context pack. This file is a read cache, not authority.
