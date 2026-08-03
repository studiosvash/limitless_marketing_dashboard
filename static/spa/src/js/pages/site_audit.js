    /* ============ SITE AUDIT ============ */
    if (tab === 'pages') {
      vals.showPages = true;
      const auSetup = !data || data.score == null || (typeof data.score === 'object' && data.score.state === 'setup') || (data.crawl && (data.crawl.status === 'never' || data.crawl.pagesCrawled === 0));

      if (auSetup) {
        /* Setup state: nothing measured, so nothing to attribute. */
        vals.au = {
          setup: true,
          srcScore: this.srcBadge(null), srcVitals: this.srcBadge(null),
          srcBreakdown: this.srcBadge(null), srcIssues: this.srcBadge(null),
          srcCrawled: this.srcBadge(null), srcStats: this.srcBadge(null),
          srcHistory: this.srcBadge(null), srcDomChecks: this.srcBadge(null),
          subTabs: [], showOverview: false, showIssues: false, showCrawled: false,
          showCompare: false, showProgress: false, showStats: false,
          domain: project.domain, crawlDate: '', pagesCrawled: 0, crawlDuration: '', userAgent: '', measuredLabel: '',
          barSegs: [], breakRows: [], sevTotals: [], cats: [], vitals: [], domChecks: [], noDomChecks: false, hasDomChecks: false, topIssues: [],
          hasCritical: false, noCritical: false, criticalRows: [], criticalMore: false,
          criticalCountLabel: '', criticalMoreLabel: '',
          sevFilters: [], catFilters: [], noIssues: true, issueRows: [], search: '',
          tableTabStyle: {}, treeTabStyle: {}, showTable: false, showTree: false,
          pgSearch: '', pageRows: [], pageRowCount: '', treeRows: [],
          statKpis: [], statCharts: [],
          statShowEmpty: false, statHasKpis: false, statEmptyTitle: '', statEmptyMsg: '',
          cmpOptions: [], cmpOptions2: [], cmpFilters: [], cmpKpis: [], cmpEmpty: true, cmpRows: [],
          cmpA: '', cmpB: '', cmpALabel: '', cmpBLabel: '',
          cmpHasHistory: false, cmpShowEmpty: false, cmpEmptyTitle: '', cmpEmptyMsg: '',
          progToggles: [], progLines: [], progFrom: '', progTo: '', progRows: [],
          progHasHistory: false, progShowEmpty: false, progHasChart: false, progOnePoint: false,
          progEmptyTitle: '', progEmptyMsg: '', progCountLabel: ''
        };
        return vals;
      }

      const SEVC = { error: '#dc2626', warning: '#d97706', notice: '#2563eb' };
      const sevRank = { error: 0, warning: 1, notice: 2 };
      const scoreColor = v => v >= 80 ? '#059669' : v >= 60 ? '#d97706' : '#dc2626';
      /* MEASURED vs UNMEASURED. Only a sampled subset of crawled pages is ever Lighthouse-
         scored, so `score`, `loadTimeMs`, `inLinks`, `internalLinks` and `wordCount` are null
         on every page the relevant crawler never reached. Null is never rendered as 0 and
         never enters an average: it renders as an em dash in a neutral chip, so an unscored
         page reads as "not measured" rather than as the worst score on the site. */
      const NA = '—';
      const chipBase = { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '34px', height: '22px', padding: '0 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 700 };
      const chipNA = Object.assign({}, chipBase, { background: '#f1f5f9', color: '#94a3b8' });
      const scoreChip = v => v == null ? chipNA : Object.assign({}, chipBase, { background: v >= 80 ? '#dcfce7' : v >= 60 ? '#fef3c7' : '#fee2e2', color: v >= 80 ? '#15803d' : v >= 60 ? '#b45309' : '#b91c1c' });
      const scoreText = v => v == null ? NA : v;
      const secsText = ms => ms == null ? NA : (ms / 1000).toFixed(1) + ' s';
      const numText = v => v == null ? NA : this.fmt(v);
      /* Mean over the values that exist. Returns null — not 0 — for an empty set, so a KPI
         with nothing measured behind it disappears instead of printing a confident zero. */
      const avgOf = (arr, f) => {
        const vals = arr.map(f).filter(v => v != null);
        return vals.length ? vals.reduce((a, b2) => a + b2, 0) / vals.length : null;
      };
      const dot = c => ({ width: '9px', height: '9px', borderRadius: '50%', background: c, flexShrink: 0 });
      const sub = s.auSub;
      const totalIssues = data.totals.errors + data.totals.warnings + data.totals.notices;
      const goSub = v => { this.setState({ auSub: v }); this.pushNav({ auSub: v }); };
      const subBase = { padding: '10px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', color: '#64748b', borderBottom: '2px solid transparent', marginBottom: '-1px' };
      const activeChecks = data.checks.filter(c => !c.hidden && !c.resolved && c.count > 0);
      const hiddenChecks = data.checks.filter(c => c.hidden);
      const resolvedChecks = data.checks.filter(c => c.resolved);
      const crawlDate = data.crawl.startedAt;

      /* Provenance. This page is the clearest case for naming the OLDEST contributing source
         rather than one label: the health score is literally 60% Lighthouse mobile performance
         + 40% GSC URL-Inspection indexed share, with issue counts from DataForSEO OnPage. Three
         connectors, three separate schedules -- so the score is only as fresh as whichever ran
         longest ago, which is exactly what srcBadge() reports.

         The sub-surfaces are attributed individually because they genuinely differ:
           Core Web Vitals      -> Lighthouse only
           Indexing breakdown   -> GSC URL Inspection only
           Issues / Top issues  -> DataForSEO OnPage (+ rows derived from the other two)
           Crawled pages        -> GSC inventory, with Lighthouse scores where measured
           Domain checks        -> run during sync, not a connector; see the note below
           Compare / Progress   -> audit_snapshots, written after each crawl completes */
      const AUDIT_ALL = ['pagespeed', 'url_inspection', 'dataforseo_onpage'];
      const au = {
        srcScore: this.srcBadge(AUDIT_ALL),
        srcVitals: this.srcBadge(['pagespeed']),
        srcBreakdown: this.srcBadge(['url_inspection']),
        srcIssues: this.srcBadge(['dataforseo_onpage', 'url_inspection', 'pagespeed']),
        srcCrawled: this.srcBadge(['url_inspection', 'pagespeed'],
          'A dash means the page was crawled but never Lighthouse-scored — only a sample is.'),
        srcStats: this.srcBadge(['url_inspection', 'pagespeed'],
          'Averages and distributions cover Lighthouse-measured pages only.'),
        srcHistory: this.srcBadge(AUDIT_ALL,
          'One snapshot is recorded per completed crawl, so history is as fresh as the last sync.'),
        srcDomChecks: this.srcBadge(AUDIT_ALL,
          'SSL, sitemap, robots.txt, HTTP/2 and llms.txt are probed during the sync, not when this page loads.'),
        domain: project.domain,
        crawlDate, pagesCrawled: data.crawl.pagesCrawled, crawlDuration: data.crawl.duration, userAgent: data.crawl.userAgent,
        /* Lighthouse samples; GSC's URL inspection covers everything. The two counts are
           routinely far apart, so the header says which is which rather than letting
           "pages crawled" be read as "pages measured". */
        measuredLabel: (data.crawl.pagesMeasured || 0) + ' Lighthouse-measured',
        subTabs: [['overview', 'Overview'], ['issues', 'Issues (' + this.fmt(totalIssues) + ')'], ['crawled', 'Crawled Pages (' + data.crawl.pagesCrawled + ')'], ['stats', 'Statistics'], ['compare', 'Compare Crawls'], ['progress', 'Progress']].map(t => ({
          label: t[1],
          style: sub === t[0] ? Object.assign({}, subBase, { color: '#4f46e5', borderBottom: '2px solid #4f46e5' }) : subBase,
          click: () => goSub(t[0])
        })),
        showOverview: sub === 'overview', showIssues: sub === 'issues', showCrawled: sub === 'crawled',
        showCompare: sub === 'compare', showProgress: sub === 'progress', showStats: sub === 'stats',
        score: data.score, search: s.auSearch, pgSearch: s.auPgSearch
      };

      if (sub === 'overview') {
        const sc = scoreColor(data.score);
        au.gaugeOuter = { width: '128px', height: '128px', borderRadius: '50%', background: 'conic-gradient(' + sc + ' ' + (data.score * 3.6) + 'deg, #f1f5f9 0deg)', display: 'flex', alignItems: 'center', justifyContent: 'center' };
        au.gaugeNum = { fontSize: '34px', fontWeight: 800, lineHeight: 1, color: sc };
        au.scoreWord = data.score >= 80 ? 'Good' : data.score >= 60 ? 'Needs work' : 'Poor';
        au.scoreWordStyle = { fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: sc };
        const bd = data.breakdown;
        const bdRows = [
          ['healthy', 'Healthy', '#059669'], ['withIssues', 'With issues', '#d97706'],
          ['broken', 'Broken (4xx/5xx)', '#dc2626'], ['redirected', 'Redirected', '#8b5cf6'], ['blocked', 'Blocked', '#64748b']
        ];
        au.barSegs = bdRows.filter(r => bd[r[0]] > 0).map(r => ({ style: { flex: String(bd[r[0]]), background: r[2] } }));
        au.breakRows = bdRows.map(r => ({
          label: r[1], count: bd[r[0]], dot: dot(r[2]),
          click: () => goSub('crawled')
        }));
        const sevCardBase = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderRadius: '10px', cursor: 'pointer', flex: 1 };
        au.sevTotals = [
          ['error', 'Errors', data.totals.errors, '#fef2f2', '#b91c1c'],
          ['warning', 'Warnings', data.totals.warnings, '#fffbeb', '#b45309'],
          ['notice', 'Notices', data.totals.notices, '#eff6ff', '#1d4ed8']
        ].map(v => ({
          label: v[1], count: this.fmt(v[2]),
          style: Object.assign({}, sevCardBase, { background: v[3], color: v[4] }),
          click: () => { this.setState({ auSub: 'issues', auSev: v[0], auCat: 'all' }); this.pushNav({ auSub: 'issues' }); }
        }));
        au.cats = Object.entries(data.catScore).map(([name, sc2]) => {
          const failing = activeChecks.filter(c => c.category === name).length;
          return {
            name, score: sc2,
            scoreStyle: { fontSize: '24px', fontWeight: 800, lineHeight: 1, color: scoreColor(sc2) },
            issueLine: failing ? failing + ' check' + (failing === 1 ? '' : 's') + ' failing' : 'All checks passed',
            click: () => { this.setState({ auSub: 'issues', auCat: name, auSev: 'all' }); this.pushNav({ auSub: 'issues' }); }
          };
        });
        const vitalVerdict = (m) => m.p75 === null ? ['N/A', '#f1f5f9', '#64748b'] : m.p75 <= m.good ? ['Good', '#dcfce7', '#15803d'] : m.p75 <= m.poor ? ['Needs work', '#fef3c7', '#b45309'] : ['Poor', '#fee2e2', '#b91c1c'];
        au.vitals = [
          ['LCP', 'Largest Contentful Paint', data.cwv.lcp],
          ['TBT', 'Total Blocking Time', data.cwv.tbt],
          ['CLS', 'Cumulative Layout Shift', data.cwv.cls]
        ].map(v => {
          const m = v[2], vd = vitalVerdict(m);
          const b = m.buckets, tot = Math.max(1, b.good + b.mid + b.poor);
          return {
            name: v[0], desc: v[1], p75: m.p75 !== null ? m.p75 : '—', unit: m.p75 !== null ? m.unit : '',
            verdict: vd[0], badge: { fontSize: '11px', fontWeight: 700, padding: '2px 9px', borderRadius: '999px', background: vd[1], color: vd[2] },
            numStyle: { fontSize: '30px', fontWeight: 800, marginTop: '10px', color: vd[2] },
            segs: [
              { style: { flex: String(b.good / tot || 0.001), background: '#059669' } },
              { style: { flex: String(b.mid / tot || 0.001), background: '#d97706' } },
              { style: { flex: String(b.poor / tot || 0.001), background: '#dc2626' } }
            ],
            goodLbl: 'Good ' + b.good, midLbl: 'Needs impr. ' + b.mid, poorLbl: 'Poor ' + b.poor
          };
        });
        /* Domain checks are probed during a crawl, not on page load (the six SSL/sitemap/
           robots/HTTP-2/www/llms.txt requests used to run inside this GET). An empty list
           therefore means "no crawl has recorded them yet", not "the domain has no checks" --
           say that instead of rendering a blank card. */
        au.noDomChecks = data.domainChecks.length === 0;
        au.hasDomChecks = !au.noDomChecks;   // gates the header's "Re-run" link
        au.domChecks = data.domainChecks.map(d => ({
          label: d.label, detail: d.detail, mark: d.ok ? '✓' : '!',
          icon: { display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px', borderRadius: '50%', fontSize: '12px', fontWeight: 700, background: d.ok ? '#dcfce7' : '#fef3c7', color: d.ok ? '#15803d' : '#b45309', flexShrink: 0 }
        }));
        au.topIssues = activeChecks.slice().sort((a, b2) => sevRank[a.severity] - sevRank[b2.severity] || b2.count - a.count).slice(0, 6).map(c => ({
          title: c.title, category: c.category, count: this.fmt(c.count),
          dot: dot(SEVC[c.severity]),
          countStyle: { fontSize: '12px', fontWeight: 700, color: SEVC[c.severity], minWidth: '28px', textAlign: 'right' },
          click: () => { this.setState({ auSub: 'issues', auSev: 'all', auCat: 'all', auOpen: c.id, auSearch: '' }); this.pushNav({ auSub: 'issues' }); }
        }));

        /* --- Critical Issues ("Fix these first") ---------------------------------
           The design's lead section. Deliberately narrower than Top Issues: only
           error-severity, non-hidden checks that actually affect a page, biggest
           blast radius first, with the fix guidance inline so the user can act
           without expanding anything. data.totals.errors is already the sum of
           counts over exactly this set (non-hidden), so it needs no re-derivation. */
        const CRIT_MAX = 5;
        const critical = activeChecks.filter(c => c.severity === 'error').slice().sort((a, b2) => b2.count - a.count);
        au.hasCritical = critical.length > 0;
        au.noCritical = critical.length === 0;
        au.criticalCountLabel = critical.length + ' check' + (critical.length === 1 ? '' : 's') + ' · ' + this.fmt(data.totals.errors) + ' affected page' + (data.totals.errors === 1 ? '' : 's');
        au.criticalRows = critical.slice(0, CRIT_MAX).map(c => ({
          title: c.title, category: c.category,
          dot: dot(SEVC.error),
          countLabel: this.fmt(c.count) + ' page' + (c.count === 1 ? '' : 's'),
          hasFix: !!c.howToFix, howToFix: c.howToFix,
          aria: 'Critical issue: ' + c.title + ', ' + c.category + ', ' + c.count + ' page' + (c.count === 1 ? '' : 's') + ' affected. Open this check in the Issues tab.',
          click: () => { this.setState({ auSub: 'issues', auSev: 'all', auCat: 'all', auOpen: c.id, auSearch: '' }); this.pushNav({ auSub: 'issues' }); }
        }));
        au.criticalMore = critical.length > CRIT_MAX;
        au.criticalMoreLabel = 'View all ' + critical.length + ' critical issues →';
        au.criticalMoreClick = () => { this.setState({ auSub: 'issues', auSev: 'error', auCat: 'all', auOpen: null, auSearch: '' }); this.pushNav({ auSub: 'issues' }); };
      }

      if (sub === 'issues') {
        const fBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        au.sevFilters = [
          ['all', 'All (' + activeChecks.length + ')'],
          ['error', 'Errors (' + activeChecks.filter(c => c.severity === 'error').length + ')'],
          ['warning', 'Warnings (' + activeChecks.filter(c => c.severity === 'warning').length + ')'],
          ['notice', 'Notices (' + activeChecks.filter(c => c.severity === 'notice').length + ')'],
          ['hidden', 'Hidden (' + hiddenChecks.length + ')'],
          ['resolved', 'Resolved (' + resolvedChecks.length + ')']
        ].map(f => ({ label: f[1], style: s.auSev === f[0] ? fActive : fBase, click: () => this.setState({ auSev: f[0], auOpen: null }) }));
        const chipBase = { padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
        const chipActive = Object.assign({}, chipBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff' });
        au.catFilters = ['all'].concat(Object.keys(data.catScore)).map(cat => ({
          label: cat === 'all' ? 'All categories' : cat,
          style: s.auCat === cat ? chipActive : chipBase,
          click: () => this.setState({ auCat: cat, auOpen: null })
        }));
        let list = s.auSev === 'hidden' ? hiddenChecks
          : s.auSev === 'resolved' ? resolvedChecks
          : activeChecks.filter(c => s.auSev === 'all' || c.severity === s.auSev);
        if (s.auCat !== 'all') list = list.filter(c => c.category === s.auCat);
        if (s.auSearch) { const q = s.auSearch.toLowerCase(); list = list.filter(c => c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)); }
        list = list.slice().sort((a, b2) => sevRank[a.severity] - sevRank[b2.severity] || b2.count - a.count);
        au.noIssues = list.length === 0;
        const statusOf = pg2 => pg2 ? (pg2.statusCode + (pg2.kind === 'gone' ? ' · broken' : pg2.kind === 'redirect' ? ' · redirect' : '')) : '200';
        const pgByUrl = {};
        data.crawledPages.forEach(pg2 => { pgByUrl[pg2.url] = pg2; });
        /* AFFECTED PAGES: collapsed to a preview, expandable to the whole list.
           The payload carries every affected URL (site_audit_service builds checks[].pages
           from all TechnicalIssue rows), so "+ 99 more pages" was hiding data the browser
           already had and sending the user to a CSV for it. PAGE_PREVIEW keeps the row
           scannable when several checks are open; "Show all" reveals the rest in place.
           RENDER_MAX is a DOM guard for checks with thousands of URLs — when it bites, the
           label says exactly how many are rendered rather than implying the list is complete. */
        const PAGE_PREVIEW = 8;
        const RENDER_MAX = 500;
        au.issueRows = list.map(c => {
          const open = s.auOpen === c.id;
          const showAll = open && s.auAllPages === c.id;
          const total = c.pages.length;
          const shownN = showAll ? Math.min(total, RENDER_MAX) : Math.min(total, PAGE_PREVIEW);
          const shown = c.pages.slice(0, shownN);
          return {
            title: c.title, category: c.category, open, howToFix: c.howToFix,
            dot: dot(c.hidden ? '#cbd5e1' : SEVC[c.severity]),
            rowStyle: { display: 'flex', alignItems: 'center', gap: '12px', padding: '13px 20px', cursor: 'pointer', opacity: (c.hidden || c.resolved) ? 0.6 : 1 },
            resolved: c.resolved,
            resolveAria: (c.resolved ? 'Unresolve' : 'Mark resolved') + ': ' + c.title,
            checkboxStyle: { width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (c.resolved ? '#059669' : '#cbd5e1'), background: c.resolved ? '#059669' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontSize: '10px', fontWeight: 700, cursor: 'pointer' },
            resolveToggle: (e) => { if (e && e.stopPropagation) e.stopPropagation(); this.toggleResolvedCheck(c.id); },
            resolveLabel: c.resolved ? 'Unresolve' : 'Mark as resolved',
            countLabel: this.fmt(c.count) + ' page' + (c.count === 1 ? '' : 's'),
            countStyle: { fontSize: '12px', fontWeight: 700, color: c.hidden ? '#94a3b8' : SEVC[c.severity], minWidth: '60px', textAlign: 'right' },
            chev: { color: '#cbd5e1', fontSize: '18px', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease' },
            toggle: () => this.setState({ auOpen: open ? null : c.id }),
            hasPages: c.pages.length > 0,
            /* Expanded lists scroll inside their own box so a 107-page check does not push
               every other check off the screen. */
            pagesWrap: showAll
              ? { maxHeight: '420px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '8px' }
              : {},
            pages: shown.map(u => {
              const urlStr = typeof u === 'string' ? u : u.url;
              const pg2 = pgByUrl[urlStr];
              /* Both sources carry the same measured-or-null score by contract, so an
                 unscored page shows the neutral dash chip here too rather than a red 0. */
              const sc3 = pg2 ? pg2.score : (u && u.score !== undefined ? u.score : null);
              return {
                url: urlStr,
                score: scoreText(sc3),
                scoreStyle: scoreChip(sc3),
                status: (pg2 && pg2.statusCode) ? statusOf(pg2) : (u.status || '200')
              };
            }),
            more: total > PAGE_PREVIEW,
            moreLabel: showAll
              ? 'Show fewer'
              : 'Show all ' + this.fmt(total) + ' affected pages',
            toggleAll: () => this.setState({ auAllPages: showAll ? null : c.id }),
            capped: showAll && total > RENDER_MAX,
            cappedLabel: 'Showing the first ' + this.fmt(RENDER_MAX) + ' of ' + this.fmt(total) + ' — export for the full list',
            exportPages: () => this.downloadCsv(project.domain + '-' + c.id + '.csv', [['url', 'url']], c.pages.map(x => ({ url: typeof x === 'string' ? x : x.url }))),
            hide: () => this.toggleAuditCheck(c.id),
            hideLabel: c.hidden ? 'Restore check' : 'Hide this check'
          };
        });
      }

      if (sub === 'crawled') {
        const vBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const vActive = Object.assign({}, vBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        au.tableTabStyle = s.auView === 'table' ? vActive : vBase;
        au.treeTabStyle = s.auView === 'tree' ? vActive : vBase;
        au.showTable = s.auView === 'table';
        au.showTree = s.auView === 'tree';
        if (s.auView === 'table') {
          let rows = data.crawledPages.map(pg2 => Object.assign({}, pg2, { issues: pg2.errors * 10000 + pg2.warnings * 100 + pg2.notices }));
          if (s.auPgSearch) { const q = s.auPgSearch.toLowerCase(); rows = rows.filter(r => r.url.toLowerCase().includes(q)); }
          rows = this.sortRows(rows, s.auPgSort);
          /* PAGINATION. The whole crawled-page list is already in this payload — the table used
             to render `rows.slice(0, 40)` and tell you to export a CSV to see the rest, which on
             a 1 139-page site meant 96% of the data the browser was holding was unreachable in
             the UI. Paging rather than rendering everything keeps the DOM small on those sites.

             The page index is CLAMPED here, not trusted: filtering can shrink the list under a
             reader who is on page 12, and an out-of-range slice renders an empty table that is
             indistinguishable from "no pages matched". */
          const PAGE_SIZE = 40;
          const pg = this.pageSlice(rows.length, s.auPgPage, PAGE_SIZE);
          const pageCount = pg.pageCount, pageIdx = pg.pageIdx, from = pg.from;
          const visible = rows.slice(from, from + PAGE_SIZE);
          au.pageRows = visible.map(r => ({
            open: () => this.setState({ auPage: r.id }),
            url: r.url, score: scoreText(r.score), scoreStyle: scoreChip(r.score),
            status: String(r.statusCode),
            statusStyle: { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, background: r.statusCode === 200 ? '#dcfce7' : r.statusCode < 400 ? '#f3e8ff' : '#fee2e2', color: r.statusCode === 200 ? '#15803d' : r.statusCode < 400 ? '#7c3aed' : '#b91c1c' },
            issuesLabel: r.errors + 'E · ' + r.warnings + 'W · ' + r.notices + 'N',
            /* In-links = OnPage's meta.inbound_links_count, i.e. internal links POINTING AT
               this page. A real 0 means an orphan page and is called out in amber; a page the
               OnPage crawl never reached is null and shows a dash, because "no inbound links"
               and "we did not look" are different findings. */
            depth: r.depth,
            inLinks: numText(r.inLinks),
            inLinksStyle: { fontSize: '12.5px', fontWeight: 600, color: r.inLinks == null ? '#94a3b8' : r.inLinks === 0 ? '#b45309' : '#64748b' },
            loadLabel: secsText(r.loadTimeMs),
            loadStyle: { fontSize: '12.5px', fontWeight: 600, color: r.loadTimeMs == null ? '#94a3b8' : r.loadTimeMs > 3000 ? '#dc2626' : r.loadTimeMs > 1500 ? '#b45309' : '#64748b' }
          }));
          /* The Lighthouse count is over the WHOLE filtered list, not just this page. Per-page
             it would swing between 40/40 and 0/40 as you clicked through and read as coverage
             changing, when all that changed was which slice you are looking at. */
          const measuredAll = rows.filter(r => r.measured).length;
          au.pageRowCount = (rows.length === 0
              ? 'No pages match this filter'
              : 'Showing ' + (from + 1) + '–' + (from + visible.length) + ' of ' + rows.length + ' page' + (rows.length === 1 ? '' : 's'))
            + ' · ' + measuredAll + ' of ' + rows.length + ' Lighthouse-scored across the whole list'
            + ' (a dash means the page was crawled but not measured)';

          /* Numbered pages, windowed to 7 so a 29-page site audit does not print 29 buttons.
             First and last are always reachable so you can jump to either end in one click. */
          const pageBtn = (n, label, active, click) => ({
            label: label, click: click,
            style: {
              minWidth: '30px', padding: '5px 9px', fontSize: '12.5px', fontWeight: 600,
              borderRadius: '6px', cursor: 'pointer', border: '1px solid ' + (active ? '#4f46e5' : '#e2e8f0'),
              background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b'
            }
          });
          const go = n => () => this.setState({ auPgPage: n });
          const nums = this.pageWindow(pageCount, pageIdx).map(n => n === 'gap'
            ? { label: '…', style: { padding: '5px 4px', fontSize: '12.5px', color: '#cbd5e1' } }
            : pageBtn(n, String(n + 1), n === pageIdx, go(n)));
          const navBtn = (on, click) => ({
            click: on ? click : () => {},
            style: {
              padding: '5px 11px', fontSize: '12.5px', fontWeight: 600, borderRadius: '6px',
              border: '1px solid #e2e8f0', background: 'white',
              color: on ? '#64748b' : '#cbd5e1', cursor: on ? 'pointer' : 'default'
            }
          });
          au.hasPageNav = pageCount > 1;
          au.pageNums = nums;
          au.pagePrev = navBtn(pageIdx > 0, go(pageIdx - 1));
          au.pageNext = navBtn(pageIdx < pageCount - 1, go(pageIdx + 1));
        } else {
          /* `avgScore` averages the folder's MEASURED pages only and is null when it has
             none, so the column states its own denominator instead of implying the average
             covers every page in the folder. */
          au.treeRows = data.structure.map(t => ({
            folder: t.folder, pages: t.pages,
            avgScore: scoreText(t.avgScore), scoreStyle: scoreChip(t.avgScore),
            measuredLabel: t.measuredPages > 0 ? 'of ' + t.measuredPages + ' measured' : 'not measured',
            errors: t.errors, warnings: t.warnings, notices: t.notices
          }));
        }
      }
      if (sub === 'stats') {
        /* EVERY AGGREGATE ON THIS TAB STATES ITS OWN DENOMINATOR.

           `crawledPages` is one row per GSC-inspected URL (154 on the live site), but only the
           pages Lighthouse sampled carry a score or a load time (48), and only the pages the
           OnPage crawl reached carry link and word counts. The payload marks the rest null.

           Averaging or bucketing across all of them is what produced "Avg. page score 27
           across 152 healthy pages" and "Fast (<1.5 s): 152 (100%)" — a placeholder 0 counted
           as a measurement. Each aggregate below filters to the pages that have the value it
           needs, and prints how many that was. */
        const cp = data.crawledPages;
        const ok = cp.filter(x => x.kind === 'ok');
        const scored = ok.filter(x => x.score != null);
        const timed = ok.filter(x => x.loadTimeMs != null);
        const linked = cp.filter(x => x.internalLinks != null);
        const worded = cp.filter(x => x.wordCount != null);
        const pages = n => n + ' page' + (n === 1 ? '' : 's');

        au.statKpis = [];
        if (scored.length) au.statKpis.push({
          label: 'Avg. page score', value: Math.round(avgOf(scored, x => x.score)),
          sub: 'across ' + pages(scored.length) + ' measured by Lighthouse'
        });
        if (timed.length) au.statKpis.push({
          label: 'Avg. load time', value: secsText(avgOf(timed, x => x.loadTimeMs)),
          sub: 'server response · across ' + pages(timed.length) + ' measured'
        });
        /* Restored as real measurements: OnPage's meta.internal_links_count and
           meta.content.plain_text_word_count. They previously read `performance_score * 0.4`
           and `fcp_ms * 1.5`, i.e. a Lighthouse score and a millisecond timing relabelled as
           links and words. A tile only appears when something was actually counted. */
        if (linked.length) au.statKpis.push({
          label: 'Avg. internal links', value: Math.round(avgOf(linked, x => x.internalLinks)),
          sub: 'links on the page · across ' + pages(linked.length) + ' crawled'
        });
        if (worded.length) au.statKpis.push({
          label: 'Avg. word count', value: this.fmt(Math.round(avgOf(worded, x => x.wordCount))),
          sub: 'across ' + pages(worded.length) + ' crawled'
        });

        const mkChart = (title, sub2, defs, colorAt) => {
          const total = Math.max(1, defs.reduce((s2, d) => s2 + d[1], 0));
          return {
            title, sub: sub2,
            rows: defs.map((d, k) => {
              const col = colorAt(k, d);
              return {
                label: d[0], count: d[1], pct: Math.round((d[1] / total) * 100) + '%',
                dot: { width: '8px', height: '8px', borderRadius: '50%', background: col, flexShrink: 0 },
                bar: { height: '100%', width: Math.max(1, Math.round((d[1] / total) * 100)) + '%', background: col, borderRadius: '4px' }
              };
            })
          };
        };
        const seq = ['#4f46e5', '#818cf8', '#c7d2fe', '#e0e7ff'];
        const gwp = ['#059669', '#d97706', '#dc2626'];
        /* HTTP status and crawl depth are facts about every crawled URL — status comes from
           GSC coverage, depth from the URL path — so they legitimately cover all of `cp`. */
        au.statCharts = [
          mkChart('HTTP status codes', 'all ' + pages(cp.length) + ' crawled', [
            ['200 OK', cp.filter(x => x.statusCode === 200).length],
            ['3xx redirect', cp.filter(x => x.statusCode >= 300 && x.statusCode < 400).length],
            ['4xx client error', cp.filter(x => x.statusCode >= 400 && x.statusCode < 500).length],
            ['5xx server error', cp.filter(x => x.statusCode >= 500).length]
          ], (k) => k === 0 ? '#059669' : k === 1 ? '#8b5cf6' : k === 2 ? '#dc2626' : '#991b1b'),
          mkChart('Crawl depth', 'all ' + pages(cp.length) + ' crawled', [
            ['1 click', cp.filter(x => x.depth <= 1).length],
            ['2 clicks', cp.filter(x => x.depth === 2).length],
            ['3 clicks', cp.filter(x => x.depth === 3).length],
            ['4+ clicks', cp.filter(x => x.depth >= 4).length]
          ], k => seq[k])
        ];
        if (timed.length) au.statCharts.push(
          mkChart('Load time', pages(timed.length) + ' measured', [
            ['Fast (<1.5 s)', timed.filter(x => x.loadTimeMs < 1500).length],
            ['Average (1.5–3 s)', timed.filter(x => x.loadTimeMs >= 1500 && x.loadTimeMs <= 3000).length],
            ['Slow (>3 s)', timed.filter(x => x.loadTimeMs > 3000).length]
          ], k => gwp[k])
        );
        /* Content length, restored over real word counts. Buckets are the conventional
           thin/short/medium/long split; before, every bucket was counting `fcp_ms * 1.5`, so
           a page's render time decided whether it was called in-depth or thin. */
        if (worded.length) au.statCharts.push(
          mkChart('Content length', pages(worded.length) + ' crawled', [
            ['Thin (<300 words)', worded.filter(x => x.wordCount < 300).length],
            ['Short (300–999)', worded.filter(x => x.wordCount >= 300 && x.wordCount < 1000).length],
            ['Medium (1,000–1,999)', worded.filter(x => x.wordCount >= 1000 && x.wordCount < 2000).length],
            ['Long (2,000+)', worded.filter(x => x.wordCount >= 2000).length]
          ], k => seq[k])
        );

        /* Nothing measured at all: the two structural charts above still describe the crawl
           honestly, but there is no score, timing, link or word data to summarise. Say that
           and offer the crawl, rather than printing four zeroed tiles. */
        au.statShowEmpty = au.statKpis.length === 0;
        au.statHasKpis = au.statKpis.length > 0;
        au.statEmptyTitle = 'No page measurements recorded yet';
        au.statEmptyMsg = 'Page scores and load times come from the Lighthouse sample, link and word counts from the OnPage crawl. Neither has run for this site yet, so there is nothing to average — the charts below still describe every crawled URL.';
      }

      if (sub === 'compare' && data.snapshots.length < 2) {
        /* Comparison needs TWO crawls. Zero and one are different situations and the user
           should be told which one they are in -- the old bare empty state said only
           "No checks changed between these two crawls", which is a lie when there are no
           crawls to compare. Nothing is fabricated to fill the gap. */
        const n = data.snapshots.length;
        au.cmpOptions = []; au.cmpOptions2 = []; au.cmpFilters = []; au.cmpKpis = [];
        au.cmpRows = []; au.cmpEmpty = false; au.cmpA = ''; au.cmpB = '';
        au.cmpALabel = '—'; au.cmpBLabel = '—';
        au.cmpHasHistory = false;
        au.cmpShowEmpty = true;
        au.cmpEmptyTitle = n === 0 ? 'No crawl history recorded yet' : 'Only one crawl recorded so far';
        au.cmpEmptyMsg = n === 0
          ? 'Each completed crawl saves a snapshot of the score, issue counts and pages crawled. Nothing has been recorded for this site yet — run a crawl to capture the first one. Comparing needs two.'
          : 'The first snapshot was captured on ' + data.snapshots[0].date + '. Run another crawl to compare it against and see which checks were fixed and which are new.';
      } else if (sub === 'compare') {
        const snaps = data.snapshots;
        au.cmpHasHistory = true;
        au.cmpShowEmpty = false;
        au.cmpEmptyTitle = ''; au.cmpEmptyMsg = '';
        const iA = Math.min(s.auCmpA != null ? s.auCmpA : 0, snaps.length - 1);
        const iB = Math.min(s.auCmpB != null ? s.auCmpB : snaps.length - 1, snaps.length - 1);
        const A = snaps[iA], B = snaps[iB];
        au.cmpA = String(iA); au.cmpB = String(iB);
        const opt = snaps.map((sn, k) => ({ value: String(k), label: sn.date + (k === snaps.length - 1 ? ' (latest)' : '') }));
        au.cmpOptions = opt; au.cmpOptions2 = opt;
        au.cmpALabel = A.date; au.cmpBLabel = B.date;
        const deltaChip = (d, invert) => {
          const good = invert ? d > 0 : d < 0;
          const col = d === 0 ? ['#f1f5f9', '#64748b'] : good ? ['#dcfce7', '#15803d'] : ['#fee2e2', '#b91c1c'];
          return { padding: '2px 9px', borderRadius: '999px', fontSize: '12px', fontWeight: 700, background: col[0], color: col[1] };
        };
        const sgn = d => (d > 0 ? '+' : '') + d;
        au.cmpKpis = [
          ['Health score', B.score, A.score, true],
          ['Errors', B.errors, A.errors, false],
          ['Warnings', B.warnings, A.warnings, false],
          ['Pages crawled', B.pagesCrawled, A.pagesCrawled, true]
        ].map(k => ({
          label: k[0], now: this.fmt(k[1]), was: this.fmt(k[2]),
          delta: sgn(k[1] - k[2]), deltaStyle: deltaChip(k[1] - k[2], k[3])
        }));
        const fBase2 = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const fActive2 = Object.assign({}, fBase2, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        let rows = data.checks.map(c => ({
          c, a: A.byCheck[c.id] || 0, b: B.byCheck[c.id] || 0
        })).map(r => Object.assign(r, { d: r.b - r.a }));
        const nFixed = rows.filter(r => r.d < 0).length, nNew = rows.filter(r => r.d > 0).length;
        au.cmpFilters = [['all', 'All changes (' + rows.filter(r => r.d !== 0).length + ')'], ['fixed', 'Fixed (' + nFixed + ')'], ['new', 'New (' + nNew + ')']].map(f => ({
          label: f[1], style: s.auCmpFilter === f[0] ? fActive2 : fBase2,
          click: () => this.setState({ auCmpFilter: f[0] })
        }));
        rows = rows.filter(r => s.auCmpFilter === 'fixed' ? r.d < 0 : s.auCmpFilter === 'new' ? r.d > 0 : r.d !== 0);
        rows.sort((x, y) => Math.abs(y.d) - Math.abs(x.d));
        au.cmpEmpty = rows.length === 0;
        au.cmpRows = rows.map(r => ({
          title: r.c.title, category: r.c.category,
          dot: dot(SEVC[r.c.severity]),
          a: r.a, b: r.b, delta: sgn(r.d) + (r.d < 0 ? ' fixed' : ' new'),
          deltaStyle: deltaChip(r.d, false)
        }));
      }

      if (sub === 'progress' && !data.snapshots.length) {
        // No audit history yet -- empty state instead of crashing on snaps[0].date.
        au.progToggles = []; au.progLines = []; au.progRows = [];
        au.progFrom = '—'; au.progTo = '—';
        au.progShowEmpty = true; au.progHasHistory = false;
        au.progHasChart = false; au.progOnePoint = false;
        au.progCountLabel = '';
        au.progEmptyTitle = 'No crawl history recorded yet';
        au.progEmptyMsg = 'Every completed crawl saves one snapshot here — health score, errors, warnings, notices and pages crawled. Run a crawl to record the first one; the trend line appears once there are two.';
      } else if (sub === 'progress') {
        const snaps = data.snapshots;
        au.progShowEmpty = false; au.progHasHistory = true;
        au.progEmptyTitle = ''; au.progEmptyMsg = '';
        /* A polyline needs two points: with one snapshot `k / (snaps.length - 1)` is a
           division by zero and every x becomes NaN. Show the real single row in the table
           and say plainly why there is no line yet. */
        au.progHasChart = snaps.length > 1;
        au.progOnePoint = snaps.length === 1;
        au.progCountLabel = snaps.length === 1
          ? '1 recorded crawl'
          : snaps.length + ' recorded crawls · ' + snaps[0].date + ' → ' + snaps[snaps.length - 1].date;
        const prog = s.auProg;
        const METRICS = [
          ['score', 'Health score', '#4f46e5', sn => sn.score],
          ['errors', 'Errors', '#dc2626', sn => sn.errors],
          ['warnings', 'Warnings', '#d97706', sn => sn.warnings],
          ['notices', 'Notices', '#2563eb', sn => sn.notices],
          ['pages', 'Pages crawled', '#059669', sn => sn.pagesCrawled]
        ];
        const chipBase2 = { display: 'inline-flex', alignItems: 'center', gap: '7px', padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
        au.progToggles = METRICS.map(m => {
          const on = !!prog[m[0]];
          return {
            label: m[1],
            dot: { width: '8px', height: '8px', borderRadius: '50%', background: on ? m[2] : '#cbd5e1', flexShrink: 0 },
            style: on ? Object.assign({}, chipBase2, { borderColor: m[2], color: '#0f172a' }) : chipBase2,
            click: () => this.setState(st => ({ auProg: Object.assign({}, st.auProg, { [m[0]]: !st.auProg[m[0]] }) }))
          };
        });
        au.progLines = !au.progHasChart ? [] : METRICS.filter(m => prog[m[0]]).map(m => {
          const vals2 = snaps.map(m[3]);
          const max = Math.max(1, ...vals2);
          const pts = vals2.map((v, k) => {
            const x = (k / (snaps.length - 1)) * 590 + 5;
            const y = 190 - (v / max) * 175;
            return x.toFixed(1) + ',' + y.toFixed(1);
          }).join(' ');
          return { pts, color: m[2] };
        });
        au.progFrom = snaps[0].date; au.progTo = snaps[snaps.length - 1].date;
        au.progRows = snaps.slice().reverse().map((sn, k) => ({
          date: sn.date, latest: k === 0,
          score: sn.score, scoreStyle: scoreChip(sn.score),
          errors: this.fmt(sn.errors), warnings: this.fmt(sn.warnings), notices: this.fmt(sn.notices),
          pages: sn.pagesCrawled
        }));
      }

      /* page detail drawer */
      if (s.auPage) {
        const pg3 = data.crawledPages.find(x => x.id === s.auPage);
        if (pg3) {
          /* The failed checks for this page come from the real check list -- every check
             carries the pages it affects. `pg3.failed` was read here but the payload has
             never contained it, so opening the drawer threw on `pg3.failed.length` and took
             the whole render down with it. */
          const failed = data.checks.filter(c => c.pages.some(p => (typeof p === 'string' ? p : p.url) === pg3.url));
          /* Only measured facts, and only when they were measured. Each tile below is pushed
             only if its source produced a value for THIS page: score/load time come from the
             Lighthouse sample, the link and word counts from the OnPage crawl, and neither
             covers every crawled URL. A tile that would read "—" is omitted instead. */
          const pdStats = [
            { label: 'Crawl depth', value: pg3.depth + (pg3.depth === 1 ? ' click' : ' clicks') }
          ];
          if (pg3.loadTimeMs != null) pdStats.push({ label: 'Load time', value: secsText(pg3.loadTimeMs) });
          if (pg3.inLinks != null) pdStats.push({ label: 'In-links', value: numText(pg3.inLinks) });
          if (pg3.internalLinks != null) pdStats.push({ label: 'Internal links', value: numText(pg3.internalLinks) });
          if (pg3.externalLinks != null) pdStats.push({ label: 'External links', value: numText(pg3.externalLinks) });
          if (pg3.wordCount != null) pdStats.push({ label: 'Word count', value: numText(pg3.wordCount) });
          pdStats.push({ label: 'Issues', value: pg3.errors + 'E · ' + pg3.warnings + 'W · ' + pg3.notices + 'N' });
          vals.pd = {
            show: true, url: pg3.url,
            /* Unmeasured renders as the neutral dash chip (the drawer template in index.html
               reads pd.score/pd.scoreStyle as-is), so a page Lighthouse never sampled does not
               open showing a red 0. */
            score: scoreText(pg3.score), scoreStyle: scoreChip(pg3.score),
            status: pg3.statusCode + (pg3.kind === 'gone' ? ' · broken' : pg3.kind === 'redirect' ? ' · redirect' : pg3.kind === 'noindex' ? ' · blocked' : ' OK'),
            statusStyle: { marginLeft: 'auto', padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700, background: pg3.statusCode === 200 ? '#dcfce7' : pg3.statusCode < 400 ? '#f3e8ff' : '#fee2e2', color: pg3.statusCode === 200 ? '#15803d' : pg3.statusCode < 400 ? '#7c3aed' : '#b91c1c' },
            stats: pdStats,
            /* Per-page Core Web Vitals are not in the crawled-page payload (the site-wide p75
               is, on the Overview tab). The section stays hidden rather than showing zeros. */
            hasCwv: false, cwv: [],
            checkCount: failed.length, noChecks: failed.length === 0,
            checks: failed.map(c => ({
              title: c.title, sev: c.severity,
              sevStyle: { fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: SEVC[c.severity] },
              dot: dot(SEVC[c.severity]),
              click: () => { this.setState({ auPage: null, auSub: 'issues', auSev: 'all', auCat: 'all', auOpen: c.id, auSearch: '' }); this.pushNav({ auSub: 'issues' }); }
            }))
          };
        }
      }

      vals.au = au;
    }

