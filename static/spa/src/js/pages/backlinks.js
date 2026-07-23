    /* ============ BACKLINKS ============ */
    if (tab === 'backlinks') {
      vals.showBacklinks = true;
      const sum = data.summary;
      const setup = !data || !sum || sum.state === 'setup' || (sum.backlinks === 0 && (!data.links || !data.links.length));

      if (setup) {
        vals.bl = {
          setup: true,
          tabs: [], isOverview: false, isLinks: false, isRefDom: false, isAnchors: false, isGap: false,
          lastUpdated: '', chartBars: [], chartLabels: [], typeArcs: [], typeLegend: [],
          asBuckets: [], topAnchors: [], topRefDomains: [], allRefDomains: [],
          rows: [], statusFilters: [], followFilters: [], allAnchors: [],
          gapCols: [], gapRows: [], gapOnly: false,
          gapBtnBorder: '#e2e8f0', gapBtnBg: 'white', gapBtnColor: '#64748b'
        };
        return vals;
      }

      const links = data.links;
      const asColorOf = as => as >= 60 ? '#059669' : as >= 40 ? '#0891b2' : as >= 20 ? '#d97706' : '#94a3b8';
      const asBgOf = as => as >= 60 ? '#ecfdf5' : as >= 40 ? '#ecfeff' : as >= 20 ? '#fffbeb' : '#f1f5f9';
      const spamColorOf = sp => sp >= 30 ? '#dc2626' : sp >= 10 ? '#d97706' : '#059669';
      const asChip = as => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', minWidth: '26px', padding: '2px 6px', borderRadius: '5px', fontSize: '12px', fontWeight: 600, color: asColorOf(as), background: asBgOf(as) });
      const shortN = n => n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + 'K' : ('' + n);

      const bl = {};
      bl.lastUpdated = sum.lastUpdated;
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
      bl.asDash = (sum.authorityScore / 100 * 188.5).toFixed(1) + ' 188.5'; bl.asDelta = sum.asDelta;
      bl.refDomainsFmt = this.fmt(sum.refDomains); bl.newRdMonth = sum.newRdMonth;
      bl.backlinksFmt = this.fmt(sum.backlinks); bl.backlinksShort = shortN(sum.backlinks);
      bl.dofollowPct = sum.dofollowPct; bl.brokenFmt = this.fmt(sum.broken);
      bl.spamScore = sum.spamScore; bl.spamColor = spamColorOf(sum.spamScore);

      // new/lost chart
      const months = data.months;
      const maxMonth = Math.max(...months.map(m => Math.max(m.nw, m.lost)));
      const barW = 640 / months.length;
      bl.chartBars = months.map((m, i) => ({ x: (i * barW + 2).toFixed(1), w: (barW - 4).toFixed(1), newH: ((m.nw / maxMonth) * 82).toFixed(1), newY: (90 - (m.nw / maxMonth) * 82).toFixed(1), lostH: ((m.lost / maxMonth) * 82).toFixed(1) }));
      bl.chartLabels = months.filter((m, i) => i % 4 === 0).map(m => m.label);

      // types donut
      let acc = 0;
      bl.typeArcs = data.types.map(t => { const arc = { color: t.color, dash: t.pct + ' ' + (100 - t.pct), offset: (100 - acc) % 100 }; acc += t.pct; return arc; });
      bl.typeLegend = data.types.map(t => ({ label: t.label, color: t.color, pct: t.pct }));

      // AS buckets
      const maxBucket = Math.max(...data.asBuckets.map(b => b.count));
      bl.asBuckets = data.asBuckets.map(b => ({ label: b.label, color: b.color, countFmt: this.fmt(b.count), pct: Math.round((b.count / maxBucket) * 100) }));

      // top anchors
      const maxAnchor = Math.max(...data.anchors.map(a => a.backlinks));
      bl.topAnchors = data.anchors.slice(0, 6).map(a => ({ anchor: a.anchor, pct: Math.round((a.backlinks / maxAnchor) * 100) }));

      // referring domains
      const refRow = x => ({ domain: x.domain, flag: x.flag, as: x.rank, asStyle: asChip(x.rank), backlinksFmt: this.fmt(x.backlinks), linksToUs: x.linksToUs, follow: x.follow ? 'Dofollow' : 'Nofollow', followColor: x.follow ? '#059669' : '#94a3b8', firstSeen: x.firstSeen, isNew: x.isNew, category: x.category });
      bl.topRefDomains = data.refDomains.slice(0, 8).map(refRow);
      bl.allRefDomains = data.refDomains.map(refRow);

      // backlinks table (derived from referring domains, deterministic)
      const paths = ['/blog/top-providers', '/reviews/best-services', '/guides/pricing', '/news/industry-2026', '/resources/how-it-works', '/directory/listings'];
      const titles = ['Top Providers in 2026', 'Best Services Reviewed', 'Complete Pricing Guide', 'Industry Trends 2026', 'How It Works, Explained', 'Local Directory Listing'];
      const statusPool = [];
      data.refDomains.forEach((rd, i) => {
        const cnt = 1 + (i % 3);
        for (let j = 0; j < cnt; j++) {
          const rr = this.blHash('blk:' + s.projectId + rd.domain + j);
          const anchorsL = [rd.domain.split('.')[0], (data.project ? '' : '') + 'services', project.domain, 'read the full review', 'here', 'learn more'];
          const dofollow = rr() > (1 - sum.dofollowPct / 100);
          const isNew = rr() > 0.8, isLost = !isNew && rr() > 0.9, isBroken = rr() > 0.94;
          statusPool.push({ domain: rd.domain, flag: rd.flag, pageTitle: titles[Math.floor(rr() * titles.length)], urlFrom: rd.domain + paths[Math.floor(rr() * paths.length)], anchor: anchorsL[Math.floor(rr() * anchorsL.length)], urlTo: project.domain + ['/', '/services', '/pricing', '/about'][Math.floor(rr() * 4)], domainRank: rd.rank, spam: rd.spam, dofollow, firstSeen: rd.firstSeen, isNew, isLost, isBroken });
        }
      });
      let blr = statusPool;
      if (s.blFilter === 'new') blr = blr.filter(x => x.isNew);
      else if (s.blFilter === 'lost') blr = blr.filter(x => x.isLost);
      else if (s.blFilter === 'broken') blr = blr.filter(x => x.isBroken);
      if (s.blFollow === 'dofollow') blr = blr.filter(x => x.dofollow);
      else if (s.blFollow === 'nofollow') blr = blr.filter(x => !x.dofollow);
      bl.rowCount = this.fmt(Math.min(blr.length, 60));
      bl.rows = blr.slice(0, 60).map(x => {
        const badges = [];
        if (x.isNew) badges.push({ label: 'NEW', color: '#059669', bg: '#ecfdf5' });
        if (x.isLost) badges.push({ label: 'LOST', color: '#dc2626', bg: '#fef2f2' });
        if (x.isBroken) badges.push({ label: 'BROKEN', color: '#b45309', bg: '#fffbeb' });
        return { flag: x.flag, pageTitle: x.pageTitle, urlFrom: x.urlFrom, anchor: x.anchor, urlTo: x.urlTo, domainRank: x.domainRank, asStyle: asChip(x.domainRank), spam: x.spam, spamColor: spamColorOf(x.spam), follow: x.dofollow ? 'Dofollow' : 'Nofollow', followColor: x.dofollow ? '#059669' : '#94a3b8', firstSeen: x.firstSeen, badges };
      });
      const mkF = (val, cur, key, label) => { const active = cur === val; return { label, click: () => { this.setState({ [key]: val }); this.pushNav(); }, style: { padding: '8px 14px', cursor: 'pointer', background: active ? '#eef2ff' : 'white', color: active ? '#4338ca' : '#64748b', fontWeight: active ? 600 : 400, borderLeft: '1px solid #e2e8f0' } }; };
      bl.statusFilters = [mkF('all', s.blFilter, 'blFilter', 'All'), mkF('new', s.blFilter, 'blFilter', 'New'), mkF('lost', s.blFilter, 'blFilter', 'Lost'), mkF('broken', s.blFilter, 'blFilter', 'Broken')];
      bl.statusFilters[0].style.borderLeft = 'none';
      bl.followFilters = [mkF('all', s.blFollow, 'blFollow', 'All links'), mkF('dofollow', s.blFollow, 'blFollow', 'Dofollow'), mkF('nofollow', s.blFollow, 'blFollow', 'Nofollow')];
      bl.followFilters[0].style.borderLeft = 'none';

      // anchors
      const typeColors = { Branded: ['#4338ca', '#eef2ff'], URL: ['#0891b2', '#ecfeff'], Keyword: ['#059669', '#ecfdf5'], Generic: ['#64748b', '#f1f5f9'], Empty: ['#94a3b8', '#f8fafc'] };
      bl.allAnchors = data.anchors.map(a => ({ anchor: a.anchor, type: a.type, typeColor: (typeColors[a.type] || typeColors.Generic)[0], typeBg: (typeColors[a.type] || typeColors.Generic)[1], backlinksFmt: this.fmt(a.backlinks), refDomainsFmt: this.fmt(a.refDomains), dofollowPct: a.dofollowPct }));

      // link gap
      const gapCols = [{ name: 'You', color: '#4f46e5' }, ...data.competitors.map(c => ({ name: c, color: '#64748b' }))];
      bl.gapCols = gapCols;
      let gapSource = data.gapDomains;
      if (s.gapOnly) gapSource = gapSource.filter(g => !g.you && g.comp.filter(Boolean).length >= 2);
      bl.gapRows = gapSource.slice().sort((a, b) => b.rank - a.rank).map(g => {
        const compCount = g.comp.filter(Boolean).length;
        const cells = [{ linked: g.you, missing: !g.you, color: '#4f46e5' }, ...g.comp.map(c => ({ linked: c, missing: !c, color: '#22c55e' }))];
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

