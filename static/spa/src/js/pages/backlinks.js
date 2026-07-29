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
          gapCols: [], gapRows: [], gapOnly: false,
          gapBtnBorder: '#e2e8f0', gapBtnBg: 'white', gapBtnColor: '#64748b'
        };
        return vals;
      }

      const links = data.links || [];
      const asColorOf = as => as >= 60 ? '#059669' : as >= 40 ? '#0891b2' : as >= 20 ? '#d97706' : '#94a3b8';
      const asBgOf = as => as >= 60 ? '#ecfdf5' : as >= 40 ? '#ecfeff' : as >= 20 ? '#fffbeb' : '#f1f5f9';
      const spamColorOf = sp => sp >= 30 ? '#dc2626' : sp >= 10 ? '#d97706' : '#059669';
      const asChip = as => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '26px', padding: '2px 6px', borderRadius: '5px', fontSize: '12px', fontWeight: 600, color: asColorOf(as), background: asBgOf(as) });
      const shortN = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'K' : ('' + n);
      // Values with no column behind them arrive as null; show a dash, never a stand-in number.
      const orDash = v => (v === null || v === undefined || v === '') ? '—' : v;
      const stripProto = u => ('' + (u || '')).replace(/^https?:\/\//, '');

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
      bl.as = sum.authorityScore; bl.asColor = asColorOf(sum.authorityScore);
      bl.asDash = (sum.authorityScore / 100 * 188.5).toFixed(1) + ' 188.5'; bl.asDelta = orDash(sum.asDelta);
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

      // referring domains
      const refRow = x => ({ domain: x.domain, flag: x.flag, as: x.rank, asStyle: asChip(x.rank), backlinksFmt: this.fmt(x.backlinks), linksToUs: x.linksToUs, follow: x.follow ? 'Dofollow' : 'Nofollow', followColor: x.follow ? '#059669' : '#94a3b8', firstSeen: x.firstSeen || '', isNew: !!x.isNew, category: x.category || '' });
      const refDomains = data.refDomains || [];
      bl.topRefDomains = refDomains.slice(0, 8).map(refRow);
      bl.allRefDomains = refDomains.map(refRow);

      // backlinks table — one row per stored Backlink, nothing synthesised.
      // The source *page* URL and title are not columns on `backlinks`, so the row shows the
      // referring domain and leaves the sub-line empty rather than inventing a deep link.
      const blRows = links.map(l => ({
        domain: l.domain,
        flag: '🌐',
        anchor: l.anchor || '—',
        urlTo: stripProto(l.target_url),
        rank: (l.domain_rank === null || l.domain_rank === undefined) ? null : l.domain_rank,
        dofollow: !!l.dofollow,
        isNew: !!l.isNew,
        isLost: l.status === 'lost',
        firstSeen: l.firstSeen || ''
      }));
      const anyFirstSeen = blRows.some(x => !!x.firstSeen);

      let blr = blRows;
      if (s.blFilter === 'new') blr = blr.filter(x => x.isNew);
      else if (s.blFilter === 'lost') blr = blr.filter(x => x.isLost);
      if (s.blFollow === 'dofollow') blr = blr.filter(x => x.dofollow);
      else if (s.blFollow === 'nofollow') blr = blr.filter(x => !x.dofollow);
      bl.rowCount = this.fmt(Math.min(blr.length, 60));
      bl.rows = blr.slice(0, 60).map(x => {
        const badges = [];
        if (x.isNew) badges.push({ label: 'NEW', color: '#059669', bg: '#ecfdf5' });
        if (x.isLost) badges.push({ label: 'LOST', color: '#dc2626', bg: '#fef2f2' });
        return {
          flag: x.flag,
          pageTitle: x.domain,
          urlFrom: '',
          anchor: x.anchor,
          urlTo: x.urlTo,
          domainRank: orDash(x.rank),
          asStyle: asChip(x.rank || 0),
          // No spam-score column on `backlinks`; the markup hard-codes a trailing "%", so the
          // cell is rendered transparent until that column is removed from backlinks.html.
          spam: '',
          spamColor: 'transparent',
          follow: x.dofollow ? 'Dofollow' : 'Nofollow',
          followColor: x.dofollow ? '#059669' : '#94a3b8',
          firstSeen: x.firstSeen,
          badges
        };
      });
      const mkF = (val, cur, key, label) => { const active = cur === val; return { label, click: () => { this.setState({ [key]: val }); this.pushNav(); }, style: { padding: '8px 14px', cursor: 'pointer', background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b', fontWeight: active ? 600 : 400, borderLeft: '1px solid #e2e8f0' } }; };
      // "Broken" is not tracked (no HTTP-status column), and "New" needs real first_seen dates.
      bl.statusFilters = [mkF('all', s.blFilter, 'blFilter', 'All')];
      if (anyFirstSeen) bl.statusFilters.push(mkF('new', s.blFilter, 'blFilter', 'New'));
      bl.statusFilters.push(mkF('lost', s.blFilter, 'blFilter', 'Lost'));
      bl.statusFilters[0].style.borderLeft = 'none';
      bl.followFilters = [mkF('all', s.blFollow, 'blFollow', 'All links'), mkF('dofollow', s.blFollow, 'blFollow', 'Dofollow'), mkF('nofollow', s.blFollow, 'blFollow', 'Nofollow')];
      bl.followFilters[0].style.borderLeft = 'none';

      // anchors
      const typeColors = { Branded: ['#4338ca', '#eef2ff'], URL: ['#0891b2', '#ecfeff'], Keyword: ['#059669', '#ecfdf5'], Generic: ['#64748b', '#f1f5f9'], Empty: ['#94a3b8', '#f8fafc'] };
      bl.allAnchors = anchorsSrc.map(a => ({ anchor: a.anchor, type: a.type, typeColor: (typeColors[a.type] || typeColors.Generic)[0], typeBg: (typeColors[a.type] || typeColors.Generic)[1], backlinksFmt: this.fmt(a.backlinks), refDomainsFmt: this.fmt(a.refDomains), dofollowPct: a.dofollowPct }));

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

