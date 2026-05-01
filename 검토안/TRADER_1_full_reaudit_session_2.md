# TRADER_1.zip Full Re-Audit — Session 2

검토 대상: `/mnt/data/TRADER_1.zip` 추출본 `/mnt/data/trader1_src`

검토 일자: 2026-05-01

세션 2 범위:

- 세션 1에서 확인한 런처 import 불능 상태 이후의 실제 패키지 구성 재검증
- authority manifest, source bundle manifest, validator registry, fixture catalog, schema bundle, generated/current implementation state 검토
- 사용자 요구 20개 영역 전체에 대해 문서/스키마/산출물/실행 가능성 관점의 2차 판정
- pytest 실행 가능성 및 테스트 산출물 존재 여부 확인

누적 검토 상태:

- 세션 1 결론 유지: 현재 패키지는 루트 실행기가 `trader1.runtime.boot.safe_launcher`를 import하지만 `trader1/` 소스 트리가 없어서 PAPER/LIVE 실행이 불가능하다.
- 세션 2 추가 결론: 패키지 내부 manifest와 실제 파일 트리가 심각하게 불일치한다. `TRADER_1.md`가 manifest에는 authoritative로 선언되어 있으나 추출본에는 존재하지 않는다. validator registry는 101개 validator가 구현되었다고 선언하지만 해당 모듈 `trader1.validation.mvp0_validators`가 존재하지 않는다. fixture catalog는 91개 fixture를 참조하지만 실제 fixture 파일은 0개다. source bundle manifest는 776개 파일을 선언하지만 665개가 누락되고 45개는 SHA256이 불일치한다. `pytest`는 테스트 파일이 없어 exit code 5로 종료한다.

---

## 0. 세션 2 직접 확인 증거

### 0.1 실제 파일 구조

실제 추출본의 최상위 실행 관련 Python 파일은 다음 2개뿐이다.

- `BINANCE_PAPER.py`
- `BINANCE_LIVE.py`

두 파일 모두 아래 import에 의존한다.

```python
from trader1.runtime.boot.safe_launcher import launcher_main
```

그러나 추출본에는 `trader1/` 패키지 디렉터리가 없다. 따라서 루트 실행기는 실행 즉시 import 단계에서 실패한다.

### 0.2 authoritative 파일 누락

`contracts/authority_manifest.json`에는 다음이 선언되어 있다.

- `trader1_md_path`: `TRADER_1.md`
- `trader1_md_sha256`: `FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B`
- `agents_md_path`: `AGENTS.md`

실제 추출본에는 `AGENTS.md`는 존재하지만 `TRADER_1.md`는 존재하지 않는다. 즉 active authority set이 닫혀 있지 않다.

### 0.3 validator 구현 선언과 실제 소스 불일치

`contracts/validators/validator_registry.json` 확인 결과:

- declared implemented validators: 101개
- status 분포:
  - `IMPLEMENTED_FAIL_CLOSED`: 78개
  - `IMPLEMENTED`: 21개
  - `IMPLEMENTED_NEGATIVE_GUARD`: 1개
  - `IMPLEMENTED_AUDIT_PRESERVING`: 1개
- 모든 validator의 module path: `trader1.validation.mvp0_validators`
- 실제 해당 파일: 없음

따라서 validator registry는 현재 실행 가능한 구현 증거가 아니다.

### 0.4 fixture catalog 전량 누락

`contracts/validators/fixture_catalog.json` 확인 결과:

- declared fixtures: 91개
- 실제 존재 fixture: 0개
- 누락 fixture: 91개

대표 누락 예:

- `tests/validators/fixtures/candidate_cooldown_blocked_pass.json`
- `tests/validators/fixtures/convergence_assessment_pass.json`
- `tests/validators/fixtures/exploration_exploitation_policy_pass.json`

### 0.5 source bundle manifest 불일치

`contracts/security/source_bundle_manifest.json` 확인 결과:

- declared included files: 776개
- missing files: 665개
- hash mismatch files: 45개

대표 누락:

- `tests/__init__.py`
- `tests/adapter/test_binance_adapter_surface.py`
- `tests/contract/test_root_launchers.py`
- `tests/contract/test_schema_instance_validation.py`
- `tests/dashboard/test_read_only_dashboard.py`

대표 SHA mismatch:

- `BINANCE_LIVE.py`
- `BINANCE_PAPER.py`
- `contracts/authority_manifest.json`
- `contracts/registry.yaml`
- `contracts/schema/candidate_scorecard.schema.json`
- `contracts/schema/common.defs.schema.json`

### 0.6 pytest 실행 결과

명령:

```bash
cd /mnt/data/trader1_src && python -m pytest -q
```

결과:

- 테스트 파일을 찾지 못함
- pytest warning: `No files were found in testpaths`
- exit code: 5

따라서 현재 패키지는 테스트 통과 상태가 아니라 테스트 부재 상태다.

### 0.7 schema bundle의 성격

JSON 파일 자체는 모두 parse 가능했다. 그러나 다수 스키마는 “실행 구현”이 아니라 “보고서/증거 산출물의 형태”만 정의한다. 예컨대 `candidate_scorecard.schema.json`, `overfit_diagnostic_report.schema.json`, `market_regime_adaptation_report.schema.json`에는 threshold/status 필드가 있으나, 이를 실제 시장 데이터에서 산출하고 validator로 검증하는 실행 코드와 fixture가 없다.

---

## 1. strategy / regime / entry / exit

- 현재 상태
  - `strategy_unit.schema.json`, `strategy_condition_matrix.schema.json`, `market_regime_adaptation_report.schema.json`, `symbol_strategy_regime_fit_report.schema.json` 등 전략 관련 schema는 존재한다.
  - 전략 조건 행, regime scope, signal intent, strategy confidence, regime confidence 같은 필드는 정의되어 있다.
  - 그러나 실제 entry/exit 엔진, 전략 계산 코드, feature 계산 코드, regime classifier 구현, position transition 구현은 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - 사용자가 요구한 구조는 하락장 회피, 횡보장 VWAP, 상승장 눌림목/돌파 전략의 실제 실행 가능성이다.
  - 현재 패키지는 strategy candidate와 condition matrix의 보고서 스키마만 있고, 실제 candle/orderbook/trade 데이터를 입력받아 entry/exit 신호를 만들 구현이 없다.
  - `strategy_condition_matrix.schema.json`도 `live_order_ready=false`, `live_order_allowed=false`, `can_live_trade=false`를 const로 고정한다. 이는 live safety에는 유리하지만 전략 승격 경로의 실제 구현이 닫혀 있지 않다는 뜻이다.

- 실제 운영 시 어떤 위험이 생기는지
  - PAPER를 실행해도 전략 신호가 생성되지 않는다.
  - dashboard에 표시되는 strategy 상태가 실제 매매 판단과 연결되지 않는다.
  - AI compiler가 schema 필드만 보고 임의의 전략 로직을 추측 구현할 위험이 크다.

- 필요한 수정 방향
  - strategy engine을 실제 패키지에 추가해야 한다.
  - 최소 단위는 `trader1/strategy/` namespace 안에 regime classifier, entry evaluator, exit evaluator, no-trade reason generator, signal grading interface를 분리 구현하는 것이다.
  - entry/exit 조건은 수식, threshold, 데이터 freshness 조건, 비용 차감 후 net EV 조건까지 닫혀야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/strategy/regime.py` 구현: trend/range/downtrend/quiet/squeeze 등 regime 산출.
  - `trader1/strategy/entry.py` 구현: VWAP mean reversion, pullback trend-following, breakout 조건 구현.
  - `trader1/strategy/exit.py` 구현: stop, take-profit, trailing, time stop, regime invalidation exit 구현.
  - `trader1/strategy/no_trade.py` 구현: schema의 no_trade_reason enum과 실제 blocker 매핑.
  - `tests/strategy/fixtures/`에 candle/orderbook/trade fixture 추가.

- 검증 방법 또는 acceptance 조건
  - fixture 기반으로 각 regime별 entry/exit expected output이 deterministic해야 한다.
  - downtrend regime에서는 long entry가 fail-closed로 차단되어야 한다.
  - range regime에서는 VWAP 조건이 비용 차감 후 net EV 양수일 때만 candidate를 생성해야 한다.
  - trend regime에서는 pullback/breakout 조건이 threshold, risk, freshness, cost model을 모두 통과해야 한다.

---

## 2. expected edge / fee / slippage / funding

- 현재 상태
  - `candidate_scorecard.schema.json`에는 `gross_expected_edge_bps`, `expected_fee_bps`, `expected_spread_bps`, `expected_slippage_bps`, `expected_impact_bps`, `expected_latency_penalty_bps`, `net_ev_after_cost_bps`, `min_required_edge_bps`가 required다.
  - `execution_quality_measurement_report.schema.json`도 존재한다.
  - 하지만 실제 fee table, exchange별 tick/lot/min notional, Upbit KRW fee, Binance spot/futures fee, funding 계산, slippage estimator 구현은 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - 대수의 법칙 기반 기대값 수렴은 거래 1건당 net EV가 일관되게 양수라는 전제가 있어야 한다.
  - schema는 비용 항목명을 요구하지만 비용 산출 수식과 공식 API/수수료 검증 구현이 없다.
  - Binance futures의 funding은 spot/Upbit에는 없는 비용/수익 항목인데, 현재 cost model에서 market_type별 적용 규칙이 닫혀 있지 않다.

- 실제 운영 시 어떤 위험이 생기는지
  - gross edge는 양수지만 비용 차감 후 음수인 거래가 PAPER에서 우수 후보로 보일 수 있다.
  - Binance futures에서 funding을 누락하면 보유 시간이 긴 전략의 기대값이 과대평가된다.
  - Upbit KRW 현금흐름 목표에서 수수료/슬리피지/호가단위 반영 실패로 실제 출금 가능 수익이 왜곡된다.

- 필요한 수정 방향
  - exchange/market_type별 cost model을 hard-coded 임시값이 아니라 공식 API/설정/검증 산출물로 닫아야 한다.
  - net EV 산식과 최소 edge threshold를 validator가 검증해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/cost/fee_model.py` 구현.
  - `trader1/cost/slippage.py` 구현: spread, depth, impact, partial fill risk, latency penalty.
  - `trader1/cost/funding.py` 구현: Binance USDⓈ-M futures only.
  - `official_api_verification_report`를 실제 exchange metadata snapshot과 연결.
  - candidate scorecard validator가 `net_ev_after_cost_bps = gross - fee - spread - slippage - impact - latency - funding_adjustment`를 허용 오차 내 검증.

- 검증 방법 또는 acceptance 조건
  - Upbit spot, Binance spot, Binance futures 각각의 비용 fixture가 있어야 한다.
  - funding 없는 market_type에서 funding 필드는 0 또는 not_applicable로 고정되어야 한다.
  - 비용 누락 또는 음수 비용 조작 시 scorecard validation이 FAIL이어야 한다.

---

## 3. signal grading / parameter search / strategy competition

- 현재 상태
  - `profit_optimizer_config.schema.json`, `optimization_state.schema.json`, `optimizer_memory_state.schema.json`, `parameter_narrowing_report.schema.json`, `search_space_snapshot.schema.json`, `exploration_exploitation_policy.schema.json`이 존재한다.
  - 그러나 optimizer 실행 코드, parameter search loop, strategy competition scheduler, candidate promotion implementation은 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - 사용자 요구는 PAPER/SHADOW에서 자동으로 데이터가 축적되고 파라미터가 개선되는 구조다.
  - 현재는 optimizer 관련 산출물의 형태만 있고 실제 parameter trial 생성, scoring, OOS 검증, 후보 탈락/승격 절차가 없다.
  - `exploration_exploitation_policy.schema.json`은 live mutation 관련 필드를 대부분 const false로 잠그고 있어 안전하지만, PAPER 내 자동 개선 구현은 보이지 않는다.

- 실제 운영 시 어떤 위험이 생기는지
  - PAPER를 오래 돌려도 전략 파라미터가 개선되지 않는다.
  - AI compiler가 “optimizer”라는 명칭만 보고 임의 탐색 정책을 추가할 수 있다.
  - strategy competition 결과가 실제 거래 성능이 아니라 report 작성 여부에 의해 결정될 수 있다.

- 필요한 수정 방향
  - 탐색 후보 생성, paper/shadow 실행, scorecard 집계, overfit 필터, parameter narrowing까지 하나의 deterministic pipeline으로 닫아야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/optimizer/search_space.py`
  - `trader1/optimizer/runner.py`
  - `trader1/optimizer/ranking.py`
  - `trader1/optimizer/promotion.py`
  - shadow strategy별 independent ledger/evidence namespace 생성.

- 검증 방법 또는 acceptance 조건
  - 동일 seed와 동일 입력 데이터에서 동일 ranking이 재현되어야 한다.
  - parameter search 후보가 live config를 직접 수정하면 FAIL이어야 한다.
  - scorecard winner라도 OOS/walk-forward/bootstrap fail이면 LIVE_READY 후보가 될 수 없어야 한다.

---

## 4. paper / shadow / replay / micro-live / live

- 현재 상태
  - schema enum에는 `REPLAY`, `PAPER`, `SHADOW`, `LIVE`, `SAFE`, `READ_ONLY`가 있다.
  - 사용자 요구의 `MICRO_LIVE`는 mode enum에 없다.
  - root launcher는 Binance paper/live만 존재하고 Upbit root launcher는 없다.
  - 루트 launcher 자체가 import 실패한다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - 사용자 운영 흐름은 PAPER 실행 → dashboard 확인 → LIVE_READY 확인 → MICRO_LIVE/LIVE 전환이다.
  - 현재 mode enum에 MICRO_LIVE가 없으므로 요구 운영 단계가 authority surface에 닫혀 있지 않다.
  - Upbit/Binance 전체 지원 요구와 다르게 실제 root launcher는 Binance 2개뿐이다.

- 실제 운영 시 어떤 위험이 생기는지
  - MICRO_LIVE 단계 없이 LIVE로 바로 넘어가거나, AI compiler가 임의로 MICRO_LIVE를 추가하면서 schema와 충돌할 수 있다.
  - Upbit KRW cashflow 요구가 root 실행 구조에서 누락된다.
  - paper/shadow/replay evidence가 실제 runtime 없이 보고서로만 존재할 수 있다.

- 필요한 수정 방향
  - MICRO_LIVE를 명시적 mode로 추가하거나, LIVE 내부 substage로 닫아야 한다.
  - root launchers는 사용자가 혼동하지 않게 exchange/mode별로 닫아야 한다.

- AI compiler가 구현해야 할 구체 작업
  - mode enum 확정: `MICRO_LIVE` 추가 또는 `LIVE_STAGE=MICRO_LIVE` schema 추가.
  - `UPBIT_PAPER.py`, `UPBIT_LIVE.py`, `BINANCE_PAPER.py`, `BINANCE_LIVE.py` root launcher 복구.
  - `trader1/runtime/boot/safe_launcher.py` 구현.
  - PAPER/SHADOW/REPLAY runtime orchestrator 구현.

- 검증 방법 또는 acceptance 조건
  - 모든 root launcher가 import 성공해야 한다.
  - LIVE launcher는 LIVE_READY snapshot 없이는 fail-closed 종료해야 한다.
  - MICRO_LIVE는 사이징 상한, max daily loss, kill-switch, manual/order test evidence를 별도로 요구해야 한다.

---

## 5. LIVE_READY snapshot / live gating / fail-closed

- 현재 상태
  - `live_ready_snapshot.schema.json`은 존재한다.
  - `live_order_allowed=true` 조건에서 `official_api_verification_id`, `read_only_burn_in_id`, `emergency_protection_evidence_id`, validator PASS, invalidated_by empty를 요구한다.
  - 그러나 `performance_summary`, `risk_limits`, `sizing_limits`, `validation_results`는 단순 object로만 정의되어 내부 필수 구조가 닫혀 있지 않다.
  - live_ready_snapshot writer 구현이 없다.

- 문제 여부
  - 부분적으로 안전하지만 닫힌 설계로는 부족함.

- 결함 등급
  - High

- 왜 문제인지
  - live gating 자체는 방향이 맞다.
  - 그러나 핵심 근거 object들이 빈 object나 임의 payload로 통과될 수 있다면 LIVE_READY snapshot이 실질적 증거가 아니라 형식 문서가 된다.
  - validator 구현과 fixture가 누락되어 schema의 조건이 실제로 강제되지 않는다.

- 실제 운영 시 어떤 위험이 생기는지
  - 잘못된 snapshot이 있으면 LIVE 전환 판단이 왜곡될 수 있다.
  - 반대로 현재처럼 writer/validator가 없으면 영구적으로 LIVE_READY가 생성되지 않는다.

- 필요한 수정 방향
  - LIVE_READY snapshot 내부 구조를 nested schema로 닫아야 한다.
  - writer는 read-only evidence bundle, paper/shadow scorecard, reconciliation, live preflight, official API verification, manual micro order test evidence를 모두 join해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/readiness/live_ready_writer.py`
  - `trader1/readiness/live_ready_validator.py`
  - nested schemas: performance_summary, risk_limits, sizing_limits, validation_results.
  - snapshot expiry and invalidation checker.

- 검증 방법 또는 acceptance 조건
  - empty object가 `performance_summary`에 들어가면 FAIL.
  - stale snapshot이면 LIVE launcher가 FAIL.
  - manifest hash/source tree hash mismatch면 FAIL.

---

## 6. risk engine / drawdown / cooling / kill switch

- 현재 상태
  - `risk_scaling_decision.schema.json`, `position_sizing_decision.schema.json`, `emergency_flatten_report.schema.json`, `safety_control_report.schema.json`, `survival_layer_report.schema.json`이 존재한다.
  - 실제 risk engine, drawdown tracker, cooldown scheduler, kill switch runtime, emergency flatten adapter는 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - live safety는 단순 boolean만으로 충분하지 않다.
  - 포지션 크기, 일손실, 연속손실, 계좌 drawdown, stale data, exchange private stream health, partial fill 상태가 runtime에서 kill switch로 연결되어야 한다.
  - 현재는 산출물 schema만 있고 실제 emergency flatten을 실행하거나 live를 차단할 runtime loop가 없다.

- 실제 운영 시 어떤 위험이 생기는지
  - 실거래에서 손실 제한이 작동하지 않는다.
  - 장애 중 주문이 계속 나가거나 포지션이 방치될 수 있다.
  - cooling/circuit breaker가 dashboard 문구로만 존재할 수 있다.

- 필요한 수정 방향
  - risk engine은 order submission path 앞단에서 hard gate로 작동해야 한다.
  - kill switch는 dashboard 표시가 아니라 executor를 중단시키는 authoritative state여야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/risk/limits.py`
  - `trader1/risk/drawdown.py`
  - `trader1/risk/cooldown.py`
  - `trader1/risk/kill_switch.py`
  - `trader1/execution/emergency_flatten.py`는 live stage에서만 adapter 연결, PAPER에서는 simulation.

- 검증 방법 또는 acceptance 조건
  - max daily loss 초과 fixture에서 can_submit_order=false.
  - stale private stream에서 new entry blocked.
  - kill switch active 상태에서 모든 order path 호출 금지.

---

## 7. exchange / market_type / namespace separation

- 현재 상태
  - common defs에는 `UPBIT`, `BINANCE`, `KRW_SPOT`, `SPOT`, `FUTURES_USDT_M`가 있다.
  - source bundle denylist는 `UPBIT_PAPER.py`, `UPBIT_LIVE.py`, `BINANCE_PAPER.py`, `BINANCE_LIVE.py`를 allow root로 둔다.
  - 실제 root launcher는 Binance 2개뿐이다.
  - runtime directories는 현재 source bundle에 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - schema enum은 exchange/market_type 분리를 암시하지만 실제 namespace 구현이 없다.
  - Upbit와 Binance spot/futures는 주문 제약, 수수료, 포지션 개념, 계좌 snapshot 구조가 다르다.
  - 단일 executor나 ledger가 이를 섞으면 reconciliation과 세금/출금 계산이 붕괴한다.

- 실제 운영 시 어떤 위험이 생기는지
  - Binance futures 포지션을 spot position처럼 처리할 수 있다.
  - Upbit KRW cashflow와 Binance USDT PnL이 dashboard에서 섞일 수 있다.
  - exchange-specific order rejection 처리가 누락된다.

- 필요한 수정 방향
  - exchange/market_type/mode/session_id를 모든 artifact path와 DB key에 포함해야 한다.
  - adapter interface는 common interface + exchange-specific implementation으로 분리해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/adapters/upbit/`
  - `trader1/adapters/binance_spot/`
  - `trader1/adapters/binance_futures_usdt_m/`
  - namespace path validator 구현.
  - artifact path convention 강제.

- 검증 방법 또는 acceptance 조건
  - UPBIT/KRW_SPOT artifact가 BINANCE/SPOT path에 쓰이면 FAIL.
  - futures position fields가 spot ledger에 들어가면 FAIL.
  - root launcher별 allowed market_type이 명확해야 한다.

---

## 8. Upbit spot / Binance spot / Binance futures 1x long-short

- 현재 상태
  - Binance launchers에 `MARKET_TYPE_OPTIONS = ("SPOT", "FUTURES_USDT_M")`가 있으나 `FUTURES_USDT_M_STATUS = "BLOCKED_NOT_IMPLEMENTED"`로 표시된다.
  - Upbit launchers는 실제 파일에 없다.
  - Binance futures 1x long-short 실행 구현은 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - 사용자가 명시한 대상은 Upbit spot, Binance spot, Binance futures 1x long-short다.
  - 현재 Binance futures는 surface-only blocked이며 Upbit root execution도 없다.
  - futures long-short라면 one-way/hedge mode, leverage=1, margin type, reduce-only, liquidation/risk, funding, position side 정책이 닫혀야 하는데 구현이 없다.

- 실제 운영 시 어떤 위험이 생기는지
  - futures를 사용 가능하다고 착각할 수 있다.
  - long-short semantics가 spot sell/buy semantics와 섞이면 위험하다.
  - leverage=1 보장이 없다면 실거래 위험이 커진다.

- 필요한 수정 방향
  - Binance futures는 별도 staged adapter로 구현하고, 구현 전에는 명시적으로 unavailable이어야 한다.
  - Upbit spot root launcher를 복구해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - Upbit spot paper runtime 최소 구현.
  - Binance spot paper runtime 최소 구현.
  - Binance futures adapter는 read-only metadata/preflight부터 구현.
  - futures live는 leverage=1, margin mode, position mode verification이 PASS일 때만 micro-live 후보.

- 검증 방법 또는 acceptance 조건
  - Binance futures order path는 implementation 전 항상 blocked.
  - futures live preflight에서 leverage != 1이면 FAIL.
  - position mode mismatch면 FAIL.

---

## 9. order lifecycle / execution quality / partial fill

- 현재 상태
  - `ledger_event.schema.json`, `execution_quality_measurement_report.schema.json`, `manual_order_test_evidence.schema.json`이 존재한다.
  - 실제 order state machine, order adapter, partial fill handler, cancel/replace logic은 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - 주문 생애주기는 trading bot의 핵심 runtime이다.
  - schema만 있고 order submitted/open/partial/filled/cancelled/rejected/expired/reconciled 상태 전이가 없다.
  - partial fill 처리 없이는 position, ledger, risk가 모두 틀어진다.

- 실제 운영 시 어떤 위험이 생기는지
  - 주문 일부 체결 후 잔량 처리 실패.
  - 중복 주문, 미체결 방치, 포지션 과다 노출.
  - dashboard와 실제 계좌 상태 불일치.

- 필요한 수정 방향
  - order lifecycle state machine을 구현하고, 모든 전이를 idempotent ledger event로 기록해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/execution/order_state.py`
  - `trader1/execution/router.py`
  - `trader1/execution/fill_handler.py`
  - `trader1/execution/execution_quality.py`
  - partial fill and cancel fixtures.

- 검증 방법 또는 acceptance 조건
  - duplicate fill event는 idempotent 처리.
  - partial fill 후 available balance/position/risk가 정확히 갱신.
  - rejected order는 new entry cooldown 또는 exchange rejection taxonomy에 연결.

---

## 10. ledger / reconciliation / idempotency

- 현재 상태
  - `ledger_event.schema.json`, `reconciliation_report.schema.json`, `paper_ledger_rollup_report.schema.json`, `intent_wal_event.schema.json`이 존재한다.
  - 실제 WAL append, atomic write, replay recovery, exchange snapshot reconciliation 구현은 없다.
  - source bundle manifest가 선언한 테스트/코드 대부분이 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - ledger와 reconciliation은 실거래 안전의 최종 방어선이다.
  - 현재 schema는 있지만 실제 ledger head hash, idempotency key, exchange snapshot join, mismatch resolver가 없다.

- 실제 운영 시 어떤 위험이 생기는지
  - 재시작 후 중복 주문.
  - 잔고/포지션 불일치를 모른 채 계속 매매.
  - 손익/세금/export 데이터가 신뢰 불가능.

- 필요한 수정 방향
  - intent WAL, order event ledger, fill ledger, reconciliation snapshot을 분리하고 hash chain으로 연결해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/ledger/wal.py`
  - `trader1/ledger/events.py`
  - `trader1/ledger/reconciliation.py`
  - `trader1/ledger/idempotency.py`
  - crash recovery fixtures.

- 검증 방법 또는 acceptance 조건
  - 동일 event 재처리 시 ledger hash가 변하지 않아야 한다.
  - exchange snapshot mismatch 발생 시 new entry blocked.
  - partial write JSONL recovery test PASS.

---

## 11. data health / stale data / gap / duplicate / clock drift

- 현재 상태
  - `heartbeat.schema.json`, `private_stream_health.schema.json`, `upbit_public_market_data_collection_report.schema.json`, `upbit_public_rest_continuity_report.schema.json` 등이 존재한다.
  - 실제 collector, gap detector, dedupe engine, clock drift monitor는 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - 전략 판단은 data freshness와 sequence integrity 없이는 무효다.
  - schema의 stale/gap fields가 실제 feed 처리와 연결되지 않는다.

- 실제 운영 시 어떤 위험이 생기는지
  - stale orderbook으로 진입.
  - 누락 candle/trade 기반으로 잘못된 regime 판단.
  - 시계 드리프트로 주문/캔들 정렬 오류.

- 필요한 수정 방향
  - public/private data collectors와 health gate를 구현해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/data/collector/`
  - `trader1/data/health.py`
  - `trader1/data/dedupe.py`
  - `trader1/time/clock.py`

- 검증 방법 또는 acceptance 조건
  - stale threshold 초과 시 entry blocked.
  - duplicate event는 single canonical event로만 반영.
  - clock drift threshold 초과 시 order path blocked.

---

## 12. concurrency / race condition / restart recovery

- 현재 상태
  - `restart_recovery_report.schema.json`, `runtime_stability_history.schema.json`, `upbit_paper_runtime_recovery_guard_report.schema.json` 등이 존재한다.
  - 실제 lock, lease, atomic writer, process supervisor, restart recovery code는 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - 24/7 trading system은 restart, crash, partial write, duplicate process 문제를 전제로 설계해야 한다.
  - 현재는 schema/report 중심이고 runtime write lock이 구현되어 있지 않다.

- 실제 운영 시 어떤 위험이 생기는지
  - PAPER와 LIVE가 같은 artifact를 동시에 갱신.
  - Windows 재부팅/강제 종료 후 state corruption.
  - dashboard stale state를 fresh로 오인.

- 필요한 수정 방향
  - single-writer lock, atomic rename, write-ahead intent, startup recovery gate를 구현해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/runtime/locks.py`
  - `trader1/runtime/recovery.py`
  - `trader1/runtime/supervisor.py`
  - stale heartbeat and lock lease expiry tests.

- 검증 방법 또는 acceptance 조건
  - active lock이 있으면 second process가 fail-closed.
  - crash during write fixture에서 corrupted file을 quarantine.
  - recovery unresolved 상태에서는 new entry blocked.

---

## 13. dashboard / USER_STATUS_SUMMARY / user simplicity

- 현재 상태
  - `read_only_dashboard_shell.schema.json`, `summary.schema.json`, 여러 dashboard context pack이 존재한다.
  - 실제 dashboard runtime files는 source bundle에 없다.
  - dashboard renderer/server 구현도 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - 사용자 요구는 단순 조작 구조다: PAPER 실행, dashboard 확인, LIVE_READY 확인, MICRO_LIVE/LIVE 전환, STOP.
  - 현재는 dashboard schema와 evidence prose가 많지만 사용자가 실행할 실제 dashboard surface가 없다.

- 실제 운영 시 어떤 위험이 생기는지
  - 사용자가 무엇이 정상/비정상인지 확인할 수 없다.
  - LIVE_READY가 없거나 stale인 상태를 구분하지 못한다.
  - “사용자 단순성”이 구현되지 않고 문서 요구로만 남는다.

- 필요한 수정 방향
  - dashboard는 read-only truth surface로 실제 runtime artifact를 읽고 표시해야 한다.
  - USER_STATUS_SUMMARY는 1화면에서 LIVE_READY, net EV maturity, data health, risk, reconciliation, next action을 보여야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/dashboard/render.py`
  - `trader1/dashboard/status_summary.py`
  - `trader1/dashboard/static/` 또는 간단한 local HTML writer.
  - STOP control은 execution truth와 분리하되 operator control WAL에 기록.

- 검증 방법 또는 acceptance 조건
  - dashboard가 order adapter를 호출하면 FAIL.
  - missing/stale source artifact를 fresh로 표시하면 FAIL.
  - primary_status_text가 forbidden optimistic wording을 포함하면 FAIL.

---

## 14. validator / schema / registry / acceptance artifacts

- 현재 상태
  - registry와 schema files는 다수 존재한다.
  - validator registry는 101개 implemented validator를 선언한다.
  - 그러나 validator module은 없다.
  - fixture는 전량 누락이다.
  - source bundle manifest는 actual tree와 대규모 불일치한다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - AI가 판단 없이 구현하려면 registry/schema/validator/acceptance가 실제로 닫혀 있어야 한다.
  - 현재는 registry와 manifest가 실제 파일 시스템을 반영하지 않는다.
  - “IMPLEMENTED” 선언이 실행 불가능하므로 acceptance artifact가 신뢰 불가능하다.

- 실제 운영 시 어떤 위험이 생기는지
  - AI compiler가 이미 구현된 것으로 착각하고 핵심 validator를 건너뛸 수 있다.
  - release package가 통과했다고 오판할 수 있다.
  - live readiness 검증이 불가능하다.

- 필요한 수정 방향
  - 먼저 manifest를 실제 tree 기준으로 재생성하거나, 누락 파일을 복구해야 한다.
  - validator registry는 실제 import 가능한 module과 테스트 fixture를 기준으로만 IMPLEMENTED를 선언해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/validation/mvp0_validators.py` 실제 구현.
  - `tests/validators/fixtures/*.json` 복구.
  - source bundle manifest 재생성.
  - authority manifest가 실제 `TRADER_1.md` 존재와 hash를 검증.

- 검증 방법 또는 acceptance 조건
  - source bundle manifest missing=0, mismatch=0.
  - fixture catalog missing=0.
  - all validator module imports PASS.
  - negative fixtures가 expected FAIL/BLOCKED로 동작.

---

## 15. testing / pytest / paper run proof / live block proof

- 현재 상태
  - `pyproject.toml`은 `testpaths = ["tests"]`로 설정되어 있다.
  - 실제 `tests/` 디렉터리가 없다.
  - pytest 실행 결과 exit code 5.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - 테스트가 없는 상태에서 acceptance를 주장할 수 없다.
  - live block proof도 실행 가능한 negative test가 아니다.

- 실제 운영 시 어떤 위험이 생기는지
  - live safety regression을 잡을 수 없다.
  - paper runtime이 실제로 돌아가는지 증명할 수 없다.
  - release마다 manifest drift를 놓친다.

- 필요한 수정 방향
  - smoke, contract, validator, runtime, dashboard, ledger, risk, adapter tests를 복구해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `tests/test_import_smoke.py`
  - `tests/contract/test_manifest_integrity.py`
  - `tests/contract/test_live_blocked_defaults.py`
  - `tests/runtime/test_paper_boot.py`
  - `tests/validators/test_fixture_catalog.py`

- 검증 방법 또는 acceptance 조건
  - `python -m pytest -q` exit code 0.
  - live launcher without valid LIVE_READY snapshot returns blocked code.
  - PAPER launcher creates fresh heartbeat/dashboard/reconciliation artifacts in temp runtime root.

---

## 16. security / secrets / API key safety

- 현재 상태
  - `source_bundle_denylist.json` includes `.env`, pem/key, credential dump patterns.
  - 실제 secret scan code는 없다.
  - `api_key_permission_check_report.schema.json`은 존재하지만 실행 구현이 없다.

- 문제 여부
  - 부분 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - denylist는 선언일 뿐이다.
  - API key 권한 검사와 credential loading block이 runtime에서 구현되어 있지 않다.
  - Binance/Upbit live adapter 구현 전에는 key loading 자체가 차단되어야 한다.

- 실제 운영 시 어떤 위험이 생기는지
  - 잘못된 권한의 API key 사용.
  - live-disabled stage에서 credential 접근.
  - secret이 manifest/release/log에 포함될 수 있음.

- 필요한 수정 방향
  - secret scan과 credential access gate를 실제 코드로 구현해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/security/secrets.py`
  - `trader1/security/source_scan.py`
  - API key permission checker는 read-only/live stage별 권한을 분리.

- 검증 방법 또는 acceptance 조건
  - `.env` 포함 release는 FAIL.
  - PAPER/REPLAY/SHADOW에서 credential loading attempt는 FAIL.
  - LIVE preflight 이전 order permission key는 rejected.

---

## 17. deployment / packaging / git hygiene / pycache / generated artifacts

- 현재 상태
  - zip에 `.git/` 전체가 포함되어 있다.
  - source bundle denylist는 `contracts/generated/`, `system/`, `__pycache__/`, `.pytest_cache/` 등을 deny한다.
  - 실제 package에는 `contracts/generated/`와 `system/evidence/`가 포함되어 있다.
  - source bundle manifest는 대규모 누락/불일치를 보인다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Critical

- 왜 문제인지
  - release/source package boundary가 닫혀 있지 않다.
  - `.git/` 포함은 불필요하고, history/object에 민감 정보가 섞일 수 있는 위험이 있다.
  - generated artifact와 source authority가 섞여 있어 AI compiler가 무엇을 truth로 봐야 하는지 혼동할 수 있다.

- 실제 운영 시 어떤 위험이 생기는지
  - 잘못된 generated stale artifact를 기준으로 구현.
  - release 재현성 붕괴.
  - git object 포함으로 패키지 크기/보안/추적성 문제.

- 필요한 수정 방향
  - source package와 runtime/generated package를 분리해야 한다.
  - source bundle manifest를 현재 package 기준으로 재생성하고, denylist 위반을 0으로 만들어야 한다.

- AI compiler가 구현해야 할 구체 작업
  - packaging script 구현: source bundle, evidence bundle, runtime bundle 분리.
  - `.git/`, generated stale artifacts 제외.
  - manifest hash 재생성 및 verify command 추가.

- 검증 방법 또는 acceptance 조건
  - packaged zip에 `.git/` 없음.
  - denylist violation=0.
  - manifest missing=0, mismatch=0.

---

## 18. tax/accounting/export readiness

- 현재 상태
  - 이 영역에 해당하는 명시적 accounting/export runtime implementation은 확인되지 않았다.
  - ledger schema가 존재하지만 세금/회계용 realized PnL, fee currency, FX conversion, withdrawal records, exchange statements join 구조는 닫혀 있지 않다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Medium

- 왜 문제인지
  - 실거래 이후 사용자가 손익과 출금 가능 현금흐름을 확인하려면 tax/accounting/export가 필요하다.
  - 특히 Upbit KRW, Binance USDT, KRW conversion을 분리해야 한다.

- 실제 운영 시 어떤 위험이 생기는지
  - 실제 수익과 dashboard 수익이 다르게 보임.
  - 세금 신고 또는 회계 정산 시 필요한 거래 내역이 누락될 수 있음.

- 필요한 수정 방향
  - MVP live 전 필수는 아니지만, ledger 설계 단계에서 export-ready 필드를 포함해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/accounting/export.py`
  - realized/unrealized PnL 분리.
  - fee currency, quote currency, settlement currency 기록.
  - CSV/Parquet export schema 추가.

- 검증 방법 또는 acceptance 조건
  - spot buy/sell round trip fixture에서 realized PnL이 수수료 차감 후 일치.
  - futures funding/fee/realized PnL이 별도 line item으로 export.

---

## 19. KRW cashflow / profit conversion / withdrawal policy

- 현재 상태
  - Upbit KRW spot 지원 의도는 common defs에 `KRW_SPOT`로만 반영되어 있다.
  - KRW cashflow, Binance USDT to KRW conversion, withdrawal policy, remittance/exchange transfer policy 구현은 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - Medium

- 왜 문제인지
  - 사용자가 원화 현금흐름을 원하면 Upbit KRW 실현손익과 Binance USDT 손익의 KRW 환산 정책이 필요하다.
  - 환산 기준 시간, 환율 source, 출금 가능 금액, reserve buffer가 닫혀 있지 않다.

- 실제 운영 시 어떤 위험이 생기는지
  - dashboard의 “수익”이 원화 출금 가능 수익과 다를 수 있다.
  - Binance futures 수익을 KRW cashflow로 오인할 수 있다.

- 필요한 수정 방향
  - dashboard에는 native PnL과 KRW converted PnL을 분리 표시해야 한다.
  - withdrawal policy는 자동 출금이 아니라 operator-visible planning artifact로 시작해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/accounting/krw_cashflow.py`
  - KRW conversion source schema.
  - withdrawal buffer/reserve policy schema.

- 검증 방법 또는 acceptance 조건
  - Upbit KRW realized cashflow와 Binance USDT converted estimate를 별도 표시.
  - 환율 source missing/stale이면 KRW converted PnL은 unavailable로 표시.

---

## 20. overfitting / walk-forward / out-of-sample validation

- 현재 상태
  - `overfit_diagnostic_report.schema.json`은 비교적 많은 required field를 가진다.
  - sample_count, train/oos/walk-forward/bootstrap counts, degradation bps, pass rate, confidence lower bound, ranking stability score 등이 요구된다.
  - 그러나 actual runner, sample generator, bootstrap implementation, OOS splitter는 없다.

- 문제 여부
  - 문제 있음.

- 결함 등급
  - High

- 왜 문제인지
  - 대수의 법칙 기반 기대값 수렴 구조는 충분한 독립 표본, OOS 검증, regime별 robustness가 필요하다.
  - schema는 좋은 방향이지만 계산 구현과 fixture가 없으면 숫자를 임의로 채울 수 있다.

- 실제 운영 시 어떤 위험이 생기는지
  - overfit 후보가 LIVE_READY로 승격될 수 있다.
  - paper sample이 특정 구간에 편중되어 실제 시장에서 기대값이 붕괴한다.

- 필요한 수정 방향
  - walk-forward splitter, bootstrap lower confidence bound, regime-balanced sampling을 실제 구현해야 한다.

- AI compiler가 구현해야 할 구체 작업
  - `trader1/research/split.py`
  - `trader1/research/bootstrap.py`
  - `trader1/research/oos.py`
  - `trader1/research/overfit.py`

- 검증 방법 또는 acceptance 조건
  - train-only 성과가 좋고 OOS가 나쁘면 promotion_eligible=false.
  - bootstrap lower bound가 threshold 미달이면 FAIL.
  - sample_count < min_required_sample_count이면 FAIL.

---

## 전체 상태 한 줄 정의

현재 TRADER_1.zip은 schema/report 중심의 부분 산출물은 많지만, active authority 누락, source manifest 붕괴, validator/test/runtime 부재, root launcher import 실패 때문에 PAPER 실행조차 불가능한 비실행 패키지다.

## 전체 완성도 점수

- 설계 의도와 schema 표면: 45 / 100
- 실제 실행 가능성: 5 / 100
- live safety 보수성: 70 / 100
- AI compiler 구현 가능성: 25 / 100
- 종합 점수: 22 / 100

점수 근거:

- live safety는 기본적으로 false/block 중심이라 무리하게 live를 여는 구조는 아니다.
- 그러나 실행 코드, tests, validators, fixtures, authority file, manifest consistency가 모두 무너져 있어 구현 가능성 점수가 낮다.
- AI compiler가 판단 없이 구현하기에는 “implemented” 선언과 실제 파일 상태가 충돌한다.

## 실거래 후보 여부

실거래 후보 아님.

현재는 MICRO_LIVE 후보도 아니고, PAPER runtime 후보도 아니다. 먼저 package integrity와 PAPER boot가 복구되어야 한다.

## 가장 위험한 결함 Top 10

1. `TRADER_1.md` authoritative file 누락.
2. `trader1/` runtime package 전량 누락으로 root launcher import 실패.
3. source bundle manifest: 776개 선언 중 665개 누락, 45개 hash mismatch.
4. validator registry는 101개 implemented를 선언하지만 실제 validator module 없음.
5. fixture catalog 91개 전량 누락.
6. `tests/` 디렉터리 없음, pytest exit code 5.
7. strategy/regime/entry/exit 실제 구현 없음.
8. order lifecycle/partial fill/reconciliation 실제 구현 없음.
9. MICRO_LIVE가 mode enum과 runtime flow에 없음.
10. Binance futures 1x long-short와 Upbit spot root execution이 구현되지 않음.

## 다음 세션에서 이어서 볼 영역

세션 3에서는 다음을 우선 검토해야 한다.

1. `AGENTS.md` 내부 authority/read order/stage boundary가 현재 실제 파일 누락과 어떻게 충돌하는지 정독 검토.
2. `contracts/registry.yaml`의 requirement id, blocker code, validator mapping이 실제 schema와 일관되는지 정밀 검토.
3. `contracts/generated/current_implementation_state.json`의 completed requirement 선언이 실제 파일 상태와 얼마나 불일치하는지 requirement 단위로 추적.
4. `candidate_scorecard`, `overfit_diagnostic`, `live_ready_snapshot`, `runtime_config`, `read_only_dashboard_shell`의 schema hole 정밀 검토.
5. source bundle manifest 재생성 전제와 복구 우선순위 확정.

## 구현 우선순위 로드맵

### P0. 패키지 무결성 복구

- `TRADER_1.md` 복구 또는 authority manifest에서 제거하고 active authority를 재정의.
- `trader1/` source package 복구.
- `tests/`와 validator fixtures 복구.
- source bundle manifest 재생성.
- `.git/`와 stale generated/runtime evidence를 package boundary에서 제거.

Acceptance:

- manifest missing=0.
- manifest mismatch=0.
- fixture missing=0.
- `python -m pytest -q` exit code 0.

### P1. root launcher and fail-closed boot 복구

- `safe_launcher` 구현.
- UPBIT/BINANCE PAPER/LIVE launchers 정리.
- LIVE launcher는 valid LIVE_READY 없으면 blocked.

Acceptance:

- 모든 launcher import PASS.
- PAPER launcher creates temp runtime artifacts.
- LIVE launcher blocked by default.

### P2. validator/schema/registry 실행화

- validator registry의 declared validators를 실제 Python implementation과 연결.
- negative fixtures로 false-live, stale snapshot, manifest drift, cost omission 차단.

Acceptance:

- validator registry import check PASS.
- declared implemented validator 100% callable.
- negative fixtures expected FAIL/BLOCKED.

### P3. PAPER runtime 최소 실행 경로

- data collector mock/fixture path.
- strategy candidate generation.
- cost-adjusted scorecard.
- paper order/fill simulation.
- ledger/reconciliation/dashboard write.

Acceptance:

- PAPER one-cycle deterministic smoke PASS.
- stale data fixture blocks entry.
- partial fill simulation reconciles.

### P4. shadow/replay/optimizer/OOS

- parameter search and strategy competition 구현.
- walk-forward/OOS/bootstrap validation 구현.
- winner cannot mutate live config directly.

Acceptance:

- overfit fixture blocked.
- OOS fail blocks promotion.
- candidate ranking deterministic.

### P5. MICRO_LIVE 정의 및 실거래 전 preflight

- MICRO_LIVE mode 또는 substage 명시.
- API permission verification.
- read-only burn-in.
- manual micro order test evidence.
- kill switch/emergency flatten proof.

Acceptance:

- MICRO_LIVE absent/invalid evidence blocks LIVE.
- leverage=1 verification required for Binance futures.
- emergency protection evidence required for live_order_allowed=true.
