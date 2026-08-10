    /* ============ BACKLINKS ============ */
    if (tab === 'backlinks') {
      vals.showBacklinks = true;
      const sum = data.summary;
      const setup = !data || !sum || sum.state === 'setup' || (sum.backlinks === 0 && (!data.links || !data.links.length));

      if (setup) {
        vals.bl = {
          setup: true,
          srcMain: this.srcBadge(null), srcGap: this.srcBadge(null),
          tabs: [], isOverview: false, isLinks: false, isRefDom: false, isAnchors: false, isGap: false,
          lastUpdated: '', chartBars: [], chartLabels: [], typeArcs: [], typeLegend: [],
          asBuckets: [], topAnchors: [], topRefDomains: [], allRefDomains: [],
          rows: [], statusFilters: [], followFilters: [], allAnchors: [],
          /* Paging + counters for the three paginated lists. Present and empty in the setup
             state because the template reads them unconditionally — a missing key here is a
             render crash, not a blank card. */
          rowCount: '', rdCount: '', anCount: '',
          hasPageNav: false, pageNums: [], pagePrev: {}, pageNext: {},
          rdHasPageNav: false, rdPageNums: [], rdPagePrev: {}, rdPageNext: {},
          anHasPageNav: false, anPageNums: [], anPagePrev: {}, anPageNext: {},
          sort: { rank: () => {}, spam: () => {}, firstSeen: () => {} },
          arrow: { rank: '', spam: '', firstSeen: '' },
          gapCols: [], gapRows: [], gapOnly: false,
          gapBtnBorder: '#e2e8f0', gapBtnBg: 'white', gapBtnColor: '#64748b'
        };
        return vals;
      }

      const links = data.links || [];
      const asColorOf = as => as >= 60 ? '#059669' : as >= 40 ? '#0891b2' : as >= 20 ? '#d97706' : '#94a3b8';
      const asBgOf = as => as >= 60 ? '#ecfdf5' : as >= 40 ? '#ecfeff' : as >= 20 ? '#fffbeb' : '#f1f5f9';
      /* DataForSEO's backlink spam score is 0-100. Green to 30, amber 31-60, red above 60 —
         one banding for every spam surface on the page (the KPI card, the referring-domain
         column and the per-link column), because two scales on one screen is how a reader
         learns to distrust both. The old bands were red at 30 and amber at 10, which painted
         an ordinary 12 amber and a merely-questionable 30 red. */
      const spamColorOf = sp => sp > 60 ? '#dc2626' : sp > 30 ? '#d97706' : '#059669';
      const asChip = as => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '26px', padding: '2px 6px', borderRadius: '5px', fontSize: '12px', fontWeight: 600, color: asColorOf(as), background: asBgOf(as) });
      const shortN = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'K' : ('' + n);
      // Values with no column behind them arrive as null; show a dash, never a stand-in number.
      const orDash = v => (v === null || v === undefined || v === '') ? '—' : v;
      const stripProto = u => ('' + (u || '')).replace(/^https?:\/\//, '');
      // `domain_rank` off the `backlinks` table is DataForSEO's raw 0-1000 domain_from_rank.
      // Every "AS" surface here (chip colors, the donut ring) assumes a 0-100 scale -- the same
      // /10 conversion pipeline/services/backlinks_service.py already applies for the snapshot
      // aggregates. Without it a rank of 703 rendered as "AS 703" against a 0-100 donut and
      // always hit the >=60 "green" color band regardless of real standing.
      const asOf = raw => (raw === null || raw === undefined) ? null : Math.max(0, Math.min(100, Math.round(raw / 10)));

      const bl = {};
      /* Every backlink surface comes from the one DataForSEO Backlinks connector. Link Gap
         additionally needs the tracked-competitor list, but that is user-entered config
         rather than synced data, so it adds no connector to the badge. */
      bl.srcMain = this.srcBadge(['dataforseo_backlinks']);
      bl.srcGap = this.srcBadge(['dataforseo_backlinks'],
        'Compared against the competitor domains you configured — that list is not synced.');
      bl.lastUpdated = sum.lastUpdated || 'never';
      // sub-tabs
      const tabDef = [['overview', 'Overview'], ['backlinks', 'Backlinks'], ['refdomains', 'Referring Domains'], ['anchors', 'Anchors'], ['linkgap', 'Link Gap']];
      bl.tabs = tabDef.map(([k, label]) => {
        const active = s.blTab === k;
        return { label, click: () => { this.setState({ blTab: k }); this.pushNav({ blTab: k }); }, style: { padding: '12px 16px', fontSize: '14px', cursor: 'pointer', color: active ? '#4f46e5' : '#64748b', fontWeight: active ? 600 : 400, borderBottom: '2px solid ' + (active ? '#4f46e5' : 'transparent') } };
      });
      bl.isOverview = s.blTab === 'overview';
      bl.isLinks = s.blTab === 'backlinks';
      bl.isRefDom = s.blTab === 'refdomains';
      bl.isAnchors = s.blTab === 'anchors';
      bl.isGap = s.blTab === 'linkgap';

      // KPIs
      const asScore = asOf(sum.authorityScore) || 0;
      bl.as = asScore; bl.asColor = asColorOf(asScore);
      bl.asDash = (asScore / 100 * 188.5).toFixed(1) + ' 188.5'; bl.asDelta = orDash(sum.asDelta);
      bl.refDomainsFmt = this.fmt(sum.refDomains); bl.newRdMonth = orDash(sum.newRdMonth);
      bl.backlinksFmt = this.fmt(sum.backlinks); bl.backlinksShort = shortN(sum.backlinks);
      bl.dofollowPct = sum.dofollowPct; bl.brokenFmt = this.fmt(sum.broken);
      bl.spamScore = orDash(sum.spamScore);
      bl.spamColor = sum.spamScore === null || sum.spamScore === undefined ? '#94a3b8' : spamColorOf(sum.spamScore);
      /* The markup hard-codes a trailing "%" on spam and a leading "▲" on new-this-month, so a
         null value rendered as "—%" and "▲ — new this month" — a unit and a direction asserted
         over a number that does not exist. These booleans let the template drop the whole line
         instead. Same defect class as the Spam column that was removed outright. */
      bl.hasSpamScore = sum.spamScore !== null && sum.spamScore !== undefined;
      bl.hasNewRdMonth = sum.newRdMonth !== null && sum.newRdMonth !== undefined;

      // new/lost chart — empty until a backlinks sync stores real history
      const months = data.months || [];
      const maxMonth = months.reduce((m, x) => Math.max(m, x.nw || 0, x.lost || 0), 0) || 1;
      const barW = months.length ? 640 / months.length : 0;
      bl.chartBars = months.map((m, i) => ({ x: (i * barW + 2).toFixed(1), w: Math.max(0, barW - 4).toFixed(1), newH: (((m.nw || 0) / maxMonth) * 82).toFixed(1), newY: (90 - ((m.nw || 0) / maxMonth) * 82).toFixed(1), lostH: (((m.lost || 0) / maxMonth) * 82).toFixed(1) }));
      if (months.length) {
        const labelStep = Math.max(1, Math.ceil(months.length / 6));
        bl.chartLabels = months.filter((m, i) => i % labelStep === 0).map(m => m.label);
      } else {
        bl.chartLabels = ['No new/lost history synced yet'];
      }

      // types donut — only from the stored DataForSEO link-type breakdown
      const types = data.types || [];
      let acc = 0;
      bl.typeArcs = types.map(t => { const arc = { color: t.color, dash: t.pct + ' ' + (100 - t.pct), offset: (100 - acc) % 100 }; acc += t.pct; return arc; });
      bl.typeLegend = types.map(t => ({ label: t.label, color: t.color, pct: t.pct }));

      // AS buckets
      const asbSrc = data.asBuckets || [];
      const maxBucket = asbSrc.reduce((m, b) => Math.max(m, b.count || 0), 0) || 1;
      bl.asBuckets = asbSrc.map(b => ({ label: b.label, color: b.color, countFmt: this.fmt(b.count), pct: Math.round(((b.count || 0) / maxBucket) * 100) }));

      // top anchors
      const anchorsSrc = data.anchors || [];
      const maxAnchor = anchorsSrc.reduce((m, a) => Math.max(m, a.backlinks || 0), 0) || 1;
      bl.topAnchors = anchorsSrc.slice(0, 6).map(a => ({ anchor: a.anchor, pct: Math.round(((a.backlinks || 0) / maxAnchor) * 100) }));

      /* ---- PAGINATION ----------------------------------------------------------------
         Three lists on this page render straight into the DOM: the backlinks table used to
         hard-slice to 60 (the endpoint returns up to 1000, so rows 61-1000 were downloaded
         and unreachable), while Referring Domains and Anchors rendered EVERY row behind a
         fixed-height scroller. Now that one referring domain can contribute one row per
         source page rather than exactly one row, those two are the ones that grow fastest.

         The arithmetic is `this.pageSlice` / `this.pageWindow` from app.js — the same helpers
         the Site Audit table uses, pinned by static/spa/tests/page_window.test.js. `pageSlice`
         CLAMPS the requested index rather than trusting it, which is what keeps a stale page
         number from rendering an empty table that reads as "nothing matched your filter".
         That clamp is also what covers switching project or finishing a sync while parked on
         page 8: those two live in app.js's own handlers, so the page index is not reset there,
         but a clamped index still lands on real rows. */
      const BL_PAGE_SIZE = 40;
      const pageBtnStyle = active => ({ minWidth: '30px', padding: '5px 9px', fontSize: '12.5px', fontWeight: 600, borderRadius: '6px', cursor: 'pointer', border: '1px solid ' + (active ? '#4f46e5' : '#e2e8f0'), background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b' });
      const navBtnStyle = on => ({ padding: '5px 11px', fontSize: '12.5px', fontWeight: 600, borderRadius: '6px', border: '1px solid #e2e8f0', background: 'white', color: on ? '#64748b' : '#cbd5e1', cursor: on ? 'pointer' : 'default' });
      const paginate = (rows, requested, stateKey) => {
        const pg = this.pageSlice(rows.length, requested, BL_PAGE_SIZE);
        const go = n => () => this.setState({ [stateKey]: n });
        return {
          visible: rows.slice(pg.from, pg.from + BL_PAGE_SIZE),
          from: pg.from, shown: pg.shown,
          hasNav: pg.pageCount > 1,
          nums: this.pageWindow(pg.pageCount, pg.pageIdx).map(n => n === 'gap'
            ? { label: '…', click: () => {}, style: { padding: '5px 4px', fontSize: '12.5px', color: '#cbd5e1' } }
            : { label: String(n + 1), click: go(n), style: pageBtnStyle(n === pg.pageIdx) }),
          prev: { click: pg.pageIdx > 0 ? go(pg.pageIdx - 1) : () => {}, style: navBtnStyle(pg.pageIdx > 0) },
          next: { click: pg.pageIdx < pg.pageCount - 1 ? go(pg.pageIdx + 1) : () => {}, style: navBtnStyle(pg.pageIdx < pg.pageCount - 1) }
        };
      };
      /* "Showing 41–80 of 213" — the range and the total it is a range OF. `noun` names what
         is being counted so the sentence never has to be reconstructed from a bare number. */
      const showingText = (pg, total, noun) => total === 0
        ? 'No ' + noun + ' match this filter'
        : 'Showing ' + (pg.from + 1) + '–' + (pg.from + pg.shown) + ' of ' + this.fmt(total);

      // referring domains
      const refRow = x => { const as = asOf(x.rank) || 0; return { domain: x.domain, flag: x.flag, as: as, asStyle: asChip(as), backlinksFmt: this.fmt(x.backlinks), linksToUs: x.linksToUs, follow: x.follow ? 'Dofollow' : 'Nofollow', followColor: x.follow ? '#059669' : '#94a3b8', firstSeen: x.firstSeen || '', isNew: !!x.isNew, category: x.category || '', hasSpam: x.spam !== null && x.spam !== undefined, spam: orDash(x.spam), spamColor: (x.spam === null || x.spam === undefined) ? '#94a3b8' : spamColorOf(x.spam) }; };
      const refDomains = data.refDomains || [];
      bl.topRefDomains = refDomains.slice(0, 8).map(refRow);
      const rdPg = paginate(refDomains, s.blRdPage, 'blRdPage');
      bl.allRefDomains = rdPg.visible.map(refRow);
      bl.rdCount = showingText(rdPg, refDomains.length, 'referring domains');
      bl.rdHasPageNav = rdPg.hasNav;
      bl.rdPageNums = rdPg.nums; bl.rdPagePrev = rdPg.prev; bl.rdPageNext = rdPg.next;

      /* The path part of a source URL, for the second line of the referring-domain cell.
         Shows what distinguishes one source page from another: the scheme and the host are
         already on the line above, and repeating them costs the width the path needs. */
      const sourcePathOf = u => {
        const bare = stripProto(u);
        const cut = bare.indexOf('/');
        return cut === -1 ? '/' : (bare.slice(cut) || '/');
      };

      // backlinks table — one row per stored Backlink, nothing synthesised.
      const blRows = links.map(l => ({
        domain: l.domain,
        flag: '🌐',
        anchor: l.anchor || '—',
        urlTo: stripProto(l.target_url),
        // The exact page carrying the link. '' for a row whose source page was never
        // recorded — see the row builder below for why that is shown as its own state
        // rather than quietly swapped for the referring domain's homepage.
        urlFrom: l.url_from || '',
        rank: (l.domain_rank === null || l.domain_rank === undefined) ? null : l.domain_rank,
        pageRank: (l.page_rank === null || l.page_rank === undefined) ? null : l.page_rank,
        spam: (l.spam_score === null || l.spam_score === undefined) ? null : l.spam_score,
        dofollow: !!l.dofollow,
        isNew: !!l.isNew,
        isLost: l.status === 'lost',
        firstSeen: l.firstSeen || '',
        // The raw ISO date is what the First-seen column sorts on. `firstSeen` is the display
        // string ("Jan 01, 2026"), and sorting THAT compares text, so April would precede
        // January (skills.md §9: format at the edge, sort the value).
        firstSeenIso: l.first_seen || null
      }));
      const anyFirstSeen = blRows.some(x => !!x.firstSeen);

      let blr = blRows;
      if (s.blFilter === 'new') blr = blr.filter(x => x.isNew);
      else if (s.blFilter === 'lost') blr = blr.filter(x => x.isLost);
      if (s.blFollow === 'dofollow') blr = blr.filter(x => x.dofollow);
      else if (s.blFollow === 'nofollow') blr = blr.filter(x => !x.dofollow);
      blr = this.sortRows(blr, s.blSort);
      const blPg = paginate(blr, s.blPage, 'blPage');
      /* THE COUNTER. It used to read "Showing {min(filtered, 60)} of {summary.backlinks}" —
         a filtered, 60-capped sample printed as a ratio of the snapshot's WHOLE-PROFILE
         total, so with the Lost filter on it said "Showing 12 of 729". Those two numbers
         answer different questions and were never a ratio. Now the range and its own total
         are one statement, and the profile total is a separate, labelled clause. */
      bl.rowCount = showingText(blPg, blr.length, 'backlinks')
        + (blr.length ? ' matching' : '')
        + (sum.backlinks ? ' (of ' + this.fmt(sum.backlinks) + ' in the profile)' : '')
        /* The stored rows are a per-sync SAMPLE, bought at a configurable row limit. When it
           is full, the profile has more links than we hold and the page must say so rather
           than letting a reader take the sample for the whole. */
        + (data.linksCapped ? ' · this sample is capped at ' + this.fmt(data.linksLimit) + ' links per sync' : '');
      bl.rows = blPg.visible.map(x => {
        const badges = [];
        if (x.isNew) badges.push({ label: 'NEW', color: '#059669', bg: '#ecfdf5' });
        if (x.isLost) badges.push({ label: 'LOST', color: '#dc2626', bg: '#fef2f2' });
        /* SOURCE PAGE. This used to be `x.urlFrom || ('https://' + x.domain)`, used only as
           an invisible href on the domain name — so the table showed OUR url and never
           THEIRS, and a row whose source page we never recorded was indistinguishable from
           one where we know the exact page: both rendered as the same clickable domain.
           The path is now visible text, and "unknown" is its own state. */
        const hasSource = !!x.urlFrom;
        const hasSpam = x.spam !== null && x.spam !== undefined;
        const domainAs = asOf(x.rank);
        return {
          flag: x.flag,
          pageTitle: x.domain,
          domainHref: 'https://' + x.domain,
          hasSource: hasSource,
          noSource: !hasSource,
          urlFrom: x.urlFrom,
          sourcePath: hasSource ? sourcePathOf(x.urlFrom) : 'source page unknown',
          anchor: x.anchor,
          urlTo: x.urlTo,
          domainRank: orDash(domainAs),
          asStyle: asChip(domainAs || 0),
          pageRank: orDash(asOf(x.pageRank)),
          hasSpam: hasSpam,
          spam: hasSpam ? x.spam : '',
          spamColor: hasSpam ? spamColorOf(x.spam) : 'transparent',
          follow: x.dofollow ? 'Dofollow' : 'Nofollow',
          followColor: x.dofollow ? '#059669' : '#94a3b8',
          firstSeen: x.firstSeen,
          badges
        };
      });
      bl.hasPageNav = blPg.hasNav;
      bl.pageNums = blPg.nums; bl.pagePrev = blPg.prev; bl.pageNext = blPg.next;
      /* Sortable columns. The third argument to `mkSortHandler` is the page-index state key:
         re-sorting has to return the reader to page 1, or the rows they were looking at are
         replaced by an arbitrary slice of a different ordering. app.js registers an unused
         `h.sortBl` / `h.blArrow` pair for the same state key, built WITHOUT that third
         argument and wired to nothing; these are the live handlers. */
      bl.sort = {
        rank: this.mkSortHandler('blSort', 'rank', 'blPage'),
        spam: this.mkSortHandler('blSort', 'spam', 'blPage'),
        firstSeen: this.mkSortHandler('blSort', 'firstSeenIso', 'blPage')
      };
      bl.arrow = {
        rank: this.arrow(s.blSort, 'rank'),
        spam: this.arrow(s.blSort, 'spam'),
        firstSeen: this.arrow(s.blSort, 'firstSeenIso')
      };
      /* Every filter chip resets the page as well as setting the filter. Without it, filtering
         900 rows down to 12 while parked on page 8 renders an empty table that reads as "no
         backlinks match" — the Site Audit table resets `auPgPage` from its search box for
         exactly this reason. */
      const mkF = (val, cur, key, label) => { const active = cur === val; return { label, click: () => { this.setState({ [key]: val, blPage: 0 }); this.pushNav(); }, style: { padding: '8px 14px', cursor: 'pointer', background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b', fontWeight: active ? 600 : 400, borderLeft: '1px solid #e2e8f0' } }; };
      // "Broken" is not tracked (no HTTP-status column), and "New" needs real first_seen dates.
      bl.statusFilters = [mkF('all', s.blFilter, 'blFilter', 'All')];
      if (anyFirstSeen) bl.statusFilters.push(mkF('new', s.blFilter, 'blFilter', 'New'));
      bl.statusFilters.push(mkF('lost', s.blFilter, 'blFilter', 'Lost'));
      bl.statusFilters[0].style.borderLeft = 'none';
      bl.followFilters = [mkF('all', s.blFollow, 'blFollow', 'All links'), mkF('dofollow', s.blFollow, 'blFollow', 'Dofollow'), mkF('nofollow', s.blFollow, 'blFollow', 'Nofollow')];
      bl.followFilters[0].style.borderLeft = 'none';

      // anchors
      const typeColors = { Branded: ['#4338ca', '#eef2ff'], URL: ['#0891b2', '#ecfeff'], Keyword: ['#059669', '#ecfdf5'], Generic: ['#64748b', '#f1f5f9'], Empty: ['#94a3b8', '#f8fafc'] };
      const anPg = paginate(anchorsSrc, s.blAnPage, 'blAnPage');
      bl.allAnchors = anPg.visible.map(a => ({ anchor: a.anchor, type: a.type, typeColor: (typeColors[a.type] || typeColors.Generic)[0], typeBg: (typeColors[a.type] || typeColors.Generic)[1], backlinksFmt: this.fmt(a.backlinks), refDomainsFmt: this.fmt(a.refDomains), dofollowPct: a.dofollowPct }));
      bl.anCount = showingText(anPg, anchorsSrc.length, 'anchors');
      bl.anHasPageNav = anPg.hasNav;
      bl.anPageNums = anPg.nums; bl.anPagePrev = anPg.prev; bl.anPageNext = anPg.next;

      // link gap — needs each competitor's referring domains, which nothing syncs yet
      let gapSource = data.gapDomains || [];
      if (s.gapOnly) gapSource = gapSource.filter(g => !g.you && g.comp.filter(Boolean).length >= 2);
      bl.gapCols = gapSource.length ? [{ name: 'You', color: '#4f46e5' }].concat((data.competitors || []).map(c => ({ name: c, color: '#64748b' }))) : [];
      bl.gapRows = gapSource.slice().sort((a, b) => b.rank - a.rank).map(g => {
        const compCount = g.comp.filter(Boolean).length;
        const cells = [{ linked: g.you, missing: !g.you, color: '#4f46e5' }].concat(g.comp.map(c => ({ linked: c, missing: !c, color: '#22c55e' })));
        let opp = 'Low', oc = '#64748b', ob = '#f1f5f9';
        if (!g.you && compCount >= 3 && g.rank >= 50) { opp = 'High'; oc = '#059669'; ob = '#ecfdf5'; }
        else if (!g.you && compCount >= 2) { opp = 'Medium'; oc = '#d97706'; ob = '#fffbeb'; }
        else if (g.you) { opp = 'Have it'; oc = '#4f46e5'; ob = '#eef2ff'; }
        return { domain: g.domain, flag: g.flag, as: g.rank, asStyle: asChip(g.rank), cells, opp, oppColor: oc, oppBg: ob };
      });
      bl.gapOnly = s.gapOnly;
      bl.gapBtnBorder = s.gapOnly ? '#c7d2fe' : '#e2e8f0';
      bl.gapBtnBg = s.gapOnly ? '#eef2ff' : 'white';
      bl.gapBtnColor = s.gapOnly ? '#4338ca' : '#64748b';

      vals.bl = bl;
    }

