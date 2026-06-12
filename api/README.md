# STS2 Expert — community ratings backend

뷰어(`index.html`)에 "전문가 등급 + 커뮤니티 평점"을 붙이기 위한 서버리스 백엔드.
**Cloudflare Workers + D1**(둘 다 무료 티어로 충분), 스팸 방어는 **Turnstile**(무료).

정적 사이트(GitHub Pages)는 그대로 두고, 이 Worker 에 cross-origin `fetch` 만 한다.
`index.html` 의 `COMMUNITY.apiBase` 가 비어 있으면 평점 기능 전체가 꺼져 사이트는 기존과 동일하게 동작한다.

## 데이터 모델

`votes(kind, item, grade, voter, ts)` — `(kind,item,voter)` 가 PK 라 한 사람이 한 항목에 1표(재투표는 덮어씀). `kind ∈ {cards,relics,potions}`, `grade ∈ {S,A,B,C,D}`. 평균은 S=5…D=1 로 환산.

## API

- `GET /aggregate` → `{ ok, items: { "cards:CARD.X": { n, avg, dist:{S,A,B,C,D} }, ... } }`
- `POST /vote` body `{ kind, id, grade, voter, token }` → `{ ok, agg:{n,avg,dist} }`

## 배포 (한 번만)

> `wrangler login` 등 계정 인증은 직접 실행해야 한다. Claude Code 세션이면 프롬프트에
> `! wrangler login` 처럼 `!` 접두로 실행하면 출력이 대화에 들어온다.

```bash
npm install -g wrangler          # 또는 npx wrangler ...
cd api
wrangler login

# 1) D1 생성 → 출력된 database_id 를 wrangler.toml 의 REPLACE_... 자리에 붙여넣기
wrangler d1 create sts2_expert_votes

# 2) 스키마 적용 (원격 D1)
wrangler d1 execute sts2_expert_votes --remote --file=./schema.sql

# 3) (권장) Turnstile 위젯 생성: dashboard → Turnstile → Add site
#    - Site Key  : index.html 의 COMMUNITY.turnstileSiteKey 에 넣는다(공개값)
#    - Secret Key: 아래로 Worker 에 주입(비공개)
wrangler secret put TURNSTILE_SECRET

# 4) 배포 → 출력된 https://sts2-expert-api.<subdomain>.workers.dev 를 복사
wrangler deploy
```

## 프론트 연결

`index.html` 상단 `COMMUNITY` 설정 두 줄을 채우고 커밋:

```js
const COMMUNITY = {
  apiBase: 'https://sts2-expert-api.<subdomain>.workers.dev',  // ← wrangler deploy 출력
  turnstileSiteKey: '0x4AAAAAAA...',                           // ← Turnstile Site Key (없으면 '' → 캡차 생략)
  ...
};
```

`ALLOW_ORIGIN` 은 `wrangler.toml` 에서 사이트 origin(`https://ing-gom.github.io`)으로 제한돼 있다. 커스텀 도메인이면 그 값으로 바꿔 재배포.

## 운영 메모

- 1인1표는 localStorage UUID 기반(가벼운 중복 방지) + Turnstile(봇 차단)의 조합 — 완전한 신원 보증은 아니다(계정 없음). 취미 규모엔 충분.
- 무료 티어: Workers 100k req/day, D1 넉넉, Turnstile 무료.
- 표 데이터 확인: `wrangler d1 execute sts2_expert_votes --remote --command "SELECT kind,item,grade,COUNT(*) FROM votes GROUP BY 1,2,3"`
