    /* ============ DOMAIN OVERVIEW ============ */
    if (tab === 'domain_overview') {
      vals.showDomainOverview = true;
      vals.do = {
        query: s.doQuery || '',
        data: s.doData || null,
        loading: s.doLoading || false,
        error: s.doError || null
      };
      
      if (s.doData && s.doData.status === 'ok') {
        const metrics = s.doData.metrics || {};
        vals.do.metrics = {
          organicTraffic: this.fmt(metrics.organic_traffic || 0),
          trafficValue: this.money(metrics.traffic_value || 0),
          rankedKeywords: this.fmt(metrics.ranked_keywords || 0)
        };
        
        vals.do.rows = (s.doData.keywords || []).map(k => {
          const iv = this.intentView(k.intent);
          return {
            kw: k.keyword,
            url: k.url,
            intentLabel: iv.label,
            intentStyle: iv.style,
            posText: k.position,
            posStyle: this.posBadge(k.position),
            volFmt: this.fmt(k.volume),
            cpcFmt: this.money(k.cpc),
            trafficFmt: this.fmt(k.traffic)
          };
        });
      }
    }
