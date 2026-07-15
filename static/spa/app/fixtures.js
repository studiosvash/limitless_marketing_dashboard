/* ============================================================================
   FuseHealth / Limitless marketing dashboard — demo fixtures
   ----------------------------------------------------------------------------
   Deterministic, seeded demo data shaped EXACTLY like the REST contract the
   Django backend will implement (see API_CONTRACT.md). The frontend never
   reads this file directly — it goes through FuseAPI (app/api.js), which
   serves these fixtures until FuseAPI.config.baseUrl points at the real API.
   ============================================================================ */
window.FuseFixtures = (function () {
  'use strict';

  /* ---------- seeded RNG ---------- */
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hashStr(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  /* ---------- projects ---------- */
  const PROJECTS = [
    {
      id: 'fusehealth', domain: 'fusehealth.com', name: 'FuseHealth',
      vertical: 'IV therapy & wellness', seed: 11, location: 'United States',
      competitors: ['driphydration.com', 'restoreiv.com', 'mobileivmedics.com'],
      linkDomains: ['healthline.com', 'wellnessmama.com', 'austinchronicle.com', 'yelp.com', 'reddit.com', 'mindbodygreen.com', 'austinmonthly.com', 'expertise.com', 'localdirectory.net', 'medicalnewstoday.com', 'thumbtack.com', 'groupon.com', 'healthgrades.com', 'vagaro.com'],
      pages: [
        ['/services/iv-therapy', 'ok'], ['/services/nad-therapy', 'ok'], ['/services/vitamin-injections', 'ok'],
        ['/services/mobile-iv', 'ok'], ['/locations/austin', 'ok'], ['/locations/dallas', 'ok'],
        ['/locations/houston', 'ok'], ['/blog/nad-benefits', 'ok'], ['/blog/hydration-guide', 'ok'],
        ['/blog/myers-cocktail-explained', 'ok'], ['/blog/iv-therapy-cost', 'ok'], ['/blog/hangover-remedies', 'ok'],
        ['/pricing', 'ok'], ['/about', 'ok'], ['/book', 'ok'],
        ['/blog/old-promo-2023', 'gone'], ['/services/legacy-drip', 'redirect'], ['/blog/staging-draft', 'noindex']
      ],
      bank: [
        ['iv therapy near me', 9900], ['iv drip near me', 3600], ['iv therapy austin', 2400],
        ['hydration iv therapy', 2400], ['what is iv therapy', 1900], ['mobile iv therapy', 1900],
        ['iv therapy cost', 1600], ['myers cocktail iv', 1300], ['vitamin infusion therapy', 1000],
        ['vitamin b12 injection near me', 1000], ['nad+ infusion near me', 880], ['glutathione iv', 880],
        ['hangover iv austin', 720], ['myers cocktail benefits', 720], ['wellness clinic austin', 590],
        ['immune boost iv', 590], ['mobile iv therapy dallas', 590], ['iv therapy prices', 590],
        ['nad+ therapy benefits', 480], ['hangover cure iv', 480], ['iv hydration houston', 480],
        ['iv vitamin therapy benefits', 390], ['nad iv therapy cost', 390], ['b12 shots austin', 320],
        ['iv therapy for athletes', 320], ['best iv therapy austin', 260], ['energy iv drip', 210],
        ['iv therapy membership', 170]
      ]
    },
    {
      id: 'limitless', domain: 'limitlesshold.com', name: 'Limitless Holdings',
      vertical: 'Growth marketing group', seed: 29, location: 'United States',
      competitors: ['webfx.com', 'thriveagency.com', 'ignitevisibility.com'],
      linkDomains: ['clutch.co', 'upcity.com', 'g2.com', 'hubspot.com', 'searchenginejournal.com', 'forbes.com', 'austininno.com', 'linkedin.com', 'medium.com', 'designrush.com', 'reddit.com', 'expertise.com'],
      pages: [
        ['/services/seo', 'ok'], ['/services/ppc', 'ok'], ['/services/fractional-cmo', 'ok'],
        ['/services/content', 'ok'], ['/work', 'ok'], ['/industries/saas', 'ok'],
        ['/industries/healthcare', 'ok'], ['/blog/seo-cost-guide', 'ok'], ['/blog/cmo-vs-vp-marketing', 'ok'],
        ['/blog/local-seo-checklist', 'ok'], ['/pricing', 'ok'], ['/about', 'ok'], ['/contact', 'ok'],
        ['/blog/2022-marketing-trends', 'gone'], ['/lp/old-webinar', 'noindex']
      ],
      bank: [
        ['digital marketing services', 2900], ['local seo services', 2400], ['google ads agency', 1900],
        ['fractional cmo', 1600], ['marketing agency austin', 1300], ['content marketing agency', 1300],
        ['what does a cmo do', 1000], ['ppc management agency', 880], ['how much does seo cost', 880],
        ['seo services austin', 720], ['growth marketing agency', 720], ['marketing consultant near me', 720],
        ['b2b lead generation agency', 590], ['email marketing agency', 590], ['brand strategy agency', 480],
        ['saas marketing agency', 480], ['seo audit services', 390], ['linkedin ads agency', 320],
        ['conversion rate optimization agency', 260], ['best marketing agencies austin', 210]
      ]
    },
    {
      id: 'auremed', domain: 'auremedspa.com', name: 'Auré Med Spa',
      vertical: 'Medical spa', seed: 47, location: 'United States',
      competitors: ['idealimage.com', 'laseraway.com', 'skinspirit.com'],
      linkDomains: ['realself.com', 'allure.com', 'byrdie.com', 'yelp.com', 'groupon.com', 'austinmonthly.com', 'newbeauty.com', 'healthgrades.com', 'tripadvisor.com', 'expertise.com', 'reddit.com'],
      pages: [
        ['/treatments/botox', 'ok'], ['/treatments/fillers', 'ok'], ['/treatments/hydrafacial', 'ok'],
        ['/treatments/laser-hair-removal', 'ok'], ['/treatments/microneedling', 'ok'], ['/treatments/morpheus8', 'ok'],
        ['/blog/dysport-vs-botox', 'ok'], ['/blog/botox-aftercare', 'ok'], ['/blog/hydrafacial-guide', 'ok'],
        ['/pricing', 'ok'], ['/about', 'ok'], ['/book', 'ok'],
        ['/specials/summer-2024', 'gone'], ['/blog/draft-prp', 'noindex']
      ],
      bank: [
        ['lip filler near me', 4400], ['botox austin', 2900], ['laser hair removal austin', 2400],
        ['what is a hydrafacial', 2400], ['hydrafacial cost', 1900], ['med spa austin', 1600],
        ['dysport vs botox', 1600], ['microneedling benefits', 1300], ['dermal fillers cost', 1000],
        ['facial austin', 1000], ['chemical peel near me', 880], ['botox aftercare', 880],
        ['prp facial', 720], ['skin tightening treatment', 720], ['kybella near me', 590],
        ['laser facial', 590], ['morpheus8 austin', 480], ['best med spa austin', 390],
        ['juvederm austin', 320], ['botox membership', 170]
      ]
    }
  ];

  const KNOWN_RANK = {
    'healthline.com': 88, 'forbes.com': 92, 'reddit.com': 90, 'linkedin.com': 94, 'hubspot.com': 89,
    'yelp.com': 87, 'medium.com': 86, 'groupon.com': 82, 'g2.com': 80, 'allure.com': 84,
    'searchenginejournal.com': 79, 'medicalnewstoday.com': 85, 'realself.com': 76, 'clutch.co': 74,
    'mindbodygreen.com': 72, 'byrdie.com': 73, 'tripadvisor.com': 88, 'wellnessmama.com': 46,
    'newbeauty.com': 58, 'healthgrades.com': 71, 'austinchronicle.com': 62, 'austinmonthly.com': 48,
    'upcity.com': 52, 'designrush.com': 55, 'expertise.com': 50, 'austininno.com': 44,
    'thumbtack.com': 68, 'vagaro.com': 47, 'localdirectory.net': 21
  };

  /* ---------- helpers ---------- */
  function classifyIntent(kw) {
    if (/(near me|book|buy|membership)/.test(kw)) return 'transactional';
    if (/(cost|price|prices|how much)/.test(kw)) return 'transactional';
    if (/(what|how|benefits|guide|explained|aftercare|vs )/.test(kw)) return 'informational';
    if (/(best |agency|services|austin|dallas|houston|clinic|spa)/.test(kw)) return 'commercial';
    return 'informational';
  }
  function ctrForPos(p) {
    if (p <= 1) return 0.28; if (p <= 2) return 0.15; if (p <= 3) return 0.10;
    if (p <= 5) return 0.065; if (p <= 10) return 0.03; if (p <= 20) return 0.011;
    return 0.003;
  }
  const DAY = 86400000;
  function iso(ts) { return new Date(ts).toISOString().slice(0, 10); }

  /* ---------- add a new site at runtime ---------- */
  const GENERIC_LINK_DOMAINS = ['reddit.com', 'linkedin.com', 'medium.com', 'g2.com', 'yelp.com', 'forbes.com', 'clutch.co', 'trustpilot.com', 'youtube.com', 'quora.com'];
  const GENERIC_PAGES = [
    ['/services', 'ok'], ['/pricing', 'ok'], ['/about', 'ok'], ['/contact', 'ok'],
    ['/blog/getting-started', 'ok'], ['/blog/how-it-works', 'ok'], ['/blog/customer-stories', 'ok'],
    ['/faq', 'ok'], ['/locations', 'ok'], ['/book', 'ok'],
    ['/blog/old-announcement', 'gone'], ['/lp/legacy-offer', 'redirect'], ['/blog/staging-draft', 'noindex']
  ];
  function slugify(s) {
    return s.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split(/[.\/]/)[0].replace(/[^a-z0-9]/g, '') || 'site';
  }
  function brandFromDomain(domain) {
    const root = slugify(domain);
    return root.charAt(0).toUpperCase() + root.slice(1);
  }
  function addProject(domain, opts) {
    opts = opts || {};
    domain = (domain || '').trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/$/, '');
    if (!domain) throw new Error('Domain required');
    let id = slugify(domain);
    let n = 1;
    while (PROJECTS.some(p => p.id === id)) { n++; id = slugify(domain) + n; }
    const brand = opts.name || brandFromDomain(domain);
    const seed = hashStr(domain) % 1000;
    const bankSeeds = ['{b} reviews', '{b} pricing', '{b} alternatives', 'is {b} worth it', 'what is {b}',
      'best {b} plans', '{b} vs competitors', '{b} customer service', '{b} near me', 'how does {b} work',
      '{b} discount code', '{b} sign up'];
    const bank = bankSeeds.map((tpl, i) => [tpl.replace(/\{b\}/g, brand.toLowerCase()), Math.max(30, 2400 - i * 190)]);
    const p = {
      id, domain, name: brand,
      vertical: opts.vertical || 'General business', seed, location: opts.location || 'United States',
      competitors: [],
      linkDomains: GENERIC_LINK_DOMAINS.slice(),
      pages: GENERIC_PAGES.slice(),
      bank
    };
    PROJECTS.push(p);
    return { id: p.id, domain: p.domain, name: p.name, vertical: p.vertical, location: p.location };
  }

  /* ---------- per-project generator ---------- */
  const cache = {};
  function build(projectId) {
    if (cache[projectId]) return cache[projectId];
    const p = PROJECTS.find(x => x.id === projectId);
    if (!p) return null;
    const rnd = mulberry32(p.seed);
    const ri = (a, b) => Math.floor(rnd() * (b - a + 1)) + a;
    const pick = arr => arr[Math.floor(rnd() * arr.length)];
    const now = Date.now();

    const goodPages = p.pages.filter(x => x[1] === 'ok').map(x => x[0]);

    /* ----- keywords ----- */
    const keywords = p.bank.map((entry, i) => {
      const kw = entry[0], baseVol = entry[1];
      const volume = Math.round(baseVol * (0.9 + rnd() * 0.25));
      const r = rnd();
      const pos = r < 0.16 ? ri(1, 3) : r < 0.46 ? ri(4, 10) : r < 0.72 ? ri(11, 20) : ri(21, 58);
      const mv = rnd();
      const prevPos = clamp(pos + (mv < 0.22 ? ri(2, 6) : mv < 0.42 ? -ri(2, 5) : ri(-1, 1)), 1, 100);
      const isNew = rnd() < 0.05 && pos <= 20;
      const intent = classifyIntent(kw);
      const kd = clamp(Math.round(16 + Math.log10(volume) * 13 + ri(-12, 18)), 4, 88);
      const cpc = +(intent === 'transactional' ? 2 + rnd() * 6 : intent === 'commercial' ? 1.5 + rnd() * 4 : 0.3 + rnd() * 1.6).toFixed(2);
      const impressions = Math.round(volume * (pos <= 10 ? 0.55 + rnd() * 0.3 : pos <= 20 ? 0.25 + rnd() * 0.2 : 0.05 + rnd() * 0.1));
      const ctr = ctrForPos(pos) * (0.75 + rnd() * 0.5);
      const clicks = Math.round(impressions * ctr);
      const monthly = [];
      for (let m = 0; m < 12; m++) monthly.push(Math.round(volume * (0.75 + rnd() * 0.45)));
      monthly[11] = volume;
      return {
        id: p.id + '-kw-' + i, kw, intent, pos, prevPos: isNew ? null : prevPos,
        volume, kd, cpc, clicks, impressions, ctr: +(ctr * 100).toFixed(1),
        url: goodPages[i % goodPages.length], monthly, source: 'sync',
        serpFeatures: pick([['featured_snippet', 'people_also_ask'], ['local_pack', 'reviews'], ['people_also_ask'], ['images', 'video'], []])
      };
    });

    /* ----- pages / audit ----- */
    const clicksByUrl = {};
    keywords.forEach(k => { clicksByUrl[k.url] = (clicksByUrl[k.url] || 0) + k.clicks; });
    const pages = p.pages.map((entry, i) => {
      const url = entry[0], kind = entry[1];
      const kwClicks = clicksByUrl[url] || 0;
      const clicks = kind === 'ok' ? kwClicks + ri(0, 60) : 0;
      const impressions = kind === 'ok' ? Math.round(clicks * (14 + rnd() * 14)) + ri(50, 400) : (kind === 'gone' ? ri(200, 1400) : ri(0, 450));
      const speed = kind === 'ok' ? ri(38, 97) : ri(28, 55);
      const indexed = kind === 'ok' ? rnd() > 0.06 : false;
      const verdict = kind === 'gone' ? '404 Not Found' : kind === 'redirect' ? 'Redirect chain (3 hops)' : kind === 'noindex' ? 'Excluded by noindex' : (indexed ? 'Indexed' : 'Crawled – not indexed');
      return {
        id: p.id + '-pg-' + i, url, clicks, impressions,
        ctr: impressions ? +((clicks / impressions) * 100).toFixed(1) : 0,
        speed, indexed: kind === 'ok' ? indexed : false, kind, verdict,
        title_length: ri(28, 74), word_count: ri(240, 2400)
      };
    });

    /* ----- backlinks ----- */
    const nLinks = 34 + ri(0, 10);
    const backlinks = [];
    for (let i = 0; i < nLinks; i++) {
      const domain = pick(p.linkDomains);
      const baseRank = KNOWN_RANK[domain] || (18 + (hashStr(domain) % 40));
      const status = rnd() < 0.9 ? 'live' : 'lost';
      const firstSeen = now - ri(10, 320) * DAY;
      backlinks.push({
        id: p.id + '-bl-' + i, domain,
        anchor: rnd() < 0.25 ? p.name.toLowerCase() : pick(keywords).kw,
        type: rnd() < 0.78 ? 'dofollow' : 'nofollow',
        status, rank: clamp(baseRank + ri(-4, 4), 5, 95),
        firstSeen: iso(firstSeen),
        lostAt: status === 'lost' ? iso(now - ri(2, 45) * DAY) : null,
        target: pick(goodPages)
      });
    }
    backlinks.sort((a, b) => (b.firstSeen > a.firstSeen ? 1 : -1));

    /* ----- 90-day traffic series ----- */
    const totalClicks = keywords.reduce((s, k) => s + k.clicks, 0);
    const series = [];
    const dailyBase = Math.max(8, totalClicks / 30);
    for (let d = 89; d >= 0; d--) {
      const ts = now - d * DAY;
      const dow = new Date(ts).getDay();
      const wf = (dow === 0 || dow === 6) ? 0.72 : 1;
      const growth = 1 + (89 - d) * 0.0022;
      const dip = (d >= 3 && d <= 4) ? 0.62 : 1; // recent anomaly window
      const clicks = Math.round(dailyBase * wf * growth * dip * (0.85 + rnd() * 0.3));
      series.push({ date: iso(ts), clicks, impressions: Math.round(clicks * (17 + rnd() * 9)) });
    }

    /* ----- competitors ----- */
    const compRows = keywords.slice().sort((a, b) => b.volume - a.volume).slice(0, 12).map(k => ({
      kw: k.kw, you: k.pos,
      comps: p.competitors.map(() => (rnd() < 0.18 ? null : clamp(k.pos + ri(-6, 14), 1, 80)))
    }));

    /* ----- countries ----- */
    const countries = [
      { country: 'United States', share: 0.78 }, { country: 'Canada', share: 0.10 },
      { country: 'United Kingdom', share: 0.05 }, { country: 'Australia', share: 0.04 },
      { country: 'Other', share: 0.03 }
    ].map(c => ({
      country: c.country, clicks: Math.round(totalClicks * c.share),
      ctr: +(3 + rnd() * 2.2).toFixed(1)
    }));

    /* ----- ads (Google Ads API + GA4 Data API, pulled every 12h) ----- */
    const avgOrder = 120 + (hashStr(p.id) % 90);
    // name, platform, type, status, budget/day, spend/day, clicks/day, cvr, lostIS(budget), lostIS(rank), groups
    const CMP_DEFS = [
      ['Brand — Search', 'Google Ads', 'Search', 'enabled', 38, 31, 18, 0.058, 3, 2,
        ['Exact — brand terms', 'Phrase — brand + service', 'Broad — misspellings']],
      ['Non-Brand — Search', 'Google Ads', 'Search', 'enabled', 60, 52, 26, 0.021, 19, 8,
        ['Exact — core services', 'Phrase — near me', 'Broad — new intents']],
      ['Performance Max — Services', 'Google Ads', 'Performance Max', 'enabled', 48, 43, 31, 0.028, 24, 5,
        ['Asset group — Services', 'Asset group — Locations']],
      ['Competitor — Search', 'Google Ads', 'Search', 'paused', 25, 9, 6, 0.011, 0, 0,
        ['Exact — competitor brands']],
      ['Retargeting — Site Visitors', 'Meta', 'Retargeting', 'enabled', 30, 25, 39, 0.015, 0, 0,
        ['Ad set — 30d visitors', 'Ad set — booking abandoners']],
      ['Prospecting — Lookalike', 'Meta', 'Prospecting', 'enabled', 34, 28, 34, 0.009, 0, 0,
        ['Ad set — 1% lookalike', 'Ad set — interest stack']]
    ];
    const adCampaigns = CMP_DEFS.map((cd, ci) => {
      const daily = [];
      for (let i = 89; i >= 0; i--) {
        const dt = new Date(now - i * DAY);
        const wk = [0.72, 1, 1.06, 1.08, 1.04, 0.97, 0.8][dt.getDay()];
        const off = cd[3] === 'paused' && i < 34; // paused ~5 weeks ago
        const spend = off ? 0 : +(cd[5] * wk * (0.75 + rnd() * 0.5)).toFixed(2);
        const clicks = off ? 0 : Math.max(1, Math.round(cd[6] * wk * (0.7 + rnd() * 0.6)));
        const conversions = off ? 0 : +(clicks * cd[7] * (0.6 + rnd() * 0.9)).toFixed(2);
        const conv_value = +(conversions * avgOrder * (0.8 + rnd() * 0.5)).toFixed(2);
        daily.push({
          date: iso(now - i * DAY), spend, clicks,
          impressions: clicks * ri(16, 34), conversions, conv_value,
          ga4_key_events: +(conversions * (0.66 + rnd() * 0.26)).toFixed(2),
          ga4_revenue: +(conv_value * (0.64 + rnd() * 0.28)).toFixed(2)
        });
      }
      const shares = cd[10].map(() => 0.4 + rnd());
      const shareSum = shares.reduce((a2, x) => a2 + x, 0);
      return {
        id: p.id + '-cmp-' + ci, name: cd[0], platform: cd[1], type: cd[2], status: cd[3],
        budgetDaily: cd[4], lostISBudget: cd[8], lostISRank: cd[9],
        adGroups: cd[10].map((g, gi) => ({ id: p.id + '-ag-' + ci + '-' + gi, name: g, share: +(shares[gi] / shareSum).toFixed(3) })),
        daily
      };
    });

    const gAdsCmps = adCampaigns.filter(c => c.platform === 'Google Ads' && c.status === 'enabled');
    const stKws = keywords.slice().sort((a2, b2) => b2.volume - a2.volume).slice(0, 9);
    const searchTerms = [];
    stKws.forEach((k, j) => {
      const cmp = gAdsCmps[j % gAdsCmps.length];
      const clicks = ri(14, 95);
      searchTerms.push({
        id: p.id + '-st-' + j, term: k.kw, matchedKeyword: k.kw,
        matchType: ['exact', 'phrase', 'broad'][j % 3],
        campaignId: cmp.id, campaign: cmp.name,
        impressions: clicks * ri(12, 28), clicks,
        cost: +(clicks * (0.8 + rnd() * 3.2)).toFixed(2),
        conversions: rnd() < 0.72 ? +(clicks * (0.012 + rnd() * 0.05)).toFixed(1) : 0
      });
    });
    const junkBase = [stKws[0].kw, (stKws[1] || stKws[0]).kw, (stKws[2] || stKws[0]).kw];
    ['free ' + junkBase[0], junkBase[1] + ' jobs', 'diy ' + junkBase[2], junkBase[0] + ' reddit review'].forEach((t2, j) => {
      const cmp = gAdsCmps[(j + 1) % gAdsCmps.length];
      const clicks = ri(9, 42);
      searchTerms.push({
        id: p.id + '-stx-' + j, term: t2, matchedKeyword: junkBase[j % 3],
        matchType: 'broad', campaignId: cmp.id, campaign: cmp.name,
        impressions: clicks * ri(15, 32), clicks,
        cost: +(clicks * (0.7 + rnd() * 2.6)).toFixed(2), conversions: 0
      });
    });
    searchTerms.sort((a2, b2) => b2.cost - a2.cost);

    const enabledCmps = adCampaigns.filter(c => c.status === 'enabled');
    const adLandingPages = pages.filter(x => x.kind === 'ok').slice(0, 6).map((pg, j) => {
      const cmp = enabledCmps[j % enabledCmps.length];
      const sessions = ri(160, 940);
      return {
        id: p.id + '-lp-' + j, url: pg.url, campaignId: cmp.id, campaign: cmp.name,
        sessions, engagedRate: +(0.3 + rnd() * 0.42).toFixed(2),
        keyEvents: +(sessions * (0.015 + rnd() * 0.05)).toFixed(1),
        revenue: Math.round(sessions * (0.02 + rnd() * 0.05) * avgOrder)
      };
    });

    const ads = { campaigns: adCampaigns, searchTerms, landingPages: adLandingPages, avgOrder };

    /* ----- alerts feed ----- */
    const feed = [];
    let ai = 0;
    const push = (daysAgo, severity, kind, title, detail) =>
      feed.push({ id: p.id + '-al-' + (ai++), ts: iso(now - daysAgo * DAY), severity, kind, title, detail });
    push(3, 'high', 'anomaly', 'Clicks dropped 38% vs. daily average', 'Organic clicks fell sharply on ' + iso(now - 4 * DAY) + '. Check GSC for manual actions or SERP volatility.');
    const decliners = keywords.filter(k => k.prevPos && k.pos - k.prevPos >= 3).slice(0, 2);
    decliners.forEach((k, j) => push(4 + j, 'high', 'ranking', '"' + k.kw + '" dropped ' + (k.pos - k.prevPos) + ' positions', 'Now #' + k.pos + ' (was #' + k.prevPos + '). Volume ' + k.volume.toLocaleString() + '/mo.'));
    backlinks.filter(b => b.status === 'lost').slice(0, 2).forEach((b, j) =>
      push(5 + j, 'medium', 'backlink', 'Lost backlink from ' + b.domain, 'Anchor "' + b.anchor + '" (rank ' + b.rank + ') last seen ' + b.lostAt + '.'));
    const gone = pages.filter(x => x.kind === 'gone');
    if (gone.length) push(8, 'high', 'technical', gone.length + ' page(s) returning 404', gone.map(x => x.url).join(', ') + ' — still receiving impressions and backlinks.');
    push(6, 'medium', 'anomaly', 'Impressions up 22% vs. weekly average', 'Sustained impression growth without matching clicks — review titles on rising pages.');
    push(1, 'medium', 'ads', '"Non-Brand — Search" limited by budget', 'Lost 19% impression share to budget over the last 7 days — raise the daily cap or add negatives to cut waste.');
    push(2, 'high', 'ads', 'CPA spike on "Performance Max — Services"', 'Cost per conversion up 41% vs. the prior 7 days while spend held steady. Review asset group performance.');
    push(11, 'info', 'ads', '"Competitor — Search" paused', 'Paused after ROAS held under 0.8 for three weeks. Budget reallocated to Non-Brand — Search.');
    push(9, 'info', 'system', 'Weekly sync completed', keywords.length + ' keywords, ' + backlinks.length + ' backlinks, ' + pages.length + ' pages refreshed.');
    feed.sort((a, b) => (a.ts < b.ts ? 1 : -1));

    /* ----- settings ----- */
    const settings = {
      credentials: { gsc_property: 'sc-domain:' + p.domain, ga4_property_id: String(500000000 + (hashStr(p.domain) % 99999999)) },
      connectors: [
        { name: 'Search Console', status: 'ok', last_sync: iso(now - 1 * DAY), records: totalClicks },
        { name: 'Analytics 4', status: 'ok', last_sync: iso(now), records: Math.round(totalClicks * 0.6) },
        { name: 'Google Ads', status: 'ok', last_sync: iso(now), records: adCampaigns.length * 90 },
        { name: 'DataForSEO', status: 'ok', last_sync: iso(now - 2 * DAY), records: keywords.length + backlinks.length },
        { name: 'OpenAI (summaries)', status: 'ok', last_sync: iso(now - 2 * DAY), records: 4 }
      ],
      prefs: { email_alerts: true, weekly_digest: true },
      sync: { cadence: 'weekly', day: 'Monday', next_run: iso(now + ((8 - new Date(now).getDay()) % 7 || 7) * DAY) }
    };

    /* ----- site audit (OnPage-shaped) ----- */
    const AUDIT_CHECKS = [
      ['broken_pages', 'error', 'Crawlability', 'Broken pages (4xx/5xx)', 'Restore the page or 301-redirect it to the closest live equivalent; update internal links pointing at it.'],
      ['broken_internal_links', 'error', 'Internal Linking', 'Broken internal links', 'Update or remove links that point to 4xx/5xx URLs.'],
      ['duplicate_titles', 'error', 'Content', 'Duplicate title tags', 'Write a unique, descriptive title (50\u201360 chars) for each page.'],
      ['missing_title', 'error', 'Content', 'Missing title tag', 'Add a <title> element describing the page\u2019s primary topic.'],
      ['duplicate_content', 'error', 'Content', 'Duplicate content', 'Canonicalize to one URL or differentiate the pages substantially.'],
      ['canonical_to_broken', 'error', 'Crawlability', 'Canonical points to broken/redirected URL', 'Point rel=canonical at the final, 200-status URL.'],
      ['redirect_chains', 'error', 'Crawlability', 'Redirect chains & loops', 'Point redirects and internal links directly at the final URL (max 1 hop).'],
      ['mixed_content', 'error', 'HTTPS', 'Mixed content (HTTP resources on HTTPS page)', 'Serve all scripts, styles and images over HTTPS.'],
      ['huge_page_size', 'error', 'Performance', 'Page size over 3 MB', 'Compress images, remove unused scripts, enable text compression.'],
      ['title_too_long', 'warning', 'Content', 'Title too long (>60 chars)', 'Shorten the title so it does not truncate in SERPs.'],
      ['missing_description', 'warning', 'Content', 'Missing meta description', 'Add a 120\u2013155 char description with the primary keyword.'],
      ['duplicate_descriptions', 'warning', 'Content', 'Duplicate meta descriptions', 'Write a unique description per page.'],
      ['low_word_count', 'warning', 'Content', 'Thin content (<250 words)', 'Expand the page to properly cover its topic or merge it into a stronger page.'],
      ['slow_load', 'warning', 'Performance', 'Slow page load (>3 s)', 'Optimize LCP element, defer non-critical JS, use a CDN.'],
      ['missing_alt_tags', 'warning', 'Content', 'Images missing alt attributes', 'Add descriptive alt text to meaningful images.'],
      ['temporary_redirects', 'warning', 'Crawlability', 'Temporary (302) redirects', 'Use 301 for permanent moves so equity consolidates.'],
      ['links_to_redirects', 'warning', 'Internal Linking', 'Internal links to redirected URLs', 'Update links to the final destination URL.'],
      ['no_h1', 'warning', 'Content', 'Missing H1 heading', 'Add a single H1 matching search intent.'],
      ['multiple_h1', 'warning', 'Content', 'Multiple H1 headings', 'Keep one H1; demote the rest to H2.'],
      ['https_to_http_links', 'warning', 'HTTPS', 'HTTPS page links to HTTP pages', 'Update outgoing links to HTTPS targets.'],
      ['uncompressed_pages', 'warning', 'Performance', 'No text compression (gzip/brotli)', 'Enable gzip or brotli on the server.'],
      ['unminified_resources', 'warning', 'Performance', 'Unminified JS / CSS', 'Minify bundles in the build pipeline.'],
      ['orphaned_pages', 'notice', 'Internal Linking', 'Orphaned pages (no incoming internal links)', 'Link to the page from relevant hub or navigation pages.'],
      ['deep_pages', 'notice', 'Crawlability', 'Page crawl depth more than 3 clicks', 'Surface the page from a category or hub page closer to home.'],
      ['long_urls', 'notice', 'Content', 'URL longer than 100 characters', 'Prefer short, readable slugs.'],
      ['nofollow_internal', 'notice', 'Internal Linking', 'Internal links with rel=nofollow', 'Remove nofollow from internal links unless intentional.'],
      ['no_structured_data', 'notice', 'Markup', 'No structured data (schema.org)', 'Add Organization / Service / FAQ schema where relevant.'],
      ['multiple_canonicals', 'notice', 'Crawlability', 'Multiple canonical tags', 'Keep exactly one rel=canonical per page.'],
      ['blocked_by_robots', 'notice', 'Crawlability', 'Blocked by robots.txt', 'Confirm the block is intentional; blocked pages cannot rank.']
    ];
    const EXTRA_PATHS = ['/blog/hydration-myths', '/blog/what-is-nad', '/blog/event-recovery-guide', '/blog/electrolytes-explained', '/blog/b12-benefits', '/blog/hangover-science', '/resources/faq', '/resources/pricing-guide', '/resources/first-visit', '/about/team', '/about/press', '/careers', '/reviews', '/gift-cards', '/blog', '/resources', '/blog/immune-boost-basics', '/blog/athletes-and-ivs', '/blog/migraine-relief-options', '/blog/wellness-trends-2026'];
    const crawledPages = [];
    const failMap = {};       /* checkId -> [urls] */
    const fail = (id, url) => { (failMap[id] = failMap[id] || []).push(url); };
    const allPaths = p.pages.map(e => [e[0], e[1]]).concat(EXTRA_PATHS.map((u, i) => [u, rnd() < 0.06 ? 'gone' : 'ok']));
    allPaths.forEach((entry, i) => {
      const url = entry[0], kind = entry[1];
      const seg = url.split('/').filter(Boolean);
      const depth = Math.min(seg.length, 4) + (rnd() < 0.12 ? 1 : 0);
      const statusCode = kind === 'gone' ? (rnd() < 0.75 ? 404 : 500) : kind === 'redirect' ? (rnd() < 0.6 ? 301 : 302) : 200;
      const loadTimeMs = kind === 'ok' ? ri(420, 4400) : ri(200, 900);
      const wordCount = kind === 'ok' ? ri(140, 2400) : 0;
      const inLinks = depth <= 1 ? ri(14, 60) : depth === 2 ? ri(3, 18) : ri(0, 6);
      const failed = [];
      const f = (id, prob) => { if (rnd() < prob) { fail(id, url); failed.push(id); } };
      if (kind === 'gone') { fail('broken_pages', url); failed.push('broken_pages'); }
      if (kind === 'redirect') { fail('redirect_chains', url); failed.push('redirect_chains'); if (statusCode === 302) { fail('temporary_redirects', url); failed.push('temporary_redirects'); } }
      if (kind === 'noindex') { fail('blocked_by_robots', url); failed.push('blocked_by_robots'); }
      if (kind === 'ok') {
        f('broken_internal_links', 0.10); f('duplicate_titles', 0.08); f('missing_title', 0.03);
        f('duplicate_content', 0.05); f('canonical_to_broken', 0.04); f('mixed_content', 0.04);
        if (loadTimeMs > 3000) { fail('slow_load', url); failed.push('slow_load'); }
        f('huge_page_size', loadTimeMs > 2800 ? 0.35 : 0.04);
        f('title_too_long', 0.16); f('missing_description', 0.18); f('duplicate_descriptions', 0.10);
        if (wordCount < 250) { fail('low_word_count', url); failed.push('low_word_count'); }
        f('missing_alt_tags', 0.22); f('links_to_redirects', 0.12); f('no_h1', 0.06); f('multiple_h1', 0.07);
        f('https_to_http_links', 0.05); f('uncompressed_pages', 0.06); f('unminified_resources', 0.14);
        if (inLinks === 0) { fail('orphaned_pages', url); failed.push('orphaned_pages'); }
        if (depth > 3) { fail('deep_pages', url); failed.push('deep_pages'); }
        if (url.length > 34) f('long_urls', 0.3);
        f('nofollow_internal', 0.05); f('no_structured_data', 0.30); f('multiple_canonicals', 0.03);
      }
      const sevCount = { error: 0, warning: 0, notice: 0 };
      failed.forEach(id => { const c = AUDIT_CHECKS.find(x => x[0] === id); if (c) sevCount[c[1]]++; });
      const score = kind !== 'ok' ? (kind === 'redirect' ? 55 : 0) : clamp(Math.round(100 - sevCount.error * 22 - sevCount.warning * 7 - sevCount.notice * 2 - ri(0, 4)), 8, 100);
      crawledPages.push({
        id: p.id + '-cp-' + i, url, statusCode, kind, depth,
        score, errors: sevCount.error, warnings: sevCount.warning, notices: sevCount.notice,
        inLinks, internalLinks: kind === 'ok' ? ri(4, 42) : 0, externalLinks: kind === 'ok' ? ri(0, 9) : 0,
        loadTimeMs, wordCount, failed,
        cwv: kind === 'ok' ? { lcp: +(1.2 + rnd() * 3.8).toFixed(1), tbt: ri(30, 980), cls: +(rnd() * 0.42).toFixed(2) } : null
      });
    });
    const auditChecks = AUDIT_CHECKS.map(c => ({
      id: c[0], severity: c[1], category: c[2], title: c[3], howToFix: c[4], pages: failMap[c[0]] || []
    })).filter(c => c.pages.length || true);
    const okPages = crawledPages.filter(x => x.kind === 'ok');
    const errN = auditChecks.filter(c => c.severity === 'error').reduce((s, c) => s + c.pages.length, 0);
    const warnN = auditChecks.filter(c => c.severity === 'warning').reduce((s, c) => s + c.pages.length, 0);
    const auditScore = clamp(Math.round(100 - (errN * 3.2 + warnN * 0.8) / crawledPages.length * 10), 20, 98);
    const catScore = {};
    ['Crawlability', 'HTTPS', 'Internal Linking', 'Markup', 'Performance', 'Content'].forEach(cat => {
      const cs = auditChecks.filter(c => c.category === cat);
      const weighted = cs.reduce((s, c) => s + c.pages.length * (c.severity === 'error' ? 3 : c.severity === 'warning' ? 1 : 0.3), 0);
      catScore[cat] = clamp(Math.round(100 - weighted / crawledPages.length * 14), 25, 100);
    });
    const cwvBucket = (arr, good, poor) => ({
      good: arr.filter(v => v <= good).length,
      mid: arr.filter(v => v > good && v <= poor).length,
      poor: arr.filter(v => v > poor).length
    });
    const lcps = okPages.map(x => x.cwv.lcp), tbts = okPages.map(x => x.cwv.tbt), clss = okPages.map(x => x.cwv.cls);
    const p75 = arr => { const s = arr.slice().sort((a, b) => a - b); return s[Math.floor(s.length * 0.75)]; };
    const audit = {
      score: auditScore,
      crawl: {
        status: 'finished', pagesCrawled: crawledPages.length, maxPages: 500,
        startedAt: iso(now - 2 * DAY), duration: ri(4, 11) + 'm ' + ri(5, 55) + 's', userAgent: 'FuseBot/1.0 (DataForSEO OnPage)'
      },
      domainChecks: [
        { id: 'ssl', label: 'SSL certificate', ok: true, detail: 'Valid \u00b7 expires in ' + ri(90, 300) + ' days' },
        { id: 'sitemap', label: 'Sitemap.xml', ok: rnd() > 0.15, detail: '/sitemap.xml' },
        { id: 'robots', label: 'Robots.txt', ok: true, detail: '/robots.txt \u00b7 ' + ri(4, 14) + ' rules' },
        { id: 'http2', label: 'HTTP/2', ok: rnd() > 0.25, detail: 'Protocol support' },
        { id: 'www', label: 'WWW redirect', ok: rnd() > 0.2, detail: 'non-www \u2192 www consolidated' }
      ],
      breakdown: {
        healthy: okPages.filter(x => x.errors === 0 && x.warnings === 0).length,
        withIssues: okPages.filter(x => x.errors > 0 || x.warnings > 0).length,
        broken: crawledPages.filter(x => x.kind === 'gone').length,
        redirected: crawledPages.filter(x => x.kind === 'redirect').length,
        blocked: crawledPages.filter(x => x.kind === 'noindex').length
      },
      catScore,
      cwv: {
        lcp: { p75: +p75(lcps).toFixed(1), unit: 's', good: 2.5, poor: 4, buckets: cwvBucket(lcps, 2.5, 4) },
        tbt: { p75: Math.round(p75(tbts)), unit: 'ms', good: 200, poor: 600, buckets: cwvBucket(tbts, 200, 600) },
        cls: { p75: +p75(clss).toFixed(2), unit: '', good: 0.1, poor: 0.25, buckets: cwvBucket(clss, 0.1, 0.25) }
      },
      checks: auditChecks,
      crawledPages
    };

    /* ----- crawl history snapshots (weekly, oldest → latest) ----- */
    const sevOf = {};
    AUDIT_CHECKS.forEach(c => { sevOf[c[0]] = c[1]; });
    const curCounts = {};
    auditChecks.forEach(c => { curCounts[c.id] = c.pages.length; });
    const snapRaw = [{ byCheck: Object.assign({}, curCounts), score: auditScore, pagesCrawled: crawledPages.length }];
    let walk = Object.assign({}, curCounts), walkScore = auditScore, walkPages = crawledPages.length;
    for (let k = 1; k < 8; k++) {
      const prev = {};
      Object.keys(walk).forEach(id => {
        const r = rnd();
        const drift = r < 0.42 ? ri(1, 3) : r < 0.55 ? -ri(1, 2) : 0;
        prev[id] = Math.max(0, walk[id] + drift);
      });
      walk = prev;
      walkScore = clamp(walkScore - ri(0, 3), 20, 98);
      walkPages = Math.max(10, walkPages - ri(0, 3));
      snapRaw.push({ byCheck: Object.assign({}, prev), score: walkScore, pagesCrawled: walkPages });
    }
    audit.snapshots = snapRaw.reverse().map((sn, k) => {
      const sums = { error: 0, warning: 0, notice: 0 };
      Object.keys(sn.byCheck).forEach(id => { sums[sevOf[id]] += sn.byCheck[id]; });
      return {
        id: 'crawl-' + k, date: iso(now - 2 * DAY - (7 - k) * 7 * DAY),
        score: sn.score, pagesCrawled: sn.pagesCrawled,
        errors: sums.error, warnings: sums.warning, notices: sums.notice,
        byCheck: sn.byCheck
      };
    });

    /* ----- AI Optimization (AI Optimization API-shaped) ----- */
    /* LLM Mentions API covers only Google AI Overviews + ChatGPT */
    const MENTION_PLATFORMS = [
      { id: 'ai_overview', name: 'AI Overviews', color: '#4f46e5' },
      { id: 'chat_gpt', name: 'ChatGPT', color: '#0d9488' }
    ];
    /* LLM Responses API models we run tracked prompts on */
    const LLM_PLATFORMS = [
      { id: 'chat_gpt', name: 'ChatGPT', color: '#0d9488' },
      { id: 'claude', name: 'Claude', color: '#d97706' },
      { id: 'gemini', name: 'Gemini', color: '#8b5cf6' },
      { id: 'perplexity', name: 'Perplexity', color: '#0ea5e9' }
    ];
    const aiDomains = [p.domain].concat(p.competitors);
    const aiBase = aiDomains.map((d, j) => {
      const m = Math.round((j === 0 ? 150 : 90) * (0.7 + rnd() * 0.9));
      return { domain: d, isYou: j === 0, mentions: m, prevMentions: Math.round(m * (0.82 + rnd() * 0.3)), aiVolume: Math.round(m * (28 + rnd() * 26)) };
    });
    const aiTotal = aiBase.reduce((a2, r) => a2 + r.mentions, 0);
    const aiPrevTotal = aiBase.reduce((a2, r) => a2 + r.prevMentions, 0);
    const sovRows = aiBase.map(r => ({
      domain: r.domain, isYou: r.isYou, mentions: r.mentions,
      sov: +((r.mentions / aiTotal) * 100).toFixed(1),
      prevSov: +((r.prevMentions / aiPrevTotal) * 100).toFixed(1),
      aiVolume: r.aiVolume,
      byPlatform: MENTION_PLATFORMS.map(() => Math.round(r.mentions * (0.3 + rnd() * 0.4)))
    })).sort((x, y) => y.sov - x.sov);

    const youRow = sovRows.find(r => r.isYou);
    const aiTrend = [];
    for (let w = 11; w >= 0; w--) {
      const grow = 1 + (11 - w) * 0.018;
      const pt2 = { date: iso(now - 2 * DAY - w * 7 * DAY) };
      MENTION_PLATFORMS.forEach((pl2, j) => {
        const base2 = [9, 7][j];
        pt2[pl2.id] = Math.round(base2 * grow * (0.7 + rnd() * 0.7) * (youRow.mentions / 40));
      });
      aiTrend.push(pt2);
    }

    const aiTopPages = goodPages.slice(0, 6).map(pg2 => ({
      url: pg2,
      mentions: Math.round(4 + rnd() * 36),
      impressions: Math.round(400 + rnd() * 5200),
      platforms: MENTION_PLATFORMS.filter(() => rnd() < 0.7).map(x => x.name)
    })).sort((x, y) => y.mentions - x.mentions);

    const authority = (p.linkDomains || []).slice(0, 5);
    const aiTopDomains = aiDomains.concat(authority).map(d => {
      const row2 = aiBase.find(r => r.domain === d);
      return { domain: d, isYou: d === p.domain, isComp: p.competitors.includes(d), mentions: row2 ? row2.mentions : Math.round(30 + rnd() * 190) };
    }).sort((x, y) => y.mentions - x.mentions).slice(0, 9);
    const aiDomTotal = aiTopDomains.reduce((a2, r) => a2 + r.mentions, 0);
    aiTopDomains.forEach(r => { r.share = +((r.mentions / aiDomTotal) * 100).toFixed(1); });

    /* prompt suggestion pool (template-based, derived from tracked keywords) */
    const PROMPT_TPLS = [
      [kw2 => 'What is the best ' + kw2 + ' and who do you recommend?', 'recommendation'],
      [kw2 => 'Who are the top providers for ' + kw2 + '?', 'recommendation'],
      [kw2 => 'Is ' + kw2 + ' worth it? What should I look for?', 'question'],
      [kw2 => 'How much does ' + kw2 + ' cost and which companies are reliable?', 'cost'],
      [kw2 => 'Compare the best options for ' + kw2 + '.', 'comparison'],
      [kw2 => 'What should I know before choosing ' + kw2 + '?', 'question']
    ];
    const promptSuggestions = keywords.slice().sort((x, y) => y.volume - x.volume).slice(0, 12).map((k2, j) => {
      const t = PROMPT_TPLS[j % PROMPT_TPLS.length];
      return { id: p.id + '-ps-' + j, text: t[0](k2.kw), kw: k2.kw, category: t[1], aiVolume: Math.round(k2.volume * (0.12 + rnd() * 0.3) / 10) * 10 };
    });

    const aiKeywords = keywords.slice().sort((x, y) => y.volume - x.volume).slice(0, 15).map(k2 => {
      const ratio = 0.06 + rnd() * 0.5;
      const aiVol = Math.round(k2.volume * ratio / 10) * 10;
      const trend2 = [];
      let v2 = aiVol * (0.5 + rnd() * 0.3);
      for (let m2 = 0; m2 < 12; m2++) { trend2.push(Math.round(v2)); v2 *= 1.02 + rnd() * 0.09; }
      const mentions2 = rnd() < 0.6 ? Math.round(rnd() * 14) : 0;
      return { kw: k2.kw, aiVolume: aiVol, gVolume: k2.volume, ratio: +(ratio * 100).toFixed(0), trend: trend2, intent: k2.intent, mentions: mentions2, gap: aiVol >= 200 && mentions2 === 0 };
    });

    const aiviz = {
      mentionPlatforms: MENTION_PLATFORMS,
      llmPlatforms: LLM_PLATFORMS,
      sov: { rows: sovRows, you: youRow.sov, delta: +(youRow.sov - youRow.prevSov).toFixed(1) },
      trend: aiTrend, topPages: aiTopPages, topDomains: aiTopDomains,
      suggestions: promptSuggestions, aiKeywords
    };

    /* ----- AI-derived alerts ----- */
    if (aiviz.sov.delta < 0) push(1, 'medium', 'ai', 'AI share of voice slipped to ' + youRow.sov + '% (was ' + youRow.prevSov + '%)',
      'Mentions across AI Overviews and ChatGPT declined week-over-week \u2014 see SEO \u2192 AI Optimization.');
    const missPrompt = promptSuggestions.find(sg => !genPromptResults(p.id, sg.text, 0).chat_gpt.mentioned);
    if (missPrompt) push(2, 'medium', 'ai', 'Not mentioned by ChatGPT for a tracked prompt',
      '\u201c' + missPrompt.text + '\u201d \u2014 competitors are cited instead. Review the Answer Inspector.');

    /* ----- audit-derived alerts ----- */
    const topErr = auditChecks.filter(c => c.severity === 'error' && c.pages.length).sort((a, b) => b.pages.length - a.pages.length)[0];
    if (errN) push(2, 'high', 'technical', 'Site audit: ' + errN + ' error' + (errN === 1 ? '' : 's') + ' in latest crawl',
      (topErr ? 'Most affected: ' + topErr.title + ' (' + topErr.pages.length + ' page' + (topErr.pages.length === 1 ? '' : 's') + '). ' : '') + 'Open Site Audit → Issues to triage.');
    if (audit.cwv.lcp.p75 > 2.5) push(2, audit.cwv.lcp.p75 > 4 ? 'high' : 'medium', 'technical',
      'LCP p75 is ' + audit.cwv.lcp.p75 + 's (target ≤ 2.5s)',
      'Largest Contentful Paint is above the "good" threshold across crawled pages — see Site Audit → Core Web Vitals.');
    feed.sort((a, b) => (a.ts < b.ts ? 1 : -1));

    /* ----- off-site organic (GA4 Data API: referral + organic social/video) -----
       These are off-SITE interactions GA4 attributes to the site: sessions that
       arrived from other websites (referral — your backlinks/PR paying off) and
       from social/video platforms (organic social/video). GA4 gives the
       click-through side (sessions, engaged sessions, key events, revenue).
       On-platform IMPRESSIONS/CTR (e.g. LinkedIn feed) come from that platform's
       own connector, not GA4 — modeled per-source via `impressions`/`connected`. */
    const _blSet = {}; backlinks.forEach(b => { _blSet[b.domain] = true; });
    const offReferrers = p.linkDomains.slice(0, 12).map((domain) => {
      const rank = KNOWN_RANK[domain] || (18 + (hashStr(domain) % 40));
      const sessions = Math.round((rank * rank) / 14 * (0.55 + rnd() * 0.9)) + ri(15, 90);
      const engagedRate = +(0.42 + rnd() * 0.4).toFixed(2);
      const keyEvents = +(sessions * (0.008 + rnd() * 0.05)).toFixed(1);
      return {
        domain, rank, source: domain, channel: 'Referral',
        sessions, engagedSessions: Math.round(sessions * engagedRate), engagedRate,
        keyEvents, revenue: +(keyEvents * (60 + rnd() * 230)).toFixed(2),
        newUserRate: +(0.38 + rnd() * 0.5).toFixed(2), avgEngagementSec: ri(35, 210),
        tracked: !!_blSet[domain]
      };
    }).sort((a, b) => b.sessions - a.sessions);

    const _isB2B = /market|agency|growth|saas|b2b/i.test(p.vertical) || p.id === 'limitless';
    const SOCIAL_DEF = [
      ['LinkedIn', 'linkedin.com', 'Organic Social'], ['Reddit', 'reddit.com', 'Organic Social'],
      ['YouTube', 'youtube.com', 'Organic Video'], ['X (Twitter)', 't.co', 'Organic Social'],
      ['Facebook', 'facebook.com', 'Organic Social'], ['Instagram', 'instagram.com', 'Organic Social']
    ];
    const _socialW = { 'LinkedIn': _isB2B ? 3.6 : 1.5, 'Reddit': 1.4, 'YouTube': 1.15, 'X (Twitter)': 0.95, 'Facebook': _isB2B ? 0.7 : 1.6, 'Instagram': _isB2B ? 0.5 : 1.8 };
    const _connectors = { linkedin: true, reddit: false, youtube: false, x: false, facebook: false, instagram: false };
    const _connKey = { 'LinkedIn': 'linkedin', 'Reddit': 'reddit', 'YouTube': 'youtube', 'X (Twitter)': 'x', 'Facebook': 'facebook', 'Instagram': 'instagram' };
    const offSocial = SOCIAL_DEF.map((row) => {
      const platform = row[0], src = row[1], ch = row[2];
      const w = _socialW[platform] || 1;
      const sessions = Math.round(130 * w * (0.6 + rnd() * 0.7));
      const engagedRate = +(0.4 + rnd() * 0.42).toFixed(2);
      const keyEvents = +(sessions * (0.006 + rnd() * 0.045)).toFixed(1);
      const connected = _connectors[_connKey[platform]];
      return {
        platform, source: src, channel: ch,
        sessions, engagedSessions: Math.round(sessions * engagedRate), engagedRate,
        keyEvents, revenue: +(keyEvents * (55 + rnd() * 215)).toFixed(2),
        impressions: connected ? Math.round(sessions * (26 + rnd() * 44)) : null,
        connected
      };
    }).sort((a, b) => b.sessions - a.sessions);

    const _refTotal = offReferrers.reduce((s, r) => s + r.sessions, 0);
    const _socTotal = offSocial.filter(r => r.channel === 'Organic Social').reduce((s, r) => s + r.sessions, 0);
    const _vidTotal = offSocial.filter(r => r.channel === 'Organic Video').reduce((s, r) => s + r.sessions, 0);
    const _organicSearch = Math.round(totalClicks * (0.85 + rnd() * 0.2));
    const _direct = Math.round(_organicSearch * (0.35 + rnd() * 0.25));
    const _email = Math.round((_refTotal + _socTotal) * (0.15 + rnd() * 0.2));
    const _mkCh = (channel, sessions, offsiteFlag) => {
      const cr = 0.012 + rnd() * 0.03;
      return {
        channel, sessions, offsite: offsiteFlag,
        keyEvents: +(sessions * cr).toFixed(1),
        revenue: +(sessions * cr * (70 + rnd() * 160)).toFixed(2),
        engagedRate: +(0.45 + rnd() * 0.35).toFixed(2)
      };
    };
    const offChannels = [
      _mkCh('Organic Search', _organicSearch, false),
      _mkCh('Direct', _direct, false),
      _mkCh('Referral', _refTotal, true),
      _mkCh('Organic Social', _socTotal, true),
      _mkCh('Organic Video', _vidTotal, true),
      _mkCh('Email', _email, false)
    ].sort((a, b) => b.sessions - a.sessions);

    const offLandingPages = pages.filter(x => x.kind === 'ok').slice(0, 7).map((pg, j) => {
      const sessions = ri(45, 400);
      const engagedRate = +(0.4 + rnd() * 0.42).toFixed(2);
      const keyEvents = +(sessions * (0.01 + rnd() * 0.05)).toFixed(1);
      return {
        url: pg.url, sessions, engagedSessions: Math.round(sessions * engagedRate), engagedRate,
        keyEvents, revenue: +(keyEvents * (60 + rnd() * 220)).toFixed(2),
        topSource: j % 3 === 0 ? 'LinkedIn' : pick(p.linkDomains)
      };
    }).sort((a, b) => b.sessions - a.sessions);

    const offDailyBase = Math.max(6, (_refTotal + _socTotal + _vidTotal) / 90);
    const offSeries = [];
    for (let d = 89; d >= 0; d--) {
      const ts = now - d * DAY;
      const dow = new Date(ts).getDay();
      const wf = (dow === 0 || dow === 6) ? 0.68 : 1;
      const growth = 1 + (89 - d) * 0.003;
      const spike = (d >= 8 && d <= 10) ? 1.55 : 1; // a LinkedIn post landed
      const sessions = Math.round(offDailyBase * wf * growth * spike * (0.8 + rnd() * 0.4));
      const engagedSessions = Math.round(sessions * (0.5 + rnd() * 0.22));
      const keyEvents = +(sessions * (0.01 + rnd() * 0.03)).toFixed(1);
      offSeries.push({ date: iso(ts), sessions, engagedSessions, keyEvents, revenue: +(keyEvents * (70 + rnd() * 180)).toFixed(2) });
    }

    const offsite = { series: offSeries, channels: offChannels, referrers: offReferrers, social: offSocial, landingPages: offLandingPages, connectors: _connectors };

    const out = { project: p, keywords, pages, backlinks, series, compRows, countries, ads, feed, settings, goodPages, audit, aiviz, offsite };
    cache[projectId] = out;
    return out;
  }

  /* ---------- AI prompt-run generators (LLM Responses / Scraper shaped) ---------- */
  function genPromptResults(projectId, text, salt) {
    const p = PROJECTS.find(x => x.id === projectId) || PROJECTS[0];
    const rnd = mulberry32(hashStr(p.id + '|' + text + '|' + (salt || 0)));
    const results = {};
    ['chat_gpt', 'claude', 'gemini', 'perplexity'].forEach((id, i) => {
      const mentioned = rnd() < (i === 0 ? 0.7 : 0.52);
      const cited = mentioned && rnd() < 0.6;
      results[id] = {
        mentioned, cited,
        position: mentioned ? 1 + Math.floor(rnd() * 6) : null,
        snippet: mentioned
          ? p.name + ' is named among the recommended providers \u2014 noted for licensed staff and transparent pricing.' + (cited ? ' The answer links to ' + p.domain + '.' : ' No link to your site is included.')
          : 'The answer recommends ' + (p.competitors[Math.floor(rnd() * p.competitors.length)] || 'a competitor') + '; ' + p.name + ' is not mentioned.'
      };
    });
    return results;
  }

  function genScrape(projectId, text, salt) {
    const p = PROJECTS.find(x => x.id === projectId) || PROJECTS[0];
    const results = genPromptResults(projectId, text, salt);
    const cg = results.chat_gpt;
    const auth = (p.linkDomains || ['healthline.com', 'yelp.com']);
    const cites = [{ title: 'Guide: ' + text.slice(0, 60), domain: auth[0] || 'healthline.com', isYou: false }];
    if (cg.cited) cites.push({ title: p.name + ' \u2014 official site', domain: p.domain, isYou: true });
    cites.push({ title: 'Comparison: top providers reviewed', domain: p.competitors[0], isYou: false });
    cites.push({ title: 'Reviews and ratings roundup', domain: auth[1] || 'yelp.com', isYou: false });
    cites.forEach((c2, ci) => { c2.n = ci + 1; });
    const youN = cg.cited ? 2 : null;
    const compN = cg.cited ? 3 : 2;
    const revN = cg.cited ? 4 : 3;
    return {
      model: 'ChatGPT \u00b7 gpt-4o with search', location: p.location, results,
      paragraphs: [
        { text: 'The strongest options here combine licensed clinical staff, transparent pricing, and same-week availability. Based on recent reviews and coverage, these are the standouts. [1]', hit: false },
        cg.mentioned
          ? { text: p.name + ' (' + p.domain + ') is frequently recommended \u2014 it stands out for vetted providers, upfront pricing, and consistently high review scores across ' + p.location + '.' + (youN ? ' [' + youN + ']' : ''), hit: true }
          : { text: (p.competitors[0] || 'A national provider') + ' leads most comparisons on availability and price, with ' + (p.competitors[1] || 'another provider') + ' as a runner-up. [' + compN + ']', hit: false },
        { text: 'Comparison sites also shortlist ' + p.competitors.slice(0, 2).join(' and ') + '; check independent reviews before booking, and confirm licensing for your state. [' + compN + '][' + revN + ']', hit: false }
      ],
      citations: cites
    };
  }

  return { PROJECTS, build, addProject, mulberry32, hashStr, classifyIntent, ctrForPos, genPromptResults, genScrape };
})();
