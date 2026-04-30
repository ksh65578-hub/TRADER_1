# TOKEN_EFFICIENT_IMPLEMENTATION_NAVIGATION_OVERLAY_START

## 0G. Token-efficient implementation navigation and precision-preservation overlay

document status: active additive implementation navigation hardening supplement

This overlay improves AGENTS.md so AI compiler work can conserve tokens while still implementing TRADER_1 with full precision. It does not delete, replace, shrink, summarize, move, or weaken any existing AGENTS baseline content, TRADER_1 authority content, automatic profit-convergence reinforcement content, profitability-convergence optimizer content, validator requirement, patch class, live blocker, promotion gate, retained archive, or safety rule. Existing AGENTS content remains preserved below this overlay and remains available for exact implementation detail, traceability, coverage, and retained-archive lookup.

```yaml
overlay_schema_id: trader1.agents_token_efficient_implementation_navigation_overlay.v1
patch_class: DOC_CONTRACT_PATCH
patch_date: "2026-04-28T09:12:27Z"
patch_method: additive_navigation_overlay_plus_verbatim_baseline_preservation
patch_input_agents_file: "AGENTS(158).md"
patch_input_agents_sha256: "669f3b1cc753f63435be38b23af16dcc2b75a7bf7f3266259f5aac3af23245ba"
patch_input_trader1_file: "TRADER_1(150).md"
patch_input_trader1_sha256: "5c8e61807cf8ade9797f7ec5a4c2615a965d314586eaf26278a16f9f32c7a31b"
delivered_paired_trader1_file: "TRADER_1_151_token_efficient_navigation.md"
delivered_paired_trader1_sha256: "ff6c3046fd64c3b16e874f3770ccb57e04b1e1e75775125382f285f33bd0052b"
file_split: false
removed_requirements: []
detail_reduction_allowed: false
semantic_reduction_allowed: false
retained_archive_preserved: true
baseline_body_preserved_verbatim: true
existing_detail_preserved: true
source_replacement_created: false
summary_as_replacement_allowed: false
token_optimization_method: read_routing_indexing_context_cache
profit_guarantee_created: false
live_order_ready_after_document_patch: false
live_order_allowed_after_document_patch: false
can_live_trade_after_document_patch: false
```

### 0G.1 Implementation purpose

The AI compiler must conserve tokens by reading the correct source regions, not by ignoring requirements.

```text
less reading -> allowed only through exact section routing
less reading -> allowed only with source hashes and source references
less reading -> allowed only when implementation depth is preserved
less reading -> allowed only when validators and evidence remain required
```

Forbidden:

```text
using a generated working view as authority
using a context pack as authority
summarizing away source requirements
skipping exact schema fields when generating schema
skipping validator dependencies when implementing validator logic
skipping fixture cases for live-affecting validators
using retained archive as execution authority
```

Default live state remains:

```text
live_order_ready=false
live_order_allowed=false
can_live_trade=false
```

### 0G.2 Active implementation read surface

Before coding, the AI compiler should read in this order.

```text
1. TRADER_1 0G token-efficient authority navigation overlay
2. TRADER_1 0F automatic profit-convergence reinforcement overlay
3. TRADER_1 0E profitability-convergence optimizer overlay
4. TRADER_1 active contract pack
5. TRADER_1 live safety, LIVE_READY writer guard, live final guard
6. AGENTS 0G token-efficient implementation navigation overlay
7. AGENTS 0F automatic profit-convergence implementation reinforcement overlay
8. AGENTS active implementation guide
9. generated authority_section_map and requirement_index when present
10. generated task-specific context_pack when present
11. exact source sections required by current task class
12. retained archive only when coverage or traceability requires it
```

Rules:

```text
Do not read full TRADER_1.md or full AGENTS.md by default when generated navigation artifacts are fresh.
Do not read retained archive by default.
Do not implement from a summary label alone.
Exact field generation requires exact source expansion.
Exact validator implementation requires exact validator and dependency expansion.
```

### 0G.3 First navigation synchronization patch

The first implementation patch after this overlay should be a non-live contract synchronization patch when navigation artifacts are missing.

Required sequence:

```text
1. verify TRADER_1 and AGENTS hashes or mark authority_hash_checked=false
2. generate contracts/generated/authority_section_map.json
3. generate contracts/generated/requirement_index.json
4. generate contracts/generated/requirement_artifact_matrix.json
5. generate contracts/generated/read_cache_manifest.json
6. generate contracts/generated/ACTIVE_WORKING_VIEW.md
7. generate task-specific context packs for current MVP
8. generate contracts/generated/current_implementation_state.json
9. create or update system/evidence/implementation_patch_ledger.json
10. emit patch_result with live_order_allowed_after=false
```

This patch is not a LIVE_ENABLING_PATCH.

### 0G.4 Generated navigation artifacts

Required generated artifacts:

```text
contracts/generated/authority_section_map.json
contracts/generated/requirement_index.json
contracts/generated/requirement_artifact_matrix.json
contracts/generated/read_cache_manifest.json
contracts/generated/ACTIVE_WORKING_VIEW.md
contracts/generated/context_pack/MVP0_CONTRACT_BASELINE.md
contracts/generated/context_pack/SCHEMA_GENERATION.md
contracts/generated/context_pack/VALIDATOR_IMPLEMENTATION.md
contracts/generated/context_pack/PROFIT_CONVERGENCE_MVP0.md
contracts/generated/context_pack/PROFIT_CONVERGENCE_MVP3.md
contracts/generated/context_pack/OPTIMIZER_MVP3.md
contracts/generated/context_pack/LIVE_BLOCKED_TEST.md
contracts/generated/current_implementation_state.json
system/evidence/implementation_patch_ledger.json
```

Generated artifact rules:

```text
generated navigation artifact is not authority
generated navigation artifact cannot replace source requirements
generated navigation artifact must include source section IDs and source hashes
generated navigation artifact must preserve exact source references
generated navigation artifact must be invalidated when source hash changes
generated navigation artifact cannot create live permission
```

### 0G.5 Task classification before reading

Before source expansion, classify the task.

Task classes:

```text
MVP0_CONTRACT_BASELINE
SCHEMA_GENERATION
VALIDATOR_IMPLEMENTATION
PROFIT_CONVERGENCE_MVP0
PROFIT_CONVERGENCE_MVP1
PROFIT_CONVERGENCE_MVP2
PROFIT_CONVERGENCE_MVP3
OPTIMIZER_MVP3
LIVE_BLOCKED_TEST
EXCHANGE_ADAPTER
DASHBOARD_UX
BUNDLE_SECURITY
DOCUMENT_NORMALIZATION
RETAINED_ARCHIVE_COVERAGE
```

Rules:

```text
task_class missing -> classify before coding
task_class unknown -> use MVP0_CONTRACT_BASELINE or safe scaffold only
task_class live-affecting -> include SECTION_LIVE_GATE and SECTION_LIVE_FINAL_GUARD
task_class optimizer or convergence -> include corresponding slices and live safety dependencies
```

### 0G.6 Read routing implementation rules

The AI compiler must use the read routing table from TRADER_1 0G. If generated `authority_section_map.json` exists and is fresh, use it to locate exact sections. If it is missing or stale, regenerate it before large implementation work.

Rules:

```text
required_section_ids must be read before changing affected files
expanded_section_ids must be recorded in patch_result
forbidden_default_sections must not be read unless expansion trigger exists
retained_archive_read must be false unless coverage or traceability requires it
full_document_read must be false unless exact expansion trigger exists
```

### 0G.7 Implementation depth enforcement

Do not use token efficiency to implement shallowly.

Closed implementation depth levels:

```text
DEPTH_0_SCAFFOLD_ONLY
DEPTH_1_SCHEMA_AND_ARTIFACT_STRUCTURE
DEPTH_2_VALIDATOR_LOGIC
DEPTH_3_NEGATIVE_FIXTURES
DEPTH_4_RUNTIME_INTEGRATION
DEPTH_5_EVIDENCE_AND_STAGE_GATE
DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY
```

Minimum depth requirements:

```text
MVP0 registry and schema -> DEPTH_1_SCHEMA_AND_ARTIFACT_STRUCTURE
live-blocking validator -> DEPTH_3_NEGATIVE_FIXTURES
optimizer ranking path -> DEPTH_4_RUNTIME_INTEGRATION
convergence memory path -> DEPTH_4_RUNTIME_INTEGRATION
convergence risk scaling -> DEPTH_5_EVIDENCE_AND_STAGE_GATE
dashboard readiness display -> DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY
```

If the context pack lacks enough detail to meet the required depth, expand the exact source section.

### 0G.8 Section and requirement mapping

The AI compiler must preserve mapping from source requirements to concrete implementation outputs.

`requirement_index.json` must include:

```text
requirement_id
source_section_id
source_file
source_heading
full_text_marker
authority_level
requirement_title
requirement_kind
schema_ids
validator_ids
artifact_ids
test_ids
mvp_stage
implementation_depth_min
blocking_level
live_affecting
read_when
depends_on
source_text_sha256
implementation_status
test_status
```

`requirement_artifact_matrix.json` must include:

```text
requirement_id
section_id
schema_files
validator_files
test_files
fixture_files
runtime_modules
evidence_artifacts
dashboard_artifacts
patch_result_fields
minimum_depth
live_affecting
status
```

If a live-affecting requirement has no mapped validator or test, keep `live_order_allowed=false`.

### 0G.9 Schema expansion on demand

When performing schema work, do not expand all schemas by default.

Default schema read:

```text
schema_id
required fields
linked requirement_ids
linked validator_ids
linked artifact_ids
blocking conditions
```

Full schema expansion is required when:

```text
generating schema file
implementing schema validator
validating exact field behavior
resolving schema conflict
generating registry projection
validating LIVE_READY writer input
validating patch_result
```

### 0G.10 Validator group navigation

Validator groups may be used for planning and read routing only. They do not replace individual validator definitions.

Required groups:

```text
VALIDATOR_GROUP:MVP0_CORE
VALIDATOR_GROUP:LIVE_SAFETY_CORE
VALIDATOR_GROUP:OPTIMIZER_CORE
VALIDATOR_GROUP:OPTIMIZER_ROBUSTNESS
VALIDATOR_GROUP:CONVERGENCE_CORE
VALIDATOR_GROUP:CONVERGENCE_RISK_SCALE
```

When implementing a validator group:

```text
expand each individual validator definition
expand dependencies
expand input and output schema
add PASS fixture
add FAIL fixture
add BLOCKED fixture for live-affecting validator
record validators_run actual command and status
```

### 0G.11 Optimizer and convergence slice navigation

Use topic slices to avoid reading unrelated optimizer or convergence text.

Optimizer slices:

```text
OPT_SLICE_CONFIG
OPT_SLICE_OBJECTIVE
OPT_SLICE_SCORECARD
OPT_SLICE_RANKING
OPT_SLICE_EXPLOITATION
OPT_SLICE_NARROWING
OPT_SLICE_SYMBOL_REGIME_FIT
OPT_SLICE_EXECUTION_FEEDBACK
OPT_SLICE_OVERFIT
OPT_SLICE_CONVERGENCE_CLAIM
OPT_SLICE_GUARDRAIL
OPT_SLICE_DASHBOARD
```

Convergence slices:

```text
CONV_SLICE_OBJECTIVE
CONV_SLICE_MEMORY
CONV_SLICE_CONTROLLER
CONV_SLICE_REGIME_ADAPTATION
CONV_SLICE_FAILURE_LEARNING
CONV_SLICE_OVERFIT_DEFENSE
CONV_SLICE_EXECUTION_CALIBRATION
CONV_SLICE_RISK_SCALING
CONV_SLICE_SURVIVAL
CONV_SLICE_ASSESSMENT
CONV_SLICE_DASHBOARD
```

Rules:

```text
slice read cannot omit linked schema
slice read cannot omit linked validator
slice read cannot omit linked fixture
slice read cannot omit live safety dependency
slice read cannot create direct live permission
```

### 0G.12 Context pack rules

Generated context packs must include only task-relevant source extracts and source references. They are read caches, not authority.

Each context pack must include:

```text
context_pack_id
task_class
source_trader1_sha256
source_agents_sha256
included_section_ids
included_requirement_ids
included_schema_ids
included_validator_ids
included_artifact_ids
source_section_hashes
acceptance_checklist
known_omissions_by_design
conflict_resolution_rule
```

Rules:

```text
known_omissions_by_design are not requirement deletion
context pack conflict with source -> source wins
context pack stale -> regenerate before use
context pack cannot be used for live readiness claim unless source hashes match
```

### 0G.13 Current implementation state

`current_implementation_state.json` must track progress so the AI compiler does not reread full source to infer state.

Required fields:

```text
state_schema_id
created_at_utc
updated_at_utc
trader1_sha256
agents_sha256
current_mvp
completed_requirement_ids
implemented_schema_ids
implemented_validator_ids
untested_validator_ids
blocked_requirement_ids
open_contract_gap_ids
last_patch_id
last_patch_result_hash
next_allowed_task_class
live_order_ready
live_order_allowed
can_live_trade
state_hash
```

Rules:

```text
current implementation state is not authority
if state conflicts with source authority, source authority wins
if state hash is stale, regenerate from patch ledger and validator results
```

### 0G.14 Patch result extension

Every navigation-aware patch result must include these fields or stricter equivalents.

```text
token_navigation_patch
active_read_surface_used
task_class
required_section_ids
expanded_section_ids
forbidden_default_sections_respected
authority_section_map_status
requirement_index_status
requirement_artifact_matrix_status
read_cache_manifest_status
context_pack_status
current_implementation_state_status
retained_archive_read
full_document_read
read_cache_invalidated
next_task_class
next_required_section_ids
next_optional_section_ids
next_forbidden_default_sections
```

Required values:

```text
removed_requirements=[]
file_split=false
detail_reduction_allowed=false
semantic_reduction_allowed=false
non-LIVE_ENABLING_PATCH -> live_order_allowed_after=false
```

### 0G.15 Future patch writing rule

Future patches must be delta-oriented.

```text
future_overlay_delta_only=true
```

Rules:

```text
reference existing requirement_id and section_id
write only the new strengthening delta
do not restate full live gate unless changing it
do not restate full validator list unless changing it
do not restate full enum list unless changing it
preserve existing details
state removed_requirements=[]
state no live permission created
```

### 0G.16 Exact expansion trigger

Full document or retained archive expansion is allowed only when one of these triggers exists.

```text
authority_section_map missing
authority_section_map stale
read_cache_manifest stale
authority hash changed
section hash mismatch
contract conflict detected
schema extraction required
validator implementation requires exact fields
requirement preservation validation required
coverage validation required
retained archive coverage lookup required
user explicitly requests full document review
```

Patch result must record the trigger.

### 0G.17 Acceptance condition

A token-efficient implementation patch is acceptable only if:

```text
all linked requirement_ids remain mapped
all live-affecting requirements preserve blockers
schema and validator exact details are expanded when needed
retained_archive_preserved=true
removed_requirements=[]
file_split=false
detail_reduction_allowed=false
semantic_reduction_allowed=false
live_order_allowed_after=false unless independent LIVE_ENABLING evidence exists
```

### 0G.18 One-line implementation navigation rule

```text
Implement with less repeated reading, not less rigor. Use section IDs, requirement IDs, generated read caches, context packs, validator groups, schema references, and exact expansion triggers to conserve tokens, while preserving full source authority, exact implementation detail, validator coverage, evidence quality, live safety, retained archive preservation, and requirement traceability.
```

# TOKEN_EFFICIENT_IMPLEMENTATION_NAVIGATION_OVERLAY_END


# AUTOMATIC_PROFIT_CONVERGENCE_IMPLEMENTATION_REINFORCEMENT_OVERLAY_START

## 0F. Automatic profit-convergence implementation reinforcement overlay

document status: active additive implementation hardening supplement

This overlay strengthens AGENTS.md so the AI compiler can implement the reinforced automatic profit-convergence system without deleting, replacing, shrinking, summarizing, moving, or weakening any existing AGENTS baseline content, TRADER_1 authority content, optimizer overlay content, validator requirement, patch class, live blocker, promotion gate, retained archive, or safety rule. Existing AGENTS content remains preserved verbatim below this overlay and remains available for implementation detail, traceability, coverage, and retained-archive lookup.

```yaml
overlay_schema_id: trader1.agents_automatic_profit_convergence_implementation_reinforcement_overlay.v1
patch_class: DOC_CONTRACT_PATCH
patch_date: "2026-04-28T07:30:00Z"
patch_method: additive_overlay_plus_verbatim_baseline_preservation
patch_input_agents_file: "AGENTS(145).md"
patch_input_agents_sha256: "7fd23928215f62919407b69d8512b498479064af139148c85dbf69f864a34994"
patch_input_trader1_file: "TRADER_1(137).md"
patch_input_trader1_sha256: "8c3f5901d7acbb5dbacfcea2dfdcc19da3be7c0a5eacfc95957aaf41a38aab8a"
delivered_paired_trader1_file: "TRADER_1(138)_automatic_profit_convergence_reinforced.md"
delivered_paired_trader1_sha256: "5c8e61807cf8ade9797f7ec5a4c2615a965d314586eaf26278a16f9f32c7a31b"
file_split: false
removed_requirements: []
detail_reduction_allowed: false
semantic_reduction_allowed: false
retained_archive_preserved: true
baseline_body_preserved_verbatim: true
existing_detail_preserved: true
profit_guarantee_created: false
live_order_ready_after_document_patch: false
live_order_allowed_after_document_patch: false
can_live_trade_after_document_patch: false
```

### 0F.1 Implementation read priority

Implementation agents must apply this overlay together with the paired TRADER_1 automatic profit-convergence reinforcement overlay.

Read priority:

```text
1. TRADER_1.md active contract pack
2. TRADER_1.md automatic profit-convergence reinforcement overlay
3. TRADER_1.md profitability-convergence optimizer overlay
4. TRADER_1.md execution contract body and active hardening supplements
5. AGENTS.md active implementation guide and this overlay
6. registry, schema, validator, generated contract, source tree, and manifest artifacts
7. preserved baseline and retained archive only for coverage, traceability, backlog, and omitted-detail lookup
```

AGENTS.md cannot weaken TRADER_1.md. Repository code cannot override TRADER_1.md. Runtime artifacts cannot override TRADER_1.md.

### 0F.2 AI compiler implementation meaning

Implement the profit-convergence system as a stateful, evidence-backed, safety-gated improvement loop. Do not implement it as a simple score sorter, one-shot backtest optimizer, raw PnL ranker, or direct live configuration writer.

Required interpretation:

```text
profit convergence implementation -> iterative improvement loop
profit convergence implementation -> no profit guarantee
profit convergence implementation -> no direct live permission
profit convergence implementation -> no direct live config mutation
profit convergence implementation -> no direct LIVE_READY snapshot write
profit convergence implementation -> no direct scale-up
```

Default live state remains:

```text
live_order_ready=false
live_order_allowed=false
can_live_trade=false
```

### 0F.3 MVP implementation sequence

The reinforced convergence layer must be implemented in staged patches.

```text
MVP-0:
  add registry groups
  add schema files
  add validator ids
  add fixture catalog placeholders
  add convergence artifact paths
  add patch_result fields
  generate external authority manifest when possible
  keep convergence logic UNTESTED when not implemented
  keep live_order_allowed=false

MVP-1:
  implement namespace-safe convergence artifact scaffolds
  implement memory store interfaces without live write access
  implement dashboard placeholder projection as analysis-only
  implement convergence_objective_profile scaffold
  keep all outputs research-only

MVP-2:
  implement replay and paper metric collection
  implement strategy_performance_memory and parameter_outcome_memory writes
  implement objective component extraction
  implement failure_analysis_report scaffold
  implement resource budget checks
  do not implement live mutation

MVP-3:
  implement convergence objective scoring
  implement optimizer_memory_state
  implement failure root-cause classifier
  implement exploration_exploitation_policy
  implement market_regime_adaptation_report
  implement overfit and robustness validator integration
  implement paper/shadow convergence cycle reports

MVP-4:
  implement read-only live observation feedback when official API verification exists
  implement execution calibration from realized execution fields
  implement model_drift_report
  implement dashboard convergence status
  keep live_order_ready=false unless independent live review evidence exists

MVP-5:
  allow convergence output to become LIVE_READY_CANDIDATE_WRITER_INPUT only after all existing promotion gates PASS
  require live_ready_snapshot_writer_validator PASS before any LIVE_READY snapshot write
  do not allow convergence layer to write LIVE_READY snapshot directly
  do not allow convergence layer to mutate live config directly

MVP-6/MVP-7:
  extend convergence memory and regime adaptation to Binance spot and futures only with exchange and market_type scoped evidence
  never transfer convergence evidence across exchange or market_type by inference
```

### 0F.4 Required files for MVP-0 convergence scaffold

Create or update these schema files during the first convergence-related contract patch.

```text
contracts/schema/convergence_objective_profile.schema.json
contracts/schema/optimizer_memory_state.schema.json
contracts/schema/strategy_performance_memory.schema.json
contracts/schema/failure_analysis_report.schema.json
contracts/schema/market_regime_adaptation_report.schema.json
contracts/schema/exploration_exploitation_policy.schema.json
contracts/schema/risk_scaling_decision.schema.json
contracts/schema/convergence_assessment_report.schema.json
contracts/schema/model_drift_report.schema.json
contracts/schema/live_burn_in_feedback_report.schema.json
contracts/schema/profit_convergence_cycle_report.schema.json
```

Create or update these artifact directories.

```text
system/reports/<exchange>/<market_type>/<mode>/<session_id>/convergence/
system/evidence/<exchange>/<market_type>/<mode>/<session_id>/convergence/
system/runtime/<exchange>/<market_type>/<mode>/<session_id>/convergence/
system/snapshots/<exchange>/<market_type>/<mode>/CONVERGENCE/
tests/convergence/
tests/convergence/fixtures/
```

### 0F.5 Required registry additions

Add or generate these registry groups before convergence runtime logic is implemented.

```text
profit_convergence_state
profit_convergence_objective_component
profit_convergence_penalty_component
profit_convergence_memory_type
profit_convergence_root_cause
profit_convergence_controller_state
profit_convergence_action
profit_convergence_claim_type
risk_scaling_decision_type
risk_scaling_trigger
market_regime_adaptation_signal
failure_pattern_status
model_drift_status
survival_layer_action
convergence_blocker_code
```

All convergence blocker codes that can block promotion, live readiness, scale-up, or operator-facing readiness must be mapped into closed no_trade_reason or live_blocker_code.

### 0F.6 Required validators

Add these validators or stricter equivalents.

```text
convergence_objective_profile_validator
optimizer_memory_state_validator
strategy_performance_memory_validator
failure_analysis_validator
root_cause_classifier_validator
market_regime_adaptation_validator
exploration_exploitation_policy_validator
risk_scaling_decision_validator
convergence_assessment_validator
model_drift_validator
live_burn_in_feedback_validator
profit_convergence_cycle_validator
survival_layer_validator
scale_up_eligibility_validator
convergence_claim_validator_v2
```

Validator implementation rules:

```text
validator missing -> UNTESTED
validator not run -> UNTESTED
UNTESTED -> not READY
TIMEOUT -> not PASS
STALE -> unusable for convergence claim
convergence validator FAIL -> affected convergence path BLOCKED
convergence validator FAIL cannot be overridden by score
parent validator cannot PASS when required dependency is FAIL, BLOCKED, UNTESTED, STALE, or TIMEOUT
```

### 0F.7 Validator dependency rules

```text
convergence_assessment_validator depends on convergence_objective_profile_validator, optimizer_memory_state_validator, strategy_performance_memory_validator, overfit_diagnostic_validator, execution_feedback_loop_validator, model_drift_validator, and coverage_index_validator.
risk_scaling_decision_validator depends on live_burn_in_feedback_validator when scale-up is proposed, paper_live_parity_validator, execution_quality_measurement_validator, survival_layer_validator, and operator_control_validator.
exploration_exploitation_policy_validator depends on ranking_stability_validator, optimizer_resource_budget_validator, overfit_diagnostic_validator, convergence_assessment_validator, and exploration_resource_validator.
market_regime_adaptation_validator depends on symbol_strategy_regime_fit_validator, data_freshness_validator, regime_scope_validator, timeframe_scope_validator, and official_api_verification_validator when live observation is used.
failure_analysis_validator depends on realized execution measurement when execution failure is claimed.
scale_up_eligibility_validator depends on risk_scaling_decision_validator, live_burn_in_feedback_validator, paper_live_parity_validator, live_final_guard_validator, emergency_flatten_validator, ledger_reconciliation_validator, and all live-blocking validators.
```

### 0F.8 Required convergence test fixtures

Add PASS, FAIL, and BLOCKED fixtures for every convergence-related validator that can influence promotion, scale-up, live readiness, or operator-facing readiness.

Minimum fixture cases:

```text
raw PnL improves while net_ev_after_cost is negative -> FAIL
short-window improvement with OOS failure -> BLOCKED
paper success with live burn-in slippage divergence -> BLOCKED
high score with UNKNOWN_ROOT_CAUSE in live-affecting failure -> BLOCKED
regime shift with unchanged promoted strategy -> FAIL
risk scale-up without live burn-in evidence -> BLOCKED
risk scale-up with drawdown breach -> BLOCKED
optimizer memory missing for repeated candidate -> BLOCKED
memory forgets failed candidate without audit -> FAIL
model drift detected while convergence claim remains ROBUSTLY_IMPROVING -> FAIL
scale-up eligible while emergency protection unavailable -> BLOCKED
survival layer blocked while optimizer score improves -> BLOCKED
candidate repeats same failure root cause across cycles -> FAIL or BLOCKED
execution feedback worsens but objective score improves without penalty -> FAIL
```

### 0F.9 Implementation algorithm

For every profit-convergence cycle:

```text
1. load TRADER_1.md, AGENTS.md, registry, schemas, authority manifest, and convergence config
2. verify namespace: exchange, market_type, mode, session_id, strategy_id, strategy_build_id, parameter_hash, timeframe_scope, regime_scope
3. verify live_order_ready=false and live_order_allowed=false unless independent LIVE_ENABLING evidence exists
4. load candidate evidence from REPLAY, PAPER, SHADOW, or READ_ONLY only
5. reject raw cross-mode joins
6. load optimizer_memory_state
7. update strategy_performance_memory from validated evidence
8. classify failures and write failure_analysis_report
9. compute convergence_objective_score
10. run overfit and robustness diagnostics
11. run market_regime_adaptation_report
12. update exploration_exploitation_policy
13. generate or update candidate scorecards
14. apply risk_scaling_decision only as recommendation
15. write convergence_assessment_report
16. write model_drift_report when drift signals exist
17. write profit_convergence_cycle_report
18. run required validators
19. write evidence manifest
20. emit live_order_ready=false and live_order_allowed=false unless independent LIVE_ENABLING evidence exists
```

### 0F.10 Memory implementation rules

Memory stores must be append-auditable and hash-linked.

Required behavior:

```text
preserve failed candidates
preserve retired candidates
preserve blocked candidates
preserve previous search space
preserve previous objective profile version
preserve root-cause history
preserve risk-scaling decisions
preserve model drift history
```

Forbidden behavior:

```text
silent memory reset
forgetting failed candidate without audit
using memory to bypass validator
using memory to bypass promotion threshold
using memory to bypass live blocker
using memory to write LIVE_READY snapshot
using memory to mutate live config
```

### 0F.11 Failure learning implementation rules

For each failure:

```text
create failure_analysis_report
assign primary_root_cause_code
assign secondary_root_cause_codes when known
link source_evidence_ids
link affected candidate_id and strategy_unit
record recommended_response
record blocks_promotion
record blocks_live_order
```

When root cause is unknown:

```text
UNKNOWN_ROOT_CAUSE in research-only scope -> candidate remains auditable and cannot promote
UNKNOWN_ROOT_CAUSE in live-affecting scope -> live_order_allowed=false for affected scope
```

### 0F.12 Risk scaling implementation rules

Scale-down recommendations may be immediate when risk-reducing. Scale-up recommendations must remain proposals until validators pass.

Implementation must enforce:

```text
risk scale-up requires scale_up_eligibility_validator PASS
risk scale-up requires live_burn_in_feedback_validator PASS
risk scale-up requires paper_live_parity_validator PASS
risk scale-up requires execution_quality_measurement_validator PASS
risk scale-up requires survival_layer_validator PASS
risk scale-up requires operator policy permission
risk scale-up cannot be created by optimizer score alone
risk scale-up cannot bypass risk veto
risk scale-up cannot bypass emergency protection
```

### 0F.13 Dashboard implementation rules

Dashboard may display convergence status only as analysis status unless exact live readiness and live_order_allowed evidence exists.

Required display fields:

```text
convergence_state
optimizer_status
optimizer_stage
optimizer_maturity_level
objective_score_band
primary_convergence_blocker_code
primary_convergence_blocker_message
last_convergence_assessment_id
last_memory_state_id
last_failure_analysis_id
last_risk_scaling_decision_id
live_order_ready
live_order_allowed
scale_up_eligible
```

Forbidden wording:

```text
profit guaranteed
automatic profit
converged to profit
self-optimizing live
safe to scale automatically
ready to size up
```

Allowed wording:

```text
CONVERGENCE: COLLECTING, LIVE ORDERS BLOCKED
CONVERGENCE: LOCALLY IMPROVING, PROMOTION BLOCKED
CONVERGENCE: ROBUSTLY IMPROVING, NOT LIVE_READY
CONVERGENCE: WRITER INPUT ELIGIBLE, SNAPSHOT NOT WRITTEN
CONVERGENCE: LIVE BURN-IN OBSERVING, SCALE-UP BLOCKED
CONVERGENCE: SCALE-UP ELIGIBLE, OPERATOR AND VALIDATORS REQUIRED
```

### 0F.14 Patch result extension

Every convergence-related patch result must include:

```text
profit_convergence_patch
convergence_layer_changed
convergence_state_before
convergence_state_after
objective_profile_changed
memory_schema_changed
memory_state_id
failure_analysis_required
failure_analysis_status
exploration_exploitation_policy_changed
regime_adaptation_changed
risk_scaling_policy_changed
survival_layer_changed
convergence_validators_required
convergence_validators_run
convergence_guardrail_result
convergence_live_mutation_detected
convergence_live_order_allowed_after
scale_up_eligibility_changed
scale_up_allowed_after
```

Required values:

```text
convergence_live_mutation_detected=false
convergence_live_order_allowed_after=false unless independent LIVE_ENABLING evidence exists
scale_up_allowed_after=false unless scale_up_eligibility_validator PASS and live_order_allowed remains true for exact scope
removed_requirements=[]
file_split=false
detail_reduction_allowed=false
```

### 0F.15 First implementation patch order

The first implementation patch after this overlay must not start with runtime trading behavior. It must start with contract synchronization.

Required first patch sequence:

```text
1. REGISTRY_PATCH: add convergence registry groups and blocker projection
2. SCHEMA_PATCH: add convergence schemas
3. SCHEMA_PATCH: extend patch_result.schema.json with convergence fields
4. VALIDATOR_PATCH: add convergence validators as UNTESTED scaffold
5. VALIDATOR_PATCH: add PASS, FAIL, BLOCKED fixture placeholders
6. DOC_CONTRACT_PATCH: add generated projection references
7. evidence: emit patch_result with live_order_allowed_after=false
```

### 0F.16 One-line implementation rule

```text
Implement the convergence system as a persistent, evidence-linked, failure-learning, regime-adaptive, execution-calibrated, risk-gated improvement loop. It may improve candidate selection and convergence probability, but it must never directly create profit claims, live permission, LIVE_READY snapshots, ACTIVE snapshots, live config mutations, or scale-up actions without independent validators and evidence.
```

# AUTOMATIC_PROFIT_CONVERGENCE_IMPLEMENTATION_REINFORCEMENT_OVERLAY_END


# PROFITABILITY_CONVERGENCE_OPTIMIZER_IMPLEMENTATION_OVERLAY_START

## 0E. Automatic profitability-convergence optimizer implementation overlay

document status: active additive implementation hardening supplement

This overlay adds implementation rules for the automatic profitability-convergence optimizer to this single-file AGENTS guide. It does not delete, replace, shrink, summarize, move, or weaken any existing AGENTS baseline content. Existing AGENTS content remains preserved below this overlay and remains available for implementation detail, traceability, coverage, and retained-archive lookup.

```yaml
overlay_schema_id: trader1.agents_profitability_convergence_optimizer_implementation_overlay.v1
patch_class: DOC_CONTRACT_PATCH
patch_date: "2026-04-28T06:49:25Z"
patch_method: additive_overlay_plus_verbatim_baseline_preservation
patch_input_agents_file: "AGENTS(136).md"
patch_input_agents_sha256: "d97e052ca0dd5dcd776baa93fbd92989e8a68d48bdef34c167060ae581d380b5"
patch_input_trader1_file: "TRADER_1(128).md"
patch_input_trader1_sha256: "ac00634ffedd90ef195692e21454d86958601a71bb91a190ab84deeacaa1ab9d"
delivered_paired_trader1_file: "TRADER_1_129_profitability_convergence_optimizer.md"
delivered_paired_trader1_sha256: "8c3f5901d7acbb5dbacfcea2dfdcc19da3be7c0a5eacfc95957aaf41a38aab8a"
file_split: false
removed_requirements: []
detail_reduction_allowed: false
semantic_reduction_allowed: false
retained_archive_preserved: true
baseline_body_preserved_verbatim: true
existing_detail_preserved: true
profit_guarantee_created: false
live_order_ready_after_document_patch: false
live_order_allowed_after_document_patch: false
can_live_trade_after_document_patch: false
```

### 0E.1 Active implementation priority

Implementation agents must apply this overlay together with the paired TRADER_1 profitability-convergence optimizer overlay.

Read priority:

```text
1. TRADER_1.md active contract pack
2. TRADER_1.md profitability-convergence optimizer overlay
3. TRADER_1.md execution contract body
4. TRADER_1.md active hardening supplements
5. AGENTS.md active implementation guide and this overlay
6. registry, schema, validator, generated contract, and manifest artifacts
7. preserved baseline and retained archive only for coverage, traceability, backlog, and omitted-detail lookup
```

AGENTS.md cannot weaken TRADER_1.md. Repository code cannot override TRADER_1.md. Runtime artifacts cannot override TRADER_1.md.

### 0E.2 Implementation meaning

The optimizer implementation is a system for candidate ranking, adaptive search, parameter narrowing, symbol-strategy-regime fit learning, execution-feedback learning, overfit detection, and optimizer guardrail validation.

It is not a system for guaranteed profit.

```text
optimizer implemented -> no profitability claim
optimizer run completed -> no profitability claim
optimizer winner found -> no live permission
optimizer convergence status improved -> no live permission
optimizer recommendation -> no direct live config mutation
```

Default live state remains:

```text
live_order_ready=false
live_order_allowed=false
can_live_trade=false
```

### 0E.3 MVP implementation sequence

The optimizer must not be implemented as one uncontrolled block. Use the following staged implementation sequence.

```text
MVP-0:
  add registry groups
  add schema files
  add validator ids
  add fixture catalog placeholders
  add optimizer artifact paths
  add patch_result fields
  keep optimizer implementation UNTESTED when logic is not implemented
  keep live_order_allowed=false

MVP-1:
  add optimizer namespace checks
  add safe boot handling
  add dashboard placeholder projection
  add optimizer_guardrail_report scaffold
  keep all optimizer outputs research-only

MVP-2:
  implement replay and Upbit paper metric collection
  implement candidate_scorecard creation
  implement optimizer_run_report scaffold
  implement resource budget checks
  do not implement live mutation

MVP-3:
  implement candidate ranking
  implement ranking stability check
  implement constrained exploration and local exploitation
  implement adaptive parameter narrowing proposals
  implement symbol-strategy-regime fit reports
  implement overfit diagnostics
  implement paper/shadow optimizer evidence manifest

MVP-4:
  implement read-only live observation feedback when official API verification exists
  implement execution feedback reports
  implement dashboard optimizer status
  keep live_order_ready=false unless independent live review evidence exists

MVP-5:
  allow optimizer output to become LIVE_READY_CANDIDATE_WRITER_INPUT only after all existing promotion gates PASS
  require live_ready_snapshot_writer_validator PASS before any LIVE_READY snapshot write
  do not allow optimizer to write LIVE_READY snapshot directly
  do not allow optimizer to mutate live config directly

MVP-6/MVP-7:
  extend optimizer to Binance spot and futures only with exchange and market_type scoped evidence
  never transfer optimizer evidence across exchange or market_type by inference
```

### 0E.4 Required files for MVP-0 optimizer scaffold

Create or update these files during the first optimizer-related contract patch.

```text
contracts/schema/profit_optimizer_config.schema.json
contracts/schema/candidate_scorecard.schema.json
contracts/schema/optimizer_run_report.schema.json
contracts/schema/optimization_state.schema.json
contracts/schema/search_space_snapshot.schema.json
contracts/schema/parameter_narrowing_report.schema.json
contracts/schema/symbol_strategy_regime_fit_report.schema.json
contracts/schema/optimizer_feedback_report.schema.json
contracts/schema/overfit_diagnostic_report.schema.json
contracts/schema/optimizer_recommendation_report.schema.json
contracts/schema/optimizer_guardrail_report.schema.json
```

Create or update these artifact directories.

```text
system/reports/<exchange>/<market_type>/<mode>/<session_id>/optimizer/
system/evidence/<exchange>/<market_type>/<mode>/<session_id>/optimizer/
system/runtime/<exchange>/<market_type>/<mode>/<session_id>/optimizer/
system/snapshots/<exchange>/<market_type>/<mode>/OPTIMIZER/
tests/optimizer/
tests/optimizer/fixtures/
```

### 0E.5 Required registry additions

Add or generate these registry groups before optimizer runtime logic is implemented.

```text
profit_optimizer_status
profit_optimizer_stage
profit_optimizer_output_type
profit_optimizer_maturity_level
profit_optimizer_objective_component
profit_optimizer_metric
profit_optimizer_penalty
profit_optimizer_search_policy
profit_optimizer_model_type
profit_optimizer_feedback_type
profit_optimizer_convergence_status
profit_optimizer_blocker_code
profit_optimizer_artifact_role
profit_optimizer_decision
profit_optimizer_score_band
profit_optimizer_safety_mode
```

All optimizer blocker codes that can block promotion, live readiness, or operator-facing status must be mapped into closed no_trade_reason or live_blocker_code.

### 0E.6 Required validators

Add these validators or stricter equivalents.

```text
profit_optimizer_config_validator
objective_function_validator
candidate_scorecard_validator
optimizer_run_report_validator
optimization_state_validator
search_space_snapshot_validator
candidate_ranking_validator
ranking_stability_validator
exploration_to_exploitation_validator
parameter_narrowing_validator
symbol_strategy_regime_fit_validator
execution_feedback_loop_validator
overfit_diagnostic_validator
convergence_claim_validator
optimizer_recommendation_validator
optimizer_guardrail_validator
optimizer_no_live_mutation_validator
optimizer_artifact_namespace_validator
optimizer_resource_budget_validator
optimizer_fixture_catalog_validator
```

Validator implementation rules:

```text
validator missing -> UNTESTED
validator not run -> UNTESTED
UNTESTED -> not READY
TIMEOUT -> not PASS
STALE -> unusable for optimizer convergence claim
optimizer validator FAIL -> affected optimizer path BLOCKED
optimizer validator FAIL cannot be overridden by score
```

### 0E.7 Validator dependency rules

```text
candidate_ranking_validator depends on candidate_scorecard_validator and objective_function_validator.
ranking_stability_validator depends on candidate_scorecard_validator and optimizer_run_report_validator.
exploration_to_exploitation_validator depends on ranking_stability_validator and optimizer_resource_budget_validator.
parameter_narrowing_validator depends on overfit_diagnostic_validator, search_space_snapshot_validator, walk-forward evidence, OOS evidence, and execution feedback when available.
symbol_strategy_regime_fit_validator depends on data quality, liquidity, spread, depth, volatility, and regime evidence.
execution_feedback_loop_validator depends on realized execution measurement fields and execution_quality_measurement_validator.
convergence_claim_validator depends on candidate_scorecard_validator, overfit_diagnostic_validator, execution_feedback_loop_validator, promotion_threshold_validator, paper_live_parity_validator when applicable, coverage_index_validator, and evidence_manifest_validator.
optimizer_guardrail_validator depends on optimizer_no_live_mutation_validator, live_final_guard_validator, registry_validator, schema_validator, and closed_enum_validator.
```

A parent validator cannot PASS when a required dependency is FAIL, BLOCKED, UNTESTED, STALE, or TIMEOUT.

### 0E.8 Required optimizer test fixtures

Add PASS, FAIL, and BLOCKED fixtures for every live-affecting optimizer validator.

Minimum fixture cases:

```text
raw PnL winner with negative net_ev_after_cost -> FAIL
paper winner with missing slippage -> BLOCKED
high score with HIGH overfit risk -> BLOCKED
high score with one-symbol dominance -> BLOCKED or concentration review
high score with missing holdout -> BLOCKED
ranked candidate with stale evidence -> BLOCKED
parameter narrowing with no rollback plan -> FAIL
optimizer recommendation tries live config mutation -> BLOCKED
optimizer output attempts LIVE_READY snapshot -> BLOCKED
optimizer output creates live_order_allowed=true -> BLOCKED
execution feedback worsens but score improves -> FAIL
symbol fit ignores liquidity blocker -> FAIL
regime fit transfers across market_type -> FAIL
```

### 0E.9 Implementation algorithm

For every optimizer run:

```text
1. load registry, schemas, authority manifest, and optimizer config
2. verify namespace: exchange, market_type, mode, session_id, strategy_id
3. collect candidate evidence from REPLAY, PAPER, SHADOW, or READ_ONLY only
4. reject raw cross-mode joins
5. build candidate_scorecard for every candidate
6. apply objective_function_validator
7. apply candidate_scorecard_validator
8. apply candidate_ranking_validator
9. prune duplicates and blocked candidates
10. run ranking_stability_validator
11. decide BROAD_EXPLORATION, LOCAL_EXPLOITATION, ROBUSTNESS_SWEEP, PARAMETER_NARROWING, SYMBOL_FIT_LEARNING, REGIME_FIT_LEARNING, EXECUTION_FEEDBACK, or OVERFIT_DIAGNOSTIC
12. write optimizer_run_report
13. write optimizer_guardrail_report
14. write optimizer_evidence_manifest
15. emit live_order_ready=false and live_order_allowed=false unless an independent LIVE_ENABLING evidence package exists
```

### 0E.10 Objective implementation rule

Do not rank by raw PnL only.

Default implementation must compute or explicitly mark missing:

```text
net_ev_after_cost_score
drawdown_control_score
downside_deviation_score
tail_loss_control_score
stability_score
consistency_score
sample_confidence_score
regime_robustness_score
symbol_robustness_score
execution_quality_score
fee_accuracy_score
slippage_accuracy_score
impact_accuracy_score
latency_robustness_score
capital_efficiency_score
operational_safety_score
overfit_penalty
concentration_penalty
tail_loss_penalty
cost_underestimation_penalty
resource_cost_penalty
complexity_penalty
objective_score
```

Missing objective component handling:

```text
net_ev_after_cost_score missing -> OBJECTIVE_FUNCTION_MISSING
execution_quality_score missing -> EXECUTION_QUALITY_UNTESTED
sample_confidence_score missing -> SAMPLE_INSUFFICIENT
objective_score missing -> affected candidate BLOCKED from ranking
```

### 0E.11 Ranking and selection implementation rule

Ranking produces ordering only. Ranking does not produce live permission.

Implementation must:

```text
scope ranking by exchange, market_type, mode, strategy_id, timeframe_scope, regime_scope, risk_profile, and parameter_hash
exclude hard-blocked candidates from promotion ranking
keep blocked candidates auditable
preserve challenger candidates
preserve control candidates
record tie breakers
record pruned duplicate candidates
record concentration warnings
```

### 0E.12 Exploration-to-exploitation implementation rule

The optimizer may move from exploration to exploitation only after evidence.

```text
BROAD_EXPLORATION -> LOCAL_EXPLOITATION requires ranking_stability_validator PASS
LOCAL_EXPLOITATION -> ROBUSTNESS_SWEEP requires optimizer_resource_budget_validator PASS
ROBUSTNESS_SWEEP -> PARAMETER_NARROWING requires overfit_diagnostic_validator PASS
PARAMETER_NARROWING -> PAPER_CONFIRMATION requires parameter_narrowing_validator PASS
PAPER_CONFIRMATION -> LIVE_READY_CANDIDATE_WRITER_INPUT requires all existing promotion gates PASS
```

If any transition validator is missing or UNTESTED, the transition is BLOCKED.

### 0E.13 Adaptive narrowing implementation rule

Parameter narrowing must be reversible and evidence-backed.

Implementation must:

```text
keep previous_search_space_hash
write proposed_search_space_hash
record narrowed, widened, and unchanged parameters
record supporting scorecard ids
record holdout, walk-forward, OOS, regime, symbol, and execution-feedback status
include rollback_plan_id
set narrowing_allowed_for_live=false
```

Forbidden:

```text
narrowing directly mutates live parameter bound
narrowing removes original baseline range from audit
narrowing removes control candidates
narrowing collapses to one parameter set without robustness evidence
narrowing widens risk after loss
```

### 0E.14 Symbol and regime fit implementation rule

Implement symbol-strategy-regime fit as a scored report, not as direct execution permission.

Required scoring inputs:

```text
liquidity
spread
depth
volume stability
volatility fit
trend quality
mean-reversion quality
regime stability
data freshness
data gap rate
fee impact
slippage impact
fill quality
min_notional feasibility
tick_size feasibility
correlation with existing exposure
drawdown contribution
strategy-specific realized edge
```

Rules:

```text
cold-start symbol -> candidate only
low-liquidity symbol -> no trade or exploration-only
symbol score cannot override symbol rules
symbol score cannot override liquidity or slippage blockers
regime-specific winner cannot transfer to another regime without evidence
DOWNTREND spot long remains restricted unless validated exception exists
```

### 0E.15 Execution feedback implementation rule

Execution feedback must feed ranking and narrowing.

Implementation must compare expected versus realized:

```text
fee
spread cost
slippage
market impact
latency cost
fill rate
partial fill rate
missed fill rate
reject rate
rate limit events
ambiguous transport events
reconciliation events
```

Rules:

```text
paper execution feedback cannot be treated as live execution feedback
read-only live observation may improve estimates but cannot create live permission
slippage worse than expected -> reduce score or block scale-up
impact worse than expected -> reduce symbol liquidity fit
fee mismatch -> FEE_MODEL_UNVERIFIED
fill quality poor -> EXECUTION_QUALITY_UNTESTED or BLOCKED
```

### 0E.16 Overfit diagnostic implementation rule

The optimizer must run overfit diagnostics before convergence claims or writer-input eligibility.

Required diagnostics:

```text
walk-forward validation
out-of-sample validation
bootstrap stability
parameter sensitivity
symbol concentration
regime concentration
outlier dominance
cost stress test
slippage stress test
liquidity stress test
timeframe sensitivity
data quality audit
survivorship bias check
data snooping check
multiple-comparison penalty
```

Blocking behavior:

```text
walk-forward missing -> WALK_FORWARD_MISSING
OOS missing -> OOS_MISSING
holdout missing -> HOLDOUT_MISSING
bootstrap unstable -> BOOTSTRAP_UNSTABLE
overfit risk HIGH -> promotion BLOCKED
outlier dominance FAIL -> promotion BLOCKED
parameter sensitivity extreme -> parameter_narrowing BLOCKED
```

### 0E.17 Guardrail implementation rule

Every optimizer run must produce `optimizer_guardrail_report`.

The guardrail must check:

```text
direct_live_mutation_detected
live_config_mutation_detected
live_parameter_bound_mutation_detected
active_snapshot_mutation_detected
live_order_permission_created
promotion_threshold_weakened
risk_limit_weakened
validator_requirement_weakened
namespace_violation_detected
```

Rules:

```text
any live mutation detected -> BLOCKED
live_order_permission_created=true -> BLOCKED
promotion_threshold_weakened=true -> BLOCKED
risk_limit_weakened=true -> BLOCKED
validator_requirement_weakened=true -> BLOCKED
namespace_violation_detected=true -> BLOCKED
```

### 0E.18 Dashboard implementation rule

Dashboard may display optimizer status only as analysis status.

Required display fields:

```text
optimizer_status
optimizer_stage
optimizer_maturity_level
convergence_status
top_candidate_count
blocked_candidate_count
primary_optimizer_blocker_code
primary_optimizer_blocker_message
last_optimizer_run_id
last_optimizer_evidence_id
live_order_allowed
```

Display wording:

```text
OPTIMIZER: RESEARCH ONLY
OPTIMIZER: COLLECTING
OPTIMIZER: RANKING CANDIDATES
OPTIMIZER: LOCAL IMPROVEMENT DETECTED - NOT LIVE READY
OPTIMIZER: ROBUST CANDIDATE DETECTED - LIVE ORDERS BLOCKED
OPTIMIZER: WRITER INPUT ELIGIBLE - SNAPSHOT NOT WRITTEN
```

Forbidden wording:

```text
optimizer profitable
profit guaranteed
automatic profit
profit converged without scope
self-optimizing live
```

### 0E.19 Patch result extension

Every optimizer-related patch result must include:

```text
optimizer_patch
optimizer_stage
optimizer_status_before
optimizer_status_after
optimizer_maturity_level_before
optimizer_maturity_level_after
optimizer_output_type
optimizer_run_id
optimizer_config_id
optimizer_objective_profile_id
optimizer_search_policy
optimizer_model_type
candidate_count_scored
candidate_count_ranked
candidate_count_pruned
candidate_count_blocked
top_candidate_ids
convergence_status_before
convergence_status_after
optimizer_validators_required
optimizer_validators_run
optimizer_guardrail_result
optimizer_live_mutation_detected
optimizer_live_order_allowed_after
```

Required values:

```text
optimizer_live_mutation_detected=false
optimizer_live_order_allowed_after=false unless independent LIVE_ENABLING evidence exists
optimizer_guardrail_result=PASS for any optimizer output claim
removed_requirements=[]
file_split=false
detail_reduction_allowed=false
```

### 0E.20 One-line optimizer implementation rule

```text
Implement the optimizer as a bounded, evidence-backed, cost-adjusted, risk-adjusted, overfit-penalized, execution-feedback-aware candidate improvement system. It may improve candidate selection and convergence probability, but it must never directly create live permission, never mutate live config, never write LIVE_READY snapshot directly, and never claim profitability without scoped evidence.
```

# PROFITABILITY_CONVERGENCE_OPTIMIZER_IMPLEMENTATION_OVERLAY_END


# LOSSLESS_VALIDATED_IMPLEMENTATION_OVERLAY_START

## 0D. Lossless validated implementation preservation overlay

document status: active additive implementation hardening supplement

This overlay applies the valid implementation recommendations to this single-file AGENTS guide without deleting, replacing, shrinking, summarizing, or moving any existing baseline content. The baseline AGENTS body is preserved verbatim below this overlay and remains available for implementation detail, traceability, coverage, and retained-archive lookup.

```yaml
overlay_schema_id: trader1.agents_lossless_validated_implementation_overlay.v1
patch_class: DOC_CONTRACT_PATCH
patch_date: "2026-04-28"
patch_method: additive_overlay_plus_verbatim_baseline_preservation
patch_input_agents_file: "AGENTS(127).md"
patch_input_agents_sha256: "37436a316c8c8b281f06388b722681f20a0bcf615b2f7d1a46510f1133fb3a28"
patch_input_trader1_file: "TRADER_1(120).md"
patch_input_trader1_sha256: "e24c697aba1553705818fe4c272b2208fd67c163e8a2816af77739821083b6d8"
delivered_paired_trader1_file: "TRADER_1_122_lossless_validated_improved.md"
delivered_paired_trader1_sha256: "ac00634ffedd90ef195692e21454d86958601a71bb91a190ab84deeacaa1ab9d"
merged_recommended_improvements_file: "TRADER_1_AGENTS_merged_recommended_improvements.md"
merged_recommended_improvements_sha256: "3418bbfd886eea07e7285671c32dcf4bfb2c0f179f450b7224eddf9f4207eaa6"
file_split: false
removed_requirements: []
detail_reduction_allowed: false
retained_archive_preserved: true
baseline_body_preserved_verbatim: true
existing_detail_preserved: true
live_order_ready_after_document_patch: false
live_order_allowed_after_document_patch: false
can_live_trade_after_document_patch: false
```

### 0D.1 Non-deletion and non-reduction invariant

```text
No existing AGENTS content is deleted.
No existing AGENTS content is summarized as a replacement.
No existing AGENTS table, list, implementation rule, validator instruction, patch class, retained archive text, or detail is removed.
No baseline section is split into another file.
All valid improvements are expressed as stricter additive implementation rules, validator requirements, generated artifact requirements, reporting requirements, coverage requirements, or interpretation rules.
If this overlay and later baseline wording appear to duplicate each other, the duplicate baseline wording is preserved and this overlay supplies the stricter active interpretation.
```

### 0D.2 Active implementation read priority

```text
1. TRADER_1.md active contract pack
2. TRADER_1.md execution contract body
3. TRADER_1.md active hardening supplements
4. AGENTS.md active implementation guide and this overlay
5. registry, schema, validator, generated contract, and manifest artifacts
6. preserved baseline and retained archive only for coverage, traceability, backlog, and omitted-detail lookup
```

AGENTS.md cannot weaken TRADER_1.md. Repository code cannot override TRADER_1.md. Runtime artifacts cannot override TRADER_1.md.

### 0D.3 Authority and manifest implementation requirements

```text
If the delivered paired TRADER_1 file hash does not match delivered_paired_trader1_sha256 above or the external authority manifest, block live-affecting patches, live readiness claims, and live_order_allowed=true.
The external authority manifest must be generated after final write and must include final TRADER_1 and AGENTS hashes.
A missing manifest blocks release identity PASS, source identity PASS, live readiness claims, and live_order_allowed=true.
Safe scaffold work remains allowed only for REPLAY, PAPER, SHADOW, and READ_ONLY when fail-closed behavior is preserved.
```

### 0D.4 Mandatory AI_IMPLEMENTATION_START_REPORT

Before coding or large repository changes, emit an AI_IMPLEMENTATION_START_REPORT with:

```text
active_authority_files
target_mvp_level
current_repo_state
root_launchers_found
unexpected_root_launchers_found
live_order_path_found
direct_strategy_to_exchange_call_found
paper_live_namespace_status
registry_status
schema_status
validator_status
test_status
highest_risk_gap
first_patch_class
first_patch_scope
remaining_initial_blockers
live_order_ready_before=false
live_order_allowed_before=false
```

```text
start report missing -> large patch BLOCKED
start report missing -> live-affecting patch BLOCKED
unknown repo state -> safe scaffold only
```

### 0D.5 PATCH_RESULT enforcement

Every patch result must use `trader1.patch_result.v1` or a stricter equivalent and include:

```text
schema_id
patch_id
created_at_utc
target_mvp_level
patch_class
input_authority_files
input_authority_hash_status
authority_hash_checked
affected_contract_ids
affected_exchange
affected_market_type
affected_mode
removed_requirements
merged_requirements
new_registry_items
new_or_changed_schema_ids
validators_required
validators_run
tests_run
retained_archive_preserved
normalization_metadata_updated
schema_enum_hardening_applied
coverage_unmapped_count
registry_yaml_parse_status
registry_placeholders_remaining
retained_archive_semantic_mapping_status
source_file_matches_current_input
output_file_matches_generated_output
detail_reduction_allowed
coverage_index_result
file_split
live_order_ready_before
live_order_ready_after
live_order_allowed_before
live_order_allowed_after
remaining_blockers
evidence_manifest_path
evidence_manifest_hash
validator_run_log_path
stage_gate_result_path
result_hash
```

Required values:

```text
removed_requirements=[]
file_split=false
detail_reduction_allowed=false
non-LIVE_ENABLING_PATCH -> live_order_allowed_after=false
DOCUMENT_NORMALIZATION_PATCH -> retained_archive_preserved=true
validators_run must list actual command and status
```

### 0D.6 Registry, schema, generated artifact, and CI sequence

Implementation must follow this sequence for MVP-0 or the first relevant contract patch:

```text
1. verify authority hash or mark authority_hash_checked=false
2. read the external authority manifest or generate it after final write
3. extract TRADER_1 registry seed from active contract areas only
4. replace authority_sha256 placeholder with final TRADER_1 hash in generated contracts/registry.yaml
5. remove registry_defined_required and all other placeholders from generated registry output
6. ensure parser-safe YAML
7. generate registry-backed common $defs
8. generate all schema files
9. generate TRADER_1 and AGENTS generated projections
10. run authority_integrity_validator, registry_validator, schema_validator, closed_enum_validator, common_defs_drift_validator, patch_result_schema_validator, coverage_index_validator, active_schema_extraction_validator, and generated_artifact_dirty_validator
11. emit live_order_ready=false, live_order_allowed=false, and can_live_trade=false unless a valid LIVE_ENABLING_PATCH with full evidence exists
```

### 0D.7 Required validators and fixture standards

High-priority MVP-0 validator scaffold:

```text
authority_integrity_validator
external_authority_manifest_validator
registry_validator
schema_validator
closed_enum_validator
common_defs_drift_validator
path_namespace_validator
config_schema_validator
readiness_surface_validator
live_ready_snapshot_validator
live_final_guard_validator
coverage_index_validator
patch_result_schema_validator
validator_fixture_catalog_validator
active_schema_extraction_validator
generated_artifact_dirty_validator
```

```text
validator missing -> UNTESTED
validator not run -> UNTESTED
UNTESTED -> not READY
TIMEOUT -> not PASS
STALE -> unusable for live readiness
missing artifact -> BLOCKED
live-blocking validator without PASS, FAIL, and BLOCKED fixtures -> cannot support live safety PASS
```

### 0D.8 Live-blocked negative test implementation

`tests/live_blocked` must verify `expected_order_adapter_called=false`, `live_order_allowed=false`, and closed primary blocker codes for:

```text
LIVE_READY missing
LIVE_READY invalid
official API verification missing
official API verification stale
operator approval missing
manual order test missing
reconciliation stale
symbol rule unknown
risk veto active
HIGH contract_gap open
CRITICAL contract_gap open
stale data
validator FAIL
source identity mismatch
emergency flatten unavailable
final guard disabled
local_state_only protection
artifact hygiene fail
config invalid
shadow or replay incomplete
edge model incomplete
sizing trace missing
regime confidence too low
strategy unit scope mismatch
ACTIVE snapshot invalid
strategy threshold not validated
entry maturity below Level 5
exit maturity below Level 5
```

### 0D.9 Retained archive and baseline-content handling

```text
ARCHIVE_ONLY
NON_AUTHORITY
TRACEABILITY_ONLY
DO_NOT_USE_FOR_EXECUTION_AUTHORITY
```

Retained archive and preserved baseline wording cannot weaken TRADER_1.md, cannot weaken this active implementation overlay, cannot create live permission, cannot create readiness, and cannot relax promotion thresholds. Unmapped live-affecting preserved requirements create or update contract_gap and keep live_order_ready=false and live_order_allowed=false.

### 0D.10 Runtime, strategy, dashboard, and emergency implementation rules

```text
summary.json and dashboard artifacts are display truth only.
If dashboard and engine disagree, engine truth wins and dashboard shows mismatch warning.
cancel_all_open_orders must not create entry risk.
manual_exit_all_positions cannot submit entry or add-position orders.
manual_reduce_position and emergency flatten must still use adapter, ledger, and reconciliation rules.
strategy signal cannot place orders directly.
strategy thresholds are not live evidence.
Stage A output cannot become LIVE_READY evidence.
Stage B PASS cannot become LIVE_READY snapshot.
LIVE_READY_CANDIDATE_WRITER_INPUT cannot become LIVE_READY without live_ready_snapshot_writer_validator PASS.
paper winner cannot mutate live config.
candidate snapshot cannot become ACTIVE snapshot directly.
expanded exploration bound cannot become live parameter bound.
```

### 0D.11 Semantic correction map for preserved baseline text

The preserved baseline content below is not edited or deleted. If a preserved section contains a machine-normalized token, generated artifacts and implementation agents must use the semantic English interpretation below unless a stricter TRADER_1 contract applies.

```text
guihoweverce -> guidance
howeverger -> danger
stlongly -> strongly
geurub -> group
pildeu -> field
junbi -> preparation or readiness
bidelete -> non-deletion
safetyseong -> safety
yaghwasikiji -> weaken
sujibman -> collection only
truthda -> truth
geo of ready -> state of readiness or readiness status, according to context
ama possible -> possibly available or potentially possible, according to context
```

The correction map does not delete the preserved wording. It prevents corrupted preserved wording from becoming an implementation contract, generated schema value, live permission, or weaker safety rule.

### 0D.12 Patch outcome invariant

```text
This lossless validated implementation overlay is not a LIVE_ENABLING_PATCH.
It cannot make live_order_ready=true.
It cannot make live_order_allowed=true.
It cannot make can_live_trade=true.
It preserves all baseline content and adds stricter authority identity, registry generation, schema closure, validator fixture, semantic interpretation, coverage handling, runtime safety, patch audit, and live-safety constraints.
```

# LOSSLESS_VALIDATED_IMPLEMENTATION_OVERLAY_END

# BASELINE_AGENTS_CONTENT_VERBATIM_START

# AGENTS.md

document status: active implementation guide

## 0C. Final integrated improvement application supplement

document status: active implementation hardening supplement

This supplement applies the consolidated TRADER_1 / AGENTS improvement list to this single-file implementation guide. It does not split the file, delete requirements, reduce detail, weaken TRADER_1.md, weaken safety, or create live permission.

```yaml
integration_schema_id: trader1.agents_integrated_improvement_application.v1
patch_class: DOC_CONTRACT_PATCH
source_file: AGENTS(112).md
source_sha256: "dec9b84c614e1a8c217f783dab74dfa75b48ffc73048d351c7d378fb8efb7dd5"
paired_design_authority_file: TRADER_1_106_integrated_improved.md
paired_design_authority_sha256: "e24c697aba1553705818fe4c272b2208fd67c163e8a2816af77739821083b6d8"
paired_design_authority_input_file: TRADER_1(105).md
paired_design_authority_input_sha256: "08429c55f822cac66368730ac8107d7441c62c2265b55c28ff0705ea0d995867"
consolidated_improvement_list_file: TRADER_1_AGENTS_integrated_improvement_list.md
consolidated_improvement_list_sha256: "b8580a5c3ba18d6e35e340ae2b28a134a59dacd87df4be9ae42d53b508dcc898"
file_split: false
removed_requirements: []
detail_reduction_allowed: false
retained_archive_preserved: true
live_order_ready_after_document_patch: false
live_order_allowed_after_document_patch: false
external_authority_manifest_required: true
```

### 0C.1 Implementation read-priority index

```text
1. TRADER_1.md active contract pack
2. TRADER_1.md execution contract body
3. TRADER_1.md active hardening supplements
4. AGENTS.md active implementation guide and this supplement
5. registry, schema, validator, generated contract, and manifest artifacts
6. retained archive only for coverage, traceability, backlog, and omitted-detail lookup
```

### 0C.2 Authority, manifest, and source identity rules

```text
If the delivered TRADER_1 file hash does not match the paired_design_authority_sha256 above or the external authority manifest, block live-affecting patches, live readiness claims, and live_order_allowed=true.
AGENTS.md cannot override TRADER_1.md.
repository code cannot override TRADER_1.md.
runtime artifacts cannot override TRADER_1.md.
Safe scaffold work remains allowed only for REPLAY, PAPER, SHADOW, and READ_ONLY when fail-closed behavior is preserved.
```

The generated external authority manifest must contain:

```text
manifest_schema_id
created_at_utc
trader1_md_path
trader1_md_sha256
agents_md_path
agents_md_sha256
registry_yaml_sha256_when_generated
schema_bundle_sha256_when_generated
source_tree_hash_when_generated
manifest_hash_policy
```

### 0C.3 Mandatory AI_IMPLEMENTATION_START_REPORT

Before coding, emit:

```text
active_authority_files
target_mvp_level
current_repo_state
root_launchers_found
live_order_path_found
registry_status
schema_status
validator_status
test_status
highest_risk_gap
first_patch_class
live_order_ready_before=false
live_order_allowed_before=false
```

### 0C.4 patch_result requirements

Every patch result must use `trader1.patch_result.v1` or a stricter equivalent and include:

```text
authority_hash_checked
registry_yaml_parse_status
registry_placeholders_remaining
retained_archive_semantic_mapping_status
source_file_matches_current_input
output_file_matches_generated_output
detail_reduction_allowed
schema_enum_hardening_applied
coverage_unmapped_count
file_split
```

Required values:

```text
removed_requirements=[]
file_split=false
detail_reduction_allowed=false
non-LIVE_ENABLING_PATCH -> live_order_allowed_after=false
DOCUMENT_NORMALIZATION_PATCH -> retained_archive_preserved=true
```

### 0C.5 Registry, schema, and validator generation sequence

```text
1. verify authority hash or mark authority_hash_checked=false
2. extract TRADER_1 registry seed
3. replace authority_sha256 placeholder with final TRADER_1 hash in generated contracts/registry.yaml
4. remove registry-defined-required and all other placeholders from generated registry output
5. ensure parser-safe YAML
6. generate registry-backed schema $defs
7. generate all schema files
8. run schema_validator, registry_validator, closed_enum_validator, patch_result_schema_validator, and coverage_index_validator
9. emit live_order_ready=false and live_order_allowed=false unless a valid LIVE_ENABLING_PATCH with full evidence exists
```

### 0C.6 Required closed schema behavior

```text
free-text-only blocker code is invalid
unknown no-trade reason is invalid
unknown live blocker code is invalid
unknown order_failure_type is invalid
unknown ledger_event.event_type is BLOCKED or RECONCILE_REQUIRED
summary.json cannot become execution truth
LIVE_READY_CANDIDATE_WRITER_INPUT cannot become LIVE_READY without live_ready_snapshot_writer_validator PASS
Stage B PASS cannot become LIVE_READY
paper winner cannot mutate live config
```

### 0C.7 Validator and fixture rules

```text
validator missing -> UNTESTED
validator not run -> UNTESTED
UNTESTED -> not READY
TIMEOUT -> not PASS
STALE -> unusable for live readiness
live-blocking validator without negative fixture -> cannot support live safety PASS
missing_fixture_count must be 0 for live readiness claims
```

High-priority MVP-0 validators:

```text
authority_integrity_validator
registry_validator
schema_validator
closed_enum_validator
path_namespace_validator
config_schema_validator
readiness_surface_validator
live_ready_snapshot_validator
live_final_guard_validator
coverage_index_validator
patch_result_schema_validator
```

### 0C.8 Live blocked negative tests

`tests/live_blocked` must verify `expected_order_adapter_called=false` for:

```text
LIVE_READY missing
official API verification stale
operator approval missing
manual order test missing
reconciliation stale
symbol rule unknown
risk veto active
HIGH contract_gap open
CRITICAL contract_gap open
stale data
validator FAIL
source identity mismatch
emergency flatten unavailable
final guard disabled
```

### 0C.9 Runtime and dashboard implementation constraints

```text
implement emergency protection paths before live permission claims
cancel_all_open_orders must not create entry risk
manual_exit_all_positions cannot submit entry or add-position orders
summary.json and dashboard artifacts are display truth only
if dashboard and engine disagree, engine truth wins and dashboard shows mismatch warning
standalone READY, LIVE READY, probably ready, and almost ready are forbidden
readiness text must include scope, evidence, blocker status, and live_order_allowed
```

### 0C.10 Document normalization and retained archive

```text
ARCHIVE_ONLY
NON_AUTHORITY
TRACEABILITY_ONLY
DO_NOT_USE_FOR_EXECUTION_AUTHORITY
```

Retained archive wording cannot weaken the active implementation guide or TRADER_1.md. Unmapped live-affecting retained requirements create contract_gap and keep live_order_ready=false and live_order_allowed=false. Semantic cleanup must not delete, summarize, soften, move, or split requirements.

### 0C.11 Patch outcome invariant

```text
This integrated implementation-guide patch is not a LIVE_ENABLING_PATCH.
It cannot make live_order_ready=true.
It cannot make live_order_allowed=true.
It cannot make can_live_trade=true.
It preserves all requirements and makes implementation order, authority identity, registry generation, schema closure, validator fixtures, coverage handling, and live safety stricter.
```


## 0B. Semantic English completion and preservation supplement

document status: active document-normalization hardening supplement

This supplement records the current semantic-English cleanup. It does not split the file, delete requirements, reduce detail, weaken safety, or create live permission.

```yaml
normalization_schema_id: trader1.semantic_english_completion.v1
source_file: AGENTS(112).md
output_file: AGENTS_113_integrated_improved.md
file_split: false
removed_requirements: []
detail_reduction_allowed: false
existing_detail_preserved: true
retained_archive_preserved: true
romanized_korean_residue_policy: translate_to_semantic_english_without_requirement_deletion
live_order_ready_after_document_patch: false
live_order_allowed_after_document_patch: false
```

Rules:

```text
Romanized retained-archive wording is not deleted; it is converted to semantic English.
If any retained archive requirement remains semantically unclear, it must be mapped through the active contract pack, coverage index, validator, or contract_gap.
No document-normalization patch may create live_order_ready=true or live_order_allowed=true.
Existing active contracts, detailed requirements, retained archive content, and hardening supplements remain preserved in this single file.
```

This document is the AI compiler guide that converts TRADER_1.md into repository work rules. This document is lower-authority than TRADER_1.md and must not weaken design authority.

## 0A. Active authority binding and hardening supplement

document status: active implementation hardening supplement

Authority document: TRADER_1.md
Authority SHA256 for delivered paired TRADER_1 file: e24c697aba1553705818fe4c272b2208fd67c163e8a2816af77739821083b6d8
Authority source input: TRADER_1(105).md
Authority source input SHA256: 08429c55f822cac66368730ac8107d7441c62c2265b55c28ff0705ea0d995867
Implementation guide source input: AGENTS(112).md
Implementation guide source input SHA256: dec9b84c614e1a8c217f783dab74dfa75b48ffc73048d351c7d378fb8efb7dd5

This supplement is lower-authority than TRADER_1.md. It exists to bind this AGENTS.md to the delivered TRADER_1 authority, fix current metadata drift, and prevent implementation agents from treating placeholders, retained archive text, or generated artifacts as live permission.

Required behavior:

```text
If the delivered TRADER_1 file hash does not match the Authority SHA256 above, block live-affecting patches, live readiness claims, and live_order_allowed=true.
If contracts/registry.yaml contains an authority hash placeholder, block authority_integrity_validator PASS.
If generated_marker.header contains an unquoted colon string, fix the registry seed before generating contracts/registry.yaml.
If registry-defined-required placeholders remain in generated registry output, block registry_validator PASS.
If retained archive wording is unclear or machine-normalized, map it through the active TRADER_1 contract pack and coverage index before implementation.
If any retained archive requirement affects live safety and is UNMAPPED, keep live_order_ready=false and live_order_allowed=false.
```

Patch result requirement extension:

```text
Every patch result must include authority_hash_checked, registry_yaml_parse_status, registry_placeholders_remaining, retained_archive_semantic_mapping_status, and live_order_allowed_after.
For this DOCUMENT_NORMALIZATION_PATCH, live_order_allowed_after must be false.
removed_requirements must remain [].
file_split must remain false.
```

# ACTIVE_IMPLEMENTATION_GUIDE_START

## 0. AI compiler start rules

```text
Read TRADER_1.md and AGENTS.md as the active authority set.
Apply the TRADER_1.md active contract pack as the highest authority.
Use AGENTS.md as implementation guidance, but do not weaken TRADER_1.md.
If repository code conflicts with the documents, modify, isolate, or block the code.
The implementation starting stage is MVP-0 Contract baseline.
The first task is to create contracts/registry.yaml and contracts/schema/*.schema.json.
Use live_order_ready=false and live_order_allowed=false as defaults.
```

The AI compiler has full implementation authority, but it does not have authority to permit live orders. `live_order_allowed=true` may be produced only when the active contract pack, validator PASS, evidence manifest, official API verification, manual order test, operator approval, reconciliation, and emergency protection are all satisfied.

## 1. authority order

When conflicts occur, follow this order.

```text
1. TRADER_1.md active contract pack
2. TRADER_1.md execution contract body
3. TRADER_1.md detailed scope
4. AGENTS.md active implementation guide
5. repository code
6. runtime artifacts
```

Rules:

```text
TRADER_1.md must never be weakened.
repository code never overrides design authority.
runtime artifacts never override design authority.
current official exchange information wins only for external API facts, fees, rate limits, symbol rules, order constraints, margin rules, and policy details.
official exchange information must not weaken fail closed behavior, namespace separation, logging, validation, live blocking, or UX behavior.
```

## 2. non-negotiable priorities

Apply this priority order whenever implementation choices conflict.

```text
safety
state consistency
data and namespace separation
exchange constraints
market type risk constraints
fail closed
user-simple UX
validation ability
maintainability
profitability improvement potential
extensibility
```

Mandatory behavior:

```text
unknown input -> fail closed
missing hard truth -> NO_TRADE or SAFE_MODE
state mismatch -> stop new orders and reconcile
ambiguous order result -> do not resend with a new identifier
validator failure -> block affected path
live uncertainty -> block live
dashboard uncertainty -> display blocked or checking, not normal
```

## 3. implementation autonomy

AI compiler may decide file names, function names, class names, module boundaries, and local implementation details when the design authority does not specify them.

Allowed autonomous choices:

```text
naming functions and classes
choosing simple module boundaries
adding schema fields required by design authority
adding validators and tests
adding safe defaults
blocking unverified live paths
adapting repository structure without weakening design authority
creating paper, shadow, read-only, or mock adapters before live adapters
recording contract_gap when ambiguity remains
```

Forbidden autonomous choices:

```text
opening live trading by inference
assuming strategy profitability
assuming official exchange API details are current
mixing paper, shadow, live, replay, exchange, or market type data
letting dashboard state become trading truth
letting strategy code call exchange APIs directly
silently swallowing failures
resubmitting ambiguous orders with new identifiers
weakening live blockers
weakening validator requirements
weakening schema conditions
```

When a conservative, safe, and verifiable choice is available, do not ask the user for clarification. Proceed and record the decision.

## 4. registry-first work rule

Contract values include:

```text
enum value
schema id
schema required field
hard truth field
soft truth fallback
no-trade reason
operator action
validator id
stage gate id
readiness vocabulary
path slug
risk profile id
strategy level
live readiness blocker
bundle rule
API verification TTL
```

When changing any contract value, use this sequence:

```text
registry_update
schema_update_if_needed
validator_update_if_needed
generated_section_update
manifest_hash_update
ci_validator_run
evidence_or_audit_record
```

Generated section marker:

```text
GENERATED_FROM: contracts/registry.yaml
DO_NOT_EDIT_MANUALLY
```

Rules:

```text
do not manually edit generated sections
do not duplicate registry lists in prose
if a prose section needs the list, reference the registry id
if registry and prose differ, registry wins when generated from active authority
unknown enum or unknown schema field in critical path -> BLOCKED or SAFE_MODE until mapped
```

## 5. MVP declaration

Before modifying code, declare target MVP level.

```text
MVP-0 Contract baseline
MVP-1 Safe boot skeleton
MVP-2 Upbit paper dry-run
MVP-3 Operational Upbit paper
MVP-4 Upbit live review
MVP-5 Upbit limited live
MVP-6 Multi-exchange paper
MVP-7 Binance limited live
```

Rules:

```text
when unsure, target the lower MVP level
MVP progress never implies live_order_ready without explicit evidence
do not implement MVP-5 live-enabling behavior before MVP-0 through MVP-4 evidence exists
do not treat Binance futures as part of Upbit MVP
do not mark automatic strategy generation as required for MVP-2 or MVP-3
```

## 6. patch classes

Every patch must be classified before implementation.

```text
DOC_CONTRACT_PATCH
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
RUNTIME_SAFETY_PATCH
PAPER_FUNCTIONAL_PATCH
LIVE_BLOCKING_PATCH
LIVE_ENABLING_PATCH
BUNDLE_HYGIENE_PATCH
DASHBOARD_UX_PATCH
DOCUMENT_NORMALIZATION_PATCH
```

The following patch classes cannot make `live_order_allowed=true`.

```text
DOC_CONTRACT_PATCH
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
BUNDLE_HYGIENE_PATCH
DASHBOARD_UX_PATCH
PAPER_FUNCTIONAL_PATCH
RUNTIME_SAFETY_PATCH
LIVE_BLOCKING_PATCH
DOCUMENT_NORMALIZATION_PATCH
```

Only `LIVE_ENABLING_PATCH` can make `live_order_allowed=true`, and only when all evidence exists.

Required evidence:

```text
valid LIVE_READY snapshot
official API verification PASS and fresh
manual order test PASS when required
operator approval valid when required
read-only burn-in PASS
emergency protection available
ledger reconciliation PASS
bundle hygiene PASS when release package is used
source identity PASS when release package is used
live blocked negative tests PASS
all blocking validators PASS
no HIGH or CRITICAL contract_gap open
```

If any item is missing, record `live_order_allowed_after=false`.

## 7. patch result format

Every patch result must state:

```text
target_mvp_level
patch_class
affected_contract_ids
affected_exchange
affected_market_type
affected_mode
removed_requirements
merged_requirements
new_registry_items
new_or_changed_schema_ids
validators_required
validators_run
live_order_allowed_before
live_order_allowed_after
remaining_blockers
coverage_index_result
patch_result_schema_id
input_authority_files
input_authority_hash_status
retained_archive_preserved
normalization_metadata_updated
schema_enum_hardening_applied
coverage_unmapped_count
file_split
```

Rules:

```text
removed_requirements must be []
validators_run must list actual commands and status
validator not run means UNTESTED
UNTESTED is not READY
TIMEOUT is not PASS
STALE is not usable for live readiness
```

Additional hardening fields required for this improved authority pair:

```text
authority_hash_checked
registry_yaml_parse_status
registry_placeholders_remaining
retained_archive_semantic_mapping_status
source_file_matches_current_input
output_file_matches_generated_output
detail_reduction_allowed
```

Rules:

```text
authority_hash_checked=false blocks live-affecting changes.
registry_yaml_parse_status other than PASS blocks registry generation.
registry_placeholders_remaining must be [] in generated contracts/registry.yaml.
retained_archive_semantic_mapping_status=UNMAPPED for any live-affecting requirement keeps live_order_allowed_after=false.
source_file_matches_current_input=false blocks document normalization PASS.
detail_reduction_allowed must be false.
```

## 8. MVP-0 contract baseline task

MVP-0 must create:

```text
contracts/registry.yaml
contracts/schema/readiness_surface.schema.json
contracts/schema/live_ready_snapshot.schema.json
contracts/schema/manual_order_test_evidence.schema.json
contracts/schema/final_decision.schema.json
contracts/schema/ledger_event.schema.json
contracts/schema/summary.schema.json
contracts/schema/evidence_manifest.schema.json
contracts/schema/official_api_verification_report.schema.json
contracts/schema/validator_result.schema.json
contracts/schema/operator_action_audit.schema.json
contracts/schema/release_source_identity.schema.json
contracts/schema/contract_gap.schema.json
contracts/schema/patch_result.schema.json
contracts/schema/strategy_candidate.schema.json
contracts/schema/candidate_generation_report.schema.json
contracts/schema/live_ready_candidate_writer_input.schema.json
contracts/schema/validator_fixture_catalog.schema.json
contracts/generated/TRADER_1.generated.md
contracts/generated/AGENTS.generated.md
```

Generation rules:

```text
copy actual JSON Schema blocks exactly from TRADER_1.md active contract pack when present
convert logical schema contracts into JSON Schema using TRADER_1.md field definitions when no full JSON Schema exists
set additionalProperties=false unless the active schema says otherwise
unknown enum is invalid
schema identity mismatch blocks affected live path
schema file generation must be followed by schema_validator
schema_validator failure blocks affected path
```

After schema generation, run:

```text
python -m trader1.validation.schema
python -m trader1.validation.registry
python -m trader1.validation.coverage_index
```

Failure means affected path is BLOCKED and `live_order_allowed=false`.

## 9. live gate hardening

`live_ready_snapshot` validation must enforce:

```text
live_order_allowed=true -> live_ready=true
live_order_allowed=true -> official_api_verification_id is non-null string
live_order_allowed=true and manual_order_test_required=true -> manual_order_test_id is non-null string
live_order_allowed=true and operator_approval_required=true -> operator_approval_id is non-null string
live_order_allowed=true -> read_only_burn_in_id is non-null string
live_order_allowed=true -> emergency_protection_evidence_id is non-null string
live_order_allowed=true -> validator_rollup_status=PASS
live_order_allowed=true -> invalidated_by empty
```

`readiness_surface` validation must enforce:

```text
live_order_allowed=true -> live_order_ready=true
live_order_allowed=true -> can_live_trade=true
live_order_allowed=true -> live_trading_status is SMALL_LIVE_BURN_IN or LIVE_ACTIVE
live_order_allowed=true -> no blocker with blocks_live_order=true
live_order_allowed=true -> primary_blocker_code=null
live_order_allowed=true -> primary_blocker_message=null
```

## 10. contract_gap handling

When ambiguity, omission, or contradiction remains, create `contract_gap` record.

Minimum fields:

```text
gap_id
created_at_utc
source_contract_id
missing_or_ambiguous_item
risk_level
affected_modules
affected_modes
affected_exchanges
decision
fallback_behavior
validator_required
evidence_required
live_blocks
status
```

Rules:

```text
HIGH contract_gap open -> live_order_ready=false
CRITICAL contract_gap open -> live_order_ready=false
CRITICAL contract_gap may block paper if it affects runtime safety
contract_gap must not be used to postpone live blocking
contract_gap must include validator_required when recurrence is possible
```

## 11. root launcher contract

Repository root must expose exactly four user launchers:

```text
UPBIT_PAPER
UPBIT_LIVE
BINANCE_PAPER
BINANCE_LIVE
```

Rules:

```text
no dashboard-only launcher at root
no debug launcher at root
no temporary launcher at root
no duplicate launcher at root
paper launcher cannot submit live order
live launcher cannot use paper broker as execution
BINANCE launchers must select SPOT or FUTURES_USDT_M explicitly
futures live cannot be implicit default
```

## 12. recommended repository structure

Prefer this structure when safe to adapt:

```text
src/trader1/
  adapters/
    upbit/
    binance_spot/
    binance_futures/
  core/
    decision/
    risk/
    sizing/
    strategy/
    portfolio/
    ledger/
    state/
    events/
    registry/
  runtime/
    boot/
    health/
    readiness/
    reconciliation/
    resource_guard/
  dashboard/
  validation/
  research/
  reports/
  config/
  security/
  utils/
contracts/
  registry.yaml
  schema/
  generated/
tests/
  unit/
  integration/
  contract/
  replay/
  adapter/
  live_blocked/
system/
  data/
  runtime/
  reports/
  validation/
  evidence/
  snapshots/
  configs/
```

Do not rewrite the whole repository solely for style. Refactor only when needed to satisfy design authority or remove actual risk.

## 13. namespace contract

Every runtime artifact must be keyed or physically separated by:

```text
exchange
market_type
mode
session_id
strategy_id if applicable
symbol if applicable
```

Recommended paths:

```text
system/data/<exchange>/<market_type>/<mode>/
system/logs/<exchange>/<market_type>/<mode>/
system/runtime/<exchange>/<market_type>/<mode>/
system/reports/<exchange>/<market_type>/<mode>/
system/validation/<exchange>/<market_type>/<mode>/
system/evidence/<exchange>/<market_type>/<mode>/<session_id>/
system/snapshots/<exchange>/<market_type>/LIVE_READY/
system/configs/<exchange>/<market_type>/
```

Forbidden:

```text
cross mode raw join
cross exchange raw join
cross market_type raw join
paper broker used as live broker
summary.json used as execution truth
dashboard direct ledger mutation
```

## 14. truth source discipline

Execution truth:

```text
ledger
intent WAL
order events
fill events
balance snapshots
position snapshots
exchange reconciliation snapshot
risk decisions
final decisions
```

Analysis truth:

```text
signal outcome reports
no-trade reviews
score calibration reports
shadow reports
walk-forward reports
replay reports
performance summaries
```

Dashboard serving truth:

```text
summary.json
heartbeat.json
startup_probe.json
action_queue.json
operator_status.json
readiness_surface.json
recent_no_trade_context.json
recent_entry_context.json
```

Rules:

```text
ledger and reconciliation truth drive trading decisions
summary and dashboard files display state but do not create trading truth
reports inform review and validation but do not override live execution state
validation support artifacts are evidence, not runtime truth
truth source conflict blocks new orders and requires reconciliation
```

## 15. decision and order path

Strategies propose. Risk and decision arbiter decide. Execution only executes FinalDecision.

Required decision path:

```text
hard truth check
resource health check
exchange health check
market data freshness check
exchange and symbol rule check
account reconciliation check
strategy signal normalization
market regime filter
risk veto
portfolio and exposure check
allocator arbitration
execution quality check
final decision
single execution path
ledger and evidence recording
```

Order path rules:

```text
use one writer or equivalent serialized transaction path
reserve budget before external order submission
no network I/O inside database transactions
commit local reservation before external submit
use client_order_id or intent_id for idempotency
ambiguous submit result -> do not send new order with new identifier
ambiguous submit result -> reconcile using same identifier first
exchange order exists but local commit failed -> stop or reconcile before new orders
fill events must be deduplicated
ledger mismatch blocks new orders
```

## 16. adapter implementation rules

Strategies must not call exchange APIs directly.

Every exchange adapter must provide or emulate:

```text
MarketDataAdapter
AccountAdapter
OrderAdapter
PositionAdapter
FeeAdapter
SlippageAdapter
SymbolRulesAdapter
RiskAdapter
WebSocketAdapter
RateLimitAdapter
ErrorNormalizer
HealthAdapter
ReconciliationAdapter
```

If official API information is not verified:

```text
adapter may be implemented as contract or mock
paper and shadow may run
read-only checks may run
live readiness remains BLOCKED
```

Never use outdated examples, old SDK behavior, or assumed exchange rules as live authority.

## 17. strategy implementation rules

A strategy unit is:

```text
strategy_id
strategy_build_id
parameter_set
parameter_hash
exchange
market_type
regime_scope
risk_profile
```

Rules:

```text
LIVE_READY applies to the full strategy unit, not to the strategy name alone
same strategy with different parameters, exchange, market type, regime, or risk profile is a separate candidate
strategies may propose signals but must not place orders directly
strategies must produce reason data for entry and no-entry decisions
strategy thresholds are not live evidence
seed strategies may be used for paper, replay, tests, and fixtures before profitability is proven
strategy changes require relevant revalidation before live expansion
```

Strategy candidate generation must remain bounded.

Allowed:

```text
parameter range adjustment
entry filter adjustment
exit filter adjustment
regime scope adjustment
liquidity tier adjustment
spread/depth policy adjustment
time stop adjustment
trailing behavior adjustment
risk profile downgrade or same-profile adjustment
symbol universe scoring adjustment
```

Forbidden:

```text
new live strategy without validation
risk veto bypass candidate
hard truth requirement relaxation
edge improvement claim without costs
unbounded complexity stacking
aggressive live hot swap
```

## 18. risk and sizing rules

Risk profile defaults come from TRADER_1.md active risk default table.

Rules:

```text
first live order starts small
account size does not imply full-size trading
good performance can expand size only step by step
expansion requires evidence and risk health
poor performance, drift, data issues, execution issues, or resource pressure reduce or stop trading
futures sizing must consider leverage, margin ratio, liquidation price, funding, and reduce-only paths
if sizing inputs conflict or are missing, reduce size or choose NO_TRADE
```

Risk units:

```text
pct_of_equity fields are percent_point
0.10 means 0.10 percent
basis point fields are basis_points
leverage fields are multiplier_or_policy
```

## 19. live final guard

Every live order submit must check:

```text
mode == LIVE
exchange verified
market_type verified
ACTIVE snapshot valid
FinalDecision exists
FinalDecision not stale
risk veto false
hard truth complete
data freshness pass
reconciliation fresh
protection ready
emergency flatten available
watchdog active
idempotency key exists
ledger writer available
live_order_ready true
live_order_allowed true
```

Failure means no order submit.

## 20. testing and validation

Run relevant tests after each change when possible.

```text
python -m pytest
```

If tests do not exist, add minimal tests for the changed contract rather than claiming untested success.

Required test lanes:

```text
compileall
unit
contract
config schema
integration
paper dry-run
replay
readiness
live blocked
emergency flatten dry-run
reconciliation
artifact hygiene
source identity
security scan
```

Critical failures block affected path:

```text
live launcher can place orders without paper validation
paper launcher can call live order API
exchange-specific data mix
paper and live data mix
paper, shadow, and live data mix
exchange or market type data mix
duplicate order possibility exists
duplicate order path exists
duplicate execution truth source exists
ledger mismatch does not block trading
API key secret exposed
withdrawal permission accepted
risk veto can be bypassed
kill switch does not block new order
adapter order constraints are not reflected
adapter symbol rules unverified but live allowed
futures liquidation risk missing
dashboard can mislead the operator about current state
unknown hard truth opens trading
summary.json is used as runtime truth
ambiguous order outcome creates a new order
unknown enum is accepted
schema identity mismatch allows live
live can start without LIVE_READY snapshot
```

## 21. live blocked negative tests

`tests/live_blocked` must verify no live order adapter call under these conditions:

```text
live_entry_enabled false
LIVE_READY missing or invalid
operator policy fail
local_state_only protection
stale data
risk blocked
reconciliation stale
artifact hygiene fail
shadow or replay incomplete
config invalid
emergency flatten unavailable
symbol rule unknown
final guard disabled
official API verification stale
source identity mismatch
manual order test missing
operator approval missing
entry maturity below Level 5
exit maturity below Level 5
edge model incomplete
sizing trace missing
regime confidence too low
strategy unit scope mismatch
ACTIVE snapshot invalid
strategy threshold not validated
HIGH contract_gap open
CRITICAL contract_gap open
```

No live safety claim is valid until these tests pass.

## 22. stage gate and evidence rules

A stage is not complete because code exists. A stage is complete only when evidence exists.

Minimum evidence pack:

```text
validator_run_log
stage_gate_rollup
manifest_hash
schema_id
test_result_summary
audit_findings
blocking_defect_count
unresolved_minor_defects
implemented_contracts
tests_executed
validator_results
known_blockers
runtime_artifacts_produced
risk_assessment
next_allowed_stage
```

Rules:

```text
stage skip is forbidden when it bypasses safety, namespace separation, ledger integrity, or live blocking
validator FAIL -> affected path BLOCKED
validator not run -> status UNTESTED, not READY
paper stage success does not imply live readiness
live readiness requires explicit LIVE_READY snapshot and preflight success
```

## 23. dashboard UX rules

Dashboard is an operating interface, not a research notebook and not a truth engine.

First view must show:

```text
mode
exchange
market_type
operator badge
engine state
LIVE TRADING status
primary blocker
next action
portfolio equity
cash or available balance
locked balance
today PnL
realized PnL
unrealized PnL
MDD
positions
open orders
pending confirms
watch universe
entry candidates
last no-trade reason
recent errors
resource health
exchange health
data freshness
applied snapshot id for live
protection status
reconciliation age
```

Rules:

```text
basic screen is simple
details are collapsible
no-trade reason must be visible
entry reason for held positions must be visible
dashboard must not reinterpret ledger or report truth into trading truth
dashboard failure must not stop trading engine unless resource or state safety is affected
if dashboard and engine disagree, engine truth wins and dashboard shows mismatch warning
```

## 24. bundle hygiene rules

Source bundle, release bundle, evidence bundle, and diagnostic bundle are separate.

Source bundle must not include:

```text
system/
export/
release/
.pytest_cache/
.mypy_cache/
.ruff_cache/
__pycache__/
*.pyc
*.pyo
*.sqlite
*.db
*.jsonl
*.log
*.tmp
*.bak
.env
.env.*
*secret*
*token*
*private*
```

Rules:

```text
credential scan and redaction must run before bundle creation
external share requires source archive forbidden_count=0
contains_secret=true blocks release and external share
source identity mismatch blocks live readiness
release package READY never implies live_order_ready
```

## 25. security rules

```text
API keys must not be committed
API keys must not appear in logs
signatures, account IDs, private payloads, and secrets must be masked
withdrawal permission must not be accepted as normal
live API key permission must be validated before live start
IP restriction and key rotation support should be documented when applicable
if secret handling is unclear, block live and use paper or read-only
```

## 26. operator control rules

Allowed operator controls:

```text
manual_stop
manual_resume_read_only
manual_ack_trade_disabled
manual_unlock_held_market_event
manual_retry_reconcile
manual_safe_mode
manual_disable_strategy
manual_reduce_position
manual_exit_all_positions
```

Rules:

```text
manual control must produce an audit record
manual control cannot convert BLOCKED live to LIVE_ACTIVE without preflight
manual override cannot force an unverified strategy into live
manual close or reduce may be allowed for risk reduction, but must still use adapter, ledger, and reconciliation rules
manual_exit_all_positions cannot submit entry or add-position order
```

## 27. repository audit before large changes

Before large changes, inspect:

```text
root launchers
live order path
config paths
data paths
log paths
runtime paths
state truth sources
strategy-to-exchange direct calls
dashboard source paths
tests and validators
secret leakage risk
bundle hygiene risk
```

Priority fixes:

```text
live safety
mode separation
single truth source
order idempotency
risk veto
kill switch
ledger integrity
secret leakage
no-trade reason visibility
dashboard truth discipline
registry drift
readiness vocabulary confusion
artifact hygiene
```

## 28. completion language

Do not claim these unless evidence exists:

```text
profitable
live ready
fully safe
production ready
API verified
READY without scope
validated without scope
complete without scope
```

Allowed claims when true:

```text
implemented scaffold
paper path ready for local test
validator added
live path blocked by design
adapter mock added
preflight blocks unverified live
source bundle hygiene PASS
Upbit paper dry-run READY
live review READY, live orders BLOCKED
release package BUNDLE_READY, live_order_ready=false
limited live order ready for exact snapshot scope
```

Every readiness claim must include:

```text
exchange
market_type
mode
scope
blocking status
live_order_allowed
evidence id if applicable
```

## 29. default behavior when unsure

```text
Do not open new live risk.
Preserve or reduce existing risk.
Reconcile state.
Use paper, shadow, read-only, or safe mode.
Show a one-line reason.
Record the decision.
Add a validator or test if the issue can recur.
```

## 30. one-line operating rule

```text
Implement autonomously, but when uncertain, choose no trade, safe mode, reconciliation, read-only, paper, shadow, or blocked status over risky progress.
```

# ACTIVE_IMPLEMENTATION_GUIDE_END

## 31. candidate parameter, promotion, parity, and execution-quality implementation supplement

This section is an implementation guide supplement. It does not weaken TRADER_1.md. If TRADER_1.md defines stricter values, the stricter values win.

AI compiler must treat the following as default implementation contracts when building candidate generation, LIVE_READY candidate writers, rolling performance, paper/live parity checks, and execution-quality measurement.

### 31.1 registry items to add in MVP-0 or the first relevant contract patch

Add or generate these registry groups before implementing the affected path:

```text
candidate_parameter_bounds
candidate_generation_limits
auto_adjustment_cooldowns
promotion_threshold_defaults
paper_live_parity_thresholds
rolling_performance_window_defaults
order_failure_type
realized_execution_measurement_fields
execution_quality_blockers
```

Patch classification:

```text
REGISTRY_PATCH when adding registry values
SCHEMA_PATCH when adding schema fields
VALIDATOR_PATCH when adding validators
RUNTIME_SAFETY_PATCH when using the values to block unsafe paths
LIVE_ENABLING_PATCH only if all live evidence already exists
```

Any non-LIVE_ENABLING_PATCH must keep:

```text
live_order_allowed_after=false
```

### 31.2 initial candidate parameter bounds

These are initial exploration bounds only. They are not live-optimal parameters and must not be used as evidence of profitability.

| strategy_family | parameter | initial_candidate_bound |
|---|---|---|
| open_reset_micro | reset_window_candles | 3 to 12 |
| open_reset_micro | momentum_window_candles | 3 to 20 |
| open_reset_micro | signal_ttl_candles | 1 to 5 |
| open_reset_micro | fomo_distance_atr | 0.5 to 1.5 |
| open_reset_micro | stop_distance_atr | 0.6 to 1.5 |
| open_reset_micro | take_profit_r | 1.0 to 2.5 |
| open_reset_micro | time_stop_candles | 3 to 12 |
| breakout_retest | breakout_window_candles | 20 to 80 |
| breakout_retest | retest_tolerance_atr | 0.2 to 0.8 |
| breakout_retest | false_breakout_confirmation_candles | 1 to 3 |
| breakout_retest | signal_ttl_candles | 2 to 8 |
| breakout_retest | stop_distance_atr | 0.5 to 1.8 or validated invalidation level |
| breakout_retest | take_profit_r | 1.5 to 3.0 |
| trend_pullback | fast_ema_period | 10 to 30 |
| trend_pullback | slow_ema_period | 40 to 100 |
| trend_pullback | pullback_depth_atr | 0.5 to 2.5 |
| trend_pullback | stop_distance_atr | 0.8 to 2.5 |
| trend_pullback | take_profit_r | 1.5 to 3.5 |
| trend_pullback | signal_ttl_candles | 3 to 12 |
| trend_pullback | higher_timeframe_ratio | 4 to 12 base timeframe units |
| range_reversion_vwap | vwap_deviation_std | 1.0 to 2.5 |
| range_reversion_vwap | range_window_candles | 30 to 120 |
| range_reversion_vwap | reversion_trigger_candles | 1 to 4 |
| range_reversion_vwap | stop_distance_atr | 0.8 to 2.0 |
| range_reversion_vwap | take_profit_r | 1.0 to 2.0 |
| range_reversion_vwap | time_stop_candles | 10 to 40 |

Implementation rules:

```text
max_candidates_per_strategy_build=200
max_candidates_per_generation_cycle=1000
max_entry_conditions_per_candidate=8
max_exit_conditions_per_candidate=8
out-of-bound candidate -> CANDIDATE only until registry patch, validator update, and evidence exist
parameter_complexity_exceeded -> BLOCKED or RETIRED candidate
```

### 31.3 automatic adjustment cooldowns

```text
candidate generation may run in REPLAY, PAPER, or SHADOW.
approved LIVE_READY snapshot rollover for same strategy unit -> minimum 24h cooldown unless risk-reducing rollback.
live ACTIVE snapshot replacement -> only at position-free boundary, new-entry boundary, or decision-cycle boundary.
risk_profile upgrade -> minimum 7d cooldown and explicit evidence pack.
parameter range expansion -> minimum 7d cooldown and explicit evidence pack.
strategy re-promotion after DEGRADED or BLOCKED -> minimum 24h cooldown plus cause-resolution evidence.
emergency downgrade, size reduction, safe mode, and stop trading actions -> no cooldown.
```

Forbidden:

```text
poor live performance -> immediate aggressive parameter change
loss streak -> widen stop without evidence
paper winner -> live config mutation without LIVE_READY snapshot
candidate snapshot -> ACTIVE snapshot directly
same position -> hot-swap that relaxes exit or risk
```

### 31.4 LIVE_READY candidate promotion defaults

Default minimum thresholds:

```text
replay closed trades >= 100 or explicit insufficient-sample blocker
replay coverage includes at least two market regimes when available
walk-forward or out-of-sample >= 30 percent of evaluated period or explicit reason
paper closed trades >= 30 for exact strategy unit
paper runtime >= 72h for liquid short-cycle strategies, longer by validator policy for low-frequency strategies
shadow signal opportunities >= 50
net_ev_after_cost positive and above profile minimum net edge buffer
profit_factor > 1.05 by default and not dominated by one outlier trade
max_drawdown within active risk profile threshold
fill_quality_score PASS
paper_live_gap within parity threshold when live comparison exists
zero HIGH or CRITICAL contract_gap
zero blocking validator FAIL
```

Promotion is blocked when:

```text
sample_count missing
cost components missing
fee/slippage/impact underestimated beyond threshold
strategy result dominated by one symbol without concentration approval
overfit_signal suspected
regime fit unknown
entry maturity below Level 5
exit maturity below Level 5 for live new entry
```

### 31.5 paper/live parity thresholds

Default parity thresholds:

```text
paper_live_gap_abs_net_ev_bps <= 15 bps
realized_vs_expected_slippage_mean_abs_bps <= active profile max_expected_slippage_bps
realized_vs_expected_slippage_p95_bps <= 2 times active profile max_expected_slippage_bps
realized_vs_expected_impact_mean_abs_bps <= active profile max_expected_impact_bps
fee_error_abs_bps <= 2 bps or <= 10 percent relative error, whichever is looser
fill_rate_gap <= 20 percent relative gap
partial_fill_model_error -> no HIGH severity mismatch
latency_p95 -> within signal TTL and live final guard TTL
```

Rules:

```text
cost underestimation blocks promotion more strongly than cost overestimation.
favorable slippage cannot offset missing hard truth or failed validator.
parity PASS is scoped by strategy_unit, exchange, market_type, risk_profile, and parameter_hash.
parity must not transfer across exchange or market_type.
```

### 31.6 rolling performance window defaults

```text
short_window = 20 closed trades or 24h, whichever is later
medium_window = 100 closed trades or 7d, whichever is later
long_window = 500 closed trades or 30d, whichever is later
regime_window = 30 closed trades per regime or explicit insufficient-sample blocker
symbol_window = 20 closed trades per symbol or explicit insufficient-sample blocker
adapter_window = 100 order events or 7d
live_burn_in_window = 20 live orders or 7d, whichever is later
```

Insufficient sample means:

```text
no promotion
no scale-up
no profitability claim
strategy may remain candidate, paper, or shadow
```

### 31.7 order failure taxonomy

Add a closed order_failure_type enum or equivalent.

```text
INSUFFICIENT_BALANCE
MIN_NOTIONAL_FAIL
PRICE_FILTER_FAIL
LOT_SIZE_FAIL
TICK_SIZE_FAIL
STEP_SIZE_FAIL
SYMBOL_RULE_MISMATCH
FEE_MODEL_MISMATCH
POST_ONLY_REJECT
IOC_PARTIAL
FOK_REJECT
MARKET_ORDER_REJECT
RATE_LIMIT_HIT
API_TIMEOUT
AUTH_FAILURE
PERMISSION_DENIED
WITHDRAWAL_PERMISSION_DETECTED
SIGNATURE_INVALID
TIMESTAMP_DRIFT
NETWORK_TIMEOUT
TRANSPORT_AMBIGUOUS
EXCHANGE_UNKNOWN_ORDER
DUPLICATE_CLIENT_ORDER_ID
ORDER_NOT_FOUND_DURING_RECONCILE
CANCEL_REJECTED_ALREADY_FILLED
PARTIAL_FILL_STALE
PRIVATE_WS_GAP
UNKNOWN_REJECT
```

Behavior mapping:

```text
symbol or rule failure -> block affected symbol or adapter path until verification and reconciliation
balance failure -> reconciliation required before new orders
rate limit hit -> throttle and block new orders when pressure persists
transport ambiguous -> same identifier reconciliation only
auth, permission, withdrawal permission, signature failure -> live BLOCKED and key review required
unknown reject -> block affected live path until normalized
```

### 31.8 realized slippage and impact measurement

Minimum fields to record for measurable order execution:

```text
decision_id
intent_id
client_order_id
symbol
side
quantity
order_type
decision_time_utc
submit_time_utc
exchange_ack_time when available
first_fill_time when available
last_fill_time when available
decision_mid_price
decision_best_bid
decision_best_ask
expected_fee_bps
expected_spread_cost_bps
expected_slippage_bps
expected_impact_bps
expected_latency_cost_bps
average_fill_price when available
realized_fee_bps when available
realized_spread_cost_bps when available
realized_slippage_bps when available
realized_impact_bps when available
slippage_error_bps
impact_error_bps
latency_ms
orderbook_snapshot_id
depth_snapshot_id
fee_snapshot_id
```

Formula baseline:

```text
BUY realized_slippage_bps = ((average_fill_price - decision_mid_price) / decision_mid_price) * 10000
SELL realized_slippage_bps = ((decision_mid_price - average_fill_price) / decision_mid_price) * 10000
slippage_error_bps = realized_slippage_bps - expected_slippage_bps
impact_error_bps = realized_impact_bps - expected_impact_bps
```

Partial fill rule:

```text
use filled quantity weighted average price
record unfilled residual separately
never infer unfilled quantity as filled
```

Execution quality blockers:

```text
realized_slippage_bps p95 > 2x expected threshold -> scale-up BLOCKED
realized_slippage_bps exceeds active profile max_expected_slippage_bps for 3 consecutive filled orders -> block new entries for affected strategy unit pending review
impact_error_bps exceeds threshold on thin market -> NO_TRADE for affected symbol until liquidity review
fee_error_abs_bps exceeds threshold -> FEE_MODEL_UNVERIFIED
measurement fields missing -> execution quality UNTESTED, not READY
```

### 31.9 supplemental validators

Add these validators or stricter equivalents before LIVE_READY candidate writer or live scale-up logic is considered complete:

```text
parameter_bound_validator
candidate_cooldown_validator
promotion_threshold_validator
paper_live_parity_validator
order_failure_taxonomy_validator
realized_slippage_validator
execution_quality_measurement_validator
rolling_window_default_validator
```

Rules:

```text
validator missing -> UNTESTED
UNTESTED -> not READY
validator FAIL -> affected promotion, scale-up, or live path BLOCKED
```


---

## 32. document cleanliness, consistency, and coverage hardening supplement

document status: active implementation guide hardening supplement

This chapter is an active supplement for cleaning up the AGENTS.md implementation guide and strengthening consistency with TRADER_1.md. This chapter does not weaken TRADER_1.md and does not delete existing requirements.

### 32.1 single-file preservation rule

```text
file_split=false
removed_requirements=[]
existing_detail_preserved=true
retained_archive_preserved=true
```

Rules:

```text
Document cleanup is not requirement deletion.
Duplicate body text is retained for preservation, traceability, coverage, and backlog candidacy, not as execution authority.
Do not split files.
Existing user requirements, detailed requirements, and hardening appendices remain preserved in the retained archive.
The top active implementation guide is the execution guidance, and repeated retained archive wording does not create looser exceptions.
```

### 32.2 authority and runtime artifact consistency

Interpret the AGENTS.md authority order together with the TRADER_1.md authority order.

```text
1. TRADER_1.md active contract pack
2. TRADER_1.md execution contract body
3. TRADER_1.md detailed scope
4. AGENTS.md active implementation guide
5. repository code
6. runtime artifacts
```

Rules:

```text
runtime artifacts never override design authority.
repository code never overrides design authority.
AGENTS.md can only operationalize TRADER_1.md and cannot relax TRADER_1.md.
retained archive cannot relax active implementation guide.
```

### 32.3 closed enum and schema generation hardening

When generating or updating schemas, the following fields must be registry-backed closed values, not arbitrary free text.

```text
final_decision.blocking_reason -> no_trade_reason or live_blocker code
summary.blocking_reason -> no_trade_reason or live_blocker code
readiness_surface.primary_blocker_code -> no_trade_reason or live_blocker code
readiness_surface.blockers[].code -> no_trade_reason or live_blocker code
manual_order_test_evidence.blockers[] -> no_trade_reason or live_blocker code
official_api_verification_report.blockers[].code -> no_trade_reason or live_blocker code
evidence_manifest.known_blockers[] -> no_trade_reason, live_blocker, validator_id, or contract_gap_id
order failure classification -> order_failure_type enum
```

Rules:

```text
If prose says string but registry defines a closed enum, generated schema must use the stricter registry-backed enum.
Free-text message is allowed only as message or detail, not as code.
UNKNOWN_BLOCKED is allowed only as a last-resort closed code and must include detail.
Unknown critical code -> BLOCKED or SAFE_MODE until mapped.
```

### 32.4 blocker object normalization

Any blocker shown to the operator, validator, evidence pack, or readiness surface should use this shape or a stricter equivalent.

```text
code
category
severity
message
detail when needed
evidence_id when available
blocks_start
blocks_live_order
source_contract_id when available
```

Rules:

```text
code is closed.
message is user-facing text.
detail is explanatory text.
severity does not replace code.
category does not replace code.
blocks_live_order=true always forces live_order_allowed=false.
```

### 32.5 coverage index and retained archive handling

Coverage status values:

```text
ACTIVE_MAPPED
RETAINED_MAPPED
BACKLOG_CANDIDATE
VALIDATOR_CANDIDATE
SUPERSEDED_BY_ACTIVE
BLOCKED_BY_SAFETY
UNMAPPED
```

Rules:

```text
UNMAPPED retained requirement is not deleted.
UNMAPPED live-affecting requirement creates or updates contract_gap.
Coverage index failure blocks live readiness claims.
Coverage index must not be used to weaken active authority.
```

### 32.6 patch result strengthening

Every patch result must additionally state:

```text
input_authority_files
input_authority_hash_status
retained_archive_preserved
normalization_metadata_updated
schema_enum_hardening_applied
coverage_unmapped_count
```

Rules:

```text
retained_archive_preserved must be true for document cleanup patches.
removed_requirements must remain [].
coverage_unmapped_count > 0 does not delete requirements; it creates follow-up mapping work.
Any live-affecting UNMAPPED item keeps live_order_allowed_after=false.
```


## 33. exploration, promotion, LIVE_READY writer, and patch-result implementation hardening supplement

document status: active implementation guide hardening supplement

This chapter integrates the uploaded final patch proposal improvement version into the AGENTS.md implementation guide. TRADER_1.md active design authority takes precedence, and this chapter converts that contract into repository work rules.

### 33.1 patch application invariant

```text
removed_requirements=[]
file_split=false
retained_archive_preserved=true
existing_detail_preserved=true
live_order_allowed_after=false for all non-LIVE_ENABLING_PATCH classes
```

Rules:

```text
Do not split TRADER_1.md or AGENTS.md.
Do not summarize retained archive content.
Do not delete duplicate lower-body requirements.
Do not use exploration success as live evidence.
Do not turn Stage B PASS into LIVE_READY snapshot.
Do not treat LIVE_READY_CANDIDATE_WRITER_INPUT as LIVE_READY snapshot.
```

### 33.2 patch class additions

`DOCUMENT_NORMALIZATION_PATCH` is a valid patch class. It cannot make live_order_allowed=true.

```text
DOCUMENT_NORMALIZATION_PATCH -> live_order_allowed_after=false
DOCUMENT_NORMALIZATION_PATCH -> file_split=false
DOCUMENT_NORMALIZATION_PATCH -> removed_requirements=[]
DOCUMENT_NORMALIZATION_PATCH -> retained_archive_preserved=true
```

### 33.3 required MVP-0 registry and schema additions

MVP-0 or the first relevant contract patch must add or generate these registry groups and schema IDs.

```text
exploration_stage
promotion_input_type
exploration_bound_type
entry_variation
exit_variation
execution_variation
regime_family
combination_dimensions
exploration_parameter_bounds
exploration_limits
patch_result
strategy_candidate
candidate_generation_report
live_ready_candidate_writer_input
validator_fixture_catalog
```

The following schema files are required when the affected path is implemented.

```text
contracts/schema/patch_result.schema.json
contracts/schema/strategy_candidate.schema.json
contracts/schema/candidate_generation_report.schema.json
contracts/schema/live_ready_candidate_writer_input.schema.json
contracts/schema/validator_fixture_catalog.schema.json
```

### 33.4 required validators

Add validator scaffold in MVP-0 when the path is not implemented yet. Missing implementation means UNTESTED, and UNTESTED is not READY.

```text
exploration_stage_validator
expanded_bound_validator
low_rr_ratio_validator
structural_variation_validator
execution_realism_validator
regime_scope_validator
combination_complexity_validator
candidate_budget_validator
duplicate_candidate_pruning_validator
timeframe_scope_validator
cost_after_edge_validator
fill_quality_validator
exploration_resource_validator
candidate_complexity_validator
promotion_input_type_validator
live_ready_snapshot_writer_validator
patch_result_schema_validator
validator_fixture_catalog_validator
```

DOCUMENT_NORMALIZATION_PATCH validators:

```text
document_no_korean_text_validator
requirement_preservation_validator
heading_coverage_validator
retained_archive_coverage_validator
contract_semantics_equivalence_validator
no_file_split_validator
```

Rules:

```text
document_no_korean_text_validator is required only for Full English Replacement patches or when full_english_replacement=true.
Other document normalization patches may keep Korean prose only when they are not Full English Replacement patches.
Full English Replacement must still keep removed_requirements=[], file_split=false, retained_archive_preserved=true, and contract_semantics_equivalence_validator PASS.
```

### 33.5 stage implementation rules

```text
STAGE_A_WIDE:
  implement only REPLAY/SHADOW by default
  emit EXPLORATION_CANDIDATE only
  direct live promotion forbidden
  live_ready_evidence forbidden

STAGE_B_REFINEMENT:
  implement REPLAY/PAPER/SHADOW evidence consolidation
  emit LIVE_READY_CANDIDATE_WRITER_INPUT only
  do not emit LIVE_READY snapshot
  do not emit ACTIVE snapshot

LIVE_READY snapshot writing:
  require live_ready_snapshot_writer_validator PASS
  require all promotion thresholds PASS
  require all blocking validators PASS
  require evidence manifest fresh
  require registry_hash, schema_bundle_hash, source_tree_hash, parameter_hash, risk_profile, exchange, market_type, and strategy scope match
```

### 33.6 patch result output requirements

Every patch result must use `trader1.patch_result.v1` or a stricter equivalent and include all prior fields plus these fields.

```text
schema_id
patch_id
created_at_utc
input_authority_files
input_authority_hash_status
retained_archive_preserved
normalization_metadata_updated
schema_enum_hardening_applied
coverage_unmapped_count
file_split
live_order_ready_before
live_order_ready_after
live_order_allowed_before
live_order_allowed_after
remaining_blockers
evidence_manifest_path
result_hash
```

Rules:

```text
removed_requirements must be []
file_split must be false
retained_archive_preserved must be true for document cleanup and normalization patches
validators_run must list actual commands and status
validator not run means UNTESTED
TIMEOUT is not PASS
STALE is not usable for live readiness
non-LIVE_ENABLING_PATCH -> live_order_allowed_after=false
```

### 33.7 uploaded patch source preserved for traceability

The following source patch is preserved verbatim for traceability. The operational rules above and TRADER_1.md active design authority control implementation.

~~~text
# Final patch proposal improvement version

## 0. Application principles

```text
No requirement removal
No requirement reduction
No detail loss
No file splitting
No semantic weakening
No live safety weakening
No promotion threshold weakening
No active contract weakening
```

English normalization is separated as a follow-up patch.

```text
Full English Replacement is separated as DOCUMENT_NORMALIZATION_PATCH, not as an immediate implementation patch.
Do not block MVP-0 through MVP-3 implementation.
Apply it after active contract, registry, schema, and validator semantics are frozen.
```

---

# 1. Priority 1: recommended for immediate application

## 1.1 Separate exploration stages

PATCH_CLASS:

```text
REGISTRY_PATCH
DOC_CONTRACT_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

Add:

```text
exploration_stage:
  STAGE_A_WIDE
  STAGE_B_REFINEMENT
```

Rules:

```text
STAGE_A_WIDE:
  allowed_modes = REPLAY, SHADOW
  expanded_bounds_allowed = true
  expanded_bounds_validator_required = true
  output = EXPLORATION_CANDIDATE only
  direct_live_promotion = forbidden
  live_ready_evidence = forbidden

STAGE_B_REFINEMENT:
  allowed_modes = REPLAY, PAPER, SHADOW
  expanded_bounds_allowed = true
  expanded_bounds_validator_required = true
  output = LIVE_READY_CANDIDATE_WRITER_INPUT only
  not LIVE_READY snapshot
  not ACTIVE snapshot
```

---

## 1.2 Strengthen separation between exploration and execution

PATCH_CLASS:

```text
DOC_CONTRACT_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

additional rule:

```text
exploration_candidate != ACTIVE_snapshot
paper_winner != live_config
candidate_snapshot != LIVE_READY_snapshot
expanded_exploration_bound != live_parameter_bound
LIVE_READY_CANDIDATE_WRITER_INPUT != LIVE_READY snapshot
Stage_A_output != LIVE_READY evidence
Stage_B_output != LIVE_READY snapshot
```

Enforce:

```text
candidate -> LIVE direct path forbidden
candidate_snapshot -> ACTIVE snapshot direct transition forbidden
LIVE_READY_CANDIDATE_WRITER_INPUT -> LIVE_READY direct interpretation forbidden
Stage_B PASS -> LIVE_READY direct interpretation forbidden
LIVE uses only a valid LIVE_READY snapshot
live_order_ready=true and live_order_allowed=true are both required
```

---

## 1.3 promotion input type closed enum

PATCH_CLASS:

```text
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

new enum:

```text
promotion_input_type:
  NOT_PROMOTION_INPUT
  EXPLORATION_CANDIDATE
  REFINEMENT_CANDIDATE
  LIVE_READY_CANDIDATE_WRITER_INPUT
```

Rules:

```text
NOT_PROMOTION_INPUT -> promotion forbidden
EXPLORATION_CANDIDATE -> promotion forbidden
REFINEMENT_CANDIDATE -> may become writer input only after Stage B validator PASS
LIVE_READY_CANDIDATE_WRITER_INPUT -> input to LIVE_READY snapshot generation only, not LIVE_READY itself
unknown promotion_input_type -> BLOCKED
```

---

## 1.4 LIVE_READY snapshot writer guard

PATCH_CLASS:

```text
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

Additional validators:

```text
live_ready_snapshot_writer_validator
```

Rules:

```text
LIVE_READY_CANDIDATE_WRITER_INPUT -> LIVE_READY snapshot generation requires separate live_ready_snapshot_writer_validator PASS
```

Required validation:

```text
promotion_input_type == LIVE_READY_CANDIDATE_WRITER_INPUT
all promotion thresholds PASS
all blocking validators PASS
zero HIGH contract_gap
zero CRITICAL contract_gap
registry_hash match
schema_bundle_hash match
source_tree_hash match
strategy_unit scope match
exchange scope match
market_type scope match
risk_profile scope match
parameter_hash match
paper/live parity PASS when applicable
execution quality PASS
cost_after_edge PASS
evidence_manifest present and fresh
validator results fresh
manual or operator requirements preserved
```

Forbidden:

```text
writer input treated as snapshot
Stage B PASS treated as LIVE_READY
snapshot generated with stale validator result
snapshot generated with UNTESTED validator result
snapshot generated with missing evidence manifest
snapshot generated with scope mismatch
```

---

## 1.5 Exploration-only parameter bounds

PATCH_CLASS:

```text
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

new registry group:

```yaml
exploration_parameter_bounds:
  initial_candidate_bound:
  expanded_exploration_bound:
  allowed_stage:
  allowed_mode:
  expanded_bounds_allowed:
  expanded_bounds_validator_required:
  validator_required:
  promotion_allowed:
```

Example:

```text
ATR:
  initial = 0.5 ~ 2.5
  expanded = 0.2 ~ 4.0

take_profit_r:
  initial = 1.0 ~ 3.5
  expanded = 0.5 ~ 5.0

EMA:
  initial = 10 ~ 100
  expanded = 5 ~ 200

signal_ttl_candles:
  initial = 1 ~ 12
  expanded = 1 ~ 30

time_stop_candles:
  initial = 3 ~ 40
  expanded = 1 ~ 100
```

Rules:

```text
expanded_exploration_bound is REPLAY/SHADOW only by default
PAPER use requires validator PASS
PAPER use requires explicit_experiment_scope
PAPER use requires candidate_risk_profile = CONSERVATIVE
PAPER use may use a registry-defined stricter-than-CONSERVATIVE profile if added later
LIVE_READY promotion requires Stage B validation
expanded bound itself is not profitability evidence
expanded bound itself is not live_parameter_bound
```

---

## 1.6 State that promotion criteria are invariant

PATCH_CLASS:

```text
DOC_CONTRACT_PATCH
VALIDATOR_PATCH
```

Additional wording:

```text
exploration expansion does not weaken promotion
expanded exploration bound does not lower LIVE_READY requirements
promotion threshold relaxation is forbidden
Stage A success is not LIVE_READY evidence by itself
Stage B PASS is required before LIVE_READY candidate generation
LIVE_READY_CANDIDATE_WRITER_INPUT is not LIVE_READY
LIVE_READY snapshot generation still requires all promotion thresholds and all blocking validators PASS
LIVE_READY_CANDIDATE_WRITER_INPUT -> LIVE_READY snapshot generation requires live_ready_snapshot_writer_validator PASS
```

Keep existing criteria:

```text
replay closed trades >= 100
paper closed trades >= 30
paper runtime >= 72h
shadow signal opportunities >= 50
walk-forward or out-of-sample >= 30%
net_ev_after_cost positive
profit_factor > 1.05
fill_quality_score PASS
paper_live_gap within threshold
zero HIGH or CRITICAL contract_gap
zero blocking validator FAIL
```

---

## 1.7 New reason and blocker codes

PATCH_CLASS:

```text
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
DASHBOARD_UX_PATCH
```

Additional closed codes:

```text
MEASUREMENT_MISSING
EXECUTION_QUALITY_UNTESTED
EXPANDED_BOUND_UNVERIFIED
PROMOTION_INPUT_TYPE_INVALID
EXPLORATION_STAGE_MISMATCH
VARIATION_UNREGISTERED
TIMEFRAME_SCOPE_MISMATCH
CANDIDATE_BUDGET_EXCEEDED
DUPLICATE_CANDIDATE
EXPLORATION_RESOURCE_LIMIT
LIVE_READY_SNAPSHOT_WRITER_UNTESTED
LIVE_READY_SNAPSHOT_WRITER_FAILED
```

Rules:

```text
All new codes must be registered as closed registry codes
Free-text-only reason is forbidden
Dashboard display text mapping is required
Validator result and readiness blocker must use the same code
```

---

# 2. Priority 2: strategy diversification and validation hardening

## 2.1 Conditional allowance for risky parameters

PATCH_CLASS:

```text
VALIDATOR_PATCH
SCHEMA_PATCH
```

Additional validators:

```text
low_rr_ratio_validator
cost_after_edge_validator
expanded_bound_validator
timeframe_scope_validator
```

Rules:

```text
take_profit_r < 1.0:
  high_winrate_hypothesis required
  cost_after_edge_validator PASS required
  sufficient_sample_required
  overfit_signal_check required
  LIVE_READY direct promotion forbidden
```

Additional conditions:

```text
TTL/time_stop expansion:
  base_timeframe required
  timeframe_scope required
  holding_time_estimate required
```

---

## 2.2 Register strategy-structure variations

PATCH_CLASS:

```text
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

new registry group:

```yaml
entry_variation:
exit_variation:
execution_variation:
```

Example:

```text
entry_variation:
  breakout
  retest
  momentum
  mean_reversion
  vwap_reversion
  pullback

exit_variation:
  fixed_tp
  trailing_tp
  partial_exit
  time_exit
  volatility_exit
  invalidation_exit
  hard_stop

execution_variation:
  market
  limit
  ioc
  maker
  split_order
  single_order
```

Rules:

```text
unregistered variation -> BLOCKED
variation combination must affect strategy_build_id and parameter_hash
variation change is a new candidate
execution variation cannot become LIVE_READY without exchange rule verification
```

---

## 2.3 Live restrictions on execution variations

PATCH_CLASS:

```text
VALIDATOR_PATCH
SCHEMA_PATCH
```

Additional validators:

```text
execution_realism_validator
execution_quality_measurement_validator
realized_slippage_validator
fill_quality_validator
```

Rules:

```text
slippage unknown -> promotion BLOCKED
impact unknown -> promotion BLOCKED
fill_quality missing -> promotion BLOCKED
measurement missing -> execution quality UNTESTED
fee model unknown -> FEE_MODEL_UNVERIFIED
execution variation cannot become LIVE_READY without exchange rule verification
```

---

## 2.4 Separate regime-based exploration

PATCH_CLASS:

```text
DOC_CONTRACT_PATCH
REGISTRY_PATCH
VALIDATOR_PATCH
```

Keep the existing enum:

```text
DOWNTREND
RANGE
UPTREND
BREAKDOWN
HIGH_VOLATILITY
LOW_LIQUIDITY
UNCERTAIN
```

Additional grouping:

```yaml
regime_family:
  TRENDING:
    - UPTREND
    - DOWNTREND
  RANGE:
    - RANGE
  RISK_OFF:
    - BREAKDOWN
    - HIGH_VOLATILITY
    - LOW_LIQUIDITY
    - UNCERTAIN
```

Rules:

```text
regime_family is a convenience grouping and does not replace canonical MarketRegime enum
DOWNTREND spot long -> restricted unless validated exception exists
regime_scope is part of strategy_unit
regime mismatch -> promotion BLOCKED
insufficient regime evidence -> LIVE_READY forbidden
regime evidence is separated by strategy_unit, exchange, market_type, and timeframe_scope
```

---

## 2.5 Add timeframe scope

PATCH_CLASS:

```text
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
```

Additional fields:

```text
timeframe_scope
base_timeframe
holding_time_estimate
```

Rules:

```text
timeframe_scope mismatch -> BLOCKED
TTL/time_stop expansion requires timeframe_scope
timeframe_scope must be included in candidate identity when it changes signal or holding behavior
```

---

# 3. Priority 3: combination exploration and resource control

## 3.1 combination dimensions

PATCH_CLASS:

```text
REGISTRY_PATCH
VALIDATOR_PATCH
SCHEMA_PATCH
```

new registry group:

```yaml
combination_dimensions:
  - entry
  - exit
  - regime
  - execution
  - timeframe
  - liquidity_tier
```

Rules:

```text
combination exploration prioritizes REPLAY/SHADOW
PAPER application is allowed only in Stage B
LIVE_READY candidate requires complexity validator PASS
combination_dimension change must affect parameter_hash or strategy_build_id
unregistered combination_dimension -> BLOCKED
```

---

## 3.2 Complexity limits

PATCH_CLASS:

```text
VALIDATOR_PATCH
```

Additional validators:

```text
combination_complexity_validator
structural_variation_validator
timeframe_scope_validator
candidate_complexity_validator
```

Conditions:

```text
max_entry_conditions_per_candidate exceeded -> BLOCKED
max_exit_conditions_per_candidate exceeded -> BLOCKED
timeframe_scope mismatch -> BLOCKED
unregistered variation -> BLOCKED
complexity score exceeded -> BLOCKED or RETIRED
```

---

## 3.3 Exploration resource limits

PATCH_CLASS:

```text
REGISTRY_PATCH
VALIDATOR_PATCH
```

new registry group:

```yaml
exploration_limits:
  max_parallel_shadow_builds
  max_generation_cycles_per_day
  max_replay_cpu_budget
  max_candidate_family_share
  max_storage_growth_per_day
  max_unreviewed_candidate_age
```

Additional validators:

```text
candidate_budget_validator
exploration_resource_validator
```

Rules:

```text
resource budget exceeded -> exploration throttled
resource critical -> exploration paused
exploration path cannot outrank live path
exploration cannot outrank ledger, reconciliation, live blocker, or dashboard health
exploration_resource_limit cannot weaken live safety blocker
```

---

## 3.4 Duplicate candidate pruning

PATCH_CLASS:

```text
VALIDATOR_PATCH
SCHEMA_PATCH
```

Additional validators:

```text
duplicate_candidate_pruning_validator
```

Duplicate criteria:

```text
same exchange
same market_type
same strategy_id
same strategy_build_id
same parameter_hash
same regime_scope
same timeframe_scope
```

Rules:

```text
exact duplicate -> prune
near duplicate -> merge or lower priority
duplicate candidate is excluded from promotion
pruned candidate keeps audit record
```

---

## 3.5 Prohibit unbounded candidate count expansion

PATCH_CLASS:

```text
DOC_CONTRACT_PATCH
VALIDATOR_PATCH
```

additional rule:

```text
Unbounded candidate expansion is forbidden
Increase exploration density through build iteration, shadow parallelism, and pruning
Keep max_candidates_per_strategy_build
Keep max_candidates_per_generation_cycle
Candidate growth is allowed only within resource budget
```

---

# 4. Priority 4: data quality and automatic-adjustment safety

## 4.1 Make data quality mandatory

PATCH_CLASS:

```text
VALIDATOR_PATCH
SCHEMA_PATCH
```

Enforce:

```text
fee missing -> FEE_MODEL_UNVERIFIED
slippage missing -> MEASUREMENT_MISSING
impact missing -> MEASUREMENT_MISSING
fill_quality missing -> EXECUTION_QUALITY_UNTESTED
cost components missing -> promotion BLOCKED
```

Mode-specific handling:

```text
REPLAY/SHADOW:
  candidate may remain
  promotion forbidden

PAPER:
  Stage B promotion BLOCKED

LIVE_READY:
  BLOCKED

LIVE:
  NO_TRADE
```

---

## 4.2 Harden automatic-adjustment safety

PATCH_CLASS:

```text
DOC_CONTRACT_PATCH
VALIDATOR_PATCH
```

Additional prohibitions:

```text
stop widening after loss is forbidden
paper winner immediate live application is forbidden
candidate snapshot -> ACTIVE snapshot direct transition is forbidden
same-position hot-swap without risk reduction is forbidden
aggressive parameter change after poor live performance is forbidden
live parameter change based on Stage A result is forbidden
```

Exceptions:

```text
risk-reducing rollback may bypass cooldown
emergency downgrade is immediate
safe mode is immediate
size reduction is immediate
```

---

# 5. New schema field candidates

PATCH_CLASS:

```text
SCHEMA_PATCH
```

candidate field:

```text
exploration_stage
exploration_bound_type
variation_signature
timeframe_scope
base_timeframe
holding_time_estimate
regime_family
combination_dimensions
experiment_scope
candidate_risk_profile
candidate_budget_id
duplicate_group_id
promotion_input_type
live_ready_snapshot_writer_status
live_ready_snapshot_writer_validator_id
```

Application targets:

```text
strategy_candidate
candidate_generation_report
evidence_manifest
live_ready_candidate_writer_input
validator_result
readiness_surface
live_ready_snapshot
```

---

# 6. Final list of new validators

```text
exploration_stage_validator
expanded_bound_validator
low_rr_ratio_validator
structural_variation_validator
execution_realism_validator
regime_scope_validator
combination_complexity_validator
candidate_budget_validator
duplicate_candidate_pruning_validator
timeframe_scope_validator
cost_after_edge_validator
fill_quality_validator
exploration_resource_validator
candidate_complexity_validator
promotion_input_type_validator
live_ready_snapshot_writer_validator
```

MVP application rules:

```text
MVP-0:
  registry entry + schema placeholder + validator scaffold allowed
  missing implementation -> UNTESTED
  UNTESTED -> not READY
  live_order_allowed=false

MVP-2~MVP-3:
  actual validator logic should be implemented for paper, replay, shadow candidate paths

MVP-4~MVP-5:
  all promotion and live writer validators must PASS before live readiness claim
```

---

# 7. Separate follow-up patch: Full English Replacement

PATCH_CLASS:

```text
DOCUMENT_NORMALIZATION_PATCH
DOC_CONTRACT_PATCH
```

apply condition:

```text
active contract pack, registry, schema, validator semantics are frozen
MVP-0 through MVP-3 implementation must not be blocked by English replacement
English normalization is optional unless Korean prose causes actual implementation ambiguity
```

Scope:

```text
TRADER_1.md
AGENTS.md
active contract sections
generated section descriptions
normalization layers
retained source archive content
tables
validator descriptions
schema comments or prose
dashboard display mapping prose
patch workflow prose
evidence and audit prose
```

Rules:

```text
Replace 100% of Korean prose with English
Do not summarize Korean sections
Do not delete Korean sections
Do not move details into separate files
Do not reduce retained archive content
Do not collapse detailed lists into shorter summaries
Do not convert exact contract terms into softer language
Do not change enum names unless they are explicitly Korean-only prose labels
Do not change schema IDs unless required by registry policy
Do not change project identity
Do not change file structure
```

Additional validators:

```text
document_no_korean_text_validator
requirement_preservation_validator
heading_coverage_validator
retained_archive_coverage_validator
contract_semantics_equivalence_validator
no_file_split_validator
```

Acceptance condition:

```text
removed_requirements = []
file_split = false
all prior headings preserved or English-equivalent heading preserved
all contract lists preserved
all tables preserved
all active and retained archive sections preserved
all Korean prose replaced with English
no live safety weakening
no promotion threshold weakening
```

---

# 8. Final structure

```text
Stage A:
wide exploration
REPLAY/SHADOW centered
extreme values allowed
generates EXPLORATION_CANDIDATE only
direct live promotion forbidden
cannot be LIVE_READY evidence by itself

Stage B:
refinement validation
REPLAY/PAPER/SHADOW evidence consolidation
cost, slippage, impact, fill quality validation
generates LIVE_READY_CANDIDATE_WRITER_INPUT
not LIVE_READY snapshot itself
snapshot generation requires live_ready_snapshot_writer_validator PASS

LIVE:
uses only valid LIVE_READY snapshot
snapshot scope match required
live_order_ready=true required
live_order_allowed=true required
live final guard PASS required
```

# 9. Core conclusion

```text
Exploration becomes more aggressive.
Validation becomes stricter.
Promotion is never weakened.
LIVE remains more conservative than before.
Exploration candidates are not live candidates.
Only a valid LIVE_READY snapshot can be an input to live execution.
Full English Replacement is useful, but should remain a separate normalization patch.
```

~~~

# document cleanliness, duplicate-risk, and machine-readability improvement layer

document status: normalized single-file authority view

Layered source requirements must not be deleted. Lower retained or duplicated body text must not be reinterpreted as execution authority. The AI compiler must read the active area first and use the retained archive only for preservation, traceability, coverage, and backlog mapping.

## normalization application rules

```yaml
normalization_schema_id: trader1.document_normalization.v4_current_source_hardened
generated_at_utc: 2026-04-27T00:00:00Z
source_file: AGENTS(112).md
output_file: AGENTS.md
document_kind: active implementation guide
file_split: false
removed_requirements: []
content_preservation_mode: additive_patch_with_no_requirement_removal
full_english_replacement: true
korean_codepoint_count_after_write: 0
semantic_reduction_allowed: false
detail_reduction_allowed: false
input_sha256: dec9b84c614e1a8c217f783dab74dfa75b48ffc73048d351c7d378fb8efb7dd5
input_line_count: 8293
output_file_sha256_policy: calculate_after_write_do_not_embed_self_hash
authority_sha256_recording_policy: record_final_TRADER_1_sha256_in_AGENTS_or_external_manifest
retained_archive_language_quality: machine_normalized_archive_requires_semantic_mapping
retained_archive_execution_authority: false
retained_archive_can_weaken_active_contract: false
canonical_read_order:
  - active contract or implementation section above
  - normalization and hardening supplement
  - retained archive for coverage and traceability only
live_effect:
  live_order_ready_after: false
  live_order_allowed_after: false
validator_expectations:
  - no_file_split_validator
  - requirement_preservation_validator
  - contract_semantics_equivalence_validator
  - document_no_korean_text_validator
  - coverage_index_validator
  - registry_validator
  - schema_validator
```

## machine reading priority

```text
1. apply the top active contract or active implementation guide in this file first.
2. if an active hardening supplement exists, apply it as part of the active region.
3. duplicated or older lower-body text is for requirement preservation and traceability.
4. lower retained source text does not weaken the active contract.
5. Additional functional requirements that exist only in the lower retained source text remain in final scope as long as they do not weaken safety, namespace separation, fail-closed behavior, validation, or user-simple UX.
6. no requirements were deleted during cleanup; they were preserved in the retained source archive instead.
```

## duplicate-risk handling rules

```text
when the same requirement appears in the active region and retained archive, use the active region as execution authority.
Repeated wording in the retained archive does not create new authority or looser exceptions.
additional retained archive details are used as backlog, coverage, or validator candidates.
retained archive and active area if conflict existing authority order and more conservative fail-closed rule follows.
```

## consistency hardening application result

```text
metadata_source_file_updated=true
metadata_hash_policy_updated=true
active_retained_boundary_strengthened=true
schema_enum_hardening_rule_added=true
blocker_object_normalization_rule_added=true
coverage_status_values_added=true
removed_requirements=[]
file_split=false
```

## schema enum hardening summary

```text
blocking_reason, primary_blocker_code, blockers[].code, known_blockers[], and order failure classification must be registry-backed closed values.
Free-text is allowed only in message or detail fields.
If an older schema block uses plain string for a closed-code field, generated schema must use the stricter registry-backed enum.
UNKNOWN_BLOCKED is a last-resort closed code, not a replacement for detailed mapping.
```

## coverage status policy

```text
ACTIVE_MAPPED: requirement is represented in active authority.
RETAINED_MAPPED: requirement is preserved in retained archive and compatible with active authority.
BACKLOG_CANDIDATE: requirement is preserved and should become implementation backlog.
VALIDATOR_CANDIDATE: requirement is preserved and should become validator coverage.
SUPERSEDED_BY_ACTIVE: retained wording is replaced by stricter active rule.
BLOCKED_BY_SAFETY: retained wording is preserved but cannot be implemented as written because it weakens safety.
UNMAPPED: mapping is unresolved; requirement is not deleted.
```

## RETAINED_ARCHIVE_START

# retained source archive

document status: ARCHIVE_ONLY NON_AUTHORITY TRACEABILITY_ONLY DO_NOT_USE_FOR_EXECUTION_AUTHORITY heading index

| coverage_id | archive_line | level | retained_heading |
|---|---:|---:|---|
| RET-0001 | 1 | 1 | detailed requirements body |
| RET-0002 | 3 | 2 | 1. implementation guide body |
| RET-0003 | 5 | 2 | 1. Role |
| RET-0004 | 15 | 2 | 2. Authority order |
| RET-0005 | 37 | 2 | 3. Top-level interpretation rules |
| RET-0006 | 59 | 2 | 4. Non-deletion and preservation rule |
| RET-0007 | 97 | 2 | 5. Authority integrity discipline |
| RET-0008 | 115 | 2 | 6. Registry-first editing discipline |
| RET-0009 | 161 | 2 | 7. Target MVP declaration |
| RET-0010 | 190 | 2 | 8. Patch workflow for existing repository |
| RET-0011 | 235 | 2 | 9. Non-negotiable priorities |
| RET-0012 | 269 | 2 | 10. AI autonomy rules |
| RET-0013 | 306 | 2 | 11. Root launcher contract |
| RET-0014 | 329 | 2 | 12. Recommended repository structure |
| RET-0015 | 386 | 2 | 13. Namespace contract |
| RET-0016 | 416 | 2 | 14. Runtime truth hierarchy |
| RET-0017 | 462 | 2 | 15. Hard truth and soft truth |
| RET-0018 | 481 | 2 | 16. Decision and conflict resolution |
| RET-0019 | 523 | 2 | 17. Single writer and idempotent order path |
| RET-0020 | 542 | 2 | 18. Adapter contract |
| RET-0021 | 568 | 2 | 19. Strategy implementation rules |
| RET-0022 | 598 | 2 | 20. Risk and sizing rules |
| RET-0023 | 618 | 2 | 21. Readiness and user flow |
| RET-0024 | 657 | 2 | 22. Implementation order |
| RET-0025 | 736 | 2 | 23. Testing and validation |
| RET-0026 | 796 | 2 | 24. Stage gate and evidence pack rules |
| RET-0027 | 838 | 2 | 25. External API handling |
| RET-0028 | 864 | 2 | 26. Bundle hygiene rules |
| RET-0029 | 899 | 2 | 27. Security rules |
| RET-0030 | 913 | 2 | 28. Operator control rules |
| RET-0031 | 943 | 2 | 29. Existing code handling |
| RET-0032 | 978 | 2 | 30. Scenario rulebook |
| RET-0033 | 1000 | 2 | 31. Completion language |
| RET-0034 | 1034 | 2 | 32. Default behavior when unsure |
| RET-0035 | 1048 | 2 | 33. One-line operating rule |
| RET-0036 | 1056 | 1 | detailed requirements body |
| RET-0037 | 1061 | 1 | AGENTS.md |
| RET-0038 | 1071 | 2 | 1. Role |
| RET-0039 | 1083 | 2 | 2. Authority order |
| RET-0040 | 1105 | 2 | 3. Non-removal rule |
| RET-0041 | 1135 | 2 | 4. Interpretation rules |
| RET-0042 | 1156 | 2 | 5. Registry-first discipline |
| RET-0043 | 1204 | 2 | 6. Non-negotiable priorities |
| RET-0044 | 1238 | 2 | 7. AI autonomy rules |
| RET-0045 | 1277 | 2 | 8. Root launcher contract |
| RET-0046 | 1298 | 2 | 9. Namespace contract |
| RET-0047 | 1328 | 2 | 10. Truth hierarchy |
| RET-0048 | 1381 | 2 | 11. Decision, risk, and order path |
| RET-0049 | 1418 | 2 | 12. Adapter contract |
| RET-0050 | 1444 | 2 | 13. Strategy and risk rules |
| RET-0051 | 1484 | 2 | 14. Readiness vocabulary |
| RET-0052 | 1508 | 2 | 15. Live readiness and user flow |
| RET-0053 | 1534 | 2 | 16. MVP implementation order |
| RET-0054 | 1553 | 2 | 17. Testing and validation |
| RET-0055 | 1589 | 2 | 18. External API handling |
| RET-0056 | 1606 | 2 | 19. Security rules |
| RET-0057 | 1620 | 2 | 20. Operator control rules |
| RET-0058 | 1648 | 2 | 21. Bundle rules |
| RET-0059 | 1688 | 2 | 22. Existing code handling |
| RET-0060 | 1726 | 2 | 23. Completion language |
| RET-0061 | 1753 | 2 | 24. Patch workflow |
| RET-0062 | 1774 | 2 | 25. Default behavior when unsure |
| RET-0063 | 1787 | 1 | detailed requirements body |
| RET-0064 | 1793 | 1 | AGENTS.md |
| RET-0065 | 1800 | 2 | 1. Role |
| RET-0066 | 1808 | 2 | 2. Authority order |
| RET-0067 | 1828 | 2 | 3. Top-level interpretation rules |
| RET-0068 | 1847 | 2 | 3A. Authority integrity discipline |
| RET-0069 | 1863 | 2 | 3B. Canonical registry and generated artifact discipline |
| RET-0070 | 1889 | 2 | 4. Non-negotiable priorities |
| RET-0071 | 1921 | 2 | 5. AI autonomy rules |
| RET-0072 | 1956 | 2 | 6. Root launcher contract |
| RET-0073 | 1977 | 2 | 7. Recommended repository structure |
| RET-0074 | 2027 | 2 | 8. Namespace contract |
| RET-0075 | 2083 | 2 | 9. Runtime truth hierarchy |
| RET-0076 | 2124 | 2 | 10. Hard truth and soft truth |
| RET-0077 | 2188 | 2 | 11. Closed enums |
| RET-0078 | 2339 | 2 | 12. No-trade reason enum |
| RET-0079 | 2396 | 2 | 13. Decision and conflict resolution |
| RET-0080 | 2452 | 2 | 14. Single writer and idempotent order path |
| RET-0081 | 2471 | 2 | 15. Adapter contract |
| RET-0082 | 2536 | 2 | 16. Strategy implementation rules |
| RET-0083 | 2564 | 2 | 16A. Market regime and universe rules |
| RET-0084 | 2596 | 2 | 17. Sizing and risk rules |
| RET-0085 | 2638 | 2 | 17A. Risk profile contract |
| RET-0086 | 2674 | 2 | 18. Dashboard contract |
| RET-0087 | 2734 | 2 | 19. Summary schema guidance |
| RET-0088 | 2775 | 2 | 19A. Minimum runtime schema contracts |
| RET-0089 | 2873 | 2 | 20. Live readiness and user flow |
| RET-0090 | 2906 | 2 | 21. Implementation order |
| RET-0091 | 2987 | 2 | 22. Testing and validation |
| RET-0092 | 3048 | 2 | 22A. Stage gate and evidence pack rules |
| RET-0093 | 3088 | 2 | 23. External API handling |
| RET-0094 | 3103 | 2 | 24. Security rules |
| RET-0095 | 3116 | 2 | 24A. Operator control rules |
| RET-0096 | 3143 | 2 | 25. Audit and implementation evidence |
| RET-0097 | 3171 | 2 | 26. User experience rules |
| RET-0098 | 3198 | 2 | 27. Existing code handling |
| RET-0099 | 3231 | 2 | 27A. Scenario rulebook |
| RET-0100 | 3250 | 2 | 28. Completion language |
| RET-0101 | 3291 | 2 | 29. Default behavior when unsure |
| RET-0102 | 3305 | 2 | 30. One-line operating rule |
| RET-0103 | 3311 | 2 | 31. final user flow implementation rule |
| RET-0104 | 3323 | 2 | 32. paper of implementation role |
| RET-0105 | 3336 | 2 | 33. LIVE execution internal parallel engine rule |
| RET-0106 | 3349 | 2 | 34. snapshot automatic improvement and rollover implementation rule |
| RET-0107 | 3367 | 2 | 35. immediate live entry implementation rule |
| RET-0108 | 3383 | 2 | 36. advancement per level implementation goal |
| RET-0109 | 3397 | 2 | 37. by strategy exit implementation rule |
| RET-0110 | 3427 | 2 | 38. live final guard implementation rule |
| RET-0111 | 3451 | 2 | 39. local_state_only protection rule |
| RET-0112 | 3476 | 2 | 40. readiness vocabulary implementation rule |
| RET-0113 | 3495 | 2 | 41. data freshness and blocker taxonomy implementation rule |
| RET-0114 | 3516 | 2 | 42. test and environment implementation rule |
| RET-0115 | 3555 | 2 | 43. source, release, and evidence bundle implementation rule |
| RET-0116 | 3561 | 2 | 44. code structure advancement implementation rule |
| RET-0117 | 3586 | 2 | 45. user screen implementation rule |
| RET-0118 | 3606 | 2 | 46. strategy execution advancement implementation rule |
| RET-0119 | 3631 | 2 | 47. by strategy entry and exit advancement level implementation rule |
| RET-0120 | 3657 | 2 | 48. regime, edge, and sizing implementation rule |
| RET-0121 | 3730 | 2 | 49. strategy family entry implementation rule |
| RET-0122 | 3800 | 2 | 50. strategy family exit implementation rule |
| RET-0123 | 3868 | 2 | 51. strategy execution validation implementation rule |
| RET-0124 | 3904 | 2 | 52. strategy operation quality implementation rule |
| RET-0125 | 3947 | 2 | 53. strategy candidate generation implementation rule |
| RET-0126 | 3980 | 2 | 54. rolling performance implementation rule |
| RET-0127 | 4014 | 2 | 55. strategy replacement during live implementation rule |
| RET-0128 | 4044 | 2 | 56. official API freshness implementation rule |
| RET-0129 | 4076 | 2 | 57. validator implementation rule |
| RET-0130 | 4140 | 2 | 58. contract reduction forbidden implementation rule |
| RET-0131 | 4174 | 2 | 59. read-only burn-in and protection implementation rule |
| RET-0132 | 4225 | 1 | hardening appendix A. AI compiler execution compression rule |
| RET-0133 | 4231 | 2 | A.1 default execution rule |
| RET-0134 | 4244 | 2 | A.2 work selection algorithm |
| RET-0135 | 4262 | 2 | A.3 pre-patch declaration rule |
| RET-0136 | 4279 | 2 | A.4 implementation result format |
| RET-0137 | 4318 | 1 | hardening appendix B. AI implementation checklist by MVP |
| RET-0138 | 4322 | 2 | B.1 MVP common rule |
| RET-0139 | 4332 | 2 | B.2 MVP-0 Contract baseline |
| RET-0140 | 4365 | 2 | B.3 MVP-1 Safe boot skeleton |
| RET-0141 | 4395 | 2 | B.4 MVP-2 Upbit paper dry-run |
| RET-0142 | 4420 | 2 | B.5 MVP-3 Operational Upbit paper |
| RET-0143 | 4451 | 2 | B.6 MVP-4 Upbit live review |
| RET-0144 | 4476 | 2 | B.7 MVP-5 Upbit limited live |
| RET-0145 | 4502 | 2 | B.8 MVP-6 Multi-exchange paper |
| RET-0146 | 4526 | 2 | B.9 MVP-7 Binance limited live |
| RET-0147 | 4546 | 1 | hardening appendix C. strategy implementation standard work rule |
| RET-0148 | 4550 | 2 | C.1 strategy is not an order executor |
| RET-0149 | 4560 | 2 | C.2 StrategyUnit implementation fields |
| RET-0150 | 4582 | 2 | C.3 common entry gate |
| RET-0151 | 4599 | 2 | C.4 common hard exit priority |
| RET-0152 | 4615 | 2 | C.5 default strategy family implementation |
| RET-0153 | 4641 | 2 | C.6 strategy live block condition |
| RET-0154 | 4664 | 1 | hardening appendix D. Coverage and non-deletion execution rule |
| RET-0155 | 4668 | 2 | D.1 non-deletion rule |
| RET-0156 | 4678 | 2 | D.2 coverage index status |
| RET-0157 | 4695 | 2 | D.3 coverage check mandatory item |
| RET-0158 | 4712 | 2 | D.4 UNMAPPED handling |
| RET-0159 | 4723 | 1 | hardening appendix E. direct execution instruction that can be given to the AI |
| RET-0160 | 4750 | 1 | hardening appendix F. AI implementation start observe form |
| RET-0161 | 4756 | 2 | F.1 writing time |
| RET-0162 | 4765 | 2 | F.2 AI_IMPLEMENTATION_START_REPORT |
| RET-0163 | 4793 | 2 | F.3 start observe rule |
| RET-0164 | 4804 | 1 | hardening appendix G. Patch Result JSON standard |
| RET-0165 | 4808 | 2 | G.1 PATCH_RESULT_TEMPLATE |
| RET-0166 | 4856 | 2 | G.2 mandatory rule |
| RET-0167 | 4868 | 1 | hardening appendix H. actual output file checklist by MVP |
| RET-0168 | 4874 | 2 | H.1 MVP-0 required files |
| RET-0169 | 4900 | 2 | H.2 MVP-1 required files |
| RET-0170 | 4921 | 2 | H.3 MVP-2 required files |
| RET-0171 | 4941 | 2 | H.4 MVP-3 required files |
| RET-0172 | 4961 | 2 | H.5 MVP-4 required files |
| RET-0173 | 4977 | 2 | H.6 MVP-5 required files |
| RET-0174 | 4995 | 2 | H.7 MVP-6 required files |
| RET-0175 | 5010 | 2 | H.8 MVP-7 required files |
| RET-0176 | 5025 | 2 | H.9 file checklist rule |
| RET-0177 | 5035 | 1 | hardening appendix I. Live blocked negative test matrix |
| RET-0178 | 5039 | 2 | I.1 Matrix schema |
| RET-0179 | 5056 | 2 | I.2 Required cases |
| RET-0180 | 5091 | 2 | I.3 Pass rule |
| RET-0181 | 5100 | 1 | hardening appendix J. user-facing text standard |
| RET-0182 | 5104 | 2 | J.1 display rule |
| RET-0183 | 5113 | 2 | J.2 Status text map |
| RET-0184 | 5145 | 2 | J.3 forbidden wording |
| RET-0185 | 5159 | 2 | J.4 source discipline |

---

# retained source archive

document status: lower-authority English-equivalent preservation archive

This area is for source preservation. It is not execution authority; it is for coverage, traceability, backlog review, and verification. Repeated headings, enums, schemas, or rules in this archive do not weaken the top active region or the existing authority order.

````````````````text
# Detailed requirements body

## 1. implementation guide body

## 1. Role

You are the AI compiler for TRADER_1.

Your job is to implement, audit, improve, refactor, and test the repository so that it follows the design authority.

You must prioritize the whole system over local feature completion. A local feature is invalid if it weakens safety, state consistency, data separation, fail-closed behavior, validation ability, or user simplicity.

---

## 2. Authority order

When instructions conflict, apply this order.

```text
1. Top-level interpretation contract in TRADER_1.md
2. AI Compiler autonomy contract in TRADER_1.md
3. Canonical Contract Body in TRADER_1.md
4. Canonical registry, schema, enum, state machine, validator, stage gate, and scenario rules
5. detailed requirements body in TRADER_1.md
6. This AGENTS.md
7. Existing repository code
```

This AGENTS.md must never weaken design authority.

Existing code never overrides the design authority. Code that conflicts with the design authority must be revised, isolated, blocked, or removed.

Current official exchange information wins only for external API facts, fees, rate limits, symbol rules, order constraints, margin rules, and policy details. Official exchange information must not weaken fail-closed behavior, namespace separation, logging, validation, or UX behavior.

---

## 3. Top-level interpretation rules

Apply these rules in every implementation decision.

```text
If the document has internal contradictions, use the newest upper-level contract.
If upper-level contracts conflict, choose safety, consistency, and fail closed.
If exchange API facts conflict with the document, use current official exchange information.
Do not assert profitability by reasoning.
Profitability is decided only by replay, walk-forward, out-of-sample, paper, shadow, and live burn-in evidence.
If the document is wrong or incomplete, continue with a safe default, record the correction, and keep implementation moving.
Never open live trading capability by assumption.
```

Core rule:

```text
Document wording is subordinate to system intent, safety, state consistency, exchange reality, and verifiability.
```

---

## 4. Non-deletion and preservation rule

Document cleanup is not a feature deletion mechanism.

The following scopes remain detail requirements unless the user explicitly removes them.

```text
UPBIT KRW spot
BINANCE spot
BINANCE USD-M futures
replay
paper
shadow
live
LIVE_READY snapshot
small live burn-in
automatic scale up
automatic scale down
automatic strategy promotion/degradation/retirement
dashboard UX
security, backup, accounting, tax, regulation, operations
full audit and validator blocking
```

MVP scope means staged implementation, not removal.

Rules:

```text
do not delete a user requirement during cleanup
move broad or future scope to a later MVP or detailed requirements body if needed
do not mark postponed scope as removed
do not simplify by weakening safety
if a feature conflicts with safety, block or defer it rather than deleting the requirement
```

---

## 5. Authority integrity discipline

Before implementation work begins, identify the active design authority and record its path and integrity hash when available.

Required behavior:

```text
active design authority -> TRADER_1.md unless explicitly superseded
manifest match available -> verify and record
manifest missing -> record AUTHORITY_HASH_UNVERIFIED but continue from the provided authority file
manifest mismatch -> block live-affecting changes until the active authority is resolved
multiple authority candidates found -> use the file explicitly selected by the user, otherwise block live-affecting changes until resolved
```

This rule should not stop safe paper-only scaffolding. It must stop live readiness claims and live-enabling changes when authority identity is ambiguous.

---

## 6. Registry-first editing discipline

When changing any contract value, update the canonical registry first.

Contract values include:

```text
enum value
schema id
schema required field
hard truth field
soft truth fallback
no-trade reason
operator action
validator id
stage gate id
readiness vocabulary
path slug
risk profile id
strategy level
live readiness blocker
```

Rules:

```text
do not manually edit generated sections
do not duplicate registry lists in prose
if a prose section needs the list, reference the registry id
if registry and prose differ, registry wins only when it is generated from the active authority
if registry is missing, create minimal registry before adding new contract values
unknown enum or unknown schema field in critical path -> BLOCKED or SAFE_MODE until mapped
```

Required output for contract edits:

```text
registry diff
generated section update
validator update or explanation
test update or explanation
evidence/audit record
```

---

## 7. Target MVP declaration

Before modifying code, declare the target MVP level.

Valid target levels:

```text
MVP-0 Contract baseline
MVP-1 Safe boot skeleton
MVP-2 Upbit paper dry-run
MVP-3 Operational Upbit paper
MVP-4 Upbit live review
MVP-5 Upbit limited live
MVP-6 Multi-exchange paper
MVP-7 Binance limited live
```

Rules:

```text
do not implement MVP-5 live-enabling behavior before MVP-0 through MVP-4 evidence exists
do not treat Binance futures as part of Upbit MVP
do not mark automatic strategy generation as required for MVP-2 or MVP-3
when unsure, target the lower MVP level
MVP progress never implies live_order_ready without explicit evidence
```

---

## 8. Patch workflow for existing repository

For every patch, classify it before implementation.

Patch classes:

```text
DOC_CONTRACT_PATCH
REGISTRY_PATCH
SCHEMA_PATCH
VALIDATOR_PATCH
RUNTIME_SAFETY_PATCH
PAPER_FUNCTIONAL_PATCH
LIVE_BLOCKING_PATCH
LIVE_ENABLING_PATCH
BUNDLE_HYGIENE_PATCH
DASHBOARD_UX_PATCH
```

Rules:

```text
LIVE_ENABLING_PATCH requires explicit evidence, validator pass, and operator approval contract.
LIVE_BLOCKING_PATCH may be applied before feature completeness.
BUNDLE_HYGIENE_PATCH is required before external sharing.
DOC_CONTRACT_PATCH must not weaken safety.
REGISTRY_PATCH must regenerate generated sections.
SCHEMA_PATCH must add validator coverage.
```

Every patch result must state:

```text
target_mvp_level
affected_exchange
affected_market_type
affected_mode
live_order_allowed_before
live_order_allowed_after
validators_run
remaining_blockers
```

---

## 9. Non-negotiable priorities

Apply this priority order whenever implementation choices conflict.

```text
safety
state consistency
data and namespace separation
exchange constraints
market type risk constraints
fail closed
user-simple UX
validation ability
maintainability
profitability improvement potential
extensibility
```

Profitability is considered only after safety, consistency, validation, and exchange realism are satisfied.

Mandatory behavior:

```text
unknown input -> fail closed
missing hard truth -> no trade
state mismatch -> stop new orders and reconcile
ambiguous order result -> do not resend with a new identifier
validator failure -> block affected path
live uncertainty -> block live
dashboard uncertainty -> display blocked or checking, not normal
```

---

## 10. AI autonomy rules

The agent may decide missing file names, function names, class names, module boundaries, and local implementation details when the document does not specify them.

The agent must choose the simplest implementation that satisfies the design authority contract.

The agent must not ask the user for clarification when a conservative, safe, and verifiable implementation choice is available.

The agent must record meaningful autonomous decisions when they affect runtime behavior, schema, live blocking, state transitions, or safety.

Allowed autonomous choices:

```text
naming functions and classes
choosing simple module boundaries
adding schema fields required by the design authority
adding validators and tests
adding safe defaults
blocking unverified live paths
adapting existing repo structure without weakening design authority
```

Forbidden autonomous choices:

```text
opening live trading by inference
assuming strategy profitability
assuming official exchange API details are current
mixing paper, shadow, live, replay, exchange, or market type data
letting dashboard state become trading truth
letting strategy code call exchange APIs directly
silently swallowing failures
resubmitting ambiguous orders with new identifiers
```

---

## 11. Root launcher contract

Repository root must expose only the user-facing launchers required by the design authority.

Allowed user launchers:

```text
UPBIT_PAPER
UPBIT_LIVE
BINANCE_PAPER
BINANCE_LIVE
```

The exact extension may follow the operating system or existing project convention.

Do not place dashboard-only, debug-only, test-only, temporary, duplicate, or experimental launchers at repository root.

Paper launchers must not be able to submit live orders.

Live launchers must not use a paper broker as live execution.

---

## 12. Recommended repository structure

If the existing repository already has a clean structure, adapt it incrementally. If a new structure is needed, prefer this shape.

```text
src/trader1/
  adapters/
    upbit/
    binance_spot/
    binance_futures/
  core/
    decision/
    risk/
    sizing/
    strategy/
    portfolio/
    ledger/
    state/
    events/
    registry/
  runtime/
    boot/
    health/
    readiness/
    reconciliation/
    resource_guard/
  dashboard/
  validation/
  research/
  reports/
  config/
  security/
  utils/
contracts/
  registry.yaml
  schema/
  generated/
tests/
  unit/
  integration/
  contract/
  replay/
  adapter/
system/
  data/
  runtime/
  reports/
  validation/
  evidence/
  snapshots/
  configs/
```

Do not rewrite the whole repository solely for style. Refactor only when needed to satisfy design authority or remove actual risk.

---

## 13. Namespace contract

Every runtime artifact must be keyed or physically separated by:

```text
exchange
market_type
mode
session_id
strategy_id if applicable
symbol if applicable
```

Recommended path format:

```text
system/data/<exchange>/<market_type>/<mode>/
system/logs/<exchange>/<market_type>/<mode>/
system/runtime/<exchange>/<market_type>/<mode>/
system/reports/<exchange>/<market_type>/<mode>/
system/validation/<exchange>/<market_type>/<mode>/
system/evidence/<exchange>/<market_type>/<mode>/<session_id>/
system/snapshots/<exchange>/<market_type>/LIVE_READY/
system/configs/<exchange>/<market_type>/
```

Never join raw paper, shadow, and live data directly. Cross-mode comparison must use an explicit comparison evidence pack or defined comparison report.

---

## 14. Runtime truth hierarchy

Execution truth:

```text
ledger
intent WAL
order events
fill events
exchange reconciliation snapshot
```

Analysis truth:

```text
signal outcome reports
no-trade reviews
score calibration reports
shadow reports
performance summaries
```

Dashboard serving truth:

```text
summary.json
heartbeat.json
startup_probe.json
action_queue.json
operator_status.json
recent_no_trade_context.json
recent_entry_context.json
```

Rules:

```text
ledger and reconciliation truth drive trading decisions
summary and dashboard files display state but do not create trading truth
reports inform review and validation but do not override live execution state
validation support artifacts are evidence, not runtime truth
truth source conflict blocks new orders and requires reconciliation
```

---

## 15. Hard truth and soft truth

Hard truth is required for trading decisions. If hard truth is missing, stale, contradictory, or unverified, new entry is forbidden.

Hard truth fields are defined by the registry and baseline TRADER_1.md.

Soft truth may use a declared neutral or conservative fallback.

Rules:

```text
unknown hard truth -> NO_TRADE or SAFE_MODE
soft truth fallback -> declared and conservative only
undefined fallback -> hard truth missing
missing data must never increase risk, size, leverage, confidence, or live readiness
```

---

## 16. Decision and conflict resolution

All strategy signals must pass through a central decision path before execution.

Global conflict priority:

```text
P0 manual emergency stop, kill switch, legal or exchange-enforced block
P1 hard truth availability, schema integrity, ledger durability
P2 exchange constraints, market type constraints, API policy, symbol rules
P3 account reconciliation, balance truth, position truth, open order truth
P4 portfolio risk, strategy risk, exposure, MDD, loss limit
P5 market regime, volatility, liquidity, data quality
P6 strategy lifecycle, strategy score, LIVE_READY scope
P7 execution quality, fee, slippage, market impact, latency
P8 user dashboard display and convenience
```

Required decision path:

```text
hard truth check
resource health check
exchange health check
market data freshness check
exchange and symbol rule check
account reconciliation check
strategy signal normalization
market regime filter
risk veto
portfolio and exposure check
allocator arbitration
execution quality check
final decision
single execution path
ledger and evidence recording
```

Strategies propose. Risk and decision arbiter decide. Execution only executes final decisions.

---

## 17. Single writer and idempotent order path

Rules:

```text
use one writer or equivalent serialized transaction path
reserve budget before external order submission
no network I/O inside database transactions
commit local reservation before external submit
use client_order_id or intent_id for idempotency
ambiguous submit result -> do not send new order with new identifier
ambiguous submit result -> reconcile using same identifier first
exchange order exists but local commit failed -> stop or reconcile before new orders
fill events must be deduplicated
ledger mismatch blocks new orders
```

---

## 18. Adapter contract

Strategies must not call exchange APIs directly.

Every exchange adapter must provide or emulate these responsibilities:

```text
MarketDataAdapter
AccountAdapter
OrderAdapter
PositionAdapter
FeeAdapter
SlippageAdapter
SymbolRulesAdapter
RiskAdapter
WebSocketAdapter
RateLimitAdapter
ErrorNormalizer
HealthAdapter
ReconciliationAdapter
```

If official API information is not verified, adapter state is not live-ready.

---

## 19. Strategy implementation rules

Strategies must be treated as candidates until evidence exists.

Strategy unit:

```text
strategy_id
strategy_build_id
parameter_set
exchange
market_type
regime_scope
risk_profile
```

Rules:

```text
LIVE_READY applies to the full strategy unit, not to the name alone
same strategy with different parameters, exchange, market type, regime, or risk profile is a separate candidate
strategies may propose signals but must not place orders directly
strategies must produce reason data for entry and no-entry decisions
strategy thresholds are not live evidence
seed strategies may be used for paper, replay, tests, and fixtures before profitability is proven
strategy changes require relevant revalidation before live expansion
```

---

## 20. Risk and sizing rules

Sizing must prioritize survival and cost control over aggression.

Rules:

```text
first live order starts small
account size does not imply full-size trading
good performance can expand size only step by step
expansion requires evidence and risk health
poor performance, drift, data issues, execution issues, or resource pressure reduce or stop trading
futures sizing must consider leverage, margin ratio, liquidation price, funding, and reduce-only paths
if sizing inputs conflict or are missing, reduce size or choose NO_TRADE
```

Risk profile defaults are defined in TRADER_1.md. Missing risk profile means CONSERVATIVE or NO_TRADE depending on live context.

---

## 21. Readiness and user flow

User flow:

```text
run UPBIT_PAPER or BINANCE_PAPER
watch dashboard
confirm scoped LIVE_READY status
stop or keep paper
run UPBIT_LIVE or BINANCE_LIVE
watch live dashboard
stop if needed
```

Readiness claims must never use unscoped READY.

Allowed scoped forms:

```text
Upbit paper dry-run READY
live review READY, live orders BLOCKED
release package BUNDLE_READY, live_order_ready=false
limited live order ready for exact snapshot scope
```

Every readiness claim must include:

```text
exchange
market_type
mode
scope
blocking status
live_order_allowed
evidence id if applicable
```

---

## 22. Implementation order

Stage P0. Safety and state foundation:

```text
mode and namespace separation
root launcher separation
config validation
ledger or equivalent execution truth
intent WAL or equivalent journal
single writer order state path
startup probe
safe mode
kill switch
basic resource guard
```

Stage P1. Paper and dashboard foundation:

```text
paper execution model
shadow separation
runtime summary
heartbeat
dashboard first view
no-trade reason enum
entry reason logging
basic strategy fixtures
basic risk and sizing
```

Stage P2. Validation foundation:

```text
schema validators
strategy decision validator
risk sizing validator
adapter contract validator
numeric determinism validator
replay consistency test
paper and shadow separation test
ledger reconciliation test
```

Stage P3. Upbit readiness:

```text
upbit adapter official rule verification
upbit paper realism
upbit private stream or reconciliation path
upbit live preflight
upbit live blocked until evidence
```

Stage P4. Binance readiness:

```text
binance spot adapter
binance futures adapter
futures risk model
funding, liquidation, margin, reduce-only handling
binance live blocked until evidence
```

Stage P5. Automatic improvement:

```text
strategy scoring
candidate pool
promotion and degradation
parameter candidate generation
walk-forward and out-of-sample checks
LIVE_READY snapshot creation
```

Do not implement advanced profitability optimization before P0 through P2 safety and validation paths are stable.

---

## 23. Testing and validation

Run relevant tests after each change when possible.

If the repo has pytest:

```text
python -m pytest
```

If the repo has no tests, add minimal tests for the changed contract rather than claiming untested success.

Required test lanes:

```text
compileall
unit
contract
config schema
integration
paper dry-run
replay
readiness
live blocked
emergency flatten dry-run
reconciliation
artifact hygiene
```

Critical failures block affected path:

```text
live launcher can place orders without paper validation
paper launcher can call live order API
exchange-specific data mix
paper and live data mix
paper, shadow, and live data mix
exchange or market type data mix
duplicate order possibility exists
duplicate order path exists
duplicate execution truth source exists
ledger mismatch does not block trading
API key secret exposed
withdrawal permission accepted
risk veto can be bypassed
kill switch does not block new order
adapter order constraints are not reflected
adapter symbol rules unverified but live allowed
futures liquidation risk missing
dashboard can mislead the operator about current state
unknown hard truth opens trading
summary.json is used as runtime truth
ambiguous order outcome creates a new order
unknown enum is accepted
schema identity mismatch allows live
live can start without LIVE_READY snapshot
```

---

## 24. Stage gate and evidence pack rules

A stage is not complete because code exists. A stage is complete only when required evidence exists.

Minimum evidence pack contents:

```text
validator_run_log
stage_gate_rollup
manifest_hash
schema_id
test_result_summary
audit_findings
blocking_defect_count
unresolved_minor_defects
paper_live_parity_report if applicable
reconciliation_report if applicable
stage_id
timestamp_utc
affected_exchange
affected_market_type
implemented_contracts
tests_executed
validator_results
known_blockers
runtime_artifacts_produced
risk_assessment
next_allowed_stage
```

Rules:

```text
stage skip is forbidden when it would bypass safety, namespace separation, ledger integrity, or live blocking
validator FAIL -> affected path BLOCKED
validator not run -> status UNTESTED, not READY
paper stage success does not imply live readiness
live readiness requires explicit LIVE_READY snapshot and preflight success
```

---

## 25. External API handling

Before marking any live adapter ready, verify current official exchange information.

If verification is not available:

```text
adapter may be implemented as contract or mock
paper and shadow may run
read-only checks may run
live readiness remains BLOCKED
```

Create an official API verification report with:

```text
result=UNVERIFIED
live_order_ready=false
primary_blocker=API_UNVERIFIED
expires_at_utc=null
```

Never use outdated examples, old SDK behavior, or assumed exchange rules as live authority.

---

## 26. Bundle hygiene rules

Source bundle, release bundle, evidence bundle, diagnostic bundle are separate.

Source bundle must not include:

```text
system/
export/
release/
.pytest_cache/
.mypy_cache/
.ruff_cache/
__pycache__/
*.pyc
*.pyo
*.sqlite
*.db
*.jsonl
*.log
*.tmp
*.bak
.env
.env.*
*secret*
*token*
*private*
```

Credential scan and redaction must run before bundle creation.

External share requires source archive forbidden_count=0.

---

## 27. Security rules

```text
API keys must not be committed
API keys must not appear in logs
signatures, account IDs, private payloads, and secrets must be masked
withdrawal permission must not be accepted as normal
live API key permission must be validated before live start
IP restriction and key rotation support should be documented when applicable
if secret handling is unclear, block live and use paper or read-only
```

---

## 28. Operator control rules

Operator control must be limited, explicit, and auditable. User actions must not bypass risk veto, state reconciliation, or live readiness.

Allowed operator controls where implemented:

```text
manual_stop
manual_resume_read_only
manual_ack_trade_disabled
manual_unlock_held_market_event
manual_retry_reconcile
manual_safe_mode
manual_disable_strategy
manual_reduce_position
manual_exit_all_positions
```

Rules:

```text
manual control must produce an audit record
manual control cannot convert BLOCKED live to LIVE_ACTIVE without preflight
manual override cannot force an unverified strategy into live
manual close or reduce may be allowed for risk reduction, but must still use adapter, ledger, and reconciliation rules
manual_exit_all_positions cannot submit entry or add-position order
```

---

## 29. Existing code handling

When applying this guide to an existing repository:

```text
inspect the full repository before large changes
identify actual root launchers
identify any live order path
identify data, log, config, and runtime paths
identify state truth sources
identify strategy-to-exchange direct calls
identify dashboard source paths
identify tests and validators
fix highest-risk violations first
avoid broad rewrites unless necessary to remove safety risk
```

Priority fixes:

```text
live safety
mode separation
single truth source
order idempotency
risk veto
kill switch
ledger integrity
secret leakage
no-trade reason visibility
dashboard truth discipline
bundle hygiene
```

---

## 30. Scenario rulebook

Use these defaults when implementation details are missing.

```text
hard truth missing -> NO_TRADE or SAFE_MODE
strategy conflict -> central arbiter creates one FinalDecision
risk conflict -> risk veto wins
market regime mismatch -> no aggressive entry, show regime mismatch reason
exchange state mismatch -> stop new orders and reconcile
ambiguous order result -> same identifier reconciliation only
dashboard and ledger conflict -> ledger wins, dashboard shows mismatch
disk full or ledger write failure -> block live new orders
private websocket unhealthy -> block live if private stream is required; otherwise use defined reconciliation fallback
futures liquidation risk high -> reduce, close, or block expansion
unknown API rule -> paper/read-only only, live blocked
unknown strategy profitability -> candidate/paper/shadow only
unknown readiness scope -> live_order_ready=false
```

---

## 31. Completion language

Do not claim these unless evidence exists:

```text
profitable
live ready
fully safe
production ready
API verified
READY without scope
validated without scope
complete without scope
```

Allowed claims when true:

```text
implemented scaffold
paper path ready for local test
validator added
live path blocked by design
adapter mock added
preflight blocks unverified live
source bundle hygiene PASS
Upbit paper dry-run READY
live review READY, live orders BLOCKED
release package BUNDLE_READY, live_order_ready=false
```

Avoid vague status words such as probably, almost, likely ready, or seems fine for live.

---

## 32. Default behavior when unsure

```text
Do not open new live risk.
Preserve or reduce existing risk.
Reconcile state.
Use paper, shadow, read-only, or safe mode.
Show a one-line reason.
Record the decision.
Add a validator or test if the issue can recur.
```

---

## 33. One-line operating rule

```text
Implement autonomously, but when uncertain, choose no trade, safe mode, reconciliation, or blocked status over risky progress.
```

---

# Detailed requirements body


---

# AGENTS.md

TRADER_1 AI compiler implementation guide

document status: active implementation guide

This file guides AI coding agents working on TRADER_1. It does not replace TRADER_1.md. It converts the design authority into operational implementation rules.

---

## 1. Role

You are the AI compiler for TRADER_1.

Your job is to implement, audit, improve, refactor, and test the repository so that it follows the active design authority.

You must prioritize the whole system over local feature completion. A local feature is invalid if it weakens safety, state consistency, data separation, fail-closed behavior, validation ability, or user simplicity.

The goal is not to make a perfect document or a perfect system in one pass. The goal is to keep implementation moving in the correct direction when the document is incomplete, while never opening unsafe live risk by assumption.

---

## 2. Authority order

When instructions conflict, apply this order.

```text
1. TRADER_1.md AUTH top-level interpretation contract
2. TRADER_1.md SAFE safety invariant contract
3. TRADER_1.md REG canonical registry and generated contract
4. TRADER_1.md enum, schema, state machine, validator, stage gate, readiness rules
5. TRADER_1.md detail requirements requirements detailed requirements body
6. This AGENTS.md
7. Existing repository code
```

This AGENTS.md must never weaken any enum, schema, state machine, validator, stage gate, readiness, safety, or namespace rule in TRADER_1.md.

Existing code never overrides the design authority. Code that conflicts with the design authority must be revised, isolated, blocked, or removed.

If the design authority conflicts with current official exchange API documentation, official exchange information wins only for external API facts, fees, rate limits, symbol rules, order constraints, margin rules, and policy details. Official exchange information must not weaken safety, fail-closed behavior, namespace separation, logging, validation, or UX behavior.

---

## 3. Non-removal rule

Do not remove user requirements or existing intended features by treating them as out of scope.

Final scope includes:

```text
Upbit KRW spot
Binance spot
Binance USD-M futures
replay
paper
shadow
live
LIVE_READY snapshot
small live burn-in
gradual capital scale-up
automatic scale-down, degradation, retirement
automatic strategy candidate generation
strategy scoring and competition
market regime adaptation
dashboard UX
security, backup, accounting, tax, regulation, operations monitoring
full audit and validator-based blocking
```

MVP scope only controls implementation order. MVP scope does not delete final scope.

---

## 4. Interpretation rules

Apply these rules in every implementation decision.

```text
If the document has internal contradictions, use the newest upper-level contract.
If upper-level contracts conflict, choose safety, consistency, and fail closed.
If exchange API, fees, rate limits, symbol rules, order constraints, or policy details conflict with the document, use current official exchange information.
Do not assert profitability by reasoning. Profitability is decided only by replay, paper, shadow, and live burn-in evidence.
If the document is wrong or incomplete, continue with a safe default, record the correction, and keep implementation moving.
Never open live trading capability by assumption.
```

Core rule:

```text
Document wording is subordinate to system intent, safety, state consistency, exchange reality, and verifiability.
```

---

## 5. Registry-first discipline

The implementation does not need an oversized registry before basic scaffolding, but it must not allow conflicting sources of contract truth.

Minimum registry scope when code reaches contract implementation:

```text
closed enums
schema identifiers
required schema fields
path and namespace rules
validator list
stage gates
no-trade reason codes
engine and order lifecycle states
risk profiles
strategy lifecycle states
strategy levels
readiness vocabulary
live readiness blockers
operator action codes
bundle rules
```

Rules:

```text
if canonical registry exists, generated docs and generated schema projections must not be manually edited
if no registry exists, code may start with minimal typed constants and schema files
if two contract sources disagree, use TRADER_1 authority order and record the correction
unknown enum or unknown schema field in critical path -> BLOCKED or SAFE_MODE until mapped
registry/document mismatch -> CONTRACT_DRIFT and affected path BLOCKED
```

When changing a contract value, use this order.

```text
registry_update
schema_update_if_needed
validator_update_if_needed
dashboard_wording_update_if_needed
regenerate_generated_sections
manifest_hash_update
stage_gate_revalidation
```

---

## 6. Non-negotiable priorities

Apply this priority order whenever implementation choices conflict.

```text
safety
state consistency
data and namespace separation
exchange constraints
market type risk constraints
fail closed
user-simple UX
validation ability
maintainability
profitability improvement potential
extensibility
```

Profitability is considered only after safety, consistency, validation, and exchange realism are satisfied.

Mandatory behavior:

```text
unknown input -> fail closed
missing hard truth -> no trade
state mismatch -> stop new orders and reconcile
ambiguous order result -> do not resend with a new identifier
validator failure -> block affected path
live uncertainty -> block live
dashboard uncertainty -> display blocked or checking, not normal
```

---

## 7. AI autonomy rules

The AI compiler may decide missing file names, function names, class names, module boundaries, and local implementation details when the design authority does not specify them.

The AI compiler must choose the simplest implementation that satisfies the design authority contract.

The AI compiler must not ask the user for clarification when a conservative, safe, and verifiable implementation choice is available.

The AI compiler must record meaningful autonomous decisions when they affect runtime behavior, schema, live blocking, state transitions, or safety.

Allowed autonomous choices:

```text
naming functions and classes
choosing simple module boundaries
adding schema fields required by the design authority
adding validators and tests
adding safe defaults
blocking unverified live paths
adapting existing repo structure without weakening design authority
creating paper, shadow, read-only, or mock adapters before live adapters
```

Forbidden autonomous choices:

```text
opening live trading by inference
assuming strategy profitability
assuming official exchange API details are current
mixing paper, shadow, live, replay, exchange, or market type data
letting dashboard state become trading truth
letting strategy code call exchange APIs directly
silently swallowing failures
resubmitting ambiguous orders with new identifiers
removing user-intended final-scope features because they are not in the current MVP
```

---

## 8. Root launcher contract

Allowed root launchers:

```text
UPBIT_PAPER
UPBIT_LIVE
BINANCE_PAPER
BINANCE_LIVE
```

Do not place dashboard-only, debug-only, test-only, temporary, duplicate, or experimental launchers at the repository root.

Paper launchers must not be able to submit live orders.

Live launchers must not use a paper broker as live execution.

BINANCE launchers must select SPOT or FUTURES_USDT_M through validated config, internal UI, or explicit command option. Futures live must never be an implicit default.

---

## 9. Namespace contract

Every runtime artifact must be keyed or physically separated by:

```text
exchange
market_type
mode
session_id
strategy_id if applicable
symbol if applicable
```

Path format:

```text
system/data/<exchange>/<market_type>/<mode>/
system/logs/<exchange>/<market_type>/<mode>/
system/runtime/<exchange>/<market_type>/<mode>/
system/reports/<exchange>/<market_type>/<mode>/
system/validation/<exchange>/<market_type>/<mode>/
system/evidence/<exchange>/<market_type>/<mode>/<session_id>/
system/snapshots/<exchange>/<market_type>/LIVE_READY/
system/configs/<exchange>/<market_type>/
```

Never join raw paper, shadow, and live data directly. Cross-mode comparison must use an explicit comparison evidence pack or a defined comparison report.

---

## 10. Truth hierarchy

Execution truth:

```text
ledger
intent WAL
order events
fill events
balance snapshots
position snapshots
exchange reconciliation snapshot
risk decisions
final decisions
```

Analysis truth:

```text
signal outcome reports
no-trade reviews
score calibration reports
shadow reports
walk-forward reports
replay reports
performance summaries
```

Dashboard serving truth:

```text
summary.json
heartbeat.json
startup_probe.json
action_queue.json
operator_status.json
recent_no_trade_context.json
recent_entry_context.json
readiness_surface.json
```

Rules:

```text
ledger and reconciliation truth drive trading decisions
summary and dashboard files display state but do not create trading truth
reports inform review and validation but do not override live execution state
validation support artifacts are evidence, not runtime truth
truth source conflict blocks new orders and requires reconciliation
```

---

## 11. Decision, risk, and order path

All strategy signals must pass through a central decision path before execution.

Global conflict priority:

```text
P0 manual emergency stop, kill switch, legal or exchange-enforced block
P1 hard truth availability, schema integrity, ledger durability
P2 exchange constraints, market type constraints, API policy, symbol rules
P3 account reconciliation, balance truth, position truth, open order truth
P4 portfolio risk, strategy risk, exposure, MDD, loss limit
P5 market regime, volatility, liquidity, data quality
P6 strategy lifecycle, strategy score, LIVE_READY scope
P7 execution quality, fee, slippage, market impact, latency
P8 user dashboard display and convenience
```

Strategies propose. Risk and decision arbiter decide. Execution only executes final decisions.

Order path rules:

```text
use one writer or equivalent serialized transaction path
reserve budget before external order submission
no network I/O inside database transactions
commit local reservation before external submit
use client_order_id or intent_id for idempotency
ambiguous submit result -> do not send new order with new identifier
ambiguous submit result -> reconcile using same identifier first
exchange order exists but local commit failed -> stop or reconcile before new orders
fill events must be deduplicated
ledger mismatch blocks new orders
```

---

## 12. Adapter contract

Strategies must not call exchange APIs directly.

Every exchange adapter must provide or emulate:

```text
MarketDataAdapter
AccountAdapter
OrderAdapter
PositionAdapter
FeeAdapter
SlippageAdapter
SymbolRulesAdapter
RiskAdapter
WebSocketAdapter
RateLimitAdapter
ErrorNormalizer
HealthAdapter
ReconciliationAdapter
```

If official API information is not verified, adapter state is not live-ready.

---

## 13. Strategy and risk rules

A strategy unit is:

```text
strategy_id
strategy_build_id
parameter_set
parameter_hash
exchange
market_type
regime_scope
risk_profile
```

Rules:

```text
LIVE_READY applies to the full strategy unit, not to the name alone
same strategy with different parameters, exchange, market type, regime, or risk profile is a separate candidate
strategies may propose signals but must not place orders directly
strategies must produce reason data for entry and no-entry decisions
strategy thresholds are not live evidence
seed strategies may be used for paper, replay, tests, and fixtures before profitability is proven
strategy changes require relevant revalidation before live expansion
```

Risk profiles:

```text
CONSERVATIVE
BALANCED
GROWTH
AGGRESSIVE_SANDBOX
```

AGGRESSIVE_SANDBOX must never become the default profile and must not share capital limits with core operating capital.

---

## 14. Readiness vocabulary

Implement these as separate fields, not synonyms.

```text
release_ready
bundle_ready
can_start
can_collect_data
can_evaluate_candidates
can_paper_trade
can_shadow_evaluate
can_replay
can_live_review
can_live_trade
live_order_ready
```

release_ready, bundle_ready, can_start, and can_live_review do not imply live_order_ready.

Dashboard must avoid unscoped READY labels.

---

## 15. Live readiness and user flow

Live launcher must:

```text
load latest valid LIVE_READY snapshot for correct exchange and market type
run preflight automatically
verify user approval if required by implementation stage
verify official API report
verify API permissions
verify exchange sync
verify symbol rules and fee model
verify risk limits and kill switch
verify ledger and resource health
verify source/release identity
verify artifact hygiene
start with small order sizing if all checks pass
block live new orders with one clear reason if any check fails
```

Paper launcher must never place live orders.

Live launcher must never use paper broker as live execution.

---

## 16. MVP implementation order

Follow this implementation order unless existing repository state requires a safer prerequisite.

```text
MVP-0 Contract baseline
MVP-1 Safe boot skeleton
MVP-2 Upbit paper dry-run
MVP-3 Operational Upbit paper
MVP-4 Upbit live review
MVP-5 Upbit limited live
MVP-6 Multi-exchange paper
MVP-7 Binance limited live
```

Do not implement advanced profitability optimization before safety, namespace separation, ledger integrity, decision arbiter, risk veto, dashboard source discipline, and live-blocked validation paths are stable.

---

## 17. Testing and validation

Run relevant tests after each change when possible.

```text
python -m pytest
```

If the repo has no tests, add minimal tests for the changed contract rather than claiming untested success.

Required validator categories:

```text
schema_validator
state_transition_validator
strategy_decision_validator
risk_sizing_validator
exchange_adapter_validator
numeric_determinism_validator
path_namespace_validator
dashboard_source_validator
ledger_reconciliation_validator
live_ready_snapshot_validator
security_validator
resource_limit_validator
stage_gate_validator
artifact_hygiene_validator
bundle_identity_validator
official_api_verification_validator
operator_control_validator
```

Validator not run means UNTESTED, not READY.

---

## 18. External API handling

Before marking any live adapter ready, verify current official exchange information using the official API verification report schema in TRADER_1.md.

If verification is not available in the coding environment:

```text
adapter may be implemented as contract or mock
paper and shadow may run
read-only checks may run
live readiness remains BLOCKED
```

Never use outdated examples, old SDK behavior, or assumed exchange rules as live authority.

---

## 19. Security rules

```text
API keys must not be committed
API keys must not appear in logs
signatures, account IDs, private payloads, and secrets must be masked
withdrawal permission must not be accepted as normal
live API key permission must be validated before live start
IP restriction and key rotation support should be documented when applicable
if secret handling is unclear, block live and use paper or read-only
```

---

## 20. Operator control rules

Allowed operator controls where implemented:

```text
manual_stop
manual_resume_read_only
manual_ack_trade_disabled
manual_unlock_held_market_event
manual_retry_reconcile
manual_safe_mode
manual_disable_strategy
manual_reduce_position
manual_exit_all_positions
```

Rules:

```text
manual control must produce an audit record
manual control cannot convert BLOCKED live to LIVE_ACTIVE without preflight
manual override cannot force an unverified strategy into live
manual close or reduce may be allowed for risk reduction, but must still use adapter, ledger, and reconciliation rules
stlong actions require operator identity, action id, reason, scope, confirmation, ledger record, and reconciliation after action
```

---

## 21. Bundle rules

Separate:

```text
source bundle
release bundle
evidence bundle
diagnostic bundle
```

Source bundle denylist:

```text
system/
export/
release/
logs/
__pycache__/
.pytest_cache/
*.pyc
*.pyo
*.sqlite
*.db
*.jsonl
*.log
*.tmp
*.bak
runtime journal
large raw data
local private path artifact
credential-bearing file
```

Credential scan and redaction must run before bundle creation.

Unexplained root/release source drift blocks release readiness and live readiness.

---

## 22. Existing code handling

When applying this guide to an existing repository:

```text
inspect the full repository before large changes
identify actual root launchers
identify any live order path
identify data, log, config, and runtime paths
identify state truth sources
identify strategy-to-exchange direct calls
identify dashboard source paths
identify tests and validators
fix highest-risk violations first
avoid broad rewrites unless necessary to remove safety risk
preserve existing intended features unless they violate safety or authority
```

Priority fixes:

```text
live safety
mode separation
single truth source
order idempotency
risk veto
kill switch
ledger integrity
secret leakage
no-trade reason visibility
dashboard truth discipline
registry drift
readiness vocabulary confusion
artifact hygiene
```

---

## 23. Completion language

Do not claim these unless evidence exists:

```text
profitable
live ready
fully safe
production ready
API verified
```

Allowed claims when true:

```text
implemented scaffold
paper path ready for local test
validator added
live path blocked by design
adapter mock added
preflight blocks unverified live
```

PASS_WITH_LIMITATION is not live readiness.

---

## 24. Patch workflow

When making a document or code patch:

```text
1. Identify affected contract ids.
2. Confirm no user requirement or final-scope feature is silently removed.
3. Update registry first if contract values change.
4. Update schema and validators if needed.
5. Update implementation.
6. Update dashboard wording if user-facing state changes.
7. Add or update tests.
8. Run relevant validation.
9. Create evidence or audit record.
10. Mark unresolved blockers explicitly.
```

A patch that narrows live risk is allowed when evidence is missing. A patch that opens live risk requires evidence.

---

## 25. Default behavior when unsure

```text
Do not open new live risk.
Preserve or reduce existing risk.
Reconcile state.
Use paper, shadow, read-only, or safe mode.
Show a one-line reason.
Record the decision.
Add a validator or test if the issue can recur.
```


# Detailed requirements body



---

# AGENTS.md

TRADER_1 AI compiler implementation guide


This file is the implementation guide for AI coding agents working on TRADER_1. It does not replace the design authority. It converts the design authority into operational rules for repository work.

## 1. Role

You are the AI compiler for TRADER_1.

Your job is to implement, audit, improve, refactor, and test the repository so that it follows the design authority.

You must prioritize the whole system over local feature completion. A local feature is invalid if it weakens safety, state consistency, data separation, fail-closed behavior, or user simplicity.

## 2. Authority order

When instructions conflict, apply this order.

```text
1. Top-level interpretation contract
2. AI Compiler autonomy contract
3. Closed execution contract body
4. Enum, schema, state machine, validator, stage gate, and scenario rules
5. Detailed requirements contract
6. This AGENTS.md
7. Existing repository code
```

This AGENTS.md must never weaken any enum, schema, state machine, validator, or stage gate requirement in the design authority. If this file appears looser than the design authority, the design authority wins.

Existing code never overrides the design authority. Code that conflicts with the design authority must be revised, isolated, blocked, or removed.

If the design authority conflicts with current official exchange API documentation, official exchange information wins only for external API facts, fees, rate limits, symbol rules, order constraints, and policy details. Official exchange information must not weaken safety, fail-closed behavior, namespace separation, logging, validation, or UX behavior.

## 3. Top-level interpretation rules

Apply these rules in every implementation decision.

```text
1. If the document has internal contradictions, use the newest upper-level contract.
2. If upper-level contracts conflict, choose safety, consistency, and fail closed.
3. If exchange API, fees, rate limits, symbol rules, order constraints, or policy details conflict with the document, use the current official exchange information.
4. Do not assert profitability by reasoning. Profitability is decided only by replay, paper, shadow, and live burn-in evidence.
5. If the document is wrong or incomplete, continue with a safe default, record the correction, and keep implementation moving.
6. Never open live trading capability by assumption.
```

The core rule is:

```text
Document wording is subordinate to system intent, safety, state consistency, exchange reality, and verifiability.
```

## 3A. Authority integrity discipline

Before implementation work begins, identify the active design authority and record its path and integrity hash when available.

Required behavior:

```text
active design authority -> TRADER_1.md unless explicitly superseded
manifest match available -> verify and record
manifest missing -> record AUTHORITY_HASH_UNVERIFIED but continue from the provided authority file
manifest mismatch -> block live-affecting changes until the active authority is resolved
multiple authority candidates found -> use the file explicitly selected by the user, otherwise block live-affecting changes until resolved
```

This rule should not stop safe paper-only scaffolding. It must stop live readiness claims and live-enabling changes when authority identity is ambiguous.

## 3B. Canonical registry and generated artifact discipline

The implementation does not need an oversized registry before basic scaffolding, but it must not allow conflicting sources of contract truth.

Minimum registry scope when code reaches contract implementation:

```text
closed enums
schema identifiers
path and namespace rules
validator list
stage gates
no-trade reason codes
engine and order lifecycle states
live readiness blockers
```

Rules:

```text
if a canonical registry exists, generated docs and generated schema projections must not be manually edited
if no registry exists, code may start with minimal typed constants and schema files
if two contract sources disagree, use the design authority order and record the correction
unknown enum or unknown schema field in critical path -> BLOCKED or SAFE_MODE until mapped
```

## 4. Non-negotiable priorities

Apply this priority order whenever implementation choices conflict.

```text
safety
state consistency
data and namespace separation
exchange constraints
market type risk constraints
fail closed
user-simple UX
validation ability
maintainability
profitability improvement potential
extensibility
```

Profitability is considered only after safety, consistency, validation, and exchange realism are satisfied.

Mandatory behavior:

```text
unknown input -> fail closed
missing hard truth -> no trade
state mismatch -> stop new orders and reconcile
ambiguous order result -> do not resend with a new identifier
validator failure -> block affected path
live uncertainty -> block live
dashboard uncertainty -> display blocked or checking, not normal
```

## 5. AI autonomy rules

The agent may decide missing file names, function names, class names, module boundaries, and local implementation details when the document does not specify them.

The agent must choose the simplest implementation that satisfies the design authority contract.

The agent must not ask the user for clarification when a conservative, safe, and verifiable implementation choice is available.

The agent must record meaningful autonomous decisions when they affect runtime behavior, schema, live blocking, state transitions, or safety.

Allowed autonomous choices:

```text
naming functions and classes
choosing simple module boundaries
adding schema fields required by the design authority
adding validators and tests
adding safe defaults
blocking unverified live paths
adapting existing repo structure without weakening design authority
```

Forbidden autonomous choices:

```text
opening live trading by inference
assuming strategy profitability
assuming official exchange API details are current
mixing paper, shadow, live, replay, exchange, or market type data
letting dashboard state become trading truth
letting strategy code call exchange APIs directly
silently swallowing failures
resubmitting ambiguous orders with new identifiers
```

## 6. Root launcher contract

The repository root must expose only the user-facing launchers required by the design authority.

Allowed user launchers:

```text
UPBIT_PAPER
UPBIT_LIVE
BINANCE_PAPER
BINANCE_LIVE
```

The exact extension may follow the operating system or existing project convention, such as .py, .bat, .sh, or packaged executable.

Do not place dashboard-only, debug-only, test-only, temporary, duplicate, or experimental launchers at the repository root.

Paper launchers must not be able to submit live orders.

Live launchers must not use a paper broker as live execution.

## 7. Recommended repository structure

If the existing repository already has a clean structure, adapt it incrementally. If a new structure is needed, prefer this shape.

```text
src/trader1/
  adapters/
    upbit/
    binance_spot/
    binance_futures/
  core/
    decision/
    risk/
    sizing/
    strategy/
    portfolio/
    ledger/
    state/
    events/
  runtime/
    boot/
    health/
    reconciliation/
    resource_guard/
  dashboard/
  validation/
  research/
  reports/
  config/
  utils/

tests/
  unit/
  integration/
  contract/
  replay/
  adapter/

system/
  data/
  runtime/
  reports/
  validation/
  evidence/
  snapshots/
  configs/
```

Do not rewrite the whole repository solely for style. Refactor only when needed to satisfy design authority or remove actual risk.

## 8. Namespace contract

Every runtime artifact must be keyed or physically separated by:

```text
exchange
market_type
mode
session_id
strategy_id if applicable
symbol if applicable
```

Recommended path slugs are directory names only. Runtime schema fields must use the closed enum values in section 11 unless an explicit enum-to-path-slug mapper is implemented and validated.

Recommended exchange path slugs:

```text
upbit
binance
```

Recommended market type path slugs:

```text
krw_spot
spot
futures_usdt_m
```

Recommended mode path slugs:

```text
paper
live
shadow
replay
read_only
safe
```

Recommended path format:

```text
system/data/<exchange>/<market_type>/<mode>/
system/logs/<exchange>/<market_type>/<mode>/
system/runtime/<exchange>/<market_type>/<mode>/
system/reports/<exchange>/<market_type>/<mode>/
system/validation/<exchange>/<market_type>/<mode>/
system/evidence/<exchange>/<market_type>/<mode>/<session_id>/
system/snapshots/<exchange>/<market_type>/LIVE_READY/
system/configs/<exchange>/<market_type>/
```

Never join raw paper, shadow, and live data directly. Cross-mode comparison must use an explicit comparison evidence pack or a defined comparison report.

## 9. Runtime truth hierarchy

Execution truth:

```text
ledger
intent WAL
order events
fill events
exchange reconciliation snapshot
```

Analysis truth:

```text
signal outcome reports
no-trade reviews
score calibration reports
shadow reports
performance summaries
```

Dashboard serving truth:

```text
summary.json
heartbeat.json
startup_probe.json
action_queue.json when used
```

Rules:

```text
ledger and reconciliation truth drive trading decisions
summary and dashboard files display state but do not create trading truth
reports inform review and validation but do not override live execution state
validation support artifacts are evidence, not runtime truth
truth source conflict blocks new orders and requires reconciliation
```

## 10. Hard truth and soft truth

Hard truth is required for trading decisions. If hard truth is missing, stale, contradictory, or unverified, new entry is forbidden.

Hard truth fields:

```text
engine_state
mode
exchange
market_type
session_id
config_hash
registry_hash
schema_id
ledger_write_status
startup_probe_phase
exchange_account_snapshot
balance_snapshot
position_snapshot
open_order_snapshot
pending_intent_state
orderbook_freshness
trade_stream_freshness
confirmed_candle_state
symbol_rules
min_notional_rule
tick_size_rule
step_size_rule
fee_snapshot
slippage_bound
risk_limit_state
kill_switch_state
resource_health_state
private_ws_health_if_live
reconciliation_status
LIVE_READY_snapshot_if_live
strategy_lifecycle_state
final_decision_id
```

Soft truth may use a declared neutral or conservative fallback.

Soft truth fields:

```text
optional_market_breadth_metric
optional_taker_buy_ratio
optional_sentiment_metric
optional_dashboard_display_value
optional_review_score
optional_explanatory_text
optional_noncritical_backtest_tag
```

Rules:

```text
unknown hard truth -> NO_TRADE or SAFE_MODE
soft truth fallback -> declared and conservative only
undefined fallback -> hard truth missing
missing data must never increase risk, size, leverage, confidence, or live readiness
```

## 11. Closed enums

Use closed enums for runtime decision and state values covered here. Unknown enum values must not silently pass.

Exchange values:

```text
UPBIT
BINANCE
```

Market type values:

```text
KRW_SPOT
SPOT
FUTURES_USDT_M
```

Mode values:

```text
REPLAY
PAPER
SHADOW
LIVE
SAFE
READ_ONLY
```

Engine states:

```text
BOOTSTRAP_READ_ONLY
STARTUP_PROBE
RUNNING
TRADE_DISABLED
SAFE_MODE
HELD_MARKET_EVENT_LOCK
DEGRADED_QUEUE_PRESSURE
DRIFT_UNRECOVERED
PRIVATE_WS_UNHEALTHY
RECONCILE_REQUIRED
RESOURCE_LIMITED
KILL_SWITCH_TRIGGERED
ACTION_REQUIRED
BLOCKED
SHUTTING_DOWN
STOPPED
```

Strategy lifecycle states:

```text
CANDIDATE
REPLAY_TESTING
REPLAY_VALIDATED
PAPER_VALIDATING
PAPER_VALIDATED
SHADOW_VALIDATED
LIVE_READY
LIVE_ACTIVE
DEGRADED
RETIRED
BLOCKED
```

Order lifecycle states:

```text
INTENT_CREATED
PRECHECKED
RESERVED
SENT
PENDING_CONFIRM
OPEN
PARTIAL_FILLED
FILLED
CANCELED
REJECTED
EXPIRED
REST_RECONCILED
RECONCILE_REQUIRED
```

Final decisions:

```text
ENTER_LONG
ENTER_SHORT
EXIT_POSITION
REDUCE_POSITION
CANCEL_ORDER
HOLD_POSITION
NO_TRADE
SAFE_MODE
RECONCILE_REQUIRED
TRADE_DISABLED
KILL_SWITCH
BLOCKED
```

UPBIT KRW spot and BINANCE spot must reject ENTER_SHORT. Short exposure is allowed only through the futures adapter after futures-specific risk, margin, liquidation, funding, leverage, reduce-only, and reconciliation checks pass.

POSITION_PROTECT_ONLY is not a canonical internal enum. It may be used only as a user-facing display alias that maps to one or more of these internal decisions:

```text
REDUCE_POSITION
EXIT_POSITION
CANCEL_ORDER
RECONCILE_REQUIRED
SAFE_MODE
BLOCKED
```

Operator badges:

```text
NORMAL
READ_ONLY
DEGRADED
ACTION_REQUIRED
STOPPED
BLOCKED
```

Action queue codes:

```text
STARTUP_PROBE_IN_PROGRESS
STARTUP_PROBE_GATE_BLOCKED
PRIVATE_WS_UNHEALTHY
PENDING_CONFIRM_STUCK
DRIFT_UNRECOVERED
HELD_MARKET_EVENT
TRUTH_QUEUE_PRESSURE
REPORT_BUILD_DELAY
RATE_LIMIT_PRESSURE
CRASH_LOOP_REVIEW_REQUIRED
EXTERNAL_OPEN_ORDER_REVIEW_REQUIRED
SUMMARY_LAGGING
STORAGE_DURABILITY_FAILURE
CLOCK_DRIFT
PUBLIC_IP_CHANGE
RECONCILIATION_REQUIRED
LIVE_READY_SNAPSHOT_REQUIRED
MANUAL_APPROVAL_REQUIRED
KILL_SWITCH_REVIEW_REQUIRED
RESOURCE_LIMIT_REVIEW_REQUIRED
```

## 12. No-trade reason enum

Every no-trade decision must have a closed reason code. Free-text alone is invalid.

Baseline reason codes:

```text
MIN_EDGE_FAIL
EXPECTED_SLIPPAGE_EXCEEDED
DEPTH_TOO_THIN
DEPTH_EXCHANGE_REJECT_RISK
STALE_ORDERBOOK
PRIVATE_WS_UNHEALTHY
DRIFT_UNRECOVERED
SESSION_PAUSE
TICK_SIZE_CLIFF
BALANCE_MISMATCH
MARKET_EVENT_RISK
BREADTH_OFF_BLOCKED
PENDING_CONFIRM_EXISTS
COOLDOWN
CLUSTER_RISK
UNIVERSE_FILTERED
POSITION_LIMIT
TRADE_DISABLED
COLD_START
DATA_UNAVAILABLE
HARD_TRUTH_MISSING
SOFT_TRUTH_UNREGISTERED_FALLBACK
RESOURCE_LIMIT
RESOURCE_LIMIT_BLOCK
LEDGER_INTEGRITY_FAIL
LEDGER_UNAVAILABLE
EXCHANGE_SYNC_REQUIRED
RECONCILIATION_REQUIRED
SYMBOL_RULE_BLOCK
SYMBOL_RULE_UNVERIFIED
FEE_MODEL_UNVERIFIED
FEE_EXCEEDS_EDGE
MARKET_IMPACT_EXCEEDS_EDGE
LIVE_READY_MISSING
USER_APPROVAL_MISSING
PREFLIGHT_FAILED
SNAPSHOT_SCOPE_MISMATCH
API_UNVERIFIED
RISK_VETO
REGIME_MISMATCH
EXCHANGE_POLICY_BLOCK
STRATEGY_NOT_ELIGIBLE
STRATEGY_CONFIDENCE_LOW
KILL_SWITCH_ACTIVE
LATENCY_TTL_EXPIRED
UNKNOWN_BLOCKED
```

If a new reason is needed, add it to the enum, add dashboard wording, and add tests. Do not store only arbitrary prose.

## 13. Decision and conflict resolution

All strategy signals must pass through a central decision path before execution.

Global conflict priority:

```text
P0 manual emergency stop, kill switch, legal or exchange-enforced block
P1 hard truth availability, schema integrity, ledger durability
P2 exchange constraints, market type constraints, API policy, symbol rules
P3 account reconciliation, balance truth, position truth, open order truth
P4 portfolio risk, strategy risk, exposure, MDD, loss limit
P5 market regime, volatility, liquidity, data quality
P6 strategy lifecycle, strategy score, LIVE_READY scope
P7 execution quality, fee, slippage, market impact, latency
P8 user dashboard display and convenience
```

Required decision path:

```text
hard truth check
resource health check
exchange health check
market data freshness check
exchange and symbol rule check
account reconciliation check
strategy signal normalization
market regime filter
risk veto
portfolio and exposure check
allocator arbitration
execution quality check
final decision
single execution path
ledger and evidence recording
```

Conflict rules:

```text
higher global priority always beats lower global priority
risk veto beats market regime, strategy, allocator, execution preference, and UX convenience
exchange and symbol constraints beat market regime and strategy intent
market regime beats strategy signal
portfolio exposure constraints beat individual strategy score
allocator decides equal-ranked capital competition
allocator uncertainty -> NO_TRADE
opposing signals for same symbol or contract -> one final decision only
state inconsistency -> RECONCILE_REQUIRED or SAFE_MODE
stale or partial data -> NO_TRADE or BLOCKED
uncertain live permission -> BLOCKED
```

Strategies propose. Risk and decision arbiter decide. Execution only executes final decisions.

## 14. Single writer and idempotent order path

The order path must be idempotent and recoverable.

Rules:

```text
use one writer or equivalent serialized transaction path
reserve budget before external order submission
no network I/O inside database transactions
commit local reservation before external submit
use client_order_id or intent_id for idempotency
ambiguous submit result -> do not send new order with new identifier
ambiguous submit result -> reconcile using same identifier first
exchange order exists but local commit failed -> stop or reconcile before new orders
fill events must be deduplicated
ledger mismatch blocks new orders
```

## 15. Adapter contract

Strategies must not call exchange APIs directly.

Every exchange adapter must provide or emulate these responsibilities:

```text
MarketDataAdapter
AccountAdapter
OrderAdapter
PositionAdapter
FeeAdapter
SlippageAdapter
SymbolRulesAdapter
RiskAdapter
WebSocketAdapter
RateLimitAdapter
ErrorNormalizer
HealthAdapter
ReconciliationAdapter
```

Upbit KRW spot requirements:

```text
KRW spot long-oriented structure
minimum order amount validation
tick size and price normalization
fee calculation
KRW and coin free and locked balance tracking
public and private stream separation
rate limit throttling
order error normalization
candle no-trade versus missing-candle distinction
live blocked unless official current rules are verified
```

Binance spot requirements:

```text
base and quote free and locked balances
min notional, tick size, step size, min quantity
maker and taker fees, VIP tier, BNB discount when applicable
timestamp, recvWindow, signature, server time drift handling
user stream reconnect and gap recovery
partial and multiple fill ledger accuracy
no futures margin, liquidation, or reduce-only logic in spot adapter
```

Binance futures requirements:

```text
long and short position modeling
hedge mode and one-way mode distinction
isolated and cross margin distinction
leverage, margin ratio, liquidation price, mark price, and funding fee
reduce-only, stop market, take profit, and trailing stop support where used
listenKey or user data stream renewal and recovery
realized and unrealized PnL separation
liquidation risk reduction before expansion
no spot balance model misuse
```

If official API information is not verified, adapter state is not live-ready.

## 16. Strategy implementation rules

Strategies must be treated as candidates until evidence exists.

A strategy unit is:

```text
strategy_id
strategy_build_id
parameter_set
exchange
market_type
regime_scope
risk_profile
```

Rules:

```text
LIVE_READY applies to the full strategy unit, not to the name alone
same strategy with different parameters, exchange, market type, regime, or risk profile is a separate candidate
strategies may propose signals but must not place orders directly
strategies must produce reason data for entry and no-entry decisions
strategy thresholds are not live evidence
seed strategies may be used for paper, replay, tests, and fixtures before profitability is proven
strategy changes require relevant revalidation before live expansion
```

## 16A. Market regime and universe rules

Market regime must influence entry permission, strategy selection, universe ranking, risk filtering, and sizing.

Minimum regime classes:

```text
DOWNTREND
RANGE
UPTREND
BREAKDOWN
HIGH_VOLATILITY
LOW_LIQUIDITY
UNCERTAIN
```

Rules:

```text
DOWNTREND -> spot long entry is restricted unless an explicitly validated exception exists
RANGE -> mean-revert or VWAP-style candidates may be considered
UPTREND -> pullback, breakout, and momentum candidates may be considered
BREAKDOWN -> block new entries or enter extreme conservative mode
HIGH_VOLATILITY -> reduce size, restrict entries, or block entries
LOW_LIQUIDITY -> block new entries
UNCERTAIN -> no aggressive entry
```

Universe selection must consider at least liquidity, spread, volatility, recent trend, depth, execution feasibility, symbol rules, strategy fit, and market type constraints.

Every excluded candidate should produce a structured exclusion reason. Universe filtering must not become silent loss of opportunity without dashboard-readable explanation.

## 17. Sizing and risk rules

Sizing must prioritize survival and cost control over aggression.

Sizing inputs should include:

```text
equity
cash
locked cash
open risk
unrealized PnL
realized PnL
volatility
liquidity
spread
orderbook depth
signal quality
strategy confidence
recent performance
loss streak
current exposure
portfolio concentration
exchange
market type
regime
symbol rules
minimum order constraints
```

Rules:

```text
first live order starts small
account size does not imply full-size trading
good performance can expand size only step by step
expansion requires evidence and risk health
poor performance, drift, data issues, execution issues, or resource pressure reduce or stop trading
futures sizing must consider leverage, margin ratio, liquidation price, funding, and reduce-only paths
if sizing inputs conflict or are missing, reduce size or choose NO_TRADE
```

## 17A. Risk profile contract

Risk limits must be profile-based rather than a single global aggression setting. Profile selection may change only through config, validated strategy unit scope, LIVE_READY snapshot scope, or an auditable operator-approved transition.

Canonical risk profiles:

```text
CONSERVATIVE
BALANCED
GROWTH
AGGRESSIVE_SANDBOX
```

Profile intent:

```text
CONSERVATIVE -> new strategy, new adapter, new exchange, early paper, early live burn-in
BALANCED -> default operation profile for validated production-like use
GROWTH -> verified strategy units with stable live evidence and healthy risk state
AGGRESSIVE_SANDBOX -> isolated small-capital experiment bucket only
```

Rules:

```text
risk profile is part of the strategy unit
LIVE_READY applies only to the exact risk profile included in the snapshot
raising risk profile requires relevant revalidation and evidence
AGGRESSIVE_SANDBOX must never become the default profile
AGGRESSIVE_SANDBOX must not share capital limits with core operating capital
all profiles still obey hard truth, risk veto, ledger, reconciliation, kill switch, and live readiness rules
profile uncertainty -> downgrade to a safer profile or choose NO_TRADE
```

Core capital should use CONSERVATIVE or BALANCED unless a specific strategy unit has earned GROWTH through evidence. High-risk experiments belong only in AGGRESSIVE_SANDBOX and must be isolated so failure cannot propagate to core operation.

## 18. Dashboard contract

The dashboard is an operating interface, not a research notebook and not a truth engine.

The first view must answer:

```text
Is the system normal?
Is it paper or live?
Which exchange and market type?
Is LIVE_READY yes, no, checking, or blocked?
Is it making or losing money?
Why is it not entering?
Why did it enter held positions?
Should the user wait, stop, or act?
```

Required first-view fields where applicable:

```text
mode
exchange
market_type
operator badge
engine state
LIVE_READY
current action
one-line blocking reason
portfolio equity
cash or available balance
locked balance
today PnL
realized PnL
unrealized PnL
MDD
positions
open orders
pending confirms
watch universe
entry candidates
last no-trade reason
recent errors
resource health
exchange health
data freshness
applied snapshot id for live
```

Rules:

```text
basic screen is simple
details are collapsible
no-trade reason must be visible
entry reason for held positions must be visible
dashboard must not reinterpret ledger or report truth into trading truth
dashboard failure must not stop trading engine unless resource or state safety is affected
if dashboard and engine disagree, engine truth wins and dashboard shows a mismatch warning
```

## 19. Summary schema guidance

When summary.json is implemented, it should include at least:

```text
schema_id
project
generated_at_utc
exchange
market_type
mode
session_id
engine
startup
operator_status
connectivity
caches
queues
rate_limits
resources
portfolio
orders
watch_universe
entry_candidates
positions
strategies
market_context
action_queue
recent_errors
recent_no_trade_context
recent_entry_context
fee_snapshot
live_ready
applied_snapshot
final_action
blocking_reason
next_action
```

summary.json is display serving state only. It must not be used as primary ledger, fill, order, or reconciliation truth.

## 19A. Minimum runtime schema contracts

The exact implementation language and storage backend may vary, but these logical schemmust exist in some typed, testable form.

FinalDecision minimum fields:

```text
schema_id
decision_id
created_at_utc
mode
exchange
market_type
session_id
strategy_id when applicable
strategy_build_id when applicable
parameter_hash when applicable
symbol when applicable
side when applicable
final_decision
priority_path
blocking_reason when blocked
risk_veto
regime when applicable
expected_edge_bps when applicable
expected_fee_bps when applicable
expected_slippage_bps when applicable
expected_impact_bps when applicable
confidence_score when applicable
approved_notional when applicable
idempotency_key when applicable
input_hash
output_hash
```

LIVE_READY snapshot minimum fields:

```text
schema_id
snapshot_id
created_at_utc
exchange
market_type
mode_source
strategy_id
strategy_build_id
parameter_set
parameter_hash
risk_profile
regime_scope
build_id
data_schema_id
cost_model_id
adapter_contract_id
validation_results
performance_summary
paper_live_parity_estimate
fill_quality_summary
risk_limits
sizing_limits
live_ready
invalidated_by
manifest_hash
```

Ledger event minimum fields:

```text
schema_id
event_id
event_time_utc
exchange_time when applicable
mode
exchange
market_type
session_id
event_type
order_id when available
client_order_id when applicable
intent_id when applicable
symbol when applicable
side when applicable
quantity when applicable
price when applicable
fee_amount when applicable
fee_asset when applicable
realized_pnl when applicable
unrealized_pnl when applicable
balance_delta when applicable
position_delta when applicable
source
dedup_key
previous_hash when applicable
event_hash
```

If a field is not applicable, it should be explicitly null or absent by schema rule. It must not be silently invented.

## 20. Live readiness and user flow

User flow:

```text
run UPBIT_PAPER or BINANCE_PAPER
watch dashboard
confirm LIVE_READY yes
stop or keep paper
run UPBIT_LIVE or BINANCE_LIVE
watch live dashboard
stop if needed
```

Live launcher must:

```text
load the latest valid LIVE_READY snapshot for the correct exchange and market type
run preflight automatically
verify user approval if required by implementation stage
verify API permissions
verify exchange sync
verify symbol rules and fee model
verify risk limits and kill switch
verify ledger and resource health
start with small order sizing if all checks pass
block live new orders with one clear reason if any check fails
```

Paper launcher must never place live orders.

Live launcher must never use paper broker as live execution.

## 21. Implementation order

Follow this implementation order unless the existing repository requires a safer prerequisite.

These implementation phases do not replace the stage gate identifiers defined by the design authority. evidence packs must use the design authority stage gate identifiers when applicable.

Stage P0. Safety and state foundation:

```text
mode and namespace separation
root launcher separation
config validation
ledger or equivalent execution truth
intent WAL or equivalent journal
single writer order state path
startup probe
safe mode
kill switch
basic resource guard
```

Stage P1. Paper and dashboard foundation:

```text
paper execution model
shadow separation
runtime summary
heartbeat
dashboard first view
no-trade reason enum
entry reason logging
basic strategy fixtures
basic risk and sizing
```

Stage P2. Validation foundation:

```text
schema validators
strategy decision validator
risk sizing validator
adapter contract validator
numeric determinism validator
replay consistency test
paper and shadow separation test
ledger reconciliation test
```

Stage P3. Upbit readiness:

```text
upbit adapter official rule verification
upbit paper realism
upbit private stream or reconciliation path
upbit live preflight
upbit live blocked until evidence
```

Stage P4. Binance readiness:

```text
binance spot adapter
binance futures adapter
futures risk model
funding, liquidation, margin, reduce-only handling
binance live blocked until evidence
```

Stage P5. Automatic improvement:

```text
strategy scoring
candidate pool
promotion and degradation
parameter candidate generation
walk-forward and out-of-sample checks
LIVE_READY snapshot creation
```

Do not implement advanced profitability optimization before P0 through P2 safety and validation paths are stable.

## 22. Testing and validation

Run relevant tests after each change when possible.

If the repo has pytest:

```text
python -m pytest
```

If the repo has no tests, add minimal tests for the changed contract rather than claiming untested success.

Required validator categories must match the design authority validator scaffold at minimum:

```text
schema_validator
state_transition_validator
strategy_decision_validator
risk_sizing_validator
exchange_adapter_validator
numeric_determinism_validator
path_namespace_validator
dashboard_source_validator
ledger_reconciliation_validator
live_ready_snapshot_validator
security_validator
resource_limit_validator
stage_gate_validator
```

Critical failures block the affected paper or live path according to the design authority:

```text
live launcher can place orders without paper validation
paper launcher can call live order API
exchange-specific data mix
paper and live data mix
paper, shadow, and live data mix
exchange or market type data mix
duplicate order possibility exists
duplicate order path exists
duplicate execution truth source exists
ledger mismatch does not block trading
API key secret exposed
withdrawal permission accepted
risk veto can be bypassed
kill switch does not block new order
adapter order constraints are not reflected
adapter symbol rules unverified but live allowed
futures liquidation risk missing
dashboard can mislead the operator about current state
repeated critical defect recurs in full audit
unknown hard truth opens trading
summary.json is used as runtime truth
ambiguous order outcome creates a new order
unknown enum is accepted
schema identity mismatch allows live
live can start without LIVE_READY snapshot
```


## 22A. Stage gate and evidence pack rules

A stage is not complete because code exists. A stage is complete only when its required evidence exists.

Minimum evidence pack contents must include the design authority evidence pack fields and may include additional operational fields:

```text
validator_run_log
stage_gate_rollup
manifest_hash
schema_id
test_result_summary
audit_findings
blocking_defect_count
unresolved_minor_defects
paper_live_parity_report if applicable
reconciliation_report if applicable
stage_id
timestamp_utc
affected_exchange
affected_market_type
implemented_contracts
tests_executed
validator_results
known_blockers
runtime_artifacts_produced
risk_assessment
next_allowed_stage
```

Rules:

```text
stage skip is forbidden when it would bypass safety, namespace separation, ledger integrity, or live blocking
validator FAIL -> affected path BLOCKED
validator not run -> status UNTESTED, not READY
paper stage success does not imply live readiness
live readiness requires explicit LIVE_READY snapshot and preflight success
```

## 23. External API handling

Before marking any live adapter ready, verify current official exchange information.

If verification is not available in the coding environment:

```text
adapter may be implemented as contract or mock
paper and shadow may run
read-only checks may run
live readiness remains BLOCKED
```

Never use outdated examples, old SDK behavior, or assumed exchange rules as live authority.

## 24. Security rules

```text
API keys must not be committed
API keys must not appear in logs
signatures, account IDs, private payloads, and secrets must be masked
withdrawal permission must not be accepted as normal
live API key permission must be validated before live start
IP restriction and key rotation support should be documented when applicable
if secret handling is unclear, block live and use paper or read-only
```


## 24A. Operator control rules

Operator control must be limited, explicit, and auditable. User actions must not bypass risk veto, state reconciliation, or live readiness.

Allowed operator controls where implemented:

```text
manual_stop
manual_resume_read_only
manual_ack_trade_disabled
manual_unlock_held_market_event
manual_retry_reconcile
manual_safe_mode
manual_disable_strategy
manual_reduce_position
manual_exit_all_positions
```

Rules:

```text
manual control must produce an audit record
manual control cannot convert BLOCKED live to LIVE_ACTIVE without preflight
manual override cannot force an unverified strategy into live
manual close or reduce may be allowed for risk reduction, but must still use adapter, ledger, and reconciliation rules
```

## 25. Audit and implementation evidence

When the agent makes a meaningful architectural decision, schema change, safety rule, live blocking change, or document correction, record it.

Preferred locations:

```text
system/evidence/audit/
system/evidence/implementation_decisions/
system/evidence/implementation_evidence/
system/evidence/safety_evidence/
```

Minimum record fields:

```text
timestamp
agent or process
change summary
reason
affected files
risk assessment
validation performed
remaining blocked items
```

Do not claim completion without recording unresolved blockers.

## 26. User experience rules

The user should not manage internal parameters, hashes, evidence files, adapter states, or risk formulas manually.

User-visible text must be short and operational.

Good examples:

```text
LIVE_READY: NO - paper validation trade can insufficient
status: SAFE_MODE - exchange balance synchronization required
current no-entry: insufficient expected value, excessive spread
initial safety bijung as start among
```

Bad examples:

```text
startup failed
internal error
unknown problem
strategy not working
preflight object invalid without reason
```

If the system cannot trade, show one clear reason first and details second.

## 27. Existing code handling

When applying this guide to an existing repository:

```text
inspect the full repository before large changes
identify actual root launchers
identify any live order path
identify data, log, config, and runtime paths
identify state truth sources
identify strategy-to-exchange direct calls
identify dashboard source paths
identify tests and validators
fix highest-risk violations first
avoid broad rewrites unless necessary to remove safety risk
```

Priority fixes:

```text
live safety
mode separation
single truth source
order idempotency
risk veto
kill switch
ledger integrity
secret leakage
no-trade reason visibility
dashboard truth discipline
```


## 27A. Scenario rulebook

Use these defaults when implementation details are missing.

```text
hard truth missing -> NO_TRADE or SAFE_MODE
strategy conflict -> central arbiter creates one FinalDecision
risk conflict -> risk veto wins
market regime mismatch -> no aggressive entry, show regime mismatch reason
exchange state mismatch -> stop new orders and reconcile
ambiguous order result -> same identifier reconciliation only
dashboard and ledger conflict -> ledger wins, dashboard shows mismatch
disk full or ledger write failure -> block live new orders
private websocket unhealthy -> block live if private stream is required; otherwise use defined reconciliation fallback
futures liquidation risk high -> reduce, close, or block expansion
unknown API rule -> paper/read-only only, live blocked
unknown strategy profitability -> candidate/paper/shadow only
```

## 28. Completion language

Do not claim these unless evidence exists:

```text
profitable
live ready
fully safe
production ready
API verified
```

Allowed claims when true:

```text
implemented scaffold
paper path ready for local test
validator added
live path blocked by design
adapter mock added
preflight blocks unverified live
```

Use precise status words:

```text
READY
BLOCKED
PARTIAL
UNTESTED
NO_TRADE
SAFE_MODE
READ_ONLY
RECONCILE_REQUIRED
REQUIRES_OFFICIAL_API_VERIFICATION
PAPER_ONLY
SHADOW_ONLY
```

Avoid vague status words such as probably, almost, likely ready, or seems fine for live.

## 29. Default behavior when unsure

When unsure, apply this exact behavior:

```text
Do not open new live risk.
Preserve or reduce existing risk.
Reconcile state.
Use paper, shadow, read-only, or safe mode.
Show a one-line reason.
Record the decision.
Add a validator or test if the issue can recur.
```

## 30. One-line operating rule

```text
Implement autonomously, but when uncertain, choose no trade, safe mode, reconciliation, or blocked status over risky progress.
```

## 31. final user flow implementation rule

AI compiler TRADER_1 user following floweuroman operationhal can issge implementation must.

```text
initial preparation: PAPER execution -> dashboard check -> LIVE_READY check
live trading: LIVE execution -> immediate limit live entry or immediate block
operation: user geudae as preserve and required when end
```

user parameter, strategy candidate, evidence, hash, adapter state, risk formula directly must select ha implementation user experience wibanida.

## 32. paper of implementation role

Paper mode is not the final objective. It is an automatic learning, validation, and parameter-adjustment process for creating a live-safe immediate trading path.

implementation rule:

```text
Paper mode does not call the live order API.
Paper mode must apply fees, slippage, depth, spread, and symbol rules as realistically as possible.
Paper and shadow must evaluate candidate parameters and candidate strategies in parallel.
Paper mode may create LIVE_READY snapshot candidates, but it does not create live order permission.
```

## 33. LIVE execution internal parallel engine rule

Even when the user only runs the LIVE launcher, internal live, paper, shadow, replay, and validation functions must remain separated and must be able to operate independently.

```text
live engine -> actual order and position management
paper engine -> live trading and comparison possible internal validation
shadow engine -> candidate strategy and candidate parameter evaluation
replay/validation engine -> deterministic validation and hoegwi validation
```

Internal paper and shadow work must not be directly connected to the live broker. Internal paper and shadow work has lower priority than the live order path.

## 34. snapshot automatic improvement and rollover implementation rule

Live trading must operate on a fixed ACTIVE snapshot. New parameter candidates are explored as candidate snapshots and become approved LIVE_READY snapshots only after validation PASS.

implementation rule:

```text
ACTIVE snapshot none live new entry forbidden
candidate snapshot of live directly apply forbidden
approved snapshotman rollover possible
existing position principlejeog as entry howevergsi snapshot as management
new position current approved snapshot apply possible
aggressive parameter change of live hot swap forbidden
conservative reduction, stop, safe mode transition allowed possible
```

Automatic rollover must be performed only at safe timing, such as when no position exists, before a new entry, or at a decision-cycle boundary.

## 35. immediate live entry implementation rule

Live execution is not a procedure for performing new long-running validation. The live launcher must quickly verify the current valid LIVE_READY snapshot and precomputed readiness state.

goal implementation:

```text
warm start
precomputed readiness state
incremental health update
near-O(1) live_order_ready judgment
long-running validation startup path bagg in performance
```

READYif immediate limit live entry, NOT READYif immediate block and one-line reason display implementation must.

## 36. advancement per level implementation goal

```text
Level 0: execution possible
Level 1: paper dry-run possible
Level 2: operational form paper possible
Level 3: live review possible
Level 4: limit live possible
Level 5: paper none live-safe bootstrap possible
Level 6: production autonomous live possible
```

The AI compiler must state which target level each work item pursues. From Level 5 onward, if a valid snapshot exists, starting LIVE execution alone must allow immediate limited live entry. Level 6 supports long-term operation, automatic replacement, and advanced operation.adong expansion/reduction, multi-exchange production operation must include be done.

## 37. by strategy exit implementation rule

common hard exit all by strategy exittakes priority over.

common hard exit:

```text
bear regime exit
stop loss reached
take profit reached
trailing stop reached
trend structure deteriorated
risk veto exit
emergency flatten
reconciliation mismatch exit
data stale exit
manual emergency exit
```

by strategy exit advice:

```text
open_reset_micro -> momentum weakening, time stop, taker flow weakening, spread expansion
breakout_retest -> breakout level ital, retest failure, follow-through absence
trend_pullback -> EMA structure weakening, VWAP ital, trend breadth weakening, higher low collapse
range_reversion_vwap -> VWAP dodal, range top, midline failure, range structure collapse, thesis timeout
```

Strategy-specific exits must only be proposed to the RiskManager and DecisionArbiter. Common hard exits, risk veto, emergency flatten, and reconciliation mismatch handling cannot be overridden.

## 38. live final guard implementation rule

Before every live order submission, the following items must be verified again.

```text
mode == LIVE
exchange verified
market_type verified
ACTIVE snapshot valid
FinalDecision exists
FinalDecision not stale
risk veto false
hard truth complete
data freshness pass
reconciliation fresh
protection ready
emergency flatten available
watchdog active
idempotency key exists
ledger writer available
```

If any item fails, the order must not be submitted.

## 39. local_state_only protection rule

local_state_only protection in the status live new entry is allowed not.

allowed action:

```text
existing position reduction
existing position exit
open order cancel
reconciliation
safe mode
emergency flatten preparation
```

forbidden action:

```text
new live entry
add position
pyramiding
size expansion
risk profile upgrade
```

## 40. readiness vocabulary implementation rule

The following statuses must be implemented separately.

```text
release_ready
can_start
can_collect_data
can_evaluate_candidates
can_paper_trade
can_shadow_evaluate
can_replay
can_live_review
can_live_trade
live_order_ready
```

release_ready, can_start, and live_review_ready do not have the same meaning as live_order_ready. The dashboard must avoid standalone READY text and must attach scope.

## 41. data freshness and blocker taxonomy implementation rule

stale_market_data single reason as ggeutnaeji malgo by source as must decompose.

mandatory decomposition:

```text
STALE_TICKER
STALE_ORDERBOOK
STALE_TRADE_TAPE
STALE_CANDLE_15M
STALE_CANDLE_60M
STALE_BENCHMARK_CONTEXT
MARKET_CONTEXT_LOAD_TIMEOUT
API_TIMEOUT
WEBSOCKET_GAP
CLOCK_DRIFT
```

Candidate blockers must include one of the categories DATA, LIQUIDITY, REGIME, STRATEGY, RISK, PORTFOLIO, EXECUTION, CONFIG, READINESS, or OPERATOR.

## 42. test and environment implementation rule

The test environment must be fixed to Python 3.12 or later and aiohttp 3.11 or later but below 4.

mandatory test lane:

```text
compileall
unit
contract
config schema
integration
paper dry-run
replay
readiness
live blocked
emergency flatten dry-run
reconciliation
artifact hygiene
```

Live-blocked tests must validate that live order APIs are not called under the following failure conditions.

```text
live_entry_enabled false
LIVE_READY missing/invalid
operator policy fail
local_state_only protection
stale data
risk blocked
reconciliation stale
artifact hygiene fail
shadow/replay incomplete
config invalid
emergency flatten unavailable
symbol rule unknown
final guard disabled
```

## 43. source, release, and evidence bundle implementation rule

Source bundles, release bundles, evidence bundles, and diagnostic bundles must be separated. Source bundles must not include runtime journals, large JSONL files, SQLite files, databases, logs, pyc files, or caches.

Credential scanning and redaction must run automatically before bundle generation.

## 44. code structure advancement implementation rule

Large application-centered structures must be separated gradually. Full rewrites are forbidden; behavior-preserving extraction has priority.

Recommended separation:

```text
runtime/startup
runtime/cycle
runtime/readiness
runtime/data_health
runtime/candidate_pipeline
runtime/decision_pipeline
runtime/order_pipeline
runtime/summary_writer
execution/live_order_gateway
execution/live_reconciliation
execution/live_protection_manager
risk/entry_risk
risk/exit_risk
risk/position_sizing
risk/portfolio_limits
telemetry/contracts/*
```

## 45. user screen implementation rule

The user screen must show the following at a glance.

```text
LIVE TRADING: READY or BLOCKED
PRIMARY BLOCKER
NEXT ACTION
CAPITAL MODE
PROTECTION STATUS
RECONCILIATION AGE
DATA FRESHNESS
ACTIVE SNAPSHOT
current no-entry reason
holding position entry reason
current exit condition
```

If the user must read raw logs to understand status, that is a UX failure.

## 46. strategy execution advancement implementation rule

The AI compiler must not implement strategies as a bundle of fixed numbers. Strategies must be implemented as executable contracts that can be validated.

strategy implementation following item must have must be performed.

```text
strategy_id
strategy_build_id
parameter_hash
entry_plan_type
exit_plan_type
regime_scope
risk_profile
required_hard_truth
optional_soft_truth
entry_maturity_level
exit_maturity_level
edge_model_level
sizing_model_level
validation_state
```

strategy numeric value, threshold, indicator period, band width, stop distance, take profit distance live confirmvalue is not. affected value replay, paper, shadow, live burn-in evidence as validated until candidate parameterroman must treat be performed.

## 47. by strategy entry and exit advancement level implementation rule

Strategy-specific entries and exits must be managed by the following levels.

```text
Strategy Level 0: signal candidates only existence
Strategy Level 1: input data, TTL, reason code existence
Strategy Level 2: regime, liquidity, spread, depth filter existence
Strategy Level 3: cost deducted edge, risk veto, sizing trace existence
Strategy Level 4: replay, paper, shadow evidence existence
Strategy Level 5: LIVE_READY snapshot scope and ilci
Strategy Level 6: live performance-based automatic reduction, degradation, retirement, and candidate re-evaluation are possible.
```

allowed standard:

```text
paper candidate -> Strategy Level 1 anomaly
operational form paper -> Strategy Level 2 anomaly
LIVE_READY candidate -> Strategy Level 4 anomaly
live new entry -> Strategy Level 5 anomaly
production autonomous live -> Strategy Level 6 goal
```

Entry and exit have separate levels. Even if the entry level is high, live new entry is not allowed when the exit level is low.

## 48. regime, edge, and sizing implementation rule

Regime judgment must not be made from a single indicator. Minimum inputs are as follows.

```text
trend
volatility
liquidity
spread
volume
drawdown
market breadth when available
higher timeframe context
data quality
```

The regime judgment result must use one of the following values.

```text
UPTREND
RANGE
DOWNTREND
BREAKDOWN
HIGH_VOLATILITY
LOW_LIQUIDITY
UNCERTAIN
```

When confidence is low, reduce new entries or block them.

edge calculation minimum following structure follows.

```text
net_edge_bps =
expected_move_bps
- expected_fee_bps
- expected_spread_cost_bps
- expected_slippage_bps
- expected_impact_bps
- expected_latency_cost_bps
- expected_funding_cost_bps when applicable
```

Rules:

```text
net_edge_bps <= minimum_required_edge_bps -> NO_TRADE
edge component missing -> NO_TRADE
fee unknown -> NO_TRADE
slippage unknown -> NO_TRADE
impact unknown on thin market -> NO_TRADE
futures funding unknown when material -> NO_TRADE
```

Sizing must be determined as the minimum of the following upper bounds.

```text
approved_notional =
min(
  strategy_risk_budget_notional,
  profile_max_notional,
  symbol_exposure_cap,
  portfolio_exposure_cap,
  liquidity_depth_cap,
  volatility_adjusted_cap,
  stop_distance_risk_cap,
  first_order_cap when applicable,
  live_burn_in_cap when applicable
)
```

If the minimum order condition is not satisfied, no order is submitted. If the stop distance is missing or invalid, new entry is forbidden. Confidence score may reduce size or exclude a candidate, but it cannot compensate for missing hard truth.

## 49. strategy family entry implementation rule

default strategy family is as follows.

```text
open_reset_micro
breakout_retest
trend_pullback
range_reversion_vwap
```

open_reset_micro entry must use only short-term momentum candidates after a reset window or volatility reset.

mandatory condition:

```text
fresh market data
spread pass
depth pass
momentum confirmation
taker flow or equivalent pressure confirmation when available
signal TTL
FOMO distance guard
net edge positive
```

breakout_retest entry must have a breakout, retest, and follow-through structure, not a simple high breakout only.

mandatory condition:

```text
breakout reference level
confirmed breakout or accepted retest
false breakout filter
volume or liquidity confirmation
invalidated level
signal TTL
net edge positive after costs
```

trend_pullback entry must have evidence that the pullback has ended within a detailed or valid trend.

mandatory condition:

```text
trend regime pass
higher timeframe not hostile
pullback reference such as EMA, VWAP, structure level, or equivalent
higher low or structure recovery evidence
spread and depth pass
risk distance known
net edge positive
```

range_reversion_vwap entry range regime or mean reversion regimeeseoman is allowed.

mandatory condition:

```text
range regime pass
trend breakdown absent
distance from VWAP or range boundary measured
reversion trigger
spread and depth pass
thesis timeout defined
net edge positive
```

Strategy-specific entry plans must only be proposed to the Decision Arbiter. They cannot bypass risk veto, hard truth gates, exchange rules, reconciliation, or the live final guard.

## 50. strategy family exit implementation rule

all strategy common hard exit first must apply be done.

common hard exit:

```text
risk veto exit
stop loss reached
take profit reached
trailing stop reached
data stale exit
reconciliation mismatch exit
emergency flatten
manual emergency exit
kill switch exit
```

open_reset_micro exit bbareun failure insig coreida.

Mandatory exit advice:

```text
momentum weakens
taker flow weakens
spread widens
no progress within time window
reset effect expires
```

breakout_retest exit invalidation standard coreida.

Mandatory exit advice:

```text
breakout level lost
retest failed
follow-through absent
breakout candle invalidated
impact or spread worsens after entry
```

The core of trend_pullback exit is trend damage detection.

Mandatory exit advice:

```text
trend structure deteriorates
EMA or VWAP structure fails
higher low breaks
trend breadth weakens
trailing protection tightens on exhaustion
```

range_reversion_vwap exit must distinguish between thesis completion and thesis failure.

Mandatory exit advice:

```text
VWAP reached
range midline reached
range upper boundary reached when applicable
range structure breaks
mean reversion thesis expires
```

Exit reasons must be recorded as closed enum values. An exit record containing only free text is invalid.

## 51. strategy execution validation implementation rule

strategy execution contract at following test is required.

```text
strategy entry maturity level test
strategy exit maturity level test
regime suitability test
edge component completeness test
net edge positive gate test
sizing cap min selection test
stop distance missing no-trade test
FOMO distance guard test
breakout false breakout filter test
range regime only reversion test
trend pullback hostile higher timeframe block test
hard exit priority test
strategy-specific exit advice test
FinalDecision without direct order test
LIVE_READY scope strategy unit test
```

Live blocked tests must verify that the live order adapter is not called under the following conditions.

```text
entry maturity below Level 5
exit maturity below Level 4
edge model incomplete
sizing trace missing
regime confidence too low
strategy unit scope mismatch
ACTIVE snapshot invalid
strategy threshold not validated
```


## 52. strategy operation quality implementation rule

The AI compiler must not implement strategies as simple signal functions. Every strategy must have a strategy unit, failure taxonomy, candidate generation, rolling performance, and validation evidence.

mandatory implementation rule:

```text
strategy failure closed failure type as record
candidate generator limited scopeeseoman candidate generation
parameter candidate range, hypothesis, validation scope holding
strategy Level strategy unit unit as calculated
profitability expression evidence none forbidden
LIVE_READY is scoped to the strategy unit, not to the strategy name.
```

mandatory failure type:

```text
FALSE_BREAKOUT
LATE_ENTRY
MEAN_REVERSION_FAILURE
TREND_EXHAUSTION
SPREAD_EXPANSION
DEPTH_COLLAPSE
REGIME_MISCLASSIFICATION
TIME_STOP_FAILURE
EXIT_TOO_EARLY
EXIT_TOO_LATE
OVERFIT_SIGNAL
COST_MODEL_UNDERSTATED
SLIPPAGE_UNDERSTATED
PAPER_LIVE_DIVERGENCE
SYMBOL_CONCENTRATION
LIQUIDITY_REGIME_MISMATCH
FUNDING_COST_SPIKE
LIQUIDATION_RISK_UNDERMODELED
DATA_QUALITY_FAILURE
ADAPTER_RULE_MISMATCH
RISK_BUDGET_EXCEEDED
PARAMETER_COMPLEXITY_EXCEEDED
INSUFFICIENT_SAMPLE
```

## 53. strategy candidate generation implementation rule

Candidate generation is not unlimited automatic invention. The AI compiler must generate only validatable candidates based on existing strategy families and failure reasons.

allowed scope:

```text
parameter range adjustment
entry filter adjustment
exit filter adjustment
regime scope adjustment
liquidity tier adjustment
spread/depth policy adjustment
time stop adjustment
trailing behavior adjustment
risk profile hahyang or same profile nae adjustment
symbol universe scoring adjustment
```

forbidden scope:

```text
validation none completehi new live strategy generation
cause analysis none same failure candidate repetition generation
risk veto uhoe candidate generation
hard truth requirement relaxation
cost deducted none edge improvement claim
bogjabdo upper bounds none condition jungceob
live among aggressive parameter immediate apply
```

After candidate generation, the default status is CANDIDATE or REPLAY_TESTING. Granting LIVE_READY is forbidden.

## 54. rolling performance implementation rule

The AI compiler must not implement performance evaluation as a single average value. At minimum, the following windows must be implemented.

```text
short_window
medium_window
long_window
regime_window
symbol_window
adapter_window
live_burn_in_window
```

Each window must calculate the following metrics.

```text
net_ev_after_cost
profit_factor
max_drawdown
hit_rate
payoff_ratio
closed_trade_count
fill_quality_score
paper_live_gap
slippage_error
fee_error
latency_error
regime_fit_score
recent_degradation_score
```

The short_window blocks rapid automatic expansion. Failure to meet the long_window requirement is a reason for revalidation, degradation, or retirement.

## 55. strategy replacement during live implementation rule

Strategy replacement is not an existing-position hot swap. It must be a snapshot-unit transition applied from new positions onward.

allowed condition:

```text
standby strategy unit LIVE_READY
risk_profile same or more conservative
exchange and market_type same
regime_scope current market at fit
paper/live gap normal
adapter evidence yuhyo
reconciliation fresh
no aggressive change on an existing position
```

forbidden condition:

```text
holding position stop aggressive as neolbhim
exit standard relaxation without validation
risk profile upgrade
parameter_hash mismatch
snapshot hash mismatch
standby evidence stale
```

Strategy replacement must leave replacement evidence and a rollback snapshot.

## 56. official API freshness implementation rule

live adapter current official API verification report none READY become cannot.

required validation scope:

```text
order endpoint
account endpoint
position endpoint
websocket user stream
rate limit
symbol rule
fee rule
min notional
tick size
step size
permission policy
withdrawal permission policy
futures leverage/margin/funding/liquidation rule
```

verification missing, expired, invalidated in the status following must apply be done.

```text
market data read-only possible
paper possible
shadow possible
live new order BLOCKED
existing position protection reconciliation and risk veto PASS when conditional allowed
```

## 57. validator implementation rule

A validator is not considered implemented merely because its name exists. Every mandatory validator must have an executable module_path, command, input schema, output schema, timeout, and result state.

result status:

```text
PASS
FAIL
BLOCKED
UNTESTED
STALE
SKIPPED_NOT_APPLICABLE
TIMEOUT
```

Rules:

```text
not implemented -> UNTESTED
not run -> UNTESTED
missing artifact -> BLOCKED
timeout -> TIMEOUT, not PASS
stale result -> stage gate use forbidden
negative safety test missing -> live safety PASS forbidden
```

mandatory validator:

```text
schema_validator
state_transition_validator
closed_enum_validator
hard_truth_validator
soft_truth_fallback_validator
path_namespace_validator
dashboard_source_validator
summary_schema_validator
strategy_decision_validator
strategy_failure_taxonomy_validator
candidate_generator_validator
risk_sizing_validator
edge_cost_validator
single_writer_validator
reservation_before_submit_validator
idempotency_validator
ambiguous_transport_reconciliation_validator
ledger_reconciliation_validator
live_ready_snapshot_validator
startup_probe_phase_validator
official_api_verification_validator
adapter_contract_validator
binance_futures_risk_validator
emergency_flatten_validator
read_only_burn_in_validator
orphan_position_validator
bundle_hygiene_validator
secret_scan_validator
stage_gate_validator
numeric_determinism_validator
rolling_performance_window_validator
live_strategy_replacement_validator
```

## 58. contract reduction forbidden implementation rule

AI compiler documentna registry organize when following item reductionhageona if omitted must not.

```text
closed enum list
no-trade reason list
order lifecycle status
engine state status
risk profile list
operator action list
live final guard condition
live order ready condition
per adapter mandatory evidence
validator mandatory list
forbidden implementation rules
blocking defect list
```

cleanup output artifact following coverage check PASS is required.

```text
coverage_index_present
closed_enum_coverage_pass
live_gate_coverage_pass
strategy_contract_coverage_pass
adapter_contract_coverage_pass
validator_contract_coverage_pass
bundle_contract_coverage_pass
operator_ux_coverage_pass
```

coverage check failure when standard documentna implementation gaideu as is promoted not.

## 59. read-only burn-in and protection implementation rule

live before read-only burn-in live_order_ready of required condition.

validation item:

```text
public market data health
private account snapshot health
private websocket or polling fallback health
symbol rule freshness
fee model freshness
rate limit pressure
ledger write dry-run
reconciliation dry-run
resource health
watchdog health
summary/dashboard source health
```

orphan position detection live start and restart in mandatoryda.

```text
orphan open order -> new entry forbidden, reconciliation priority
orphan position -> new entry forbidden, protection or reconcile priority
local position but exchange missing -> ledger review and reconcile priority
position side mismatch -> futures live block
unknown orphan state -> SAFE_MODE or RECONCILE_REQUIRED
```

emergency protection mandatory element:

```text
emergency_flatten_available
manual_exit_all_positions_available
manual_reduce_position_available
cancel_all_open_orders_available
reduce_only_path_available_for_futures
reconciliation_path_available
operator_alert_available
ledger_recording_available
```

If the emergency protection path is missing, live entry is blocked.

```text
active contract pack precedence is mandatory for every patch and implementation decision.
```

---

# hardening appendix A. AI compiler execution compression rule

document status: supplemental implementation guide

 appendix AGENTS.md source text does not replace. appendix AI compiler work sequence, patch result, MVP progress, live block more consistent as perform helping auxiliary jicinot met. TRADER_1.md always top-level authoritywiand, AGENTS.md geu implementation jicinot met.

## A.1 default execution rule

```text
TRADER_1.md and AGENTS.md jeonce active authority set as read.
Apply the TRADER_1.md active contract pack as the highest authority.
 appendix bbareun for execution source text does not replace.
When ambiguous, select the lower MVP.
When ambiguous, select the safer status.
Implementation must proceed from the lowest incomplete MVP.
Readiness claims without evidence are forbidden.
live_order_ready=false and live_order_allowed=false must be preserved as defaults.
```

## A.2 work selection algorithm

The AI compiler must select work using the following sequence.

```text
1. active authority identity check
2. repository root launcher status check
3. live order path existence whether check
4. paper/live/shadow/replay namespace separation check
5. hard truth and execution truth source check
6. registry and schema existence whether check
7. validator and test lane existence whether check
8. select the lowest incomplete MVP
9. safety or live blocking related defect priority modify
10. paper function live block preservationhan only_in_status extension
11. strategy optimization P0 through P2 stabilization dwieman performance
```

## A.3 pre-patch declaration rule

Before every patch, the following must be declared.

```text
target_mvp_level
patch_class
affected_contract_ids
affected_exchange
affected_market_type
affected_mode
expected_live_order_allowed_after
expected_remaining_blockers
```

`expected_live_order_allowed_after=true` is possible only for LIVE_ENABLING_PATCH. For all other patch classes it must be false.

## A.4 implementation result format

All implementation results must be recorded in the following format.

```text
target_mvp_level:
patch_class:
affected_contract_ids:
affected_exchange:
affected_market_type:
affected_mode:
removed_requirements:
merged_requirements:
new_registry_items:
new_or_changed_schema_ids:
validators_required:
validators_run:
tests_added_or_changed:
live_order_allowed_before:
live_order_allowed_after:
remaining_blockers:
coverage_index_result:
evidence_or_audit_record:
next_allowed_stage:
```

gangje rule.

```text
removed_requirements must be []
validator not run means UNTESTED
UNTESTED is not READY
TIMEOUT is not PASS
STALE is not usable for live readiness
PASS_WITH_LIMITATION is not live readiness
```

---

# hardening appendix B. AI implementation checklist by MVP

document status: supplemental MVP worklist

## B.1 MVP common rule

```text
Proceed from the lowest incomplete MVP.
MVP skip forbidden.
MVP completion code existence not evidence existence as must judge.
live_order_allowed MVP-5 or MVP-7 exact scope live gate until falseda.
MVP-0 through MVP-4 live new order is allowed not.
```

## B.2 MVP-0 Contract baseline

priority generation or must align be performed.

```text
contracts/registry.yaml
contracts/schema/readiness_surface.schema.json
contracts/schema/live_ready_snapshot.schema.json
contracts/schema/manual_order_test_evidence.schema.json
contracts/schema/final_decision.schema.json
contracts/schema/ledger_event.schema.json
contracts/schema/summary.schema.json
contracts/schema/evidence_manifest.schema.json
contracts/schema/official_api_verification_report.schema.json
contracts/schema/validator_result.schema.json
contracts/schema/operator_action_audit.schema.json
contracts/schema/release_source_identity.schema.json
contracts/schema/contract_gap.schema.json
contracts/generated/TRADER_1.generated.md
contracts/generated/AGENTS.generated.md
coverage index scaffold
```

required validation.

```text
python -m trader1.validation.schema
python -m trader1.validation.registry
python -m trader1.validation.coverage_index
```

If a validation command is not yet implemented, its status is UNTESTED and READY is forbidden.

## B.3 MVP-1 Safe boot skeleton

Implement first.

```text
UPBIT_PAPER
UPBIT_LIVE
BINANCE_PAPER
BINANCE_LIVE
config validation
namespace manager
startup_probe
heartbeat
summary shell
read-only dashboard shell
live path hard block
kill switch scaffold
resource guard scaffold
```

Mandatory test.

```text
root launcher contract test
paper cannot call live order API test
live blocked when LIVE_READY missing test
summary is dashboard source only test
namespace separation test
```

## B.4 MVP-2 Upbit paper dry-run

Implement first.

```text
Upbit public data path
Upbit paper adapter
paper broker
paper ledger skeleton
no-trade reason logging
entry reason logging
fee and slippage baseline
symbol rule validator scaffold
```

Mandatory test.

```text
paper dry-run test
paper ledger write test
no-trade reason enum test
entry reason schema test
paper/live data separation test
```

## B.5 MVP-3 Operational Upbit paper

Implement first.

```text
ledger
intent WAL
restart recovery
paper/shadow separation
DecisionArbiter
RiskVetoEngine
SizingEngine
cost model
basic strategy fixtures
paper dashboard first view
replay consistency baseline
stage evidence pack
```

Mandatory test.

```text
decision arbiter priority test
risk veto test
single writer test
idempotency test
ledger reconciliation test
paper operation gate test
strategy direct order forbidden test
```

## B.6 MVP-4 Upbit live review

Implement first.

```text
read-only account snapshot
read-only balance snapshot
read-only position snapshot
read-only open order snapshot
private stream or reconciliation path
official API verification report
manual approval surface
live preflight report
live review dashboard
```

Mandatory test.

```text
can_live_review true but live_order_ready false test
preflight blocks live new order test
official API verification missing blocks live test
read-only burn-in does not imply live_order_ready test
```

## B.7 MVP-5 Upbit limited live

LIVE_ENABLING_PATCHroman possible. following evidence all must exist must be performed.

```text
valid LIVE_READY snapshot
official API verification PASS and fresh
manual order test PASS when required
operator approval valid when required
read-only burn-in PASS
emergency protection available
ledger reconciliation PASS
bundle hygiene PASS when release package is used
source identity PASS when release package is used
live blocked negative tests PASS
all blocking validators PASS
no HIGH or CRITICAL contract_gap open
```

If any item is missing, the following must be recorded.

```text
live_order_allowed_after=false
remaining_blockers includes missing evidence
```

## B.8 MVP-6 Multi-exchange paper

Implement first.

```text
Binance spot paper scaffold
Binance futures paper scaffold
futures simulator
exchange namespace split
market_type namespace split
futures liquidation model scaffold
funding model scaffold
cross-exchange dashboard summary
```

Mandatory test.

```text
Binance paper test
spot/futures separation test
futures liquidation risk scaffold test
Binance live remains blocked test
```

## B.9 MVP-7 Binance limited live

LIVE_ENABLING_PATCHroman possible. SPOT and FUTURES_USDT_M separate scopeda.

mandatory condition.

```text
exact Binance exchange scope
exact market_type scope
separate LIVE_READY snapshot
separate official API verification
separate manual order test when required
futures risk validator PASS when FUTURES_USDT_M
reduce-only path available when FUTURES_USDT_M
funding and liquidation model verified when FUTURES_USDT_M
all blocking validators PASS
```

---

# hardening appendix C. strategy implementation standard work rule

document status: supplemental strategy implementation guide

## C.1 strategy is not an order executor

```text
strategy produces signal only
DecisionArbiter produces FinalDecision
RiskVetoEngine can block all strategy proposals
Execution executes FinalDecision only
OrderAdapter is called only after live final guard when mode is LIVE
```

## C.2 StrategyUnit implementation fields

all strategy gaegce or record following unit has.

```text
strategy_id
strategy_build_id
parameter_set
parameter_hash
exchange
market_type
regime_scope
risk_profile
entry_plan_type
exit_plan_type
entry_maturity_level
exit_maturity_level
edge_model_level
sizing_model_level
validation_state
```

## C.3 common entry gate

strategy entry jean minimum following PASS is required.

```text
fresh market data
regime suitability
liquidity pass
spread pass
depth pass
signal TTL
net edge positive after costs
risk distance known
sizing trace present
closed no-trade reason available when rejected
```

## C.4 common hard exit priority

The following priority must be applied before all per-strategy exit guidance.

```text
risk veto exit
stop loss reached
take profit reached
trailing stop reached
data stale exit
reconciliation mismatch exit
emergency flatten
manual emergency exit
kill switch exit
```

## C.5 default strategy family implementation

default strategy family is as follows.

```text
open_reset_micro
breakout_retest
trend_pullback
range_reversion_vwap
```

each strategy following output artifact must have must be performed.

```text
entry contract
exit contract
no-trade reason mapping
failure taxonomy
required hard truth list
optional soft truth fallback list
edge component list
sizing trace
validation tests
LIVE_READY scope test
```

## C.6 strategy live block condition

followingif live order adapter call forbidden.

```text
entry maturity below Level 5
exit maturity below Level 5
edge model incomplete
sizing trace missing
regime confidence too low
strategy unit scope mismatch
ACTIVE snapshot invalid
strategy threshold not validated
parameter_hash mismatch
risk_profile mismatch
strategy_build_id mismatch
replay evidence missing
paper evidence missing
shadow evidence missing
```

---

# hardening appendix D. Coverage and non-deletion execution rule

document status: supplemental coverage enforcement guide

## D.1 non-deletion rule

```text
existing requirements must not be deleted.
MVP deferred removed is not.
scope reduction is forbidden be done.
safety hardening for block or defer is allowed.
removed_requirements always []ieoya must be performed.
```

## D.2 coverage index status

each requirements following among one as must classify be performed.

```text
MAPPED_TO_REGISTRY
MAPPED_TO_SCHEMA
MAPPED_TO_VALIDATOR
MAPPED_TO_TEST
MAPPED_TO_RUNTIME_SCAFFOLD
MAPPED_TO_DASHBOARD
MAPPED_TO_EVIDENCE
DEFERRED_TO_LATER_MVP
BLOCKED_BY_CONTRACT_GAP
UNMAPPED
```

## D.3 coverage check mandatory item

```text
coverage_index_present
closed_enum_coverage_pass
no_trade_reason_coverage_pass
live_gate_coverage_pass
strategy_contract_coverage_pass
adapter_contract_coverage_pass
validator_contract_coverage_pass
bundle_contract_coverage_pass
operator_ux_coverage_pass
security_contract_coverage_pass
evidence_contract_coverage_pass
MVP_boundary_coverage_pass
```

## D.4 UNMAPPED handling

```text
UNMAPPED if exists complete claim forbidden
UNMAPPED live safety at impact if exists live_order_ready=false
UNMAPPED runtime safety at impact if exists affected path BLOCKED
UNMAPPED items are not deleted and remain in the coverage index.
```

---

# hardening appendix E. direct execution instruction that can be given to the AI

document status: reusable implementation prompt

following instruction AI compilerege geudae as jegonghal can exist.

```text
TRADER_1.md and AGENTS.md jeonce active authority set as ilgeora.
TRADER_1.md top-level design authority as sado not.
AGENTS.md implementation jicimeuroman must use do.
 hardening appendix bbareun for interpretation source text does not replace.
conflict when TRADER_1.md of more safety and more gucejeogin rule follows.
Do not delete or weaken existing requirements.
Always implement from the lowest incomplete MVP.
first work contracts/registry.yaml, contracts/schema, validator scaffold, coverage index align geosida.
live_order_ready=false and live_order_allowed=false default value as must preserve do.
Do not allow live new orders from MVP-0 through MVP-4.
validator not run UNTESTED as must record do.
Do not treat UNTESTED, STALE, or TIMEOUT as READY.
A strategy must not place orders; it only proposes signals.
all order FinalDecision, risk veto, single writer, idempotency, ledger, reconciliation PASShage must do.
if ambiguous NO_TRADE, SAFE_MODE, READ_ONLY, RECONCILE_REQUIRED, BLOCKED among one as must handle do.
all patch result at target_mvp_level, patch_class, validators_run, remaining_blockers, live_order_allowed_after must record do.
removed_requirements always []ieoya must be performed.
```

---
# hardening appendix F. AI implementation start observe form

document status: supplemental implementation report template

 This appendix is an observation form for fixing current status before the AI compiler modifies code. It does not replace the authority of TRADER_1.md.

## F.1 writing time

```text
repository ceoeum modify before
large patch starthagi before
target_mvp_level baggwigi before
live path or order path geondeurigi before
```

## F.2 AI_IMPLEMENTATION_START_REPORT

```json
{
  "report_schema_id": "trader1.ai_implementation_start_report.v1",
  "created_at_utc": "string",
  "active_authority_files": ["TRADER_1.md", "AGENTS.md"],
  "target_mvp_level": "MVP-0 Contract baseline",
  "current_repo_state": "UNKNOWN|EMPTY|PARTIAL|EXISTING_REPO|BLOCKED",
  "root_launchers_found": [],
  "unexpected_root_launchers_found": [],
  "live_order_path_found": false,
  "direct_strategy_to_exchange_call_found": false,
  "paper_live_namespace_status": "UNKNOWN|PASS|FAIL|BLOCKED|UNTESTED",
  "registry_status": "MISSING|PARTIAL|PRESENT|VALIDATED|BLOCKED",
  "schema_status": "MISSING|PARTIAL|PRESENT|VALIDATED|BLOCKED",
  "validator_status": "MISSING|PARTIAL|PRESENT|VALIDATED|BLOCKED",
  "test_status": "MISSING|PARTIAL|PRESENT|PASS|FAIL|UNTESTED",
  "highest_risk_gap": "string|null",
  "first_patch_class": "DOC_CONTRACT_PATCH|REGISTRY_PATCH|SCHEMA_PATCH|VALIDATOR_PATCH|RUNTIME_SAFETY_PATCH|PAPER_FUNCTIONAL_PATCH|LIVE_BLOCKING_PATCH|LIVE_ENABLING_PATCH|BUNDLE_HYGIENE_PATCH|DASHBOARD_UX_PATCH",
  "first_patch_scope": "string",
  "live_order_ready_before": false,
  "live_order_allowed_before": false,
  "expected_live_order_allowed_after": false,
  "remaining_initial_blockers": []
}
```

## F.3 start observe rule

```text
Do not start live-related implementation until root launchers and the live order path have been verified.
If the registry is missing, handle it from the MVP-0 registry.
If schemas are missing, handle them from MVP-0 schemas.
If validators are missing, create the validator scaffold first.
live_order_allowed_before and expected_live_order_allowed_after default falseda.
```

---
# hardening appendix G. Patch Result JSON standard

document status: supplemental patch result template

## G.1 PATCH_RESULT_TEMPLATE

```json
{
  "patch_result_schema_id": "trader1.patch_result.v1",
  "created_at_utc": "string",
  "target_mvp_level": "MVP-0 Contract baseline",
  "patch_class": "SCHEMA_PATCH",
  "patch_summary": "string",
  "affected_contract_ids": [],
  "affected_files": [],
  "affected_exchange": null,
  "affected_market_type": null,
  "affected_mode": null,
  "removed_requirements": [],
  "merged_requirements": [],
  "deferred_requirements": [],
  "new_registry_items": [],
  "new_or_changed_schema_ids": [],
  "validators_required": [],
  "validators_run": [
    {
      "command": "string",
      "status": "PASS|FAIL|BLOCKED|UNTESTED|STALE|SKIPPED_NOT_APPLICABLE|TIMEOUT",
      "evidence_path": "string|null"
    }
  ],
  "tests_added_or_changed": [],
  "tests_run": [
    {
      "command": "string",
      "status": "PASS|FAIL|BLOCKED|UNTESTED|STALE|SKIPPED_NOT_APPLICABLE|TIMEOUT",
      "evidence_path": "string|null"
    }
  ],
  "live_order_ready_before": false,
  "live_order_ready_after": false,
  "live_order_allowed_before": false,
  "live_order_allowed_after": false,
  "remaining_blockers": [],
  "new_contract_gaps": [],
  "coverage_index_result": "PASS|FAIL|BLOCKED|UNTESTED|STALE|TIMEOUT",
  "evidence_manifest_path": "string|null",
  "operator_visible_status": "string",
  "next_allowed_stage": "string|null"
}
```

## G.2 mandatory rule

```text
removed_requirements always []is.
validators_run actual execution command and status record.
If test execution has not been performed, record the status as UNTESTED.
UNTESTED, STALE, TIMEOUT READY is not.
live_order_allowed_after=true LIVE_ENABLING_PATCH oe at forbiddenda.
Even for LIVE_ENABLING_PATCH, if any evidence item is missing, live_order_allowed_after=false.
```

---
# hardening appendix H. actual output file checklist by MVP

document status: supplemental file output checklist

 This appendix is the minimum list of files that the AI compiler must generate or check in each MVP. If the existing repository structure differs, map to a module with the same responsibility and record the mapping in the patch result.

## H.1 MVP-0 required files

```text
contracts/registry.yaml
contracts/schema/readiness_surface.schema.json
contracts/schema/live_ready_snapshot.schema.json
contracts/schema/manual_order_test_evidence.schema.json
contracts/schema/final_decision.schema.json
contracts/schema/ledger_event.schema.json
contracts/schema/summary.schema.json
contracts/schema/evidence_manifest.schema.json
contracts/schema/official_api_verification_report.schema.json
contracts/schema/validator_result.schema.json
contracts/schema/operator_action_audit.schema.json
contracts/schema/release_source_identity.schema.json
contracts/schema/contract_gap.schema.json
contracts/generated/TRADER_1.generated.md
contracts/generated/AGENTS.generated.md
src/trader1/validation/schema.py
src/trader1/validation/registry.py
src/trader1/validation/coverage_index.py
tests/contract/test_schema_contracts.py
tests/contract/test_registry_contracts.py
tests/contract/test_coverage_index.py
```

## H.2 MVP-1 required files

```text
UPBIT_PAPER
UPBIT_LIVE
BINANCE_PAPER
BINANCE_LIVE
src/trader1/runtime/boot/startup_probe.py
src/trader1/runtime/boot/launcher_guard.py
src/trader1/runtime/health/heartbeat.py
src/trader1/runtime/readiness/readiness_surface.py
src/trader1/config/config_schema.py
src/trader1/core/registry/loader.py
src/trader1/core/state/engine_state.py
src/trader1/core/state/mode_namespace.py
src/trader1/dashboard/summary_writer.py
tests/live_blocked/test_live_order_blocked_without_ready.py
tests/contract/test_root_launchers.py
tests/contract/test_mode_namespace.py
```

## H.3 MVP-2 required files

```text
src/trader1/adapters/upbit/market_data.py
src/trader1/adapters/upbit/symbol_rules.py
src/trader1/adapters/upbit/fee_model.py
src/trader1/adapters/upbit/paper_broker.py
src/trader1/core/decision/final_decision.py
src/trader1/core/decision/decision_arbiter.py
src/trader1/core/risk/risk_veto.py
src/trader1/core/ledger/ledger_event.py
src/trader1/core/ledger/paper_ledger.py
src/trader1/core/events/intent_wal.py
src/trader1/reports/no_trade_reason.py
tests/adapter/test_upbit_paper_adapter.py
tests/contract/test_final_decision_schema.py
tests/contract/test_no_trade_reason_enum.py
tests/paper/test_upbit_paper_dry_run.py
```

## H.4 MVP-3 required files

```text
src/trader1/core/ledger/reconciliation.py
src/trader1/core/ledger/restart_recovery.py
src/trader1/core/sizing/position_sizing.py
src/trader1/core/strategy/strategy_unit.py
src/trader1/core/strategy/strategy_level.py
src/trader1/runtime/reconciliation/paper_reconciliation.py
src/trader1/dashboard/panels/status_panel.py
src/trader1/dashboard/panels/portfolio_panel.py
src/trader1/dashboard/panels/no_trade_panel.py
src/trader1/research/replay/replay_runner.py
src/trader1/research/shadow/shadow_runner.py
tests/replay/test_replay_determinism.py
tests/contract/test_strategy_unit_scope.py
tests/contract/test_paper_shadow_separation.py
tests/integration/test_upbit_operational_paper_cycle.py
```

## H.5 MVP-4 required files

```text
src/trader1/adapters/upbit/account_readonly.py
src/trader1/adapters/upbit/private_stream.py
src/trader1/adapters/upbit/reconciliation.py
src/trader1/runtime/readiness/live_preflight.py
src/trader1/runtime/readiness/official_api_verification.py
src/trader1/runtime/readiness/live_ready_snapshot_validator.py
src/trader1/runtime/readiness/manual_order_test_evidence.py
src/trader1/security/api_key_permission_check.py
tests/readiness/test_upbit_live_review_preflight.py
tests/live_blocked/test_upbit_live_review_no_new_order.py
tests/contract/test_official_api_verification_report.py
```

## H.6 MVP-5 required files

```text
src/trader1/execution/live_order_gateway.py
src/trader1/execution/live_final_guard.py
src/trader1/execution/idempotency.py
src/trader1/execution/reservation.py
src/trader1/runtime/protection/emergency_flatten.py
src/trader1/runtime/protection/kill_switch.py
src/trader1/runtime/reconciliation/live_reconciliation.py
src/trader1/runtime/readiness/read_only_burn_in.py
src/trader1/evidence/evidence_manifest.py
tests/live_blocked/test_live_final_guard_blocks_invalid.py
tests/integration/test_upbit_limited_live_guarded_path.py
tests/reconciliation/test_same_identifier_reconciliation.py
tests/emergency/test_emergency_flatten_dry_run.py
```

## H.7 MVP-6 required files

```text
src/trader1/adapters/binance_spot/market_data.py
src/trader1/adapters/binance_spot/symbol_rules.py
src/trader1/adapters/binance_spot/paper_broker.py
src/trader1/adapters/binance_futures/market_data.py
src/trader1/adapters/binance_futures/symbol_rules.py
src/trader1/adapters/binance_futures/futures_risk_model.py
src/trader1/adapters/binance_futures/paper_broker.py
tests/adapter/test_binance_spot_paper_adapter.py
tests/adapter/test_binance_futures_paper_adapter.py
tests/contract/test_cross_exchange_namespace_separation.py
```

## H.8 MVP-7 required files

```text
src/trader1/adapters/binance_spot/account_readonly.py
src/trader1/adapters/binance_spot/order_adapter.py
src/trader1/adapters/binance_futures/account_readonly.py
src/trader1/adapters/binance_futures/order_adapter.py
src/trader1/adapters/binance_futures/liquidation_risk.py
src/trader1/adapters/binance_futures/reduce_only.py
src/trader1/adapters/binance_futures/funding_model.py
tests/live_blocked/test_binance_live_blocked_without_exact_scope.py
tests/adapter/test_binance_futures_liquidation_risk.py
tests/integration/test_binance_limited_live_guarded_path.py
```

## H.9 file checklist rule

```text
This is a recommended file name.
If the existing structure differs, it must be mapped to a module with the same responsibility.
Mapped cases must be recorded in the patch result.
Responsibilities that could not be created or mapped remain in the coverage index as UNMAPPED or BLOCKED_BY_CONTRACT_GAP.
```

---
# hardening appendix I. Live blocked negative test matrix

document status: supplemental live safety test matrix

## I.1 Matrix schema

```json
{
  "case_id": "string",
  "condition": "string",
  "mode": "LIVE",
  "exchange": "UPBIT|BINANCE|null",
  "market_type": "KRW_SPOT|SPOT|FUTURES_USDT_M|null",
  "expected_engine_state": "BLOCKED|SAFE_MODE|TRADE_DISABLED|RECONCILE_REQUIRED|KILL_SWITCH_TRIGGERED",
  "expected_final_decision": "BLOCKED|NO_TRADE|SAFE_MODE|RECONCILE_REQUIRED|TRADE_DISABLED|KILL_SWITCH",
  "expected_order_adapter_called": false,
  "expected_blocker_code": "string",
  "required_evidence": "validator_result|test_result|evidence_manifest|contract_gap"
}
```

## I.2 Required cases

```text
LIVE_BLOCKED_001 | LIVE_READY missing | BLOCKED | BLOCKED | false | LIVE_READY_MISSING
LIVE_BLOCKED_002 | LIVE_READY invalid | BLOCKED | BLOCKED | false | LIVE_READY_MISSING
LIVE_BLOCKED_003 | official API verification missing | BLOCKED | BLOCKED | false | API_UNVERIFIED
LIVE_BLOCKED_004 | official API verification stale | BLOCKED | BLOCKED | false | OFFICIAL_API_VERIFICATION_EXPIRED
LIVE_BLOCKED_005 | manual order test missing when required | BLOCKED | BLOCKED | false | MANUAL_ORDER_TEST_MISSING
LIVE_BLOCKED_006 | operator approval missing when required | BLOCKED | BLOCKED | false | OPERATOR_APPROVAL_MISSING
LIVE_BLOCKED_007 | local_state_only protection active | BLOCKED | BLOCKED | false | LIVE_FINAL_GUARD_FAILED
LIVE_BLOCKED_008 | stale orderbook | BLOCKED | NO_TRADE | false | STALE_ORDERBOOK
LIVE_BLOCKED_009 | stale ticker | BLOCKED | NO_TRADE | false | STALE_TICKER
LIVE_BLOCKED_010 | stale trade tape | BLOCKED | NO_TRADE | false | STALE_TRADE_TAPE
LIVE_BLOCKED_011 | reconciliation stale | RECONCILE_REQUIRED | RECONCILE_REQUIRED | false | RECONCILIATION_REQUIRED
LIVE_BLOCKED_012 | symbol rule unknown | BLOCKED | BLOCKED | false | SYMBOL_RULE_UNVERIFIED
LIVE_BLOCKED_013 | fee model unknown | BLOCKED | NO_TRADE | false | FEE_MODEL_UNVERIFIED
LIVE_BLOCKED_014 | slippage unknown | BLOCKED | NO_TRADE | false | EXPECTED_SLIPPAGE_EXCEEDED
LIVE_BLOCKED_015 | risk veto active | BLOCKED | NO_TRADE | false | RISK_VETO
LIVE_BLOCKED_016 | kill switch active | KILL_SWITCH_TRIGGERED | KILL_SWITCH | false | KILL_SWITCH_ACTIVE
LIVE_BLOCKED_017 | ledger writer unavailable | BLOCKED | BLOCKED | false | LEDGER_UNAVAILABLE
LIVE_BLOCKED_018 | idempotency key missing | BLOCKED | BLOCKED | false | LIVE_FINAL_GUARD_FAILED
LIVE_BLOCKED_019 | emergency flatten unavailable | BLOCKED | BLOCKED | false | EMERGENCY_FLATTEN_UNAVAILABLE
LIVE_BLOCKED_020 | source identity mismatch | BLOCKED | BLOCKED | false | SOURCE_IDENTITY_MISMATCH
LIVE_BLOCKED_021 | bundle hygiene fail | BLOCKED | BLOCKED | false | BUNDLE_HYGIENE_FAIL
LIVE_BLOCKED_022 | HIGH contract gap open | BLOCKED | BLOCKED | false | CONTRACT_GAP_HIGH
LIVE_BLOCKED_023 | CRITICAL contract gap open | BLOCKED | BLOCKED | false | CONTRACT_GAP_CRITICAL
LIVE_BLOCKED_024 | entry maturity below Level 5 | BLOCKED | BLOCKED | false | STRATEGY_NOT_ELIGIBLE
LIVE_BLOCKED_025 | exit maturity below Level 5 | BLOCKED | BLOCKED | false | STRATEGY_NOT_ELIGIBLE
LIVE_BLOCKED_026 | edge model incomplete | BLOCKED | NO_TRADE | false | MIN_EDGE_FAIL
LIVE_BLOCKED_027 | sizing trace missing | BLOCKED | NO_TRADE | false | HARD_TRUTH_MISSING
LIVE_BLOCKED_028 | ACTIVE snapshot invalid | BLOCKED | BLOCKED | false | SNAPSHOT_SCOPE_MISMATCH
LIVE_BLOCKED_029 | final guard disabled | BLOCKED | BLOCKED | false | LIVE_FINAL_GUARD_FAILED
LIVE_BLOCKED_030 | paper launcher attempts live order API | BLOCKED | BLOCKED | false | TRADE_DISABLED
```

## I.3 Pass rule

```text
In all cases, the order adapter call must be false.
If any live order adapter is called, live safety is FAIL.
If the live blocked negative test is missing, live safety PASS is forbidden.
```

---
# hardening appendix J. user-facing text standard

document status: supplemental operator UX text map

## J.1 display rule

```text
The first line must include mode, trading status, and the primary blocker.
Standalone READY display is forbidden.
release_ready or bundle_ready live_order_readyceoreom display not.
If the user must read raw logs to understand status, that is a UX failure.
```

## J.2 Status text map

```text
LIVE_READY_MISSING -> LIVE TRADING: BLOCKED - LIVE_READY snapshot missing
SNAPSHOT_SCOPE_MISMATCH -> LIVE TRADING: BLOCKED - LIVE_READY scope mismatch
API_UNVERIFIED -> LIVE TRADING: BLOCKED - exchange official API validation required
OFFICIAL_API_VERIFICATION_EXPIRED -> LIVE TRADING: BLOCKED - exchange official API validation expiry
MANUAL_ORDER_TEST_MISSING -> LIVE TRADING: BLOCKED - manual order test evidence required
OPERATOR_APPROVAL_MISSING -> LIVE TRADING: BLOCKED - operator approval required
READ_ONLY_BURN_IN_MISSING -> LIVE TRADING: BLOCKED - read-only burn-in evidence required
EMERGENCY_FLATTEN_UNAVAILABLE -> LIVE TRADING: BLOCKED - emergency flatten preparation required
RECONCILIATION_REQUIRED -> LIVE TRADING: BLOCKED - account and internal status synchronization required
BALANCE_MISMATCH -> LIVE TRADING: BLOCKED - balance mismatch check required
SYMBOL_RULE_UNVERIFIED -> LIVE TRADING: BLOCKED - symbol rule validation required
FEE_MODEL_UNVERIFIED -> LIVE TRADING: BLOCKED - fee model validation required
STALE_ORDERBOOK -> LIVE TRADING: BLOCKED - orderbook data delay
STALE_TICKER -> LIVE TRADING: BLOCKED - ticker data delay
STALE_TRADE_TAPE -> LIVE TRADING: BLOCKED - trade tape data delay
RISK_VETO -> LIVE TRADING: BLOCKED - risk veto active
KILL_SWITCH_ACTIVE -> LIVE TRADING: BLOCKED - kill switch active
LEDGER_UNAVAILABLE -> LIVE TRADING: BLOCKED - ledger record not allowed
SOURCE_IDENTITY_MISMATCH -> LIVE TRADING: BLOCKED - source identity mismatch
BUNDLE_HYGIENE_FAIL -> LIVE TRADING: BLOCKED - bundle hygiene fail
CONTRACT_GAP_HIGH -> LIVE TRADING: BLOCKED - HIGH contract gap open
CONTRACT_GAP_CRITICAL -> LIVE TRADING: BLOCKED - CRITICAL contract gap open
PAPER_READY -> PAPER TRADING: READY - live order not allowed
READ_ONLY_READY -> READ ONLY: READY - data sujibman possible
LIVE_REVIEW_READY -> LIVE TRADING: REVIEW ONLY - live order not allowed
SMALL_LIVE_BURN_IN_READY -> LIVE TRADING: SMALL BURN-IN - exact scope limit live
LIVE_ACTIVE_READY -> LIVE TRADING: ACTIVE - exact scope live active
```

## J.3 forbidden wording

```text
READY
LIVE READY
geo of ready
no issue
ama possible
startup failed
internal error
unknown problem
release ready therefore live ready
```

## J.4 source discipline

```text
user-facing text dashboard serving truthda.
user-facing text trading truth is not.
Trading decisions must be determined by the ledger, reconciliation, FinalDecision, and live final guard.
If dashboard and engine status differ, engine truth takes priority and the dashboard must display a mismatch warning.
```
````````````````


---
# normalization validation result

```yaml
source_file: AGENTS(86).md
output_file: AGENTS.md
document_kind: active implementation guide
file_split: false
removed_requirements: []
detail_reduction_allowed: false
semantic_reduction_allowed: false
original_requirement_preservation_mode: additive_patch_with_stricter_active_replacements
original_line_subsequence_preserved: not_required_because_active_hardening_and_metadata_update_are_additive
input_line_count: 8204
input_sha256: 950cba698e0e40cceab77e15127f82b55c58aff88b8b9d38e29983adf1027c7e
active_payload_line_count_before_final_note: 3057
active_payload_sha256_before_final_note: 6beaaa6133e3ae9edf28b2abaac967fa1582c7176dc55b2da66428a37bce6009
retained_archive_line_count_before_final_note: 5199
retained_archive_sha256_before_final_note: 70ee293ae5b9b8b4dcc7a3ba7ba1072d7ad6af9f77bc49e2bb7ac3a4ab3400d8
output_sha256_policy: calculate_after_write_do_not_embed_self_hash
authority_sha256_recording_policy: final_TRADER_1_sha256_recorded_in_paired_AGENTS_or_external_manifest
patch_payload_source: user_request_2026-04-27_current_file_hardening
patch_class: DOCUMENT_NORMALIZATION_PATCH
registry_yaml_parse_fix_applied: true
authority_sha256_null_replaced: true
registry-defined-required_placeholders_replaced: true
retained_archive_semantic_handling_added: true
live_order_ready_after: false
live_order_allowed_after: false
```


# RETAINED_ARCHIVE_END


# BASELINE_AGENTS_CONTENT_VERBATIM_END
