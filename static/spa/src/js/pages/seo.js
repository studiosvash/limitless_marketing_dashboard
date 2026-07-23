    /* ============ SEO ============ */
    if (tab === 'seo') {
      vals.showSeo = true;
      vals.seo = {
        lowCtrCount: data.kpis.low_ctr, anomalyCount: data.kpis.anomalies,
        criticalCount: data.kpis.critical, quickWins: data.quickWinKws,
        lowCtrRows: data.lowCtrPages.map(r => ({ url: r.url, imprFmt: this.fmt(r.impressions), clicks: r.clicks, ctrFmt: r.ctr + '%', avgPos: r.avg_pos })),
        countries: data.countries.map(c => ({ country: c.country, clicksFmt: this.fmt(c.clicks), ctrFmt: c.ctr + '%' })),
        anomalies: data.anomalies.map(a => ({
          metric: a.metric, severity: a.severity, date: a.date,
          deviation: a.deviation || '—',
          sevStyle: this.sevChip(a.severity),
          devStyle: { color: String(a.deviation).indexOf('-') === 0 || String(a.deviation).indexOf('−') === 0 ? '#dc2626' : '#059669', fontWeight: 500 }
        }))
      };
    }

