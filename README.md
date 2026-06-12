# STS2 Expert — 카드·유물·포션 평가 에이전트 & 카탈로그

슬레이 더 스파이어 2 (Slay the Spire 2, 얼리액세스)의 **카드·유물·포션을 정리하고 평가하는
Claude Code 전문가 에이전트**와, 에이전트가 사용하는 데이터 스냅샷, 그리고 브라우저에서 바로
볼 수 있는 HTML 카탈로그 뷰어를 담은 공개 번들입니다.

**📊 카탈로그 뷰어**: https://ing-gom.github.io/sts2-expert/
— 카드·유물·포션 전 항목에 **S~D 등급 배지**가 표시되며, 등급순 정렬·등급 필터·근거 1줄을 지원합니다.

## 구성

```
.claude/agents/sts2-expert.md     # 평가 전문가 에이전트 (읽기 전용 평가자)
.claude/skills/
  tier-judge/                     # 코스트별 효율 테이블 + 등급 판정 루브릭
  card-expected-value/            # 5턴 EV (Expected Value) 측정 기준
  card-effect-verify/             # description 정독 검증 절차
eval_criteria.md                  # 평가 기준집 (효율·스케일링·신메커니즘·캐릭터 메타)
data/                             # 게임 데이터 스냅샷 (헤드리스 덤프 기반)
index.html                        # 카탈로그 뷰어 (GitHub Pages)
```

## 에이전트 사용법

[Claude Code](https://claude.com/claude-code)가 설치되어 있으면:

```bash
git clone https://github.com/ing-gom/sts2-expert
cd sts2-expert
claude
```

레포 안에서 Claude Code를 열면 `sts2-expert` 에이전트가 자동 등록됩니다. 예시:

```
"sts2-expert 에이전트로 BLOOD_POTION 평가해줘"
"사일런트 레어 카드 전체를 정리·평가해줘"
"Akabeko 유물 어때?"
```

## 평가 원칙

에이전트는 **읽기 전용 평가자**입니다 — 데이터에서 정보를 정리하고 S~D 등급과 근거가 담긴
리포트를 반환하며, 파일을 수정하지 않습니다.

- **단독 판정**: 등급은 카드의 **효과 사실**과 `eval_criteria.md`의 **평가 루브릭**만으로 산정합니다.
  커뮤니티 티어 리스트류의 외부 평가 데이터(`tier`·`score` 필드, 외부 티어 CSV)는 **번들에서 제거**되어
  어떤 단계에서도 조회·인용하지 않습니다. (실측 인과 데이터인 `card_empirical_lift.json`은 "외부 의견"이
  아니라 "측정값"이므로 인용 가능합니다.)
- **정적 vs 맥락 분리**: 정적 등급(천장)과 맥락 등급(덱/시점)을 항상 분리해 평가합니다.
- **평가 기준 갱신**: `eval_criteria.md`는 효율표·스케일링·덱 압축·신규 메커니즘(부식/관통/내구도)·
  조건부 페널티·캐릭터 메타 기준을 담으며, 티어 **값**이 아니라 평가 **방법론·메타**만 반영합니다.

뷰어에 게시된 전 항목 등급은 이 에이전트의 단독 평가 결과(`data/grades.json`)입니다.

## 데이터

| 파일 | 내용 |
|---|---|
| `data/cards_catalog.json` | 카드 마스터 카탈로그 (1,117장, 강화판 포함, `game_version` v0.103.2 — `tier`/`score` 필드 제거됨) |
| `data/grades.json` | **에이전트 단독 S~D 등급** (카드 577·유물 309·포션 64, 등급+맥락+근거 1줄) |
| `data/card_expected_value.json` | 카드 EV — 5턴 baseline 데미지 등가 |
| `data/card_axis_overrides.json` | 명시 축 태그 (Producer/Consumer/Amplifier/Trigger) |
| `data/card_empirical_lift.json` | 풀런 실측 기반 카드 인과 lift (외부 의견 아님) |
| `data/role_needs.json` | 축 간 시너지 방향/가중치 |
| `data/build_completion.json` | 캐릭터·아키타입별 keystone 정의 |
| `data/effect_value_table.json` | 효과 종류별 가치 환산 테이블 |
| `data/axis_labels_ko.json` | 축 한국어 레이블 |
| `data/relics_locale.json` | 유물 309종 ko/en/zh 이름+설명 (`game_version` v0.103.3) |
| `data/relic_canonical_vars.json` | 유물 placeholder 실수치 (게임 DLL 추출 상수) |
| `data/relic_axis_overrides.json` | 유물 → 카드 축 시너지 매핑 |
| `data/potions.json` | 포션 64종 — ko/en/zh 이름·설명 + Rarity/Usage/Target + **placeholder 실수치**(헤드리스 덤프) + 큐레이션 분류 (`game_version` v0.103.3) |

> 컴포넌트별로 덤프 버전이 다릅니다 — 카드는 안정 스냅샷 v0.103.2, 유물·포션은 v0.103.3.

## 뷰어 로컬 실행

`index.html`은 `data/*.json`을 fetch하므로 `file://`로는 열리지 않습니다:

```bash
python -m http.server 8000
# http://localhost:8000
```

## 라이선스 / 고지

비공식 팬 프로젝트입니다. 게임 데이터의 권리는 Mega Crit에 있습니다.
얼리액세스 특성상 데이터 스냅샷이 최신 게임 밸런스와 다를 수 있습니다.
도구 코드(에이전트/스킬/뷰어)는 MIT 라이선스입니다.
