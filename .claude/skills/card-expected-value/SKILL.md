---
name: card-expected-value
description: STS2 카드의 EV (Expected Value, 5-turn baseline dmg equivalent) 측정·갱신. Power self-mechanic / 조건부 / vars 없는 카드의 정적 가치 hand-curated. 신규 카드 추가/게임 업데이트 시 version-bump 스킬에서 호출.
---

> **공개 번들 노트**: 이 스킬은 sts2-expert 공개 레포 번들이다. 데이터 파일은 모두 레포의 `data/` 아래에 있다. 원본 개발 레포 전용 스크립트(ML 재학습 `rebuild_tiers.py`, `build_card_weights.py`, `validate_expected_values.py`, 대시보드 `build_catalog.py` 등)는 이 번들에 포함되지 않는다 — 해당 단계는 건너뛰고, 판정 결과는 리포트로만 산출한다.

# Card Expected Value 스킬

## 목적

`data/card_expected_value.json` 의 EV (Expected Value) 갱신.

EV = **5-turn baseline 의 1-use dmg equivalent**. EffectValueCatalog 가 vars 환산 못 하는 카드 (Power self-mechanic, 조건부, vars 없음) 의 fallback 정적 가치.

## EV 가 필요한 카드

| 카드 종류 | 이유 | 예시 |
|---|---|---|
| **Power 마커 카드** | NamedPower → factor 0 | Inferno (InfernoPower 6), Demon Form (StrengthPower 2 cumulative) |
| **vars 없는 카드** | 환산 식 없음 | Dark Embrace (exhaust 시 draw), Barricade (block 영구) |
| **조건부 카드** | 환산 어려움 | Feel No Pain, Battle Trance |
| **Cumulative scaling** | scaling factor 만으론 부족 | Demon Form, Rolling Boulder |

vars 환산 가능 카드 (Damage/Block/Vuln 등) 는 자동 처리 — EV 정의 불필요.

## EV 계산 식 (5-turn baseline, act2 mid 가정)

### 1. 즉발 효과
```
즉발 effect × 1 use baseline
```
- Inflame: StrengthPower 2 × 5 후속 attacks = **10**
- Crimson Mantle: Block 8 × 1.3 (innate 보강) = **12**

### 2. Cumulative Power (turn마다 누적)
```
stacks × triangular(1+2+...+N) × atks/turn × ½
```
- Demon Form +2/turn × triangular(1+2+3+4)=10 × 4 atk × ½ = **20** (turn 1 적용 지연)
- 권장값: **25** (실측 보정)

### 3. Per-event trigger
```
value × event_count × 5 turn
```
- Afterimage: 1 block × 4 cards/turn × 4 turn = **16**
- Juggernaut: 5 dmg × 4 block plays = **20** (random target ×0.9 = 18)

### 4. Self-damage Power
```
self_damage_per_turn × 5 turn
```
- Inferno: 6 dmg × 5 turn = **30**

### 5. Resource generator (별/orb)
```
resource × per-resource value
```
- Genesis: 5 stars × payoff × 1.5 = **16**
- Big Bang: STAR_BURST 4 stars × consumer 효율 = **14**

### 6. Cost reducer
```
cost_saved × per-cost dmg
```
- Corruption: skill cost 5 절감 × 4 dmg/cost = **20** (보수적)

### 7. 조건부 trigger
```
expected_trigger_count × value
```
- Dark Embrace: 1 draw × 3 exhaust events × 4 dmg eq/draw = **12**
- Feel No Pain: 3 block × 3 exhausts = **9**

### 8. Amplifier (다른 카드 효과 증폭)

**deck 평균 가정** 으로 정적 EV 추정. enabler 부족 deck 에선 *axisDependencyPenalty* 가 별도 차감 — EV 자체는 *최선 가정*.

| Amplifier 종류 | 식 | 예시 |
|---|---|---|
| **VULN_AMPLIFIER** | `bonus × atk_dmg × turns × coverage` | Cruelty: `0.25 × 8 × 5 × 0.6 = 6` (VULN 활성도 60% 가정 → 보강 후 12) |
| **BLOCK_AMPLIFIER** | `block_avg × extra × turns × ratio` | Unmovable: `6 × 1.0 × 5 × 0.83 = 25` (매 턴 첫 카드 ×2) |
| **DAMAGE_AMPLIFIER** | `bonus × atk_dmg × turns × coverage` | DAMAGE_AMPLIFIER 첫 attack ×1.5 → `0.5 × 8 × 5 = 20` (cost 보정 후 ~14~18) |
| **WEAK_AMPLIFIER** | `bonus × enemy_dmg × turns` | `0.25 × 12 × 5 = 15` |
| **POISON_AMPLIFIER** | `bonus × poison stacks × turns` | Accelerant: `1 × 4 × 4 = 16` |
| **SHIV_AMPLIFIER** | `bonus × shiv count` | Accuracy: `4 × 4 = 16` |
| **REPLAY** (Echo Form 1번 더) | `dmg_avg × turns × consume` | `8 × 5 × 0.6 = 24~30` |
| **FORGE_AMPLIFIER** | `forge × value × turns` | Hammer Time `4 × 4 = 16` |
| **CARD_RETURN** + 강화 | `dmg × turns × discard 의존` | Aggression: `8 × 5 × 0.4 = 16` |
| **POWER_AMPLIFIER** | `power_value × extra_uses` | Dual Wield: `7 × 2 = 14` |

**핵심 — Amplifier 의 *coverage* / *deck 매칭율***:
- VULN_AMPLIFIER coverage = deck 의 VULN 부여 카드 의 활성도 (보수: 0.5~0.7)
- BLOCK_AMPLIFIER ratio = "매 턴 발동" 가정 시 0.83 (첫 카드 한정)
- DAMAGE_AMPLIFIER coverage = first attack 가정 시 0.6~0.8

**enabler 부족 시 *EV 자체는 그대로*, axisDependencyPenalty 가 차감** (Stage2Scorer 1.66 의 archetype context multiplier 와 별개 layer).

## 별 cost 보정

REGENT 의 별 cost 카드는 *내부 effective_cost = energy + star × 0.4* (사용자 제안).
EV 측정 시 *별 cost 자체는 EV 식에 영향 X* — 별 cost 는 *Stage2Scorer 의 efficiency multiplier* 에서 별도 처리.

EV 는 **순수 1-use 효과** 만 측정.

## 워크플로우

### Step 1 — 신규/누락 카드 식별

```bash
# 모든 카드 중 vars 환산 0 + EV 미정의 list
python -c "
import json
catalog = json.loads(open('data/cards_catalog.json', encoding='utf-8').read())
expected = json.loads(open('data/card_expected_value.json', encoding='utf-8').read()).get('cards', {})
table = json.loads(open('data/effect_value_table.json', encoding='utf-8').read()).get('table', {})
# vars 환산 안 되는 카드 + EV 미정의
def vars_score(c):
    s = 0
    for var, val in (c.get('vars') or {}).items():
        e = table.get(var, {})
        if e.get('kind') in ('linear','ampl','triangle','scaling','shield'):
            s += val * (e.get('factor', 0) or 0)
    return s
candidates = []
for c in catalog.get('cards', []):
    if c.get('is_upgraded'): continue
    if c.get('rarity') in ('Curse','Status'): continue
    cid = c.get('id', '').removeprefix('CARD.')
    if cid in expected: continue
    if vars_score(c) > 0: continue   # vars 환산 가능 카드 skip
    candidates.append((cid, c.get('character'), c.get('cost'), c.get('axes', [])[:3]))
print(f'EV 측정 후보: {len(candidates)}')
for cid, char, cost, axes in candidates[:30]:
    print(f'  {cid:<24} cost={cost:<3} char={char:<14} axes={axes}')
"
```

### Step 2 — 카드별 EV 계산 (위 식 적용)

각 카드의 mechanic 분석 → 적용 식 선택 → 값 추정.

### Step 3 — JSON 추가

`data/card_expected_value.json` 의 `cards` 안에 추가:

```json
"NEW_CARD": {"value": 18, "basis": "식 설명 — 카드 mechanic 정량화"}
```

선택 — archetype 빌드 활성 시 도달 가능한 현실 상한이 baseline 보다 *현저히 큰* 카드면 `ceiling` 추가 (현재 *기록 전용*):

```json
"DEMON_FORM": {"value": 25, "ceiling": 50, "basis": "5턴 baseline 식", "ceiling_basis": "8턴 boss + 풀 ramp 식"}
```

> **주의 — 현재 ceiling 은 기록만**: 추천 파이프라인 (`Stage2Scorer` / `CardAdvisorService` / `DeckContextAnalyzer`) 은 ceiling 을 소비하지 않고 baseline value 만 사용. 활성도 (archetype 코어 충족율) 측정이 정교해지면 `effective_ev = baseline + activation × (ceiling - baseline)` 형태로 보간 도입 예정. 그 전까지 ceiling 은 향후 reference 자료.

**ceiling 추가 기준**:
- baseline 대비 1.5배 이상 격차가 archetype 활성 시 발생 (cumulative scaling, X-cost, 조건부 페이오프)
- 모든 카드에 추가할 필요 없음 — 천장 효과 미미하면 미정의 (= baseline 만 사용)
- 가정: 8턴 전투, archetype enabler 충족, 빌드 코어 활성

ceiling 비추가가 적절한 케이스:
- 즉발 + cost 무관 카드 (Inflame, Apothecary 강화) — 천장이 baseline 과 거의 동일
- 단발성 burst (Whirlwind 등 X-cost) — vars 가 X 로 환산되므로 별도 ceiling 불필요

### Step 4 — 검증

```bash
python scripts/validate_expected_values.py
```

- Step 1: hand-curated vs mechanic 식 추정 (|diff| ≤ 5 ✓)
- Step 2: anchor_score 와 일관성 (R² 측정)

격차 큰 카드 (|diff| > 5) 는 *식 재검토* 또는 *추정값 조정*.

### Step 5 — 빌드 + 대시보드 재생성

```bash
dotnet build Sts2CardAdvisor.csproj
python scripts/build_catalog.py
```

대시보드 EV 컬럼에 신규 카드 표시 확인.

## 합리성 체크리스트

| 체크 | 기준 |
|---|---|
| EV 단위 | 1-use dmg equivalent (5 turn baseline) |
| 즉발 vs cumulative | cumulative 카드는 triangular sum 또는 누적 |
| cost 부담 | EV 자체는 cost 무관 — Stage2Scorer 가 별도 cost multiplier 적용 |
| 조건부 trigger | expected count × value (확률 ½ ~ ⅔ 곱) |
| 다른 카드 의존 | enabler 부족 시 0 — axisDependencyPenalty 가 별도 페널티 |

## 주의

- **EV 가 너무 크면**: cost 0 + AOE 카드의 *조건부* 페널티 누락 가능 (GRAND_FINALE, COMET 등)
- **EV 가 너무 작으면**: cumulative scaling 누적 효과 누락
- **사용자 피드백 incremental** 으로 미세조정

## 호출 시점

- **version-bump 의 §3 데이터 파일 갱신** 단계에서 신규 Power/조건부 카드 발견 시
- 사용자 피드백으로 *특정 카드 추천 부정확* 보고 시
- ML 티어 자동 판정과 병행 — EV 는 *정적 가치*, tier 는 *상대 ranking*
