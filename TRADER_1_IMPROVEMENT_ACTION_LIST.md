# TRADER_1 개선안 구체 리스트

작성 시각: 2026-05-06T23:14:31.446868+00:00

목적:

```text
TRADER_1 전수검토 결과에서 도출된 개선안만 분리하여,
Codex 또는 구현 AI가 바로 작업 backlog로 사용할 수 있도록 정리한다.
```

기본 원칙:

```text
LIVE는 계속 차단한다.
live_order_ready=false
live_order_allowed=false
can_live_trade=false

새 validator / wrapper / review-only layer를 무작정 늘리지 않는다.
실제 runtime, trading quality, paper operation, ledger, strategy, dashboard 개선을 우선한다.
```

---

## P0. 즉시 수정해야 할 blocker

### P0-1. Evidence hash 정합성 복구

문제:

```text
current_implementation_state.json의 last_patch_result_hash와
implementation_patch_ledger.json의 patches[-1].patch_result_hash가 불일치한다.
```

구현 항목:

- `contracts/generated/current_implementation_state.json`의 `last_patch_result_hash` 확인
- `system/evidence/implementation_patch_ledger.json`의 top-level `last_patch_result_hash` 확인
- `system/evidence/implementation_patch_ledger.json`의 `patches[-1].patch_result_hash` 확인
- latest `patch_result.json`의 `result_hash` 확인
- 위 4개 값을 동일한 최신 patch result 기준으로 원자적으로 재생성
- 수동 조작이 아니라 ledger/state generation pipeline을 수정
- 재발 방지 regression test 추가 또는 기존 테스트 통과 보장

완료 기준:

```text
python -m pytest -q tests/live_blocked --tb=short --disable-warnings
```

결과가 실패 없이 통과해야 한다.

---

### P0-2. 테스트 profile 분리

문제:

```text
전체 pytest가 크고 느리며, 실패 원인이 runtime 품질인지 evidence 정합성인지 구분하기 어렵다.
```

구현 항목:

- `test:syntax`
- `test:smoke`
- `test:runtime-paper`
- `test:live-blocked`
- `test:evidence`
- `test:release`

형태로 실행 프로파일을 분리한다.

권장 명령 예:

```text
test:syntax
python -m compileall -q trader1 tests tools

test:live-blocked
python -m pytest -q tests/live_blocked --tb=short --disable-warnings

test:runtime-paper
isolated root에서 UPBIT PAPER bounded loop, ledger rollup, dashboard generation 검증

test:evidence
current state / patch ledger / manifest hash consistency 검증

test:release
source bundle hygiene 검증
```

완료 기준:

- 각 profile이 독립 실행 가능
- 실패 시 원인 영역이 명확히 분리됨
- quick smoke가 짧은 시간 안에 완료됨

---

### P0-3. Source / runtime / evidence / release bundle 분리

문제:

```text
현재 ZIP은 source, .git, runtime outputs, evidence artifacts, generated artifacts, pycache가 섞인 audit-heavy working bundle이다.
```

구현 항목:

- clean source bundle 생성
- runtime output bundle 분리
- evidence audit bundle 분리
- release acceptance bundle 분리
- `.git` 제외
- `__pycache__` 제외
- `*.pyc` 제외
- `system/runtime`을 source release에서 제외
- `system/evidence`를 source release에서 제외
- generated artifact는 재생성 가능해야 함

권장 구조:

```text
repo/
  trader1/
  tests/
  tools/
  contracts/schema/
  contracts/registry.yaml
  TRADER_1.md
  AGENTS.md
  pyproject.toml

runtime/
  system/runtime/...

evidence/
  system/evidence/...

release/
  acceptance bundle
```

완료 기준:

- source bundle 안에 `.git`, pycache, runtime output이 없음
- source hash가 runtime 실행으로 오염되지 않음
- release verify에서 source/runtime/evidence 경계가 명확함

---

## P1. UPBIT PAPER를 실제 장기 runner로 전환

### P1-1. `UPBIT_PAPER.py` 역할 확정

문제:

```text
현재 UPBIT_PAPER.py는 SAFE_MODE report/dashboard 생성에 가깝고,
장기 PAPER trading loop를 직접 운전하지 않는다.
```

구현 항목:

- `UPBIT_PAPER.py`를 실제 장기 PAPER runner로 연결할지 결정
- SAFE_MODE launcher와 장기 PAPER runner 역할 분리
- 혼동 방지를 위해 사용자용 실행 파일 이름 명확화
- 예시:
  - `UPBIT_PAPER.py`: 실제 장기 PAPER 실행
  - `UPBIT_PAPER_SAFE_CHECK.py`: 안전 점검 전용
  - 또는 내부 모드 플래그로 구분

완료 기준:

- 사용자가 `UPBIT_PAPER.py`를 실행하면 PAPER loop가 실제로 지속 실행됨
- dashboard에 running 상태가 표시됨
- LIVE 관련 flag는 계속 false 유지

---

### P1-2. Bounded evidence loop와 long-running loop 분리

문제:

```text
현재 paper persistent loop는 최대 20 cycle 제한의 bounded evidence generator다.
```

구현 항목:

- 기존 bounded loop는 테스트/evidence 용도로 유지
- 별도 long-running loop 구현
- cycle interval 설정
- stop signal 지원
- graceful shutdown 지원
- crash-safe latest state update
- next cycle ETA 계산
- loop status artifact 생성

완료 기준:

- bounded loop는 여전히 테스트용으로 빠르게 실행 가능
- long-running loop는 제한 cycle 없이 안전하게 반복 가능
- stop 요청 시 ledger 손상 없이 종료

---

### P1-3. Session-level single-writer lock 구현

문제:

```text
paper loop 전체에는 명확한 session-level single-writer lock이 부족하다.
```

구현 항목:

- session별 lock 파일 도입
- 동일 session duplicate start 차단
- 동일 loop_id 중복 실행 차단
- stale lock 처리
- owner pid 확인
- latest pointer update 구간 lock 보호
- ledger rollup 중 ledger write race 차단
- dashboard refresh와 write 충돌 방지

완료 기준:

- 동일 session을 2개 프로세스가 동시에 실행하면 하나는 fail-closed
- latest pointer overwrite 없음
- duplicate cycle_id artifact 생성 없음

---

### P1-4. 장기 PAPER runner 운영 정보 산출

구현 항목:

- `runner_status.json`
- `last_cycle_time`
- `next_cycle_eta`
- `current_cycle_id`
- `last_decision`
- `last_blocker`
- `current_position_count`
- `cash`
- `equity`
- `realized_pnl`
- `unrealized_pnl`
- `stop_method`
- `log_path`
- `dashboard_path`

완료 기준:

- dashboard와 JSON artifact에서 현재 PAPER 상태를 바로 확인 가능
- 초보 사용자가 “돌고 있는지 / 멈췄는지 / 뭘 해야 하는지”를 즉시 알 수 있음

---

## P1. PAPER broker / ledger / portfolio 실전성 강화

### P1-5. PAPER broker 체결 모델 강화

문제:

```text
현재 PAPER fill은 deterministic simulation에 가깝고 실전 체결 품질 모델이 약하다.
```

구현 항목:

- orderbook spread 반영
- orderbook depth 반영
- dynamic slippage
- volatility shock slippage
- partial fill
- cancel/reject
- maker/taker 구분
- queue position 추정
- latency penalty
- market impact
- liquidity vacuum 차단
- adverse selection penalty

완료 기준:

- fill price가 단순 mark price + 고정 slippage가 아님
- spread/depth/volatility 변화에 따라 fill 품질이 달라짐
- partial fill과 cancel/reject가 ledger에 반영됨

---

### P1-6. Reservation release / cancel / reject accounting 구현

구현 항목:

- order intent 생성
- budget reservation
- submit attempt
- submit reject
- partial fill
- full fill
- cancel request
- cancel accepted
- cancel failed
- reservation release
- ledger lifecycle completeness 검증

완료 기준:

- reject/cancel 시 cash reservation이 정확히 해제됨
- partial fill 후 남은 reservation 처리 가능
- ledger rollup이 모든 lifecycle을 검증

---

### P1-7. Exit lifecycle과 realized PnL 구현

문제:

```text
현재 portfolio rollup은 long spot filled order 중심이며 청산/실현손익이 약하다.
```

구현 항목:

- exit signal 생성
- reduce / close paper order
- average entry price 계산
- realized PnL 계산
- fee 반영
- slippage 반영
- position close accounting
- partial close 지원
- stop loss / take profit / trailing stop 반영
- exit reason 기록

완료 기준:

- realized PnL이 ledger 기반으로 계산됨
- open position과 closed trade가 구분됨
- dashboard에서 realized/unrealized PnL을 분리 표시

---

### P1-8. Intent WAL과 restart recovery 실제 결합

문제:

```text
intent WAL은 존재하지만 실제 paper runtime path와 강하게 결합되어 있지 않다.
```

구현 항목:

- order intent 생성 시 intent WAL durable append
- ledger event와 WAL source hash binding
- crash 후 WAL replay
- ledger head 복구
- portfolio snapshot 재생성
- incomplete intent 감지
- ambiguous state는 fail-closed

완료 기준:

- cycle 중단 후 재시작 시 ledger/head/portfolio가 일관되게 복구됨
- ambiguous recovery는 자동 live/readiness로 승격되지 않음

---

## P2. 전략 실전성 강화

### P2-1. Regime engine 고도화

문제:

```text
현재 regime detection은 EMA fast/slow와 last price 중심으로 단순하다.
```

구현 항목:

- volatility regime
- trend persistence
- crash acceleration detection
- chop filter
- multi-timeframe alignment
- breadth / market participation
- liquidity collapse detection
- correlation panic detection
- fake breakout regime
- sideways compression regime
- data quality degraded regime

완료 기준:

- 단순 UPTREND/RANGE/RISK_OFF 이상으로 regime reason이 표시됨
- 각 regime별 strategy enable/disable가 명확함
- dashboard에 why no trade / why entry가 설명됨

---

### P2-2. VWAP mean reversion 강화

구현 항목:

- adaptive VWAP band
- volatility adjusted deviation
- mean reversion exhaustion detection
- liquidity sweep / stop hunt filter
- spread widening 회피
- chop quality score
- dynamic entry threshold
- dynamic exit threshold
- failed mean reversion guard

완료 기준:

- RANGE regime에서만 기계적으로 진입하지 않음
- volatility와 spread 변화에 따라 진입 기준이 조정됨
- 실패한 mean reversion 조건은 차단됨

---

### P2-3. Pullback trend 강화

구현 항목:

- higher timeframe trend filter
- trend continuation probability
- pullback depth scoring
- trend exhaustion detection
- volume confirmation
- volatility compression confirmation
- dynamic stop placement
- trailing stop
- failed pullback guard

완료 기준:

- 단순 EMA 위 조건이 아니라 continuation 품질을 평가
- 손절/익절/추적 청산이 ledger와 portfolio에 연결됨

---

### P2-4. Breakout retest 강화

구현 항목:

- false breakout filter
- volume expansion confirmation
- volatility squeeze detection
- retest quality score
- breakout failure handling
- orderbook imbalance
- slippage guard
- failed breakout cooldown

완료 기준:

- 돌파 후보가 무조건 진입 후보가 되지 않음
- false breakout과 liquidity sweep 상황을 차단

---

### P2-5. Adaptive position sizing 구현

구현 항목:

- ATR / volatility adjusted sizing
- drawdown adaptive risk reduction
- realized performance adaptive sizing
- regime adaptive sizing
- symbol liquidity adjusted sizing
- correlation/covariance cap
- max exposure cap 유지
- min notional guard 유지
- confidence cap 유지

완료 기준:

- sizing이 단순 min caps 방식에서 벗어나 시장 상태와 성과를 반영
- 보수적 fail-closed cap은 유지

---

## P2. Dynamic symbol selection 구현

### P2-6. Upbit dynamic universe 구현

구현 항목:

- KRW market universe 수집
- stale symbol 제외
- min liquidity filter
- min volume filter
- spread/depth filter
- volatility expansion ranking
- momentum ranking
- regime compatibility ranking
- top-N selection
- symbol rotation cooldown
- per-symbol evidence 저장

완료 기준:

- KRW-BTC 단일 심볼 중심에서 벗어남
- dashboard에 후보 종목과 제외 사유 표시
- symbol별 paper/shadow 성과가 분리 저장됨

---

### P2-7. Candidate ranking 개선

구현 항목:

- gross edge
- expected cost
- net EV
- liquidity penalty
- volatility penalty
- spread penalty
- regime score
- strategy confidence
- symbol freshness
- historical paper performance
- shadow comparison
- drawdown penalty

완료 기준:

- candidate scorecard가 fixture성 정적 값이 아니라 실제 runtime evidence 기반으로 계산됨
- ranking_eligible과 live_ready는 계속 분리

---

## P2. Dashboard / UX 개선

### P2-8. 초보자용 3줄 상태 고정

dashboard 최상단에 아래 3줄을 고정한다.

```text
1. 지금 PAPER가 실제로 돌고 있는가
2. LIVE_READY인가
3. 사용자가 지금 할 일은 무엇인가
```

완료 기준:

- 고급 evidence를 보지 않아도 현재 상태 이해 가능
- LIVE_READY false가 명확히 보임
- 사용자가 다음 행동을 혼동하지 않음

---

### P2-9. PAPER runtime 상태 표시

구현 항목:

- running / stopped / stale
- process id
- session id
- last cycle time
- next cycle ETA
- current symbol
- current position
- last decision
- why no trade
- why entry
- blocker
- cash/equity/PnL
- stop method
- log path
- dashboard refresh timestamp

완료 기준:

- dashboard만 보고 PAPER 상태 파악 가능
- 사용자는 코드나 JSON 파일을 직접 열 필요 없음

---

### P2-10. 고급 evidence panel 접기

구현 항목:

- 기본 화면: 운영 상태, PnL, 포지션, LIVE_READY, 다음 행동
- 고급 화면: evidence, hash, schema, blocker chain, scorecard detail
- advanced panel collapse 기본값
- operator-friendly 문장 추가

완료 기준:

- 초보자 기본 화면이 단순함
- 고급 검증 정보는 필요할 때만 펼침

---

## P2. Runtime watchdog / 운영 안정성

### P2-11. 실제 watchdog 구현

구현 항목:

- watchdog process 또는 thread
- last cycle timestamp 감시
- cycle duration 감시
- data feed freshness 감시
- exception count
- retry count
- API latency
- queue backlog
- memory RSS
- disk growth
- artifact count
- stale state fail-closed

완료 기준:

- heartbeat schema만 있는 상태가 아니라 실제 값이 자동 측정됨
- trading loop hang / stale / crash를 감지

---

### P2-12. Retry / backoff / dead-letter queue 구현

구현 항목:

- retry count
- exponential backoff
- retryable vs non-retryable error 분리
- dead-letter queue
- operator report
- idempotency key
- task lease
- ack
- timeout

완료 기준:

- 일시적 오류는 제한적으로 재시도
- 애매한 상태는 fail-closed
- 무한 재시도 없음

---

### P2-13. Resource retention / cleanup 구현

구현 항목:

- log rotation
- max retained cycles
- runtime artifact compaction
- old dashboard snapshot archive
- evidence bundle export
- disk pressure guard
- cleanup dry-run
- cleanup report

완료 기준:

- 장기 실행 시 system/runtime이 무한 증가하지 않음
- cleanup이 source/evidence 정합성을 깨지 않음

---

## P3. Read-only real exchange sync

### P3-1. Upbit READ_ONLY 계좌 동기화

LIVE 이전에 반드시 READ_ONLY부터 구현한다.

구현 항목:

- secret loading policy
- API key permission verification
- withdrawal permission 차단
- read-only balance fetch
- open order fetch
- private websocket 또는 polling fallback
- account snapshot
- reconciliation report
- no order adapter call 유지

완료 기준:

- 실제 계좌 상태를 read-only로 가져올 수 있음
- 주문 권한과 출금 권한이 감지되면 차단
- live flags는 false 유지

---

### P3-2. API key / secret management 정책 구현

구현 항목:

- environment variable 기반 key load
- encrypted local secret option 검토
- no plaintext logging
- key id hash only
- permission check
- withdrawal permission hard blocker
- trade permission은 live unlock 근거가 아님
- key rotation guidance

완료 기준:

- secret이 로그, dashboard, evidence에 노출되지 않음
- read-only 검증과 live trading 권한이 분리됨

---

### P3-3. READ_ONLY burn-in evidence

구현 항목:

- balance freshness
- open order freshness
- private stream health
- polling fallback health
- reconciliation delta
- no order call proof
- burn-in duration
- blocker summary

완료 기준:

- LIVE 검토 전 read-only 안정성 증거가 누적됨
- burn-in 중에도 주문 관련 flag는 false 유지

---

## P3. Emergency protection

### P3-4. Emergency cancel / flatten dry-run 강화

구현 항목:

- cancel all open orders dry-run
- reduce/exit dry-run
- orphan position review
- ledger recording plan
- operator approval field
- idempotency key
- futures reduce-only path
- scope validation

완료 기준:

- 실제 주문 전 dry-run으로 경로와 ledger 계획이 검증됨
- live order 호출은 여전히 없음

---

### P3-5. Actual emergency protection은 micro-live 이후로 유보

원칙:

```text
actual emergency cancel/flatten은 read-only, paper, manual micro order test가 충분히 검증된 뒤에만 구현한다.
```

완료 기준:

- actual live adapter 구현 전까지 dry-run만 허용
- live enabling path와 분리

---

## P4. Profit convergence loop 실전화

### P4-1. Long-run PAPER / SHADOW evidence 확보

구현 항목:

- 최소 120시간 이상 evidence span
- 충분한 paper trade count
- 다양한 regime 포함
- realized PnL 포함
- exit reason 포함
- symbol별 성과 분리
- strategy별 성과 분리
- paper/shadow paired comparison

완료 기준:

- `long_run_evidence_eligible=true`는 실제 장기 증거 충족 후에만 가능
- promotion_eligible은 live와 별도 유지

---

### P4-2. Overfit diagnostic 강화

구현 항목:

- 실제 OOS split
- walk-forward window 분리
- bootstrap confidence interval
- concentration risk
- regime별 성과
- symbol별 성과
- slippage stress test
- fee stress test

완료 기준:

- short-window scaffold가 아니라 장기 evidence 기반 진단
- overfit LOW 판정 근거가 재현 가능

---

### P4-3. 자동 개선 루프 구현

구현 항목:

- parameter mutation
- shadow-only experiment
- paper validation
- realized PnL feedback
- drawdown feedback
- strategy degradation detection
- regime failure detection
- rollback rule
- safe promotion rule
- live와 promotion 분리

완료 기준:

- optimizer ranking이 단순 scorecard가 아니라 실제 파라미터 개선 루프로 연결됨
- 성능 악화 시 rollback 가능

---

## P5. Binance 구현

### P5-1. Binance spot paper 구현

구현 항목:

- Binance spot public market data
- symbol universe
- orderbook depth
- spread
- paper broker
- ledger lifecycle
- portfolio rollup
- dashboard 표시
- live flags false 유지

완료 기준:

- Binance spot PAPER가 Upbit PAPER와 동일 수준의 paper evidence를 생성
- LIVE는 계속 차단

---

### P5-2. Binance futures paper long/short 구현

구현 항목:

- USDT-M futures market data
- hedge mode model
- long/short position model
- isolated/cross margin policy
- leverage 1x default
- funding fee
- liquidation risk
- reduce-only
- futures ledger
- futures portfolio rollup
- short-specific risk guard

완료 기준:

- 실제 futures live 없이 paper long/short만 동작
- liquidation/funding/margin이 paper ledger에 반영됨

---

### P5-3. Binance live는 최후순위

원칙:

```text
Binance live는 spot/futures paper, read-only, reconciliation, emergency dry-run이 모두 닫힌 뒤에만 검토한다.
```

금지:

```text
초기 구현 중 Binance live order adapter 호출
API key loading
private/order endpoint 호출
can_live_trade=true
```

---

## P6. 문서 / 안내서 / 운영 파일 정리

### P6-1. README 실사용 안내 작성

구현 항목:

- 설치 방법
- PAPER 실행 방법
- dashboard 여는 방법
- 중지 방법
- LIVE_READY 해석
- LIVE가 blocked인 이유
- 로그 위치
- 문제 발생 시 확인 순서

완료 기준:

- 초보 사용자가 README만 보고 PAPER 실행과 중지를 이해 가능
- LIVE 실행 가능하다고 오해하지 않음

---

### P6-2. Codex용 구현 backlog 문서 작성

파일 권장:

```text
TRADER_1_IMPLEMENTATION_BACKLOG.md
```

포함 항목:

- P0~P6 backlog
- 금지사항
- acceptance criteria
- test profile
- live safety invariants
- 구현 순서
- 완료 기준

완료 기준:

- Codex가 “계속 진행해”만 받아도 우선순위대로 구현 가능

---

## 13. 전체 구현 순서 요약

권장 순서:

```text
1. P0 evidence/test/package hygiene 복구
2. P1 UPBIT PAPER 장기 runner 구현
3. P1 single-writer / ledger / portfolio 강화
4. P2 전략 / 종목선정 / 비용모델 강화
5. P2 dashboard novice-first 개선
6. P2 watchdog / retention / queue 구현
7. P3 Upbit READ_ONLY sync
8. P4 long-run paper/shadow evidence loop
9. P5 Binance spot paper
10. P5 Binance futures paper
11. Micro-live 검토
12. Controlled live 검토
```

---

## 14. 절대 유지해야 할 안전 invariant

```text
live_order_ready=false
live_order_allowed=false
can_live_trade=false
scale_up_allowed=false
order_adapter_called=false
private_endpoint_called=false
credential_load_attempted=false
live_key_loaded=false
```

위 값은 다음 조건 전까지 절대 true로 바꾸면 안 된다.

```text
장기 PAPER evidence
READ_ONLY burn-in
실계좌 reconciliation
manual micro order test
emergency protection
official API verification
operator approval
live readiness snapshot
```

현재 단계에서는 위 조건이 충족되지 않았다.

---

## 15. 최종 요약

```text
가장 먼저 할 일은 validator를 더 늘리는 것이 아니다.

1. evidence 정합성 실패를 고친다.
2. source/runtime/evidence 패키지 경계를 정리한다.
3. UPBIT_PAPER를 실제 장기 PAPER runner로 만든다.
4. PAPER broker, ledger, portfolio, strategy를 실전형으로 강화한다.
5. dashboard를 초보자 운전석으로 단순화한다.
6. LIVE는 계속 차단한다.
7. Binance는 별도 paper MVP부터 구현한다.
```
