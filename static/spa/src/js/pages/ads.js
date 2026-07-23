    /* ============ ADS SUITE (Paid Overview / Campaigns / Terms / Attribution) ============ */
    if (this.ADSTABS.includes(tab)) {
      const t = data.totals, pv = data.prev, cs = data.campaigns;
      const pctD = (a, b) => (b ? Math.round(((a - b) / b) * 100) : null);
      const chip = (d, invert) => {
        if (d == null || !isFinite(d)) return { label: '', style: {} };
        const good = invert ? d <= 0 : d >= 0;
        return { label: (d > 0 ? '+' : '') + d + '%', style: { fontSize: '11px', fontWeight: 600, color: good ? '#059669' : '#dc2626' } };
      };
      const platformChip = pl => ({
        fontSize: '10px', fontWeight: 500, whiteSpace: 'nowrap', padding: '1px 8px', borderRadius: '4px',
        background: pl === 'Meta' ? '#eef2ff' : '#eff6ff', color: pl === 'Meta' ? '#4f46e5' : '#2563eb',
        border: '1px solid ' + (pl === 'Meta' ? '#c7d2fe' : '#bfdbfe')
      });
      const roasSt = v => ({ fontWeight: 600, color: v >= 3 ? '#059669' : v >= 1.5 ? '#2563eb' : '#dc2626' });
      const fBase = { padding: '4px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
      const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
      const fmtTs = z => z ? new Date(z).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—';
      const sm = data.syncMeta || {};
      const adsSetup = !data || !sm || !sm.connected || sm.state === 'setup' || (data.totals && data.totals.spend === 0 && (!data.campaigns || !data.campaigns.length));
      vals.adsSync = {
        cadence: sm.connected ? sm.cadence : 'not yet connected',
        last: fmtTs(sm.last_pull), next: fmtTs(sm.next_pull),
        quota: sm.ops_used + ' / ' + this.fmt(sm.ops_limit) + ' ops today',
        ga4: sm.ga4_tokens_used + ' / ' + this.fmt(sm.ga4_tokens_limit) + ' tokens',
        dotStyle: { width: '7px', height: '7px', borderRadius: '9999px', background: sm.connected ? '#10b981' : '#cbd5e1' }
      };
      const fmtD = z => new Date(z + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      vals.adsWindow = data.window && data.window.from ? (fmtD(data.window.from) + ' – ' + fmtD(data.window.to) + ' · ' + data.window.days + ' days') : '';
      const wastedTerms = data.searchTerms.filter(x => x.status === 'wasted');
      const wasted = wastedTerms.reduce((s2, x2) => s2 + x2.cost, 0);

      /* ---- Paid Overview ---- */
      if (tab === 'ads') {
        vals.showAds = true;
        if (adsSetup) {
          vals.ads = { setup: true };
          return vals;
        }
        const cpa = t.conversions ? t.spend / t.conversions : 0;
        const pCpa = pv.conversions ? pv.spend / pv.conversions : 0;
        const kpi = (label, value, c, note) => ({ label, value, chipLabel: c.label, chipStyle: c.style, note: note || '' });
        const noChip = { label: '', style: {} };
        vals.ads = {
          kpis: [
            kpi('Spend', this.money(t.spend), chip(pctD(t.spend, pv.spend), true), 'vs. previous period'),
            kpi('Conversions', String(Math.round(t.conversions)), chip(pctD(t.conversions, pv.conversions)), 'Google Ads + Meta'),
            kpi('CPA', this.money(cpa), chip(pCpa ? Math.round((cpa - pCpa) / pCpa * 100) : null, true), 'cost / conversion'),
            kpi('ROAS', t.roas.toFixed(2) + 'x', noChip, this.money(t.conv_value) + ' conv. value'),
            kpi('Avg CPC', this.money(t.cpc), noChip, this.fmt(t.clicks) + ' clicks'),
            kpi('GA4 key events', String(Math.round(t.ga4_key_events)), noChip, 'GA4 attribution')
          ]
        };
        const tr = data.trend;
        const W = 600, H = 220, P = 8;
        const maxSp = Math.max.apply(null, tr.map(d => d.spend).concat([1]));
        const maxCv = Math.max.apply(null, tr.map(d => Math.max(d.conversions, d.ga4_key_events)).concat([1]));
        const xs = i => (tr.length > 1 ? P + i * ((W - 2 * P) / (tr.length - 1)) : W / 2);
        const yOf = (v, max) => H - P - (v / max) * (H - 2 * P);
        const pts = (k, max) => tr.map((d, i) => xs(i).toFixed(1) + ',' + yOf(d[k], max).toFixed(1)).join(' ');
        vals.ads.spendPts = pts('spend', maxSp);
        vals.ads.convPts = pts('conversions', maxCv);
        vals.ads.ga4Pts = pts('ga4_key_events', maxCv);
        vals.ads.spendArea = tr.length ? 'M' + xs(0).toFixed(1) + ',' + (H - P) + ' L' + vals.ads.spendPts.split(' ').join(' L') + ' L' + xs(tr.length - 1).toFixed(1) + ',' + (H - P) + ' Z' : '';
        vals.ads.trendStart = tr.length ? tr[0].date : '';
        vals.ads.trendEnd = tr.length ? tr[tr.length - 1].date : '';
        vals.ads.trendRangeLabel = s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days';
        const pc = data.pacing;
        const over = pc.projected > pc.monthly_budget * 1.05, under = pc.projected < pc.monthly_budget * 0.8;
        vals.ads.pacing = {
          budget: this.money(pc.monthly_budget), mtd: this.money(pc.mtd_spend), projected: this.money(pc.projected),
          dayLabel: 'day ' + pc.day_of_month + ' of ' + pc.days_in_month,
          statusLabel: over ? 'Over pace' : under ? 'Under pace' : 'On pace',
          statusStyle: { fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '4px', background: over ? '#fee2e2' : under ? '#fef9c3' : '#ecfdf5', color: over ? '#b91c1c' : under ? '#a16207' : '#059669' },
          barStyle: { height: '100%', width: pc.pct + '%', background: over ? '#dc2626' : '#4f46e5', borderRadius: '9999px', transition: 'width 0.3s ease' },
          channels: pc.channels.map(c => ({
            platform: c.platform, mtdFmt: this.money(c.mtd), budgetFmt: this.money(c.budget),
            barStyle: { height: '100%', width: c.pct + '%', background: c.platform === 'Meta' ? '#818cf8' : '#4f46e5', borderRadius: '9999px' }
          }))
        };
        const attn = [];
        cs.filter(c => c.status === 'enabled' && c.lost_is_budget >= 15).forEach(c => attn.push({
          sev: 'medium', title: '"' + c.name + '" is limited by budget',
          detail: 'Losing ' + c.lost_is_budget + '% of impression share to budget in this period.',
          action: 'Adjust budget', go: () => this.go('campaigns')
        }));
        cs.filter(c => c.status === 'enabled' && c.cpa && c.prev.conversions > 0.5).forEach(c => {
          const p2 = c.prev.spend / c.prev.conversions;
          if (p2 > 0 && c.cpa > p2 * 1.3) attn.push({
            sev: 'high', title: 'CPA up ' + Math.round((c.cpa / p2 - 1) * 100) + '% on "' + c.name + '"',
            detail: this.money(c.cpa) + ' now vs. ' + this.money(p2) + ' in the previous period.',
            action: 'Review campaign', go: () => this.go('campaigns')
          });
        });
        if (wastedTerms.length) attn.push({
          sev: 'medium', title: this.money(wasted) + ' spent on zero-conversion search terms',
          detail: wastedTerms.length + ' term' + (wastedTerms.length === 1 ? '' : 's') + ' with clicks but no conversions in this period.',
          action: 'Review terms', go: () => this.go('terms')
        });
        vals.ads.attention = attn.slice(0, 4).map(x2 => Object.assign({}, x2, { sevLabel: x2.sev, sevStyle: this.sevChip(x2.sev) }));
        vals.ads.attEmpty = attn.length === 0;
      }

      /* ---- Campaigns ---- */
      if (tab === 'campaigns') {
        vals.showCampaigns = true;
        if (adsSetup) {
          vals.cmp = { setup: true };
          return vals;
        }
        let rows = cs.slice();
        if (s.cmpFilter === 'google') rows = rows.filter(c => c.platform === 'Google Ads');
        if (s.cmpFilter === 'meta') rows = rows.filter(c => c.platform === 'Meta');
        if (s.cmpFilter === 'paused') rows = rows.filter(c => c.status === 'paused');
        if (s.cmpSearch.trim()) rows = rows.filter(c => c.name.toLowerCase().includes(s.cmpSearch.trim().toLowerCase()));
        if (s.cmpSort && s.cmpSort.key) rows = this.sortRows(rows, s.cmpSort);
        const totC = rows.reduce((o, c) => ({ spend: o.spend + c.spend, clicks: o.clicks + c.clicks, impressions: o.impressions + c.impressions, conversions: o.conversions + c.conversions, conv_value: o.conv_value + c.conv_value, budget: o.budget + (c.status === 'enabled' ? c.budget_daily : 0) }), { spend: 0, clicks: 0, impressions: 0, conversions: 0, conv_value: 0, budget: 0 });
        vals.cmp = {
          count: rows.length + ' of ' + cs.length + ' campaigns',
          notEmpty: rows.length > 0,
          totLabel: rows.length + ' campaign' + (rows.length === 1 ? '' : 's'),
          totBudget: this.money(totC.budget) + '/day active',
          totSpend: this.money(totC.spend),
          totClicks: this.fmt(totC.clicks),
          totCtr: totC.impressions ? (totC.clicks / totC.impressions * 100).toFixed(2) + '%' : '—',
          totCpc: totC.clicks ? this.money(totC.spend / totC.clicks) : '—',
          totConv: String(Math.round(totC.conversions)),
          totCpa: totC.conversions ? this.money(totC.spend / totC.conversions) : '—',
          totRoas: totC.spend ? (totC.conv_value / totC.spend).toFixed(2) + 'x' : '—',
          search: s.cmpSearch,
          filters: [['all', 'All'], ['google', 'Google Ads'], ['meta', 'Meta'], ['paused', 'Paused']].map(f => ({
            label: f[1], style: s.cmpFilter === f[0] ? fActive : fBase,
            click: () => this.setState({ cmpFilter: f[0] })
          })),
          empty: rows.length === 0,
          rows: rows.map(c => {
            const on = c.status === 'enabled';
            const editing = s.editBudgetId === c.id;
            const open = s.cmpOpenId === c.id;
            return {
              name: c.name, typeLabel: c.type, platform: c.platform, platformStyle: platformChip(c.platform),
              statusLabel: on ? 'Active' : 'Paused',
              statusTextStyle: { fontSize: '11px', fontWeight: 600, color: on ? '#059669' : '#94a3b8', width: '44px', flexShrink: 0 },
              track: { width: '36px', height: '20px', borderRadius: '9999px', background: on ? '#4f46e5' : '#cbd5e1', position: 'relative', cursor: 'pointer', transition: 'background 0.15s ease', flexShrink: 0 },
              knob: { position: 'absolute', top: '2px', left: on ? '18px' : '2px', width: '16px', height: '16px', borderRadius: '9999px', background: 'white', transition: 'left 0.15s ease' },
              onToggle: () => this.setCampaignStatus(c),
              toggleAria: (on ? 'Pause' : 'Enable') + ' ' + c.name,
              nameColor: on ? '#334155' : '#94a3b8',
              editing, notEditing: !editing,
              budgetFmt: this.money(c.budget_daily),
              budgetVal: s.editBudgetVal,
              onBudgetClick: () => this.setState({ editBudgetId: c.id, editBudgetVal: String(c.budget_daily) }),
              onBudgetInput: e => this.setState({ editBudgetVal: e.target.value }),
              onBudgetKey: e => { if (e.key === 'Enter') this.saveBudget(c); if (e.key === 'Escape') this.setState({ editBudgetId: null }); },
              onBudgetBlur: () => { if (this.state.editBudgetId === c.id) this.saveBudget(c); },
              spendFmt: this.money(c.spend), imprFmt: this.fmt(c.impressions), clicksFmt: this.fmt(c.clicks),
              ctrFmt: c.ctr + '%', cpcFmt: this.money(c.cpc),
              convFmt: String(Math.round(c.conversions)), cpaFmt: c.cpa != null ? this.money(c.cpa) : '—',
              roasFmt: c.roas.toFixed(2) + 'x', roasStyle: roasSt(c.roas),
              isLabel: c.lost_is_budget ? c.lost_is_budget + '%' : '—',
              isStyle: { fontSize: '12.5px', fontWeight: 600, color: c.lost_is_budget >= 15 ? '#b45309' : '#94a3b8' },
              open,
              onOpen: () => this.setState(st2 => ({ cmpOpenId: st2.cmpOpenId === c.id ? null : c.id })),
              openAria: (open ? 'Collapse' : 'Expand') + ' ' + c.name,
              chevStyle: { display: 'inline-flex', color: '#94a3b8', cursor: 'pointer', padding: '6px', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s ease' },
              groupsLabel: (c.type === 'Performance Max' ? 'Asset groups' : c.platform === 'Meta' ? 'Ad sets' : 'Ad groups'),
              hasTerms: c.platform === 'Google Ads',
              onViewTerms: () => { this.setState({ termCampaign: c.id, termFilter: 'all' }); this.go('terms'); },
              adGroups: c.adGroups.map(g => ({
                name: g.name, spendFmt: this.money(g.spend), clicksFmt: this.fmt(g.clicks) + ' clicks',
                convFmt: Math.round(g.conversions) + ' conv.', cpaFmt: g.cpa != null ? this.money(g.cpa) + ' CPA' : '— CPA'
              }))
            };
          })
        };
      }

      /* ---- Search Terms ---- */
      if (tab === 'terms') {
        vals.showTerms = true;
        if (adsSetup) {
          vals.trm = { setup: true };
          return vals;
        }
        const scopeCmp = s.termCampaign ? cs.find(c2 => c2.id === s.termCampaign) : null;
        const all = scopeCmp ? data.searchTerms.filter(x2 => x2.campaignId === scopeCmp.id) : data.searchTerms;
        const counts = {
          all: all.length,
          converting: all.filter(x2 => x2.status === 'converting').length,
          wasted: all.filter(x2 => x2.status === 'wasted').length,
          managed: all.filter(x2 => x2.status === 'negative' || x2.status === 'tracked').length
        };
        let rows = all;
        if (s.termFilter === 'converting') rows = all.filter(x2 => x2.status === 'converting');
        if (s.termFilter === 'wasted') rows = all.filter(x2 => x2.status === 'wasted');
        if (s.termFilter === 'managed') rows = all.filter(x2 => x2.status === 'negative' || x2.status === 'tracked');
        if (s.trmMatch !== 'all') rows = rows.filter(x2 => x2.matchType === s.trmMatch);
        if (s.trmSearch.trim()) {
          const q2 = s.trmSearch.trim().toLowerCase();
          rows = rows.filter(x2 => x2.term.toLowerCase().includes(q2) || x2.matchedKeyword.toLowerCase().includes(q2));
        }
        rows = this.sortRows(rows, s.trmSort);
        const totT = rows.reduce((o, x2) => ({ impressions: o.impressions + x2.impressions, clicks: o.clicks + x2.clicks, cost: o.cost + x2.cost, conversions: o.conversions + x2.conversions }), { impressions: 0, clicks: 0, cost: 0, conversions: 0 });
        const per = s.trmPer;
        const pageMax = Math.max(0, Math.ceil(rows.length / per) - 1);
        const page = Math.min(s.trmPage, pageMax);
        const pageRows = rows.slice(page * per, (page + 1) * per);
        const selSet = new Set(s.trmSel);
        const actionableFn = x2 => x2.status === 'converting' || x2.status === 'wasted';
        const selRows = rows.filter(x2 => selSet.has(x2.id) && actionableFn(x2));
        const pageIds = pageRows.filter(actionableFn).map(x2 => x2.id);
        const allChecked = pageIds.length > 0 && pageIds.every(i2 => selSet.has(i2));
        const ck = on => ({ width: '15px', height: '15px', borderRadius: '4px', border: '1.5px solid ' + (on ? '#4f46e5' : '#cbd5e1'), background: on ? '#4f46e5' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 });
        const navBtn = en => ({ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '26px', height: '26px', border: '1px solid #e2e8f0', borderRadius: '7px', cursor: en ? 'pointer' : 'default', color: en ? '#334155' : '#cbd5e1', background: 'white' });
        const mtTitle = {
          exact: 'Exact match — the query matched this keyword exactly',
          phrase: 'Phrase match — the query contained this keyword phrase',
          broad: 'Broad match — the query was semantically related to this keyword'
        };
        const stChipMap = {
          converting: { label: 'Converting', bg: '#ecfdf5', fg: '#059669' },
          wasted: { label: 'No conversions', bg: '#fef2f2', fg: '#b91c1c' },
          negative: { label: 'Negative added', bg: '#f1f5f9', fg: '#64748b' },
          tracked: { label: 'Tracking as keyword', bg: '#eef2ff', fg: '#4338ca' }
        };
        vals.trm = {
          kpis: [
            { label: 'Term spend', value: this.money(all.reduce((s2, x2) => s2 + x2.cost, 0)), note: all.length + ' terms in period' },
            { label: 'Wasted spend', value: this.money(wasted), note: counts.wasted + ' zero-conversion terms', accent: '#b91c1c' },
            { label: 'Converting terms', value: String(counts.converting), note: 'clicks that became conversions', accent: '#059669' },
            { label: 'Negatives added', value: String(data.negatives.length), note: 'written back on next sync' }
          ].map(k => ({ label: k.label, value: k.value, note: k.note, valueStyle: { fontSize: '24px', fontWeight: 700, color: k.accent || '#0f172a' } })),
          filters: [['all', 'All'], ['converting', 'Converting'], ['wasted', 'Wasted spend'], ['managed', 'Managed']].map(f => ({
            label: f[1] + ' (' + counts[f[0]] + ')',
            style: s.termFilter === f[0] ? fActive : fBase,
            click: () => this.setState({ termFilter: f[0], trmPage: 0 })
          })),
          scoped: !!scopeCmp,
          scopeLabel: scopeCmp ? 'Campaign: ' + scopeCmp.name : '',
          clearScope: () => this.setState({ termCampaign: null, trmPage: 0 }),
          search: s.trmSearch,
          onSearch: e => this.setState({ trmSearch: e.target.value, trmPage: 0 }),
          match: s.trmMatch,
          onMatch: e => this.setState({ trmMatch: e.target.value, trmPage: 0 }),
          countLine: rows.length ? ('Showing ' + (page * per + 1) + '–' + Math.min(rows.length, (page + 1) * per) + ' of ' + rows.length + ' term' + (rows.length === 1 ? '' : 's') + (rows.length === all.length ? '' : ' (' + all.length + ' total)')) : 'No matching terms',
          empty: rows.length === 0,
          notEmpty: rows.length > 0,
          totLabel: rows.length + ' term' + (rows.length === 1 ? '' : 's'),
          totImpr: this.fmt(totT.impressions), totClicks: this.fmt(totT.clicks), totCost: this.money(totT.cost),
          totConv: String(Math.round(totT.conversions)),
          totCpa: totT.conversions ? this.money(totT.cost / totT.conversions) : '—',
          hasSel: selRows.length > 0, selCount: selRows.length,
          bulkNeg: () => this.bulkNegatives(selRows, 'phrase'),
          bulkTrack: () => this.bulkPromote(selRows),
          clearSel: () => this.setState({ trmSel: [] }),
          allChecked, allCheckStyle: ck(allChecked),
          toggleAll: () => this.setState(st2 => {
            const cur = new Set(st2.trmSel);
            if (allChecked) pageIds.forEach(i2 => cur.delete(i2)); else pageIds.forEach(i2 => cur.add(i2));
            return { trmSel: Array.from(cur) };
          }),
          per: String(per),
          onPer: e => this.setState({ trmPer: +e.target.value, trmPage: 0 }),
          pageLabel: (page + 1) + ' of ' + (pageMax + 1),
          prevPage: () => { if (page > 0) this.setState({ trmPage: page - 1 }); },
          nextPage: () => { if (page < pageMax) this.setState({ trmPage: page + 1 }); },
          prevStyle: navBtn(page > 0), nextStyle: navBtn(page < pageMax),
          rows: pageRows.map(t2 => {
            const c2 = stChipMap[t2.status] || stChipMap.wasted;
            const canSel = actionableFn(t2);
            const checked = canSel && selSet.has(t2.id);
            return {
              term: t2.term, matched: t2.matchedKeyword, campaign: t2.campaign,
              matchLabel: t2.matchType,
              matchTitle: mtTitle[t2.matchType] || '',
              matchStyle: { fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: '4px', cursor: 'help' },
              imprFmt: this.fmt(t2.impressions), clicksFmt: this.fmt(t2.clicks), costFmt: this.money(t2.cost),
              convFmt: t2.conversions ? String(t2.conversions) : '0',
              cpaFmt: t2.cpa != null ? this.money(t2.cpa) : '—',
              statusLabel: c2.label,
              statusStyle: { fontSize: '10.5px', fontWeight: 600, background: c2.bg, color: c2.fg, padding: '2px 8px', borderRadius: '4px', whiteSpace: 'nowrap' },
              actionable: canSel, canSel,
              checked, checkStyle: ck(checked),
              selAria: (checked ? 'Deselect ' : 'Select ') + t2.term,
              onSel: () => this.setState(st2 => { const cur = new Set(st2.trmSel); if (cur.has(t2.id)) cur.delete(t2.id); else cur.add(t2.id); return { trmSel: Array.from(cur) }; }),
              negOpen: s.negMenuFor === t2.id,
              onNegMenu: () => this.setState(st2 => ({ negMenuFor: st2.negMenuFor === t2.id ? null : t2.id })),
              negPhrase: () => this.addNegative(t2, 'phrase'),
              negExact: () => this.addNegative(t2, 'exact'),
              negBroad: () => this.addNegative(t2, 'broad'),
              onTrack: () => this.promoteTerm(t2),
              onCampaign: () => { this.setState({ cmpSearch: t2.campaign, cmpFilter: 'all', cmpOpenId: t2.campaignId }); this.go('campaigns'); },
              negAria: 'Add ' + t2.term + ' as negative keyword',
              trackAria: 'Track ' + t2.term + ' as organic keyword'
            };
          })
        };
      }

      /* ---- Attribution ---- */
      if (tab === 'attribution') {
        vals.showAttribution = true;
        if (adsSetup) {
          vals.att = { setup: true };
          return vals;
        }
        const rowsA = data.attribution;
        const maxConv = Math.max.apply(null, rowsA.map(r2 => Math.max(r2.ads_conversions, r2.ga4_key_events)).concat([1]));
        vals.att = {
          totals: {
            ads: String(Math.round(t.conversions)), ga4: String(Math.round(t.ga4_key_events)),
            adsVal: this.money(t.conv_value), ga4Val: this.money(t.ga4_revenue),
            gap: (t.conversions ? Math.round((t.ga4_key_events - t.conversions) / t.conversions * 100) : 0) + '%'
          },
          rows: rowsA.map(r2 => ({
            name: r2.name, platform: r2.platform, platformStyle: platformChip(r2.platform),
            onCampaign: () => { this.setState({ cmpSearch: r2.name, cmpFilter: 'all', cmpOpenId: r2.id }); this.go('campaigns'); },
            ads: String(Math.round(r2.ads_conversions)), ga4: String(Math.round(r2.ga4_key_events)),
            adsBar: { height: '6px', borderRadius: '9999px', background: '#4f46e5', width: Math.max(2, Math.round(r2.ads_conversions / maxConv * 100)) + '%' },
            ga4Bar: { height: '6px', borderRadius: '9999px', background: '#10b981', width: Math.max(2, Math.round(r2.ga4_key_events / maxConv * 100)) + '%' },
            adsVal: this.money(r2.ads_value), ga4Val: this.money(r2.ga4_revenue),
            gapLabel: (r2.gap_pct > 0 ? '+' : '') + r2.gap_pct + '%',
            gapStyle: { fontSize: '11.5px', fontWeight: 600, color: Math.abs(r2.gap_pct) <= 25 ? '#64748b' : '#b45309' }
          })),
          pages: data.landingPages.map(lp => ({
            url: lp.url, campaign: lp.campaign,
            sessions: this.fmt(lp.sessions),
            erLabel: Math.round(lp.engagedRate * 100) + '%',
            erBar: { height: '5px', borderRadius: '9999px', background: lp.engagedRate >= 0.5 ? '#10b981' : lp.engagedRate >= 0.35 ? '#f59e0b' : '#dc2626', width: Math.round(lp.engagedRate * 100) + '%' },
            keyEvents: String(lp.keyEvents), revenue: this.money(lp.revenue)
          }))
        };
      }
    }

