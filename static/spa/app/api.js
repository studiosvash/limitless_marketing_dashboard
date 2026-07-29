/* ============================================================================
   FuseAPI — the ONLY way the frontend talks to data.
   ----------------------------------------------------------------------------
   - FuseAPI.config.baseUrl = null  → fixture mode (app/fixtures.js) with
     simulated latency, task-based syncs, and localStorage-persisted mutations.
   - FuseAPI.config.baseUrl = 'https://…' → every call becomes a real fetch()
     against the Django backend implementing API_CONTRACT.md. Nothing else in
     the frontend changes.
   ============================================================================ */
window.FuseAPI = (function () {
  'use strict';

  const config = { baseUrl: null, authToken: null, minLatency: 160, maxLatency: 420 };
  const LS_KEY = 'fuse.mutations.v1';

  /* ---------- persisted demo mutations (replaced by real DB later) ---------- */
  function loadMut() {
    try { return JSON.parse(localStorage.getItem(LS_KEY)) || {}; } catch (e) { return {}; }
  }
  function saveMut(m) { try { localStorage.setItem(LS_KEY, JSON.stringify(m)); } catch (e) {} }
  function mut(path, fallback) {
    const m = loadMut();
    return path.split('.').reduce((o, k) => (o && o[k] != null ? o[k] : undefined), m) ?? fallback;
  }
  function setMut(path, val) {
    const m = loadMut();
    const keys = path.split('.');
    let o = m;
    keys.slice(0, -1).forEach(k => { if (typeof o[k] !== 'object' || o[k] == null) o[k] = {}; o = o[k]; });
    o[keys[keys.length - 1]] = val;
    saveMut(m);
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  async function latency() {
    await sleep(config.minLatency + Math.random() * (config.maxLatency - config.minLatency));
  }

  /* ---------- real-backend transport ---------- */
  async function http(method, path, params, body) {
    const url = new URL(config.baseUrl.replace(/\/$/, '') + path, location.origin);
    if (params) Object.entries(params).forEach(([k, v]) => { if (v != null) url.searchParams.set(k, v); });
    const headers = { 'Content-Type': 'application/json' };
    if (config.authToken) headers['Authorization'] = 'Bearer ' + config.authToken;
    const res = await fetch(url, {
      method,
      headers,
      credentials: 'include',
      body: body ? JSON.stringify(body) : undefined
    });
    if (!res.ok) {
      let detail = 'API ' + res.status + ' ' + path;
      try { const j = await res.json(); if (j.detail) detail = j.detail; } catch (e) {}
      const err = new Error(detail);
      err.detail = detail;
      err.status = res.status;
      throw err;
    }
    /* 204 No Content has no body, so res.json() throws
       "Failed to execute 'json' on 'Response': Unexpected end of JSON input" -- and because
       that throw happens AFTER the server has already done the work, the caller reports a
       failure for an operation that actually succeeded. Every DELETE in this API returns 204
       (DELETE /projects/<slug>, DELETE /projects/<slug>/data), so both the Danger-zone
       "Delete this project" and "Clear data" hit it.
       205 and 304 are equally body-less; a Content-Length of 0 covers any endpoint that
       returns 200 with an empty body. */
    if (res.status === 204 || res.status === 205 || res.status === 304) return null;
    if (res.headers.get('content-length') === '0') return null;
    const text = await res.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (e) {
      /* A 2xx that is genuinely not JSON. Surface what came back rather than the opaque
         parser message, which named neither the endpoint nor the payload. */
      const err = new Error('Server returned a non-JSON response for ' + path);
      err.detail = 'Server returned a non-JSON response for ' + path;
      err.status = res.status;
      err.body = text.slice(0, 200);
      throw err;
    }
  }

  /* ---------- fixture routing ---------- */
  const F = () => window.FuseFixtures;

  function rangeDays(range) { return range === '7d' ? 7 : range === '90d' ? 90 : 30; }

  function mergedKeywords(fix) {
    const added = mut('added.' + fix.project.id, []);
    return fix.keywords.concat(added);
  }

  function overview(fix, range) {
    const n = rangeDays(range);
    const s = fix.series;
    const cur = s.slice(-n), prev = s.slice(-(n * 2), -n);
    const sum = (arr, k) => arr.reduce((a, x) => a + x[k], 0);
    const clicks = sum(cur, 'clicks'), pClicks = Math.max(1, sum(prev, 'clicks'));
    const impr = sum(cur, 'impressions'), pImpr = Math.max(1, sum(prev, 'impressions'));
    const kws = mergedKeywords(fix);
    const avgPos = +(kws.reduce((a, k) => a + k.pos, 0) / kws.length).toFixed(1);
    const prevAvg = +(kws.reduce((a, k) => a + (k.prevPos || k.pos), 0) / kws.length).toFixed(1);
    const ctr = +((clicks / impr) * 100).toFixed(1);
    const pct = (a, b) => +(((a - b) / b) * 100).toFixed(1);

    const gone = fix.pages.filter(p => p.kind === 'gone');
    const lowCtr = fix.pages.filter(p => p.kind === 'ok' && p.impressions >= 100 && p.ctr < 2);
    const quickWins = kws.filter(k => k.pos >= 4 && k.pos <= 10 && k.clicks > 0);

    const signals = [];
    if (pct(clicks, pClicks) > 2) signals.push({ type: 'positive', title: 'Organic clicks trending up', detail: 'Clicks up ' + pct(clicks, pClicks) + '% vs. previous ' + n + ' days.' });
    else signals.push({ type: 'negative', title: 'Organic clicks flat or down', detail: 'Clicks ' + pct(clicks, pClicks) + '% vs. previous ' + n + ' days — review recent ranking losses.' });
    if (gone.length) signals.push({ type: 'negative', title: gone.length + ' page(s) returning 404', detail: 'Broken pages still receiving impressions and backlinks.' });
    if (lowCtr.length) signals.push({ type: 'opportunity', title: 'Low-CTR opportunity', detail: lowCtr.length + ' pages get impressions but under 2% CTR — rewrite titles.' });
    if (quickWins.length) signals.push({ type: 'opportunity', title: quickWins.length + ' quick-win keywords', detail: 'Ranking #4–10 with real clicks — a small push reaches top 3.' });

    const topPages = fix.pages.filter(p => p.kind === 'ok').sort((a, b) => b.clicks - a.clicks).slice(0, 6)
      .map(p => ({ url: p.url, clicks: p.clicks, impressions: p.impressions, ctr: p.ctr }));

    /* ---- command-center rollups: module summaries + cross-module priority feed ---- */
    const fmt = n => n == null ? '—' : (Math.abs(n) >= 1000 ? +(n / 1000).toFixed(1) + 'k' : String(n));
    const rangeKey = range === '7d' ? '7d' : range === '90d' ? '90d' : '30d';

    /* pull the module views so the overview matches each screen exactly */
    let adsRoll = null, aiRoll = null, auditRoll = null;
    try { adsRoll = adsView(fix, range); } catch (e) {}
    try { aiRoll = aiView(fix); } catch (e) {}
    try { auditRoll = auditView(fix); } catch (e) {}

    const audit = fix.audit;
    const snaps = audit.snapshots || [];
    const scorePrev = snaps.length >= 2 ? snaps[snaps.length - 2].score : audit.score;
    const scoreDelta = audit.score - scorePrev;
    const auditErrors = auditRoll ? auditRoll.totals.errors : 0;
    const auditHealthy = audit.breakdown ? audit.breakdown.healthy : 0;

    /* backlinks weekly new / lost, computed from firstSeen / lostAt */
    const nowMs = Date.now(), WK = 7 * 864e5;
    const tms = d => d ? new Date(d).getTime() : 0;
    const blLive = fix.backlinks.filter(b => b.status === 'live').length;
    const blNew = fix.backlinks.filter(b => tms(b.firstSeen) && nowMs - tms(b.firstSeen) <= WK).length;
    const blLost = fix.backlinks.filter(b => tms(b.lostAt) && nowMs - tms(b.lostAt) <= WK).length;

    const top3 = kws.filter(k => k.pos <= 3).length;
    const declined = kws.filter(k => k.prevPos && k.pos - k.prevPos >= 2).length;
    const improved = kws.filter(k => k.prevPos && k.prevPos - k.pos >= 2).length;
    const aiSetup = !!(aiRoll && aiRoll.setupDone);
    const aiSov = aiRoll && aiRoll.sov ? aiRoll.sov : null;

    const pillars = [
      { label: 'Organic clicks', target: 'overview', valueKind: 'num', value: clicks, delta: pct(clicks, pClicks), deltaUnit: '%', sub: 'clicks · ' + rangeKey },
      { label: 'Avg. position', target: 'positioning', valueKind: 'pos', value: avgPos, delta: +(prevAvg - avgPos).toFixed(1), deltaUnit: 'pos', sub: top3 + ' keywords in top 3' },
      { label: 'Site health', target: 'pages', valueKind: 'score', value: audit.score, delta: scoreDelta, deltaUnit: 'pts', sub: auditErrors + ' errors to fix' },
      { label: 'Paid ROAS', target: 'ads', valueKind: 'roas', value: adsRoll ? adsRoll.totals.roas : null, delta: null, sub: adsRoll ? ('$' + fmt(Math.round(adsRoll.totals.spend)) + ' spend · ' + adsRoll.pacing.pct + '% of budget') : null },
      { label: 'AI visibility', target: 'ai', valueKind: 'pct', value: aiSetup && aiSov ? aiSov.you : null, delta: aiSetup && aiSov ? aiSov.delta : null, deltaUnit: 'pts', state: aiSetup ? 'ok' : 'setup', sub: aiSetup ? 'share of AI answers' : 'not set up yet' }
    ];

    const modules = [
      { label: 'SEO Performance', target: 'seo', stat: fmt(clicks) + ' clicks', sub: lowCtr.length + ' low-CTR · ' + gone.length + ' broken', tone: gone.length ? 'bad' : (lowCtr.length ? 'warn' : 'ok') },
      { label: 'Keywords', target: 'keywords', stat: kws.length + ' tracked', sub: top3 + ' in top 3 · ' + quickWins.length + ' quick wins', tone: 'ok' },
      { label: 'Position Tracking', target: 'positioning', stat: '#' + avgPos + ' avg', sub: '▲' + improved + ' up · ▼' + declined + ' down', tone: declined > improved ? 'warn' : 'ok' },
      { label: 'Backlinks', target: 'backlinks', stat: fmt(blLive) + ' live', sub: '+' + blNew + ' new · −' + blLost + ' lost (7d)', tone: blLost > blNew ? 'warn' : 'ok' },
      { label: 'Site Audit', target: 'pages', stat: audit.score + '/100', sub: auditErrors + ' errors · ' + auditHealthy + ' healthy', tone: auditErrors > 0 ? 'bad' : 'ok' },
      { label: 'AI Optimization', target: 'ai', stat: aiSetup && aiSov ? aiSov.you + '% SOV' : 'Not set up', sub: aiSetup && aiRoll.kpis ? (aiRoll.kpis.prompt_coverage.cited + '/' + aiRoll.kpis.prompt_coverage.total + ' prompts cited') : 'Track ChatGPT, Claude, Gemini', tone: aiSetup ? 'ok' : 'setup' },
      { label: 'Paid Media', target: 'ads', stat: adsRoll ? ('$' + fmt(Math.round(adsRoll.totals.spend))) : '—', sub: adsRoll ? (adsRoll.totals.roas + '× ROAS · ' + adsRoll.pacing.pct + '% budget') : '', tone: adsRoll && adsRoll.pacing.pct >= 100 ? 'warn' : 'ok' }
    ];

    /* priority feed = unacknowledged alerts, tagged with their owning module */
    const kindMap = {
      anomaly: { label: 'SEO', target: 'seo' }, ranking: { label: 'Positions', target: 'positioning' },
      backlink: { label: 'Backlinks', target: 'backlinks' }, technical: { label: 'Site Audit', target: 'pages' },
      ads: { label: 'Ads', target: 'ads' }, system: { label: 'System', target: 'alerts' }
    };
    const sevRank = { high: 0, medium: 1, info: 2 };
    const ackMap = mut('ack', {});
    const priority = fix.feed
      .filter(f => !ackMap[f.id])
      .sort((a, b) => (sevRank[a.severity] - sevRank[b.severity]) || (a.ts < b.ts ? 1 : -1))
      .slice(0, 6)
      .map(f => ({ id: f.id, severity: f.severity, kind: f.kind, title: f.title, detail: f.detail, ts: f.ts, module: kindMap[f.kind] || { label: 'General', target: 'alerts' } }));

    return {
      kpis: [
        { label: 'Total clicks', value: clicks, delta: pct(clicks, pClicks), unit: '%' },
        { label: 'Impressions', value: impr, delta: pct(impr, pImpr), unit: '%' },
        { label: 'Avg. position', value: avgPos, delta: +(prevAvg - avgPos).toFixed(1), unit: 'pos' },
        { label: 'CTR', value: ctr, delta: null, unit: '%' }
      ],
      pillars, modules, priority,
      signals: signals.slice(0, 3),
      trend: cur,
      summary: {
        wins: ['Organic clicks ' + (pct(clicks, pClicks) >= 0 ? 'up ' : 'down ') + Math.abs(pct(clicks, pClicks)) + '% vs. previous period, led by ' + (topPages[0] ? topPages[0].url : 'top pages') + '.'],
        critical: gone.length ? [gone.length + ' URL(s) returning 404 — still linked externally: ' + gone.map(g => g.url).join(', ')] : [],
        watch: [quickWins.length + ' keywords sit at #4–10; ' + lowCtr.length + ' pages have <2% CTR despite impressions.']
      },
      topPages
    };
  }

  function seoView(fix) {
    const kws = mergedKeywords(fix);
    const lowCtrPages = fix.pages.filter(p => p.kind === 'ok' && p.impressions >= 100 && p.ctr < 2)
      .sort((a, b) => b.impressions - a.impressions);
    const anomalies = fix.feed.filter(f => f.kind === 'anomaly').map(f => ({
      id: f.id, metric: /click/i.test(f.title) ? 'Clicks' : 'Impressions',
      severity: f.severity, deviation: (f.title.match(/[-+]?\d+%/) || [/./.test(f.title) && (f.title.includes('drop') ? '-38%' : '+22%')])[0], date: f.ts, detail: f.detail
    }));
    return {
      kpis: {
        low_ctr: lowCtrPages.length,
        anomalies: anomalies.length,
        critical: fix.pages.filter(p => p.kind === 'gone').length,
        total_issues: fix.pages.filter(p => p.kind !== 'ok').length + anomalies.length + lowCtrPages.length
      },
      lowCtrPages: lowCtrPages.map(p => ({ url: p.url, impressions: p.impressions, clicks: p.clicks, ctr: p.ctr, avg_pos: +(6 + (F().hashStr(p.url) % 90) / 10).toFixed(1) })),
      countries: fix.countries,
      anomalies,
      quickWinKws: kws.filter(k => k.pos >= 4 && k.pos <= 10 && k.clicks > 0).length
    };
  }

  function keywordsView(fix) {
    const kws = mergedKeywords(fix);
    const seg = {
      quick_wins: kws.filter(k => k.pos >= 4 && k.pos <= 10 && k.clicks > 0).map(k => k.id),
      striking: kws.filter(k => k.pos >= 11 && k.pos <= 20).map(k => k.id),
      declining: kws.filter(k => k.prevPos && k.pos - k.prevPos >= 2).map(k => k.id),
      low_ctr: kws.filter(k => k.impressions >= 100 && k.ctr < 2).map(k => k.id)
    };
    return {
      kpis: {
        total: kws.length,
        avg_pos: +(kws.reduce((a, k) => a + k.pos, 0) / kws.length).toFixed(1),
        total_volume: kws.reduce((a, k) => a + k.volume, 0),
        total_clicks: kws.reduce((a, k) => a + k.clicks, 0)
      },
      intents: {
        informational: kws.filter(k => k.intent === 'informational').length,
        commercial: kws.filter(k => k.intent === 'commercial').length,
        transactional: kws.filter(k => k.intent === 'transactional').length,
        navigational: kws.filter(k => k.intent === 'navigational').length
      },
      difficulty: {
        easy: kws.filter(k => k.kd < 30).length,
        medium: kws.filter(k => k.kd >= 30 && k.kd < 60).length,
        hard: kws.filter(k => k.kd >= 60).length
      },
      segments: seg,
      keywords: kws
    };
  }

  function positionsView(fix) {
    const kws = mergedKeywords(fix);
    const dist = {
      top3: kws.filter(k => k.pos <= 3).length,
      p4_10: kws.filter(k => k.pos >= 4 && k.pos <= 10).length,
      p11_20: kws.filter(k => k.pos >= 11 && k.pos <= 20).length,
      p21_100: kws.filter(k => k.pos > 20).length
    };
    return {
      kpis: {
        tracked: kws.length,
        avg_pos: +(kws.reduce((a, k) => a + k.pos, 0) / kws.length).toFixed(1),
        est_traffic: kws.reduce((a, k) => a + k.clicks, 0),
        impressions: kws.reduce((a, k) => a + k.impressions, 0)
      },
      distribution: dist,
      movement: {
        improved: kws.filter(k => k.prevPos && k.prevPos - k.pos >= 2).length,
        declined: kws.filter(k => k.prevPos && k.pos - k.prevPos >= 2).length,
        added: kws.filter(k => !k.prevPos || k.source === 'manual').length,
        lost: 2
      },
      competitors: { domains: fix.project.competitors, rows: fix.compRows },
      movers: kws.filter(k => k.prevPos && Math.abs(k.pos - k.prevPos) >= 2)
        .sort((a, b) => Math.abs(b.pos - b.prevPos) - Math.abs(a.pos - a.prevPos)).slice(0, 8)
    };
  }

  function backlinksView(fix) {
    const links = fix.backlinks;
    const live = links.filter(l => l.status === 'live');
    const domains = [...new Set(links.map(l => l.domain))];

    /* ---- rich Backlink Analytics dataset ----
       Maps to DataForSEO Backlinks API:
         summary        → backlinks/summary (rank, referring_domains, backlinks count, broken, spam)
         months[]       → backlinks/history (new/lost referring domains, 24 mo)
         types[]        → backlinks/summary referring_links_types
         asBuckets[]    → backlinks/referring_domains grouped by rank band
         refDomains[]   → backlinks/referring_domains (Live)
         anchors[]      → backlinks/anchors
         gap/competitors→ backlinks/domain_intersection (this domain vs competitors)
       Deterministic per-domain generator stands in until the connector is live. */
    const target = fix.project.domain;
    const hashStr = s => { let h = 1779033703 ^ s.length; for (let i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); } return function () { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; }; };
    const R = hashStr('bl:' + target);
    const authorityScore = 30 + Math.floor(R() * 30);
    const refDomainsCount = Math.max(domains.length, 600 + Math.floor(R() * 1400));
    const backlinksCount = refDomainsCount * (5 + Math.floor(R() * 8));
    const dofollowPct = 62 + Math.floor(R() * 22);
    const broken = 20 + Math.floor(R() * 90);
    const spamScore = 2 + Math.floor(R() * 8);
    const newRdMonth = 20 + Math.floor(R() * 60);
    const mn = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    const months = [];
    for (let i = 0; i < 24; i++) {
      const rr = hashStr('m:' + target + i);
      const dt = new Date(2024, 6 + i, 1);
      months.push({ label: mn[dt.getMonth()] + " '" + String(dt.getFullYear()).slice(2), nw: 15 + Math.floor(rr() * 70), lost: 8 + Math.floor(rr() * 45) });
    }

    const typesRaw = [
      { key: 'text', label: 'Text', color: '#4f46e5', w: 50 + R() * 20 },
      { key: 'image', label: 'Image', color: '#22c55e', w: 12 + R() * 14 },
      { key: 'redirect', label: 'Redirect', color: '#f59e0b', w: 6 + R() * 10 },
      { key: 'form', label: 'Frame / Form', color: '#94a3b8', w: 3 + R() * 8 }
    ];
    const tsum = typesRaw.reduce((a, t) => a + t.w, 0);
    const types = typesRaw.map(t => ({ key: t.key, label: t.label, color: t.color, pct: Math.round((t.w / tsum) * 100) }));

    const bkDefs = [['81-100', '#059669', 0.06], ['61-80', '#0891b2', 0.14], ['41-60', '#0ea5e9', 0.24], ['21-40', '#d97706', 0.31], ['0-20', '#94a3b8', 0.25]];
    const asBuckets = bkDefs.map((b, i) => { const rr = hashStr('bk:' + target + i); return { label: b[0], color: b[1], count: Math.round(refDomainsCount * b[2] * (0.8 + rr() * 0.4)) }; });

    const flagOf = tld => ({ edu: '\uD83C\uDF93', gov: '\uD83C\uDFDB\uFE0F' })[tld] || '\uD83C\uDF10';
    const cats = ['News', 'Health', 'Blog', 'Forum', 'Wiki', 'Medical', 'Reference'];
    const pool = [...new Set((fix.project.linkDomains || []).concat(['healthline.com', 'webmd.com', 'forbes.com', 'nytimes.com', 'reddit.com', 'wikipedia.org', 'medium.com', 'healthgrades.com', 'goodrx.com', 'ncbi.nlm.nih.gov', 'everydayhealth.com', 'verywellhealth.com', 'mindbodygreen.com', 'prevention.com', 'health.com', 'medicalnewstoday.com', 'psychologytoday.com', 'byrdie.com', 'popsugar.com', 'bustle.com', 'greatist.com', 'livestrong.com', 'clinicaltrials.gov', 'trustpilot.com', 'g2.com', 'clutch.co', 'yelp.com', 'expertise.com']))];
    const knownRank = {};
    links.forEach(l => { knownRank[l.domain] = l.rank; });
    const refDomains = pool.map(domain => {
      const rr = hashStr('rd:' + target + domain);
      const tld = domain.split('.').pop();
      return {
        domain, flag: flagOf(tld), rank: knownRank[domain] != null ? knownRank[domain] : 20 + Math.floor(rr() * 78),
        backlinks: 1 + Math.floor(rr() * 240), linksToUs: 1 + Math.floor(rr() * 12), follow: rr() > 0.28,
        category: cats[Math.floor(rr() * cats.length)], firstSeen: mn[Math.floor(rr() * 12)] + ' ' + (2020 + Math.floor(rr() * 6)),
        isNew: rr() > 0.82, spam: Math.floor(rr() * 22)
      };
    }).sort((a, b) => b.rank - a.rank);

    const brand = target.split('.')[0];
    const anchorDefs = [
      [brand, 'Branded'], [brand + ' review', 'Branded'], [target, 'URL'], ['https://' + target, 'URL'],
      [fix.project.vertical || 'services', 'Keyword'], [brand + ' pricing', 'Keyword'], ['book ' + brand, 'Keyword'],
      ['near me', 'Keyword'], ['online booking', 'Keyword'], ['click here', 'Generic'], ['read more', 'Generic'],
      ['here', 'Generic'], ['learn more', 'Generic'], ['website', 'Generic'], ['(empty)', 'Empty'],
      [brand + ' team', 'Branded'], ['this article', 'Generic'], ['view services', 'Keyword']
    ];
    const anchors = anchorDefs.map(a => {
      const rr = hashStr('an:' + target + a[0]);
      const bl2 = 3 + Math.floor(rr() * ((a[1] === 'Branded' || a[1] === 'URL') ? 900 : 260));
      return { anchor: a[0], type: a[1], backlinks: bl2, refDomains: 1 + Math.floor(bl2 * (0.1 + rr() * 0.3)), dofollowPct: 45 + Math.floor(rr() * 52) };
    }).sort((a, b) => b.backlinks - a.backlinks);

    const competitors = (fix.project.competitors || []).slice(0, 4);
    const gapDomains = pool.slice(0, 30).map(domain => {
      const rr = hashStr('gap:' + target + domain);
      const tld = domain.split('.').pop();
      return { domain, flag: flagOf(tld), rank: 20 + Math.floor(rr() * 78), you: rr() > 0.55, comp: competitors.map(c => hashStr('g:' + domain + c)() > 0.42) };
    });

    return {
      kpis: {
        total: backlinksCount, live: live.length, lost: links.length - live.length,
        referring_domains: refDomainsCount,
        avg_rank: Math.round(links.reduce((a, l) => a + l.rank, 0) / Math.max(1, links.length))
      },
      links,
      summary: { authorityScore, asDelta: 1 + Math.floor(hashStr('dl' + target)() * 4), refDomains: refDomainsCount, backlinks: backlinksCount, dofollowPct, broken, spamScore, newRdMonth, lastUpdated: 'Jun 30, 2026' },
      months, types, asBuckets, refDomains, anchors, competitors, gapDomains
    };
  }

  function auditView(fix) {
    const a = fix.audit;
    const hidden = mut('auditHidden.' + fix.project.id, []);
    const checks = a.checks.map(c => ({ ...c, count: c.pages.length, hidden: hidden.includes(c.id) }));
    const active = checks.filter(c => !c.hidden);
    const sums = sev => active.filter(c => c.severity === sev).reduce((s, c) => s + c.count, 0);
    /* folder tree from crawled pages */
    const tree = {};
    a.crawledPages.forEach(pg => {
      const seg = pg.url.split('/').filter(Boolean);
      const folder = seg.length > 1 ? '/' + seg[0] + '/' : '/';
      if (!tree[folder]) tree[folder] = { folder, pages: 0, errors: 0, warnings: 0, notices: 0, avgScore: 0 };
      const t = tree[folder];
      t.pages++; t.errors += pg.errors; t.warnings += pg.warnings; t.notices += pg.notices; t.avgScore += pg.score;
    });
    const structure = Object.values(tree)
      .map(t => ({ ...t, avgScore: Math.round(t.avgScore / t.pages) }))
      .sort((x, y) => y.pages - x.pages);
    return {
      score: a.score, crawl: a.crawl, domainChecks: a.domainChecks, breakdown: a.breakdown,
      catScore: a.catScore, cwv: a.cwv, checks,
      totals: { errors: sums('error'), warnings: sums('warning'), notices: sums('notice') },
      crawledPages: a.crawledPages, structure, snapshots: a.snapshots
    };
  }

  function toggleAuditCheck(projectId, checkId) {
    const key = 'auditHidden.' + projectId;
    const cur = mut(key, []);
    const next = cur.includes(checkId) ? cur.filter(x => x !== checkId) : cur.concat([checkId]);
    setMut(key, next);
    return { hidden: next };
  }

  /* ---------- AI Optimization layer ---------- */
  const AI_COST = { model: 0.006, inspect: 0.01 };
  const AI_CFG_DEFAULT = { models: ['chat_gpt', 'claude', 'gemini', 'perplexity'], webSearch: true, country: 'United States', city: '', cadence: 'weekly' };

  function aiTargetsOf(fix) {
    return mut('aiTargets.' + fix.project.id, null) || {
      brand: fix.project.name,
      aliases: [fix.project.name],
      competitors: fix.project.competitors.slice()
    };
  }
  function aiListsOf(fix) { return mut('aiLists.' + fix.project.id, [{ id: 'pl1', name: 'Core prompts' }]); }
  function aiPromptsOf(fix) { return mut('aiPrompts.' + fix.project.id, []); }
  function aiHistoryOf(fix) { return mut('aiHistory.' + fix.project.id, []); }

  function aiWeeklyCost(prompts) {
    return prompts.reduce((s, pr) => {
      const cfg = pr.cfg || AI_CFG_DEFAULT;
      if (cfg.cadence === 'manual') return s;
      const perRun = cfg.models.length * AI_COST.model;
      return s + perRun * (cfg.cadence === 'daily' ? 7 : 1);
    }, 0);
  }

  function aiView(fix) {
    const a = fix.aiviz;
    const id = fix.project.id;
    const setupDone = mut('aiSetup.' + id, false);
    const prompts = aiPromptsOf(fix).map(pr => Object.assign({}, pr, {
      cfg: Object.assign({}, AI_CFG_DEFAULT, pr.cfg || {}),
      results: F().genPromptResults(id, pr.text, pr.runs || 0)
    }));
    const citedAnywhere = prompts.filter(pr => pr.cfg.models.some(m => pr.results[m] && pr.results[m].cited)).length;
    const weekly = aiWeeklyCost(prompts);
    const spent = +(mut('aiSpend.' + id, 0) + weekly * 4.3 * (new Date().getDate() / 30)).toFixed(2);
    const trackedTexts = new Set(prompts.map(pr => pr.text));
    return {
      setupDone,
      targets: aiTargetsOf(fix),
      budget: { cap: mut('aiCap.' + id, 25), spent, weekly_est: +(weekly * 4.3).toFixed(2) },
      costs: AI_COST,
      next_run: fix.settings.sync.next_run,
      mentionPlatforms: a.mentionPlatforms,
      llmPlatforms: a.llmPlatforms,
      sov: a.sov,
      kpis: {
        mentions: a.sov.rows.find(r => r.isYou).mentions,
        impressions: a.topPages.reduce((s, pg) => s + pg.impressions, 0),
        cited_pages: a.topPages.length,
        prompt_coverage: { cited: citedAnywhere, total: prompts.length }
      },
      trend: a.trend,
      topPages: a.topPages,
      topDomains: a.topDomains,
      lists: aiListsOf(fix),
      prompts,
      suggestions: a.suggestions.filter(sg => !trackedTexts.has(sg.text)),
      aiKeywords: a.aiKeywords,
      history: aiHistoryOf(fix)
    };
  }

  function aiMutate(fix, action, q) {
    const id = fix.project.id;
    if (action === 'setup') {
      setMut('aiTargets.' + id, { brand: q.brand, aliases: q.aliases || [], competitors: (q.competitors || []).slice(0, 9) });
      if (q.prompts && q.prompts.length) aiAddPrompts(fix, q.prompts, q.listId || 'pl1');
      setMut('aiSetup.' + id, true);
      return { ok: true };
    }
    if (action === 'targets') {
      setMut('aiTargets.' + id, { brand: q.brand, aliases: q.aliases || [], competitors: (q.competitors || []).slice(0, 9) });
      return { ok: true };
    }
    if (action === 'prompts') { return { ok: true, added: aiAddPrompts(fix, q.texts || [], q.listId || 'pl1') }; }
    if (action === 'prompts-remove') {
      setMut('aiPrompts.' + id, aiPromptsOf(fix).filter(pr => pr.id !== q.id));
      return { ok: true };
    }
    if (action === 'prompts-config') {
      setMut('aiPrompts.' + id, aiPromptsOf(fix).map(pr => pr.id === q.id ? Object.assign({}, pr, { cfg: Object.assign({}, AI_CFG_DEFAULT, pr.cfg || {}, q.cfg || {}), listId: q.listId || pr.listId }) : pr));
      return { ok: true };
    }
    if (action === 'lists') {
      let lists = aiListsOf(fix).slice();
      if (q.op === 'create') { const lid = 'pl' + Date.now().toString(36); lists.push({ id: lid, name: (q.name || 'Prompt list').trim() }); setMut('aiLists.' + id, lists); return { ok: true, id: lid }; }
      if (q.op === 'rename') { lists = lists.map(l => l.id === q.id ? Object.assign({}, l, { name: q.name }) : l); setMut('aiLists.' + id, lists); return { ok: true }; }
      if (q.op === 'delete') {
        lists = lists.filter(l => l.id !== q.id);
        if (!lists.length) lists = [{ id: 'pl1', name: 'Core prompts' }];
        setMut('aiLists.' + id, lists);
        setMut('aiPrompts.' + id, aiPromptsOf(fix).map(pr => pr.listId === q.id ? Object.assign({}, pr, { listId: lists[0].id }) : pr));
        return { ok: true };
      }
    }
    if (action === 'run') {
      const all = aiPromptsOf(fix);
      const hit = all.filter(pr => q.promptId ? pr.id === q.promptId : q.listId ? pr.listId === q.listId : true);
      let cost = 0;
      const next = all.map(pr => {
        if (!hit.includes(pr)) return pr;
        const cfg = Object.assign({}, AI_CFG_DEFAULT, pr.cfg || {});
        cost += cfg.models.length * AI_COST.model;
        return Object.assign({}, pr, { runs: (pr.runs || 0) + 1, lastRun: new Date().toISOString().slice(0, 10) });
      });
      setMut('aiPrompts.' + id, next);
      cost = +cost.toFixed(3);
      setMut('aiSpend.' + id, +(mut('aiSpend.' + id, 0) + cost).toFixed(2));
      return { ok: true, ran: hit.length, cost };
    }
    if (action === 'inspect') {
      const question = (q.question || '').trim().slice(0, 500);
      if (!question) throw new Error('Empty question');
      const salt = aiHistoryOf(fix).filter(h2 => h2.question === question).length;
      const scrape = F().genScrape(id, question, salt);
      const cg = scrape.results.chat_gpt;
      const entry = {
        id: 'insp' + Date.now().toString(36) + Math.floor(Math.random() * 99),
        question, promptId: q.promptId || null,
        ts: new Date().toISOString().slice(0, 10),
        verdict: cg.cited ? 'cited' : cg.mentioned ? 'mentioned' : 'absent',
        position: cg.position,
        cost: AI_COST.inspect,
        scrape
      };
      const hist = [entry].concat(aiHistoryOf(fix)).slice(0, 50);
      setMut('aiHistory.' + id, hist);
      setMut('aiSpend.' + id, +(mut('aiSpend.' + id, 0) + AI_COST.inspect).toFixed(2));
      return entry;
    }
    throw new Error('Unknown ai action ' + action);
  }

  function aiAddPrompts(fix, texts, listId) {
    const id = fix.project.id;
    const cur = aiPromptsOf(fix);
    const seen = new Set(cur.map(pr => pr.text));
    const added = [];
    texts.map(t => String(t).trim().replace(/\s+/g, ' ').slice(0, 500)).filter(Boolean).forEach(t => {
      if (seen.has(t)) return;
      seen.add(t);
      added.push({
        id: id + '-upr-' + Date.now().toString(36) + '-' + added.length,
        text: t, listId: listId || 'pl1', cfg: Object.assign({}, AI_CFG_DEFAULT),
        addedAt: new Date().toISOString().slice(0, 10), runs: 0, lastRun: null
      });
    });
    if (added.length) setMut('aiPrompts.' + id, cur.concat(added));
    return added.length;
  }

  /* ---------- prompt explorer (template-based, mirrors Keyword Explorer) ---------- */
  function promptExplore(body) {
    const fix = F().build(body.project) || F().build('fusehealth');
    const seeds = (body.seeds || []).map(s => s.trim().toLowerCase()).filter(Boolean);
    const rnd = F().mulberry32(F().hashStr('pe|' + seeds.join('|') + '|' + body.project));
    const tracked = new Set(aiPromptsOf(fix).map(pr => pr.text));
    const city = (fix.project.location === 'United States') ? 'my city' : fix.project.location;
    const TPLS = [
      ['recommendation', s => 'What is the best ' + s + ' and who do you recommend?'],
      ['recommendation', s => 'Recommend a trusted company for ' + s + '.'],
      ['recommendation', s => 'Who are the top-rated providers for ' + s + '?'],
      ['comparison', s => 'Compare the best options for ' + s + ' \u2014 which should I choose?'],
      ['comparison', s => s + ' vs alternatives: pros and cons?'],
      ['cost', s => 'How much does ' + s + ' cost? Is it worth the price?'],
      ['cost', s => 'What is a fair price for ' + s + '?'],
      ['question', s => 'What should I know before choosing ' + s + '?'],
      ['question', s => 'Is ' + s + ' safe and legit? What should I look for?'],
      ['local', s => 'Best ' + s + ' near ' + city + ' \u2014 who should I call?'],
      ['local', s => 'Who offers same-week ' + s + ' in ' + city + '?']
    ];
    const rows = [];
    const seen = new Set();
    seeds.forEach(seed => {
      TPLS.forEach(t => {
        const text = t[1](seed);
        if (seen.has(text)) return;
        seen.add(text);
        rows.push({
          text, category: t[0],
          aiVolume: Math.round(Math.pow(10, 1.2 + rnd() * 2.2) / 10) * 10,
          tracked: tracked.has(text)
        });
      });
    });
    rows.sort((x, y) => y.aiVolume - x.aiVolume);
    return { rows: rows.slice(0, 40), cost: 0.01, location: fix.project.location };
  }

  /* ---------- Ads (Google Ads API + GA4 Data API) ---------- */
  function adsPullWindow() {
    const d = new Date();
    const last = new Date(d);
    last.setMinutes(0, 0, 0);
    last.setHours(d.getHours() >= 18 ? 18 : d.getHours() >= 6 ? 6 : -6); // -6 rolls to yesterday 18:00
    return { last, next: new Date(last.getTime() + 12 * 3600 * 1000) };
  }

  function adsView(fix, range) {
    const id = fix.project.id;
    const n = rangeDays(range);
    const a = fix.ads;
    const st = mut('adsStatus.' + id, {});
    const bud = mut('adsBudget.' + id, {});
    const negs = mut('adsNegatives.' + id, []);
    const promoted = mut('adsPromoted.' + id, []);
    const sum = (arr, k) => arr.reduce((x, y) => x + (y[k] || 0), 0);

    const campaigns = a.campaigns.map(c => {
      const status = st[c.id] || c.status;
      const budgetDaily = bud[c.id] != null ? bud[c.id] : c.budgetDaily;
      const cur = c.daily.slice(-n), prev = c.daily.slice(-(2 * n), -n);
      const spend = +sum(cur, 'spend').toFixed(2), clicks = sum(cur, 'clicks'),
        impressions = sum(cur, 'impressions'), conversions = +sum(cur, 'conversions').toFixed(1),
        conv_value = +sum(cur, 'conv_value').toFixed(2);
      return {
        id: c.id, name: c.name, platform: c.platform, type: c.type, status,
        budget_daily: budgetDaily,
        spend, impressions, clicks, conversions, conv_value,
        ga4_key_events: +sum(cur, 'ga4_key_events').toFixed(1),
        ga4_revenue: +sum(cur, 'ga4_revenue').toFixed(2),
        ctr: impressions ? +((clicks / impressions) * 100).toFixed(2) : 0,
        cpc: clicks ? +(spend / clicks).toFixed(2) : 0,
        cpa: conversions ? +(spend / conversions).toFixed(2) : null,
        roas: spend ? +(conv_value / spend).toFixed(2) : 0,
        lost_is_budget: status === 'enabled' ? c.lostISBudget : 0,
        lost_is_rank: status === 'enabled' ? c.lostISRank : 0,
        prev: { spend: +sum(prev, 'spend').toFixed(2), conversions: +sum(prev, 'conversions').toFixed(1) },
        adGroups: c.adGroups.map(g => ({
          id: g.id, name: g.name,
          spend: +(spend * g.share).toFixed(2),
          clicks: Math.round(clicks * g.share),
          conversions: +(conversions * g.share).toFixed(1),
          cpa: conversions * g.share > 0.05 ? +((spend * g.share) / (conversions * g.share)).toFixed(2) : null
        })),
        daily: cur
      };
    });

    const trend = [];
    for (let i = 0; i < n; i++) {
      const pt = { date: null, spend: 0, conversions: 0, ga4_key_events: 0 };
      campaigns.forEach(c => {
        const d = c.daily[i];
        if (!d) return;
        pt.date = d.date;
        pt.spend += d.spend; pt.conversions += d.conversions; pt.ga4_key_events += d.ga4_key_events;
      });
      pt.spend = +pt.spend.toFixed(2);
      pt.conversions = +pt.conversions.toFixed(1);
      pt.ga4_key_events = +pt.ga4_key_events.toFixed(1);
      if (pt.date) trend.push(pt);
    }

    const totals = {};
    ['spend', 'impressions', 'clicks', 'conversions', 'conv_value', 'ga4_key_events', 'ga4_revenue'].forEach(k => {
      totals[k] = +campaigns.reduce((s2, c) => s2 + c[k], 0).toFixed(2);
    });
    totals.cpa = totals.conversions ? +(totals.spend / totals.conversions).toFixed(2) : 0;
    totals.cpc = totals.clicks ? +(totals.spend / totals.clicks).toFixed(2) : 0;
    totals.roas = totals.spend ? +(totals.conv_value / totals.spend).toFixed(2) : 0;
    const prevTotals = {
      spend: +campaigns.reduce((s2, c) => s2 + c.prev.spend, 0).toFixed(2),
      conversions: +campaigns.reduce((s2, c) => s2 + c.prev.conversions, 0).toFixed(1)
    };

    /* pacing — calendar month, computed on raw 90-day series */
    const today = new Date();
    const dom = today.getDate();
    const dim = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
    const monthISO = today.toISOString().slice(0, 7);
    const mtdOf = plat => +a.campaigns.filter(c => !plat || c.platform === plat)
      .reduce((s2, c) => s2 + c.daily.filter(d => d.date.slice(0, 7) === monthISO).reduce((x, y) => x + y.spend, 0), 0).toFixed(2);
    const budgetOf = plat => Math.round(campaigns.filter(c => c.status === 'enabled' && (!plat || c.platform === plat))
      .reduce((s2, c) => s2 + c.budget_daily, 0) * dim);
    const mtd = mtdOf(null);
    const pacing = {
      monthly_budget: budgetOf(null), mtd_spend: mtd,
      projected: Math.round(mtd / Math.max(1, dom) * dim),
      pct: Math.min(100, Math.round(mtd / Math.max(1, budgetOf(null)) * 100)),
      day_of_month: dom, days_in_month: dim,
      channels: ['Google Ads', 'Meta'].map(pl => ({
        platform: pl, budget: budgetOf(pl), mtd: mtdOf(pl),
        pct: Math.min(100, Math.round(mtdOf(pl) / Math.max(1, budgetOf(pl)) * 100))
      }))
    };

    const negTerms = new Set(negs.map(x => x.term));
    const promotedTerms = new Set(promoted);
    /* fixture aggregates represent a 30-day window — scale metrics to the selected range
       (real backend: GAQL `WHERE segments.date BETWEEN ...` re-aggregates server-side) */
    const stHash = str => { let h2 = 0; for (let i2 = 0; i2 < str.length; i2++) h2 = (h2 * 31 + str.charCodeAt(i2)) % 997; return h2 / 997; };
    const searchTerms = a.searchTerms.map(t => {
      const f = n === 30 ? 1 : (n / 30) * (0.85 + stHash(t.term) * 0.3);
      const clicks = t.clicks > 0 ? Math.max(1, Math.round(t.clicks * f)) : 0;
      const cost = +(t.cost * f).toFixed(2);
      const conversions = +(t.conversions * f).toFixed(1);
      return Object.assign({}, t, {
        impressions: Math.max(clicks, Math.round(t.impressions * f)),
        clicks, cost, conversions,
        cpa: conversions ? +(cost / conversions).toFixed(2) : null,
        status: negTerms.has(t.term) ? 'negative' : promotedTerms.has(t.term) ? 'tracked' : conversions > 0 ? 'converting' : 'wasted'
      });
    });

    const attribution = campaigns.filter(c => c.spend > 0).map(c => ({
      id: c.id, name: c.name, platform: c.platform,
      ads_conversions: c.conversions, ga4_key_events: c.ga4_key_events,
      ads_value: c.conv_value, ga4_revenue: c.ga4_revenue,
      gap_pct: c.conversions ? Math.round((c.ga4_key_events - c.conversions) / c.conversions * 100) : 0
    }));

    const w = adsPullWindow();
    return {
      totals, prev: prevTotals, trend, pacing, campaigns, searchTerms, attribution,
      window: { from: trend.length ? trend[0].date : null, to: trend.length ? trend[trend.length - 1].date : null, days: n },
      landingPages: a.landingPages, negatives: negs,
      syncMeta: {
        cadence: 'Every 12h (06:00 & 18:00)',
        last_pull: w.last.toISOString(), next_pull: w.next.toISOString(),
        ops_used: 26, ops_limit: 15000,
        ga4_tokens_used: 310, ga4_tokens_limit: 25000,
        monthly_cost: 0
      }
    };
  }

  /* ---------- Off-site SEO (GA4 Data API: referral + organic social/video) ---------- */
  function offsiteView(fix, range) {
    const n = rangeDays(range);
    const o = fix.offsite;
    const cur = o.series.slice(-n), prev = o.series.slice(-(2 * n), -n);
    const sum = (arr, k) => arr.reduce((a, x) => a + (x[k] || 0), 0);
    const total90 = sum(o.series, 'sessions') || 1;
    const curSessions = sum(cur, 'sessions');
    const f = curSessions / total90;
    const sc = v => Math.round((v || 0) * f);
    const sc1 = v => +((v || 0) * f).toFixed(1);
    const sc2 = v => +((v || 0) * f).toFixed(2);
    const scaleRow = r => Object.assign({}, r, {
      sessions: sc(r.sessions), engagedSessions: sc(r.engagedSessions),
      keyEvents: sc1(r.keyEvents), revenue: sc2(r.revenue)
    });
    const referrers = o.referrers.map(scaleRow);
    const social = o.social.map(r => Object.assign({}, scaleRow(r), { impressions: r.impressions != null ? sc(r.impressions) : null }));
    const landingPages = o.landingPages.map(scaleRow);
    const channels = o.channels.map(c => Object.assign({}, c, { sessions: sc(c.sessions), keyEvents: sc1(c.keyEvents), revenue: sc2(c.revenue) }));

    const totals = {
      sessions: curSessions,
      engagedSessions: sum(cur, 'engagedSessions'),
      engagementRate: curSessions ? +(sum(cur, 'engagedSessions') / curSessions * 100).toFixed(1) : 0,
      keyEvents: +sum(cur, 'keyEvents').toFixed(1),
      revenue: +sum(cur, 'revenue').toFixed(2),
      referringDomains: referrers.filter(r => r.sessions > 0).length
    };
    const prevT = {
      sessions: sum(prev, 'sessions'), engagedSessions: sum(prev, 'engagedSessions'),
      keyEvents: +sum(prev, 'keyEvents').toFixed(1), revenue: +sum(prev, 'revenue').toFixed(2)
    };
    const w = adsPullWindow();
    return {
      totals, prev: prevT, trend: cur, channels, referrers, social, landingPages,
      connectors: o.connectors,
      syncMeta: { cadence: 'Every 12h (06:00 & 18:00)', last_pull: w.last.toISOString(), next_pull: w.next.toISOString(), ga4_tokens_used: 214, ga4_tokens_limit: 25000 }
    };
  }

  function alertsView(fix) {
    const ack = mut('ack', {});
    return { feed: fix.feed.map(f => ({ ...f, acknowledged: !!ack[f.id] })) };
  }

  function usageView(fix) {
    const kw = mergedKeywords(fix).length, pg = fix.pages.length;
    const items = [
      { module: 'Position tracking (SERP Standard)', cadence: 'Weekly', est: +(kw * 0.0015 * 4.3).toFixed(2) },
      { module: 'Backlinks summary + new/lost deltas', cadence: 'Weekly', est: +(0.05 * 4.3).toFixed(2) },
      { module: 'Site audit crawl (OnPage)', cadence: 'Monthly', est: +(pg * 0.00125 + 0.1).toFixed(2) },
      { module: 'Keyword volume refresh (Labs)', cadence: 'Monthly', est: 0.12 },
      { module: 'AI visibility refresh (LLM Mentions + Responses)', cadence: 'Weekly', est: +(aiPromptsOf(fix).length * (fix.aiviz.llmPlatforms.length || 5) * 0.006 * 4.3 + 0.15).toFixed(2) },
      { module: 'Keyword Explorer (on-demand)', cadence: 'On demand', est: null, note: '~$0.02 per search' }
    ];
    const fixed = items.reduce((a, i) => a + (i.est || 0), 0);
    const extra = mut('usageExtra.' + fix.project.id, 0);
    const dayFrac = new Date().getDate() / 30;
    return {
      budget: 75, currency: 'USD',
      month_to_date: +(fixed * dayFrac + extra).toFixed(2),
      est_monthly: +(fixed + extra).toFixed(2),
      items
    };
  }

  function settingsView(fix) {
    const s = fix.settings;
    const now = Date.now(), DAY = 86400000, iso = t => new Date(t).toISOString().slice(0, 10);
    const creds = mut('creds.' + fix.project.id, null);
    const prefs = mut('prefs.' + fix.project.id, null);
    const lastSync = mut('lastSync.' + fix.project.id, null);
    const crawl = mut('crawlCfg.' + fix.project.id, null);
    return {
      project: { id: fix.project.id, domain: fix.project.domain, name: fix.project.name, vertical: fix.project.vertical, location: fix.project.location, competitors: fix.project.competitors },
      credentials: creds || s.credentials,
      connectors: s.connectors,
      prefs: prefs || s.prefs,
      crawl: crawl || { maxPages: 500, frequency: 'monthly', jsRendering: false, respectRobots: true, excludedPaths: '/admin\n/cart' },
      alertRules: mut('alertRules.' + fix.project.id, null) || [
        { id: 'pos_drop', label: 'Keyword position drops by', threshold: 3, unit: 'positions', on: true },
        { id: 'lost_backlink', label: 'Backlink lost from domain rank ≥', threshold: 40, unit: '', on: true },
        { id: 'traffic_anomaly', label: 'Clicks deviate from 28-day mean by', threshold: 30, unit: '%', on: true },
        { id: 'audit_errors', label: 'Crawl finds new errors ≥', threshold: 1, unit: 'errors', on: true }
      ],
      sync: { ...s.sync, last_run: lastSync ? new Date(lastSync).toISOString().slice(0, 10) : s.connectors[2].last_sync },
      usage: usageView(fix),

      /* ----- extended settings groups (persisted per-project / per-workspace via PUT) ----- */
      workspace: mut('workspace', null) || {
        name: 'Limitless Marketing', plan: 'Growth', seats_used: 3, seats_total: 5,
        billing_cycle: 'Annual', renews: '2027-02-01', mrr: 149, currency: 'USD',
        timezone: 'America/Chicago', week_start: 'Monday', owner_email: 'founder@limitlesshold.com'
      },
      team: (function() {
        const cur = mut('team', null) || [
          { id: 'u1', name: 'Founder', email: 'founder@limitlesshold.com', role: 'Owner', status: 'active', last_active: iso(now), initials: 'FO' },
          { id: 'u2', name: 'Priya Shah', email: 'priya@limitlesshold.com', role: 'Admin', status: 'active', last_active: iso(now - 1 * DAY), initials: 'PS' },
          { id: 'u3', name: 'Marcus Lee', email: 'marcus@limitlesshold.com', role: 'Analyst', status: 'active', last_active: iso(now - 4 * DAY), initials: 'ML' }
        ];
        return cur.map((m, idx) => Object.assign({}, m, {
          role: idx === 0 ? 'Owner' : (m.role === 'Owner' || m.role === 'Viewer' ? 'Admin' : m.role)
        }));
      })(),
      syncConfig: mut('syncConfig.' + fix.project.id, null) || {
        positions: 'weekly', backlinks: 'weekly', audit: 'monthly', keywords: 'monthly', ads: '12h', ai: 'weekly'
      },
      budget: {
        cap: mut('budgetCap', 75), enforce: mut('budgetEnforce', true),
        mtd: usageView(fix).month_to_date,
        quotas: {
          ga4_tokens_used: 3820, ga4_tokens_limit: 25000,
          ads_ops_used: 26, ads_ops_limit: 15000,
          gsc_queries_used: 412, gsc_queries_limit: 1200
        }
      },
      platformConnectors: (function () {
        const saved = mut('platformConn.' + fix.project.id, null);
        const base = (fix.offsite && fix.offsite.connectors) ? Object.assign({ meta_ads: false }, fix.offsite.connectors) : { linkedin: true, reddit: false, youtube: false, x: false, facebook: false, instagram: false, meta_ads: false };
        return saved || base;
      })(),
      notifications: mut('notifications', null) || {
        email_enabled: true, weekly_digest: true, digest_day: 'Monday',
        recipients: 'founder@limitlesshold.com, priya@limitlesshold.com',
        slack_enabled: false, slack_webhook: '', quiet_start: '22:00', quiet_end: '07:00',
        route_high: 'email', route_medium: 'digest', route_info: 'none'
      },
      aiConfig: mut('aiConfig', null) || {
        provider: 'OpenAI', model: 'gpt-4o', tone: 'Concise', cadence: 'weekly',
        monthly_cap: 25, brand_voice: 'Confident, service-led, no hype. Refer to us as "we". Never use exclamation marks.'
      },
      security: mut('security', null) || {
        twofa: true, sso: false, session_timeout: '30d',
        sessions: [
          { id: 's1', device: 'Chrome · macOS', ip: '73.42.x.x', location: 'Austin, TX', current: true, last: iso(now) },
          { id: 's2', device: 'Safari · iPhone', ip: '73.42.x.x', location: 'Austin, TX', current: false, last: iso(now - 2 * DAY) }
        ],
        tokens: [
          { id: 'tk1', name: 'Looker Studio export', prefix: 'lm_live_a1b2', created: iso(now - 40 * DAY), last_used: iso(now - 1 * DAY) }
        ]
      },
      dataPrefs: mut('dataPrefs', null) || {
        export_format: 'CSV', retention: '24m', report_timezone: 'America/Chicago', number_format: '1,234.56'
      }
    };
  }

  /* ---------- research (Keyword Explorer) ---------- */
  // synonyms used to generate "related" (semantic) variants that drop a seed word
  const SYNS = {
    therapy: ['treatment', 'infusion'], iv: ['intravenous', 'drip'], drip: ['infusion', 'therapy'],
    vitamin: ['nutrient'], infusion: ['drip'], clinic: ['center'], marketing: ['advertising', 'promotion'],
    seo: ['search optimization'], agency: ['company', 'firm'], services: ['solutions'], hydration: ['fluid']
  };
  function research(body) {
    const seeds = (body.keywords || []).map(s => s.trim().toLowerCase()).filter(Boolean);
    const fix = F().build(body.project) || F().build('fusehealth');
    const tracked = new Set(mergedKeywords(fix).map(k => k.kw));
    const rnd = F().mulberry32(F().hashStr(seeds.join('|') + body.project));
    const ri = (a, b) => Math.floor(rnd() * (b - a + 1)) + a;
    const prefixes = ['best ', 'affordable ', 'mobile ', 'top ', 'cheap ', '24 hour ', 'luxury ', 'same day '];
    const mods = [' near me', ' cost', ' pricing', ' services', ' reviews', ' benefits', ' clinic', ' at home', ' packages', ' membership', ' deals', ' open now'];
    const qwords = ['what is ', 'how much is ', 'how does ', 'is ', 'why is ', 'when to get ', 'where to get ', 'does insurance cover '];
    const FEATS = ['featured_snippet', 'sitelinks', 'ai_overview', 'faq', 'reviews', 'people_also_ask', 'local_pack', 'image_pack', 'video', 'instant_answer'];
    const rows = [];
    const seen = new Set();
    const add = (kw, match) => {
      kw = kw.trim().replace(/\s+/g, ' ');
      if (!kw || seen.has(kw)) return;
      seen.add(kw);
      const volume = Math.round(Math.pow(10, 1.6 + rnd() * 2.4) / 10) * 10;
      const monthly = [];
      for (let m = 0; m < 12; m++) monthly.push(Math.max(10, Math.round(volume * (0.62 + rnd() * 0.76))));
      const nf = ri(1, 5), feats = [];
      for (let i = 0; i < FEATS.length && feats.length < nf; i++) if (rnd() < 0.4) feats.push(FEATS[i]);
      if (!feats.length) feats.push(FEATS[ri(0, FEATS.length - 1)]);
      rows.push({
        kw, volume, match, monthly, serpFeatures: feats,
        kd: Math.max(4, Math.min(88, Math.round(14 + Math.log10(volume + 10) * 13 + ri(-12, 16)))),
        cpc: +(0.4 + rnd() * 5).toFixed(2),
        intent: F().classifyIntent(kw),
        tracked: tracked.has(kw)
      });
    };
    seeds.forEach(seed => {
      const words = seed.split(/\s+/).filter(Boolean);
      // exact
      add(seed, 'exact');
      // phrase — seed kept contiguous with a prefix or suffix (keyword_suggestions)
      prefixes.forEach(pre => { if (rnd() < 0.7) add(pre + seed, 'phrase'); });
      mods.forEach(mod => add(seed + mod, 'phrase'));
      prefixes.forEach(pre => mods.forEach(mod => { if (rnd() < 0.22) add(pre + seed + mod, 'phrase'); }));
      // broad — words reordered or a qualifier inserted between them
      if (words.length >= 2) {
        add(words.slice().reverse().join(' '), 'broad');
        ['mobile', 'best', 'affordable'].forEach(q => { if (rnd() < 0.6) add(words[0] + ' ' + q + ' ' + words.slice(1).join(' '), 'broad'); });
        add(words.slice(1).join(' ') + ' ' + words[0], 'broad');
        mods.forEach(mod => { if (rnd() < 0.3) add(words.slice().reverse().join(' ') + mod, 'broad'); });
      } else {
        ['premium ', 'private ', 'concierge '].forEach(q => add(q + seed + ' service', 'broad'));
        mods.forEach(mod => { if (rnd() < 0.35) add(seed + ' service' + mod, 'broad'); });
      }
      // questions (keyword_suggestions + question-prefix filter)
      qwords.forEach(q => { if (rnd() < 0.8) add(q + seed, 'questions'); });
      qwords.slice(0, 4).forEach(q => mods.slice(0, 4).forEach(mod => { if (rnd() < 0.18) add(q + seed + mod, 'questions'); }));
      // related — replace a seed word with a synonym (drops the literal seed)
      let relAdded = 0;
      words.forEach((w, i) => {
        (SYNS[w] || []).forEach(syn => {
          const parts = words.slice(); parts[i] = syn;
          const base = parts.join(' ');
          add(base, 'related'); relAdded++;
          mods.forEach(mod => { if (rnd() < 0.3) add(base + mod, 'related'); });
        });
      });
      if (!relAdded) { add(seed + ' alternatives', 'related'); add('similar to ' + seed, 'related'); add(seed + ' competitors', 'related'); }
    });
    rows.sort((a, b) => b.volume - a.volume);
    const out = rows.slice(0, 200);
    // DataForSEO Labs live pricing: $0.012/task + $0.00012/row
    return { rows: out, cost: +(0.012 + out.length * 0.00012).toFixed(3), location: body.location || 'United States' };
  }

  /* ---------- sync tasks ---------- */
  const tasks = {};
  const SCOPE_STEPS = {
    all: ['Queueing SERP tasks', 'Fetching keyword positions', 'Pulling backlink deltas', 'Crawling pages (OnPage)', 'Refreshing volumes', 'Pulling Google Ads + GA4 reports', 'Recomputing signals & alerts'],
    positions: ['Queueing SERP tasks', 'Fetching keyword positions', 'Recomputing movement'],
    backlinks: ['Pulling backlink summary', 'Diffing new & lost links'],
    audit: ['Starting crawl', 'Crawling pages (OnPage)', 'Scoring & grouping issues'],
    keywords: ['Refreshing volumes (Labs)', 'Reclassifying intent & difficulty'],
    ads: ['Pulling Google Ads reports (GAQL)', 'Pulling GA4 metrics (runReport)', 'Joining attribution & pacing', 'Regenerating ads alerts'],
    ai: ['Querying LLM mentions (AI Overviews + ChatGPT)', 'Running tracked prompts across 5 LLMs', 'Refreshing AI keyword volumes', 'Recomputing share of voice']
  };
  function estCost(fix, scope) {
    const kw = mergedKeywords(fix).length, pg = fix.pages.length;
    const c = {
      positions: kw * 0.0015, backlinks: 0.06, audit: pg * 0.00125 + 0.1, keywords: 0.12, ads: 0,
      ai: +(aiWeeklyCost(aiPromptsOf(fix)) + 0.05).toFixed(3)
    };
    c.all = c.positions + c.backlinks + c.audit + c.keywords + c.ai;
    return +(c[scope] || c.all).toFixed(2);
  }
  function startSync(projectId, scope) {
    const fix = F().build(projectId);
    const id = 't' + Date.now().toString(36) + Math.floor(Math.random() * 999);
    const steps = SCOPE_STEPS[scope] || SCOPE_STEPS.all;
    const cost = estCost(fix, scope);
    const t = { id, projectId, scope, progress: 0, step: steps[0], steps, done: false, est_cost: cost };
    tasks[id] = t;
    const iv = setInterval(() => {
      t.progress = Math.min(1, t.progress + 0.09 + Math.random() * 0.1);
      t.step = steps[Math.min(steps.length - 1, Math.floor(t.progress * steps.length))];
      if (t.progress >= 1) {
        t.done = true; t.step = 'Done';
        clearInterval(iv);
        setMut('lastSync.' + projectId, Date.now());
        setMut('usageExtra.' + projectId, +(mut('usageExtra.' + projectId, 0) + cost).toFixed(2));
      }
    }, 420);
    return { task_id: id, est_cost: cost, steps };
  }

  /* ---------- router ---------- */
  function route(method, path, paramsOrBody) {
    const seg = path.replace(/^\/api\//, '').split('/').filter(Boolean);
    const q = paramsOrBody || {};

    if (method === 'GET' && seg[0] === 'projects' && seg.length === 1)
      return F().PROJECTS.map(p => ({ id: p.id, domain: p.domain, name: p.name, vertical: p.vertical, location: p.location }));

    if (method === 'POST' && seg[0] === 'projects' && seg.length === 1)
      return F().addProject(q.domain, { name: q.name, vertical: q.vertical, location: q.location });

    if (seg[0] === 'projects' && seg.length >= 3) {
      const fix = F().build(seg[1]);
      if (!fix) throw new Error('Unknown project ' + seg[1]);
      const res = seg[2];
      if (method === 'GET') {
        if (res === 'overview') return overview(fix, q.range || '30d');
        if (res === 'seo') return seoView(fix);
        if (res === 'keywords') return keywordsView(fix);
        if (res === 'positions') return positionsView(fix);
        if (res === 'backlinks') return backlinksView(fix);
        if (res === 'audit') return auditView(fix);
        if (res === 'ai') return aiView(fix);
        if (res === 'offsite') return offsiteView(fix, q.range || '30d');
        if (res === 'ads') return adsView(fix, q.range || '30d');
        if (res === 'alerts') return alertsView(fix);
        if (res === 'settings') return settingsView(fix);
      }
      if (method === 'POST' && res === 'keywords') {
        const added = mut('added.' + seg[1], []);
        const id = seg[1] + '-kwm-' + Date.now().toString(36);
        const row = {
          id, kw: q.kw, intent: q.intent || F().classifyIntent(q.kw),
          pos: q.pos || 30 + Math.floor(Math.random() * 40), prevPos: null,
          volume: q.volume || 0, kd: q.kd || 0, cpc: q.cpc || 0,
          clicks: 0, impressions: 0, ctr: 0, url: null,
          monthly: Array(12).fill(q.volume || 0), source: 'manual', serpFeatures: []
        };
        added.push(row);
        setMut('added.' + seg[1], added);
        return { ok: true, keyword: row };
      }
      if (method === 'POST' && res === 'sync') return startSync(seg[1], q.scope || 'all');
      if (method === 'POST' && res === 'ads' && seg[3] === 'status') {
        const cur = mut('adsStatus.' + seg[1], {});
        cur[q.campaignId] = q.status === 'paused' ? 'paused' : 'enabled';
        setMut('adsStatus.' + seg[1], cur);
        return { ok: true, status: cur[q.campaignId] };
      }
      if (method === 'POST' && res === 'ads' && seg[3] === 'budget') {
        const cur = mut('adsBudget.' + seg[1], {});
        cur[q.campaignId] = Math.max(1, Math.round(+q.budgetDaily));
        setMut('adsBudget.' + seg[1], cur);
        return { ok: true, budgetDaily: cur[q.campaignId] };
      }
      if (method === 'POST' && res === 'ads' && seg[3] === 'negatives') {
        const cur = mut('adsNegatives.' + seg[1], []);
        if (!cur.some(x => x.term === q.term)) cur.push({ term: q.term, matchType: q.matchType || 'phrase', campaignId: q.campaignId || null, addedAt: new Date().toISOString().slice(0, 10) });
        setMut('adsNegatives.' + seg[1], cur);
        return { ok: true, negatives: cur };
      }
      if (method === 'POST' && res === 'ads' && seg[3] === 'promote') {
        const kwRes = route('POST', '/api/projects/' + seg[1] + '/keywords', { kw: q.term });
        const cur = mut('adsPromoted.' + seg[1], []);
        if (!cur.includes(q.term)) { cur.push(q.term); setMut('adsPromoted.' + seg[1], cur); }
        return { ok: true, keyword: kwRes.keyword };
      }
      if (method === 'POST' && res === 'audit' && seg[3] === 'toggle-check') return toggleAuditCheck(seg[1], q.checkId);
      if (method === 'POST' && res === 'ai' && seg[3]) return aiMutate(fix, seg[3], q);
      if (method === 'PUT' && res === 'settings') {
        if (q.credentials) setMut('creds.' + seg[1], q.credentials);
        if (q.prefs) setMut('prefs.' + seg[1], q.prefs);
        if (q.crawl) setMut('crawlCfg.' + seg[1], q.crawl);
        if (q.alertRules) setMut('alertRules.' + seg[1], q.alertRules);
        if (q.syncConfig) setMut('syncConfig.' + seg[1], q.syncConfig);
        if (q.platformConnectors) setMut('platformConn.' + seg[1], q.platformConnectors);
        if (q.workspace) setMut('workspace', q.workspace);
        if (q.team) setMut('team', q.team);
        if (q.notifications) setMut('notifications', q.notifications);
        if (q.aiConfig) setMut('aiConfig', q.aiConfig);
        if (q.security) setMut('security', q.security);
        if (q.dataPrefs) setMut('dataPrefs', q.dataPrefs);
        if (q.budgetCap != null) setMut('budgetCap', q.budgetCap);
        if (q.budgetEnforce != null) setMut('budgetEnforce', q.budgetEnforce);
        return { ok: true };
      }
      if (method === 'POST' && res === 'team') {
        const cur = mut('team', null) || [
          { id: 'u1', name: 'Founder', email: 'founder@limitlesshold.com', role: 'Owner', status: 'active', last_active: new Date().toISOString().slice(0, 10), initials: 'FO' },
          { id: 'u2', name: 'Priya Shah', email: 'priya@limitlesshold.com', role: 'Admin', status: 'active', last_active: new Date().toISOString().slice(0, 10), initials: 'PS' },
          { id: 'u3', name: 'Marcus Lee', email: 'marcus@limitlesshold.com', role: 'Analyst', status: 'active', last_active: new Date().toISOString().slice(0, 10), initials: 'ML' }
        ];
        if (cur.some(x => x.name === q.username || x.email === q.email)) {
          const err = new Error('Username or email already exists.');
          err.detail = 'Username or email already exists.';
          throw err;
        }
        const id = 'u' + Date.now().toString(36);
        let r = q.role || 'Analyst';
        if (r !== 'Admin' && r !== 'Analyst') r = 'Analyst';
        cur.push({
          id, name: q.username || q.email, email: q.email, role: r,
          status: 'active', last_active: new Date().toISOString().slice(0, 10),
          initials: (q.username || q.email).slice(0, 2).toUpperCase()
        });
        setMut('team', cur);
        return { ok: true, id };
      }
      if (method === 'DELETE' && res === 'team' && seg[3]) {
        if (String(seg[3]) === 'u1' || String(seg[3]) === '1') {
          const err = new Error('Cannot delete the Owner account.');
          err.detail = 'Cannot delete the Owner account.';
          throw err;
        }
        const cur = mut('team', null) || [
          { id: 'u1', name: 'Founder', email: 'founder@limitlesshold.com', role: 'Owner', status: 'active', last_active: new Date().toISOString().slice(0, 10), initials: 'FO' },
          { id: 'u2', name: 'Priya Shah', email: 'priya@limitlesshold.com', role: 'Admin', status: 'active', last_active: new Date().toISOString().slice(0, 10), initials: 'PS' },
          { id: 'u3', name: 'Marcus Lee', email: 'marcus@limitlesshold.com', role: 'Analyst', status: 'active', last_active: new Date().toISOString().slice(0, 10), initials: 'ML' }
        ];
        const filtered = cur.filter(x => String(x.id) !== String(seg[3]));
        setMut('team', filtered);
        return { ok: true };
      }
      if (method === 'DELETE' && res === 'data') {
        return { ok: true };
      }
    }

    if (method === 'GET' && seg[0] === 'tasks' && seg[1]) {
      const t = tasks[seg[1]];
      if (!t) return { task_id: seg[1], progress: 1, done: true, step: 'Done' };
      return { task_id: t.id, progress: +t.progress.toFixed(2), step: t.step, done: t.done, est_cost: t.est_cost };
    }

    /* Batch ack must be tested BEFORE the single-alert route: "alerts/ack" is two segments
       and "alerts/<id>/ack" is three, so the single route's `seg[2] === 'ack'` never matches
       the batch path and it would otherwise fall through to "No route". Mirrors the real
       AlertBatchAckView contract: {ok, acknowledged: [...], failed: [...]}, with `ok` true
       only when nothing failed. */
    if (method === 'POST' && seg[0] === 'alerts' && seg[1] === 'ack' && !seg[2]) {
      const ids = (q && q.ids) || [];
      const acknowledged = [];
      const failed = [];
      ids.forEach(id => {
        if (typeof id === 'string' && id) { setMut('ack.' + id, true); acknowledged.push(id); }
        else failed.push({ id: String(id), detail: 'Not a valid alert id.' });
      });
      return { ok: failed.length === 0, acknowledged: acknowledged, failed: failed };
    }

    if (method === 'POST' && seg[0] === 'alerts' && seg[2] === 'ack') {
      setMut('ack.' + seg[1], true);
      return { ok: true };
    }

    if (method === 'POST' && seg[0] === 'research') return research(q);
    if (method === 'POST' && seg[0] === 'prompt-research') return promptExplore(q);

    throw new Error('No route: ' + method + ' ' + path);
  }

  /* ---------- public surface ---------- */
  async function get(path, params) {
    if (config.baseUrl) return http('GET', path, params, null);
    await latency();
    return route('GET', path, params);
  }
  async function post(path, body) {
    if (config.baseUrl) return http('POST', path, null, body);
    await latency();
    return route('POST', path, body);
  }
  async function put(path, body) {
    if (config.baseUrl) return http('PUT', path, null, body);
    await latency();
    return route('PUT', path, body);
  }
  async function del(path, body) {
    if (config.baseUrl) return http('DELETE', path, null, body);
    await latency();
    return route('DELETE', path, body);
  }

  return { config, get, post, put, del };
})();
