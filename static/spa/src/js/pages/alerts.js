    /* ============ ALERTS ============ */
    if (tab === 'alerts') {
      vals.showAlerts = true;
      const feed = data.feed;
      const counts = {
        all: feed.length,
        high: feed.filter(f => f.severity === 'high').length,
        medium: feed.filter(f => f.severity === 'medium').length,
        acked: feed.filter(f => f.acknowledged).length
      };
      const fBase = { padding: '4px 12px', fontSize: '12px', fontWeight: 500, borderRadius: '6px', cursor: 'pointer', color: '#64748b' };
      const fActive = Object.assign({}, fBase, { background: 'white', color: '#0f172a', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' });
      const rows = feed.filter(f => {
        if (s.alFilter === 'all') return true;
        if (s.alFilter === 'acked') return f.acknowledged;
        return f.severity === s.alFilter;
      });
      const kindMap = { anomaly: 'Anomaly', ranking: 'Ranking', backlink: 'Backlink', technical: 'Technical', system: 'System', ai: 'AI Visibility', ads: 'Ads' };
      vals.al = {
        hasUnacked: feed.some(f => !f.acknowledged),
        filters: [['all', 'All'], ['high', 'High'], ['medium', 'Medium'], ['acked', 'Acknowledged']].map(f => ({
          label: f[1] + ' (' + counts[f[0] === 'acked' ? 'acked' : f[0]] + ')',
          style: s.alFilter === f[0] ? fActive : fBase,
          click: () => { this.setState({ alFilter: f[0] }); this.pushNav({ alFilter: f[0] }); }
        })),
        empty: rows.length === 0,
        rows: rows.map(f => ({
          title: f.title, detail: f.detail, date: f.ts,
          kindLabel: kindMap[f.kind] || f.kind,
          sevLabel: f.severity, sevStyle: this.sevChip(f.severity),
          acknowledged: f.acknowledged, showAck: !f.acknowledged && f.severity !== 'info',
          ack: () => this.ackAlert(f.id),
          /* Undo sits on every acknowledged row, not only under the Acknowledged filter:
             "Acknowledge all" is one click that dismisses the whole feed, and the user has to
             be able to take a row back without hunting for where it went. */
          undo: () => this.unackAlert(f.id),
          rowStyle: { display: 'flex', alignItems: 'center', gap: '14px', padding: '14px 20px', borderTop: '1px solid #f1f5f9', opacity: f.acknowledged ? 0.55 : 1 }
        }))
      };
    }

