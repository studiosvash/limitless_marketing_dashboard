    /* ============ KEYWORDS ============ */
    if (tab === 'keywords') {
      vals.showKeywords = true;
      const segDefs = [
        { id: null, label: 'All', hint: null },
        { id: 'quick_wins', label: '⚡ Quick Wins', hint: 'These keywords rank #4–10 AND already get real clicks. A small push can move them into the top 3 — where CTR doubles.', action: 'Improve meta titles, add internal links, expand content depth.' },
        { id: 'striking', label: '🎯 Striking Distance', hint: 'Ranking #11–20 — page two. These are one content refresh away from page one.', action: 'Refresh content, add internal links from your top pages.' },
        { id: 'declining', label: '📉 Declining', hint: 'Dropped ≥2 positions since the last weekly sync.', action: 'Check SERP changes and competitor updates; consider a content refresh.' },
        { id: 'low_ctr', label: '👀 High Imp, Low CTR', hint: 'Seen often (≥100 impressions) but clicked under 2% of the time.', action: 'Rewrite title tags & meta descriptions.' }
      ];
      const counts = {
        null: data.keywords.length,
        quick_wins: data.segments.quick_wins.length, striking: data.segments.striking.length,
        declining: data.segments.declining.length, low_ctr: data.segments.low_ctr.length
      };
      const active = segDefs.find(d => d.id === s.kwSeg) || segDefs[0];
      const idSet = s.kwSeg ? new Set(data.segments[s.kwSeg]) : null;
      let rows = data.keywords.filter(k => !idSet || idSet.has(k.id));
      rows = this.sortRows(rows, s.kwSort);
      const tabBase = { padding: '14px 4px', borderBottom: '2px solid transparent', color: '#64748b', fontSize: '14px', cursor: 'pointer' };
      const tabActive = Object.assign({}, tabBase, { borderBottom: '2px solid #4f46e5', color: '#4f46e5', fontWeight: 500 });
      const intentTotal = Math.max(1, data.kpis.total);
      const intentDefs = [
        ['Informational', 'informational', '#3b82f6', '#dbeafe', '#2563eb', 'I'],
        ['Commercial', 'commercial', '#10b981', '#d1fae5', '#059669', 'C'],
        ['Transactional', 'transactional', '#f97316', '#ffedd5', '#ea580c', 'T'],
        ['Navigational', 'navigational', '#a855f7', '#f3e8ff', '#9333ea', 'N']
      ];
      const kdDefs = [
        ['Easy (0–29)', 'easy', '#10b981', '#d1fae5', '#059669', 'E', '#047857'],
        ['Medium (30–59)', 'medium', '#f59e0b', '#fef3c7', '#d97706', 'M', '#b45309'],
        ['Hard (60+)', 'hard', '#ef4444', '#fee2e2', '#dc2626', 'H', '#b91c1c']
      ];
      const kwSetup = !data || !data.kpis || data.kpis.state === 'setup' || (data.kpis.total === 0 && (!data.keywords || !data.keywords.length));
      if (kwSetup) {
        vals.kw = { setup: true, total: 0, avgPos: 0, totalVolume: 0, totalClicks: 0, intentRows: [], kdRows: [], tabs: [], rows: [] };
        return vals;
      }
      vals.kw = {
        total: data.kpis.total, avgPos: data.kpis.avg_pos,
        totalVolume: this.fmt(data.kpis.total_volume), totalClicks: this.fmt(data.kpis.total_clicks),
        intentRows: intentDefs.map(d => ({
          label: d[0], count: data.intents[d[1]],
          iconChar: d[5],
          iconStyle: { width: '20px', height: '20px', borderRadius: '4px', background: d[3], color: d[4], display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.round((data.intents[d[1]] / intentTotal) * 100) + '%', background: d[2] }
        })),
        kdRows: kdDefs.map(d => ({
          label: d[0], count: data.difficulty[d[1]],
          iconChar: d[5],
          iconStyle: { width: '20px', height: '20px', borderRadius: '4px', background: d[3], color: d[4], display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0 },
          barStyle: { height: '100%', width: Math.round((data.difficulty[d[1]] / intentTotal) * 100) + '%', background: d[2] },
          countStyle: { fontSize: '14px', fontWeight: 600, color: d[6], width: '32px', textAlign: 'right' }
        })),
        tabs: segDefs.map(d => ({
          label: d.label + ' (' + counts[d.id] + ')',
          style: d.id === s.kwSeg ? tabActive : tabBase,
          click: () => { this.setState({ kwSeg: d.id }); this.pushNav({ kwSeg: d.id }); }
        })),
        hasHint: !!active.hint, hintText: active.hint || '', hintAction: active.action || '',
        tableTitle: s.kwSeg ? active.label.replace(/^[^ ]+ /, '') + ' Keywords' : 'All Keywords',
        rows: rows.map(k => {
          const iv = this.intentView(k.intent);
          let deltaFmt = '—', deltaColor = '#cbd5e1';
          if (k.prevPos == null) { deltaFmt = 'new'; deltaColor = '#2563eb'; }
          else {
            const d = k.prevPos - k.pos;
            if (d > 0) { deltaFmt = '▲ ' + d; deltaColor = '#059669'; }
            else if (d < 0) { deltaFmt = '▼ ' + Math.abs(d); deltaColor = '#dc2626'; }
          }
          return {
            kw: k.kw, url: k.url || 'not ranking yet', isManual: k.source === 'manual',
            intentLabel: iv.label, intentStyle: iv.style,
            posText: k.pos == null ? '—' : k.pos, posStyle: this.posBadge(k.pos),
            deltaFmt, deltaStyle: { fontSize: '12px', fontWeight: 600, color: deltaColor },
            volFmt: this.fmt(k.volume),
            spark: this.spark(k.monthly, 46, 16),
            sparkColor: k.monthly && k.monthly[11] >= k.monthly[0] ? '#22c55e' : '#ef4444',
            kd: k.kd,
            kdBarStyle: { height: '100%', width: Math.min(100, k.kd) + '%', background: this.kdColor(k.kd) },
            clicksFmt: this.fmt(k.clicks)
          };
        })
      };
    }

