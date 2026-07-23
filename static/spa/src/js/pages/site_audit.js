    /* ============ SITE AUDIT ============ */
    if (tab === 'pages') {
      vals.showPages = true;
      const auSetup = !data || data.score == null || (typeof data.score === 'object' && data.score.state === 'setup') || (data.crawl && (data.crawl.status === 'never' || data.crawl.pagesCrawled === 0));

      if (auSetup) {
        vals.au = {
          setup: true,
          subTabs: [], showOverview: false, showIssues: false, showCrawled: false,
          showCompare: false, showProgress: false, showStats: false,
          domain: project.domain, crawlDate: '', pagesCrawled: 0, crawlDuration: '', userAgent: '',
          barSegs: [], breakRows: [], sevTotals: [], cats: [], vitals: [], domChecks: [], topIssues: [],
          sevFilters: [], catFilters: [], noIssues: true, issueRows: [], search: '',
          tableTabStyle: {}, treeTabStyle: {}, showTable: false, showTree: false,
          pgSearch: '', pageRows: [], pageRowCount: '', treeRows: [],
          statKpis: [], statCharts: [],
          cmpOptions: [], cmpOptions2: [], cmpFilters: [], cmpKpis: [], cmpEmpty: true, cmpRows: [],
          cmpA: '', cmpB: '', cmpALabel: '', cmpBLabel: '',
          progToggles: [], progLines: [], progFrom: '', progTo: '', progRows: []
        };
        return vals;
      }

      const SEVC = { error: '#dc2626', warning: '#d97706', notice: '#2563eb' };
      const sevRank = { error: 0, warning: 1, notice: 2 };
      const scoreColor = v => v >= 80 ? '#059669' : v >= 60 ? '#d97706' : '#dc2626';
      const scoreChip = v => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '34px', height: '22px', padding: '0 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, background: v >= 80 ? '#dcfce7' : v >= 60 ? '#fef3c7' : '#fee2e2', color: v >= 80 ? '#15803d' : v >= 60 ? '#b45309' : '#b91c1c' });
      const dot = c => ({ width: '9px', height: '9px', borderRadius: '50%', background: c, flexShrink: 0 });
      const sub = s.auSub;
      const totalIssues = data.totals.errors + data.totals.warnings + data.totals.notices;
      const goSub = v => { this.setState({ auSub: v }); this.pushNav({ auSub: v }); };
      const subBase = { padding: '10px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', color: '#64748b', borderBottom: '2px solid transparent', marginBottom: '-1px' };
      const activeChecks = data.checks.filter(c => !c.hidden && c.count > 0);
      const hiddenChecks = data.checks.filter(c => c.hidden);
      const crawlDate = data.crawl.startedAt;
      const au = {
        domain: project.domain,
        crawlDate, pagesCrawled: data.crawl.pagesCrawled, crawlDuration: data.crawl.duration, userAgent: data.crawl.userAgent,
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
        const vitalVerdict = (m) => m.p75 <= m.good ? ['Good', '#dcfce7', '#15803d'] : m.p75 <= m.poor ? ['Needs work', '#fef3c7', '#b45309'] : ['Poor', '#fee2e2', '#b91c1c'];
        au.vitals = [
          ['LCP', 'Largest Contentful Paint', data.cwv.lcp],
          ['TBT', 'Total Blocking Time', data.cwv.tbt],
          ['CLS', 'Cumulative Layout Shift', data.cwv.cls]
        ].map(v => {
          const m = v[2], vd = vitalVerdict(m);
          const b = m.buckets, tot = Math.max(1, b.good + b.mid + b.poor);
          return {
            name: v[0], desc: v[1], p75: m.p75, unit: m.unit,
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
      }

      if (sub === 'issues') {
        const fBase = { padding: '5px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
        const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
        au.sevFilters = [
          ['all', 'All (' + activeChecks.length + ')'],
          ['error', 'Errors (' + activeChecks.filter(c => c.severity === 'error').length + ')'],
          ['warning', 'Warnings (' + activeChecks.filter(c => c.severity === 'warning').length + ')'],
          ['notice', 'Notices (' + activeChecks.filter(c => c.severity === 'notice').length + ')'],
          ['hidden', 'Hidden (' + hiddenChecks.length + ')']
        ].map(f => ({ label: f[1], style: s.auSev === f[0] ? fActive : fBase, click: () => this.setState({ auSev: f[0], auOpen: null }) }));
        const chipBase = { padding: '5px 11px', fontSize: '12px', fontWeight: 500, borderRadius: '999px', cursor: 'pointer', color: '#64748b', border: '1px solid #e2e8f0', background: 'white' };
        const chipActive = Object.assign({}, chipBase, { borderColor: '#4f46e5', color: '#4f46e5', background: '#eef2ff' });
        au.catFilters = ['all'].concat(Object.keys(data.catScore)).map(cat => ({
          label: cat === 'all' ? 'All categories' : cat,
          style: s.auCat === cat ? chipActive : chipBase,
          click: () => this.setState({ auCat: cat, auOpen: null })
        }));
        let list = s.auSev === 'hidden' ? hiddenChecks : activeChecks.filter(c => s.auSev === 'all' || c.severity === s.auSev);
        if (s.auCat !== 'all') list = list.filter(c => c.category === s.auCat);
        if (s.auSearch) { const q = s.auSearch.toLowerCase(); list = list.filter(c => c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q)); }
        list = list.slice().sort((a, b2) => sevRank[a.severity] - sevRank[b2.severity] || b2.count - a.count);
        au.noIssues = list.length === 0;
        const statusOf = pg2 => pg2 ? (pg2.statusCode + (pg2.kind === 'gone' ? ' · broken' : pg2.kind === 'redirect' ? ' · redirect' : '')) : '200';
        const pgByUrl = {};
        data.crawledPages.forEach(pg2 => { pgByUrl[pg2.url] = pg2; });
        au.issueRows = list.map(c => {
          const open = s.auOpen === c.id;
          const shown = c.pages.slice(0, 8);
          return {
            title: c.title, category: c.category, open, howToFix: c.howToFix,
            dot: dot(c.hidden ? '#cbd5e1' : SEVC[c.severity]),
            rowStyle: { display: 'flex', alignItems: 'center', gap: '12px', padding: '13px 20px', cursor: 'pointer', opacity: c.hidden ? 0.6 : 1 },
            countLabel: this.fmt(c.count) + ' page' + (c.count === 1 ? '' : 's'),
            countStyle: { fontSize: '12px', fontWeight: 700, color: c.hidden ? '#94a3b8' : SEVC[c.severity], minWidth: '60px', textAlign: 'right' },
            chev: { color: '#cbd5e1', fontSize: '18px', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease' },
            toggle: () => this.setState({ auOpen: open ? null : c.id }),
            hasPages: c.pages.length > 0,
            pages: shown.map(u => { const pg2 = pgByUrl[u]; return { url: u, score: pg2 ? pg2.score : '—', scoreStyle: scoreChip(pg2 ? pg2.score : 0), status: statusOf(pg2) }; }),
            more: c.pages.length > 8, moreLabel: '+ ' + (c.pages.length - 8) + ' more pages — export for the full list',
            exportPages: () => this.downloadCsv(project.domain + '-' + c.id + '.csv', [['url', 'url']], c.pages.map(u => ({ url: u }))),
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
          au.pageRows = rows.slice(0, 40).map(r => ({
            open: () => this.setState({ auPage: r.id }),
            url: r.url, score: r.score, scoreStyle: scoreChip(r.score),
            status: String(r.statusCode),
            statusStyle: { padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, background: r.statusCode === 200 ? '#dcfce7' : r.statusCode < 400 ? '#f3e8ff' : '#fee2e2', color: r.statusCode === 200 ? '#15803d' : r.statusCode < 400 ? '#7c3aed' : '#b91c1c' },
            issuesLabel: r.errors + 'E · ' + r.warnings + 'W · ' + r.notices + 'N',
            depth: r.depth, inLinks: r.inLinks,
            loadLabel: (r.loadTimeMs / 1000).toFixed(1) + ' s',
            loadStyle: { fontSize: '12.5px', fontWeight: 600, color: r.loadTimeMs > 3000 ? '#dc2626' : r.loadTimeMs > 1500 ? '#b45309' : '#64748b' }
          }));
          au.pageRowCount = rows.length > 40 ? 'Showing 40 of ' + rows.length + ' pages — refine with the URL filter or export the full list' : rows.length + ' page' + (rows.length === 1 ? '' : 's');
        } else {
          au.treeRows = data.structure.map(t => ({
            folder: t.folder, pages: t.pages, avgScore: t.avgScore, scoreStyle: scoreChip(t.avgScore),
            errors: t.errors, warnings: t.warnings, notices: t.notices
          }));
        }
      }
      if (sub === 'stats') {
        const cp = data.crawledPages;
        const ok = cp.filter(x => x.kind === 'ok');
        const avg = (arr, f) => arr.length ? arr.reduce((s2, x) => s2 + f(x), 0) / arr.length : 0;
        au.statKpis = [
          { label: 'Avg. page score', value: Math.round(avg(ok, x => x.score)), sub: 'across ' + ok.length + ' healthy pages' },
          { label: 'Avg. load time', value: (avg(ok, x => x.loadTimeMs) / 1000).toFixed(1) + ' s', sub: 'server response + render' },
          { label: 'Avg. internal links', value: Math.round(avg(ok, x => x.internalLinks)), sub: 'outgoing per page' },
          { label: 'Avg. word count', value: this.fmt(Math.round(avg(ok, x => x.wordCount))), sub: 'per indexable page' }
        ];
        const mkChart = (title, defs, colorAt) => {
          const total = Math.max(1, defs.reduce((s2, d) => s2 + d[1], 0));
          return {
            title,
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
        au.statCharts = [
          mkChart('HTTP status codes', [
            ['200 OK', cp.filter(x => x.statusCode === 200).length],
            ['3xx redirect', cp.filter(x => x.statusCode >= 300 && x.statusCode < 400).length],
            ['4xx client error', cp.filter(x => x.statusCode >= 400 && x.statusCode < 500).length],
            ['5xx server error', cp.filter(x => x.statusCode >= 500).length]
          ], (k) => k === 0 ? '#059669' : k === 1 ? '#8b5cf6' : k === 2 ? '#dc2626' : '#991b1b'),
          mkChart('Crawl depth', [
            ['1 click', cp.filter(x => x.depth <= 1).length],
            ['2 clicks', cp.filter(x => x.depth === 2).length],
            ['3 clicks', cp.filter(x => x.depth === 3).length],
            ['4+ clicks', cp.filter(x => x.depth >= 4).length]
          ], k => seq[k]),
          mkChart('Load time', [
            ['Fast (<1.5 s)', ok.filter(x => x.loadTimeMs < 1500).length],
            ['Average (1.5–3 s)', ok.filter(x => x.loadTimeMs >= 1500 && x.loadTimeMs <= 3000).length],
            ['Slow (>3 s)', ok.filter(x => x.loadTimeMs > 3000).length]
          ], k => gwp[k]),
          mkChart('Content length', [
            ['In-depth (1000+ words)', ok.filter(x => x.wordCount >= 1000).length],
            ['Standard (250–999)', ok.filter(x => x.wordCount >= 250 && x.wordCount < 1000).length],
            ['Thin (<250 words)', ok.filter(x => x.wordCount < 250).length]
          ], k => gwp[k])
        ];
      }

      if (sub === 'compare' && !data.snapshots.length) {
        // No audit history yet (nothing records historical crawl snapshots) -- show an empty
        // state instead of crashing on snaps[0].
        au.cmpOptions = []; au.cmpOptions2 = []; au.cmpFilters = []; au.cmpKpis = [];
        au.cmpRows = []; au.cmpEmpty = true; au.cmpA = ''; au.cmpB = '';
        au.cmpALabel = '—'; au.cmpBLabel = '—';
      } else if (sub === 'compare') {
        const snaps = data.snapshots;
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
      } else if (sub === 'progress') {
        const snaps = data.snapshots;
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
        au.progLines = METRICS.filter(m => prog[m[0]]).map(m => {
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
          const cwvDot = (v, good, poor) => ({ width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0, background: v <= good ? '#059669' : v <= poor ? '#d97706' : '#dc2626' });
          vals.pd = {
            show: true, url: pg3.url,
            score: pg3.score, scoreStyle: scoreChip(pg3.score),
            status: pg3.statusCode + (pg3.kind === 'gone' ? ' · broken' : pg3.kind === 'redirect' ? ' · redirect' : pg3.kind === 'noindex' ? ' · blocked' : ' OK'),
            statusStyle: { marginLeft: 'auto', padding: '3px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 700, background: pg3.statusCode === 200 ? '#dcfce7' : pg3.statusCode < 400 ? '#f3e8ff' : '#fee2e2', color: pg3.statusCode === 200 ? '#15803d' : pg3.statusCode < 400 ? '#7c3aed' : '#b91c1c' },
            stats: [
              { label: 'Crawl depth', value: pg3.depth + (pg3.depth === 1 ? ' click' : ' clicks') },
              { label: 'In-links', value: pg3.inLinks },
              { label: 'Load time', value: (pg3.loadTimeMs / 1000).toFixed(1) + ' s' },
              { label: 'Internal links', value: pg3.internalLinks },
              { label: 'External links', value: pg3.externalLinks },
              { label: 'Word count', value: this.fmt(pg3.wordCount) }
            ],
            hasCwv: !!pg3.cwv,
            cwv: pg3.cwv ? [
              { name: 'LCP', value: pg3.cwv.lcp + ' s', dot: cwvDot(pg3.cwv.lcp, 2.5, 4) },
              { name: 'TBT', value: pg3.cwv.tbt + ' ms', dot: cwvDot(pg3.cwv.tbt, 200, 600) },
              { name: 'CLS', value: pg3.cwv.cls, dot: cwvDot(pg3.cwv.cls, 0.1, 0.25) }
            ] : [],
            checkCount: pg3.failed.length, noChecks: pg3.failed.length === 0,
            checks: pg3.failed.map(id => {
              const c = data.checks.find(x => x.id === id) || { title: id, severity: 'notice' };
              return {
                title: c.title, sev: c.severity,
                sevStyle: { fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: SEVC[c.severity] },
                dot: dot(SEVC[c.severity]),
                click: () => { this.setState({ auPage: null, auSub: 'issues', auSev: 'all', auCat: 'all', auOpen: id, auSearch: '' }); this.pushNav({ auSub: 'issues' }); }
              };
            })
          };
        }
      }

      vals.au = au;
    }

