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
      vals.ov = {
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
            arrowStyle: { color: '#cbd5e1', fontSize: '14px', lineHeight: 1 }
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
          onClick: () => this.go(m.target)
        })),
        clickPts: this.linePts(data.trend, 'clicks', 600, 220),
        imprPts: this.linePts(data.trend, 'impressions', 600, 220),
        maxClicks: this.fmt(Math.max.apply(null, data.trend.map(d => d.clicks))),
        dateFrom: data.trend[0] ? data.trend[0].date : '', dateTo: data.trend.length ? data.trend[data.trend.length - 1].date : '',
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
        topPages: data.topPages.map(r => ({ url: r.url, clicksFmt: this.fmt(r.clicks), imprFmt: this.fmt(r.impressions), ctrFmt: r.ctr + '%' }))
      };
    }

