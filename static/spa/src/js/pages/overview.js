    /* ============ OVERVIEW ============ */
    if (tab === 'overview') {
      vals.showOverview = true;
      const pillarDisp = (p) => {
        if (p.state === 'setup') return 'Set up';
        if (p.value == null) return '—';
        if (p.valueKind === 'pos') return '#' + p.value;
        if (p.valueKind === 'roas') return p.value + '×';
        if (p.valueKind === 'pct') return p.value + '%';
        if (p.valueKind === 'score') return String(p.value);
        return this.fmt(p.value);
      };
      const sevColor = { high: '#dc2626', medium: '#d97706', info: '#94a3b8' };
      const modColor = { SEO: '#4f46e5', Positions: '#0891b2', Backlinks: '#7c3aed', 'Site Audit': '#dc2626', Ads: '#059669', System: '#64748b', General: '#64748b' };
      const toneDot = { ok: '#10b981', warn: '#f59e0b', bad: '#ef4444', setup: '#a855f7' };
      const toneStat = { ok: '#0f172a', warn: '#b45309', bad: '#b91c1c', setup: '#7c3aed' };
      const sigTone = {
        positive: { icon: '✅', label: "What's working", bg: '#ecfdf5', border: '#a7f3d0', head: '#047857', body: '#15803d' },
        negative: { icon: '⚠️', label: 'Needs attention', bg: '#fef2f2', border: '#fecaca', head: '#991b1b', body: '#b91c1c' },
        opportunity: { icon: '💡', label: 'Opportunity', bg: '#eff6ff', border: '#bfdbfe', head: '#1d4ed8', body: '#2563eb' }
      };
      const scoreChip = v => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '34px', height: '22px', padding: '0 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, background: v >= 80 ? '#dcfce7' : v >= 60 ? '#fef3c7' : '#fee2e2', color: v >= 80 ? '#15803d' : v >= 60 ? '#b45309' : '#b91c1c' });

      /* ---- Data source provenance (see app.js srcBadge) --------------------------------
         Keyed on the pillar / module `label`, which build_pillars() and build_modules()
         emit as fixed strings. A card in `state:'setup'` / `tone:'setup'` gets NO badge:
         there is no measured number on it to attribute, and a badge there would be the
         "estimated" tier this feature exists to prevent.

         `keyword_rankings.position` is genuinely written by EITHER gsc_keywords OR
         dataforseo_serp and nothing in the row records which — so every surface reading a
         keyword position names both rather than picking one and being wrong half the time. */
      const PILLAR_SRC = {
        'Organic clicks': ['gsc'],
        /* Same source as clicks: both are read off seo_daily_totals, which is what the GSC
           connector's dimensions=["date"] call writes. */
        'Impressions': ['gsc'],
        /* value = seo_daily.avg_position (GSC); sub = "N keywords in top 3" off
           keyword_rankings.position (GSC queries or DataForSEO SERP). */
        'Avg. position': ['gsc', 'gsc_keywords', 'dataforseo_serp'],
        /* score = 60% Lighthouse mobile performance + 40% GSC URL-Inspection indexed share;
           sub = error count from technical_issues (DataForSEO OnPage + derived). */
        'Site health': ['pagespeed', 'url_inspection', 'dataforseo_onpage']
      };
      const MODULE_SRC = {
        'SEO Performance': ['gsc'],
        'Keywords': ['gsc_keywords', 'dataforseo_serp'],
        /* stat is seo_daily.avg_position — the site-wide GSC figure, not keyword_rankings. */
        'Position Tracking': ['gsc'],
        'Backlinks': ['dataforseo_backlinks'],
        'Site Audit': ['pagespeed', 'url_inspection', 'dataforseo_onpage']
      };
      /* Same geometry as scoreChip, neutral palette — for a score that was never captured. */
      const mutedChip = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '34px', height: '22px', padding: '0 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, background: '#f1f5f9', color: '#cbd5e1' };
      /* ---- the window every number on this page is about --------------------------------
         NOT "the last 7 days". The window anchors to the newest day of Search Console data
         (views.latest_data_anchor), and `gsc_safe_range` deliberately stops three days back
         where Search Console's own UI stops two — so even a perfectly healthy sync produces a
         window about a day off Console's on each end, and the totals differ to match.

         Printing the dates is what lets a user tell that apart from a sync that has quietly
         stopped. On premierstaff.com the window had drifted three weeks back and still showed
         a complete, plausible week; the only visible symptom was that it disagreed with Search
         Console, which reads as "the dashboard is wrong" rather than "the data is old". */
      const fmtWinDate = (d, withYear) => d.toLocaleDateString(undefined, Object.assign(
        { day: 'numeric', month: 'short' }, withYear ? { year: 'numeric' } : {}));
      const win = data.window;
      /* Same local-midnight guard relTime() uses: a bare "YYYY-MM-DD" is parsed as UTC by
         spec, which shifts the day for anyone west of Greenwich and would print the window
         a day early. */
      const parseWinDate = d => new Date(String(d).length <= 10 ? d + 'T00:00:00' : d);
      const winParsed = win && win.start && win.end
        ? [parseWinDate(win.start), parseWinDate(win.end)] : null;
      vals.ov = {
        /* Absent on an older cached payload — render nothing rather than "Showing undefined". */
        hasWindow: !!winParsed,
        windowText: winParsed
          ? 'Showing ' + fmtWinDate(winParsed[0], false) + ' – ' + fmtWinDate(winParsed[1], true)
          : '',
        windowTitle: winParsed
          ? 'Every figure on this page covers ' + win.start + ' to ' + win.end + ', inclusive.\n\n'
            + 'This window ends on the newest day of Search Console data, not on today. Search '
            + 'Console withholds the last ~3 days while it finalises them, and its own "Last 7 '
            + 'days" view ends one day later than this one — so the two screens cover slightly '
            + 'different weeks and their totals will not match exactly. Compare the dates '
            + 'before comparing the numbers.\n\n'
            + 'If this end date is far behind today, the sync is behind — check '
            + 'Settings → Automation, where every module shows its own last run.'
          : '',
        pillars: (data.pillars || []).map(p => {
          const setup = p.state === 'setup';
          const good = (p.delta || 0) >= 0;
          return {
            label: p.label, value: pillarDisp(p), sub: p.sub || '', hasSub: !!p.sub,
            hasDelta: p.delta != null,
            deltaFmt: p.delta == null ? '' : (p.delta >= 0 ? '▲ ' : '▼ ') + Math.abs(p.delta) + (p.deltaUnit === '%' ? '%' : ''),
            chipStyle: { fontSize: '11px', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', color: good ? '#059669' : '#e11d48', background: good ? '#ecfdf5' : '#fff1f2' },
            onClick: () => this.go(p.target),
            cardStyle: { borderRadius: '12px', background: 'white', border: '1px solid #e2e8f0', padding: '16px 18px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: 'pointer', transition: 'all .16s' },
            valueStyle: setup ? { fontSize: '16px', fontWeight: 600, color: '#6366f1' } : { fontSize: '24px', fontWeight: 600, color: '#0f172a', lineHeight: 1 },
            arrowStyle: { color: '#cbd5e1', fontSize: '14px', lineHeight: 1 },
            src: setup ? this.srcBadge(null) : this.srcBadge(PILLAR_SRC[p.label])
          };
        }),
        priority: (data.priority || []).map((a, i) => ({
          title: a.title, detail: a.detail, tsFmt: a.ts, moduleLabel: a.module.label,
          moduleStyle: { fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: modColor[a.module.label] || '#64748b', background: (modColor[a.module.label] || '#64748b') + '14', padding: '2px 7px', borderRadius: '4px' },
          sevDot: { width: '8px', height: '8px', borderRadius: '9999px', background: sevColor[a.severity] || '#94a3b8', marginTop: '6px', flexShrink: 0 },
          rowStyle: { display: 'flex', gap: '12px', alignItems: 'flex-start', padding: '14px 20px', cursor: 'pointer', borderTop: i === 0 ? 'none' : '1px solid #f1f5f9' },
          onClick: () => this.go(a.module.target)
        })),
        priorityEmpty: (data.priority || []).length === 0,
        modules: (data.modules || []).map(m => ({
          label: m.label, stat: m.stat, sub: m.sub,
          dotStyle: { width: '8px', height: '8px', borderRadius: '9999px', background: toneDot[m.tone] || '#10b981', flexShrink: 0 },
          statStyle: { fontSize: '18px', fontWeight: 600, color: toneStat[m.tone] || '#0f172a', marginTop: '8px', lineHeight: 1.1 },
          cardStyle: { borderRadius: '12px', background: 'white', border: '1px solid #e2e8f0', padding: '14px 16px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: 'pointer', transition: 'all .16s' },
          onClick: () => this.go(m.target),
          src: m.tone === 'setup' ? this.srcBadge(null) : this.srcBadge(MODULE_SRC[m.label])
        })),
        clickPts: this.linePts(data.trend, 'clicks', 600, 220),
        imprPts: this.linePts(data.trend, 'impressions', 600, 220),
        rangeLabel: s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days',
        summary: [
          { title: 'Wins', items: data.summary.wins, kind: 'win' },
          { title: 'Critical', items: data.summary.critical, kind: 'critical' },
          { title: 'Watch', items: data.summary.watch, kind: 'watch' }
        ].filter(x => x.items && x.items.length).map(x => {
          const m = x.kind === 'win' ? ['#d1fae5', 'rgba(236,253,245,0.5)', '#047857', '#34d399'] : x.kind === 'critical' ? ['#fee2e2', 'rgba(254,242,242,0.5)', '#b91c1c', '#f87171'] : ['#e2e8f0', 'rgba(248,250,252,0.6)', '#64748b', '#94a3b8'];
          return {
            title: x.title, items: x.items.map(htmlString => ({ obj: { __html: htmlString } })),
            boxStyle: { borderRadius: '8px', border: '1px solid ' + m[0], background: m[1], padding: '12px' },
            titleStyle: { fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: m[2], margin: '0 0 4px' },
            dotStyle: { marginTop: '6px', width: '4px', height: '4px', borderRadius: '9999px', background: m[3], flexShrink: 0 }
          };
        }),
        topPages: (data.topPages || []).map(r => ({ url: r.url, clicksFmt: this.fmt(r.clicks), imprFmt: this.fmt(r.impressions), ctrFmt: r.ctr + '%' })),
        topPagesEmpty: (data.topPages || []).length === 0,
        trendEmpty: (data.trend || []).length === 0,

        /* Top keywords — build_top_keywords_api returns raw numbers (or null), so this
           table formats them exactly like every other Overview table: this.fmt() for
           counts, this.posBadge() for the position chip. null means "no captured value"
           and renders as an em dash — never as 0, which would read as real data. */
        topKeywords: (data.topKeywords || []).map(r => ({
          keyword: r.keyword,
          posText: r.position == null ? '—' : String(r.position),
          posStyle: this.posBadge(r.position),
          clicksFmt: this.fmt(r.clicks),
          imprFmt: this.fmt(r.impressions),
          volFmt: this.fmt(r.volume),
          volStyle: { padding: '12px 20px', textAlign: 'right', fontSize: '12px', color: r.volume == null ? '#cbd5e1' : '#94a3b8' }
        })),
        hasTopKeywords: (data.topKeywords || []).length > 0,
        topKeywordsEmpty: (data.topKeywords || []).length === 0,
        onFetchKeywords: () => this.startSync('keywords'),

        /* Positioning vs Competitors — summary of the same competitor grid the Positioning
           page renders per keyword. The backend never invents a position for a competitor
           it has no capture for, and this view model must not paper over that either:
             state 'none'    -> the value reads "No data", the row is dimmed, no number.
             state 'partial' -> the real average IS shown, but always with "N of M keywords
                                captured" in amber so it is never compared like-for-like.
             state 'ok'      -> full coverage of the tracked keyword set. */
        po: (() => {
          const p = data.positioningOverview || { status: 'setup', note: '', you: null, competitors: [] };
          const stateColor = { ok: '#047857', partial: '#b45309', none: '#94a3b8' };
          const kwWord = (n) => n === 1 ? ' keyword' : ' keywords';
          const covLabel = (c) => {
            if (!c || c.state === 'none') return 'No captured positions';
            if (c.state === 'partial') return c.keywordsRanked + ' of ' + c.keywordsTotal + kwWord(c.keywordsTotal) + ' captured';
            return 'All ' + c.keywordsTotal + kwWord(c.keywordsTotal) + ' captured';
          };
          const you = p.you;
          const comps = p.competitors || [];
          const withData = comps.filter(c => c.state !== 'none').length;
          const partial = comps.filter(c => c.state === 'partial').length;
          let coverageNote = '';
          if (comps.length && withData === 0) coverageNote = 'No competitor positions captured yet — run a positions sync.';
          else if (withData < comps.length) coverageNote = 'Only ' + withData + ' of ' + comps.length + ' competitors have captured positions — the rest show no number rather than an estimate.';
          else if (partial) coverageNote = 'Coverage is partial for ' + partial + ' of ' + comps.length + ' competitors — their averages cover fewer keywords than yours.';
          return {
            isSetup: p.status !== 'ok',
            isReady: p.status === 'ok',
            note: p.note || '',
            onFetch: () => this.startSync('positions'),
            youValue: you && you.avgPosition != null ? '#' + you.avgPosition : 'No data',
            youValueStyle: {
              fontSize: you && you.avgPosition != null ? '30px' : '16px', fontWeight: 700, lineHeight: 1.1,
              color: you && you.avgPosition != null ? '#4338ca' : '#a5b4fc'
            },
            youNote: covLabel(you),
            youNoteStyle: { fontSize: '11px', marginTop: '6px', color: you && you.state === 'partial' ? '#b45309' : '#818cf8' },
            capturedAt: p.capturedAt ? 'Positions captured ' + p.capturedAt : 'No capture date recorded',
            hasCoverageNote: !!coverageNote,
            coverageNote: coverageNote,
            competitors: comps.map(c => ({
              domain: c.domain,
              posText: c.avgPosition == null ? 'No data' : '#' + c.avgPosition,
              posStyle: { fontSize: '13px', fontWeight: 600, color: stateColor[c.state] || '#64748b', flexShrink: 0 },
              coverage: covLabel(c),
              coverageStyle: { fontSize: '11px', marginTop: '2px', color: c.state === 'partial' ? '#b45309' : '#94a3b8' },
              rowStyle: {
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px',
                padding: '8px 10px', borderRadius: '6px', background: '#f8fafc',
                opacity: c.state === 'none' ? 0.55 : 1
              }
            }))
          };
        })(),

        signals: (data.signals || []).map(sg => {
          const t = sigTone[sg.type] || sigTone.opportunity;
          return {
            icon: t.icon, typeLabel: t.label, title: sg.title, detail: sg.detail,
            cardStyle: { borderRadius: '8px', border: '1px solid ' + t.border, background: t.bg, padding: '14px 16px' },
            eyebrowStyle: { fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: t.head },
            titleStyle: { fontSize: '14px', fontWeight: 600, color: t.head, margin: '6px 0 0', lineHeight: 1.3 },
            detailStyle: { fontSize: '13px', color: t.body, margin: '4px 0 0', lineHeight: 1.45 }
          };
        }),
        hasSignals: (data.signals || []).length > 0,

        /* ---- one badge per card, at the card header ----
           Deliberately NOT one per number: every tile inside these cards shares a source,
           and a badge on each would shout louder than the figures it annotates. Where a
           card genuinely straddles connectors it names all of them and reports the age of
           the OLDEST — a card is only as fresh as the stalest thing in it. */
        srcSignals: this.srcBadge(['gsc'],
          'Ad-overlap signals additionally compare Google Ads spend against your organic positions, and only appear once the Google Ads connector has run.'),
        /* anomalies are derived from GSC+GA4 metrics; technical items from the OnPage crawl.
           A sync-failure item in this feed comes from the app's own run log, not a connector. */
        srcPriority: this.srcBadge(['gsc', 'ga4', 'dataforseo_onpage'],
          'Sync-failure notices in this feed come from the app’s own run log rather than from a data source.'),
        srcTrend: this.srcBadge(['gsc']),
        srcTopKw: this.srcBadge(['gsc_keywords', 'dataforseo_serp', 'dataforseo_keywords']),
        srcPo: this.srcBadge(['gsc_keywords', 'dataforseo_serp', 'dataforseo_serp_competitors']),
        srcTopPages: this.srcBadge(['gsc']),
        srcGa4Pages: this.srcBadge(['ga4']),
        srcAuditPages: this.srcBadge(['pagespeed']),
        /* NO badge on the Weekly summary card. It is written by ai_summary_service (OpenAI)
           into `ai_summaries`, which is not a BaseConnector and therefore has no SyncLog row,
           and the overview payload carries no week_start / generated_at for it. There is no
           honest date to print, so nothing is printed — see the report for the field needed. */

        topGa4Pages: (data.topGa4Pages || []).map(r => ({
          url: r.url, location: r.location, trafficFmt: this.fmt(r.traffic)
        })),
        hasTopGa4Pages: (data.topGa4Pages || []).length > 0,

        /* A score of null means "not captured", not "scored zero". scoreChip() compares with
           >=, and every comparison against null is false, so a null used to fall through to the
           red band -- an uncaptured SEO score rendered identically to a failing one. Print a
           dash in the muted grey instead, the same convention Site Audit uses for an
           unmeasured page. */
        topAuditPages: (data.topAuditPages || []).map(r => ({
          url: r.url,
          perf: r.performance == null ? '—' : r.performance,
          perfStyle: r.performance == null ? mutedChip : scoreChip(r.performance),
          seo: r.seo == null ? '—' : r.seo,
          seoStyle: r.seo == null ? mutedChip : scoreChip(r.seo),
          lcpFmt: r.lcp ? (r.lcp / 1000).toFixed(1) + ' s' : '—',
          lcpStyle: { color: r.lcp ? '#475569' : '#cbd5e1' }
        })),
        hasTopAuditPages: (data.topAuditPages || []).length > 0,


        yTicksC: (() => {
          const m = Math.max(1, ...((data.trend || []).map(d => d.clicks)));
          return [this.fmt(m), this.fmt(Math.round(m * 0.66)), this.fmt(Math.round(m * 0.33)), 0];
        })(),
        yTicksI: (() => {
          const m = Math.max(1, ...((data.trend || []).map(d => d.impressions)));
          return [this.fmt(m), this.fmt(Math.round(m * 0.66)), this.fmt(Math.round(m * 0.33)), 0];
        })(),
        xTicks: (() => {
          const tr = data.trend || [];
          if (!tr.length) return [];
          const step = Math.max(1, (tr.length - 1) / 9);
          const out = [];
          for (let i = 0; i <= 9; i++) {
            const idx = Math.min(tr.length - 1, Math.round(i * step));
            if (tr[idx]) {
              const d = new Date(tr[idx].date);
              out.push({
                label: (d.getMonth() + 1) + '/' + d.getDate() + '/' + String(d.getFullYear()).slice(2),
                pct: (i * 11.111).toFixed(3)
              });
            }
          }
          return out;
        })(),

        hoverZones: (data.trend || []).map((d, i) => {
          const xCount = Math.max(1, (data.trend || []).length - 1);
          const cx = i * (600 / xCount);
          return {
            x: cx - (600 / xCount / 2),
            w: 600 / xCount,
            onEnter: () => this.setState({ chartHoverIndex: i })
          };
        }),
        hasHover: s.chartHoverIndex !== null && data.trend[s.chartHoverIndex],
        hoverX: s.chartHoverIndex !== null ? (s.chartHoverIndex * (600 / Math.max(1, (data.trend || []).length - 1))).toFixed(1) : 0,
        ttX: s.chartHoverIndex !== null ? ((s.chartHoverIndex * (600 / Math.max(1, (data.trend || []).length - 1))) < 300 ? (s.chartHoverIndex * (600 / Math.max(1, (data.trend || []).length - 1))) + 15 : (s.chartHoverIndex * (600 / Math.max(1, (data.trend || []).length - 1))) - 150) : 0,
        ttData: s.chartHoverIndex !== null ? data.trend[s.chartHoverIndex] : null,
        ttClicksFmt: s.chartHoverIndex !== null && data.trend[s.chartHoverIndex] ? this.fmt(data.trend[s.chartHoverIndex].clicks) : '',
        ttImprFmt: s.chartHoverIndex !== null && data.trend[s.chartHoverIndex] ? this.fmt(data.trend[s.chartHoverIndex].impressions) : '',
        // CTR and position come down per-day with the trend, so the hover shows the same
        // four figures Search Console's own chart does without another request.
        ttCtrFmt: s.chartHoverIndex !== null && data.trend[s.chartHoverIndex]
          ? (data.trend[s.chartHoverIndex].ctr != null ? data.trend[s.chartHoverIndex].ctr.toFixed(2) + '%' : '—') : '',
        ttPosFmt: s.chartHoverIndex !== null && data.trend[s.chartHoverIndex]
          ? (data.trend[s.chartHoverIndex].position ? data.trend[s.chartHoverIndex].position.toFixed(1) : '—') : '',
        ttDateFmt: s.chartHoverIndex !== null && data.trend[s.chartHoverIndex]
          ? data.trend[s.chartHoverIndex].date : ''
      };
    }

