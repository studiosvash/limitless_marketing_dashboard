    /* ============ SEO ============ */
    if (tab === 'seo') {
      vals.showSeo = true;
      /* Provenance. Low-CTR pages, country and device splits are all seo_daily -- GSC's
         Search Analytics report. Anomalies are DERIVED from that same table by
         anomaly_service during post-sync, so they inherit GSC's freshness rather than having
         a connector of their own. Technical issues are a different lineage: DataForSEO OnPage
         plus rows technical_issues_service derives from GSC/Lighthouse data. */
      const GSC_SRC = ['gsc'];
      vals.seo = {
        srcLowCtr: this.srcBadge(GSC_SRC),
        srcCountries: this.srcBadge(GSC_SRC),
        srcDevices: this.srcBadge(GSC_SRC),
        srcAnomalies: this.srcBadge(GSC_SRC, 'Anomalies are computed from the GSC data after each sync, so they are exactly as fresh as it is.'),
        srcIssues: this.srcBadge(['dataforseo_onpage', 'url_inspection', 'pagespeed']),
        lowCtrCount: data.kpis.low_ctr, anomalyCount: data.kpis.anomalies,
        criticalCount: data.kpis.critical, quickWins: data.quickWinKws,
        lowCtrRows: data.lowCtrPages.map(r => ({ url: r.url, imprFmt: this.fmt(r.impressions), clicks: r.clicks, ctrFmt: r.ctr + '%', avgPos: r.avg_pos })),
        countries: data.countries.map(c => ({ country: c.country, clicksFmt: this.fmt(c.clicks), ctrFmt: c.ctr + '%' })),
        // GSC hands us 'desktop'/'mobile'/'tablet' lowercase — title-case here, never in the template.
        hasDevices: (data.devices || []).length > 0,
        devices: (data.devices || []).map(d => {
          const name = String(d.device || '');
          return {
            device: name ? name.charAt(0).toUpperCase() + name.slice(1) : 'Unknown',
            clicksFmt: this.fmt(d.clicks), imprFmt: this.fmt(d.impressions), ctrFmt: d.ctr + '%'
          };
        }),
        hasIssues: (data.issues || []).length > 0,
        issues: (data.issues || []).map(i => ({
          label: i.label, severity: i.severity, sevStyle: this.sevChip(i.severity),
          pagesFmt: this.fmt(i.pages),
          url: i.example_url || '',
          urlShort: String(i.example_url || '').split('//').pop().slice(0, 55) || '—',
          description: i.description || '—'
        })),
        anomalies: data.anomalies.map(a => ({
          metric: a.metric, severity: a.severity, date: a.date,
          deviation: a.deviation || '—',
          sevStyle: this.sevChip(a.severity),
          devStyle: { color: String(a.deviation).indexOf('-') === 0 || String(a.deviation).indexOf('−') === 0 ? '#dc2626' : '#059669', fontWeight: 500 }
        }))
      };
    }

