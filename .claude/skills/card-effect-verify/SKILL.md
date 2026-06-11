---
name: card-effect-verify
description: STS2 카드의 효과를 description 에서 정확히 읽었는지 검증. axis 라벨이나 카드 이름 추측만으로 finisher/keystone 분류하기 전에 호출. 다수 오류 사례 (ABRASIVE 가시→힘, ACCELERANT "×2 누적"→"×2 발동", REAPER_FORM "자동 부착"→"공격 시 부착", DEFRAGMENT "영구 +1/턴"→"단발 +1") 재발 방지용.
---

> **공개 번들 노트**: 이 스킬은 sts2-expert 공개 레포 번들이다. 데이터 파일은 모두 레포의 `data/` 아래에 있다. 원본 개발 레포 전용 스크립트(ML 재학습 `rebuild_tiers.py`, `build_card_weights.py`, `validate_expected_values.py`, 대시보드 `build_catalog.py` 등)는 이 번들에 포함되지 않는다 — 해당 단계는 건너뛰고, 판정 결과는 리포트로만 산출한다.

# 카드 효과 정확 해석 검증 스킬

빌드 시나리오·keystone 분류·tier 평가 작업 시 카드 description 을 *내가 정확히 읽었는지* 검증하는 절차. axis 라벨이나 STS1 카드 이름 가정으로는 부족 — 실제 description 의 메커니즘을 직접 확인해야 함.

## 호출 트리거

- 새 카드를 keystone/finisher 로 분류 전
- 외부 가이드 (PCGamesN/Mobalytics) tier 와 우리 CSV tier mismatch 확인 시
- 사용자가 "이 카드 효과 X 맞나?" 질문 시
- build_completion.json / scenarios doc 갱신 시 — 카드 효과 인용 부분
- *finisher scenario 작성 시* — "이 카드가 진짜 X 효과를 내는가?" 자동 점검

## 핵심 원칙 (절대 규칙)

### 1. axis 라벨만으로 효과 추정 금지

`CardAxisMap.cs` / `card_axis_overrides.json` 의 axis 는 의미 혼재 가능. 예:
- `["Sly"] = ["CUNNING", "CUNNING_PRODUCER"]` 자동 매핑이 *Sly 키워드 보유 카드* 와 *진짜 Sly 부착 카드* 모두에 같은 라벨
- `SCALING` axis 는 다양한 메커니즘 통합 (영구 +N 누적 vs 단발 +X focus vs 시간 한정)
- `BLOCK_PAYOFF` axis 가 BODY_SLAM (block→damage 변환) 과 BARRICADE (block 영구) 모두 포함

→ axis 매칭만 보지 말고 **반드시 description 직접 읽기**.

### 2. STS1 카드 이름 가정 금지

다수 STS1 클래식 카드가 STS2 에서 다른 의미 또는 다른 강도:
- DEMON_FORM: STS1 S → STS2 C (강등)
- BULLET_TIME: STS1 핵심 keystone → STS2 C (강등)
- LIMIT_BREAK / REAPER / METALLICIZE: STS2 미존재
- SOVEREIGN BLADE: STS2 신규 (STS1 부재)
- SLY 키워드: STS2 신규 메커니즘 (디스카드 시 무료 발동)

이름이 비슷해도 메커니즘은 다를 수 있음. **항상 STS2 description 으로 재검증**.

### 3. mojibake 출력에서 글자 추측 금지

awk 또는 mojibake 된 콘솔 출력에서 한국어 키워드를 추측하다 잘못 짚은 사례 (ABRASIVE 의 [gold]가시[/gold] → "힘" 으로 오해). **반드시 Python `csv + utf-8-sig` + `sys.stdout` 강제 UTF-8** 사용.

```python
python -c "
import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open('data/card_tier_data.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    if r['IsUpgraded']=='False' and r['Id']=='CARD.${ID}':
        print(r['Description'])
        break
"
```

출력에 ??? 또는 깨진 글자 보이면 즉시 멈추고 환경 재설정.

### 4. 메커니즘 분류 4단계 검증

각 카드 description 을 *읽은 후* 다음 4가지 명시:

| 차원 | 질문 |
|---|---|
| **타이밍** | 즉발(play) / turn-start / turn-end / 조건부 / passive? |
| **지속** | 단발 (1턴) / 영구 / 시간 한정 (X턴) / duration? |
| **트리거** | 자동 / 카드 사용 시 / 데미지 받을 시 / 상태 변경 시? |
| **scaling** | 고정 데미지 / 데미지 × N / N 1장당 +M / stack 누적? |

검증 예시:
- DEFRAGMENT: "밀집을 1 얻습니다" → 즉발 / 영구 / 자동 / +1 단발 (매 턴 +1 아님)
- REAPER_FORM: "공격 카드로 피해를 줄 때마다, 그와 동일한 만큼의 종말 부여" → 트리거 (공격 시) / 영구 power / 데미지 1:1
- ACCELERANT: "중독이 1번 추가로 발동" → passive (turn-end) / 영구 power / 추가 발동 (×2 발동, ×2 누적 X)

### 5. 외부 가이드 vs CSV tier mismatch 처리

PCGamesN/Mobalytics 는 메타 평균. 우리 CSV 는 데이터 모델. 둘 다 가치 있는 신호.
- mismatch 발견 시 양쪽 출처 모두 노트 (예: "C 우리 / S 외부")
- description 메커니즘 으로 어느 쪽이 더 정확한지 판단
- 시너지 빌드 가치를 우리 CSV 가 못 잡으면 외부 가이드 따라가는 게 정답

## 자주 헷갈리는 메커니즘 패턴

### A. "추가 발동" vs "추가 누적"

**ACCELERANT**: "중독이 1번 추가로 발동"
- 의미: 한 턴에 중독 발동을 2회 트리거 (stack 4 → 4 dmg + 3 dmg = 7 dmg per turn, stack→2 로 감소)
- 잘못된 해석: "stack 누적이 2배"

**시나리오 작성 정확도**:
- ✓ "중독 한 턴에 2회 발동, stack 빠르게 burn — 한 턴 데미지 ~×1.75, 누적 가속"
- ✗ "stack 2× 누적" (잘못된 표현)

### B. "단발 +N" vs "영구 +N/턴"

**DEFRAGMENT**: "밀집을 1 얻습니다"
- 의미: Power 발동 시 1회 +1 focus. 매 턴 자동 누적 X.
- 잘못된 해석: "매 턴 +1 focus 자동 누적"

**BIASED_COGNITION**: "밀집 4 + 매 턴 시작 시 밀집 1 잃음"
- 의미: 단발 +4 → 4턴 후 0 으로 감쇄

### C. "공격 시 트리거" vs "자동 부착"

**REAPER_FORM**: "공격 카드로 피해를 줄 때마다, 그와 동일한 만큼의 종말 부여"
- 의미: 공격 카드 사용해야 발동. 1코 attack 5 dmg → 종말 5 부여.
- 잘못된 해석: "매 턴 자동 종말 부착"

### D. "scaling 1장당 +N" 패턴 — finisher 후보 다수

| 카드 | 스케일 |
|---|---|
| **PERFECTED_STRIKE** | 6 + 덱 STRIKE 카드 ×2 |
| **FINISHER** | 이번 턴 사용 공격 카드 ×6 |
| **MEMENTO_MORI** | 9 + 이번 턴 버린 카드 ×4 |
| **MURDER** | 1 + 이번 전투 뽑은 카드 ×1 |
| **SOUL_STORM** | 9 + Exhaust pile Soul ×2 |
| **DEATH_MARCH** | 8 + 이번 턴 뽑은 카드 ×3 |
| **BARRAGE** | 영창된 구체 1개 ×5 |
| **SQUEEZE** | 25 + 다른 SKELETON 공격 카드 ×5 |
| **HANG** | 10 + 매달기 카드 같은 적에 ×2 |

이런 카드들은 **conditional scaling finisher** — 빌드 후반 큰 폭딜. finisher scenarios 에 빠짐없이 등록.

### E. "단발 N + 부수 효과" 단발 단일 카드

- **DEVASTATE** (A, 1코): 단발 30 — 단일 보스 빠른 결산
- **METEOR_SHOWER** (S, 0코): AOE 14 + VULN/WEAK 2 — multi-purpose
- **BIG_BANG** (S, 0코): draw 1 + energy 1 + Star 1 + 단조 5 — multi-resource

이런 카드들은 단일 archetype keystone 보다는 *모든 빌드 윤활* 또는 *hybrid bridge* 카드.

### F. "버린 카드 회수" vs "0코 회수" vs "exhaust pile 회수"

세 가지 다른 메커니즘 — description 에서 정확히 구분:
- **HOLOGRAM**: 버린 카드 회수 (discard pile)
- **FERAL**: 매 턴 첫 0코 attack 회수 (사용 직후)
- **REANIMATE**: exhaust pile 회수 (NECROBINDER)

→ "0코 회수 빌드" 는 FERAL + 0코 attack 다수가 핵심. HOLOGRAM 은 *사이클링* 보강.

## 검증 cheatsheet

### 카드 description 빠른 조회

```bash
python -c "
import csv, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open('data/card_tier_data.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    if r['IsUpgraded']=='False' and r['Id']=='CARD.${ID}':
        d = re.sub(r'\[/?[a-z]+\]', '', r['Description']).replace(chr(10),' / ')
        print(f\"[{r['Id']}] tier={r['Tier']} cost={r['Cost']} {r['Type']} | {d}\")
        break
"
```

### scaling finisher 카드 batch 검증

```python
SCALING_KEYWORDS = ['1장당', '1개당', '1번', '횟수', '스택', '카운트']
# description 에 위 키워드 포함 + axes 에 SCALING 또는 attack type — 후보 list 추출
```

### 키워드 의미 검증

`docs/research/keywords_glossary.md` 참조. 모든 키워드의 정확한 mechanic 정리되어 있음.

## 검증 후 산출물

각 카드 분류 시 다음 표 채움:

| 항목 | 값 |
|---|---|
| 카드 ID | CARD.XXX |
| 한국어 이름 | xxx |
| Tier (CSV) | S/A/B/C/D |
| Tier (외부 가이드) | S/A/B/C (mismatch 시 명시) |
| 타이밍 | 즉발 / turn-start / turn-end / passive |
| 지속 | 단발 / 영구 / X턴 |
| 트리거 | 자동 / 카드 사용 시 / 조건 |
| scaling | 고정 / 1장당 +N / stack |
| Description (요약) | 한 줄 |
| 의도된 archetype | XXX |
| Finisher 후보? | yes / no / hybrid |

이 표가 채워지면 keystone/finisher 분류·시너지 평가 신뢰성 ↑.

## 일관성 체크 (build_completion.json 갱신 시 필수)

- [ ] 각 finisher scenario 의 primary card description 직접 읽고 인용 정확
- [ ] axis 라벨에서 추정한 메커니즘 → description 으로 재검증
- [ ] STS1 카드 이름 가정 → STS2 실재 ID 검증
- [ ] mojibake 출력 사용 X (Python UTF-8 강제 사용)
- [ ] scaling 패턴 카드 모두 finisher 후보 검토
- [ ] keywords_glossary.md 와 정합성 체크 (Sly/Doom/Stars/Soul/Forge 등)
