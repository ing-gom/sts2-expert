"""Engine Contribution Score (ECS) — 2차 엔진 기여 정량 지표.
자원 흐름(드로우/에너지) + 순환·압축 + 시너지 페이오프 인에이블(role_needs fan-out)을
정규화·가중합해 카드별 0~100 점수를 만든다. 정적 등급(혼자 센가)과 별개의 축.

산식:
  flow   = 1.5*max(0, 순에너지) + 1.0*드로우     (순에너지 = 획득E − 코스트)
  cycle  = 자기소멸캔트립(+2) + 덱서치(+2) + 소멸생산/압축(+1.5) + 드로우증폭(+1.5)
  enable = Σ(카드 축들의 role_needs 나가는 가중합)  ← 다른 역할에 얼마나 공급하는가
  각 요소를 풀의 95퍼센타일로 0~100 정규화 후 ECS = 0.40*flow + 0.20*cycle + 0.40*enable
검증: Defect 실측 lift와는 의도적으로 무상관(다른 신호) — face validity로 검증.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data')
cards = [c for c in json.load(open(os.path.join(D, 'cards_catalog.json'), encoding='utf-8'))['cards'] if not c['is_upgraded']]
rn = json.load(open(os.path.join(D, 'role_needs.json'), encoding='utf-8'))
fanout = {k: sum(e['w'] for e in v) for k, v in rn.items() if isinstance(v, list)}

W_FLOW, W_CYC, W_EN = 0.40, 0.20, 0.40

def raw(c):
    v = c.get('vars', {}) or {}; axes = c.get('axes', []); cost = c.get('cost', 0)
    energy_gain = v.get('Energy', 0) if ('ENERGY_PRODUCER' in axes or 'ENERGY' in axes) else 0
    net_energy = energy_gain - (cost if (cost and cost > 0) else 0)
    cards_drawn = v.get('Cards', 0)
    flow = 1.5 * max(0, net_energy) + 1.0 * cards_drawn
    cyc = 0.0
    if 'EXHAUST_SELF' in axes and ('DRAW' in axes or cards_drawn > 0): cyc += 2.0
    if 'DRAW_PILE_SEARCH' in axes: cyc += 2.0
    if 'EXHAUST_PRODUCER' in axes: cyc += 1.5
    if 'DRAW_ON_DRAW' in axes or 'DRAW_AMPLIFIER' in axes: cyc += 1.5
    enable = sum(fanout.get(a, 0) for a in axes)
    return flow, cyc, enable

R = {c['id']: raw(c) for c in cards}

def pct(vals, p):
    s = sorted(vals); i = min(len(s) - 1, int(p * len(s))); return max(s[i], 1e-6)
fc = pct([r[0] for r in R.values()], .95); cc = pct([r[1] for r in R.values()], .95); ec = pct([r[2] for r in R.values()], .95)
def norm(x, cap): return min(100.0, 100.0 * x / cap)

out = {'_meta': {'schema': 'sts2-expert/ecs/v1', 'formula': '0.40*flow+0.20*cycle+0.40*enable, each 0-100 (95p-normalized)',
                 'note': '2차 엔진 기여(드로우 순환·자원·시너지 공급). 정적 등급과 별개. Defect lift와 의도적 무상관(다른 신호).',
                 'p95': {'flow': round(fc, 2), 'cycle': round(cc, 2), 'enable': round(ec, 2)}}, 'cards': {}}
for cid, (f, cy, e) in R.items():
    fn, cyn, en = norm(f, fc), norm(cy, cc), norm(e, ec)
    out['cards'][cid] = {'ecs': round(W_FLOW * fn + W_CYC * cyn + W_EN * en, 1),
                         'flow': round(fn, 1), 'cycle': round(cyn, 1), 'enable': round(en, 1)}
json.dump(out, open(os.path.join(D, 'card_engine_contribution.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote data/card_engine_contribution.json :', len(out['cards']), 'cards')
