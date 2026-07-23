    /* ============ OFF-SITE SEO ============ */
    if (tab === 'offsite') {
      vals.showOffsite = true;
      const t = data.totals, pv = data.prev;
      const pctD = (a, b) => (b ? Math.round(((a - b) / b) * 100) : null);
      const chip = d => {
        if (d == null || !isFinite(d)) return { has: false, label: '', style: {} };
        const good = d >= 0;
        return { has: true, label: (d > 0 ? '+' : '') + d + '%', style: { fontSize: '11px', fontWeight: 600, padding: '2px 6px', borderRadius: '4px', color: good ? '#059669' : '#e11d48', background: good ? '#ecfdf5' : '#fff1f2' } };
      };
      const kpiCard = (label, value, c, note) => ({ label, value, hasChip: c.has, chipLabel: c.label, chipStyle: c.style, note });
      const off = {};
      const syncSetup = !data || !data.syncMeta || data.syncMeta.state === 'setup' || (data.totals && data.totals.sessions === 0 && (!data.referrers || !data.referrers.length));
      if (syncSetup) {
        vals.off = { setup: true };
        return vals;
      }
      off.cadence = data.syncMeta.cadence;
      off.tokens = (data.syncMeta.ga4_tokens_used + ' / ' + this.fmt(data.syncMeta.ga4_tokens_limit) + ' GA4 tokens');
      off.tokensEmpty = false;
      off.rangeLabel = s.range === '7d' ? 'last 7 days' : s.range === '90d' ? 'last 90 days' : 'last 30 days';
      off.kpis = [
        kpiCard('Off-site sessions', this.fmt(t.sessions), chip(pctD(t.sessions, pv.sessions)), 'vs. previous period'),
        kpiCard('Engagement rate', t.engagementRate + '%', chip(null), this.fmt(t.engagedSessions) + ' engaged'),
        kpiCard('Key events', this.fmt(Math.round(t.keyEvents)), chip(pctD(t.keyEvents, pv.keyEvents)), 'attributed conversions'),
        kpiCard('Attributed revenue', this.money(t.revenue), chip(pctD(t.revenue, pv.revenue)), 'GA4 totalRevenue'),
        kpiCard('Referring domains', String(t.referringDomains), chip(null), 'sites sending traffic')
      ];

      /* trend */
      const tr = data.trend, W = 600, H = 220, P = 8;
      const maxV = Math.max.apply(null, tr.map(d => d.sessions).concat([1]));
      const xs = i => (tr.length > 1 ? P + i * ((W - 2 * P) / (tr.length - 1)) : W / 2);
      const yOf = v => H - P - (v / maxV) * (H - 2 * P);
      const pts = k => tr.map((d, i) => xs(i).toFixed(1) + ',' + yOf(d[k]).toFixed(1)).join(' ');
      off.sessPts = pts('sessions');
      off.engPts = pts('engagedSessions');
      off.area = tr.length ? 'M' + xs(0).toFixed(1) + ',' + (H - P) + ' L' + off.sessPts.split(' ').join(' L') + ' L' + xs(tr.length - 1).toFixed(1) + ',' + (H - P) + ' Z' : '';
      off.trendStart = tr.length ? tr[0].date : '';
      off.trendEnd = tr.length ? tr[tr.length - 1].date : '';

      /* channel mix */
      const chMax = Math.max.apply(null, data.channels.map(c => c.sessions).concat([1]));
      const chTotal = data.channels.reduce((a, c) => a + c.sessions, 0) || 1;
      const chColors = { 'Organic Search': '#94a3b8', 'Direct': '#cbd5e1', 'Referral': '#4f46e5', 'Organic Social': '#0a66c2', 'Organic Video': '#dc2626', 'Email': '#a1a1aa' };
      off.channels = data.channels.map(c => {
        const col = chColors[c.channel] || '#94a3b8';
        return {
          channel: c.channel, sessFmt: this.fmt(c.sessions),
          pctLabel: Math.round(c.sessions / chTotal * 100) + '%',
          labelColor: c.offsite ? '#0f172a' : '#64748b', labelWeight: c.offsite ? 600 : 400,
          dotStyle: { width: '8px', height: '8px', borderRadius: '2px', background: col, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.max(2, Math.round(c.sessions / chMax * 100)) + '%', background: col, borderRadius: '9999px', opacity: c.offsite ? 1 : 0.5 }
        };
      });
      const offCh = data.channels.filter(c => c.offsite);
      const offSess = offCh.reduce((a, c) => a + c.sessions, 0);
      off.offShareLabel = Math.round(offSess / chTotal * 100) + '%';
      off.offKeyEvents = this.fmt(Math.round(offCh.reduce((a, c) => a + c.keyEvents, 0)));

      /* LinkedIn spotlight */
      const li = data.social.find(x => x.platform === 'LinkedIn') || { impressions: 0, sessions: 0, keyEvents: 0, revenue: 0 };
      const liConnected = !!(data.connectors && data.connectors.linkedin);
      off.li = {
        impressions: liConnected ? this.fmt(li.impressions || 0) : '—', sessions: this.fmt(li.sessions),
        ctr: liConnected && li.impressions ? +(li.sessions / li.impressions * 100).toFixed(1) + '%' : '—',
        keyEvents: this.fmt(Math.round(li.keyEvents)), revenue: this.money(li.revenue),
        connected: liConnected,
        badgeLabel: liConnected ? 'Connected' : 'Not connected',
        badgeStyle: liConnected
          ? { marginLeft: 'auto', fontSize: '10px', fontWeight: 600, color: '#059669', background: '#ecfdf5', padding: '3px 8px', borderRadius: '9999px' }
          : { marginLeft: 'auto', fontSize: '10px', fontWeight: 600, color: '#4f46e5', background: '#eef2ff', padding: '3px 8px', borderRadius: '9999px', cursor: 'pointer', textDecoration: 'underline' },
        subtitle: liConnected ? 'Connector live · impressions + click-throughs' : 'Connector not set up yet (click badge to connect in Settings)',
        imprCaption: liConnected ? 'from LinkedIn API' : 'connector needed'
      };

      /* social table */
      const socColors = { 'LinkedIn': '#0a66c2', 'Reddit': '#ff4500', 'YouTube': '#dc2626', 'X (Twitter)': '#0f172a', 'Facebook': '#1877f2', 'Instagram': '#c13584' };
      off.social = data.social.map(r => ({
        platform: r.platform, source: r.source, channel: r.channel,
        connected: r.connected, notConnected: !r.connected,
        imprFmt: r.connected && r.impressions != null ? this.fmt(r.impressions) : '—',
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents)), revFmt: this.money(r.revenue),
        badge: r.platform.slice(0, 1),
        badgeStyle: { width: '26px', height: '26px', borderRadius: '6px', background: socColors[r.platform] || '#64748b', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px', fontWeight: 700, flexShrink: 0 }
      }));

      /* referring domains (sortable) */
      const refRows = this.sortRows(data.referrers.slice(), s.offSort);
      off.sort = { sessions: this.mkSortHandler('offSort', 'sessions'), keyEvents: this.mkSortHandler('offSort', 'keyEvents'), revenue: this.mkSortHandler('offSort', 'revenue') };
      off.arrow = { sessions: this.arrow(s.offSort, 'sessions'), keyEvents: this.arrow(s.offSort, 'keyEvents'), revenue: this.arrow(s.offSort, 'revenue') };
      off.referrers = refRows.map(r => ({
        domain: r.domain, rank: r.rank, tracked: r.tracked, canTrack: !r.tracked,
        rankStyle: { fontWeight: 600, color: r.rank >= 70 ? '#059669' : r.rank >= 40 ? '#2563eb' : '#64748b' },
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents)), revFmt: this.money(r.revenue),
        href: 'https://' + r.domain,
        onTrack: () => this.notify('"' + r.domain + '" flagged — added to backlink tracking on next sync')
      }));

      /* landing pages */
      off.landing = data.landingPages.map(r => ({
        url: r.url, topSource: r.topSource,
        sessFmt: this.fmt(r.sessions), engFmt: Math.round(r.engagedRate * 100) + '%',
        keyFmt: this.fmt(Math.round(r.keyEvents))
      }));

      vals.off = off;
    }

