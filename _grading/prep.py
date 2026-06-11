"""채점 입력 준비: 모든 카드/유물/포션의 설명을 깨끗한 텍스트로 렌더해 청크 파일로 쓴다.
sts2-expert 워크플로우 에이전트가 각 청크 파일을 읽어 등급을 매긴다."""
import json, re, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, '_grading')
os.makedirs(OUT, exist_ok=True)

# ---- SmartFormat-lite (index.html smartFormat의 검증된 Python 미러) ----
def fm(s, i):
    d = 0
    while i < len(s):
        if s[i] == '{': d += 1
        elif s[i] == '}':
            d -= 1
            if d == 0: return i
        i += 1
    return -1
def split_top(s):
    out=[]; d=0; cur=''
    for ch in s:
        if ch=='{': d+=1; cur+=ch
        elif ch=='}': d-=1; cur+=ch
        elif ch=='|' and d==0: out.append(cur); cur=''
        else: cur+=ch
    out.append(cur); return out
def num(v):
    try:
        f=float(v); return str(int(f)) if f.is_integer() else str(v)
    except: return str(v)
def truthy(v):
    if v is None: return False
    if isinstance(v,str): return v.strip()!=''
    try: return float(v)!=0
    except: return bool(v)
def base(n): return n.split('.')[0]
def lookup(name,vars,strv):
    b=base(name)
    if b in strv: return strv[b]
    if b in vars: return num(vars[b])
    return '{'+name+'}'
def render(s,vars,strv):
    out=''; i=0
    while i<len(s):
        if s[i]=='{':
            j=fm(s,i)
            if j<0: out+=s[i]; i+=1; continue
            out+=tok(s[i+1:j],vars,strv); i=j+1
        else: out+=s[i]; i+=1
    return out
def tok(inner,vars,strv):
    if inner=='singleStarIcon': return '별'
    if inner=='': return ''
    ci=inner.find(':')
    if ci<0: return lookup(inner,vars,strv)
    name=inner[:ci]; rest=inner[ci+1:]
    m=re.match(r'(\w+)',rest); fmtr=m.group(1) if m else ''; rest=rest[len(fmtr):]
    args=''
    if rest.startswith('('):
        d=0
        for idx,c in enumerate(rest):
            if c=='(':d+=1
            elif c==')':
                d-=1
                if d==0: args=rest[1:idx]; rest=rest[idx+1:]; break
    options=rest[1:] if rest.startswith(':') else ''
    b=base(name); ctrl=vars.get(b); sctrl=strv.get(b)
    if fmtr in ('diff','inverseDiff','percentMore'): return lookup(name,vars,strv)
    if fmtr=='energyIcons':
        n=int(float(ctrl)) if ctrl is not None else (int(args) if args.strip().isdigit() else 1)
        return '%d에너지'%n
    if fmtr=='starIcons':
        n=int(float(ctrl)) if ctrl is not None else (int(args) if args.strip().isdigit() else 1)
        return '별%d'%n
    if fmtr in ('choose','plural','cond'):
        opts=split_top(options); cv=sctrl if sctrl is not None else ctrl
        if fmtr=='cond': pick=opts[0] if truthy(cv) else (opts[1] if len(opts)>1 else '')
        elif fmtr=='plural': pick=opts[0] if (ctrl is not None and float(ctrl)==1) else (opts[-1] if opts else '')
        else:
            a=args.strip()
            if a in ('1',''): pick=opts[0] if (ctrl is not None and float(ctrl)==1) else opts[-1]
            else:
                keys=a.split('|'); pick=opts[0]
                if cv is not None and str(cv) in keys:
                    pi=keys.index(str(cv));
                    if pi<len(opts): pick=opts[pi]
        rep=sctrl if sctrl is not None else (num(ctrl) if ctrl is not None else '')
        pick=pick.replace('{}',str(rep)); return render(pick,vars,strv)
    if fmtr=='show':
        opts=split_top(options); return render(opts[0] if opts else '',vars,strv)
    return lookup(name,vars,strv)

def strip_markup(s):
    # [gold]X[/gold] 등 색 태그 제거(내용 유지), 줄바꿈 정리
    s = re.sub(r'\[/?\w+\]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def clean(desc, vars, strv):
    return strip_markup(render(desc or '', vars or {}, strv or {}))

def lang_strv(svObj):
    out={}
    if svObj:
        for k,d in svObj.items(): out[k]=(d.get('ko') or '')
    return out

# ---- load ----
cards=json.load(open(os.path.join(D,'cards_catalog.json'),encoding='utf-8'))
ev=json.load(open(os.path.join(D,'card_expected_value.json'),encoding='utf-8')).get('cards',{})
rl=json.load(open(os.path.join(D,'relics_locale.json'),encoding='utf-8'))['relics']
cv=json.load(open(os.path.join(D,'relic_canonical_vars.json'),encoding='utf-8'))
rvars=cv['relics']; rstrv=cv.get('string_vars',{})
rax=json.load(open(os.path.join(D,'relic_axis_overrides.json'),encoding='utf-8')).get('explicit',{})
po=json.load(open(os.path.join(D,'potions.json'),encoding='utf-8'))['potions']

manifest=[]
def write_chunk(cat, name, items):
    fn=os.path.join(OUT, name+'.json')
    json.dump(items, open(fn,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    manifest.append({'category':cat,'file':name+'.json','count':len(items)})

# cards (base only) by character
bychar={}
for c in cards['cards']:
    if c['is_upgraded']: continue
    item={
        'id':c['id'],'name':c['title'],'cost':c['cost'],'star_cost':c.get('star_cost',0),
        'type':c['type'],'rarity':c['rarity'],'character':c['character'],
        'axes':c.get('axes',[]),'builds':[b['tag'] for b in c.get('builds',[])],
        'desc':strip_markup(c.get('description','')),
    }
    e=ev.get(c['id'].replace('CARD.',''))
    if e and e.get('value') is not None: item['ev']=e['value']
    bychar.setdefault(c['character'],[]).append(item)
for ch,items in bychar.items():
    if len(items)>90:  # SHARED 138 → 2분할
        h=len(items)//2
        write_chunk('cards', f'cards_{ch}_a', items[:h])
        write_chunk('cards', f'cards_{ch}_b', items[h:])
    else:
        write_chunk('cards', f'cards_{ch}', items)

# relics → 4 chunks
relic_items=[]
for k in sorted(rl):
    r=rl[k]
    item={'id':k,'name':r['name'].get('ko') or k,
          'desc':clean(r['desc'].get('ko',''), rvars.get(k,{}), lang_strv(rstrv.get(k))),
          'vars':rvars.get(k,{})}
    if k in rax: item['card_axes']=rax[k].get('card_axes',[])
    relic_items.append(item)
N=4; per=(len(relic_items)+N-1)//N
for i in range(N):
    chunk=relic_items[i*per:(i+1)*per]
    if chunk: write_chunk('relics', f'relics_{i:02d}', chunk)

# potions → 1 chunk
potion_items=[]
for tn in sorted(po):
    p=po[tn]
    sv={k:(d.get('ko') or '') for k,d in p.get('string_vars',{}).items()}
    potion_items.append({'id':tn,'name':p['name'].get('ko') or tn,
        'desc':clean(p['desc'].get('ko',''), p.get('vars',{}), sv),
        'rarity':p.get('rarity',''),'usage':p.get('usage',''),'target':p.get('target',''),
        'vars':p.get('vars',{}),'kind':p.get('kind',''),'category':p.get('category','')})
write_chunk('potions','potions', potion_items)

json.dump(manifest, open(os.path.join(OUT,'_manifest.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('chunks:', len(manifest))
for m in manifest: print(' ', m['file'], m['count'])
print('\n=== 샘플 ===')
print('card:', json.dumps(bychar['SILENT'][0], ensure_ascii=False)[:300])
print('relic:', json.dumps(relic_items[0], ensure_ascii=False)[:200])
print('potion:', json.dumps(potion_items[0], ensure_ascii=False)[:200])
