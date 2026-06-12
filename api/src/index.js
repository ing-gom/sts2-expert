// STS2 Expert — community ratings Worker (Cloudflare Workers + D1)
// Routes:
//   GET  /aggregate           → { ok, items: { "kind:id": {n, avg, dist} } }
//   POST /vote {kind,id,grade,voter,token} → { ok, agg }
// 1 vote per (kind,item,voter); re-voting upserts. Optional Turnstile spam guard.

const GRADES = ['S', 'A', 'B', 'C', 'D'];
const SCORE = { S: 5, A: 4, B: 3, C: 2, D: 1 };

function cors(env) {
  return {
    'Access-Control-Allow-Origin': env.ALLOW_ORIGIN || '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'content-type',
    'Access-Control-Max-Age': '86400',
  };
}
const json = (obj, status, env) =>
  new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { 'content-type': 'application/json; charset=utf-8', ...cors(env) },
  });

// rows: [{kind,item,grade,c}] → { "kind:item": {n, avg, dist} }
function aggFromRows(rows) {
  const items = {};
  for (const r of rows) {
    const key = r.kind + ':' + r.item;
    const it = items[key] || (items[key] = { n: 0, _sum: 0, dist: { S: 0, A: 0, B: 0, C: 0, D: 0 } });
    const c = Number(r.c) || 0;
    it.dist[r.grade] = (it.dist[r.grade] || 0) + c;
    it.n += c;
    it._sum += (SCORE[r.grade] || 0) * c;
  }
  for (const k in items) {
    const it = items[k];
    it.avg = it.n ? +(it._sum / it.n).toFixed(2) : 0;
    delete it._sum;
  }
  return items;
}

async function verifyTurnstile(secret, token, ip) {
  if (!secret) return true;        // not configured → skip (dev/no-captcha)
  if (!token) return false;
  const body = new FormData();
  body.append('secret', secret);
  body.append('response', token);
  if (ip) body.append('remoteip', ip);
  const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body });
  const j = await r.json().catch(() => ({}));
  return !!j.success;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(env) });

    if (url.pathname === '/aggregate' && req.method === 'GET') {
      const { results } = await env.DB.prepare(
        'SELECT kind,item,grade,COUNT(*) AS c FROM votes GROUP BY kind,item,grade'
      ).all();
      return json({ ok: true, items: aggFromRows(results || []) }, 200, env);
    }

    if (url.pathname === '/vote' && req.method === 'POST') {
      let b;
      try { b = await req.json(); } catch { return json({ ok: false, error: 'bad json' }, 400, env); }
      const kind = String(b.kind || '');
      const item = String(b.id || '');
      const grade = String(b.grade || '').toUpperCase();
      const voter = String(b.voter || '').slice(0, 80);
      if (!['cards', 'relics', 'potions'].includes(kind)) return json({ ok: false, error: 'bad kind' }, 400, env);
      if (!item || item.length > 120) return json({ ok: false, error: 'bad item' }, 400, env);
      if (!GRADES.includes(grade)) return json({ ok: false, error: 'bad grade' }, 400, env);
      if (!voter) return json({ ok: false, error: 'no voter' }, 400, env);

      const ip = req.headers.get('cf-connecting-ip') || '';
      const ok = await verifyTurnstile(env.TURNSTILE_SECRET, b.token, ip);
      if (!ok) return json({ ok: false, error: 'turnstile' }, 403, env);

      const ts = Date.now();
      await env.DB.prepare(
        'INSERT INTO votes (kind,item,grade,voter,ts) VALUES (?,?,?,?,?) ' +
        'ON CONFLICT(kind,item,voter) DO UPDATE SET grade=excluded.grade, ts=excluded.ts'
      ).bind(kind, item, grade, voter, ts).run();

      const { results } = await env.DB.prepare(
        'SELECT grade,COUNT(*) AS c FROM votes WHERE kind=? AND item=? GROUP BY grade'
      ).bind(kind, item).all();
      const rows = (results || []).map(r => ({ kind, item, grade: r.grade, c: r.c }));
      const agg = aggFromRows(rows)[kind + ':' + item] || { n: 0, avg: 0, dist: { S: 0, A: 0, B: 0, C: 0, D: 0 } };
      return json({ ok: true, agg }, 200, env);
    }

    return json({ ok: false, error: 'not found' }, 404, env);
  },
};
